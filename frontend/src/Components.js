import React, { useState, useEffect, useMemo } from 'react';
import gymStorage from './storage'; // Updated to correct import path
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';
import PaymentsHistory from './components/payments/PaymentsHistory';
import { nextDueDateFromJoin, isOverdue, nextDueAfterPayment } from "./billing";
import LockBadge from "./LockBadge";
import { listPlans, upsertPlan, deletePlan, migratePlansFromSettingsIfNeeded } from './storage';
import { requirePinIfEnabled } from './pinlock';

/* === Payment Preview Helper (added) === */
function computeNextDuePreview(currentNextDueISO, monthsCovered) {
  return advanceNextDueByCycles(currentNextDueISO, monthsCovered);
}
/* === End Preview Helper === */

// Component with payment logic
const PaymentComponent = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newClient, setNewClient] = useState({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
  const [isAddingClient, setIsAddingClient] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [isRecordingPayment, setIsRecordingPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [activeTab, setActiveTab] = useState('dashboard');

  const membershipPricing = {
    'Monthly': 59,
    'Quarterly': 150,
    'Annual': 500
  };

  const loadDashboardData = async () => {
    try {
      const savedClients = await gymStorage.getAllMembers();
      const normalized = savedClients.map(recomputeStatus);
      setClients(normalized);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Compute clients with billing info
  const clientsWithBilling = (Array.isArray(clients) ? clients : []).map(c => {
    const due = c?.joinDate ? nextDueDateFromJoin(c.joinDate) : null;
    const overdue = c?.joinDate ? isOverdue(c.joinDate) : false;
    return {
      ...c,
      _dueDate: due ? due.toISOString().slice(0, 10) : null,
      _status: overdue ? "Overdue" : "Active"
    };
  });

  // Dashboard counts
  const overdueClients = clientsWithBilling.filter(c => c._status === "Overdue").length;
  const totalClients = clientsWithBilling.length;

  const loadClientsFromPhone = async () => {
    try {
      setLoading(true);
      const savedClients = await gymStorage.getAllMembers();
      const normalized = savedClients.map(recomputeStatus);
      setClients(normalized);
    } catch (error) {
      console.error('Error loading clients from phone:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveClientToPhone = async (client) => {
    try {
      await gymStorage.saveMembers(client);
      await loadClientsFromPhone(); // refreshed with recomputed status
    } catch (error) {
      console.error('Error saving client to phone:', error);
      alert('Error saving client data. Please try again.');
    }
  };

  const handleAddClient = async (e) => {
    e.preventDefault();
    try {
      const todayISO = toISODate();
      const client = {
        ...newClient,
        id: Date.now().toString(),
        joinDate: todayISO,
        lastPayment: todayISO, // set to null if you don't want a payment at join
        nextDue: add30DaysFrom(todayISO), // strict 30-day cycle
        status: 'Active',
        overdue: 0,
        amount: membershipPricing[newClient.membershipType] || newClient.amount
      };

      const normalized = recomputeStatus(client);
      
      // Basic validation - check if required fields exist
      if (!normalized.name?.trim() || !normalized.membershipType) { 
        alert('Name and membership type are required'); 
        return; 
      }
      
      await gymStorage.saveMembers(normalized);
      await loadClientsFromPhone();

      setNewClient({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
      setIsAddingClient(false);
    } catch (error) {
      console.error('Error adding client:', error);
      alert('Error adding client. Please try again.');
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Settings Usage
  const [defaultFee, setDefaultFee] = useState(0);
  const [dueSoonDays, setDueSoonDays] = useState(3);
  
  useEffect(() => {
    (async () => {
      const s = await gymStorage.getSetting('gymSettings', {}) || {};
      if (s?.membershipFeeDefault) setDefaultFee(Number(s.membershipFeeDefault) || 0);
      setDueSoonDays(Number(s?.reminderDays ?? 3));
    })();
  }, []);

  const isDueSoon = (iso) => {
    if (!iso) return false;
    const diff = (new Date(iso) - new Date()) / 86400000;
    return diff >= 0 && diff <= dueSoonDays;
  };

  // PaymentTracking component with modal
  const PaymentTracking = () => {
    // Settings-based state
    const [cycleDays, setCycleDays] = useState(30);
    const [graceDays, setGraceDays] = useState(0);
    const [nextDuePreview, setNextDuePreview] = useState("");

    useEffect(() => {
      (async () => {
        const s = await gymStorage.getSetting('gymSettings', {}) || {};
        setCycleDays(Number(s.billingCycleDays ?? 30) || 30);
        setGraceDays(Number(s.graceDays ?? 0) || 0);
      })();
    }, []);

    function addDays(dateISO, days) {
      const d = new Date(dateISO);
      d.setDate(d.getDate() + Number(days || 0));
      return d.toISOString().split('T')[0];
    }

    // --- Payment preview computed values ---
    const monthlyFee = Number(selectedClient?.amount || 0);
    const paid = Number((paymentAmount || '').toString().trim() || (monthlyFee || 0));
    const monthsCovered = Number.isFinite(paid) && (monthlyFee || 0) > 0
      ? Math.max(1, Math.floor(paid / monthlyFee))
      : 0;

    const previewNextDue = selectedClient && monthsCovered > 0
      ? computeNextDuePreview(selectedClient.nextDue || new Date().toISOString().split('T')[0], monthsCovered)
      : null;

    const isPaymentInvalid = !selectedClient || !Number.isFinite(paid) || paid <= 0 || (monthlyFee || 0) <= 0;

    // Handle recording payment with prefill and preview
    const handleRecordPayment = (client) => {
      setSelectedClient(client);
      const amt = (client?.amount != null && client.amount !== '') ? client.amount : defaultFee;
      setPaymentAmount(String(amt ?? ''));
      const paidOn = new Date().toISOString().split('T')[0];
      const joinISO = client.joinDate || client.createdAt?.slice(0,10) || paidOn;
      const preview = nextDueAfterPayment({
        joinISO,
        lastDueISO: client.nextDue,
        paidOnISO: paidOn,
        cycleDays,
        graceDays
      });
      setNextDuePreview(preview);
      setIsRecordingPayment(true);
    };

    // Handle payment form submission
    const handleSubmitPayment = async (e) => {
      e.preventDefault();
      if (!selectedClient) return;

      const form = e.currentTarget;
      const paymentDateInput = form.querySelector('input[type="date"]');
      const paidOn = paymentDateInput?.value || new Date().toISOString().split('T')[0];

      const amountNum = Number(paymentAmount || 0);
      if (Number.isNaN(amountNum) || amountNum <= 0) {
        alert("Enter a valid amount.");
        return;
      }

      const joinISO = selectedClient.joinDate || selectedClient.createdAt?.slice(0,10) || paidOn;
      const nextDueISO = nextDueAfterPayment({
        joinISO,
        lastDueISO: selectedClient.nextDue,
        paidOnISO: paidOn,
        cycleDays,
        graceDays
      });

      // Save payment record
      const payment = {
        id: crypto.randomUUID(),
        memberId: selectedClient.id,
        amount: amountNum,
        paidOn,
        recordedAt: new Date().toISOString(),
        note: "Recorded via PaymentTracking"
      };
      await gymStorage.saveData('payments', payment);

      // Update member record
      const updatedMember = {
        ...selectedClient,
        lastPayment: paidOn,
        nextDue: nextDueISO,
        status: 'Active',
        overdue: 0
      };
      await gymStorage.saveData('members', updatedMember);

      // Update UI state
      setClients(prev => prev.map(c => c.id === updatedMember.id ? updatedMember : c));

      setIsRecordingPayment(false);
      setSelectedClient(null);
      setPaymentAmount('');
      setNextDuePreview('');
    };

    // Real Reminders Function (WhatsApp/Email)
    const sendReminder = async (client) => {
      try {
        const s = await gymStorage.getSetting('gymSettings', {}) || {};
        const due = client?.nextDue || client?._dueDate || 'soon';
        const subject = `Alphalete membership due ${due}`;
        const amountTxt = s?.membershipFeeDefault ? ` Amount: ${s.membershipFeeDefault}.` : '';
        const body = `Hi ${client?.name || 'member'}, your Alphalete membership is due on ${due}.${amountTxt}\n\nYou can reply here with a payment receipt. Thank you!`;

        const hasPhone = client?.phone && client.phone.replace(/\D/g, '').length >= 7;
        if (hasPhone) {
          window.open(`https://wa.me/?text=${encodeURIComponent(body)}`, '_blank');
          return;
        }
        if (client?.email) {
          window.location.href = `mailto:${encodeURIComponent(client.email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
          return;
        }
        alert('No phone or email on file for this client.');
      } catch (e) {
        console.error('Reminder failed', e);
        alert('Could not open your email/WhatsApp app on this device.');
      }
    };

    // Focus management for accessibility
    useEffect(() => {
      if (isRecordingPayment && selectedClient) {
        const focusFirstInput = () => {
          const firstInput = document.querySelector('.payment-amount-input');
          if (firstInput) {
            firstInput.focus();
          }
        };
        // Small delay to ensure modal is rendered
        setTimeout(focusFirstInput, 100);
      }
    }, [isRecordingPayment, selectedClient]);

    // ESC key handler
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsRecordingPayment(false);
        setSelectedClient(null);
        setPaymentAmount('');
      }
    };

    if (!isRecordingPayment || !selectedClient) return null;

    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        role="dialog" 
        aria-modal="true" 
        aria-labelledby="paymentModalTitle"
        onKeyDown={handleKeyDown}
      >
        <div 
          className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
          tabIndex="-1"
          role="document"
          aria-describedby="paymentModalDesc"
        >
          <h3 id="paymentModalTitle" className="text-xl font-bold text-gray-900 mb-6">Record Payment</h3>
          <p id="paymentModalDesc" className="sr-only">Enter amount to record a payment and review the new next due date.</p>
          <p className="text-gray-600 mb-4">
            Recording payment for <strong>{selectedClient.name}</strong>
          </p>
          
          <form onSubmit={handleSubmitPayment}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Payment Amount (${monthlyFee} monthly fee)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={paymentAmount || defaultFee}
                onChange={(e) => setPaymentAmount(e.target.value)}
                placeholder={`Enter amount (default: $${defaultFee || monthlyFee})`}
                className="payment-amount-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {/* Monthly fee hint */}
              <p className="mt-1 text-xs text-gray-500">
                Monthly fee:&nbsp;
                <span className="font-medium text-gray-900">
                  {Number.isFinite(monthlyFee) && monthlyFee > 0 ? `$${monthlyFee.toFixed(2)}` : '—'}
                </span>
              </p>
            </div>

            {/* Payment Preview (non-blocking UX) */}
            <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Current next due</span>
                <span className="font-medium text-gray-900">
                  {selectedClient?.nextDue || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-gray-600">Months covered</span>
                <span className="font-medium text-gray-900">
                  {monthsCovered > 0 ? monthsCovered : '—'}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-gray-600">New next due (preview)</span>
                <span className="font-semibold">
                  {previewNextDue || '—'}
                </span>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={() => {
                  setIsRecordingPayment(false);
                  setSelectedClient(null);
                  setPaymentAmount('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isPaymentInvalid}
                className={`flex-1 rounded-lg px-4 py-2 font-semibold text-white ${isPaymentInvalid ? 'bg-gray-300 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'}`}
              >
                Record Payment <LockBadge />
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'dashboard'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('paymentsHistory')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'paymentsHistory'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Payments History
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <div>
          <h1>Payment Management Component</h1>
          {/* Add your existing dashboard UI components here */}
        </div>
      )}
      
      {activeTab === 'paymentsHistory' && <PaymentsHistory />}
      
      {/* Payment Modal */}
      <PaymentTracking />
    </div>
  );
};

// MembershipManagement Component with Active Index + Filter UI
const MembershipManagement = () => {
  const [memberships, setMemberships] = useState([]);
  const [filter, setFilter] = useState('all'); // 'all' | 'active' | 'inactive'
  const [editing, setEditing] = useState(null);
  
  const counts = {
    all: memberships.length,
    active: memberships.filter(p => !!p.active).length,
    inactive: memberships.filter(p => !p.active).length
  };

  useEffect(() => {
    (async () => {
      await gymStorage.migratePlansFromSettingsIfNeeded?.();
      setMemberships(await gymStorage.listPlans());
    })();
  }, []);

  useEffect(() => {
    (async () => {
      if (filter === 'all')        setMemberships(await gymStorage.listPlans());
      else if (filter === 'active') setMemberships(await gymStorage.listPlans({ active: true }));
      else                          setMemberships(await gymStorage.listPlans({ active: false }));
    })();
  }, [filter]);

  const savePlan = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const plan = {
      id: editing?.id || crypto.randomUUID(),
      name: fd.get("name").trim(),
      price: Number(fd.get("price") || 0),
      cycleDays: Number(fd.get("cycleDays") || 30),
      description: fd.get("description") || "",
      active: fd.get("active") === "on"
    };
    if (!plan.name) { alert("Plan name is required."); return; }
    await gymStorage.upsertPlan(plan);
    if (filter === 'all')        setMemberships(await gymStorage.listPlans());
    else if (filter === 'active') setMemberships(await gymStorage.listPlans({ active: true }));
    else                          setMemberships(await gymStorage.listPlans({ active: false }));
    setEditing(null);
    e.currentTarget.reset();
  };

  const onDelete = async (id) => {
    if (!(await requirePinIfEnabled("delete this plan"))) return;
    await gymStorage.deletePlan(id);
    if (filter === 'all')        setMemberships(await gymStorage.listPlans());
    else if (filter === 'active') setMemberships(await gymStorage.listPlans({ active: true }));
    else                          setMemberships(await gymStorage.listPlans({ active: false }));
  };

  // Optimistic Toggle (instant)
  async function toggleActiveOptimistic(plan) {
    const updated = { ...plan, active: !plan.active };
    const snapshot = memberships;
    setMemberships(prev => {
      if (filter === 'all') return prev.map(p => p.id === plan.id ? updated : p);
      if (filter === 'active' && plan.active === true) return prev.filter(p => p.id !== plan.id);
      if (filter === 'inactive' && plan.active === false) return prev.filter(p => p.id !== plan.id);
      return prev.map(p => p.id === plan.id ? updated : p);
    });
    try { await gymStorage.upsertPlan(updated); }
    catch (e) { console.error(e); setMemberships(snapshot); alert('Could not update plan.'); }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Membership Plans</h1>

      <form onSubmit={savePlan} className="bg-white rounded-2xl border shadow-soft p-4 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Plan Name</label>
            <input name="name" defaultValue={editing?.name || ""} className="w-full rounded-xl border px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Price</label>
            <input name="price" type="number" step="1" defaultValue={editing?.price ?? ""} className="w-full rounded-xl border px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Cycle (days)</label>
            <input name="cycleDays" type="number" defaultValue={editing?.cycleDays ?? 30} className="w-full rounded-xl border px-3 py-2" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <input 
                name="active" 
                type="checkbox" 
                defaultChecked={editing?.active !== undefined ? !!editing.active : true}
                className="mr-2"
              />
              Active
            </label>
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <textarea name="description" rows={3} defaultValue={editing?.description || ""} className="w-full rounded-xl border px-3 py-2" />
        </div>
        <div className="flex items-center gap-2">
          <button className="btn btn-primary" type="submit">{editing ? "Update Plan" : "Create Plan"}</button>
          {editing && <button type="button" className="btn" onClick={() => setEditing(null)}>Cancel</button>}
        </div>
      </form>

      <div className="bg-white rounded-2xl border shadow-soft">
        <div className="px-4 py-3 border-b">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-gray-600">
              <span className="mr-3">All: {counts.all}</span>
              <span className="mr-3">Active: {counts.active}</span>
              <span>Inactive: {counts.inactive}</span>
            </div>
            <select 
              className="rounded-xl border px-3 py-2 text-sm" 
              value={filter} 
              onChange={e => setFilter(e.target.value)}
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
        
        <div className="divide-y">
          {memberships.map(p => (
            <div key={p.id} className="p-4 flex items-start justify-between gap-3">
              <div>
                <div className="font-medium text-gray-900">{p.name}</div>
                <div className="text-sm text-gray-600">TTD {p.price} • {p.cycleDays} days</div>
                {p.description && <div className="text-sm text-gray-500 mt-1">{p.description}</div>}
                <label className="inline-flex items-center gap-2 text-sm mt-2">
                  <input
                    type="checkbox"
                    checked={!!p.active}
                    onChange={() => toggleActiveOptimistic(p)}
                  />
                  <span>{p.active ? "Active" : "Inactive"}</span>
                </label>
              </div>
              <div className="flex items-center gap-2">
                <button className="btn" onClick={() => setEditing(p)}>Edit</button>
                <button className="btn" onClick={() => onDelete(p.id)}>Delete</button>
              </div>
            </div>
          ))}
          {memberships.length === 0 && <div className="p-4 text-sm text-gray-500">No plans yet. Create your first plan above.</div>}
        </div>
      </div>
    </div>
  );
};

export { MembershipManagement };
export default PaymentComponent;
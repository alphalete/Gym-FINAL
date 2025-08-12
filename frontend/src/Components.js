import React, { useState, useEffect, useMemo } from 'react';
import gymStorage, { getAll as getAllStore, getSetting as getSettingNamed } from './storage';
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';
import PaymentsHistory from './components/payments/PaymentsHistory';
import { nextDueDateFromJoin, isOverdue, nextDueAfterPayment } from "./billing";
import LockBadge from "./LockBadge";
import { requirePinIfEnabled } from './pinlock';

// Helper function for data change signals
function signalDataChanged(what = '') {
  try {
    localStorage.setItem('dataChangedAt', String(Date.now()));
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: what }));
  } catch {}
}

// Simple plans helpers (since we removed complex plans store)
const planHelpers = {
  async listPlans() {
    try {
      const plans = await gymStorage.getSetting('membershipPlans', []);
      return Array.isArray(plans) ? plans : [];
    } catch (e) {
      console.warn('Failed to load plans:', e);
      return [];
    }
  },
  
  async upsertPlan(plan) {
    try {
      const plans = await this.listPlans();
      const id = plan.id || crypto.randomUUID?.() || String(Date.now());
      const newPlan = { ...plan, id };
      const idx = plans.findIndex(p => p.id === id);
      
      if (idx >= 0) plans[idx] = newPlan;
      else plans.push(newPlan);
      
      await gymStorage.saveSetting('membershipPlans', plans);
      return newPlan;
    } catch (e) {
      console.error('Failed to save plan:', e);
      throw e;
    }
  },
  
  async deletePlan(id) {
    try {
      const plans = await this.listPlans();
      const filtered = plans.filter(p => p.id !== id);
      await gymStorage.saveSetting('membershipPlans', filtered);
      return true;
    } catch (e) {
      console.error('Failed to delete plan:', e);
      throw e;
    }
  }
};

// Add plan methods to gymStorage for backward compatibility
Object.assign(gymStorage, planHelpers);

// Navigation helper function
function navTo(tab){
  const t = String(tab).toLowerCase();
  try { location.hash = `#tab=${t}`; } catch {}
  if (typeof window.setActiveTab === 'function') window.setActiveTab(t);
  else window.dispatchEvent(new CustomEvent('NAVIGATE', { detail: t }));
}

// Navigation helper function (enhanced version)
function navigate(tab) {
  const t = String(tab).toLowerCase();
  // Update hash first (works even if globals aren't ready):
  try { location.hash = `#tab=${t}`; } catch {}
  if (typeof window.setActiveTab === 'function') {
    window.setActiveTab(t);
  } else {
    window.dispatchEvent(new CustomEvent('NAVIGATE', { detail: t }));
  }
  // Navigation logging
  try { console.log('[NAV]', t); } catch {}
}

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
      signalDataChanged('member');
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
      signalDataChanged('member');
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
      const s = 
        (await (gymStorage.getSetting?.('gymSettings', {}) )) ??
        (await (getSettingNamed?.('gymSettings', {}) )) ??
        {};
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
    const [cycleAnchorMode, setCycleAnchorMode] = useState("anchored");
    const [nextDuePreview, setNextDuePreview] = useState("");

    useEffect(() => {
      (async () => {
        const s = 
          (await (gymStorage.getSetting?.('gymSettings', {}) )) ??
          (await (getSettingNamed?.('gymSettings', {}) )) ??
          {};
        setCycleDays(Number(s.billingCycleDays ?? 30) || 30);
        setGraceDays(Number(s.graceDays ?? 0) || 0);
        setCycleAnchorMode(s.cycleAnchorMode || "anchored");
      })();
    }, []);

    // Auto-open payment modal if Dashboard requested it
    useEffect(() => {
      const pendingId = localStorage.getItem("pendingPaymentMemberId");
      if (!pendingId || !clients?.length) return;
      const m = clients.find(c => String(c.id) === String(pendingId));
      if (m && typeof handleRecordPayment === "function") {
        localStorage.removeItem("pendingPaymentMemberId");
        handleRecordPayment(m);
      }
    }, [clients]);

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
        graceDays,
        mode: cycleAnchorMode
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
        graceDays,
        mode: cycleAnchorMode
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
      signalDataChanged('payment');

      // Update member record
      const updatedMember = {
        ...selectedClient,
        lastPayment: paidOn,
        nextDue: nextDueISO,
        status: 'Active',
        overdue: 0
      };
      await gymStorage.saveData('members', updatedMember);
      signalDataChanged('member');

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
        const s = 
          (await (gymStorage.getSetting?.('gymSettings', {}) )) ??
          (await (getSettingNamed?.('gymSettings', {}) )) ??
          {};
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
                Payment Date
              </label>
              <input
                type="date"
                defaultValue={new Date().toISOString().split('T')[0]}
                onChange={(e) => {
                  const paidOn = e.target.value || new Date().toISOString().slice(0,10);
                  const client = selectedClient;
                  if (client) {
                    const joinISO = client.joinDate || client.createdAt?.slice(0,10) || paidOn;
                    const preview = nextDueAfterPayment({
                      joinISO,
                      lastDueISO: client.nextDue,
                      paidOnISO: paidOn,
                      cycleDays,
                      graceDays,
                      mode: cycleAnchorMode
                    });
                    setNextDuePreview(preview);
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Payment Amount (${monthlyFee} monthly fee)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                placeholder={defaultFee ? String(defaultFee) : ""}
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
                  {nextDuePreview || '—'}
                </span>
              </div>
            </div>

            {/* Next due preview display */}
            {nextDuePreview && (
              <div className="text-sm text-gray-500 mt-2">
                Next due will be: <strong>{nextDuePreview}</strong>
              </div>
            )}

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

const Dashboard = () => {
  const [clients, setClients] = useState([]);
  const [payments, setPayments] = useState([]);
  const todayISO = new Date().toISOString().slice(0,10);

  // Simple data loading without complex dependencies
  async function loadDashboard() {
    try {
      const m = await (gymStorage.getAllMembers?.() ?? []);
      const p = await (gymStorage.getAllPayments?.() ?? []);
      setClients(Array.isArray(m) ? m : []);
      setPayments(Array.isArray(p) ? p : []);
      console.log('[Dashboard] loaded', { clients: m?.length || 0, payments: p?.length || 0 });
    } catch(e) {
      console.error('[Dashboard] load error', e);
      setClients([]);
      setPayments([]);
    }
  }
  
  useEffect(() => { loadDashboard(); }, []);
  
  useEffect(() => {
    const onChanged = () => loadDashboard();
    const onVisible = () => { if (!document.hidden) loadDashboard(); };
    const onHash = () => { if (location.hash.includes('tab=dashboard') || location.hash.includes('tab=home')) loadDashboard(); };
    
    window.addEventListener('DATA_CHANGED', onChanged);
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener('hashchange', onHash);
    
    return () => {
      window.removeEventListener('DATA_CHANGED', onChanged);
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  // Simple KPIs
  const activeCount = clients.filter(m => (m.status || "Active") === "Active").length;
  const overdueCount = clients.filter(m => {
    const due = m.nextDue;
    if (!due) return false;
    return new Date(due) < new Date(todayISO);
  }).length;

  const revenueMTD = payments
    .filter(p => p.paidOn && p.paidOn.slice(0,7) === todayISO.slice(0,7))
    .reduce((sum,p)=> sum + Number(p.amount||0), 0);

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      
      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold text-green-600">{activeCount}</div>
          <div className="text-sm text-gray-600">Active Members</div>
        </div>
        
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold text-blue-600">0</div>
          <div className="text-sm text-gray-600">Due Today</div>
        </div>
        
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold text-red-600">{overdueCount}</div>
          <div className="text-sm text-gray-600">Overdue</div>
        </div>
        
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold text-purple-600">${revenueMTD.toFixed(2)}</div>
          <div className="text-sm text-gray-600">Revenue (MTD)</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-2">
        <button type="button" className="rounded-xl bg-blue-500 text-white px-4 py-2" onClick={()=> navigate('payments')}>
          + Add Payment
        </button>
        <button type="button" className="rounded-xl bg-green-500 text-white px-4 py-2" onClick={()=> navigate('clients')}>
          + Add Member
        </button>
        <button type="button" className="rounded-xl border px-4 py-2">
          Send Reminders
        </button>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl border p-4">
        <h3 className="font-semibold mb-2">Recent Activity</h3>
        {payments.length > 0 ? (
          <div className="space-y-2">
            {payments.slice(-5).reverse().map(p => (
              <div key={p.id} className="flex justify-between text-sm">
                <span>Payment: ${p.amount}</span>
                <span className="text-gray-500">{p.paidOn}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No recent activity</p>
        )}
      </div>
    </div>
  );
};

const PlansMini = () => {
  const [plans, setPlans] = useState([]);
  const [allMembers, setAllMembers] = useState([]);

  useEffect(() => {
    (async () => {
      const p = (await gymStorage.listPlans?.()) || [];
      setPlans(Array.isArray(p)? p : []);
      const m = (await gymStorage.getAllMembers?.()) || [];
      setAllMembers(Array.isArray(m)? m : []);
    })();
  }, []);

  const counts = (() => {
    const map = new Map(plans.map(p => [p.id, { ...p, count: 0 }]));
    allMembers.forEach(m => {
      const pid = m.planId || m.plan?.id;
      if (pid && map.has(pid)) map.get(pid).count++;
    });
    return Array.from(map.values()).sort((a,b)=> b.count - a.count).slice(0,3);
  })();

  if (!counts.length) return <div className="text-sm text-gray-500">No plans yet.</div>;

  return (
    <div className="space-y-2">
      {counts.map(p => (
        <div key={p.id} className="flex items-center justify-between rounded-xl border px-3 py-2">
          <div>
            <div className="font-medium">{p.name}</div>
            <div className="text-xs text-gray-500">${Number(p.price||0).toFixed(2)} • {p.cycleDays || 30}d</div>
          </div>
          <button type="button" className="text-xs rounded-lg border px-2 py-1" onClick={()=> navigate('plans')}>View</button>
        </div>
      ))}
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

// Placeholder components for missing functionality
const ClientManagement = () => (
  <div className="p-4">
    <h2 className="text-xl font-bold mb-4">Client Management</h2>
    <p className="text-gray-600">Client management functionality will be implemented here.</p>
  </div>
);

const Reports = () => (
  <div className="p-4">
    <h2 className="text-xl font-bold mb-4">Reports</h2>
    <p className="text-gray-600">Reports functionality will be implemented here.</p>
  </div>
);

const Settings = () => (
  <div className="p-4">
    <h2 className="text-xl font-bold mb-4">Settings</h2>
    <p className="text-gray-600">Settings functionality will be implemented here.</p>
  </div>
);

const Components = {
  Dashboard,
  PaymentTracking: PaymentComponent,
  ClientManagement,
  MembershipManagement,
  Reports,
  Settings
};

export { MembershipManagement, Dashboard };
export default Components;
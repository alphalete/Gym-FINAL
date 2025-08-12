import React, { useState, useEffect, useMemo } from 'react';
import gymStorage, { getAll as getAllStore, signalDataChanged } from './storage'; // Updated to correct import path
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';
import PaymentsHistory from './components/payments/PaymentsHistory';
import { nextDueDateFromJoin, isOverdue, nextDueAfterPayment } from "./billing";
import LockBadge from "./LockBadge";
import { listPlans, upsertPlan, deletePlan, migratePlansFromSettingsIfNeeded } from './storage';
import { requirePinIfEnabled } from './pinlock';

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
  // TEMP debug so you see taps working; remove later:
  try { console.log('[NAV]', t); alert(`Navigating to: ${t}`); } catch {}
}

// Dev Inspector Component
const DevInspector = () => {
  const [open, setOpen] = useState(false);
  const [snapshot, setSnapshot] = useState({ members: 0, payments: 0, sampleMember: null });

  async function refresh() {
    try {
      const m = await (gymStorage.getAllMembers?.() ?? gymStorage.getAllData?.('members') ?? []);
      const p = await (gymStorage.getAllPayments?.() ?? gymStorage.getAllData?.('payments') ?? []);
      setSnapshot({ members: (m||[]).length, payments: (p||[]).length, sampleMember: (m||[])[0] || null });
      console.log('[DevInspector] members', m, 'payments', p);
    } catch (e) {
      console.error('[DevInspector] error', e);
    }
  }

  async function seedOne() {
    const id = String(Date.now());
    const member = { 
      id, 
      name: 'Debug User', 
      email: 'debug@example.com', 
      phone: '000', 
      joinDate: new Date().toISOString().slice(0,10), 
      lastPayment: new Date().toISOString().slice(0,10), 
      nextDue: new Date(Date.now()+30*86400000).toISOString().slice(0,10), 
      status: 'Active', 
      overdue: 0 
    };
    await gymStorage.saveData('members', member);
    signalDataChanged('member');
    await refresh();
  }

  useEffect(()=>{ if (open) refresh(); }, [open]);

  return (
    <>
      {/* Long-press title to toggle */}
      <button
        onPointerDown={(e)=>{ const t=setTimeout(()=>setOpen(v=>!v),700); e.currentTarget.dataset.t=t; }}
        onPointerUp={(e)=>{ clearTimeout(e.currentTarget.dataset.t); }}
        className="hidden" aria-hidden
      />
      {open && (
        <div className="fixed bottom-4 right-4 z-[9999] bg-white border rounded-xl shadow p-3 w-[90%] max-w-sm">
          <div className="text-xs font-semibold mb-2">Dev Inspector</div>
          <div className="text-xs">members: <b>{snapshot.members}</b> • payments: <b>{snapshot.payments}</b></div>
          <div className="text-[11px] break-words mt-1">{snapshot.sampleMember ? JSON.stringify(snapshot.sampleMember) : 'no sample'}</div>
          <div className="mt-2 flex gap-2">
            <button className="border rounded px-2 py-1 text-xs" onClick={refresh}>Refresh</button>
            <button className="border rounded px-2 py-1 text-xs" onClick={seedOne}>Seed 1 member</button>
            <button className="border rounded px-2 py-1 text-xs" onClick={()=>navTo('clients')}>Go Clients</button>
            <button className="border rounded px-2 py-1 text-xs" onClick={()=>navTo('payments')}>Go Payments</button>
          </div>
        </div>
      )}
    </>
  );
};

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
    const [cycleAnchorMode, setCycleAnchorMode] = useState("anchored");
    const [nextDuePreview, setNextDuePreview] = useState("");

    useEffect(() => {
      (async () => {
        const s = await gymStorage.getSetting('gymSettings', {}) || {};
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
  const [members, setMembers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [settings, setSettings] = useState({ billingCycleDays: 30, graceDays: 0, dueSoonDays: 3 });
  const [search, setSearch] = useState("");

  // mobile swipe state for KPI + dot indicators
  const kpiScrollerRef = React.useRef(null);
  const [kpiPage, setKpiPage] = React.useState(0);
  const kpiCount = 4;

  const todayISO = new Date().toISOString().slice(0,10);

  async function loadDashboardData() {
    try {
      // Prefer dedicated helpers, fall back to generic getters
      const m1 = (await gymStorage.getAllMembers?.()) ?? [];
      const m2 = await getAllStore('members');
      const m3 = await getAllStore('clients'); // legacy/alt store name
      // Merge by id (prefer objects with more fields)
      const byId = new Map();
      [...m1, ...m2, ...m3].forEach(x => {
        if (!x) return;
        const id = String(x.id || x.memberId || x._id || x.phone || x.email || Math.random());
        const prev = byId.get(id) || {};
        byId.set(id, { ...prev, ...x, id });
      });
      const allMembers = Array.from(byId.values());

      const p1 = (await gymStorage.getAllPayments?.()) ?? [];
      const p2 = await getAllStore('payments');
      const allPayments = [...p1, ...p2];

      const s = (await gymStorage.getSetting?.('gymSettings', {})) ?? {};

      setMembers(allMembers);
      setPayments(allPayments);
      setSettings(s);
      console.log('[Dashboard] loaded', { members: allMembers.length, payments: allPayments.length });
    } catch (e) {
      console.error('[Dashboard] load error', e);
      setMembers([]); setPayments([]);
    }
  }

  useEffect(() => { loadDashboardData(); }, []);

  // Refresh when the page becomes visible again (mobile switch-back) or when we signal data changes
  useEffect(() => {
    const onVisible = () => { if (!document.hidden) loadDashboardData(); };
    const onChanged = () => loadDashboardData();
    document.addEventListener('visibilitychange', onVisible);
    window.addEventListener('DATA_CHANGED', onChanged);
    const onHash = () => { if (location.hash.includes('tab=dashboard') || location.hash.includes('tab=home')) loadDashboardData(); };
    window.addEventListener('hashchange', onHash);
    return () => {
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('DATA_CHANGED', onChanged);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  // track swipe position (mobile)
  React.useEffect(() => {
    const el = kpiScrollerRef.current;
    if (!el) return;
    const onScroll = () => {
      const w = el.getBoundingClientRect().width || el.clientWidth || 1;
      const page = Math.round(el.scrollLeft / Math.max(1, w * 0.72)); // matches min-w-[72%]
      setKpiPage(Math.max(0, Math.min(kpiCount - 1, page)));
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, [kpiCount]);

  function snapToKpi(idx) {
    const el = kpiScrollerRef.current;
    if (!el) return;
    const w = el.getBoundingClientRect().width || el.clientWidth || 1;
    const itemWidth = Math.max(1, w * 0.72);
    el.scrollTo({ left: itemWidth * idx, behavior: 'smooth' });
  }

  const parseISO = (s) => s ? new Date(s) : null;
  const isOverdue  = (iso) => !!iso && parseISO(iso) < new Date(todayISO);
  const isDueToday = (iso) => iso === todayISO;
  const dueSoonDays = Number(settings.dueSoonDays ?? settings.reminderDays ?? 3) || 3;
  const isDueSoon  = (iso) => {
    if (!iso) return false;
    const d = parseISO(iso), t = new Date(todayISO);
    const diff = Math.round((d - t) / 86400000);
    return diff > 0 && diff <= dueSoonDays;
  };

  // KPIs
  const activeCount = members.filter(m => (m.status || "Active") === "Active").length;
  const startOfMonth = new Date(todayISO.slice(0,7) + "-01");
  const newMTD = members.filter(m => {
    const c = parseISO(m.createdAt?.slice(0,10) || m.joinDate);
    return c && c >= startOfMonth;
  }).length;
  const revenueMTD = payments
    .filter(p => p.paidOn && p.paidOn.slice(0,7) === todayISO.slice(0,7))
    .reduce((sum,p)=> sum + Number(p.amount||0), 0);
  const overdueCount = members.filter(m => isOverdue(m.nextDue)).length;

  // Lists
  const dueToday = members.filter(m => isDueToday(m.nextDue))
                          .sort((a,b)=> (a.name||"").localeCompare(b.name||""))
                          .slice(0,5);
  const overdue = members.filter(m => isOverdue(m.nextDue))
                         .sort((a,b)=> (new Date(a.nextDue) - new Date(b.nextDue)))
                         .slice(0,5);

  // Search (keeps your existing list behavior below cards)
  const filteredMembers = members.filter(m => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return [m.name, m.email, m.phone].some(v => (v||"").toLowerCase().includes(q));
  });

  // Bridge to Payments → auto-open modal
  const goRecordPayment = (member) => {
    try { localStorage.setItem("pendingPaymentMemberId", member.id); } catch {}
    navigate('payments');
  };

  // Reminder (WhatsApp/email)
  const sendReminder = async (client) => {
    try {
      const s = await (gymStorage.getSetting?.('gymSettings', {}) ?? {});
      const due = client?.nextDue || "soon";
      const subject = `Membership due ${due}`;
      const amountTxt = s?.membershipFeeDefault ? ` Amount: ${s.membershipFeeDefault}.` : '';
      const body = `Hi ${client?.name || 'member'}, your membership is due on ${due}.${amountTxt}\n\nThank you!`;
      const hasPhone = client?.phone && client.phone.replace(/\D/g, '').length >= 7;
      if (hasPhone) { window.open(`https://wa.me/?text=${encodeURIComponent(body)}`, '_blank'); return; }
      if (client?.email) {
        window.location.href = `mailto:${encodeURIComponent(client.email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
        return;
      }
      alert('No phone or email on file.');
    } catch {
      alert('Could not open your email/WhatsApp app.');
    }
  };

  // Tiny revenue sparkline (last 8 weeks)
  const revenuePoints = (() => {
    const byWeek = new Map();
    const d = new Date(todayISO);
    for (let i=0;i<56;i++){ // ensure buckets exist
      const cur = new Date(d.getTime() - i*86400000);
      const year = cur.getFullYear();
      const oneJan = new Date(year,0,1);
      const week = Math.ceil((((cur - oneJan)/86400000) + oneJan.getDay()+1)/7);
      byWeek.set(`${year}-${week}`, 0);
    }
    payments.forEach(p => {
      if (!p.paidOn) return;
      const dt = new Date(p.paidOn);
      const year = dt.getFullYear();
      const oneJan = new Date(year,0,1);
      const week = Math.ceil((((dt - oneJan)/86400000) + oneJan.getDay()+1)/7);
      const key = `${year}-${week}`;
      if (byWeek.has(key)) byWeek.set(key, byWeek.get(key) + Number(p.amount||0));
    });
    return Array.from(byWeek.entries()).slice(-8).map(([,v])=>v);
  })();
  const maxRev = Math.max(1, ...revenuePoints);
  const spark = (w=160, h=40) => {
    const step = w / Math.max(1, revenuePoints.length-1);
    const pts = revenuePoints.map((v,i)=>{
      const x = i*step;
      const y = h - (v/maxRev)*h;
      return `${x},${y}`;
    }).join(" ");
    return (
      <svg width={w} height={h} className="overflow-visible text-gray-400">
        <polyline fill="none" stroke="currentColor" strokeWidth="2" points={pts} />
      </svg>
    );
  };

  return (
    <div className="p-4 space-y-4">
      <div className="text-[11px] px-2 py-1 rounded-lg bg-yellow-100 text-yellow-800">
        Dashboard debug • members: {members.length} • payments: {payments.length}
      </div>
      
      {/* --- Swipeable KPI cards (reuse your colorful cards inside each slot) --- */}
      <div className="lg:grid lg:grid-cols-4 lg:gap-3">
        <div
          ref={kpiScrollerRef}
          role="region"
          aria-label="Key performance indicators"
          className="relative z-0 flex lg:block gap-3 overflow-x-auto lg:overflow-visible snap-x snap-mandatory px-1 -mx-1 pb-2 hide-scrollbar"
        >
          <div className="min-w-[72%] sm:min-w-[320px] snap-start">
            {/* Card 1 content → Active Members */}
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <p className="text-sm font-medium text-gray-600">Active Members</p>
              <p className="text-3xl font-bold text-emerald-600">{activeCount}</p>
            </div>
          </div>
          <div className="min-w-[72%] sm:min-w-[320px] snap-start">
            {/* Card 2 → Payments Due Today */}
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <p className="text-sm font-medium text-gray-600">Payments Due Today</p>
              <p className="text-3xl font-bold text-indigo-600">{dueToday.length}</p>
            </div>
          </div>
          <div className="min-w-[72%] sm:min-w-[320px] snap-start">
            {/* Card 3 → Overdue Accounts */}
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <p className="text-sm font-medium text-gray-600">Overdue Accounts</p>
              <p className="text-3xl font-bold text-red-600">{overdue.length}</p>
            </div>
          </div>
          <div className="min-w-[72%] sm:min-w-[320px] snap-start">
            {/* Card 4 → Revenue MTD */}
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <p className="text-sm font-medium text-gray-600">Revenue (MTD)</p>
              <p className="text-3xl font-bold text-blue-600">${revenueMTD.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Dots under cards (mobile only) */}
      <div className="flex items-center justify-center gap-2 py-1 lg:hidden">
        {Array.from({ length: kpiCount }).map((_, i) => (
          <button
            key={i}
            type="button"
            aria-label={`Go to KPI ${i + 1}`}
            onClick={() => snapToKpi(i)}
            className={["kpi-dot h-2 w-2 rounded-full transition-transform",
                        i === kpiPage ? "scale-125 kpi-dot-active" : "opacity-60"].join(" ")}
          />
        ))}
      </div>

      {/* Quick Actions */}
      <div className="relative z-10 pointer-events-auto flex flex-col sm:flex-row gap-2">
        <button type="button" className="rounded-xl border px-3 py-2" onClick={()=> navigate('payments')}>+ Add Payment</button>
        <button type="button" className="rounded-xl border px-3 py-2" onClick={()=> navigate('clients')}>+ Add Member</button>
        <button type="button" className="rounded-xl border px-3 py-2" onClick={()=> overdue.concat(dueToday).forEach(m=>sendReminder(m))}>Send Reminders</button>
      </div>

      {/* Due Today */}
      <div className="bg-white rounded-2xl border p-4">
        <div className="font-semibold mb-2">Due Today</div>
        {dueToday.length === 0 ? (
          <div className="text-sm text-gray-500">No members due today.</div>
        ) : dueToday.map(m => (
          <div key={m.id} className="flex items-center justify-between py-2 border-b last:border-0">
            <div>
              <div className="font-medium">{m.name}</div>
              <div className="text-xs text-gray-500">{m.nextDue}</div>
            </div>
            <div className="flex gap-2">
              <button type="button" className="text-sm rounded-lg border px-2 py-1" onClick={()=> goRecordPayment(m)}>Record</button>
              <button type="button" className="text-sm rounded-lg border px-2 py-1" onClick={()=> sendReminder(m)}>Remind</button>
            </div>
          </div>
        ))}
      </div>

      {/* Overdue */}
      <div className="bg-white rounded-2xl border p-4">
        <div className="font-semibold mb-2">Overdue</div>
        {overdue.length === 0 ? (
          <div className="text-sm text-gray-500">No overdue members 🎉</div>
        ) : overdue.map(m => (
          <div key={m.id} className="flex items-center justify-between py-2 border-b last:border-0">
            <div>
              <div className="font-medium">{m.name}</div>
              <div className="text-xs text-red-600">{m.nextDue}</div>
            </div>
            <div className="flex gap-2">
              <button type="button" className="text-sm rounded-lg border px-2 py-1" onClick={()=> goRecordPayment(m)}>Record</button>
              <button type="button" className="text-sm rounded-lg border px-2 py-1" onClick={()=> sendReminder(m)}>Remind</button>
            </div>
          </div>
        ))}
      </div>

      {/* Trends + Plans snapshot */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="bg-white rounded-2xl border p-4 lg:col-span-2">
          <div className="flex items-center justify-between mb-2">
            <div className="font-semibold">Collections (last 8 weeks)</div>
            <button type="button" className="text-xs text-gray-500" onClick={()=> navigate('reports')}>View Reports</button>
          </div>
          {spark()}
        </div>

        <div className="bg-white rounded-2xl border p-4">
          <div className="font-semibold mb-2">Plans snapshot</div>
          <PlansMini />
        </div>
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

const Components = {
  Dashboard,
  PaymentTracking: PaymentComponent,
  ClientManagement: PaymentComponent, // You might need separate components
  MembershipManagement,
  Reports: PaymentComponent, // Placeholder - you might need separate components
  Settings: PaymentComponent // Placeholder - you might need separate components
};

export { MembershipManagement, Dashboard };
export default Components;
import React, { useEffect, useMemo, useState } from "react";
import gymStorage, { getAll as getAllStore, getPlanById, upsertMemberWithPlanSnapshot, getSetting as getSettingNamed, saveSetting as saveSettingNamed } from "./storage";
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';
import PaymentsHistory from './components/payments/PaymentsHistory';
import { nextDueDateFromJoin, isOverdue, nextDueAfterPayment } from "./billing";
import LockBadge from "./LockBadge";
import { requirePinIfEnabled } from './pinlock';
// Import consolidated utilities from common.js (Phase D requirement)
import { 
  navigate, 
  addDaysISO, 
  computeNextDueOptionA, 
  openWhatsApp, 
  openEmail, 
  buildReminder,
  formatCurrency,
  formatDate,
  getPaymentStatus,
  getInitials
} from './utils/common';

/* Share utility function */
function shareFallback(text) {
  if (navigator.share) {
    navigator.share({ text }).catch(console.error);
  } else {
    navigator.clipboard?.writeText(text).then(() => alert('Copied to clipboard!')).catch(() => {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
      alert('Copied to clipboard!');
    });
  }
}
/* /Utilities */

// Helper function for data change signals
function signalDataChanged(what = '') {
  try {
    localStorage.setItem('dataChangedAt', String(Date.now()));
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: what }));
  } catch {}
}

// Simplified signal function
function signalChanged(what='') { 
  try { 
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: what })); 
  } catch {} 
}

/* === Preview Helper (added) === */
function computeNextDuePreview(currentNextDueISO, monthsCovered) {
  return advanceNextDueByCycles(currentNextDueISO, monthsCovered);
}
/* === End Preview Helper === */

// --- Payments (PaymentTracking) ---
const PaymentComponent = () => {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [isRecordingPayment, setIsRecordingPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paidOnDate, setPaidOnDate] = useState(new Date().toISOString().slice(0,10));

  useEffect(()=>{ (async()=>{ setClients(await gymStorage.getAllMembers()||[]); })(); },[]);

  // When selecting client, default amount from snapshot
  useEffect(() => {
    if (!selectedClient) return;
    const m = clients.find(x => String(x.id)===String(selectedClient.id));
    if (!m) return;
    if (!paymentAmount && m.fee != null) setPaymentAmount(String(m.fee));
  }, [selectedClient, clients]);

  async function handlePaymentSubmit(){
    if (!selectedClient) return;
    const m = clients.find(x => String(x.id)===String(selectedClient.id));
    const amountNum = Number(paymentAmount||0);
    const paidOn = paidOnDate || new Date().toISOString().slice(0,10);
    const payRec = { id: crypto.randomUUID?.()||String(Date.now()), memberId: String(m.id), amount: amountNum, paidOn };
    await gymStorage.savePayment(payRec);

    const nextDue = computeNextDueOptionA(m.nextDue, paidOn, m.cycleDays || 30);
    const updated = { ...m, lastPayment: paidOn, nextDue, status: 'Active', overdue: 0 };
    await gymStorage.saveMembers(updated);

    try { window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:'payments'})); } catch {}
    try { window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:'members'})); } catch {}
    setIsRecordingPayment(false); setSelectedClient(null); setPaymentAmount('');
    setPaidOnDate(new Date().toISOString().slice(0,10));
    setClients(await gymStorage.getAllMembers()||[]);
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Payment Tracking</h1>
        <button 
          type="button" 
          className="border rounded px-3 py-2 bg-green-500 text-white hover:bg-green-600" 
          onClick={() => setIsRecordingPayment(true)}
        >
          Record Payment
        </button>
      </div>

      {isRecordingPayment && (
        <div className="fixed inset-0 bg-black/20 z-[999] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-4 w-full max-w-md space-y-3">
            <div className="text-lg font-semibold">Record Payment</div>
            <select 
              className="border rounded px-3 py-2 w-full"
              value={selectedClient?.id || ''}
              onChange={e => {
                const client = clients.find(c => c.id === e.target.value);
                setSelectedClient(client || null);
              }}
            >
              <option value="">Select Member</option>
              {clients.map(c => (
                <option key={c.id} value={c.id}>
                  {c.name} - {c.planName || 'No Plan'} - ${c.fee || 0}
                </option>
              ))}
            </select>
            <input 
              type="number" 
              step="0.01"
              className="border rounded px-3 py-2 w-full"
              placeholder="Payment Amount"
              value={paymentAmount}
              onChange={e => setPaymentAmount(e.target.value)}
            />
            <input 
              type="date"
              className="border rounded px-3 py-2 w-full"
              value={paidOnDate}
              onChange={e => setPaidOnDate(e.target.value)}
            />
            <div className="flex justify-end gap-2 pt-2">
              <button 
                type="button" 
                className="border rounded px-3 py-2 hover:bg-gray-50" 
                onClick={() => {
                  setIsRecordingPayment(false);
                  setSelectedClient(null);
                  setPaymentAmount('');
                }}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="border rounded px-3 py-2 bg-green-500 text-white hover:bg-green-600" 
                onClick={handlePaymentSubmit}
              >
                Record Payment
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <h2 className="text-lg font-semibold">Recent Payments</h2>
        {/* Payment history would go here */}
        <div className="text-sm text-gray-500">Payment history will display here</div>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const [clients, setClients] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const todayISO = new Date().toISOString().slice(0,10);

  // Simple data loading without complex dependencies
  async function loadDashboard() {
    try {
      setLoading(true);
      console.log('[Dashboard] Starting data load...');
      
      const m = await (gymStorage.getAllMembers?.() ?? []);
      const p = await (gymStorage.getAllPayments?.() ?? []);
      setClients(Array.isArray(m) ? m : []);
      setPayments(Array.isArray(p) ? p : []);
      
      console.log('[Dashboard] loaded', { clients: m?.length || 0, payments: p?.length || 0 });
    } catch(e) {
      console.error('[Dashboard] load error', e);
      setClients([]);
      setPayments([]);
    } finally {
      setLoading(false); // Always ensure loading stops
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

  // Show GoGym4U loading indicator
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <div className="text-gray-600">Loading Dashboard...</div>
        </div>
      </div>
    );
  }

  // Calculate KPIs with GoGym4U logic
  const activeCount = clients.filter(m => (m.status || "Active") === "Active").length;
  const totalCount = clients.length;
  
  // Due today calculation
  const dueToday = clients.filter(m => {
    if (m.status !== "Active") return false;
    return m.nextDue === todayISO;
  });
  
  // Overdue calculation
  const overdue = clients.filter(m => {
    if (m.status !== "Active") return false;
    const due = m.nextDue;
    if (!due) return false;
    return new Date(due) < new Date(todayISO);
  });

  // Due soon (next 3 days)
  const dueSoon = clients.filter(m => {
    if (m.status !== "Active" || overdue.includes(m) || dueToday.includes(m)) return false;
    const due = m.nextDue;
    if (!due) return false;
    const dueDate = new Date(due);
    const today = new Date(todayISO);
    const diffTime = dueDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 && diffDays <= 3;
  });

  // Revenue calculation (MTD)
  const revenueMTD = payments
    .filter(p => p.paidOn && p.paidOn.slice(0,7) === todayISO.slice(0,7))
    .reduce((sum,p)=> sum + Number(p.amount||0), 0);

  function goRecordPayment(m) {
    localStorage.setItem("pendingPaymentMemberId", String(m.id));
    navigate('payments');
  }

  // Get alerts (due today + overdue)
  const alerts = [...dueToday, ...overdue].slice(0, 5); // Show max 5 alerts

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title text-primary">Dashboard</h1>
              <p className="page-subtitle">Welcome back! Here's what's happening at your gym today.</p>
            </div>
            <div className="flex space-x-3">
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={() => navigate('payments')}
              >
                + Record Payment
              </button>
              <button 
                type="button" 
                className="btn btn-secondary"
                onClick={() => navigate('clients')}
              >
                + Add Member
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* KPI Cards Grid - GoGym4U Style */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
          {/* Active Members */}
          <div className="stat-card bg-primary text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{activeCount}</div>
                <div className="stat-label text-primary-100">Active Members</div>
              </div>
              <div className="text-primary-200 text-3xl">👥</div>
            </div>
          </div>

          {/* Due Soon */}
          <div className="stat-card bg-warning text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{dueSoon.length}</div>
                <div className="stat-label text-warning-100">Due Soon (3 days)</div>
              </div>
              <div className="text-warning-200 text-3xl">⏰</div>
            </div>
          </div>

          {/* Overdue */}
          <div className="stat-card bg-danger text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{overdue.length}</div>
                <div className="stat-label text-danger-100">Overdue</div>
              </div>
              <div className="text-danger-200 text-3xl">⚠️</div>
            </div>
          </div>

          {/* Revenue */}
          <div className="stat-card bg-success text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{formatCurrency(revenueMTD)}</div>
                <div className="stat-label text-success-100">Revenue (MTD)</div>
              </div>
              <div className="text-success-200 text-3xl">💰</div>
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="mb-8">
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="text-warning mr-2">⚠️</span>
                  Payment Alerts ({alerts.length})
                </h3>
              </div>
              <div className="card-body">
                <div className="space-y-3">
                  {alerts.map(member => {
                    const status = getPaymentStatus(member);
                    const isOverdue = overdue.includes(member);
                    
                    return (
                      <div key={member.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <div className="flex items-center space-x-4">
                          {/* Avatar */}
                          <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-white font-medium">
                            {getInitials(member.name)}
                          </div>
                          
                          {/* Member Info */}
                          <div>
                            <div className="font-medium text-gray-900">{member.name || "(No name)"}</div>
                            <div className="text-sm text-gray-500 flex items-center space-x-2">
                              <span>{member.planName ? `${member.planName} • ${formatCurrency(member.fee)}` : "No plan"}</span>
                              <span>•</span>
                              <span className={isOverdue ? 'text-danger font-medium' : 'text-warning font-medium'}>
                                Due: {formatDate(member.nextDue, false)}
                              </span>
                            </div>
                          </div>
                          
                          {/* Status Badge */}
                          <span className={`badge ${status.class}`}>
                            {status.label}
                          </span>
                        </div>
                        
                        {/* Action Buttons */}
                        <div className="flex space-x-2">
                          <button 
                            type="button" 
                            className="btn btn-sm btn-primary" 
                            onClick={() => goRecordPayment(member)}
                          >
                            Record Payment
                          </button>
                          <button 
                            type="button" 
                            className="btn btn-sm btn-outline" 
                            onClick={() => openWhatsApp(buildReminder(member), member.phone)}
                          >
                            WhatsApp
                          </button>
                          <button 
                            type="button" 
                            className="btn btn-sm btn-outline" 
                            onClick={() => openEmail("Payment Reminder", buildReminder(member), member.email)}
                          >
                            Email
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Payments */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-primary mr-2">💳</span>
                Recent Payments
              </h3>
            </div>
            <div className="card-body">
              {payments.length > 0 ? (
                <div className="space-y-3">
                  {payments.slice(-5).reverse().map(payment => (
                    <div key={payment.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-success-100 rounded-full flex items-center justify-center">
                          <span className="text-success text-sm">💰</span>
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{formatCurrency(payment.amount)}</div>
                          <div className="text-sm text-gray-500">{formatDate(payment.paidOn)}</div>
                        </div>
                      </div>
                      <span className="badge badge-success">Paid</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">💳</div>
                  <div>No payments yet</div>
                  <div className="text-sm">Recent payments will appear here</div>
                </div>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-info mr-2">📊</span>
                Quick Stats
              </h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Total Members</span>
                  <span className="font-semibold">{totalCount}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Active Rate</span>
                  <span className="font-semibold">{totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">This Month Revenue</span>
                  <span className="font-semibold text-success">{formatCurrency(revenueMTD)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Avg. Payment</span>
                  <span className="font-semibold">
                    {payments.length > 0 ? formatCurrency(payments.reduce((sum, p) => sum + Number(p.amount || 0), 0) / payments.length) : formatCurrency(0)}
                  </span>
                </div>
              </div>
            </div>
          </div>
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

// --- Dashboard component continues here ---

// --- Members (ClientManagement) ---
const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isAddingClient, setIsAddingClient] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [form, setForm] = useState({ name:"", email:"", phone:"", planId:"" });
  const [searchTerm, setSearchTerm] = useState("");

  async function loadMembersAndPlans(){
    try {
      const ms = await gymStorage.getAllMembers();
      setClients(ms || []);
      const ps = await gymStorage.getPlans();
      setPlans((ps || []).filter(p=>!p._deleted).sort((a,b)=> (a.name||"").localeCompare(b.name||"")));
    } catch(e){ console.error('load error', e); }
  }

  useEffect(()=>{ loadMembersAndPlans(); },[]);

  useEffect(() => {
    const onOpen = () => { 
      setEditingClient(null); 
      setForm({ name:"", email:"", phone:"", planId:"" }); 
      setIsAddingClient(true); 
    };
    window.addEventListener("OPEN_ADD_MEMBER", onOpen);
    const onChanged = () => loadMembersAndPlans();
    window.addEventListener("DATA_CHANGED", onChanged);
    return () => { 
      window.removeEventListener("OPEN_ADD_MEMBER", onOpen); 
      window.removeEventListener("DATA_CHANGED", onChanged); 
    };
  }, []);

  async function save(){
    try{
      const id = editingClient?.id || (crypto.randomUUID?.() || String(Date.now()));
      const plan = form.planId ? plans.find(p=>String(p.id)===String(form.planId)) : null;
      const base = {
        id,
        name: form.name?.trim() || '',
        email: form.email?.trim() || '',
        phone: form.phone?.trim() || '',
        status: editingClient?.status || 'Active',
        joinDate: editingClient?.joinDate || new Date().toISOString().slice(0,10),
        lastPayment: editingClient?.lastPayment || null,
        nextDue: editingClient?.nextDue || (plan ? addDaysISO(new Date().toISOString().slice(0,10), Number(plan.cycleDays||30)) : undefined),
      };
      const snap = plan ? {
        planId: plan.id,
        planName: plan.name,
        cycleDays: Number(plan.cycleDays || 30),
        fee: Number(plan.price || 0),
      } : {};
      await gymStorage.saveMembers({ ...base, ...snap });
      try { window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:'members'})); } catch {}
      setIsAddingClient(false); setEditingClient(null);
      await loadMembersAndPlans();
    }catch(e){ console.error('[save] failed', e); alert('Save failed'); }
  }

  async function toggleStatus(m) {
    await gymStorage.saveMembers({ ...m, status: m.status === "Active" ? "Inactive" : "Active" });
    signalChanged('members'); 
    loadMembersAndPlans();
  }

  // Filter clients based on search term
  const filteredClients = clients.filter(client => 
    !searchTerm || 
    (client.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (client.email || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (client.phone || "").includes(searchTerm) ||
    (client.planName || "").toLowerCase().includes(searchTerm.toLowerCase())
  );

  // GoGym4U loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <div className="text-gray-600">Loading Members...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title text-primary">Members</h1>
              <p className="page-subtitle">Manage gym memberships and member information</p>
            </div>
            <button 
              type="button" 
              className="btn btn-primary"
              onClick={() => { 
                setEditingClient(null); 
                setForm({ name:"", email:"", phone:"", planId:"" }); 
                setIsAddingClient(true); 
              }}
            >
              + Add Member
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Search and Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
          {/* Search Bar */}
          <div className="lg:col-span-2">
            <div className="relative">
              <div className="input-group">
                <div className="input-group-text">
                  <span>🔍</span>
                </div>
                <input
                  type="text"
                  className="input pl-10"
                  placeholder="Search members by name, email, phone, or plan..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="lg:col-span-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="stat-card bg-primary text-white text-center">
                <div className="stat-value">{clients.filter(c => c.status === 'Active').length}</div>
                <div className="stat-label text-primary-100">Active</div>
              </div>
              <div className="stat-card bg-gray-600 text-white text-center">
                <div className="stat-value">{clients.length}</div>
                <div className="stat-label text-gray-100">Total</div>
              </div>
            </div>
          </div>
        </div>

        {/* Members List */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="text-primary mr-2">👥</span>
              Members ({filteredClients.length})
            </h3>
          </div>
          <div className="card-body">
            {filteredClients.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredClients.map(client => {
                  const status = getPaymentStatus(client);
                  
                  return (
                    <div key={client.id} className="card hover:shadow-md transition-shadow duration-200">
                      <div className="card-body">
                        {/* Member Header */}
                        <div className="flex items-center space-x-3 mb-4">
                          {/* Avatar */}
                          <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-white font-medium text-lg">
                            {getInitials(client.name)}
                          </div>
                          
                          {/* Basic Info */}
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-gray-900 truncate">{client.name || "(No name)"}</div>
                            <div className="text-sm text-gray-500 flex items-center space-x-1">
                              <span className={`badge ${status.class}`}>{status.label}</span>
                              <span className={`badge ${client.status === 'Active' ? 'badge-success' : 'badge-gray'}`}>
                                {client.status || 'Active'}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Contact Info */}
                        <div className="space-y-2 mb-4">
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-5">📧</span>
                            <span className="truncate">{client.email || "No email"}</span>
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-5">📱</span>
                            <span>{client.phone || "No phone"}</span>
                          </div>
                          <div className="flex items-center text-sm text-gray-600">
                            <span className="w-5">📅</span>
                            <span>Joined {formatDate(client.joinDate)}</span>
                          </div>
                        </div>

                        {/* Plan Info */}
                        {client.planName ? (
                          <div className="bg-gray-50 rounded-lg p-3 mb-4">
                            <div className="flex justify-between items-start">
                              <div>
                                <div className="font-medium text-gray-900">{client.planName}</div>
                                <div className="text-sm text-gray-600">{formatCurrency(client.fee)} / {client.cycleDays || 30} days</div>
                              </div>
                              <span className="badge badge-info">Plan</span>
                            </div>
                            {client.nextDue && (
                              <div className="text-sm text-gray-600 mt-2">
                                Next due: {formatDate(client.nextDue, false)}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="bg-gray-50 rounded-lg p-3 mb-4 text-center text-gray-500">
                            <div className="text-2xl mb-1">📋</div>
                            <div className="text-sm">No plan assigned</div>
                          </div>
                        )}

                        {/* Action Buttons */}
                        <div className="flex space-x-2">
                          <button 
                            type="button" 
                            className="btn btn-sm btn-outline flex-1"
                            onClick={() => { 
                              setEditingClient(client); 
                              setForm({ 
                                name: client.name||"", 
                                email: client.email||"", 
                                phone: client.phone||"", 
                                planId: client.planId || "" 
                              }); 
                              setIsAddingClient(true); 
                            }}
                          >
                            Edit
                          </button>
                          <button 
                            type="button" 
                            className={`btn btn-sm flex-1 ${client.status === "Active" ? 'btn-warning' : 'btn-success'}`}
                            onClick={() => toggleStatus(client)}
                          >
                            {client.status === "Active" ? "Deactivate" : "Activate"}
                          </button>
                        </div>

                        {/* Quick Action Buttons for Active Members */}
                        {client.status === 'Active' && (
                          <div className="flex space-x-2 mt-2">
                            <button 
                              type="button" 
                              className="btn btn-sm btn-primary flex-1"
                              onClick={() => {
                                localStorage.setItem("pendingPaymentMemberId", String(client.id));
                                navigate('payments');
                              }}
                            >
                              Record Payment
                            </button>
                            <button 
                              type="button" 
                              className="btn btn-sm btn-outline"
                              onClick={() => openWhatsApp(buildReminder(client), client.phone)}
                            >
                              WhatsApp
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                {clients.length === 0 ? (
                  <>
                    <div className="text-6xl mb-4">👥</div>
                    <div className="text-xl font-medium text-gray-900 mb-2">No Members Yet</div>
                    <div className="text-gray-500 mb-6">Add your first gym member to get started</div>
                    <button 
                      type="button" 
                      className="btn btn-primary"
                      onClick={() => { 
                        setEditingClient(null); 
                        setForm({ name:"", email:"", phone:"", planId:"" }); 
                        setIsAddingClient(true); 
                      }}
                    >
                      + Add First Member
                    </button>
                  </>
                ) : (
                  <>
                    <div className="text-4xl mb-4">🔍</div>
                    <div className="text-xl font-medium text-gray-900 mb-2">No Results Found</div>
                    <div className="text-gray-500">Try adjusting your search terms</div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add/Edit Member Modal */}
      {isAddingClient && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">
                {editingClient ? "Edit Member" : "Add New Member"}
              </h2>
            </div>
            
            <div className="modal-body">
              <form onSubmit={(e)=>e.preventDefault()} className="space-y-4">
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <input 
                    className="input" 
                    placeholder="Enter member's full name" 
                    value={form.name} 
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Email Address</label>
                    <input 
                      className="input" 
                      type="email"
                      placeholder="member@example.com" 
                      value={form.email} 
                      onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Phone Number</label>
                    <input 
                      className="input" 
                      type="tel"
                      placeholder="(xxx) xxx-xxxx" 
                      value={form.phone} 
                      onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Membership Plan</label>
                  <select 
                    className="input" 
                    value={form.planId}
                    onChange={e=>setForm(f=>({ ...f, planId:e.target.value }))}
                  >
                    <option value="">Select a plan (optional)</option>
                    {plans.map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} — {formatCurrency(p.price)} / {p.cycleDays||30} days
                      </option>
                    ))}
                  </select>
                  <div className="form-help">
                    Choose a membership plan to automatically set billing schedule
                  </div>
                </div>
              </form>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => setIsAddingClient(false)}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={save}
                disabled={!form.name?.trim()}
              >
                {editingClient ? "Save Changes" : "Add Member"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// --- Reports ---
const Reports = () => (
  <div className="p-4">
    <h1 className="text-2xl font-semibold mb-4">Reports</h1>
    <div className="text-center py-8 text-gray-500">
      <div className="text-4xl mb-2">📊</div>
      <div>Reports Coming Soon</div>
      <div className="text-sm">Revenue and member analytics will be available here.</div>
    </div>
  </div>
);

// --- Settings ---
const Settings = () => {
  const [s, setS] = useState({ 
    membershipFeeDefault: 0, 
    billingCycleDays: 30, 
    dueSoonDays: 3, 
    graceDays: 0 
  });
  
  useEffect(() => {
    (async () => {
      const v = (await (gymStorage.getSetting?.('gymSettings', {}) )) ?? 
                (await (getSettingNamed?.('gymSettings', {}) )) ?? {};
      setS(prev => ({ ...prev, ...v }));
    })();
  }, []);
  
  async function save() {
    await (gymStorage.saveSetting?.('gymSettings', s) ?? saveSettingNamed('gymSettings', s));
    signalChanged('settings');
    alert('Settings saved successfully!');
  }
  
  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      
      <div className="space-y-4 bg-white border rounded-2xl p-4">
        <div className="font-medium">Membership Settings</div>
        
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Default Membership Fee ($)</span>
          <input 
            className="mt-1 border rounded px-3 py-2 w-full" 
            type="number" 
            min="0"
            step="0.01"
            value={s.membershipFeeDefault} 
            onChange={e => setS(v => ({ ...v, membershipFeeDefault: Number(e.target.value || 0) }))}
          />
          <span className="text-xs text-gray-500">Default amount when recording payments</span>
        </label>
        
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Billing Cycle (days)</span>
          <input 
            className="mt-1 border rounded px-3 py-2 w-full" 
            type="number" 
            min="1"
            value={s.billingCycleDays} 
            onChange={e => setS(v => ({ ...v, billingCycleDays: Number(e.target.value || 30) }))}
          />
          <span className="text-xs text-gray-500">How often members are billed</span>
        </label>
        
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Due Soon Threshold (days)</span>
          <input 
            className="mt-1 border rounded px-3 py-2 w-full" 
            type="number" 
            min="0"
            value={s.dueSoonDays} 
            onChange={e => setS(v => ({ ...v, dueSoonDays: Number(e.target.value || 3) }))}
          />
          <span className="text-xs text-gray-500">Show "due soon" when payment is due within this many days</span>
        </label>
        
        <label className="block">
          <span className="text-sm font-medium text-gray-700">Grace Period (days)</span>
          <input 
            className="mt-1 border rounded px-3 py-2 w-full" 
            type="number" 
            min="0"
            value={s.graceDays} 
            onChange={e => setS(v => ({ ...v, graceDays: Number(e.target.value || 0) }))}
          />
          <span className="text-xs text-gray-500">Additional days before marking as overdue</span>
        </label>
        
        <div className="pt-2">
          <button 
            type="button" 
            className="border rounded px-4 py-2 bg-blue-500 text-white hover:bg-blue-600" 
            onClick={save}
          >
            Save Settings
          </button>
        </div>
      </div>
      
      <div className="bg-gray-50 border rounded-2xl p-4">
        <div className="font-medium mb-2">Current Configuration</div>
        <div className="space-y-1 text-sm text-gray-600">
          <div>Default Fee: ${s.membershipFeeDefault?.toFixed(2) || '0.00'}</div>
          <div>Billing Cycle: {s.billingCycleDays || 30} days</div>
          <div>Due Soon Warning: {s.dueSoonDays || 3} days</div>
          <div>Grace Period: {s.graceDays || 0} days</div>
        </div>
      </div>
    </div>
  );
};

// --- Plans (MembershipManagement) ---
const MembershipManagement = () => {
  const [plans, setPlans] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [form, setForm] = useState({ id: "", name: "", price: 0, cycleDays: 30 });

  async function load() {
    const list = await (getAllStore?.('plans') ?? []);
    setPlans(list.sort((a,b) => (a.name||"").localeCompare(b.name||"")));
  }
  
  useEffect(() => { load(); }, []);
  
  useEffect(() => { 
    const onC = () => load(); 
    window.addEventListener('DATA_CHANGED', onC); 
    return () => window.removeEventListener('DATA_CHANGED', onC); 
  }, []);

  async function save() {
    const id = form.id || (crypto.randomUUID?.() || String(Date.now()));
    const rec = { 
      ...form, 
      id, 
      price: Number(form.price || 0), 
      cycleDays: Number(form.cycleDays || 30) 
    };
    await gymStorage.saveData('plans', rec);
    setIsOpen(false); 
    setForm({ id: "", name: "", price: 0, cycleDays: 30 }); 
    signalChanged('plans'); 
    load();
  }
  
  async function edit(p) { 
    setForm(p); 
    setIsOpen(true); 
  }
  
  async function remove(p) { 
    await gymStorage.saveData('plans', { ...p, _deleted: true }); 
    signalChanged('plans'); 
    load(); 
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Membership Plans</h1>
        <button 
          type="button" 
          className="border rounded px-3 py-2 bg-green-500 text-white hover:bg-green-600" 
          onClick={() => { 
            setForm({ id: "", name: "", price: 0, cycleDays: 30 }); 
            setIsOpen(true); 
          }}
        >
          + New Plan
        </button>
      </div>
      
      {plans.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">📋</div>
          <div>No plans yet.</div>
          <div className="text-sm">Create your first membership plan above.</div>
        </div>
      ) : (
        <div className="space-y-2">
          {plans.filter(p => !p._deleted).map(p => (
            <div key={p.id} className="flex items-center justify-between border rounded-xl px-3 py-2 bg-white">
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-xs text-gray-500">
                  ${Number(p.price || 0).toFixed(2)} • {p.cycleDays || 30} days
                </div>
              </div>
              <div className="flex gap-2">
                <button 
                  type="button" 
                  className="text-xs border rounded px-2 py-1 hover:bg-gray-50" 
                  onClick={() => edit(p)}
                >
                  Edit
                </button>
                <button 
                  type="button" 
                  className="text-xs border rounded px-2 py-1 text-red-600 hover:bg-red-50" 
                  onClick={() => remove(p)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isOpen && (
        <div className="fixed inset-0 bg-black/20 z-[999] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-4 w-full max-w-md space-y-3">
            <div className="text-lg font-semibold">{form.id ? "Edit Plan" : "New Plan"}</div>
            <input 
              className="border rounded px-3 py-2 w-full" 
              placeholder="Plan name (e.g., Monthly Membership)" 
              value={form.name} 
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
            <input 
              className="border rounded px-3 py-2 w-full" 
              type="number" 
              min="0"
              step="0.01"
              placeholder="Price ($)" 
              value={form.price} 
              onChange={e => setForm(f => ({ ...f, price: e.target.value }))}
            />
            <input 
              className="border rounded px-3 py-2 w-full" 
              type="number" 
              min="1"
              placeholder="Cycle days" 
              value={form.cycleDays} 
              onChange={e => setForm(f => ({ ...f, cycleDays: e.target.value }))}
            />
            <div className="flex justify-end gap-2 pt-2">
              <button 
                type="button" 
                className="border rounded px-3 py-2 hover:bg-gray-50" 
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="border rounded px-3 py-2 bg-green-500 text-white hover:bg-green-600" 
                onClick={save}
              >
                {form.id ? "Save Changes" : "Create Plan"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Alias for backward compatibility
const PaymentTracking = PaymentComponent;

// Explicit component exports
export {
  Dashboard,
  ClientManagement,
  PaymentTracking,
  MembershipManagement,
  Reports,
  Settings
};

// Default export object for App.js
const Components = {
  Dashboard,
  PaymentTracking,
  ClientManagement,
  MembershipManagement,
  Reports,
  Settings
};

export default Components;
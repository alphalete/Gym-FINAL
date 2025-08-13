import React, { useEffect, useMemo, useState } from "react";
import gymStorage, { getAll as getAllStore, getPlanById, upsertMemberWithPlanSnapshot, getSetting as getSettingNamed, saveSetting as saveSettingNamed } from "./storage";
import gymStorageMain, * as storageNamed from "./storage";
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

// Hook to load members from storage - prevents mockClients issues
function useMembersFromStorage() {
  const [members, setMembers] = useState([]);
  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const data = await (gymStorage?.getAllMembers?.() ?? storageNamed.getAllMembers());
        if (live) setMembers(Array.isArray(data) ? data : []);
      } catch (e) {
        console.error("[useMembersFromStorage] load failed", e);
        if (live) setMembers([]);
      }
    })();
    return () => { live = false; };
  }, []);
  return members;
}

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
  const membersPT = useMembersFromStorage(); // Use hook instead of state for consistency
  const [payments, setPayments] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [isRecordingPayment, setIsRecordingPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');
  const [paidOnDate, setPaidOnDate] = useState(new Date().toISOString().slice(0,10));
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    (async () => {
      const paymentsList = await gymStorage.getAllPayments() || [];
      setPayments(paymentsList);

      // Check for pending payment member (from dashboard navigation)
      const pendingId = localStorage.getItem("pendingPaymentMemberId");
      if (pendingId && membersPT.length > 0) {
        const member = membersPT.find(m => String(m.id) === String(pendingId));
        if (member) {
          setSelectedClient(member);
          setIsRecordingPayment(true);
        }
        localStorage.removeItem("pendingPaymentMemberId");
      }
    })();
  }, [membersPT]);

  // When selecting client, default amount from snapshot
  useEffect(() => {
    if (!selectedClient) return;
    const m = membersPT.find(x => String(x.id) === String(selectedClient.id));
    if (!m) return;
    if (!paymentAmount && m.fee != null) setPaymentAmount(String(m.fee));
  }, [selectedClient, membersPT]);

  async function handlePaymentSubmit() {
    if (!selectedClient || !paymentAmount) return;
    
    const m = membersPT.find(x => String(x.id) === String(selectedClient.id));
    const amountNum = Number(paymentAmount || 0);
    const paidOn = paidOnDate || new Date().toISOString().slice(0, 10);
    
    // Create payment record
    const payRec = { 
      id: crypto.randomUUID?.() || String(Date.now()), 
      memberId: String(m.id), 
      memberName: m.name || 'Unknown',
      amount: amountNum, 
      paidOn,
      planName: m.planName || 'No Plan',
      createdAt: new Date().toISOString()
    };
    
    await gymStorage.savePayment(payRec);

    // Update member with Option A logic
    const nextDue = computeNextDueOptionA(m.nextDue, paidOn, m.cycleDays || 30);
    const updated = { 
      ...m, 
      lastPayment: paidOn, 
      nextDue, 
      status: 'Active', 
      overdue: 0 
    };
    await gymStorage.saveMembers(updated);

    // Notify data changed
    try { 
      window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'payments' })); 
      window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'members' })); 
    } catch {}

    // Reset form
    setIsRecordingPayment(false); 
    setSelectedClient(null); 
    setPaymentAmount('');
    setPaidOnDate(new Date().toISOString().slice(0, 10));
    
    // Reload payments data
    const paymentsList = await gymStorage.getAllPayments() || [];
    setPayments(paymentsList);
  }

  // Filter payments for search
  const filteredPayments = payments.filter(payment =>
    !searchTerm || 
    (payment.memberName || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (payment.planName || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    formatCurrency(payment.amount).includes(searchTerm) ||
    formatDate(payment.paidOn).toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get active clients for payment recording
  const activeClients = membersPT.filter(c => c.status === 'Active' || !c.status);

  // Calculate stats
  const todayISO = new Date().toISOString().slice(0, 10);
  const thisMonth = todayISO.slice(0, 7);
  const monthlyRevenue = payments
    .filter(p => p.paidOn && p.paidOn.slice(0, 7) === thisMonth)
    .reduce((sum, p) => sum + Number(p.amount || 0), 0);

  const todayPayments = payments.filter(p => p.paidOn === todayISO);
  const totalRevenue = payments.reduce((sum, p) => sum + Number(p.amount || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title text-primary">Payment Tracking</h1>
              <p className="page-subtitle">Record payments and track gym revenue</p>
            </div>
            <button 
              type="button" 
              className="btn btn-primary"
              onClick={() => setIsRecordingPayment(true)}
            >
              + Record Payment
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
          <div className="stat-card bg-success text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{formatCurrency(monthlyRevenue)}</div>
                <div className="stat-label text-success-100">This Month</div>
              </div>
              <div className="text-success-200 text-3xl">💰</div>
            </div>
          </div>

          <div className="stat-card bg-primary text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{todayPayments.length}</div>
                <div className="stat-label text-primary-100">Today</div>
              </div>
              <div className="text-primary-200 text-3xl">📅</div>
            </div>
          </div>

          <div className="stat-card bg-info text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{payments.length}</div>
                <div className="stat-label text-info-100">Total Payments</div>
              </div>
              <div className="text-info-200 text-3xl">📊</div>
            </div>
          </div>

          <div className="stat-card bg-warning text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{formatCurrency(totalRevenue)}</div>
                <div className="stat-label text-warning-100">All Time</div>
              </div>
              <div className="text-warning-200 text-3xl">💎</div>
            </div>
          </div>
        </div>

        {/* Search and Payments History */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-primary mr-2">💳</span>
                Payment History ({filteredPayments.length})
              </h3>
              
              {/* Search Bar */}
              <div className="w-80">
                <div className="input-group">
                  <div className="input-group-text">
                    <span>🔍</span>
                  </div>
                  <input
                    type="text"
                    className="input pl-10"
                    placeholder="Search payments..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
            </div>
          </div>
          
          <div className="card-body">
            {filteredPayments.length > 0 ? (
              <div className="space-y-3">
                {filteredPayments
                  .sort((a, b) => new Date(b.paidOn || 0) - new Date(a.paidOn || 0))
                  .map(payment => (
                    <div key={payment.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                      {/* Payment Info */}
                      <div className="flex items-center space-x-4">
                        {/* Amount Badge */}
                        <div className="w-12 h-12 bg-success-100 rounded-full flex items-center justify-center">
                          <span className="text-success-600 font-bold text-sm">💰</span>
                        </div>
                        
                        {/* Details */}
                        <div>
                          <div className="font-medium text-gray-900">
                            {payment.memberName || 'Unknown Member'}
                          </div>
                          <div className="text-sm text-gray-500 flex items-center space-x-2">
                            <span>{payment.planName || 'No Plan'}</span>
                            <span>•</span>
                            <span>{formatDate(payment.paidOn)}</span>
                          </div>
                        </div>
                      </div>
                      
                      {/* Amount and Status */}
                      <div className="text-right">
                        <div className="text-lg font-semibold text-success-600">
                          {formatCurrency(payment.amount)}
                        </div>
                        <span className="badge badge-success">Paid</span>
                      </div>
                    </div>
                  ))
                }
              </div>
            ) : (
              <div className="text-center py-12">
                {payments.length === 0 ? (
                  <>
                    <div className="text-6xl mb-4">💳</div>
                    <div className="text-xl font-medium text-gray-900 mb-2">No Payments Yet</div>
                    <div className="text-gray-500 mb-6">Record your first payment to start tracking revenue</div>
                    <button 
                      type="button" 
                      className="btn btn-primary"
                      onClick={() => setIsRecordingPayment(true)}
                    >
                      + Record First Payment
                    </button>
                  </>
                ) : (
                  <>
                    <div className="text-4xl mb-4">🔍</div>
                    <div className="text-xl font-medium text-gray-900 mb-2">No Payments Match Your Search</div>
                    <div className="text-gray-500">Try adjusting your search terms</div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Record Payment Modal */}
      {isRecordingPayment && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">Record Payment</h2>
            </div>
            
            <div className="modal-body">
              <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
                <div className="form-group">
                  <label className="form-label">Select Member *</label>
                  <select 
                    className="input"
                    value={selectedClient?.id || ''}
                    onChange={e => {
                      const client = membersPT.find(c => c.id === e.target.value);
                      setSelectedClient(client || null);
                    }}
                    required
                  >
                    <option value="">Choose a member...</option>
                    {activeClients.map(c => (
                      <option key={c.id} value={c.id}>
                        {c.name} - {c.planName || 'No Plan'} - {formatCurrency(c.fee || 0)}
                      </option>
                    ))}
                  </select>
                  <div className="form-help">Only active members are shown</div>
                </div>

                {selectedClient && (
                  <div className="bg-primary-50 rounded-lg p-4">
                    <div className="text-sm font-medium text-primary-800 mb-2">Member Details:</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-primary-600">Plan:</span> {selectedClient.planName || 'None'}
                      </div>
                      <div>
                        <span className="text-primary-600">Current Due:</span> {formatDate(selectedClient.nextDue) || 'Not set'}
                      </div>
                      <div>
                        <span className="text-primary-600">Regular Fee:</span> {formatCurrency(selectedClient.fee || 0)}
                      </div>
                      <div>
                        <span className="text-primary-600">Cycle:</span> {selectedClient.cycleDays || 30} days
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Payment Amount *</label>
                    <div className="input-group">
                      <div className="input-group-text">TT$</div>
                      <input 
                        type="number" 
                        step="0.01"
                        min="0"
                        className="input pl-12"
                        placeholder="0.00"
                        value={paymentAmount}
                        onChange={e => setPaymentAmount(e.target.value)}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Payment Date *</label>
                    <input 
                      type="date"
                      className="input"
                      value={paidOnDate}
                      onChange={e => setPaidOnDate(e.target.value)}
                      max={new Date().toISOString().slice(0, 10)}
                      required
                    />
                  </div>
                </div>

                {/* Payment Preview */}
                {selectedClient && paymentAmount && (
                  <div className="bg-success-50 rounded-lg p-4">
                    <div className="text-sm font-medium text-success-800 mb-2">Payment Preview:</div>
                    <div className="text-sm text-success-700">
                      After this payment, {selectedClient.name}'s next due date will be:{' '}
                      <span className="font-medium">
                        {formatDate(computeNextDueOptionA(selectedClient.nextDue, paidOnDate, selectedClient.cycleDays || 30))}
                      </span>
                    </div>
                  </div>
                )}
              </form>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-outline" 
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
                className="btn btn-primary" 
                onClick={handlePaymentSubmit}
                disabled={!selectedClient || !paymentAmount}
              >
                Record Payment
              </button>
            </div>
          </div>
        </div>
      )}
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
    <div className="min-h-screen bg-slate-50">
      {/* Header Section */}
      <div className="bg-card shadow-sm border-b">
        <div className="container px-4 sm:px-6 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-gray-900">Dashboard</h1>
              <p className="text-sm md:text-base text-gray-500 leading-6">Welcome back! Here's what's happening at your gym today.</p>
            </div>
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <button 
                type="button" 
                className="btn btn-primary w-full md:w-auto"
                onClick={() => navigate('payments')}
              >
                + Record Payment
              </button>
              <button 
                type="button" 
                className="btn btn-secondary w-full md:w-auto"
                onClick={() => navigate('clients')}
              >
                + Add Member
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container px-4 sm:px-6 py-4 sm:py-6">
        {/* KPI Cards Grid - Polished GoGym4U Style */}
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4 mb-6">
          {/* Active Members */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-primary/10 text-primary">
              <span className="text-xl">👥</span>
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{activeCount}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Active</div>
            </div>
          </div>

          {/* Due Soon */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-warning/10 text-warning">
              <span className="text-xl">⏰</span>
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{dueSoon.length}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Due Soon</div>
            </div>
          </div>

          {/* Overdue */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-danger/10 text-danger">
              <span className="text-xl">⚠️</span>
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{overdue.length}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Overdue</div>
            </div>
          </div>

          {/* Revenue */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-success/10 text-success">
              <span className="text-xl">💰</span>
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{formatCurrency(revenueMTD)}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Revenue</div>
            </div>
          </div>
        </div>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="mb-6">
            <div className="bg-card rounded-xl shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <span className="text-warning mr-2">⚠️</span>
                  Payment Alerts ({alerts.length})
                </h3>
              </div>
              <div className="p-4">
                <div className="space-y-3">
                  {alerts.map(member => {
                    const status = getPaymentStatus(member);
                    const isOverdue = overdue.includes(member);
                    
                    return (
                      <div key={member.id} className="bg-card rounded-xl shadow-sm px-3 py-2 md:p-3 flex items-center justify-between hover:shadow-md transition-shadow cursor-pointer">
                        <div className="flex items-center space-x-3">
                          {/* Avatar */}
                          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600">
                            {getInitials(member.name)}
                          </div>
                          
                          {/* Member Info */}
                          <div>
                            <div className="font-medium text-gray-900">{member.name || "(No name)"}</div>
                            <div className="text-sm text-gray-500">
                              {member.planName ? `${member.planName} • ${formatCurrency(member.fee)}` : "No plan"} • 
                              <span className={isOverdue ? 'text-danger font-medium ml-1' : 'text-warning font-medium ml-1'}>
                                Due: {formatDate(member.nextDue, false)}
                              </span>
                            </div>
                          </div>
                        </div>
                        
                        {/* Status Badge and Actions */}
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                            isOverdue ? 'bg-danger/10 text-danger' : 'bg-warning/10 text-warning'
                          }`}>
                            {status.label}
                          </span>
                          <button 
                            type="button" 
                            className="p-2 rounded-lg hover:bg-slate-50 transition-colors" 
                            onClick={() => goRecordPayment(member)}
                            aria-label="Record payment"
                          >
                            <span className="text-lg">💳</span>
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Recent Payments */}
          <div className="bg-card rounded-xl shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-primary mr-2">💳</span>
                Recent Payments
              </h3>
            </div>
            <div className="p-4">
              {payments.length > 0 ? (
                <div className="space-y-3">
                  {payments.slice(-5).reverse().map(payment => (
                    <div key={payment.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-success/10 rounded-full flex items-center justify-center">
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
          <div className="bg-card rounded-xl shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <span className="text-info mr-2">📊</span>
                Quick Stats
              </h3>
            </div>
            <div className="p-4">
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
                  // Compute single status badge (no duplicates)
                  const status = (client?.status || client?.active) ? 'ACTIVE' : 'INACTIVE';
                  const StatusBadge = () => (
                    status === 'ACTIVE'
                      ? <span className="badge-active">ACTIVE</span>
                      : <span className="badge-inactive">INACTIVE</span>
                  );
                  
                  return (
                    <div key={client.id} className="card">
                      <div className="card-body">
                        {/* Top row: avatar + name + ONE status badge */}
                        <div className="flex items-center gap-3">
                          <div className="h-12 w-12 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
                            {(client?.name || '').split(' ').map(s=>s[0]).join('').slice(0,2) || 'MM'}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="text-base font-semibold">{client?.name || 'Member'}</h3>
                              <StatusBadge />
                            </div>
                            <div className="text-sm text-slate-500">{client?.email}</div>
                            <div className="text-sm text-slate-500">{client?.phone}</div>
                          </div>
                        </div>

                        {/* Plan chip (if present) */}
                        {client?.planName && (
                          <div className="mt-3">
                            <span className="badge-warning">{client.planName}</span>
                          </div>
                        )}

                        {/* Actions (normalized buttons) */}
                        <div className="mt-4 grid grid-cols-2 gap-3 sm:flex sm:flex-wrap">
                          <button 
                            className="btn-secondary" 
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
                            className="btn-warning" 
                            onClick={() => toggleStatus(client)}
                          >
                            {client.status === "Active" ? "Deactivate" : "Activate"}
                          </button>
                          <button 
                            className="btn-primary" 
                            onClick={() => {
                              localStorage.setItem("pendingPaymentMemberId", String(client.id));
                              navigate('payments');
                            }}
                          >
                            Record Payment
                          </button>
                          <button 
                            className="btn-ghost" 
                            onClick={() => openWhatsApp(buildReminder(client), client.phone)}
                          >
                            WhatsApp
                          </button>
                        </div>
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
const Reports = () => {
  const membersR = useMembersFromStorage();
  const [payments, setPayments] = useState([]);
  
  useEffect(() => {
    (async () => {
      try {
        const paymentsList = await (gymStorage?.getAllPayments?.() ?? storageNamed.getAllPayments?.() ?? []);
        setPayments(paymentsList);
      } catch (e) {
        console.error("[Reports] Failed to load payments:", e);
        setPayments([]);
      }
    })();
  }, []);
  
  const totalRevenue = payments.reduce((sum, p) => sum + Number(p.amount || 0), 0);
  const activeMembers = membersR.filter(m => m.payment_status !== 'cancelled').length;
  const totalMembers = membersR.length;
  
  return (
    <div className="p-4">
      <h1 className="text-2xl font-semibold mb-4">Reports</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white border rounded-2xl p-4">
          <div className="text-2xl font-bold text-primary">{totalMembers}</div>
          <div className="text-sm text-gray-600">Total Members</div>
        </div>
        <div className="bg-white border rounded-2xl p-4">
          <div className="text-2xl font-bold text-success">{activeMembers}</div>
          <div className="text-sm text-gray-600">Active Members</div>
        </div>
        <div className="bg-white border rounded-2xl p-4">
          <div className="text-2xl font-bold text-primary">{formatCurrency(totalRevenue)}</div>
          <div className="text-sm text-gray-600">Total Revenue</div>
        </div>
      </div>
      
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-2">📊</div>
        <div>Detailed Reports Coming Soon</div>
        <div className="text-sm">Advanced analytics and reporting features will be available here.</div>
      </div>
    </div>
  );
};

// --- Settings ---
const Settings = () => {
  const [s, setS] = useState({ 
    membershipFeeDefault: 0, 
    billingCycleDays: 30, 
    dueSoonDays: 3, 
    graceDays: 0 
  });
  const [loading, setLoading] = useState(true);
  const [storageStats, setStorageStats] = useState(null);
  
  useEffect(() => { 
    (async () => {
      try {
        // Sequential loading to avoid double IndexedDB calls
        const saved = await (gymStorage?.getSetting?.('gymSettings', s) ?? 
                             getSettingNamed?.('gymSettings', s) ?? s);
        setS(saved);
        
        // Optionally get storage stats if available
        const stats = await gymStorage?.getStorageStats?.();
        if (stats) setStorageStats(stats);
      } catch (e) { 
        console.error("Settings load error", e); 
      } finally { 
        setLoading(false); 
      }
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
      
      <div className="card">
        <div className="card-body">
          <div className="font-medium mb-2">Current Configuration</div>
          <div className="space-y-1 text-sm text-gray-600">
            <div>Default Fee: ${s.membershipFeeDefault?.toFixed(2) || '0.00'}</div>
            <div>Billing Cycle: {s.billingCycleDays || 30} days</div>
            <div>Due Soon Warning: {s.dueSoonDays || 3} days</div>
            <div>Grace Period: {s.graceDays || 0} days</div>
          </div>
        </div>
      </div>
    </div>
  );
};

// --- Plans (MembershipManagement) ---
const MembershipManagement = () => {
  const [plans, setPlans] = useState([]);
  const allClientsMM = useMembersFromStorage(); // Use hook instead of state
  const [isOpen, setIsOpen] = useState(false);
  const [form, setForm] = useState({ id: "", name: "", price: 0, cycleDays: 30, description: "" });
  const [searchTerm, setSearchTerm] = useState("");

  async function load() {
    try {
      const list = await (getAllStore?.('plans') ?? []);
      setPlans(list.filter(p => !p._deleted).sort((a,b) => (a.name||"").localeCompare(b.name||"")));
    } catch (e) {
      console.error('Plans load error:', e);
      setPlans([]);
    }
  }
  
  useEffect(() => { load(); }, []);
  
  useEffect(() => { 
    const onC = () => load(); 
    window.addEventListener('DATA_CHANGED', onC); 
    return () => window.removeEventListener('DATA_CHANGED', onC); 
  }, []);

  async function save() {
    if (!form.name?.trim()) {
      alert('Plan name is required');
      return;
    }

    const id = form.id || (crypto.randomUUID?.() || String(Date.now()));
    const rec = { 
      ...form, 
      id,
      name: form.name.trim(),
      price: Number(form.price || 0), 
      cycleDays: Number(form.cycleDays || 30),
      description: form.description?.trim() || '',
      createdAt: form.id ? form.createdAt : new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    await gymStorage.saveData('plans', rec);
    setIsOpen(false); 
    setForm({ id: "", name: "", price: 0, cycleDays: 30, description: "" }); 
    signalChanged('plans'); 
    load();
  }
  
  async function edit(p) { 
    setForm({
      id: p.id,
      name: p.name || "",
      price: p.price || 0,
      cycleDays: p.cycleDays || 30,
      description: p.description || ""
    }); 
    setIsOpen(true); 
  }
  
  async function remove(p) {
    const membersCount = allClientsMM.filter(m => m.planId === p.id).length;
    
    if (membersCount > 0) {
      if (!window.confirm(`This plan has ${membersCount} members. Are you sure you want to delete it? This will not affect existing members but they won't be able to select this plan for new signups.`)) {
        return;
      }
    } else {
      if (!window.confirm(`Are you sure you want to delete the "${p.name}" plan?`)) {
        return;
      }
    }

    await gymStorage.saveData('plans', { ...p, _deleted: true }); 
    signalChanged('plans'); 
    load(); 
  }

  // Get member count for each plan
  const getPlansWithMemberCount = () => {
    return plans.map(plan => ({
      ...plan,
      memberCount: allClientsMM.filter(member => member.planId === plan.id).length
    }));
  };

  // Filter plans based on search
  const filteredPlans = getPlansWithMemberCount().filter(plan => 
    !searchTerm || 
    (plan.name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    (plan.description || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
    formatCurrency(plan.price).includes(searchTerm)
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="page-title text-primary">Membership Plans</h1>
              <p className="page-subtitle">Create and manage gym membership plans and pricing</p>
            </div>
            <button 
              type="button" 
              className="btn btn-primary"
              onClick={() => { 
                setForm({ id: "", name: "", price: 0, cycleDays: 30, description: "" }); 
                setIsOpen(true); 
              }}
            >
              + New Plan
            </button>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Search and Quick Stats */}
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
                  placeholder="Search plans by name, description, or price..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="lg:col-span-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="stat-card bg-success text-white text-center">
                <div className="stat-value">{plans.length}</div>
                <div className="stat-label text-success-100">Total Plans</div>
              </div>
              <div className="stat-card bg-primary text-white text-center">
                <div className="stat-value">{allClientsMM.filter(m => m.planId).length}</div>
                <div className="stat-label text-primary-100">Enrolled</div>
              </div>
            </div>
          </div>
        </div>

        {/* Plans List */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <span className="text-primary mr-2">📋</span>
              Membership Plans ({filteredPlans.length})
            </h3>
          </div>
          <div className="card-body">
            {filteredPlans.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {filteredPlans.map(plan => (
                  <div key={plan.id} className="card hover:shadow-md transition-shadow duration-200 relative">
                    <div className="card-body">
                      {/* Plan Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 mb-1">{plan.name}</h3>
                          {plan.description && (
                            <p className="text-sm text-gray-600 mb-3">{plan.description}</p>
                          )}
                        </div>
                        
                        {/* Member count badge */}
                        {plan.memberCount > 0 && (
                          <span className="badge badge-info ml-2">
                            {plan.memberCount} {plan.memberCount === 1 ? 'member' : 'members'}
                          </span>
                        )}
                      </div>

                      {/* Pricing */}
                      <div className="bg-primary-50 rounded-lg p-4 mb-4">
                        <div className="text-center">
                          <div className="text-3xl font-bold text-primary mb-1">
                            {formatCurrency(plan.price)}
                          </div>
                          <div className="text-sm text-primary-600">
                            Every {plan.cycleDays} {plan.cycleDays === 1 ? 'day' : 'days'}
                          </div>
                        </div>
                      </div>

                      {/* Plan Details */}
                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Billing Cycle:</span>
                          <span className="font-medium">{plan.cycleDays} days</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Monthly Rate:</span>
                          <span className="font-medium">
                            {formatCurrency((plan.price / plan.cycleDays) * 30)}
                          </span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Created:</span>
                          <span className="font-medium">
                            {plan.createdAt ? formatDate(plan.createdAt.split('T')[0]) : 'Unknown'}
                          </span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex space-x-2">
                        <button 
                          type="button" 
                          className="btn btn-sm btn-outline flex-1"
                          onClick={() => edit(plan)}
                        >
                          Edit Plan
                        </button>
                        <button 
                          type="button" 
                          className="btn btn-sm btn-danger"
                          onClick={() => remove(plan)}
                        >
                          Delete
                        </button>
                      </div>

                      {/* Popular badge for plans with most members */}
                      {plan.memberCount > 0 && plan.memberCount === Math.max(...getPlansWithMemberCount().map(p => p.memberCount)) && (
                        <div className="absolute -top-2 -right-2">
                          <span className="badge badge-success">Popular</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                {plans.length === 0 ? (
                  <>
                    <div className="text-6xl mb-4">📋</div>
                    <div className="text-xl font-medium text-gray-900 mb-2">No Plans Yet</div>
                    <div className="text-gray-500 mb-6">Create your first membership plan to start managing subscriptions</div>
                    <button 
                      type="button" 
                      className="btn btn-primary"
                      onClick={() => { 
                        setForm({ id: "", name: "", price: 0, cycleDays: 30, description: "" }); 
                        setIsOpen(true); 
                      }}
                    >
                      + Create First Plan
                    </button>
                  </>
                ) : (
                  <>
                    <div className="text-4xl mb-4">🔍</div>
                    <div className="text-xl font-medium text-gray-900 mb-2">No Plans Match Your Search</div>
                    <div className="text-gray-500">Try adjusting your search terms</div>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add/Edit Plan Modal */}
      {isOpen && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2 className="modal-title">
                {form.id ? "Edit Membership Plan" : "New Membership Plan"}
              </h2>
            </div>
            
            <div className="modal-body">
              <form onSubmit={(e)=>e.preventDefault()} className="space-y-4">
                <div className="form-group">
                  <label className="form-label">Plan Name *</label>
                  <input 
                    className="input" 
                    placeholder="e.g., Monthly Membership, VIP Access, Student Plan" 
                    value={form.name} 
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea
                    className="input"
                    rows="2"
                    placeholder="Brief description of what this plan includes..."
                    value={form.description}
                    onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
                  />
                  <div className="form-help">Optional: Help members understand what this plan offers</div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="form-group">
                    <label className="form-label">Price *</label>
                    <div className="input-group">
                      <div className="input-group-text">TT$</div>
                      <input 
                        className="input pl-12"
                        type="number" 
                        min="0"
                        step="0.01"
                        placeholder="0.00" 
                        value={form.price} 
                        onChange={e => setForm(f => ({ ...f, price: e.target.value }))}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Billing Cycle *</label>
                    <div className="input-group">
                      <input 
                        className="input pr-16"
                        type="number" 
                        min="1"
                        placeholder="30" 
                        value={form.cycleDays} 
                        onChange={e => setForm(f => ({ ...f, cycleDays: e.target.value }))}
                        required
                      />
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <span className="text-gray-500 text-sm">days</span>
                      </div>
                    </div>
                    <div className="form-help">How often members are billed</div>
                  </div>
                </div>

                {/* Preview */}
                {form.price > 0 && form.cycleDays > 0 && (
                  <div className="card">
                    <div className="card-body">
                      <div className="text-sm font-medium text-gray-700 mb-1">Preview:</div>
                      <div className="text-sm text-gray-600">
                        Members pay {formatCurrency(form.price)} every {form.cycleDays} days
                        {form.cycleDays !== 30 && (
                          <span className="text-gray-500">
                            {' '}(≈ {formatCurrency((Number(form.price) / Number(form.cycleDays)) * 30)} monthly)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </form>
            </div>

            <div className="modal-footer">
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </button>
              <button 
                type="button" 
                className="btn btn-primary" 
                onClick={save}
                disabled={!form.name?.trim() || !form.price || !form.cycleDays}
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

// Sidebar Component for Router-based navigation
const Sidebar = () => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const navItems = [
    { path: '/dashboard', icon: '📊', label: 'Dashboard' },
    { path: '/members', icon: '👥', label: 'Members' },
    { path: '/plans', icon: '📋', label: 'Plans' },
    { path: '/payments', icon: '💳', label: 'Payments' },
    { path: '/reports', icon: '📈', label: 'Reports' },
    { path: '/settings', icon: '⚙️', label: 'Settings' }
  ];

  const isActive = (path) => window.location.hash === `#${path}`;

  return (
    <nav className={`hidden md:block fixed left-0 top-0 h-full bg-white shadow-lg z-40 transition-all duration-300 group ${
      isExpanded ? 'w-56' : 'w-16 hover:w-56'
    }`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className={`transition-opacity duration-300 ${isExpanded ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
            <h1 className="text-lg font-bold text-primary whitespace-nowrap">GoGym4U</h1>
            <p className="text-xs text-gray-500 whitespace-nowrap">Gym Management</p>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-lg hover:bg-soft transition-colors"
            aria-label="Toggle sidebar"
          >
            <span className="text-lg">☰</span>
          </button>
        </div>
      </div>

      {/* Navigation Items */}
      <div className="flex-1 py-6 overflow-hidden">
        <ul className="space-y-2 px-3">
          {navItems.map((item) => (
            <li key={item.path}>
              <a
                href={`#${item.path}`}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 cursor-pointer ${
                  isActive(item.path)
                    ? 'text-primary-600 font-semibold border-r-2 border-primary-600'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                <span className="w-5 h-5 shrink-0 text-xl flex items-center justify-center">{item.icon}</span>
                <span className={`whitespace-nowrap transition-opacity duration-300 ${
                  isExpanded ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
                }`}>
                  {item.label}
                </span>
              </a>
            </li>
          ))}
        </ul>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className={`text-xs text-gray-500 text-center transition-opacity duration-300 ${
          isExpanded ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        }`}>
          <div className="whitespace-nowrap">GoGym4U v2.0</div>
        </div>
      </div>
    </nav>
  );
};

// Simple Login Form Component
const LoginForm = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    // Simple validation - in real app, authenticate with backend
    if (credentials.username && credentials.password) {
      onLogin();
    } else {
      alert('Please enter username and password');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            GoGym4U Login
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div>
            <input
              type="text"
              required
              className="input"
              placeholder="Username"
              value={credentials.username}
              onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
            />
          </div>
          <div>
            <input
              type="password"
              required
              className="input"
              placeholder="Password"
              value={credentials.password}
              onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
            />
          </div>
          <div>
            <button type="submit" className="btn btn-primary w-full">
              Sign In
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Install Prompt Component  
const InstallPrompt = () => {
  const [showPrompt, setShowPrompt] = useState(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setShowPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
  }, []);

  if (!showPrompt) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 bg-primary text-white p-4 rounded-lg shadow-lg z-50">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">Install GoGym4U</p>
          <p className="text-sm text-primary-100">Add to home screen for quick access</p>
        </div>
        <button
          onClick={() => setShowPrompt(false)}
          className="btn btn-outline text-white border-white ml-4"
        >
          Install
        </button>
      </div>
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
  Settings,
  Sidebar,
  LoginForm,
  InstallPrompt
};

// Default export object for App.js
const Components = {
  Dashboard,
  PaymentTracking,
  ClientManagement,
  MembershipManagement,
  Reports,
  Settings,
  Sidebar,
  LoginForm,
  InstallPrompt
};

export default Components;
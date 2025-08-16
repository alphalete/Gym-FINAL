import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import useMembersFromStorage from "./hooks/useMembersFromStorage";
import useMembersRepo from "./hooks/useMembersRepo";
import storageFacade from "./storage.facade";
import gymStorage, { getSetting as getSettingNamed, saveSetting as saveSettingNamed } from "./storage";
import gymStorageMain, * as storageNamed from "./storage";
import { advanceNextDueByCycles } from './utils/date';
import { 
  computeNextDueOptionA, 
  formatCurrency,
  formatDate,
  getPaymentStatus,
  getInitials
} from './utils/common';
// Import Icon components for consistent iconography
import { Icon, StatIcon, ActionIcon } from './components/Icons';
import { PencilIcon, TrashIcon, ChatBubbleLeftRightIcon, BanknotesIcon, ClockIcon, ArrowRightIcon, EnvelopeIcon } from '@heroicons/react/24/outline';
// Import Skeleton Loaders
import { DashboardSkeleton, ReportsSkeleton } from './components/SkeletonLoader';

// Hook to load members from storage

// NOTE: Helper functions removed - using repository system (members.repo.js) instead

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
  const { members: membersPT, setMembers: setMembersPT, loading: loadingPT, refresh: refreshMembers } = useMembersRepo();
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
          console.log('🎯 Selected member for payment:', {
            name: member.name,
            plan: member.membership_type,
            fee: member.monthly_fee,
            nextDue: member.nextDue || member.dueDate,
            startDate: member.start_date
          });
          setSelectedClient(member);
          setIsRecordingPayment(true);
        }
        localStorage.removeItem("pendingPaymentMemberId");
      }

      // Auto-open payment modal if requested from dashboard
      const autoOpen = localStorage.getItem("autoOpenRecordPayment");
      if (autoOpen === "true") {
        localStorage.removeItem("autoOpenRecordPayment"); // Clean up
        setIsRecordingPayment(true);
      }
    })();
  }, [membersPT]);

  // When selecting client, default amount from enhanced member data
  useEffect(() => {
    if (!selectedClient) return;
    const m = membersPT.find(x => String(x.id) === String(selectedClient.id));
    if (!m) return;
    // Use monthly_fee from enhanced member data
    const memberFee = m.monthly_fee || m.fee;
    if (!paymentAmount && memberFee != null) {
      setPaymentAmount(String(memberFee));
      console.log('💰 Set payment amount from member data:', memberFee);
    }
  }, [selectedClient, membersPT]);

  // Render loading state without early return to avoid hook issues
  if (loadingPT) {
    return <div className="p-4">Loading payments…</div>;
  }

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

  // Get active clients for payment recording (with safety guard)
  const membersList = Array.isArray(membersPT) ? membersPT : [];
  const activeClients = membersList.filter(c => c.status === 'Active' || !c.status);

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
              <h1 className="page-title text-indigo-600">Payment Tracking</h1>
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
              <StatIcon name="💰" color="success" />
            </div>
          </div>

          <div className="stat-card bg-indigo-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{todayPayments.length}</div>
                <div className="stat-label text-indigo-100">Today</div>
              </div>
              <div className="text-indigo-200 text-3xl">
                <Icon name="📅" size="2xl" />
              </div>
            </div>
          </div>

          <div className="stat-card bg-info text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{payments.length}</div>
                <div className="stat-label text-info-100">Total Payments</div>
              </div>
              <div className="text-info-200 text-3xl">
                <Icon name="📊" size="2xl" />
              </div>
            </div>
          </div>

          <div className="stat-card bg-warning text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{formatCurrency(totalRevenue)}</div>
                <div className="stat-label text-warning-100">All Time</div>
              </div>
              <div className="text-warning-200 text-3xl">
                <Icon name="💎" size="2xl" />
              </div>
            </div>
          </div>
        </div>

        {/* Search and Payments History */}
        <div className="card">
          <div className="card-header">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <ActionIcon name="💳" className="text-indigo-600 mr-2" />
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
                          <ActionIcon name="💰" className="text-success-600" />
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
                    <div className="text-6xl mb-4">
                      <div className="flex justify-center">
                        <Icon name="💳" size="2xl" className="text-gray-400" />
                      </div>
                    </div>
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
                      const client = membersPT.find(c => c.id === e.target.value || c._id === e.target.value || c.uuid === e.target.value);
                      setSelectedClient(client || null);
                      console.log('💳 Selected client for payment:', {
                        name: client?.name,
                        plan: client?.membership_type,
                        fee: client?.monthly_fee,
                        nextDue: client?.nextDue || client?.dueDate
                      });
                    }}
                    required
                  >
                    <option value="">Choose a member...</option>
                    {activeClients.map(c => {
                      const id = c.id || c._id || c.uuid;
                      const plan = c.membership_type || 'No Plan';
                      const fee = c.monthly_fee || c.fee || 0;
                      return (
                        <option key={id} value={id}>
                          {c.name} - {plan} - TTD {fee}
                        </option>
                      );
                    })}
                  </select>
                  <div className="form-help">Only active members are shown</div>
                </div>

                {selectedClient && (
                  <div className="bg-indigo-50 rounded-lg p-4">
                    <div className="text-sm font-medium text-indigo-800 mb-2">Member Details:</div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-indigo-600">Plan:</span> {selectedClient.membership_type || 'No Plan'}
                      </div>
                      <div>
                        <span className="text-indigo-600">Next Due:</span> {selectedClient.nextDue || selectedClient.dueDate || 'Not set'}
                      </div>
                      <div>
                        <span className="text-indigo-600">Monthly Fee:</span> TTD {selectedClient.monthly_fee || selectedClient.fee || 0}
                      </div>
                      <div>
                        <span className="text-indigo-600">Status:</span> {selectedClient.status || 'Active'}
                      </div>
                      <div>
                        <span className="text-indigo-600">Email:</span> {selectedClient.email || 'Not provided'}
                      </div>
                      <div>
                        <span className="text-indigo-600">Phone:</span> {selectedClient.phone || 'Not provided'}
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
                  
                  // Navigate back to where user came from
                  const origin = localStorage.getItem("pendingPaymentOrigin");
                  if (origin) {
                    localStorage.removeItem("pendingPaymentOrigin"); // Clean up
                    window.navigateToTab?.(origin);
                  }
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
  const nav = useNavigate();
  const [clients, setClients] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const todayISO = new Date().toISOString().slice(0,10);

  // Use the same repository system as Members page
  async function loadDashboard() {
    try {
      setLoading(true);
      console.log('[Dashboard] Starting data load...');
      
      // Load from backend first, fallback to local storage
      let m = [];
      try {
        const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
        if (backendUrl) {
          const response = await fetch(`${backendUrl}/api/clients`);
          if (response.ok) {
            m = await response.json();
            console.log(`[Dashboard] ✅ Loaded ${m.length} members from backend`);
          }
        }
      } catch (backendError) {
        console.warn('[Dashboard] ⚠️ Backend failed, using local storage:', backendError.message);
        m = await (gymStorage.getAllMembers?.() ?? []);
      }
      
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
    
    // Also listen for member-specific changes to refresh dashboard stats
    const onMemberChanged = (event) => {
      if (event.detail && (event.detail.includes('member') || event.detail === 'payments')) {
        console.log('[Dashboard] Member/payment data changed, refreshing...');
        loadDashboard();
      }
    };
    window.addEventListener('DATA_CHANGED', onMemberChanged);
    
    return () => {
      window.removeEventListener('DATA_CHANGED', onChanged);
      window.removeEventListener('DATA_CHANGED', onMemberChanged);
      document.removeEventListener('visibilitychange', onVisible);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  // Show Alphalete Athletics loading indicator
  if (loading) {
    return <DashboardSkeleton />;
  }

  // Calculate KPIs with Alphalete Athletics logic
  // Safety guards for arrays
  const clientsList = Array.isArray(clients) ? clients : [];
  const paymentsList = Array.isArray(payments) ? payments : [];
  
  const activeCount = clientsList.filter(m => (m.status || "Active") === "Active").length;
  const totalCount = clientsList.length;
  
  // Due today calculation
  const dueToday = clientsList.filter(m => {
    if (m.status !== "Active") return false;
    return m.nextDue === todayISO;
  });
  
  // Overdue calculation
  const overdue = clientsList.filter(m => {
    if (m.status !== "Active") return false;
    const due = m.nextDue;
    if (!due) return false;
    return new Date(due) < new Date(todayISO);
  });

  // Due soon (next 3 days)
  const dueSoon = clientsList.filter(m => {
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
  const revenueMTD = paymentsList
    .filter(p => p.paidOn && p.paidOn.slice(0,7) === todayISO.slice(0,7))
    .reduce((sum,p)=> sum + Number(p.amount||0), 0);

  function goRecordPayment(m) {
    localStorage.setItem("pendingPaymentMemberId", String(m.id));
    nav('/payments');
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
                onClick={() => {
                  localStorage.setItem("pendingPaymentOrigin", "dashboard");
                  localStorage.setItem("autoOpenRecordPayment", "true");
                  window.navigateToTab?.('payments');
                }}
              >
                + Record Payment
              </button>
              <button 
                type="button" 
                className="btn btn-secondary w-full md:w-auto"
                onClick={() => {
                  // Navigate to members and auto-open the add form
                  localStorage.setItem("autoOpenAddMember", "true");
                  localStorage.setItem("addMemberOrigin", "dashboard");
                  window.navigateToTab?.('members');
                }}
              >
                + Add Member
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container px-4 sm:px-6 py-4 sm:py-6">
        {/* KPI Cards Grid - Polished Alphalete Athletics Style */}
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4 mb-6">
          {/* Active Members */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-indigo-600/10 text-indigo-600">
              <ActionIcon name="👥" size="lg" />
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{activeCount}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Active</div>
            </div>
          </div>

          {/* Due Soon */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-warning/10 text-warning">
              <ActionIcon name="🕐" size="lg" />
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{dueSoon.length}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Due Soon</div>
            </div>
          </div>

          {/* Overdue */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-danger/10 text-danger">
              <ActionIcon name="⚠️" size="lg" />
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{overdue.length}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Overdue</div>
            </div>
          </div>

          {/* Revenue */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-success/10 text-success">
              <ActionIcon name="💰" size="lg" />
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
                  <ActionIcon name="⚠️" className="text-warning mr-2" />
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
                            <ActionIcon name="💳" size="lg" />
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
                <ActionIcon name="💳" className="text-indigo-600 mr-2" />
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
                          <ActionIcon name="💰" className="text-success" size="sm" />
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
                  <div className="text-4xl mb-2">
                    <div className="flex justify-center">
                      <Icon name="💳" size="2xl" className="text-gray-400" />
                    </div>
                  </div>
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
                <ActionIcon name="📊" className="text-info mr-2" />
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
          <button type="button" className="text-xs rounded-lg border px-2 py-1" onClick={()=> console.log('View plans')}>View</button>
        </div>
      ))}
    </div>
  );
};

// --- Dashboard component continues here ---

// --- Members (ClientManagement) ---
function ClientManagement() {
  const { members, setMembers, loading, error, refresh, repo } = useMembersRepo();
  const [showAddForm, setShowAddForm] = React.useState(false);

  const list = Array.isArray(members) ? members : [];

  // Auto-open add form if requested from dashboard
  React.useEffect(() => {
    const autoOpen = localStorage.getItem("autoOpenAddMember");
    if (autoOpen === "true") {
      localStorage.removeItem("autoOpenAddMember"); // Clean up
      setShowAddForm(true);
    }
  }, []);

  // ADD handlers (use repo; ensure buttons in forms are type="button"):
  const onAddOrUpdateMember = async (partialOrFull) => {
    try {
      await repo.upsertMember(partialOrFull);
      await refresh(); // Refresh from backend to get latest data
      
      // Trigger dashboard refresh
      window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'member_added' }));
    } catch (e) {
      console.error("save member failed", e);
      alert("Could not save member. Please try again.");
    }
  };

  const onDeleteMember = async (id) => {
    console.log('🔥 DELETE MEMBER CALLED:', id);
    try {
      console.log('🔥 Calling repo.removeMember...');
      await repo.removeMember(id);
      console.log('🔥 repo.removeMember completed, refreshing...');
      await refresh(); // Refresh from backend to get latest data
      
      console.log('🔥 Triggering dashboard refresh event...');
      // Trigger dashboard refresh
      window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'member_deleted' }));
      console.log('✅ Member deletion completed successfully');
    } catch (e) {
      console.error("delete member failed", e);
      alert("Could not delete member. Please try again.");
    }
  };

  if (loading) return <div className="p-4">Loading members…</div>;
  if (error)   return <div className="p-4 text-rose-600">Error loading members</div>;

  const MemberCard = ({ m, onDeleteMember, onAddOrUpdateMember }) => {
    const name  = m?.name || `${m?.firstName ?? ""} ${m?.lastName ?? ""}`.trim() || "Member";
    const email = m?.email || "";
    const phone = m?.phone || m?.phoneNumber || "";
    const plan = m?.membershipType || m?.membership_type || m?.plan || m?.planName || "Unassigned";
    const isActive = m?.status === "Active" || !!m?.active;
    
    // State for edit modal and email dropdown
    const [showEditModal, setShowEditModal] = React.useState(false);
    const [showEmailDropdown, setShowEmailDropdown] = React.useState(false);
    const [emailTemplates, setEmailTemplates] = React.useState([]);
    const [sendingEmail, setSendingEmail] = React.useState(false);
    
    // Load email templates on component mount
    React.useEffect(() => {
      const loadEmailTemplates = async () => {
        try {
          const templates = await gymStorage.getAll('emailTemplates') || [];
          
          // Check if we need to update templates that still have GoGym4U branding
          const updatedTemplates = templates.map(template => {
            if (template.subject && template.subject.includes('GoGym4U')) {
              return {
                ...template,
                subject: template.subject.replace(/GoGym4U/g, 'Alphalete Athletics')
              };
            }
            if (template.body && template.body.includes('GoGym4U')) {
              return {
                ...template,
                body: template.body.replace(/GoGym4U/g, 'Alphalete Athletics')
              };
            }
            return template;
          });
          
          // Save updated templates back to storage if changes were made
          const hasChanges = updatedTemplates.some((template, index) => 
            JSON.stringify(template) !== JSON.stringify(templates[index])
          );
          
          if (hasChanges) {
            for (const template of updatedTemplates) {
              await gymStorage.upsert('emailTemplates', template);
            }
          }
          
          // Add default payment reminder template if none exist
          if (updatedTemplates.length === 0) {
            const paymentReminderTemplate = {
              id: 'payment-reminder',
              name: 'Payment Reminder',
              subject: 'Payment Reminder - Alphalete Athletics',
              body: `Dear {memberName},

This is a friendly reminder that your membership payment is due on {dueDate}.

Please make your payment at your earliest convenience to avoid any interruption to your membership.

Thank you for being a valued member of Alphalete Athletics!

Best regards,
Alphalete Athletics Team`
            };
            
            const paymentReceiptTemplate = {
              id: 'payment-receipt',
              name: 'Payment Receipt',
              subject: 'Payment Receipt - Alphalete Athletics',
              body: `Dear {memberName},

Thank you for your payment! This email serves as your receipt for the payment made today.

PAYMENT DETAILS:
• Invoice Number: #{invoiceNumber}
• Payment Amount: TTD {paymentAmount}
• Payment Date: {paymentDate}
• Membership Type: {membershipType}
• Next Due Date: {nextDueDate}

We appreciate your continued membership with Alphalete Athletics. If you have any questions about this payment or your membership, please don't hesitate to contact us.

Best regards,
Alphalete Athletics Team
Phone: (868) 123-4567
Email: info@alphaleteclub.com`
            };
            
            await gymStorage.upsert('emailTemplates', paymentReminderTemplate);
            await gymStorage.upsert('emailTemplates', paymentReceiptTemplate);
            setEmailTemplates([paymentReminderTemplate, paymentReceiptTemplate]);
          } else {
            // Check if payment receipt template exists, add if missing
            const hasReceiptTemplate = updatedTemplates.some(t => t.id === 'payment-receipt' || t.name === 'Payment Receipt');
            if (!hasReceiptTemplate) {
              const paymentReceiptTemplate = {
                id: 'payment-receipt',
                name: 'Payment Receipt',
                subject: 'Payment Receipt - Alphalete Athletics',
                body: `Dear {memberName},

Thank you for your payment! This email serves as your receipt for the payment made today.

PAYMENT DETAILS:
• Invoice Number: #{invoiceNumber}
• Payment Amount: TTD {paymentAmount}
• Payment Date: {paymentDate}
• Membership Type: {membershipType}
• Next Due Date: {nextDueDate}

We appreciate your continued membership with Alphalete Athletics. If you have any questions about this payment or your membership, please don't hesitate to contact us.

Best regards,
Alphalete Athletics Team
Phone: (868) 123-4567
Email: info@alphaleteclub.com`
              };
              
              await gymStorage.upsert('emailTemplates', paymentReceiptTemplate);
              updatedTemplates.push(paymentReceiptTemplate);
            }
            setEmailTemplates(updatedTemplates);
          }
        } catch (error) {
          console.error('Error loading email templates:', error);
          // Set default template as fallback
          setEmailTemplates([{
            id: 'payment-reminder',
            name: 'Payment Reminder',
            subject: 'Payment Reminder - Alphalete Athletics',
            body: `Dear {memberName},

This is a friendly reminder that your membership payment is due on {dueDate}.

Please make your payment at your earliest convenience to avoid any interruption to your membership.

Thank you for being a valued member of Alphalete Athletics!

Best regards,
Alphalete Athletics Team`
          }]);
        }
      };
      
      loadEmailTemplates();
    }, []);
    
    // Close email dropdown when clicking outside
    React.useEffect(() => {
      const handleClickOutside = (event) => {
        if (showEmailDropdown && !event.target.closest('.email-dropdown-container')) {
          setShowEmailDropdown(false);
        }
      };
      
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [showEmailDropdown]);
    
    // Handle email sending
    const handleSendEmail = async (template) => {
      if (!email) {
        alert('❌ No email address available for this member');
        return;
      }
      
      setSendingEmail(true);
      setShowEmailDropdown(false);
      
      try {
        // Replace template variables with member data
        const dueDate = m.nextDue || m.dueDate || 'Not set';
        const personalizedSubject = template.subject.replace('{memberName}', name).replace('{dueDate}', dueDate);
        const personalizedBody = template.body.replace('{memberName}', name).replace('{dueDate}', dueDate);
        
        const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
        if (backendUrl) {
          const response = await fetch(`${backendUrl}/api/email/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              to: email,
              subject: personalizedSubject,
              body: personalizedBody,
              memberName: name,
              templateName: template.name
            })
          });
          
          if (response.ok) {
            alert(`✅ Email sent successfully to ${name}!`);
          } else {
            throw new Error('Failed to send email');
          }
        } else {
          throw new Error('Backend URL not configured');
        }
      } catch (error) {
        console.error('Error sending email:', error);
        alert('❌ Failed to send email. Please try again.');
      } finally {
        setSendingEmail(false);
      }
    };
    
    // Calculate due date information
    const nextDue = m?.nextDue || m?.nextDueDate || m?.dueDate;
    const joinedOn = m?.joinedOn || m?.createdAt;
    
    let dueDateDisplay = null;
    let dueDateClass = "text-gray-600";
    let dueDateBadgeClass = "badge-inactive";
    
    if (nextDue) {
      try {
        const dueDate = new Date(nextDue);
        const today = new Date();
        const timeDiff = dueDate - today;
        const daysDiff = Math.ceil(timeDiff / (1000 * 60 * 60 * 24));
        
        if (daysDiff < 0) {
          // Overdue
          dueDateDisplay = `Overdue ${Math.abs(daysDiff)} day${Math.abs(daysDiff) === 1 ? '' : 's'}`;
          dueDateClass = "text-red-600 font-medium";
          dueDateBadgeClass = "bg-red-100 text-red-700";
        } else if (daysDiff <= 3) {
          // Due soon
          dueDateDisplay = daysDiff === 0 ? "Due Today" : `Due in ${daysDiff} day${daysDiff === 1 ? '' : 's'}`;
          dueDateClass = "text-orange-600 font-medium";
          dueDateBadgeClass = "bg-orange-100 text-orange-700";
        } else {
          // Future due date
          dueDateDisplay = `Due ${dueDate.toLocaleDateString()}`;
          dueDateClass = "text-green-600";
          dueDateBadgeClass = "bg-green-100 text-green-700";
        }
      } catch (e) {
        dueDateDisplay = "Invalid due date";
        dueDateClass = "text-gray-500";
      }
    } else if (joinedOn) {
      // Calculate based on join date if no due date set
      try {
        const joined = new Date(joinedOn);
        const estimatedDue = new Date(joined);
        estimatedDue.setMonth(estimatedDue.getMonth() + 1); // Add 1 month
        dueDateDisplay = `Est. due ${estimatedDue.toLocaleDateString()}`;
        dueDateClass = "text-blue-600";
        dueDateBadgeClass = "bg-blue-100 text-blue-700";
      } catch (e) {
        dueDateDisplay = "No due date set";
        dueDateClass = "text-gray-500";
      }
    } else {
      dueDateDisplay = "No due date set";
      dueDateClass = "text-gray-500";
    }

    return (
      <div className="card mb-3">
        <div className="card-body">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
              {(name.split(" ").map(s => s[0]).join("").slice(0,2) || "MM")}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold">{name}</h3>
                {isActive
                  ? <span className="badge-active">ACTIVE</span>
                  : <span className="badge-inactive">INACTIVE</span>}
              </div>
              {email ? <div className="text-sm text-slate-500">{email}</div> : null}
              {phone ? <div className="text-sm text-slate-500">{phone}</div> : null}
              <div className="mt-2 flex flex-wrap gap-2">
                <span className="badge badge-warning">{String(plan)}</span>
                {dueDateDisplay && (
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${dueDateBadgeClass}`}>
                    📅 {dueDateDisplay}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="mt-4 flex gap-1 justify-between px-2">
            <button 
              type="button"
              className="rounded-xl px-1 py-2 flex flex-col items-center justify-center w-[58px] h-16 transition-all duration-200"
              onClick={() => setShowEditModal(true)}
            >
              <div className="flex items-center justify-center mb-1">
                <PencilIcon className="w-6 h-6 text-blue-500 hover:text-blue-600 transition-colors duration-200" />
              </div>
              <span className="text-xs font-medium text-gray-700 text-center">Edit</span>
            </button>
            
            <button 
              type="button"
              className="rounded-xl px-1 py-2 flex flex-col items-center justify-center w-[58px] h-16 transition-all duration-200"
              onClick={async () => {
                if (confirm(`${isActive ? 'Deactivate' : 'Activate'} ${name}?`)) {
                  try {
                    const updatedMember = { ...m, status: isActive ? 'Inactive' : 'Active', active: !isActive };
                    
                    // Use repository system for consistent offline-first behavior
                    if (onAddOrUpdateMember) {
                      await onAddOrUpdateMember(updatedMember);
                      alert(`✅ Member ${isActive ? 'deactivated' : 'activated'} successfully`);
                    } else {
                      // Fallback to direct backend call if no repository handler
                      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
                      if (backendUrl) {
                        const response = await fetch(`${backendUrl}/api/clients/${m.id}`, {
                          method: 'PUT',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(updatedMember)
                        });
                        if (!response.ok) {
                          throw new Error('Backend update failed');
                        }
                        alert(`✅ Member ${isActive ? 'deactivated' : 'activated'} successfully`);
                        // Trigger data refresh without full page reload
                        window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'member_status_updated' }));
                      }
                    }
                  } catch (error) {
                    console.error('Error updating member status:', error);
                    alert('❌ Error updating member status. Please try again.');
                  }
                }
              }}
            >
              <div className="flex items-center justify-center mb-1">
                {isActive ? (
                  <ClockIcon className="w-6 h-6 text-orange-500 hover:text-orange-600 transition-colors duration-200" />
                ) : (
                  <ArrowRightIcon className="w-6 h-6 text-orange-500 hover:text-orange-600 transition-colors duration-200" />
                )}
              </div>
              <span className="text-xs font-medium text-gray-700 text-center">{isActive ? 'Pause' : 'Activate'}</span>
            </button>
            
            <button 
              type="button"
              className="rounded-xl px-1 py-2 flex flex-col items-center justify-center w-[58px] h-16 transition-all duration-200"
              onClick={() => {
                // WhatsApp integration
                if (phone) {
                  const phoneNumber = phone.replace(/\D/g, ''); // Remove non-digits
                  const message = `Hi ${name}, this is a message from Alphalete Athletics regarding your ${plan} membership.`;
                  const whatsappUrl = `https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`;
                  window.open(whatsappUrl, '_blank');
                } else {
                  alert('❌ No phone number available for this member');
                }
              }}
            >
              <div className="flex items-center justify-center mb-1">
                <ChatBubbleLeftRightIcon className="w-6 h-6 text-green-500 hover:text-green-600 transition-colors duration-200" />
              </div>
              <span className="text-xs font-medium text-gray-700 text-center">WhatsApp</span>
            </button>
            
            <div className="relative email-dropdown-container">
              <button 
                type="button"
                className="rounded-xl px-1 py-2 flex flex-col items-center justify-center w-[58px] h-16 transition-all duration-200"
                onClick={() => setShowEmailDropdown(!showEmailDropdown)}
                disabled={sendingEmail}
              >
                <div className="flex items-center justify-center mb-1">
                  <EnvelopeIcon className="w-6 h-6 text-indigo-500 hover:text-indigo-600 transition-colors duration-200" />
                </div>
                <span className="text-xs font-medium text-gray-700 text-center">
                  {sendingEmail ? 'Sending...' : 'Email'}
                </span>
              </button>
              
              {/* Email Template Dropdown */}
              {showEmailDropdown && (
                <div className="absolute bottom-full left-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[180px]">
                  <div className="p-3">
                    <div className="text-sm font-semibold text-gray-800 mb-3 px-1">Select Template:</div>
                    {emailTemplates.map((template) => (
                      <button
                        key={template.id}
                        className="w-full text-left px-3 py-2 text-sm text-gray-800 bg-white hover:bg-blue-50 hover:text-blue-700 rounded border border-gray-100 mb-2 transition-colors font-medium"
                        onClick={() => handleSendEmail(template)}
                      >
                        {template.name}
                      </button>
                    ))}
                    {emailTemplates.length === 0 && (
                      <div className="px-3 py-2 text-sm text-gray-500">No templates available</div>
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <button 
              type="button"
              className="rounded-xl px-1 py-2 flex flex-col items-center justify-center w-[58px] h-16 transition-all duration-200"
              onClick={async () => {
                console.log('🎯 DELETE BUTTON CLICKED!', { name, id: m.id, onDeleteMember: typeof onDeleteMember });
                
                // Check confirm first
                if (!confirm(`Are you sure you want to DELETE ${name}? This action cannot be undone.`)) {
                  console.log('🎯 Delete cancelled by user');
                  return;
                }
                
                console.log('🎯 Delete confirmed, proceeding...');
                try {
                  // Use the repository system for proper delete
                  if (onDeleteMember) {
                    console.log('🎯 Calling onDeleteMember function...');
                    await onDeleteMember(m.id || m._id || m.uuid);
                    console.log('🎯 onDeleteMember completed successfully');
                  } else {
                    console.log('🎯 No onDeleteMember function, using fallback...');
                    // Fallback to manual backend call if no handler provided
                    const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
                    if (backendUrl) {
                      const response = await fetch(`${backendUrl}/api/clients/${m.id}`, { method: 'DELETE' });
                      if (response.ok) {
                        alert('✅ Member deleted successfully');
                        // Trigger data refresh without full page reload
                        window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'member_deleted' }));
                      } else {
                        throw new Error(`Delete failed: ${response.status}`);
                      }
                    }
                  }
                } catch (error) {
                  console.error('Error deleting member:', error);
                  alert('❌ Error deleting member. Please try again.');
                }
              }}
            >
              <div className="flex items-center justify-center mb-1">
                <TrashIcon className="w-6 h-6 text-red-500 hover:text-red-600 transition-colors duration-200" />
              </div>
              <span className="text-xs font-medium text-gray-700 text-center">Delete</span>
            </button>
            
            <button 
              type="button"
              className="rounded-xl px-1 py-2 flex flex-col items-center justify-center w-[58px] h-16 transition-all duration-200"
              onClick={() => {
                // Store pending payment member ID and where user came from
                localStorage.setItem("pendingPaymentMemberId", String(m.id));
                localStorage.setItem("pendingPaymentOrigin", "members");
                window.navigateToTab?.('payments');
              }}
            >
              <div className="flex items-center justify-center mb-1">
                <BanknotesIcon className="w-6 h-6 text-purple-500 hover:text-purple-600 transition-colors duration-200" />
              </div>
              <span className="text-xs font-medium text-gray-700 text-center">Payment</span>
            </button>
          </div>
        </div>
        
        {/* Edit Member Modal */}
        {showEditModal && (
          <EditMemberForm
            member={m}
            onSave={async (updatedMember) => {
              try {
                if (onAddOrUpdateMember) {
                  await onAddOrUpdateMember(updatedMember);
                } else {
                  // Fallback to direct backend call if no repository handler
                  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
                  if (backendUrl) {
                    const response = await fetch(`${backendUrl}/api/clients/${updatedMember.id}`, {
                      method: 'PUT',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify(updatedMember)
                    });
                    if (!response.ok) {
                      throw new Error('Backend update failed');
                    }
                    // Trigger data refresh
                    window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'member_updated' }));
                  }
                }
                setShowEditModal(false);
              } catch (error) {
                console.error('Error updating member:', error);
                throw error; // Let EditMemberForm handle the error display
              }
            }}
            onCancel={() => setShowEditModal(false)}
          />
        )}
      </div>
    );
  };

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Members</h1>
        {list.length > 0 && (
          <button 
            type="button"
            className="btn btn-primary"
            onClick={() => setShowAddForm(true)}
          >
            + Add Member
          </button>
        )}
      </div>

      {/* Add Member Form */}
      {showAddForm && (
        <div className="card mb-6">
          <div className="card-header">
            <h3 className="text-lg font-semibold">Add New Member</h3>
          </div>
          <div className="card-body">
            <AddMemberForm 
              onAddOrUpdateMember={onAddOrUpdateMember}
              onCancel={() => {
                setShowAddForm(false);
                // Navigate back to origin if user came from elsewhere
                const origin = localStorage.getItem("addMemberOrigin");
                if (origin) {
                  localStorage.removeItem("addMemberOrigin"); // Clean up
                  window.navigateToTab?.(origin);
                }
              }} 
              onSuccess={() => {
                setShowAddForm(false);
                // Navigate back to origin after success if user came from elsewhere
                const origin = localStorage.getItem("addMemberOrigin");
                if (origin) {
                  localStorage.removeItem("addMemberOrigin"); // Clean up
                  window.navigateToTab?.(origin);
                } else {
                  // Refresh members list if staying on members page
                  window.location.reload();
                }
              }} 
            />
          </div>
        </div>
      )}

      {list.length === 0
        ? <div className="text-center py-8">
            <div className="text-slate-500 mb-4">No members yet.</div>
            <button 
              type="button" 
              className="btn btn-primary"
              onClick={() => setShowAddForm(true)}
            >
              Add your first member
            </button>
          </div>
        : list.map((m, i) => <MemberCard key={m.id || m._id || m.uuid || i} m={m} onDeleteMember={onDeleteMember} onAddOrUpdateMember={onAddOrUpdateMember} />)}
    </div>
  );
}

// --- Reports ---
const Reports = () => {
  const { members: membersR, loading: loadingR } = useMembersFromStorage();
  const [payments, setPayments] = useState([]);
  const [selectedDateRange, setSelectedDateRange] = useState('30days');
  
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
  
  // Render loading state without early return to avoid hook issues
  if (loadingR) {
    return <ReportsSkeleton />;
  }
  
  const paymentsList = Array.isArray(payments) ? payments : [];
  const membersList = Array.isArray(membersR) ? membersR : [];
  
  // Calculate date ranges
  const today = new Date();
  const todayISO = today.toISOString().slice(0, 10);
  const thisMonth = todayISO.slice(0, 7);
  const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1).toISOString().slice(0, 7);
  
  // Filter payments by date range
  const getDateRangeFilter = (range) => {
    const now = new Date();
    switch(range) {
      case '7days':
        const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000);
        return (p) => p.paidOn && new Date(p.paidOn) >= sevenDaysAgo;
      case '30days':
        const thirtyDaysAgo = new Date(now - 30 * 24 * 60 * 60 * 1000);
        return (p) => p.paidOn && new Date(p.paidOn) >= thirtyDaysAgo;
      case 'thisMonth':
        return (p) => p.paidOn && p.paidOn.slice(0, 7) === thisMonth;
      case 'lastMonth':
        return (p) => p.paidOn && p.paidOn.slice(0, 7) === lastMonth;
      case 'allTime':
      default:
        return () => true;
    }
  };
  
  const dateFilter = getDateRangeFilter(selectedDateRange);
  const filteredPayments = paymentsList.filter(dateFilter);
  
  // Calculate comprehensive statistics
  const totalRevenue = paymentsList.reduce((sum, p) => sum + Number(p.amount || 0), 0);
  const rangeRevenue = filteredPayments.reduce((sum, p) => sum + Number(p.amount || 0), 0);
  const activeMembers = membersList.filter(m => m.status === 'Active' || !m.status).length;
  const totalMembers = membersList.length;
  const inactiveMembers = totalMembers - activeMembers;
  
  // Payment status breakdown
  const paidMembers = membersList.filter(m => {
    const nextDue = m.nextDue || m.dueDate;
    if (!nextDue) return false;
    return new Date(nextDue) > new Date(todayISO);
  }).length;
  
  const overdueMembers = membersList.filter(m => {
    const nextDue = m.nextDue || m.dueDate;
    if (!nextDue) return false;
    return new Date(nextDue) < new Date(todayISO);
  }).length;
  
  const dueTodayMembers = membersList.filter(m => {
    const nextDue = m.nextDue || m.dueDate;
    return nextDue === todayISO;
  }).length;
  
  // Revenue trends
  const thisMonthRevenue = paymentsList.filter(p => p.paidOn && p.paidOn.slice(0, 7) === thisMonth).reduce((sum, p) => sum + Number(p.amount || 0), 0);
  const lastMonthRevenue = paymentsList.filter(p => p.paidOn && p.paidOn.slice(0, 7) === lastMonth).reduce((sum, p) => sum + Number(p.amount || 0), 0);
  const revenueGrowth = lastMonthRevenue > 0 ? ((thisMonthRevenue - lastMonthRevenue) / lastMonthRevenue * 100) : 0;
  
  // Membership plan breakdown
  const planBreakdown = membersList.reduce((acc, member) => {
    const plan = member.membership_type || member.planName || 'No Plan';
    if (!acc[plan]) {
      acc[plan] = { count: 0, revenue: 0 };
    }
    acc[plan].count++;
    
    // Calculate revenue for this plan from payments
    const memberPayments = paymentsList.filter(p => String(p.memberId) === String(member.id));
    acc[plan].revenue += memberPayments.reduce((sum, p) => sum + Number(p.amount || 0), 0);
    
    return acc;
  }, {});
  
  // Top plans by member count
  const topPlans = Object.entries(planBreakdown)
    .sort(([,a], [,b]) => b.count - a.count)
    .slice(0, 5);
  
  // Recent payments for activity feed
  const recentPayments = paymentsList
    .sort((a, b) => new Date(b.paidOn || 0) - new Date(a.paidOn || 0))
    .slice(0, 10);
  
  // Average payment calculation
  const avgPayment = paymentsList.length > 0 ? totalRevenue / paymentsList.length : 0;
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <ActionIcon name="📊" className="text-indigo-600 mr-3" size="xl" />
                Reports & Analytics
              </h1>
              <p className="text-gray-500 mt-1">Comprehensive gym performance insights and member analytics</p>
            </div>
            
            {/* Date Range Selector */}
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Date Range:</label>
              <select
                value={selectedDateRange}
                onChange={(e) => setSelectedDateRange(e.target.value)}
                className="input text-sm"
              >
                <option value="7days">Last 7 Days</option>
                <option value="30days">Last 30 Days</option>
                <option value="thisMonth">This Month</option>
                <option value="lastMonth">Last Month</option>
                <option value="allTime">All Time</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div className="px-6 py-6">
        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
          {/* Total Revenue */}
          <div className="stat-card bg-success text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{formatCurrency(rangeRevenue)}</div>
                <div className="stat-label text-success-100">Revenue ({selectedDateRange})</div>
                <div className="text-xs text-success-200 mt-1">Total: {formatCurrency(totalRevenue)}</div>
              </div>
              <BanknotesIcon className="w-10 h-10 text-success-200" />
            </div>
          </div>

          {/* Active Members */}
          <div className="stat-card bg-indigo-600 text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{activeMembers}</div>
                <div className="stat-label text-indigo-100">Active Members</div>
                <div className="text-xs text-indigo-200 mt-1">of {totalMembers} total</div>
              </div>
              <Icon name="👥" size="2xl" className="text-indigo-200" />
            </div>
          </div>

          {/* Payment Rate */}
          <div className="stat-card bg-warning text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{totalMembers > 0 ? Math.round((paidMembers / totalMembers) * 100) : 0}%</div>
                <div className="stat-label text-warning-100">Payment Rate</div>
                <div className="text-xs text-warning-200 mt-1">{paidMembers} paid up</div>
              </div>
              <Icon name="✓" size="2xl" className="text-warning-200" />
            </div>
          </div>

          {/* Growth Rate */}
          <div className="stat-card bg-info text-white">
            <div className="flex items-center justify-between">
              <div>
                <div className="stat-value">{revenueGrowth > 0 ? '+' : ''}{revenueGrowth.toFixed(1)}%</div>
                <div className="stat-label text-info-100">Monthly Growth</div>
                <div className="text-xs text-info-200 mt-1">vs last month</div>
              </div>
              <Icon name="📈" size="2xl" className="text-info-200" />
            </div>
          </div>
        </div>

        {/* Detailed Analytics Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
          {/* Member Status Breakdown */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Icon name="👥" className="text-indigo-600 mr-2" />
                Member Status
              </h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span className="text-sm">Active Members</span>
                  </div>
                  <span className="font-semibold">{activeMembers}</span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-gray-400 rounded-full mr-2"></div>
                    <span className="text-sm">Inactive Members</span>
                  </div>
                  <span className="font-semibold">{inactiveMembers}</span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                    <span className="text-sm">Overdue</span>
                  </div>
                  <span className="font-semibold">{overdueMembers}</span>
                </div>
                <div className="flex justify-between items-center">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span className="text-sm">Due Today</span>
                  </div>
                  <span className="font-semibold">{dueTodayMembers}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Revenue Breakdown */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <BanknotesIcon className="w-5 h-5 text-green-600 mr-2" />
                Revenue Metrics
              </h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">This Month</span>
                  <span className="font-semibold text-green-600">{formatCurrency(thisMonthRevenue)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Last Month</span>
                  <span className="font-semibold">{formatCurrency(lastMonthRevenue)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Average Payment</span>
                  <span className="font-semibold">{formatCurrency(avgPayment)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Total Payments</span>
                  <span className="font-semibold">{paymentsList.length}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Top Membership Plans */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                <Icon name="🏆" className="text-yellow-600 mr-2" />
                Top Plans
              </h3>
            </div>
            <div className="card-body">
              <div className="space-y-3">
                {topPlans.length > 0 ? (
                  topPlans.map(([planName, stats], index) => (
                    <div key={planName} className="flex justify-between items-center">
                      <div className="flex items-center">
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mr-2 ${
                          index === 0 ? 'bg-yellow-500' : 
                          index === 1 ? 'bg-gray-400' : 
                          index === 2 ? 'bg-yellow-600' : 'bg-indigo-500'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-medium text-sm">{planName}</div>
                          <div className="text-xs text-gray-500">{formatCurrency(stats.revenue)} revenue</div>
                        </div>
                      </div>
                      <span className="font-semibold">{stats.count}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    <div className="text-sm">No membership plans yet</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              <Icon name="🕐" className="text-blue-600 mr-2" />
              Recent Payment Activity
            </h3>
          </div>
          <div className="card-body">
            {recentPayments.length > 0 ? (
              <div className="space-y-3">
                {recentPayments.map((payment, index) => (
                  <div key={payment.id || index} className="flex items-center justify-between p-3 border border-gray-100 rounded-lg hover:bg-gray-50 transition-colors">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                        <BanknotesIcon className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">{payment.memberName || 'Unknown Member'}</div>
                        <div className="text-sm text-gray-500 flex items-center space-x-2">
                          <span>{formatDate(payment.paidOn)}</span>
                          {payment.planName && (
                            <>
                              <span>•</span>
                              <span>{payment.planName}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-green-600">{formatCurrency(payment.amount)}</div>
                      <span className="badge badge-success text-xs">Paid</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <BanknotesIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <div className="text-xl font-medium text-gray-900 mb-2">No Payment Activity</div>
                <div className="text-gray-500">Recent payments will appear here when members make payments</div>
              </div>
            )}
          </div>
        </div>
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
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [showCreateTemplate, setShowCreateTemplate] = useState(false);
  const [templateForm, setTemplateForm] = useState({
    name: '',
    subject: '',
    body: ''
  });
  
  useEffect(() => { 
    (async () => {
      try {
        // Sequential loading to avoid double IndexedDB calls
        const saved = await (gymStorage?.getSetting?.('gymSettings', s) ?? 
                             getSettingNamed?.('gymSettings', s) ?? s);
        setS(saved);
        
        // Load email templates
        const templates = await gymStorage.getAll('emailTemplates') || [];
        
        // Check if we need to update templates that still have GoGym4U branding
        const updatedTemplates = templates.map(template => {
          if (template.subject && template.subject.includes('GoGym4U')) {
            return {
              ...template,
              subject: template.subject.replace(/GoGym4U/g, 'Alphalete Athletics')
            };
          }
          if (template.body && template.body.includes('GoGym4U')) {
            return {
              ...template,
              body: template.body.replace(/GoGym4U/g, 'Alphalete Athletics')
            };
          }
          return template;
        });
        
        // Save updated templates back to storage if changes were made
        const hasChanges = updatedTemplates.some((template, index) => 
          JSON.stringify(template) !== JSON.stringify(templates[index])
        );
        
        if (hasChanges) {
          for (const template of updatedTemplates) {
            await gymStorage.upsert('emailTemplates', template);
          }
        }
        
        // Add default payment reminder template if none exist
        if (updatedTemplates.length === 0) {
          const defaultTemplate = {
            id: 'payment-reminder',
            name: 'Payment Reminder',
            subject: 'Payment Reminder - Alphalete Athletics',
            body: `Dear {memberName},

This is a friendly reminder that your membership payment is due on {dueDate}.

Please make your payment at your earliest convenience to avoid any interruption to your membership.

Thank you for being a valued member of Alphalete Athletics!

Best regards,
Alphalete Athletics Team`
          };
          await gymStorage.upsert('emailTemplates', defaultTemplate);
          setEmailTemplates([defaultTemplate]);
        } else {
          setEmailTemplates(updatedTemplates);
        }
        
        // Optionally get storage stats if available
        const stats = await gymStorage?.getStorageStats?.();
        if (stats) setStorageStats(stats);
      } catch (e) { 
        console.error("Settings load error", e); 
      } finally { 
        setLoading(false);
        setLoadingTemplates(false); 
      }
    })(); 
  }, []);
  
  async function save() {
    await (gymStorage.saveSetting?.('gymSettings', s) ?? saveSettingNamed('gymSettings', s));
    signalChanged('settings');
    alert('Settings saved successfully!');
  }
  
  // Email template management functions
  const saveTemplate = async () => {
    try {
      if (!templateForm.name.trim() || !templateForm.subject.trim() || !templateForm.body.trim()) {
        alert('Please fill in all template fields');
        return;
      }
      
      const template = {
        id: editingTemplate?.id || `template-${Date.now()}`,
        name: templateForm.name.trim(),
        subject: templateForm.subject.trim(),
        body: templateForm.body.trim()
      };
      
      await gymStorage.upsert('emailTemplates', template);
      
      // Update local state
      if (editingTemplate) {
        setEmailTemplates(prev => prev.map(t => t.id === template.id ? template : t));
      } else {
        setEmailTemplates(prev => [...prev, template]);
      }
      
      // Reset form
      setTemplateForm({ name: '', subject: '', body: '' });
      setEditingTemplate(null);
      setShowCreateTemplate(false);
      
      alert(`Template ${editingTemplate ? 'updated' : 'created'} successfully!`);
    } catch (error) {
      console.error('Error saving template:', error);
      alert('Error saving template');
    }
  };
  
  const deleteTemplate = async (template) => {
    if (!confirm(`Delete template "${template.name}"?`)) return;
    
    try {
      await gymStorage.remove('emailTemplates', template.id);
      setEmailTemplates(prev => prev.filter(t => t.id !== template.id));
      alert('Template deleted successfully!');
    } catch (error) {
      console.error('Error deleting template:', error);
      alert('Error deleting template');
    }
  };
  
  const startEdit = (template) => {
    setEditingTemplate(template);
    setTemplateForm({
      name: template.name,
      subject: template.subject,
      body: template.body
    });
    setShowCreateTemplate(true);
  };
  
  const cancelEdit = () => {
    setEditingTemplate(null);
    setTemplateForm({ name: '', subject: '', body: '' });
    setShowCreateTemplate(false);
  };
  
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
      
      {/* Email Templates Section */}
      <div className="space-y-4 bg-white border rounded-2xl p-4">
        <div className="flex justify-between items-center">
          <div className="font-medium">Email Templates</div>
          <button 
            type="button" 
            className="btn btn-primary text-sm px-3 py-1"
            onClick={() => setShowCreateTemplate(true)}
          >
            + Add Template
          </button>
        </div>
        
        {loadingTemplates ? (
          <div className="text-center py-4">Loading templates...</div>
        ) : (
          <div className="space-y-3">
            {emailTemplates.map((template) => (
              <div key={template.id} className="border border-gray-200 rounded-lg p-4 bg-white shadow-sm">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-semibold text-base text-gray-800">{template.name}</div>
                    <div className="text-sm text-gray-600 mt-1">Subject: {template.subject}</div>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      onClick={() => startEdit(template)}
                    >
                      Edit
                    </button>
                    <button 
                      className="text-red-600 hover:text-red-700 text-sm font-medium"
                      onClick={() => deleteTemplate(template)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="text-sm text-gray-800 bg-white p-3 rounded border-l-4 border-blue-400 border border-gray-200">
                  {template.body.substring(0, 100)}...
                </div>
              </div>
            ))}
            {emailTemplates.length === 0 && (
              <div className="text-center py-4 text-gray-500">No email templates found</div>
            )}
          </div>
        )}
        
        {/* Create/Edit Template Form */}
        {showCreateTemplate && (
          <div className="border-t pt-4">
            <div className="font-medium mb-3">
              {editingTemplate ? 'Edit Template' : 'Create New Template'}
            </div>
            <div className="space-y-3">
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Template Name</span>
                <input 
                  className="mt-1 border rounded px-3 py-2 w-full" 
                  type="text"
                  value={templateForm.name}
                  onChange={e => setTemplateForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g., Payment Reminder, Welcome Email"
                />
              </label>
              
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Subject Line</span>
                <input 
                  className="mt-1 border rounded px-3 py-2 w-full" 
                  type="text"
                  value={templateForm.subject}
                  onChange={e => setTemplateForm(f => ({ ...f, subject: e.target.value }))}
                  placeholder="Email subject line"
                />
              </label>
              
              <label className="block">
                <span className="text-sm font-medium text-gray-700">Email Body</span>
                <textarea 
                  className="mt-1 border rounded px-3 py-2 w-full h-32" 
                  value={templateForm.body}
                  onChange={e => setTemplateForm(f => ({ ...f, body: e.target.value }))}
                  placeholder="Email content... Use {memberName} and {dueDate} for automatic member data insertion"
                />
                <span className="text-xs text-gray-500">
                  Available variables: {'{memberName}'} and {'{dueDate}'}
                </span>
              </label>
              
              <div className="flex gap-2">
                <button 
                  type="button" 
                  className="btn btn-primary"
                  onClick={saveTemplate}
                >
                  {editingTemplate ? 'Update Template' : 'Save Template'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={cancelEdit}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
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
function MembershipManagement() {
  const { members: membersMM, loading: loadingMM, error: errorMM } = useMembersFromStorage();
  const [plans, setPlans] = React.useState([]);
  const [loadingPlans, setLoadingPlans] = React.useState(true);
  const [showCreateForm, setShowCreateForm] = React.useState(false);
  const [editingPlan, setEditingPlan] = React.useState(null);
  const [formData, setFormData] = React.useState({
    name: '',
    price: '',
    description: '',
    duration: 'monthly',
    features: []
  });

  React.useEffect(() => { let live = true; (async () => {
    try {
      // Direct storage access instead of facade
      const storage = storageNamed || gymStorageMain;
      if (storage.getPlans) {
        const p = await storage.getPlans();
        if (live) setPlans(Array.isArray(p) ? p : []);
      } else if (storage.getAll) {
        const p = await storage.getAll("plans");
        if (live) setPlans(Array.isArray(p) ? p : []);
      }
    } catch (error) {
      console.error('Error loading plans:', error);
    } finally { 
      if (live) setLoadingPlans(false); 
    }
  })(); return () => { live = false; }; }, []);

  const resetForm = () => {
    setFormData({
      name: '',
      price: '',
      description: '',
      duration: 'monthly', 
      features: []
    });
    setEditingPlan(null);
    setShowCreateForm(false);
  };

  const handleEdit = (plan) => {
    setFormData({
      name: plan.name || '',
      price: plan.price || '',
      description: plan.description || '',
      duration: plan.duration || 'monthly',
      features: plan.features || []
    });
    setEditingPlan(plan);
    setShowCreateForm(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.price) return;

    try {
      const planData = {
        ...formData,
        price: parseFloat(formData.price),
        id: editingPlan?.id || crypto?.randomUUID?.() || String(Date.now()),
        createdAt: editingPlan?.createdAt || new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      // Direct storage access instead of facade
      const storage = storageNamed || gymStorageMain;
      if (storage.savePlan) {
        await storage.savePlan(planData);
      } else if (storage.saveData) {
        await storage.saveData("plans", planData);
      }
      
      // Refresh plans using direct storage
      let updatedPlans = [];
      if (storage.getPlans) {
        updatedPlans = await storage.getPlans();
      } else if (storage.getAll) {
        updatedPlans = await storage.getAll("plans");
      }
      setPlans(Array.isArray(updatedPlans) ? updatedPlans : []);
      
      resetForm();
    } catch (error) {
      console.error('Error saving plan:', error);
      alert('Error saving plan. Please try again.');
    }
  };

  const handleDelete = async (plan) => {
    const membersArr = Array.isArray(membersMM) ? membersMM : [];
    const count = membersArr.filter(m => (m?.membershipType || m?.plan) === plan.name).length;
    
    if (count > 0) {
      alert(`Cannot delete "${plan.name}" - it has ${count} active member${count === 1 ? '' : 's'}.`);
      return;
    }

    if (!confirm(`Are you sure you want to delete the plan "${plan.name}"?`)) return;

    try {
      // Note: Implement actual delete functionality in storage.js if needed
      const updatedPlans = plans.filter(p => p.id !== plan.id);
      setPlans(updatedPlans);
      
      // If you have a deletePlan function in storage, use it here
      // await storageFacade.deletePlan(plan.id);
    } catch (error) {
      console.error('Error deleting plan:', error);
      alert('Error deleting plan. Please try again.');
    }
  };

  if (loadingMM || loadingPlans) return <div className="p-4">Loading plans…</div>;
  if (errorMM) return <div className="p-4 text-rose-600">Error loading plans</div>;

  const membersArr = Array.isArray(membersMM) ? membersMM : [];
  const plansArr   = Array.isArray(plans) ? plans : [];

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Membership Plans</h1>
        <button 
          type="button"
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
        >
          <ActionIcon name="➕" className="mr-2" />
          Add Plan
        </button>
      </div>

      {/* Create/Edit Form */}
      {showCreateForm && (
        <div className="card mb-6">
          <div className="card-header">
            <h3 className="text-lg font-semibold">
              {editingPlan ? 'Edit Plan' : 'Create New Plan'}
            </h3>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plan Name *
                  </label>
                  <input
                    type="text"
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="e.g., Premium, Basic, VIP"
                    value={formData.name}
                    onChange={(e) => setFormData(f => ({...f, name: e.target.value}))}
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price (TTD) *
                  </label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="e.g., 55.00"
                    value={formData.price}
                    onChange={(e) => setFormData(f => ({...f, price: e.target.value}))}
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duration
                </label>
                <select
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  value={formData.duration}
                  onChange={(e) => setFormData(f => ({...f, duration: e.target.value}))}
                >
                  <option value="monthly">Monthly</option>
                  <option value="quarterly">Quarterly (3 months)</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows="3"
                  placeholder="Describe what's included in this plan..."
                  value={formData.description}
                  onChange={(e) => setFormData(f => ({...f, description: e.target.value}))}
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button type="submit" className="btn btn-primary">
                  {editingPlan ? 'Update Plan' : 'Create Plan'}
                </button>
                <button 
                  type="button" 
                  className="btn btn-secondary"
                  onClick={resetForm}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Plans List */}
      {plansArr.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">
            <div className="flex justify-center">
              <Icon name="📋" size="2xl" className="text-gray-400" />
            </div>
          </div>
          <div className="text-xl font-medium text-gray-900 mb-2">No Plans Yet</div>
          <div className="text-gray-500 mb-6">Create your first membership plan to get started</div>
          <button 
            type="button"
            className="btn btn-primary"
            onClick={() => setShowCreateForm(true)}
          >
            Create First Plan
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {plansArr.map((plan, i) => {
            const name = plan?.name || "Plan";
            const count = membersArr.filter(m => (m?.membershipType || m?.plan) === name).length;
            return (
              <div key={plan.id || plan._id || i} className="card">
                <div className="card-body">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{name}</h3>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          count > 0 ? 'bg-success-100 text-success-700' : 'bg-gray-100 text-gray-600'
                        }`}>
                          {count} member{count === 1 ? '' : 's'}
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-primary-600 mb-2">
                        {formatCurrency(plan?.price ?? 0)}
                        <span className="text-sm font-normal text-gray-500 ml-1">
                          / {plan?.duration || 'month'}
                        </span>
                      </div>
                      {plan?.description && (
                        <p className="text-gray-600 text-sm">{plan.description}</p>
                      )}
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        type="button"
                        className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                        onClick={() => handleEdit(plan)}
                        title="Edit plan"
                      >
                        <ActionIcon name="✏️" size="sm" />
                      </button>
                      <button
                        type="button"
                        className="p-2 text-gray-400 hover:text-danger-600 transition-colors"
                        onClick={() => handleDelete(plan)}
                        title="Delete plan"
                      >
                        <ActionIcon name="🗑️" size="sm" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

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
            <h1 className="text-lg font-bold text-indigo-600 whitespace-nowrap">Alphalete Athletics</h1>
            <p className="text-xs text-gray-500 whitespace-nowrap">Gym Management</p>
          </div>
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-lg hover:bg-slate-50 transition-colors"
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
                    ? 'text-indigo-600 font-semibold border-r-2 border-indigo-600'
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
          <div className="whitespace-nowrap">Alphalete Athletics v2.0</div>
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
            Alphalete Athletics Login
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
    <div className="fixed bottom-4 left-4 right-4 bg-indigo-600 text-white p-4 rounded-lg shadow-lg z-50">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-medium">Install Alphalete Athletics</p>
          <p className="text-sm text-indigo-100">Add to home screen for quick access</p>
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

// --- Add Member Form ---
export function AddMember(){
  const nav = useNavigate();
  const [form, setForm] = React.useState({ firstName:"", lastName:"", email:"", phone:"", membershipType:"" });

  const onSubmit = async (e) => {
    e.preventDefault();
    // generate id if needed
    const id = crypto?.randomUUID?.() || String(Date.now());
    const member = { 
      id, 
      ...form, 
      name: `${form.firstName} ${form.lastName}`.trim() || form.firstName || form.lastName,
      status: "Active", 
      active: true, 
      joinedOn: new Date().toISOString() 
    };
    await storageFacade.saveMember(member);
    window.navigateToTab?.('members');
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Add Member</h1>
      <form onSubmit={onSubmit} className="card">
        <div className="card-body grid grid-cols-1 sm:grid-cols-2 gap-3">
          <input 
            className="btn-ghost border p-2 rounded" 
            placeholder="First name" 
            value={form.firstName}
            onChange={e=>setForm(f=>({...f, firstName:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded" 
            placeholder="Last name" 
            value={form.lastName}
            onChange={e=>setForm(f=>({...f, lastName:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded" 
            placeholder="Email" 
            value={form.email}
            onChange={e=>setForm(f=>({...f, email:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded" 
            placeholder="Phone" 
            value={form.phone}
            onChange={e=>setForm(f=>({...f, phone:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded sm:col-span-2" 
            placeholder="Plan (e.g., Standard)"
            value={form.membershipType}
            onChange={e=>setForm(f=>({...f, membershipType:e.target.value}))}
          />
        </div>
        <div className="p-4 flex gap-3">
          <button type="submit" className="btn-primary">Save Member</button>
          <button type="button" className="btn-secondary" onClick={() => window.navigateToTab?.('members')}>Cancel</button>
        </div>
      </form>
    </div>
  );
}

// --- Record Payment Form ---
export function RecordPayment(){
  const nav = useNavigate();
  const { members, loading, refresh } = useMembersRepo();
  const [form, setForm] = React.useState({ 
    memberId:"", 
    amount:"", 
    paidOn:new Date().toISOString().slice(0,10), 
    method:"Cash", 
    note:"" 
  });

  // Get selected member with enhanced data
  const selectedMember = React.useMemo(() => {
    if (!form.memberId || !Array.isArray(members)) return null;
    return members.find(m => (m.id||m._id||m.uuid) === form.memberId);
  }, [form.memberId, members]);

  // Set default amount when member is selected
  React.useEffect(() => {
    if (selectedMember && !form.amount) {
      const memberFee = selectedMember.monthly_fee || selectedMember.fee || 0;
      setForm(f => ({ ...f, amount: String(memberFee) }));
      console.log('💰 Auto-filled payment amount for', selectedMember.name, ':', memberFee);
    }
  }, [selectedMember, form.amount]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if(!selectedMember) return alert("Select a member");
    
    const payment = { 
      id: crypto?.randomUUID?.() || String(Date.now()), 
      ...form, 
      amount: Number(form.amount||0) 
    };
    
    console.log('📝 Recording payment for member:', {
      name: selectedMember.name,
      plan: selectedMember.membership_type,
      amount: payment.amount,
      nextDue: selectedMember.nextDue || selectedMember.dueDate
    });
    
    // Keep existing payment logic: save payment, update member if your code does that elsewhere
    await storageFacade.savePayment(payment);
    
    // Optional: if your existing code updates due date, call storageFacade.saveMember(updatedMember) here
    // This preserves the existing Option A payment logic
    
    window.navigateToTab?.('payments');
  };

  if (loading) {
    return <div className="p-4">Loading member data...</div>;
  }

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Record Payment</h1>
      
      {/* Selected Member Information Display */}
      {selectedMember && (
        <div className="card mb-4 bg-blue-50 border-blue-200">
          <div className="card-body">
            <h3 className="font-semibold text-lg mb-2">Member Information</h3>
            {console.log('🔍 Payment Modal - Selected Member Data:', {
              name: selectedMember.name,
              email: selectedMember.email,
              phone: selectedMember.phone,
              fullObject: selectedMember
            })}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Name:</strong> {selectedMember.name}
              </div>
              <div>
                <strong>Email:</strong> {String(selectedMember.email || 'Not provided')}
              </div>
              <div>
                <strong>Phone:</strong> {String(selectedMember.phone || 'Not provided')}
              </div>
              <div>
                <strong>Membership Plan:</strong> {selectedMember.membership_type || 'No plan'}
              </div>
              <div>
                <strong>Monthly Fee:</strong> TTD {selectedMember.monthly_fee || selectedMember.fee || 0}
              </div>
              <div>
                <strong>Due Date:</strong> {selectedMember.nextDue || selectedMember.dueDate || 'Not set'}
              </div>
              <div>
                <strong>Status:</strong> 
                <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                  selectedMember.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {selectedMember.status || 'Unknown'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      <form onSubmit={onSubmit} className="card">
        <div className="card-body grid grid-cols-1 sm:grid-cols-2 gap-3">
          <select 
            className="btn-ghost border p-2 rounded" 
            value={form.memberId}
            onChange={e=>setForm(f=>({...f, memberId:e.target.value}))}
          >
            <option value="">Select member…</option>
            {(Array.isArray(members)?members:[]).map(m=>{
              const id = m.id||m._id||m.uuid; 
              const name = m.name || `${m.firstName??""} ${m.lastName??""}`.trim() || "Member";
              const plan = m.membership_type || "No Plan";
              const fee = m.monthly_fee || m.fee || 0;
              const nextDue = m.nextDue || m.dueDate || "No due date";
              return <option key={id} value={id}>{name} - {plan} (TTD {fee}) - Due: {nextDue}</option>;
            })}
          </select>
          <input 
            className="btn-ghost border p-2 rounded" 
            type="number" 
            min="0" 
            step="0.01" 
            placeholder="Amount"
            value={form.amount} 
            onChange={e=>setForm(f=>({...f, amount:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded" 
            type="date" 
            value={form.paidOn}
            onChange={e=>setForm(f=>({...f, paidOn:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded" 
            placeholder="Method" 
            value={form.method}
            onChange={e=>setForm(f=>({...f, method:e.target.value}))}
          />
          <input 
            className="btn-ghost border p-2 rounded sm:col-span-2" 
            placeholder="Note (optional)"
            value={form.note} 
            onChange={e=>setForm(f=>({...f, note:e.target.value}))}
          />
        </div>
        <div className="p-4 flex gap-3">
          <button type="submit" className="btn-primary">Save Payment</button>
          <button type="button" className="btn-secondary" onClick={() => {
            // Go back to where user came from, default to payments if unknown
            const origin = localStorage.getItem("pendingPaymentOrigin") || "payments";
            localStorage.removeItem("pendingPaymentOrigin"); // Clean up
            window.navigateToTab?.(origin);
          }}>Cancel</button>
        </div>
      </form>
    </div>
  );
}

// --- Enhanced Add Member Form Component with Dynamic Plans Integration ---
function AddMemberForm({ onAddOrUpdateMember, onCancel, onSuccess }) {
  console.log('🔧 AddMemberForm component rendered');
  
  const [form, setForm] = React.useState({ 
    firstName: "", 
    lastName: "", 
    email: "", 
    phone: "", 
    membershipType: "",
    monthlyFee: 0
  });
  const [saving, setSaving] = React.useState(false);
  const [errors, setErrors] = React.useState([]);
  const [syncStatus, setSyncStatus] = React.useState({ isOnline: true, pendingCount: 0 });
  const [availablePlans, setAvailablePlans] = React.useState([]);
  const [plansLoading, setPlansLoading] = React.useState(true);

  // Load available plans from Plans storage
  React.useEffect(() => {
    const loadPlans = async () => {
      try {
        console.log('📋 Loading available plans for member creation...');
        // Import storage dynamically to avoid circular dependencies
        const { getAll } = await import('./storage');
        const allPlans = await getAll('plans') || [];
        const activePlans = allPlans.filter(p => !p._deleted);
        
        console.log(`📋 Loaded ${activePlans.length} active plans:`, activePlans.map(p => `${p.name} - TTD ${p.price}`));
        setAvailablePlans(activePlans);
        
        // Set default plan if available
        if (activePlans.length > 0 && !form.membershipType) {
          const defaultPlan = activePlans[0];
          setForm(f => ({
            ...f,
            membershipType: defaultPlan.name,
            monthlyFee: parseFloat(defaultPlan.price) || 0
          }));
        }
      } catch (error) {
        console.error('❌ Error loading plans:', error);
        // Fallback to hardcoded plans if storage fails
        const fallbackPlans = [
          { name: 'Basic', price: 55.0, cycleDays: 30 },
          { name: 'Premium', price: 75.0, cycleDays: 30 },
          { name: 'Elite', price: 100.0, cycleDays: 30 },
          { name: 'VIP', price: 150.0, cycleDays: 30 }
        ];
        setAvailablePlans(fallbackPlans);
        setForm(f => ({
          ...f,
          membershipType: 'Basic',
          monthlyFee: 55.0
        }));
      } finally {
        setPlansLoading(false);
      }
    };
    
    loadPlans();
    
    // Listen for plan changes to refresh available plans
    const handlePlanChanged = () => {
      console.log('🔄 Plans changed, reloading...');
      loadPlans();
    };
    
    window.addEventListener('DATA_CHANGED', handlePlanChanged);
    return () => window.removeEventListener('DATA_CHANGED', handlePlanChanged);
  }, []);

  // Check sync status on mount
  React.useEffect(() => {
    const checkSyncStatus = async () => {
      try {
        // Import repo dynamically to avoid circular dependencies
        const { getSyncStatus } = await import('./data/members.repo');
        const status = await getSyncStatus();
        setSyncStatus(status);
      } catch (e) {
        console.warn('Failed to get sync status:', e);
      }
    };
    
    checkSyncStatus();
    
    // Listen for online/offline events
    const handleOnline = () => setSyncStatus(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setSyncStatus(prev => ({ ...prev, isOnline: false }));
    
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Validate form in real-time
  const validateForm = () => {
    const newErrors = [];
    
    if (!form.firstName.trim()) {
      newErrors.push('First name is required');
    }
    
    if (!form.membershipType) {
      newErrors.push('Please select a membership plan');
    }
    
    if (form.email && form.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(form.email.trim())) {
        newErrors.push('Please enter a valid email address');
      }
    }
    
    if (form.phone && form.phone.trim()) {
      const phoneRegex = /^\+?[\d\s\-\(\)]{7,}$/;
      if (!phoneRegex.test(form.phone.trim())) {
        newErrors.push('Please enter a valid phone number');
      }
    }
    
    if (!form.monthlyFee || isNaN(form.monthlyFee) || form.monthlyFee <= 0) {
      newErrors.push('Monthly fee must be a positive number');
    }
    
    setErrors(newErrors);
    return newErrors.length === 0;
  };

  // Enhanced submit handler with comprehensive error handling
  const handleSubmit = async () => {
    console.log('🚀 AddMember form submitted');
    
    if (!validateForm()) {
      console.warn('❌ Form validation failed:', errors);
      return;
    }

    setSaving(true);
    setErrors([]);
    
    try {
      const startDate = new Date();
      const billingIntervalDays = 30; // Default 30-day billing cycle
      const nextDueDate = new Date(startDate);
      nextDueDate.setDate(nextDueDate.getDate() + billingIntervalDays);
      
      const member = { 
        name: `${form.firstName} ${form.lastName}`.trim() || form.firstName,
        email: form.email.trim() || '',
        phone: form.phone.trim() || '',
        membership_type: form.membershipType,
        monthly_fee: parseFloat(form.monthlyFee),
        start_date: startDate.toISOString().slice(0, 10),
        nextDue: nextDueDate.toISOString().slice(0, 10), // Auto-calculated due date
        dueDate: nextDueDate.toISOString().slice(0, 10), // Alternative field name
        joinedOn: startDate.toISOString().slice(0, 10), // For fallback calculations
        payment_status: "due",
        status: "Active", 
        active: true,
        auto_reminders_enabled: true,
        billing_interval_days: billingIntervalDays,
        amount_owed: parseFloat(form.monthlyFee) // Set initial amount owed
      };
      
      console.log('📝 Creating member with auto-calculated due date:', {
        name: member.name,
        plan: form.membershipType,
        startDate: member.start_date,
        nextDue: member.nextDue,
        billingInterval: billingIntervalDays
      });
      
      if (onAddOrUpdateMember) {
        await onAddOrUpdateMember(member);
        
        // Reset form with first available plan
        const defaultPlan = availablePlans[0];
        setForm({ 
          firstName: "", 
          lastName: "", 
          email: "", 
          phone: "", 
          membershipType: defaultPlan?.name || "",
          monthlyFee: parseFloat(defaultPlan?.price) || 0
        });
        
        // Show success message with sync status
        const statusMsg = syncStatus.isOnline 
          ? `✅ Member "${member.name}" added successfully with ${form.membershipType} plan!`
          : `✅ Member "${member.name}" saved locally with ${form.membershipType} plan. Will sync when online.`;
        
        alert(statusMsg);
        
        if (onSuccess) onSuccess();
      } else {
        throw new Error('No save handler provided');
      }
    } catch (error) {
      console.error('❌ Error adding member:', error);
      setErrors([error.message || 'Failed to add member. Please try again.']);
    } finally {
      setSaving(false);
    }
  };

  // Update monthly fee when membership plan changes
  const handleMembershipTypeChange = (planName) => {
    const selectedPlan = availablePlans.find(p => p.name === planName);
    if (selectedPlan) {
      console.log('📋 Plan selected:', selectedPlan.name, 'Fee:', selectedPlan.price);
      setForm(f => ({
        ...f, 
        membershipType: planName,
        monthlyFee: parseFloat(selectedPlan.price) || 0
      }));
    }
  };

  return (
    <div className="space-y-4">
      {/* Online/Offline Status */}
      <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${syncStatus.isOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm font-medium">
            {syncStatus.isOnline ? '🌐 Online' : '📴 Offline'}
          </span>
        </div>
        {syncStatus.pendingCount > 0 && (
          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
            {syncStatus.pendingCount} pending sync
          </span>
        )}
      </div>

      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="text-red-800 font-medium mb-1">Please fix the following errors:</div>
          <ul className="list-disc list-inside text-sm text-red-700">
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">First Name *</label>
          <input 
            type="text"
            className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.some(e => e.includes('First name')) ? 'border-red-300 bg-red-50' : 'border-gray-300'
            }`}
            placeholder="First Name" 
            value={form.firstName}
            onChange={e => setForm(f => ({...f, firstName: e.target.value}))}
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
          <input 
            type="text"
            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500" 
            placeholder="Last Name" 
            value={form.lastName}
            onChange={e => setForm(f => ({...f, lastName: e.target.value}))}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input 
            type="email"
            className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.some(e => e.includes('email')) ? 'border-red-300 bg-red-50' : 'border-gray-300'
            }`}
            placeholder="email@example.com" 
            value={form.email}
            onChange={e => setForm(f => ({...f, email: e.target.value}))}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input 
            type="tel"
            className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.some(e => e.includes('phone')) ? 'border-red-300 bg-red-50' : 'border-gray-300'
            }`}
            placeholder="+1 (868) 555-0123" 
            value={form.phone}
            onChange={e => setForm(f => ({...f, phone: e.target.value}))}
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Membership Plan *</label>
          {plansLoading ? (
            <div className="w-full p-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
              Loading plans...
            </div>
          ) : availablePlans.length > 0 ? (
            <select
              className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                errors.some(e => e.includes('membership plan')) ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              value={form.membershipType}
              onChange={e => handleMembershipTypeChange(e.target.value)}
              required
            >
              <option value="">Select a plan...</option>
              {availablePlans.map(plan => (
                <option key={plan.name} value={plan.name}>
                  {plan.name} - TTD {plan.price}/{plan.cycleDays} days
                </option>
              ))}
            </select>
          ) : (
            <div className="w-full p-2 border border-red-300 rounded-lg bg-red-50 text-red-600">
              <div className="text-sm">No membership plans available.</div>
              <div className="text-xs mt-1">Please create plans in the Plans section first.</div>
            </div>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Fee (TTD) *</label>
          <input 
            type="number"
            step="0.01"
            min="0"
            className={`w-full p-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
              errors.some(e => e.includes('Monthly fee')) ? 'border-red-300 bg-red-50' : 'border-gray-300'
            }`}
            placeholder="0.00" 
            value={form.monthlyFee}
            onChange={e => setForm(f => ({...f, monthlyFee: parseFloat(e.target.value) || 0}))}
            required
            disabled={plansLoading}
          />
          <div className="text-xs text-gray-500 mt-1">
            {form.membershipType && `Fee for ${form.membershipType} plan`}
          </div>
        </div>
      </div>
      
      <div className="flex gap-3 pt-4">
        {/* Enhanced submit button with proper Alphalete Athletics styling */}
        <button
          type="button"
          className={`btn text-base font-semibold min-w-[140px] ${
            saving 
              ? 'btn-secondary opacity-70 cursor-not-allowed' 
              : availablePlans.length === 0
                ? 'btn-danger opacity-70 cursor-not-allowed'
                : 'btn-primary hover:shadow-lg'
          }`}
          onClick={saving || availablePlans.length === 0 ? undefined : handleSubmit}
          disabled={saving || availablePlans.length === 0}
        >
          {saving 
            ? '💾 Saving...' 
            : availablePlans.length === 0
              ? '❌ No Plans Available'
              : syncStatus.isOnline 
                ? '➕ Add Member' 
                : '📱 Save Locally'
          }
        </button>
        
        <button
          type="button"
          className="btn btn-secondary text-base font-semibold"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

// Explicit component exports
// --- Comprehensive Edit Member Form Component ---
function EditMemberForm({ member, onSave, onCancel }) {
  console.log('🔧 EditMemberForm component rendered for:', member?.name);
  
  const [form, setForm] = React.useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    membershipType: "",
    monthlyFee: 0,
    status: "Active"
  });
  const [saving, setSaving] = React.useState(false);
  const [errors, setErrors] = React.useState([]);
  const [availablePlans, setAvailablePlans] = React.useState([]);
  const [plansLoading, setPlansLoading] = React.useState(true);

  // Initialize form with member data
  React.useEffect(() => {
    if (member) {
      const nameParts = (member.name || "").split(" ");
      const firstName = nameParts[0] || "";
      const lastName = nameParts.slice(1).join(" ") || "";
      
      setForm({
        firstName,
        lastName,
        email: member.email || "",
        phone: member.phone || "",
        membershipType: member.membershipType || member.membership_type || member.plan || member.planName || "",
        monthlyFee: parseFloat(member.monthly_fee) || 0,
        status: member.status || "Active"
      });
    }
  }, [member]);

  // Load available plans
  React.useEffect(() => {
    const loadPlans = async () => {
      try {
        console.log('📋 Loading available plans for member editing...');
        const { getAll } = await import('./storage');
        const allPlans = await getAll('plans') || [];
        const activePlans = allPlans.filter(p => !p._deleted);
        
        console.log(`📋 Loaded ${activePlans.length} active plans for editing`);
        setAvailablePlans(activePlans);
      } catch (error) {
        console.error('❌ Error loading plans:', error);
        // Fallback to hardcoded plans if storage fails
        const fallbackPlans = [
          { name: 'Basic', price: 55.0, cycleDays: 30 },
          { name: 'Premium', price: 75.0, cycleDays: 30 },
          { name: 'Elite', price: 100.0, cycleDays: 30 },
          { name: 'VIP', price: 150.0, cycleDays: 30 }
        ];
        setAvailablePlans(fallbackPlans);
      } finally {
        setPlansLoading(false);
      }
    };
    
    loadPlans();
  }, []);

  // Validate form
  const validateForm = () => {
    const newErrors = [];
    
    if (!form.firstName.trim()) {
      newErrors.push('First name is required');
    }
    
    if (!form.membershipType) {
      newErrors.push('Please select a membership plan');
    }
    
    if (form.email && form.email.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(form.email.trim())) {
        newErrors.push('Please enter a valid email address');
      }
    }
    
    if (form.phone && form.phone.trim()) {
      const phoneRegex = /^\+?[\d\s\-\(\)]{7,}$/;
      if (!phoneRegex.test(form.phone.trim())) {
        newErrors.push('Please enter a valid phone number');
      }
    }
    
    if (!form.monthlyFee || isNaN(form.monthlyFee) || form.monthlyFee <= 0) {
      newErrors.push('Monthly fee must be a positive number');
    }
    
    setErrors(newErrors);
    return newErrors.length === 0;
  };

  // Handle form submission
  const handleSubmit = async () => {
    console.log('🚀 EditMemberForm submitted for:', member?.name);
    
    if (!validateForm()) {
      console.warn('❌ Form validation failed:', errors);
      return;
    }

    setSaving(true);
    setErrors([]);
    
    try {
      // Calculate due date if it doesn't exist or if plan/billing changed
      let nextDueDate = member.nextDue || member.dueDate;
      
      // If no due date exists or if this is a plan change, calculate new due date
      if (!nextDueDate || form.membershipType !== member.membership_type) {
        const startDate = member.start_date ? new Date(member.start_date) : new Date();
        const billingIntervalDays = member.billing_interval_days || 30;
        const calculatedDue = new Date(startDate);
        calculatedDue.setDate(calculatedDue.getDate() + billingIntervalDays);
        nextDueDate = calculatedDue.toISOString().slice(0, 10);
        console.log('📅 Recalculated due date for member:', nextDueDate);
      }
      
      const updatedMember = {
        ...member,
        name: `${form.firstName} ${form.lastName}`.trim() || form.firstName,
        email: form.email.trim() || '',
        phone: form.phone.trim() || '',
        membershipType: form.membershipType,  // camelCase for consistency
        membership_type: form.membershipType, // snake_case for backend compatibility
        plan: form.membershipType,            // alternative field name
        monthly_fee: parseFloat(form.monthlyFee),
        status: form.status,
        active: form.status === "Active",
        nextDue: nextDueDate, // Ensure due date is set
        dueDate: nextDueDate, // Alternative field name
        joinedOn: member.joinedOn || member.start_date || new Date().toISOString().slice(0, 10)
      };
      
      console.log('📝 Updating member with due date:', {
        name: updatedMember.name,
        nextDue: updatedMember.nextDue,
        plan: updatedMember.membership_type
      });
      
      if (onSave) {
        await onSave(updatedMember);
        alert(`✅ Member "${updatedMember.name}" updated successfully!`);
      } else {
        throw new Error('No save handler provided');
      }
    } catch (error) {
      console.error('❌ Error updating member:', error);
      setErrors([error.message || 'Failed to update member. Please try again.']);
    } finally {
      setSaving(false);
    }
  };

  // Update monthly fee when membership plan changes
  const handleMembershipTypeChange = (planName) => {
    const selectedPlan = availablePlans.find(p => p.name === planName);
    if (selectedPlan) {
      console.log('📋 Plan selected for edit:', selectedPlan.name, 'Fee:', selectedPlan.price);
      setForm(f => ({
        ...f, 
        membershipType: planName,
        monthlyFee: parseFloat(selectedPlan.price) || 0
      }));
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-semibold mb-3">Edit Member: {member?.name}</h1>
      
      {/* Current Member Information Display */}
      <div className="card mb-4 bg-blue-50 border-blue-200">
        <div className="card-body">
          <h3 className="font-semibold text-lg mb-2">Current Information</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <strong>Name:</strong> {member?.name}
            </div>
            <div>
              <strong>Email:</strong> {member?.email || 'Not provided'}
            </div>
            <div>
              <strong>Phone:</strong> {member?.phone || 'Not provided'}
            </div>
            <div>
              <strong>Membership Plan:</strong> {member?.membership_type || 'No plan'}
            </div>
            <div>
              <strong>Monthly Fee:</strong> TTD {member?.monthly_fee || 0}
            </div>
            <div>
              <strong>Due Date:</strong> {member?.nextDue || member?.dueDate || 'Not set'}
            </div>
            <div>
              <strong>Status:</strong> 
              <span className={`ml-1 px-2 py-1 rounded-full text-xs ${
                member?.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {member?.status || 'Unknown'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Edit Form */}
      <div className="card">
        <div className="card-body">
          {/* Error Messages */}
          {errors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <div className="text-red-800 font-medium mb-1">Please fix the following errors:</div>
              <ul className="list-disc list-inside text-sm text-red-700">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <input 
              type="text"
              className="btn-ghost border p-2 rounded"
              placeholder="First name"
              value={form.firstName}
              onChange={e => setForm(f => ({...f, firstName: e.target.value}))}
            />
            <input 
              type="text"
              className="btn-ghost border p-2 rounded"
              placeholder="Last name"
              value={form.lastName}
              onChange={e => setForm(f => ({...f, lastName: e.target.value}))}
            />
            <input 
              type="email"
              className="btn-ghost border p-2 rounded"
              placeholder="Email"
              value={form.email}
              onChange={e => setForm(f => ({...f, email: e.target.value}))}
            />
            <input 
              type="tel"
              className="btn-ghost border p-2 rounded"
              placeholder="Phone"
              value={form.phone}
              onChange={e => setForm(f => ({...f, phone: e.target.value}))}
            />
            {plansLoading ? (
              <div className="btn-ghost border p-2 rounded bg-gray-50 text-gray-500">
                Loading plans...
              </div>
            ) : (
              <select
                className="btn-ghost border p-2 rounded"
                value={form.membershipType}
                onChange={e => handleMembershipTypeChange(e.target.value)}
              >
                <option value="">Select a plan...</option>
                {availablePlans.map(plan => (
                  <option key={plan.name} value={plan.name}>
                    {plan.name} - TTD {plan.price}/{plan.cycleDays || 30} days
                  </option>
                ))}
              </select>
            )}
            <input 
              type="number"
              step="0.01"
              min="0"
              className="btn-ghost border p-2 rounded"
              placeholder="Monthly Fee"
              value={form.monthlyFee}
              onChange={e => setForm(f => ({...f, monthlyFee: parseFloat(e.target.value) || 0}))}
            />
            <select
              className="btn-ghost border p-2 rounded sm:col-span-2"
              value={form.status}
              onChange={e => setForm(f => ({...f, status: e.target.value}))}
            >
              <option value="Active">Active</option>
              <option value="Inactive">Inactive</option>
              <option value="Suspended">Suspended</option>
            </select>
          </div>
        </div>
        <div className="p-4 flex gap-3">
          <button 
            type="button"
            className="btn-primary"
            onClick={handleSubmit}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button 
            type="button"
            className="btn-secondary" 
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

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
  InstallPrompt,
  AddMember,
  RecordPayment
};

export default Components;
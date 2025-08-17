import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from 'react-router-dom';
import gymStorage from "./storage";

const Dashboard = () => {
  const navigate = useNavigate();
  const [members, setMembers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [settings, setSettings] = useState({ billingCycleDays: 30, graceDays: 0, dueSoonDays: 3 });
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all"); // New state for filtering
  
  const todayISO = new Date().toISOString().slice(0,10);

  // Load dashboard data function
  const loadDashboardData = async () => {
    try {
      const [m, p, s] = await Promise.all([
        gymStorage.getAllMembers?.() ?? [],
        gymStorage.getAllPayments?.() ?? [],
        gymStorage.getSetting?.('gymSettings', {}) ?? {}
      ]);
      setMembers(Array.isArray(m) ? m : []);
      setPayments(Array.isArray(p) ? p : []);
      setSettings(prev => ({ ...prev, ...(s || {}) }));
    } catch (error) {
      console.error('Dashboard: Error loading data:', error);
    }
  };

  // Load data on mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Listen for data changes event
  useEffect(() => {
    const handleDataChanged = () => {
      console.log('Dashboard: Data changed event received, refreshing...');
      loadDashboardData();
    };

    window.addEventListener('alphalete:data-changed', handleDataChanged);

    return () => {
      window.removeEventListener('alphalete:data-changed', handleDataChanged);
    };
  }, []);

  const dueSoonDays = Number(settings.dueSoonDays ?? settings.reminderDays ?? 3) || 3;

  const parseISO = (s) => s ? new Date(s) : null;
  const isOverdue  = (iso) => !!iso && parseISO(iso) < new Date(todayISO);
  const isDueToday = (iso) => iso === todayISO;
  const isDueSoon  = (iso) => {
    if (!iso) return false;
    const d = parseISO(iso), t = new Date(todayISO);
    const diff = Math.round((d - t) / 86400000);
    return diff > 0 && diff <= dueSoonDays;
  };

  const kpis = useMemo(() => {
    const activeCount = members.filter(m => (m.status || "Active") === "Active").length;
    const startOfMonth = new Date(todayISO.slice(0,7) + "-01");
    const newMTD = members.filter(m => {
      const c = parseISO(m.createdAt?.slice(0,10) || m.joinDate);
      return c && c >= startOfMonth;
    }).length;
    const revenueMTD = payments
      .filter(p => p.paidOn && p.paidOn.slice(0,7) === todayISO.slice(0,7))
      .reduce((sum,p)=> sum + Number(p.amount||0), 0);
    const overdueCount = members.filter(m => isOverdue(m.nextDue || m.dueDate || m.next_payment_date)).length;
    const dueSoonCount = members.filter(m => isDueSoon(m.nextDue || m.dueDate || m.next_payment_date)).length;
    const dueTodayCount = members.filter(m => isDueToday(m.nextDue || m.dueDate || m.next_payment_date)).length;
    
    return { activeCount, newMTD, revenueMTD, overdueCount, dueSoonCount, dueTodayCount };
  }, [members, payments, todayISO]);

  const dueToday = useMemo(() =>
    members.filter(m => isDueToday(m.nextDue || m.dueDate || m.next_payment_date))
           .sort((a,b)=> (a.name||"").localeCompare(b.name||""))
           .slice(0,5), [members, todayISO]);

  const overdue = useMemo(() =>
    members.filter(m => isOverdue(m.nextDue || m.dueDate || m.next_payment_date))
           .sort((a,b)=> (new Date(a.nextDue || a.dueDate || a.next_payment_date) - new Date(b.nextDue || b.dueDate || b.next_payment_date)))
           .slice(0,5), [members, todayISO]);

  const dueSoon = useMemo(() =>
    members.filter(m => isDueSoon(m.nextDue || m.dueDate || m.next_payment_date))
           .sort((a,b)=> (new Date(a.nextDue || a.dueDate || a.next_payment_date) - new Date(b.nextDue || b.dueDate || b.next_payment_date)))
           .slice(0,5), [members, todayISO]);

  const activeMembers = useMemo(() =>
    members.filter(m => (m.status || "Active") === "Active")
           .sort((a,b)=> (a.name||"").localeCompare(b.name||""))
           .slice(0,10), [members]);

  // Get filtered members based on active filter
  const getFilteredMembers = () => {
    switch(activeFilter) {
      case "active":
        return members.filter(m => (m.status || "Active") === "Active");
      case "due-today":
        return members.filter(m => isDueToday(m.nextDue || m.dueDate || m.next_payment_date));
      case "due-soon":
        return members.filter(m => isDueSoon(m.nextDue || m.dueDate || m.next_payment_date));
      case "overdue":
        return members.filter(m => isOverdue(m.nextDue || m.dueDate || m.next_payment_date));
      default:
        return members;
    }
  };

  const filteredMembers = useMemo(() => {
    let baseMembers = getFilteredMembers();
    const q = search.trim().toLowerCase();
    if (!q) return baseMembers;
    return baseMembers.filter(m =>
      [m.name, m.email, m.phone].some(v => (v||"").toLowerCase().includes(q))
    );
  }, [members, search, activeFilter]);

  // Bridge to Payments tab → open "Record Payment" for member
  const goRecordPayment = (member) => {
    try { localStorage.setItem("pendingPaymentMemberId", member.id); } catch {}
    navigate("/payments");
  };

  // Lightweight reminder (WA/email) without depending on PaymentTracking internals
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

  const deleteMember = async (member) => {
    if (!member || !member.id) {
      console.error('❌ Invalid member data for deletion');
      return;
    }

    // Show confirmation dialog
    const confirmDelete = window.confirm(
      `Are you sure you want to delete "${member.name}"?\n\nThis action cannot be undone and will permanently remove:\n• Member profile\n• Payment history\n• All associated data`
    );

    if (!confirmDelete) {
      console.log('🚫 Member deletion cancelled by user');
      return;
    }

    try {
      console.log(`🗑️ Deleting member: ${member.name} (ID: ${member.id})`);
      
      // Call backend API to delete member
      const response = await fetch(`${import.meta.env.REACT_APP_BACKEND_URL}/clients/${member.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log(`✅ Successfully deleted member: ${member.name}`);
        
        // Update local state by removing the deleted member
        setMembers(prevMembers => prevMembers.filter(m => m.id !== member.id));
        
        // Show success message
        alert(`✅ "${member.name}" has been successfully deleted.`);
      } else {
        const errorData = await response.text();
        console.error(`❌ Failed to delete member: HTTP ${response.status}`, errorData);
        alert(`❌ Failed to delete "${member.name}". Please try again.\n\nError: ${response.status} ${response.statusText}`);
      }
    } catch (error) {
      console.error('❌ Error during member deletion:', error);
      alert(`❌ An error occurred while deleting "${member.name}". Please check your connection and try again.\n\nError: ${error.message}`);
    }
  };

  // Tiny revenue sparkline (last 8 weeks)
  const revenuePoints = useMemo(() => {
    const byWeek = new Map();
    const d = new Date(todayISO);
    for (let i=0;i<56;i++){ // ensure 8 weeks of buckets exist (even if 0)
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
  }, [payments, todayISO]);
  const maxRev = Math.max(1, ...revenuePoints);
  const spark = (w=160, h=40) => {
    const step = w / Math.max(1, revenuePoints.length-1);
    const pts = revenuePoints.map((v,i)=>{
      const x = i*step;
      const y = h - (v/maxRev)*h;
      return `${x},${y}`;
    }).join(" ");
    return (
      <svg width={w} height={h} className="overflow-visible">
        <polyline fill="none" stroke="currentColor" strokeWidth="2" points={pts} />
      </svg>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header Section */}
      <div className="bg-card shadow-sm border-b">
        <div className="container px-4 sm:px-6 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-gray-900" id="dashboard-header">Dashboard</h1>
              <p className="text-sm md:text-base text-gray-500 leading-6">Welcome back! Here's what's happening at your gym today.</p>
            </div>
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <button 
                type="button" 
                className="btn btn-primary w-full md:w-auto"
                onClick={() => navigate('/payments')}
              >
                + Record Payment
              </button>
              <button 
                type="button" 
                className="btn btn-secondary w-full md:w-auto"
                onClick={() => navigate('/add-member')}
              >
                + Add Member
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container px-4 sm:px-6 py-4 sm:py-6">
        {/* Search Bar */}
        <div className="mb-6">
          <input
            value={search}
            onChange={(e)=>setSearch(e.target.value)}
            placeholder="Search members by name, phone, email..."
            className="w-full rounded-xl border border-gray-300 px-4 py-3 text-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        {/* Clickable KPI Cards Grid */}
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4 mb-6">
          {/* Active Members */}
          <button 
            onClick={() => setActiveFilter(activeFilter === "active" ? "all" : "active")}
            className={`bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3 transition-all hover:shadow-md text-left w-full ${
              activeFilter === "active" ? "ring-2 ring-indigo-500 bg-indigo-50" : ""
            }`}
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-indigo-600/10 text-indigo-600">
              👥
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{kpis.activeCount}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Active</div>
              {activeFilter === "active" && <div className="text-xs text-indigo-600 mt-1">Filter active</div>}
            </div>
          </button>

          {/* Due Soon */}
          <button 
            onClick={() => setActiveFilter(activeFilter === "due-soon" ? "all" : "due-soon")}
            className={`bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3 transition-all hover:shadow-md text-left w-full ${
              activeFilter === "due-soon" ? "ring-2 ring-warning bg-warning/10" : ""
            }`}
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-warning/10 text-warning">
              🕐
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{kpis.dueSoonCount}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Due Soon</div>
              {activeFilter === "due-soon" && <div className="text-xs text-warning mt-1">Filter active</div>}
            </div>
          </button>

          {/* Overdue */}
          <button 
            onClick={() => setActiveFilter(activeFilter === "overdue" ? "all" : "overdue")}
            className={`bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3 transition-all hover:shadow-md text-left w-full ${
              activeFilter === "overdue" ? "ring-2 ring-danger bg-danger/10" : ""
            }`}
          >
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-danger/10 text-danger">
              ⚠️
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">{kpis.overdueCount}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Overdue</div>
              {activeFilter === "overdue" && <div className="text-xs text-danger mt-1">Filter active</div>}
            </div>
          </button>

          {/* Total Amount Owed */}
          <div className="bg-card rounded-xl shadow-sm p-3 md:p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full flex items-center justify-center bg-success/10 text-success">
              💰
            </div>
            <div>
              <div className="text-xl md:text-2xl font-bold text-gray-900">${members.filter(m => isOverdue(m.nextDue || m.dueDate || m.next_payment_date) || isDueToday(m.nextDue || m.dueDate || m.next_payment_date)).reduce((sum,m)=> sum + Number(m.monthly_fee||m.amount||0), 0).toFixed(2)}</div>
              <div className="text-[11px] md:text-xs uppercase tracking-wide text-gray-500">Amount Owed</div>
            </div>
          </div>
        </div>

        {/* Filter Status Bar */}
        {activeFilter !== "all" && (
          <div className="mb-4">
            <div className="bg-card rounded-xl shadow-sm p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Showing:</span>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  activeFilter === "active" ? "bg-indigo-600/10 text-indigo-600" :
                  activeFilter === "due-soon" ? "bg-warning/10 text-warning" :
                  activeFilter === "overdue" ? "bg-danger/10 text-danger" :
                  "bg-gray-100 text-gray-700"
                }`}>
                  {activeFilter === "active" ? "Active Members" :
                   activeFilter === "due-soon" ? "Due Soon" :
                   activeFilter === "overdue" ? "Overdue Members" : "All Members"} 
                  ({filteredMembers.length})
                </span>
              </div>
              <button 
                onClick={() => setActiveFilter("all")}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear Filter
              </button>
            </div>
          </div>
        )}

        {/* Member List */}
        <div className="bg-card rounded-xl shadow-sm mb-6">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center">
              👥
              <span className="ml-2">
                {activeFilter === "all" ? "All Members" :
                 activeFilter === "active" ? "Active Members" :
                 activeFilter === "due-soon" ? "Due Soon" :
                 activeFilter === "overdue" ? "Overdue Members" : "Members"}
                {filteredMembers.length > 0 && ` (${filteredMembers.length})`}
              </span>
            </h3>
          </div>
          
          <div className="p-4">
            {filteredMembers.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-gray-400 text-sm">
                  {search ? `No members found matching "${search}"` : 
                   activeFilter === "active" ? "No active members found." :
                   activeFilter === "due-soon" ? "No members due soon." :
                   activeFilter === "overdue" ? "No overdue members 🎉" :
                   "No members found."}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredMembers.map(m => {
                  const dueDate = m.nextDue || m.dueDate || m.next_payment_date;
                  const isOverdueMember = isOverdue(dueDate);
                  const isDueTodayMember = isDueToday(dueDate);
                  const isDueSoonMember = isDueSoon(dueDate);
                  
                  return (
                    <div key={m.id} className="bg-card rounded-xl shadow-sm px-3 py-2 md:p-3 flex items-center justify-between hover:shadow-md transition-shadow">
                      <div className="flex items-center space-x-3">
                        {/* Avatar */}
                        <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600">
                          {(m.name || "").split(' ').map(n => n[0]).join('').toUpperCase() || "?"}
                        </div>
                        
                        {/* Member Info */}
                        <div>
                          <div className="font-medium text-gray-900">{m.name || "(No name)"}</div>
                          <div className="text-sm text-gray-500">
                            {m.email && <span>{m.email}</span>}
                            {m.email && m.phone && <span> • </span>}
                            {m.phone && <span>{m.phone}</span>}
                          </div>
                          {dueDate && (
                            <div className={`text-xs mt-1 ${
                              isOverdueMember ? "text-danger font-semibold" :
                              isDueTodayMember ? "text-warning font-semibold" :
                              isDueSoonMember ? "text-warning" :
                              "text-gray-500"
                            }`}>
                              Due: {dueDate}
                              {isOverdueMember && " (Overdue)"}
                              {isDueTodayMember && " (Due Today)"}
                              {isDueSoonMember && " (Due Soon)"}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Status Badge and Actions */}
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                          (m.status || "Active") === "Active" ? "bg-success/10 text-success" : "bg-gray-100 text-gray-700"
                        }`}>
                          {m.status || "Active"}
                        </span>
                        {(isOverdueMember || isDueTodayMember || isDueSoonMember) && (
                          <>
                            <button 
                              type="button" 
                              className="p-2 rounded-lg hover:bg-slate-50 transition-colors" 
                              onClick={() => goRecordPayment(m)}
                              aria-label="Record payment"
                            >
                              💳
                            </button>
                            <button 
                              type="button" 
                              className="p-2 rounded-lg hover:bg-slate-50 transition-colors" 
                              onClick={() => sendReminder(m)}
                              aria-label="Send reminder"
                            >
                              📨
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Revenue Chart */}
          <div className="bg-card rounded-xl shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                📊
                <span className="ml-2">Collections (last 8 weeks)</span>
              </h3>
            </div>
            <div className="p-4">
              <div className="flex items-center justify-center text-gray-400 h-20">
                {spark()}
              </div>
              <button 
                className="text-xs text-indigo-600 hover:text-indigo-800 mt-2" 
                onClick={() => navigate('/reports')}
              >
                View Reports →
              </button>
            </div>
          </div>
          
          {/* Plans Snapshot */}
          <div className="bg-card rounded-xl shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                📋
                <span className="ml-2">Plans Snapshot</span>
              </h3>
            </div>
            <div className="p-4">
              <PlansMini />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PlansMini = () => {
  const navigate = useNavigate();
  const [members, setMembers] = useState([]);

  useEffect(() => {
    (async () => {
      const m = (await gymStorage.getAllMembers?.()) || [];
      setMembers(Array.isArray(m)? m : []);
    })();
  }, []);

  const plans = useMemo(() => {
    const planCounts = {};
    members.forEach(m => { 
      const planName = m.membershipType || m.plan || 'Standard';
      planCounts[planName] = (planCounts[planName] || 0) + 1; 
    });
    return planCounts;
  }, [members]);

  if (Object.keys(plans).length === 0) {
    return <div className="text-sm text-gray-500">No plans yet.</div>;
  }

  return (
    <div className="space-y-1">
      {Object.entries(plans).map(([name, count]) => (
        <div key={name} className="flex justify-between text-sm">
          <span>{name}</span>
          <span>{count}</span>
        </div>
      ))}
    </div>
  );
};

export default Dashboard;
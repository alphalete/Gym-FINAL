import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from 'react-router-dom';
import gymStorage from "./storage";

const Dashboard = () => {
  const navigate = useNavigate();
  const [members, setMembers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [settings, setSettings] = useState({ billingCycleDays: 30, graceDays: 0, dueSoonDays: 3 });
  const [search, setSearch] = useState("");
  
  // KPI scroll tracking state
  const kpiScrollerRef = React.useRef(null);
  const [kpiPage, setKpiPage] = React.useState(0);
  const kpiCount = 4; // we have 4 colorful KPI cards
  
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

  // Recompute page on scroll (mobile only)
  React.useEffect(() => {
    const el = kpiScrollerRef.current;
    if (!el) return;
    const onScroll = () => {
      const w = el.getBoundingClientRect().width || el.clientWidth || 1;
      const page = Math.round(el.scrollLeft / Math.max(1, w * 0.72)); // matches min-w 72%
      setKpiPage(Math.max(0, Math.min(kpiCount - 1, page)));
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, [kpiCount]);

  // Snap to a page when a dot is tapped
  function snapToKpi(idx) {
    const el = kpiScrollerRef.current;
    if (!el) return;
    const w = el.getBoundingClientRect().width || el.clientWidth || 1;
    const itemWidth = Math.max(1, w * 0.72); // same as min-w-[72%]
    el.scrollTo({ left: itemWidth * idx, behavior: 'smooth' });
  }

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
    const overdueCount = members.filter(m => isOverdue(m.nextDue)).length;
    return { activeCount, newMTD, revenueMTD, overdueCount };
  }, [members, payments, todayISO]);

  const dueToday = useMemo(() =>
    members.filter(m => isDueToday(m.nextDue))
           .sort((a,b)=> (a.name||"").localeCompare(b.name||""))
           .slice(0,5), [members, todayISO]);

  const overdue = useMemo(() =>
    members.filter(m => isOverdue(m.nextDue))
           .sort((a,b)=> (new Date(a.nextDue) - new Date(b.nextDue)))
           .slice(0,5), [members, todayISO]);

  const filteredMembers = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return members;
    return members.filter(m =>
      [m.name, m.email, m.phone].some(v => (v||"").toLowerCase().includes(q))
    );
  }, [members, search]);

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
    <div className="p-4 lg:p-6 space-y-6">
      {/* Search & Quick Actions */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <input
          value={search}
          onChange={(e)=>setSearch(e.target.value)}
          placeholder="Search members by name, phone, email..."
          className="rounded-xl border px-3 py-2 w-full sm:w-96"
        />
        <div className="flex gap-2">
          <button className="rounded-xl px-3 py-2 border" onClick={()=> navigate('/add-client')}>+ Add Member</button>
          <button className="rounded-xl px-3 py-2 border" onClick={()=> navigate('/payments')}>+ Add Payment</button>
          <button
            className="rounded-xl px-3 py-2 border"
            onClick={()=> overdue.concat(dueToday).forEach(m=>sendReminder(m))}
            title="Send reminders to Due Today + Overdue"
          >
            Send Reminders
          </button>
        </div>
      </div>

      {/* KPI cards — swipeable on mobile, grid on larger screens */}
      <div className="relative">
        {/* Optional scroll cues (fade edges on mobile) */}
        <div className="pointer-events-none absolute left-0 top-0 h-full w-6 bg-gradient-to-r from-white to-transparent lg:hidden z-10" />
        <div className="pointer-events-none absolute right-0 top-0 h-full w-6 bg-gradient-to-l from-white to-transparent lg:hidden z-10" />
        
        <div className="lg:grid lg:grid-cols-4 lg:gap-3">
          {/* Mobile: horizontal scroll with snap */}
          <div 
            ref={kpiScrollerRef}
            role="region" 
            aria-label="Key performance indicators"
            className="flex lg:block gap-3 overflow-x-auto lg:overflow-visible snap-x snap-mandatory px-1 -mx-1 pb-2 hide-scrollbar"
          >
            <div className="min-w-[72%] sm:min-w-[320px] snap-start">
              <div className="bg-white rounded-2xl border p-4">
                <h3 className="sr-only">Active Members</h3>
                <div className="text-gray-500 text-sm">ACTIVE MEMBERS</div>
                <div className="text-2xl font-semibold">{kpis.activeCount}</div>
              </div>
            </div>

            <div className="min-w-[72%] sm:min-w-[320px] snap-start">
              <div className="bg-white rounded-2xl border p-4">
                <h3 className="sr-only">Payments Due Today</h3>
                <div className="text-gray-500 text-sm">PAYMENTS DUE TODAY</div>
                <div className="text-2xl font-semibold">{dueToday.length}</div>
              </div>
            </div>

            <div className="min-w-[72%] sm:min-w-[320px] snap-start">
              <div className="bg-white rounded-2xl border p-4">
                <h3 className="sr-only">Overdue Accounts</h3>
                <div className="text-gray-500 text-sm">OVERDUE ACCOUNTS</div>
                <div className="text-2xl font-semibold">{kpis.overdueCount}</div>
              </div>
            </div>

            <div className="min-w-[72%] sm:min-w-[320px] snap-start">
              <div className="bg-white rounded-2xl border p-4">
                <h3 className="sr-only">Total Amount Owed</h3>
                <div className="text-gray-500 text-sm">TOTAL AMOUNT OWED</div>
                <div className="text-2xl font-semibold">${members.filter(m => isOverdue(m.nextDue) || isDueToday(m.nextDue)).reduce((sum,m)=> sum + Number(m.monthlyFee||m.amount||0), 0).toFixed(2)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

{/* KPI dots — mobile only */}
<div className="flex items-center justify-center gap-3 py-4 lg:hidden">
  {Array.from({ length: kpiCount }).map((_, i) => (
    <button
      key={i}
      type="button"
      aria-label={`Go to KPI ${i + 1}`}
      onClick={() => snapToKpi(i)}
      className={[
        "kpi-dot h-4 w-4 rounded-full transition-all duration-200",
        i === kpiPage ? "scale-125 kpi-dot-active" : "opacity-70 hover:opacity-90"
      ].join(" ")}
    />
  ))}
</div>

{/* === New actionable sections start === */}
<div className="mt-4 space-y-6">

  {/* Quick Actions */}
  <div className="flex flex-col sm:flex-row gap-2">
    <button
      className="rounded-xl border px-3 py-2"
      onClick={()=> navigate('/payments')}
    >
      + Add Payment
    </button>
    <button
      className="rounded-xl border px-3 py-2"
      onClick={()=> navigate('/add-client')}
    >
      + Add Member
    </button>
    <button
      className="rounded-xl border px-3 py-2"
      onClick={()=> overdue.concat(dueToday).forEach(m=>sendReminder(m))}
      title="Send reminders to Due Today + Overdue"
    >
      Send Reminders
    </button>
  </div>

  {/* Due Today list */}
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
          <button className="text-sm rounded-lg border px-2 py-1" onClick={()=> goRecordPayment(m)}>Record</button>
          <button className="text-sm rounded-lg border px-2 py-1" onClick={()=> sendReminder(m)}>Remind</button>
        </div>
      </div>
    ))}
  </div>

  {/* Overdue list */}
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
          <button className="text-sm rounded-lg border px-2 py-1" onClick={()=> goRecordPayment(m)}>Record</button>
          <button className="text-sm rounded-lg border px-2 py-1" onClick={()=> sendReminder(m)}>Remind</button>
        </div>
      </div>
    ))}
  </div>

  {/* Plans snapshot + Trends */}
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
    <div className="bg-white rounded-2xl border p-4 lg:col-span-2">
      <div className="flex items-center justify-between mb-2">
        <div className="font-semibold">Collections (last 8 weeks)</div>
        <button className="text-xs text-gray-500" onClick={()=> navigate('/reports')}>View Reports</button>
      </div>
      <div className="text-gray-400">{spark()}</div>
    </div>
    <div className="bg-white rounded-2xl border p-4">
      <div className="font-semibold mb-2">Plans snapshot</div>
      <PlansMini />
    </div>
  </div>
</div>
{/* === New actionable sections end === */}

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
import React, { useEffect, useMemo, useState } from "react";
import gymStorage, { getAll as getAllStore, getPlanById, upsertMemberWithPlanSnapshot, getSetting as getSettingNamed, saveSetting as saveSettingNamed } from "./storage";
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';
import PaymentsHistory from './components/payments/PaymentsHistory';
import { nextDueDateFromJoin, isOverdue, nextDueAfterPayment } from "./billing";
import LockBadge from "./LockBadge";
import { requirePinIfEnabled } from './pinlock';

/* Utilities */
function navigate(tab) {
  const t = String(tab).toLowerCase();
  try { location.hash = `#tab=${t}`; } catch {}
  if (typeof window.setActiveTab === 'function') window.setActiveTab(t);
  else window.dispatchEvent(new CustomEvent('NAVIGATE', { detail: t }));
}
function addDaysISO(iso, days){ const d=new Date(iso); d.setDate(d.getDate()+Number(days||0)); return d.toISOString().slice(0,10); }
/* Option A: keep cadence; roll forward by whole cycles until nextDue > paidOn */
function computeNextDueOptionA(prevNextDueISO, paidOnISO, cycleDays){
  const cycle = Number(cycleDays || 30);
  const paid = new Date(paidOnISO);
  if (!prevNextDueISO) return addDaysISO(paidOnISO, cycle);
  let nextDue = new Date(prevNextDueISO);
  while (nextDue <= paid) nextDue.setDate(nextDue.getDate() + cycle);
  return nextDue.toISOString().slice(0,10);
}
function openWhatsApp(text, phone){
  const msg = encodeURIComponent(text || "");
  const pn  = phone ? encodeURIComponent(String(phone)) : "";
  const url = pn ? `https://wa.me/${pn}?text=${msg}` : `https://wa.me/?text=${msg}`;
  window.open(url, "_blank");
}
function openEmail(subject, body, to){
  const s=encodeURIComponent(subject||""); const b=encodeURIComponent(body||""); const t=to?encodeURIComponent(to):"";
  window.location.href = `mailto:${t}?subject=${s}&body=${b}`;
}
function buildReminder(m){
  const due = m.nextDue || "your due date";
  const amt = m.fee != null ? `$${Number(m.fee).toFixed(2)}` : "your fee";
  return `Hi ${m.name||''}, this is a reminder from Alphalete Club. ${amt} is due on ${due}.`;
}
function shareFallback(text){
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

  // Show minimal loading indicator
  if (loading) {
    return <div className="p-4 text-sm text-gray-500">Loading…</div>;
  }

  // Simple KPIs
  const activeCount = clients.filter(m => (m.status || "Active") === "Active").length;
  
  const todayStr = todayISO;
  const dueToday = clients.filter(m => {
    if (m.status !== "Active") return false;
    return m.nextDue === todayStr;
  });
  
  const overdue = clients.filter(m => {
    if (m.status !== "Active") return false;
    const due = m.nextDue;
    if (!due) return false;
    return new Date(due) < new Date(todayISO);
  });

  const revenueMTD = payments
    .filter(p => p.paidOn && p.paidOn.slice(0,7) === todayISO.slice(0,7))
    .reduce((sum,p)=> sum + Number(p.amount||0), 0);

  function goRecordPayment(m) {
    localStorage.setItem("pendingPaymentMemberId", String(m.id));
    navigate('payments');
  }

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
          <div className="text-2xl font-bold text-blue-600">{dueToday.length}</div>
          <div className="text-sm text-gray-600">Due Today</div>
        </div>
        
        <div className="bg-white rounded-xl border p-4">
          <div className="text-2xl font-bold text-red-600">{overdue.length}</div>
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

      {/* Dev Inspector */}
      <button type="button" className="fixed bottom-20 right-4 z-[9998] border rounded px-2 py-1 text-xs bg-white"
        onClick={async()=>{
          const m = (await gymStorage.getAll('members')).filter(x=>x.id!=='__selftest__');
          const p = await gymStorage.getAll('payments');
          alert(`Members: ${m.length}\nPayments: ${p.length}`);
        }}>Debug</button>

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

      {/* Due Today */}
      {dueToday.length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold mb-2 text-blue-600">Due Today ({dueToday.length})</h3>
          <div className="space-y-2">
            {dueToday.map(m => (
              <div key={m.id} className="flex items-center justify-between border rounded-xl px-3 py-2">
                <div>
                  <div className="font-medium">{m.name || "(no name)"}</div>
                  <div className="text-xs text-gray-500">{m.planName ? `${m.planName} • $${Number(m.fee||0).toFixed(2)}` : "No plan"}</div>
                </div>
                <div className="flex gap-2">
                  <button type="button" className="text-xs border rounded px-2 py-1" onClick={()=>goRecordPayment(m)}>Record</button>
                  <button type="button" className="text-xs border rounded px-2 py-1"
                    onClick={()=> openWhatsApp(buildReminder(m), m.phone)}>WhatsApp</button>
                  <button type="button" className="text-xs border rounded px-2 py-1"
                    onClick={()=> openEmail("Payment Reminder", buildReminder(m), m.email)}>Email</button>
                  <button type="button" className="text-xs border rounded px-2 py-1"
                    onClick={()=> shareFallback(buildReminder(m))}>Share</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Overdue */}
      {overdue.length > 0 && (
        <div className="bg-white rounded-xl border p-4">
          <h3 className="font-semibold mb-2 text-red-600">Overdue ({overdue.length})</h3>
          <div className="space-y-2">
            {overdue.map(m => (
              <div key={m.id} className="flex items-center justify-between border rounded-xl px-3 py-2">
                <div>
                  <div className="font-medium">{m.name || "(no name)"}</div>
                  <div className="text-xs text-gray-500">
                    {m.planName ? `${m.planName} • $${Number(m.fee||0).toFixed(2)}` : "No plan"}
                    {m.nextDue && ` • Due: ${m.nextDue}`}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button type="button" className="text-xs border rounded px-2 py-1" onClick={()=>goRecordPayment(m)}>Record</button>
                  <button type="button" className="text-xs border rounded px-2 py-1"
                    onClick={()=> openWhatsApp(buildReminder(m), m.phone)}>WhatsApp</button>
                  <button type="button" className="text-xs border rounded px-2 py-1"
                    onClick={()=> openEmail("Payment Reminder", buildReminder(m), m.email)}>Email</button>
                  <button type="button" className="text-xs border rounded px-2 py-1"
                    onClick={()=> shareFallback(buildReminder(m))}>Share</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
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

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Members</h1>
        <button 
          type="button" 
          className="border rounded px-3 py-2 bg-blue-500 text-white hover:bg-blue-600" 
          onClick={() => { 
            setEditingClient(null); 
            setForm({ name:"", email:"", phone:"", planId:"" }); 
            setIsAddingClient(true); 
          }}
        >
          + Add Member
        </button>
      </div>

      {loading ? (
        <div className="text-center py-8">Loading...</div>
      ) : (
        <div className="space-y-2">
          {clients.map(c => (
            <div key={c.id} className="flex items-center justify-between border rounded-xl px-3 py-2">
              <div>
                <div className="font-medium">{c.name || "(no name)"}</div>
                <div className="text-xs text-gray-500">
                  {c.email || "—"} • {c.phone || "—"} • {c.status || "Active"}
                  {c.joinDate && ` • Joined ${c.joinDate}`}
                </div>
                {c.planName
                  ? <div className="text-xs text-gray-500">{c.planName} • ${Number(c.fee||0).toFixed(2)} / {c.cycleDays||30}d</div>
                  : <div className="text-xs text-gray-400">No plan</div>}
                {c.nextDue && <div className="text-xs">Next due: {c.nextDue}</div>}
              </div>
              <div className="flex gap-2">
                <button 
                  type="button" 
                  className="text-xs border rounded px-2 py-1 hover:bg-gray-50" 
                  onClick={() => { 
                    setEditingClient(c); 
                    setForm({ name:c.name||"", email:c.email||"", phone:c.phone||"", planId: c.planId || "" }); 
                    setIsAddingClient(true); 
                  }}
                >
                  Edit
                </button>
                <button 
                  type="button" 
                  className="text-xs border rounded px-2 py-1" 
                  onClick={() => toggleStatus(c)}
                >
                  {c.status === "Active" ? "Deactivate" : "Activate"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isAddingClient && (
        <div className="fixed inset-0 bg-black/20 z-[999] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-4 w-full max-w-md space-y-3">
            <div className="text-lg font-semibold">{editingClient ? "Edit Member" : "Add Member"}</div>
            <form onSubmit={(e)=>e.preventDefault()}>
              <input 
                className="border rounded px-3 py-2 w-full mb-3" 
                placeholder="Full Name" 
                value={form.name} 
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              />
              <input 
                className="border rounded px-3 py-2 w-full mb-3" 
                type="email"
                placeholder="Email Address" 
                value={form.email} 
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              />
              <input 
                className="border rounded px-3 py-2 w-full mb-3" 
                type="tel"
                placeholder="Phone Number" 
                value={form.phone} 
                onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
              />
              <select className="border rounded px-3 py-2 w-full mb-3" value={form.planId}
                onChange={e=>setForm(f=>({ ...f, planId:e.target.value }))}>
                <option value="">No plan</option>
                {plans.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.name} — ${Number(p.price||0).toFixed(2)} / {p.cycleDays||30}d
                  </option>
                ))}
              </select>
              <div className="flex justify-end gap-2 pt-2">
                <button 
                  type="button" 
                  className="border rounded px-3 py-2 hover:bg-gray-50" 
                  onClick={() => setIsAddingClient(false)}
                >
                  Cancel
                </button>
                <button 
                  type="button" 
                  className="border rounded px-3 py-2 bg-blue-500 text-white hover:bg-blue-600" 
                  onClick={save}
                >
                  {editingClient ? "Save Changes" : "Add Member"}
                </button>
              </div>
            </form>
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
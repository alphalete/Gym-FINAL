import React, { useEffect, useMemo, useState } from "react";
import gymStorage, { getAll as getAllStore, getPlanById, upsertMemberWithPlanSnapshot, getSetting as getSettingNamed, saveSetting as saveSettingNamed } from "./storage";
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

// Simplified signal function
function signalChanged(what='') { 
  try { 
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail: what })); 
  } catch {} 
}

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

/* === Preview Helper (added) === */
function computeNextDuePreview(currentNextDueISO, monthsCovered) {
  return advanceNextDueByCycles(currentNextDueISO, monthsCovered);
}
/* === End Preview Helper === */

// --- WhatsApp/Email/Share helpers ---
function openWhatsApp(text, phone){
  const msg = encodeURIComponent(text);
  const pn  = phone ? encodeURIComponent(String(phone)) : "";
  const url = pn ? `https://wa.me/${pn}?text=${msg}` : `https://wa.me/?text=${msg}`;
  window.open(url, "_blank");
}
function openEmail(subject, body, to){
  const s = encodeURIComponent(subject||"");
  const b = encodeURIComponent(body||"");
  const t = to ? encodeURIComponent(to) : "";
  window.location.href = `mailto:${t}?subject=${s}&body=${b}`;
}
function shareFallback(text){
  if (navigator.share) { try { navigator.share({ text }); } catch {} }
  else { alert(text); }
}
function buildReminder(m){
  const due = m.nextDue || "your due date";
  const amt = m.fee != null ? `$${Number(m.fee).toFixed(2)}` : "your fee";
  return `Hi ${m.name||''}, this is a reminder from Alphalete Club. ${amt} is due on ${due}. Reply if you have any questions.`;
}

// --- Payments (PaymentTracking) ---
const PaymentComponent = () => {
  const [members, setMembers] = useState([]);
  const [payments, setPayments] = useState([]);
  const [form, setForm] = useState({ 
    memberId: "", 
    amount: "", 
    paidOn: new Date().toISOString().slice(0,10) 
  });

  async function load() {
    const m1 = await (gymStorage.getAllMembers?.() ?? []);
    const m2 = await (getAllStore?.('members') ?? []);
    const byId = new Map(); 
    [...m1, ...m2].forEach(x => { 
      if (!x) return; 
      const id = String(x.id || x.memberId || x.email || x.phone || Date.now()); 
      byId.set(id, { ...x, id }); 
    });
    setMembers(Array.from(byId.values()).sort((a,b) => (a.name||"").localeCompare(b.name||"")));

    const p1 = await (gymStorage.getAllPayments?.() ?? []);
    const p2 = await (getAllStore?.('payments') ?? []);
    setPayments([...(p1||[]), ...(p2||[])]
      .sort((a,b) => (new Date(b.paidOn||0) - new Date(a.paidOn||0))));
  }
  
  useEffect(() => { load(); }, []);
  
  useEffect(() => { 
    const onChanged = () => load(); 
    window.addEventListener('DATA_CHANGED', onChanged); 
    return () => window.removeEventListener('DATA_CHANGED', onChanged); 
  }, []);

  // Auto-open for Dashboard "Record" jump
  useEffect(() => {
    const pendingId = localStorage.getItem("pendingPaymentMemberId");
    if (pendingId && members.length) {
      setForm(f => ({ ...f, memberId: String(pendingId) }));
      localStorage.removeItem("pendingPaymentMemberId");
    }
  }, [members]);

  // When member changes, default amount from their plan snapshot
  useEffect(() => {
    if (!form.memberId) return;
    const m = members.find(x => String(x.id) === String(form.memberId));
    if (!m) return;
    const defaultAmt = Number(m.fee || 0);
    setForm(f => ({ ...f, amount: f.amount || (defaultAmt ? String(defaultAmt) : "") }));
  }, [form.memberId, members]);

  async function savePayment() {
    if (!form.memberId || !form.amount) {
      alert('Please select a member and enter an amount.');
      return;
    }
    
    const id = crypto.randomUUID?.() || String(Date.now());
    const amount = Number(form.amount || 0);
    const rec = { 
      id, 
      memberId: String(form.memberId || ""), 
      amount, 
      paidOn: form.paidOn || new Date().toISOString().slice(0,10) 
    };
    
    await gymStorage.saveData('payments', rec);
    signalChanged('payments');
    setForm({ 
      memberId: "", 
      amount: "", 
      paidOn: new Date().toISOString().slice(0,10) 
    });
    load();
    alert('Payment recorded successfully!');
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Payments</h1>
      
      {/* Record Payment Form */}
      <div className="border rounded-2xl p-4 space-y-3 bg-white">
        <div className="font-medium">Record Payment</div>
        <select 
          className="border rounded px-3 py-2 w-full" 
          value={form.memberId} 
          onChange={e => setForm(f => ({ ...f, memberId: e.target.value }))}
        >
          <option value="">Select member…</option>
          {members.filter(m => m.status !== 'Inactive').map(m => (
            <option key={m.id} value={m.id}>
              {m.name || m.email || m.phone}
            </option>
          ))}
        </select>
        <input 
          className="border rounded px-3 py-2 w-full" 
          type="number" 
          min="0" 
          step="0.01"
          placeholder="Amount ($)" 
          value={form.amount} 
          onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
        />
        <input 
          className="border rounded px-3 py-2 w-full" 
          type="date" 
          value={form.paidOn} 
          onChange={e => setForm(f => ({ ...f, paidOn: e.target.value }))}
        />
        <div className="flex justify-end">
          <button 
            type="button" 
            className="border rounded px-3 py-2 bg-green-500 text-white hover:bg-green-600" 
            onClick={savePayment}
          >
            Save Payment
          </button>
        </div>
      </div>

      {/* Recent Payments */}
      <div className="border rounded-2xl p-4 bg-white">
        <div className="font-medium mb-2">Recent Payments</div>
        {payments.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">💰</div>
            <div>No payments yet.</div>
            <div className="text-sm">Record your first payment above.</div>
          </div>
        ) : (
          <div className="space-y-2">
            {payments.slice(0, 20).map(p => {
              const m = members.find(x => String(x.id) === String(p.memberId));
              return (
                <div key={p.id} className="flex justify-between border rounded-xl px-3 py-2">
                  <div>
                    <div className="font-medium">
                      {m?.name || m?.email || m?.phone || 'Unknown Member'}
                    </div>
                    <div className="text-xs text-gray-500">Payment on {p.paidOn}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-green-600">
                      ${Number(p.amount || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
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

// --- Dashboard component continues here ---

// --- Members (ClientManagement) ---
const ClientManagement = () => {
  const [members, setMembers] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name:"", email:"", phone:"", planId:"" });

  async function load() {
    setLoading(true);
    try {
      const m1 = await (gymStorage.getAllMembers?.() ?? []);
      const m2 = await (getAllStore?.('members') ?? []);
      const byId = new Map();
      [...m1, ...m2].forEach(x => { 
        if (!x) return; 
        const id = String(x.id || x.memberId || x.email || x.phone || Date.now()); 
        byId.set(id, { ...x, id }); 
      });
      setMembers(Array.from(byId.values()).sort((a,b)=> (a.name||"").localeCompare(b.name||"")));
    } finally { 
      setLoading(false); 
    }
  }

  async function loadMembersAndPlans(){
    await load(); // existing members loader
    const ps = await (getAllStore?.('plans') ?? []);
    setPlans((ps || []).filter(p=>!p._deleted).sort((a,b)=>(a.name||"").localeCompare(b.name||"")));
  }
  
  useEffect(() => { loadMembersAndPlans(); }, []);
  
  useEffect(() => {
    const onOpen = () => { 
      setEditing(null); 
      setForm({ name:"", email:"", phone:"", planId:"" }); 
      setIsOpen(true); 
    };
    window.addEventListener("OPEN_ADD_MEMBER", onOpen);
    const onChanged = () => loadMembersAndPlans();
    window.addEventListener("DATA_CHANGED", onChanged);
    return () => { 
      window.removeEventListener("OPEN_ADD_MEMBER", onOpen); 
      window.removeEventListener("DATA_CHANGED", onChanged); 
    };
  }, []);

  async function save() {
    const id = editing?.id || (crypto.randomUUID?.() || String(Date.now()));
    const plan = form.planId ? plans.find(p=>String(p.id)===String(form.planId)) : null;
    const base = {
      id,
      name: form.name, email: form.email, phone: form.phone,
      status: editing?.status || "Active",
      joinDate: editing?.joinDate || new Date().toISOString().slice(0,10),
      // if creating new & plan exists, set an initial nextDue = today + cycle (optional)
      nextDue: editing?.nextDue || (plan ? new Date(Date.now() + (Number(plan.cycleDays||30))*86400000).toISOString().slice(0,10) : editing?.nextDue),
      lastPayment: editing?.lastPayment || null,
    };
    await upsertMemberWithPlanSnapshot({ ...base, planId: form.planId || "" }, plan || undefined);
    setIsOpen(false); 
    setEditing(null); 
    signalChanged('members'); 
    loadMembersAndPlans();
  }
  
  async function del(m) {
    // soft delete: set status Inactive for simplicity
    await gymStorage.saveMembers({ ...m, status: "Inactive" });
    signalChanged('members'); 
    load();
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Members</h1>
        <button 
          type="button" 
          className="border rounded px-3 py-2 bg-blue-500 text-white hover:bg-blue-600" 
          onClick={() => { 
            setEditing(null); 
            setForm({ name:"", email:"", phone:"", planId:"" }); 
            setIsOpen(true); 
          }}
        >
          + Add Member
        </button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Loading…</div>
      ) : members.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <div className="text-4xl mb-2">👥</div>
          <div>No members yet.</div>
          <div className="text-sm">Click "Add Member" to get started.</div>
        </div>
      ) : (
        <div className="space-y-2">
          {members.filter(m => m.status !== 'Inactive').map(m => (
            <div key={m.id} className="flex items-center justify-between border rounded-xl px-3 py-2 bg-white">
              <div>
                <div className="font-medium">{m.name || "(no name)"}</div>
                <div className="text-xs text-gray-500">
                  {m.email || "—"} • {m.phone || "—"} • {m.status || "Active"}
                  {m.joinDate && ` • Joined ${m.joinDate}`}
                </div>
                <div className="text-xs text-gray-500">
                  {(m.planName ? `${m.planName} • $${Number(m.fee||0).toFixed(2)} / ${m.cycleDays||30}d` : "No plan")}
                </div>
                {m.nextDue && <div className="text-xs">{`Next due: ${m.nextDue}`}</div>}
              </div>
              <div className="flex gap-2">
                <button 
                  type="button" 
                  className="text-xs border rounded px-2 py-1 hover:bg-gray-50" 
                  onClick={() => { 
                    setEditing(m); 
                    setForm({ name:m.name||"", email:m.email||"", phone:m.phone||"", planId: m.planId || "" }); 
                    setIsOpen(true); 
                  }}
                >
                  Edit
                </button>
                <button 
                  type="button" 
                  className="text-xs border rounded px-2 py-1 text-red-600 hover:bg-red-50" 
                  onClick={() => del(m)}
                >
                  Deactivate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isOpen && (
        <div className="fixed inset-0 bg-black/20 z-[999] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-4 w-full max-w-md space-y-3">
            <div className="text-lg font-semibold">{editing ? "Edit Member" : "Add Member"}</div>
            <input 
              className="border rounded px-3 py-2 w-full" 
              placeholder="Full Name" 
              value={form.name} 
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
            <input 
              className="border rounded px-3 py-2 w-full" 
              type="email"
              placeholder="Email Address" 
              value={form.email} 
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
            />
            <input 
              className="border rounded px-3 py-2 w-full" 
              type="tel"
              placeholder="Phone Number" 
              value={form.phone} 
              onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
            />
            <select className="border rounded px-3 py-2 w-full" value={form.planId} onChange={e=>setForm(f=>({ ...f, planId:e.target.value }))}>
              <option value="">No plan</option>
              {plans.map(p => <option key={p.id} value={p.id}>{p.name} — ${Number(p.price||0).toFixed(2)} / {p.cycleDays||30}d</option>)}
            </select>
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
                className="border rounded px-3 py-2 bg-blue-500 text-white hover:bg-blue-600" 
                onClick={save}
              >
                {editing ? "Save Changes" : "Add Member"}
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
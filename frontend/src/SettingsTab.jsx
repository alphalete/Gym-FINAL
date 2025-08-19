import React, { useEffect, useState } from "react";
import { loadSettings, setSetting, getSetting } from "./settingsStore";
import { hasPin, setNewPin } from "./pinlock";
import { syncNow } from "./lib/sync";

function Row({ label, hint, control }){ return (
  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 items-center py-3">
    <div className="sm:col-span-1"><div className="text-sm font-medium text-gray-900">{label}</div>{hint && <div className="text-xs text-gray-500">{hint}</div>}</div>
    <div className="sm:col-span-2">{control}</div>
  </div>
);}
function Section({ title, children, defaultOpen=true }){ const [open,setOpen]=useState(defaultOpen); return (
  <div className="bg-white rounded-2xl border shadow-soft overflow-hidden">
    <button onClick={()=>setOpen(!open)} className="w-full flex items-center justify-between px-4 py-3">
      <div className="text-sm font-semibold text-gray-900">{title}</div><span className="text-gray-400">{open?"▾":"▸"}</span>
    </button>{open && <div className="px-4 pb-4">{children}</div>}
  </div>
);}

export default function SettingsTab(){
  const [s,setS]=useState(null); 
  const [pinSet,setPinSet]=useState(false);
  const [syncing, setSyncing] = useState(false);
  const [lastSync, setLastSync] = useState(null);
  
  useEffect(()=>{ 
    (async () => {
      const s = await loadSettings().catch(()=>({}));
      setS(prev => ({ ...prev, ...s }));
      
      // Get last sync time
      const lastSyncTime = await getSetting('lastSyncAt');
      setLastSync(lastSyncTime);
    })();
    (async()=>setPinSet(await hasPin()))(); 
  },[]);
  
  if(!s) return <div className="p-6 text-gray-500">Loading settings…</div>;
  
  const update=(k)=>(async v=>{ const val=(k.endsWith("Days")||k.endsWith("Minutes")||k==="billingCycleDays")?Math.max(0,Number(v||0)):v;
    await setSetting(k,val); setS(p=>({...p,[k]:val})); });

  const handleSyncNow = async () => {
    setSyncing(true);
    try {
      await syncNow();
      const newLastSync = await getSetting('lastSyncAt');
      setLastSync(newLastSync);
      alert('✅ Sync completed successfully!');
    } catch (error) {
      console.error('Sync failed:', error);
      alert('❌ Sync failed: ' + error.message);
    } finally {
      setSyncing(false);
    }
  };

  // Helper to mask API keys
  const maskApiKey = (key) => {
    if (!key || key.includes('<PASTE YOUR')) return key;
    return key.slice(0, 8) + '•••••••••••';
  };

  return (<div className="p-6 max-w-3xl mx-auto space-y-4">
    <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>

    <Section title="Billing">
      <Row label="Membership Fee (Default)" control={<input type="number" className="w-40 rounded-xl border px-3 py-2" value={s.membershipFeeDefault} onChange={e=>update("membershipFeeDefault")(e.target.value)} />} />
      <Row label="Billing Cycle Length (days)" control={<input type="number" className="w-40 rounded-xl border px-3 py-2" value={s.billingCycleDays} onChange={e=>update("billingCycleDays")(e.target.value)} />} />
      <Row label="Due Soon Window (days)" control={<input type="number" className="w-40 rounded-xl border px-3 py-2" value={s.dueSoonDays} onChange={e=>update("dueSoonDays")(e.target.value)} />} />
      <Row label="Grace Period (days)" control={<input type="number" className="w-40 rounded-xl border px-3 py-2" value={s.graceDays} onChange={e=>update("graceDays")(e.target.value)} />} />
      <Row label="Cycle Anchor Mode" hint="How billing cycles are calculated" control={<select className="rounded-xl border px-3 py-2" value={s.cycleAnchorMode || "anchored"} onChange={e=>update("cycleAnchorMode")(e.target.value)}>
        <option value="anchored">Anchored (recommended)</option>
        <option value="fromPayment">From payment date</option>
      </select>} />
    </Section>

    <Section title="Reminders">
      <Row label="Default Channel" control={<select className="rounded-xl border px-3 py-2" value={s.reminderChannel} onChange={e=>update("reminderChannel")(e.target.value)}>
        <option value="whatsapp">WhatsApp</option><option value="email">Email</option></select>} />
      <Row label="Send Time" hint="24h HH:MM" control={<input className="rounded-xl border px-3 py-2 w-32" value={s.reminderSendTime} onChange={e=>update("reminderSendTime")(e.target.value)} />} />
      <Row label="Reminder Template" hint="Use {NAME}, {DUE_DATE}, {AMOUNT}" control={
        <textarea rows={3} className="w-full rounded-xl border px-3 py-2" value={s.reminderTemplate} onChange={e=>update("reminderTemplate")(e.target.value)} />} />
    </Section>

    <Section title="Display">
      <Row label="Dashboard View" control={<select className="rounded-xl border px-3 py-2" value={s.dashboardView} onChange={e=>update("dashboardView")(e.target.value)}>
        <option value="auto">Auto</option><option value="cards">Cards</option><option value="table">Table</option></select>} />
      <Row label="Sort Order" control={<select className="rounded-xl border px-3 py-2" value={s.sortOrder} onChange={e=>update("sortOrder")(e.target.value)}>
        <option value="status_due_name">Status → Due Date → Name</option><option value="name">Name</option></select>} />
      <Row label="Show Inactive Members" control={<label className="inline-flex items-center gap-2">
        <input type="checkbox" checked={!!s.showInactive} onChange={e=>update("showInactive")(e.target.checked)} />
        <span className="text-sm text-gray-700">Show/hide inactive</span></label>} />
    </Section>

    <Section title="Currency & Locale">
      <Row label="Currency Code" control={<input className="rounded-xl border px-3 py-2 w-32 uppercase" value={s.currencyCode} onChange={e=>update("currencyCode")(e.target.value.toUpperCase())} />} />
      <Row label="Date Format" control={<select className="rounded-xl border px-3 py-2" value={s.dateFormat} onChange={e=>update("dateFormat")(e.target.value)}>
        <option value="auto">Auto</option><option value="DD/MM/YYYY">DD/MM/YYYY</option><option value="MM/DD/YYYY">MM/DD/YYYY</option></select>} />
    </Section>

    <Section title="Data & Access">
      <Row label="Export Format" control={<select className="rounded-xl border px-3 py-2" value={s.exportFormat} onChange={e=>update("exportFormat")(e.target.value)}>
        <option value="CSV">CSV</option><option value="PDF">PDF</option><option value="XLSX">XLSX</option></select>} />
      <Row label="PIN lock for sensitive actions" hint="Record payment & delete member require PIN">
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={!!s.paymentsPinEnabled}
            onChange={async e=>{ const v=e.target.checked; await setSetting("paymentsPinEnabled", v); setS(p=>({...p, paymentsPinEnabled:v})); }} />
          <span className="text-sm text-gray-700">Require PIN before proceeding</span>
        </label>
      </Row>
      <Row label={"Set/Change PIN"} hint="Stored securely (hashed)">
        <div className="flex flex-col sm:flex-row gap-2">
          <input type="password" className="rounded-xl border px-3 py-2" placeholder="Enter PIN" id="__new_pin" />
          <input type="password" className="rounded-xl border px-3 py-2" placeholder="Confirm PIN" id="__confirm_pin" />
          <button type="button" className="btn btn-primary" onClick={async ()=>{
            const a=document.getElementById("__new_pin").value; const b=document.getElementById("__confirm_pin").value;
            if(!a || a!==b){ alert("PINs do not match."); return; } await setNewPin(a); alert("PIN updated.");
          }}>Save PIN</button>
        </div>
      </Row>
    </Section>

    <Section title="Google Sheets Integration">
      <Row 
        label="Sheets API URL" 
        hint="Google Apps Script Web App URL"
        control={
          <div className="text-sm text-gray-700 font-mono bg-gray-50 px-3 py-2 rounded-lg">
            {process.env.REACT_APP_SHEETS_API_URL || 'Not configured'}
          </div>
        } 
      />
      <Row 
        label="API Key" 
        hint="Authentication key for Google Sheets"
        control={
          <div className="text-sm text-gray-700 font-mono bg-gray-50 px-3 py-2 rounded-lg">
            {maskApiKey(process.env.REACT_APP_SHEETS_API_KEY) || 'Not configured'}
          </div>
        } 
      />
      <Row 
        label="Last Sync" 
        hint="When data was last synchronized"
        control={
          <div className="text-sm text-gray-600">
            {lastSync ? new Date(lastSync).toLocaleString() : 'Never'}
          </div>
        } 
      />
      <Row 
        label="Sync Data" 
        hint="Manually sync with Google Sheets"
        control={
          <button 
            onClick={handleSyncNow}
            disabled={syncing || !navigator.onLine}
            className={`px-4 py-2 rounded-lg font-medium ${
              syncing || !navigator.onLine 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-indigo-600 text-white hover:bg-indigo-700'
            } transition-colors`}
          >
            {syncing ? '🔄 Syncing...' : '🔄 Sync Now'}
          </button>
        } 
      />
      {!navigator.onLine && (
        <div className="text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg mt-2">
          ⚠️ Currently offline - sync will happen automatically when back online
        </div>
      )}
    </Section>
  </div>);
}
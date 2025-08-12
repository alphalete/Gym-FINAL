import React from "react";
import gymStorage from "./storage";

function Field({ label, children }){ return (
  <label className="block">
    <span className="text-sm font-medium text-gray-700">{label}</span>
    <div className="mt-1">{children}</div>
  </label>
);}

export default function PlansTab(){
  const [plans, setPlans]   = React.useState([]);
  const [editing, setEdit]  = React.useState(null); // plan or null
  const [filter, setFilter] = React.useState('all');

  async function load(){
    const list = await (gymStorage.getAll?.('plans') ?? []);
    setPlans((list || []).filter(p => !p._deleted).sort((a,b)=> (a.name||"").localeCompare(b.name||"")));
  }
  React.useEffect(()=>{ load(); },[]);
  React.useEffect(()=>{ const onC=()=>load(); window.addEventListener('DATA_CHANGED', onC); return ()=>window.removeEventListener('DATA_CHANGED', onC); },[]);

  function startNew(){ setEdit({ id:"", name:"", price:0, cycleDays:30 }); }
  async function save(){
    if (!editing) return;
    const id = editing.id || (crypto.randomUUID?.() || String(Date.now()));
    const rec = { ...editing, id, price: Number(editing.price||0), cycleDays: Number(editing.cycleDays||30) };
    await gymStorage.saveData('plans', rec);
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail:'plans' }));
    setEdit(null); load();
  }
  async function remove(p){
    await gymStorage.saveData('plans', { ...p, _deleted:true });
    window.dispatchEvent?.(new CustomEvent('DATA_CHANGED', { detail:'plans' }));
    load();
  }

  const visible = plans.filter(p => filter === 'all' ? true : p.cycleDays === Number(filter));

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Plans</h1>
        <button type="button" className="border rounded px-3 py-2" onClick={startNew}>+ New Plan</button>
      </div>

      <div className="flex gap-2 text-xs">
        <button className={`border rounded px-2 py-1 ${filter==='all'?'bg-gray-100':''}`} onClick={()=>setFilter('all')}>All</button>
        {[30,28,7].map(d => (
          <button key={d} className={`border rounded px-2 py-1 ${filter===String(d)?'bg-gray-100':''}`} onClick={()=>setFilter(String(d))}>{d} days</button>
        ))}
      </div>

      {visible.length === 0 ? <div className="text-sm text-gray-500">No plans yet.</div> : (
        <div className="space-y-2">
          {visible.map(p => (
            <div key={p.id} className="flex items-center justify-between border rounded-xl px-3 py-2">
              <div>
                <div className="font-medium">{p.name}</div>
                <div className="text-xs text-gray-500">${Number(p.price||0).toFixed(2)} • {p.cycleDays || 30} days</div>
              </div>
              <div className="flex gap-2">
                <button type="button" className="text-xs border rounded px-2 py-1" onClick={()=>setEdit(p)}>Edit</button>
                <button type="button" className="text-xs border rounded px-2 py-1" onClick={()=>remove(p)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 bg-black/20 z-[999] flex items-center justify-center">
          <div className="bg-white rounded-2xl p-4 w-[90%] max-w-md space-y-3">
            <div className="text-lg font-semibold">{editing.id ? "Edit Plan" : "New Plan"}</div>
            <Field label="Name">
              <input className="border rounded px-3 py-2 w-full" value={editing.name} onChange={e=>setEdit(v=>({ ...v, name:e.target.value }))}/>
            </Field>
            <Field label="Price">
              <input className="border rounded px-3 py-2 w-full" type="number" value={editing.price} onChange={e=>setEdit(v=>({ ...v, price:e.target.value }))}/>
            </Field>
            <Field label="Cycle (days)">
              <input className="border rounded px-3 py-2 w-full" type="number" value={editing.cycleDays} onChange={e=>setEdit(v=>({ ...v, cycleDays:e.target.value }))}/>
            </Field>
            <div className="flex justify-end gap-2">
              <button type="button" className="border rounded px-3 py-2" onClick={()=>setEdit(null)}>Cancel</button>
              <button type="button" className="border rounded px-3 py-2" onClick={save}>{editing.id ? "Save" : "Create"}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
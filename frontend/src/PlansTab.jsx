import React from "react";
import { settingsStore } from "./settingsStore";
import { requirePinIfEnabled } from "./pinlock";
import { makeMoneyFormatter } from "./money";
import LockBadge from "./LockBadge";
import { listPlans, upsertPlan, deletePlan, migratePlansFromSettingsIfNeeded } from './storage';

function Field({ label, children }){ return (
  <label className="block">
    <span className="text-sm font-medium text-gray-700">{label}</span>
    <div className="mt-1">{children}</div>
  </label>
);}

export default function PlansTab(){
  const [plans,setPlans]=React.useState([]);
  const [editing,setEditing]=React.useState(null); // plan object or null
  const [money,setMoney]=React.useState(()=> (n=>`TTD ${Number(n||0)}`));
  const [filter, setFilter] = React.useState('all');
  
  const counts = React.useMemo(() => ({
    all: plans.length,
    active: plans.filter(p => !!p.active).length,
    inactive: plans.filter(p => !p.active).length
  }), [plans]);

  React.useEffect(()=>{ (async()=>{
    await migratePlansFromSettingsIfNeeded();
    setPlans(await listPlans());
    setMoney(await makeMoneyFormatter());
  })(); },[]);

  React.useEffect(() => {
    (async () => {
      if (filter === 'all') setPlans(await listPlans());
      else if (filter === 'active') setPlans(await listPlans({ active: true }));
      else setPlans(await listPlans({ active: false }));
    })();
  }, [filter]);

  const savePlan = async (e)=>{
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const plan = {
      id: editing?.id || crypto.randomUUID(),
      name: fd.get("name").trim(),
      price: Number(fd.get("price") || 0),
      cycleDays: Number(fd.get("cycleDays") || 30),
      description: fd.get("description") || "",
      active: fd.get("active")==="on"
    };
    if(!plan.name){ alert("Plan name is required."); return; }
    await upsertPlan(plan);
    // Refresh based on current filter
    if (filter === 'all') setPlans(await listPlans());
    else if (filter === 'active') setPlans(await listPlans({ active: true }));
    else setPlans(await listPlans({ active: false }));
    setEditing(null);
    e.currentTarget.reset();
  };

  const onDelete = async (id)=>{
    if(!(await requirePinIfEnabled("delete this plan"))) return;
    await deletePlan(id);
    // Refresh based on current filter
    if (filter === 'all') setPlans(await listPlans());
    else if (filter === 'active') setPlans(await listPlans({ active: true }));
    else setPlans(await listPlans({ active: false }));
  };

  // Optimistic Toggle Helper
  async function toggleActiveOptimistic(plan) {
    // Build the updated plan
    const updated = { ...plan, active: !plan.active };

    // Capture a snapshot for rollback
    const snapshot = plans;

    // Optimistically update local state FIRST
    setPlans(prev => {
      // If on "all", just update the item in place
      if (filter === 'all') {
        return prev.map(p => (p.id === plan.id ? updated : p));
      }
      // If on "active" and we turned it OFF → remove from current view
      if (filter === 'active' && plan.active === true) {
        return prev.filter(p => p.id !== plan.id);
      }
      // If on "inactive" and we turned it ON → remove from current view
      if (filter === 'inactive' && plan.active === false) {
        return prev.filter(p => p.id !== plan.id);
      }
      // Otherwise update in place
      return prev.map(p => (p.id === plan.id ? updated : p));
    });

    try {
      // Persist to DB (no refetch)
      await upsertPlan(updated);
    } catch (e) {
      console.error('Failed to update plan active state:', e);
      // Roll back on error
      setPlans(snapshot);
      alert('Could not update plan. Please try again.');
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Membership Plans</h1>

      <form onSubmit={savePlan} className="bg-white rounded-2xl border shadow-soft p-4 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Plan Name"><input name="name" defaultValue={editing?.name||""} className="w-full rounded-xl border px-3 py-2" /></Field>
          <Field label="Price"><input name="price" type="number" step="1" defaultValue={editing?.price??""} className="w-full rounded-xl border px-3 py-2" /></Field>
          <Field label="Cycle (days)"><input name="cycleDays" type="number" defaultValue={editing?.cycleDays??30} className="w-full rounded-xl border px-3 py-2" /></Field>
          <Field label="Active"><input name="active" type="checkbox" defaultChecked={editing?.active !== undefined ? !!editing.active : true} /></Field>
        </div>
        <Field label="Description">
          <textarea name="description" rows={3} defaultValue={editing?.description||""} className="w-full rounded-xl border px-3 py-2" />
        </Field>
        <div className="flex items-center gap-2">
          <button className="btn btn-primary" type="submit">{editing ? "Update Plan" : "Create Plan"}</button>
          {editing && <button type="button" className="btn" onClick={()=>setEditing(null)}>Cancel</button>}
        </div>
      </form>

      <div className="bg-white rounded-2xl border shadow-soft">
        {/* Filter Toolbar */}
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
          {plans.map(p=>(
            <div key={p.id} className="p-4 flex items-start justify-between gap-3">
              <div>
                <div className="font-medium text-gray-900">{p.name}</div>
                <div className="text-sm text-gray-600">{money(p.price)} • {p.cycleDays} days</div>
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
                <button className="btn" onClick={()=>setEditing(p)}>Edit</button>
                <button className="btn" onClick={()=>onDelete(p.id)}>Delete <LockBadge className="ml-0" /></button>
              </div>
            </div>
          ))}
          {plans.length===0 && <div className="p-4 text-sm text-gray-500">No plans yet. Create your first plan above.</div>}
        </div>
      </div>
    </div>
  );
}
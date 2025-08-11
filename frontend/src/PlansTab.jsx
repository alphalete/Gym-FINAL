import React from "react";
import { settingsStore } from "./settingsStore";
import { requirePinIfEnabled } from "./pinlock";
import { makeMoneyFormatter } from "./money";
import LockBadge from "./LockBadge";

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
  React.useEffect(()=>{ (async()=>{
    setPlans(await settingsStore.listPlans());
    setMoney(await makeMoneyFormatter());
  })(); },[]);

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
    await settingsStore.upsertPlan(plan);
    setPlans(await settingsStore.listPlans());
    setEditing(null);
    e.currentTarget.reset();
  };

  const onDelete = async (id)=>{
    if(!(await requirePinIfEnabled("delete this plan"))) return;
    await settingsStore.deletePlan(id);
    setPlans(await settingsStore.listPlans());
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">Membership Plans</h1>

      <form onSubmit={savePlan} className="bg-white rounded-2xl border shadow-soft p-4 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <Field label="Plan Name"><input name="name" defaultValue={editing?.name||""} className="w-full rounded-xl border px-3 py-2" /></Field>
          <Field label="Price"><input name="price" type="number" step="1" defaultValue={editing?.price??""} className="w-full rounded-xl border px-3 py-2" /></Field>
          <Field label="Cycle (days)"><input name="cycleDays" type="number" defaultValue={editing?.cycleDays??30} className="w-full rounded-xl border px-3 py-2" /></Field>
          <Field label="Active"><input name="active" type="checkbox" defaultChecked={!!editing?.active} /></Field>
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
        <div className="px-4 py-3 border-b text-sm font-semibold text-gray-900">All Plans</div>
        <div className="divide-y">
          {plans.map(p=>(
            <div key={p.id} className="p-4 flex items-start justify-between gap-3">
              <div>
                <div className="font-medium text-gray-900">{p.name} {p.active? <span className="badge badge-success ml-2">Active</span> : <span className="badge ml-2">Inactive</span>}</div>
                <div className="text-sm text-gray-600">{money(p.price)} • {p.cycleDays} days</div>
                {p.description && <div className="text-sm text-gray-500 mt-1">{p.description}</div>}
              </div>
              <div className="flex items-center gap-2">
                <button className="btn" onClick={()=>setEditing(p)}>Edit</button>
                <button className="btn" onClick={()=>onDelete(p.id)}>Delete</button>
              </div>
            </div>
          ))}
          {plans.length===0 && <div className="p-4 text-sm text-gray-500">No plans yet. Create your first plan above.</div>}
        </div>
      </div>
    </div>
  );
}
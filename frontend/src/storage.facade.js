import storageDefault, * as storageNamed from "./storage";

const s = storageDefault || storageNamed || {};

async function safe(fn, fb){ try{ const v = await fn?.(); return v ?? fb; }catch(e){ console.error("[storage.facade]", e); return fb; } }

// ---- Members ----
export async function getAllMembers(){
  const fn = s.getAllMembers || storageNamed.getAllMembers;
  if (fn) {
    const out = await safe(fn, []);
    return Array.isArray(out) ? out : [];
  }
  // Fallback to getAll if direct method not available
  if (s.getAll) {
    const out = await safe(() => s.getAll("members"), []);
    return Array.isArray(out) ? out : [];
  }
  // Final fallback to named export
  if (storageNamed.getAll) {
    const out = await safe(() => storageNamed.getAll("members"), []);
    return Array.isArray(out) ? out : [];
  }
  return [];
}
export async function saveMember(m){
  const fn = s.saveMember || storageNamed.saveMember;
  if (fn) return fn(m);
  const all = await getAllMembers();
  const i = all.findIndex(x=>x.id===m.id);
  if (i>-1) all[i]=m; else all.push(m);
  return s.saveMembers ? s.saveMembers(all) : undefined;
}
export async function deleteMember(id){
  const fn = s.deleteMember || storageNamed.deleteMember;
  if (fn) return fn(id);
  const all = await getAllMembers();
  return s.saveMembers ? s.saveMembers(all.filter(x=>x.id!==id)) : undefined;
}

// ---- Payments ----
export async function getAllPayments(){
  const fn = s.getAllPayments || storageNamed.getAllPayments || (s.getAll ? () => s.getAll("payments") : null);
  const out = await safe(fn, []);
  return Array.isArray(out) ? out : [];
}
export async function savePayment(p){
  const fn = s.savePayment || storageNamed.savePayment;
  if (fn) return fn(p);
  const all = await getAllPayments(); all.push(p);
  return s.savePayments ? s.savePayments(all) : undefined;
}

// ---- Plans ----
export async function getPlans(){
  const fn = s.getPlans || storageNamed.getPlans || (s.getAll ? () => s.getAll("plans") : null);
  const out = await safe(fn, []);
  return Array.isArray(out) ? out : [];
}
export async function savePlan(plan){
  const fn = s.savePlan || storageNamed.savePlan;
  if (fn) return fn(plan);
  const all = await getPlans();
  const i = all.findIndex(x=>x.id===plan.id);
  if (i>-1) all[i]=plan; else all.push(plan);
  return s.savePlans ? s.savePlans(all) : undefined;
}

// ---- Settings ----
export async function getSetting(name, fb){ const fn = s.getSetting || storageNamed.getSetting; return fn ? fn(name, fb) : fb; }
export async function saveSetting(name, val){ const fn = s.saveSetting || storageNamed.saveSetting; return fn ? fn(name, val) : undefined; }

// ---- Init / persist (no‑ops if not present)
export async function init(){ try{ return s.init?.(); }catch{} }
export async function persistHint(){ try{ return s.persistHint?.() ?? navigator.storage?.persist?.(); }catch{} }

const facade = { init, persistHint, getAllMembers, saveMember, deleteMember, getAllPayments, savePayment, getPlans, savePlan, getSetting, saveSetting };
export default facade;
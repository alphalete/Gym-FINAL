import { getSetting } from "./settingsStore";
function formatDateISO(iso, fmt="auto"){
  if(!iso) return "soon"; const d=new Date(iso); if(isNaN(d)) return "soon";
  if(fmt==="DD/MM/YYYY") return `${String(d.getDate()).padStart(2,"0")}/${String(d.getMonth()+1).padStart(2,"0")}/${d.getFullYear()}`;
  if(fmt==="MM/DD/YYYY") return `${String(d.getMonth()+1).padStart(2,"0")}/${String(d.getDate()).padStart(2,"0")}/${d.getFullYear()}`;
  return d.toLocaleDateString(undefined,{month:"short",day:"2-digit",year:"numeric"});
}
export async function buildReminder({ name, dueISO, amount, currencyFormatter }){
  const tmpl=await getSetting("reminderTemplate");
  const fmt=await getSetting("dateFormat");
  const due=formatDateISO(dueISO, fmt);
  const amt=currencyFormatter?currencyFormatter(amount):String(amount??"");
  return tmpl.replaceAll("{NAME}", name||"").replaceAll("{DUE_DATE}", due).replaceAll("{AMOUNT}", amt);
}
export function waLink(message){ return `https://wa.me/?text=${encodeURIComponent(message)}`; }
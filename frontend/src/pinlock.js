import { getSetting, setSetting } from "./settingsStore";
async function sha256Hex(str){ const enc=new TextEncoder().encode(str); const h=await crypto.subtle.digest("SHA-256",enc);
  return Array.from(new Uint8Array(h)).map(b=>b.toString(16).padStart(2,"0")).join(""); }
export async function isPinEnabled(){ return !!(await getSetting("paymentsPinEnabled")); }
export function hasPin(){ try { return !!localStorage.getItem('__PIN__'); } catch { return false; } }
export async function setNewPin(pin){ const hash=await sha256Hex(String(pin||"").trim()); await setSetting("pinHash",hash); }
export async function verifyPin(pin){ const saved=await getSetting("pinHash"); if(!saved) return false; const hash=await sha256Hex(String(pin||"").trim()); return saved===hash; }
export function promptPin({title="Enter PIN",subtitle="Confirm your PIN to proceed."}={}){
  return new Promise(resolve=>{
    const wrap=document.createElement("div"); wrap.className="fixed inset-0 z-[1000] flex items-center justify-center";
    wrap.innerHTML=`<div class="absolute inset-0 bg-black/40"></div>
      <div class="relative bg-white rounded-2xl shadow-soft border w-[92%] max-w-sm p-5">
        <div class="text-lg font-semibold text-gray-900">${title}</div>
        <div class="text-sm text-gray-500 mt-1">${subtitle}</div>
        <form class="mt-4 space-y-3">
          <input type="password" inputmode="numeric" placeholder="••••" class="w-full rounded-xl border px-3 py-2" id="__pin_input" />
          <div class="flex items-center justify-end gap-2">
            <button type="button" class="btn" id="__pin_cancel">Cancel</button>
            <button type="submit" class="btn btn-primary" id="__pin_ok">Confirm</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(wrap);
    const input=wrap.querySelector("#__pin_input"); const form=wrap.querySelector("form"); const cancel=wrap.querySelector("#__pin_cancel");
    const cleanup=(v)=>{ wrap.remove(); resolve(v); };
    cancel.addEventListener("click", ()=>cleanup(null));
    form.addEventListener("submit",(e)=>{ e.preventDefault(); cleanup(input.value||""); });
    input.focus();
  });
}
export async function requirePinIfEnabled(actionName="action"){
  if(!await isPinEnabled()) return true;
  if(!await hasPin()){ alert("A PIN is required but not set. Please set a PIN in Settings."); return false; }
  const pin=await promptPin({ title:"Confirm PIN", subtitle:`Enter PIN to ${actionName}.` });
  if(pin==null) return false;
  const ok=await verifyPin(pin); if(!ok){ alert("Incorrect PIN."); return false; }
  return true;
}
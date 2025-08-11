import { SETTINGS_DEFAULTS, SETTINGS_KEYS } from "./settingsKeys";

class SettingsStore {
  constructor(){ this.dbName="AlphaleteGymDB"; this.version=5; this.db=null; }
  async init(){ if(this.db) return this.db; return new Promise((res,rej)=>{ const r=indexedDB.open(this.dbName,this.version);
    r.onupgradeneeded=e=>{ const db=e.target.result; if(!db.objectStoreNames.contains("settings")) db.createObjectStore("settings",{keyPath:"key"}); };
    r.onsuccess=()=>{ this.db=r.result; res(this.db); }; r.onerror=()=>rej(r.error); }); }
  async getAll(){ await this.init(); return new Promise((res,rej)=>{ const tx=this.db.transaction(["settings"],"readonly");
    const st=tx.objectStore("settings"); const out={}; const c=st.openCursor(); c.onsuccess=e=>{ const cur=e.target.result;
      if(cur){ out[cur.value.key]=cur.value.value; cur.continue(); } else res(out); }; c.onerror=()=>rej(c.error); }); }
  async set(key,value){ await this.init(); return new Promise((res,rej)=>{ const tx=this.db.transaction(["settings"],"readwrite");
    tx.objectStore("settings").put({key,value}); tx.oncomplete=()=>res(true); tx.onerror=()=>rej(tx.error); }); }
}
export const settingsStore = new SettingsStore();
export async function loadSettings(){
  const saved = await settingsStore.getAll().catch(()=>({}));
  const merged = { ...SETTINGS_DEFAULTS, ...saved };
  await Promise.all(SETTINGS_KEYS.filter(k=>!(k in saved)).map(k=>settingsStore.set(k, SETTINGS_DEFAULTS[k]))).catch(()=>{});
  return merged;
}
export async function getSetting(key){
  const all = await settingsStore.getAll().catch(()=>({}));
  return (key in all) ? all[key] : SETTINGS_DEFAULTS[key];
}
export async function setSetting(key,value){ await settingsStore.set(key,value); }
/* storage.js */
class GymStorage {
  constructor(){ this.db=null; this.idbOk=null; }

  async init(){
    if (this.idbOk !== null) return this.idbOk;
    if (!('indexedDB' in window)) { this.idbOk=false; return false; }
    return new Promise((resolve) => {
      try{
        const req = indexedDB.open('gym-db', 4);
        req.onupgradeneeded = (e)=>{
          const db = e.target.result;
          if (!db.objectStoreNames.contains('members')) {
            const s = db.createObjectStore('members', { keyPath:'id' });
            s.createIndex('id','id',{unique:true});
          }
          if (!db.objectStoreNames.contains('payments')) {
            const s = db.createObjectStore('payments', { keyPath:'id' });
            s.createIndex('id','id',{unique:true});
            s.createIndex('memberId','memberId',{unique:false});
          }
          if (!db.objectStoreNames.contains('settings')) {
            const s = db.createObjectStore('settings', { keyPath:'name' });
            s.createIndex('name','name',{unique:true});
          }
          if (!db.objectStoreNames.contains('plans')) {
            const s = db.createObjectStore('plans', { keyPath:'id' });
            s.createIndex('id','id',{unique:true});
          }
        };
        req.onsuccess = () => { this.db=req.result; this.idbOk=true; resolve(true); };
        req.onerror   = () => { console.warn('[storage] IDB open failed', req.error); this.idbOk=false; resolve(false); };
      }catch(e){ console.warn('[storage] init err', e); this.idbOk=false; resolve(false); }
    });
  }

  async persistHint(){
    try{
      if (navigator.storage?.persist) {
        const granted = await navigator.storage.persist();
        console.log('[storage] persist granted:', granted);
      }
    }catch(e){}
  }

  // ---------- generic ops ----------
  async saveData(storeName, value){
    const ensureId = (rec)=> ({ id: (rec.id || crypto.randomUUID?.() || String(Date.now())), ...rec });
    const rec = ensureId(value);

    if (await this.init()){
      return new Promise((resolve,reject)=>{
        try{
          const tx = this.db.transaction([storeName],'readwrite');
          tx.objectStore(storeName).put(rec);
          tx.oncomplete = () => { try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:storeName}))}catch{} resolve(rec); };
          tx.onerror    = () => reject(tx.error);
        }catch(e){ reject(e); }
      });
    }
    // fallback
    const key = `__${storeName}__`;
    const list = JSON.parse(localStorage.getItem(key) || '[]');
    const idx = list.findIndex(x => String(x.id)===String(rec.id));
    if (idx>=0) list[idx]=rec; else list.push(rec);
    localStorage.setItem(key, JSON.stringify(list));
    try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:storeName}))}catch{}
    return rec;
  }

  async getAll(storeName){
    if (await this.init()){
      return new Promise((resolve)=>{
        try{
          const out=[]; const tx=this.db.transaction([storeName],'readonly');
          const req=tx.objectStore(storeName).openCursor();
          req.onsuccess=(e)=>{ const c=e.target.result; if(c){ out.push(c.value); c.continue(); } else resolve(out); };
          req.onerror = ()=> resolve([]);
        }catch(_e){ resolve([]); }
      });
    }
    return JSON.parse(localStorage.getItem(`__${storeName}__`) || '[]');
  }

  // ---------- domain helpers ----------
  async getAllMembers(){ return this.getAll('members'); }
  async saveMembers(m){ const list = Array.isArray(m) ? m : [m]; await Promise.all(list.map(x=>this.saveData('members', x))); return true; }

  async savePayment(p){ return this.saveData('payments', p); }
  async getAllPayments(){ return this.getAll('payments'); }

  async getSetting(name, fallback={}){
    if (await this.init()){
      return new Promise((resolve)=>{
        try{
          const tx=this.db.transaction(['settings'],'readonly');
          const req=tx.objectStore('settings').get(name);
          req.onsuccess=()=>{ const r=req.result; resolve(r && 'value' in r ? r.value : (r ?? fallback)); };
          req.onerror = ()=> resolve(fallback);
        }catch(_e){ resolve(fallback); }
      });
    }
    const raw = localStorage.getItem(`__settings__${name}`);
    return raw ? JSON.parse(raw) : fallback;
  }
  async saveSetting(name, value){
    if (await this.init()){
      return new Promise((resolve,reject)=>{
        try{
          const tx=this.db.transaction(['settings'],'readwrite');
          tx.objectStore('settings').put({name,value});
          tx.oncomplete=()=>{ try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:'settings'}))}catch{} resolve(true); };
          tx.onerror=()=>reject(tx.error);
        }catch(e){ reject(e); }
      });
    }
    localStorage.setItem(`__settings__${name}`, JSON.stringify(value));
    try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:'settings'}))}catch{}
    return true;
  }

  async getPlans(){ return this.getAll('plans'); }
  async savePlan(plan){ return this.saveData('plans', plan); }
}
const gymStorage = new GymStorage();
//-------------------------------------------------------------------------
// SAFE INITIALIZATION AND NAMED EXPORTS FOR ROBUST APP LOADING
//-------------------------------------------------------------------------

// Safe init function that always resolves quickly
export async function init(){ 
  try { 
    if (typeof indexedDB !== "undefined") {
      // Use the existing gymStorage init if available
      return gymStorage?.init?.() ?? Promise.resolve();
    }
  } catch(e){ 
    console.warn("IDB init err", e); 
  }
  return Promise.resolve();
}

export async function persistHint(){ 
  try { 
    await navigator.storage?.persist?.(); 
  } catch(_){
    // Ignore errors - not critical
  } 
}

// Ensure default instance has required methods
const gs = (typeof gymStorage !== "undefined" ? gymStorage : {});
if (!gs.init) gs.init = init;
if (!gs.persistHint) gs.persistHint = persistHint;

// Pass-through named exports used by Components.js so imports don't crash
export async function getSetting(name, fb){ 
  return (gs.getSetting ? gs.getSetting(name, fb) : fb); 
}

export async function saveSetting(name, val){ 
  return gs.saveSetting ? gs.saveSetting(name, val) : undefined; 
}

export async function getPlans(){ 
  return gs.getPlans ? gs.getPlans() : []; 
}

export async function savePlan(p){ 
  return gs.savePlan ? gs.savePlan(p) : undefined; 
}

export async function savePayment(p){ 
  return gs.savePayment ? gs.savePayment(p) : undefined; 
}

export async function getAllPayments(){ 
  return gs.getAllPayments ? gs.getAllPayments() : []; 
}

export async function getAllMembers(){
  return gs.getAllMembers ? gs.getAllMembers() : [];
}

export async function saveMembers(data){
  return gs.saveMembers ? gs.saveMembers(data) : undefined;
}

export default gymStorage;
export async function getAll(store){ return gymStorage.getAll(store); }

// ---- Named exports for existing class methods (compat for Components.js) ----
export async function getSetting(name, fallback){ return gymStorage.getSetting(name, fallback); }
export async function saveSetting(name, value){ return gymStorage.saveSetting(name, value); }

export async function getPlans(){ return gymStorage.getPlans(); }
export async function savePlan(plan){ return gymStorage.savePlan(plan); }

export async function savePayment(p){ return gymStorage.savePayment(p); }
export async function getAllPayments(){ return gymStorage.getAllPayments(); }
// ---------------------------------------------------------------------------
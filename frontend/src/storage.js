/* storage.js — robust storage:
   - IndexedDB primary (gym-db v3), automatic localStorage fallback
   - Stores: members(id), payments(id, memberId idx), settings(name), plans(id)
   - Unified helpers: init, saveData, getAll, getAllMembers, getAllPayments,
     saveMembers, getSetting, saveSetting
*/

class GymStorage {
  constructor(){ this.db=null; this.idbOk=null; }

  async init(){
    if (this.idbOk !== null) return this.idbOk;
    if (!('indexedDB' in window)) { this.idbOk=false; return false; }
    return new Promise((resolve) => {
      try {
        const req = indexedDB.open('gym-db', 3);
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
        req.onsuccess = () => { this.db=req.result; this.idbOk=true; console.log('[storage] IDB ok'); resolve(true); };
        req.onerror   = () => { console.warn('[storage] IDB open failed', req.error); this.idbOk=false; resolve(false); };
      } catch (e) { console.warn('[storage] IDB init error', e); this.idbOk=false; resolve(false); }
    });
  }

  // ---------- generic ops ----------
  async saveData(storeName, value){
    const ensureId = (rec)=> ({ id: (rec.id || crypto.randomUUID?.() || String(Date.now())), ...rec });
    const rec = ensureId(value);

    if (await this.init()){
      return new Promise((resolve,reject)=>{
        try {
          const tx = this.db.transaction([storeName],'readwrite');
          tx.objectStore(storeName).put(rec);
          tx.oncomplete = () => { try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:storeName}))}catch{} resolve(true); };
          tx.onerror    = () => reject(tx.error);
        } catch (e) { reject(e); }
      });
    }
    // fallback: localStorage
    const key = `__${storeName}__`;
    const list = JSON.parse(localStorage.getItem(key) || '[]');
    const idx = list.findIndex(x => String(x.id)===String(rec.id));
    if (idx>=0) list[idx]=rec; else list.push(rec);
    localStorage.setItem(key, JSON.stringify(list));
    try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:storeName}))}catch{}
    return true;
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
    // fallback
    return JSON.parse(localStorage.getItem(`__${storeName}__`) || '[]');
  }

  async getAllMembers(){ return this.getAll('members'); }
  async getAllPayments(){ return this.getAll('payments'); }

  async saveMembers(members){
    const list = Array.isArray(members) ? members : [members];
    await Promise.all(list.map(m => this.saveData('members', m)));
  }

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
    // fallback
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
    // fallback
    localStorage.setItem(`__settings__${name}`, JSON.stringify(value));
    try{window.dispatchEvent(new CustomEvent('DATA_CHANGED',{detail:'settings'}))}catch{}
    return true;
  }
}

const gymStorage = new GymStorage();
export default gymStorage;
export async function getAll(storeName){ return gymStorage.getAll(storeName); }
export async function getSetting(name,fallback){ return gymStorage.getSetting(name,fallback); }
export async function saveSetting(name,value){ return gymStorage.saveSetting(name,value); }

////////////////////////////////////////////////////////////////////////////////
// Self-test: try a write/read once per load (no-op if works)
////////////////////////////////////////////////////////////////////////////////
export async function __storageSelfTest(){
  try{
    const id = '__selftest__';
    await gymStorage.saveData('members', { id, name:'Self Test' });
    const all = await gymStorage.getAll('members');
    const ok = !!all.find(x=>x.id===id);
    console.log('[storage] selftest', ok ? 'PASS' : 'FAIL');
    return ok;
  }catch(e){ console.warn('[storage] selftest error', e); return false; }
}
export function isEmail(s=''){ return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(s)); }
export function isPhone(s=''){ return /^\+?[0-9()\-\s]{7,}$/.test(String(s).trim()); }
export function normalizePlan(p){
  return {
    id: p?.id || (crypto?.randomUUID?.() || String(Date.now())),
    name: String(p?.name||'').trim(),
    price: Number(p?.price||0),
    cycleDays: Number(p?.cycleDays||30),
    description: String(p?.description||''),
    active: !!p?.active
  };
}
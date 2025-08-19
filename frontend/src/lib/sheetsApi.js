const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

async function apiList(entity, params = {}) {
  console.log(`📡 [SheetsApi] Making list request for ${entity}:`, params);
  
  // Filter out undefined/null values and properly serialize objects
  const cleanParams = {};
  Object.keys(params).forEach(key => {
    if (params[key] !== undefined && params[key] !== null) {
      // Convert Date objects and other objects to strings
      if (params[key] instanceof Date) {
        cleanParams[key] = params[key].toISOString();
      } else if (typeof params[key] === 'object') {
        cleanParams[key] = JSON.stringify(params[key]);
      } else {
        cleanParams[key] = params[key];
      }
    }
  });
  
  const qs = new URLSearchParams({ entity, key: API_KEY, ...cleanParams }).toString();
  const url = `${API_URL}?${qs}`;
  console.log(`📡 [SheetsApi] GET request URL:`, url);
  
  const r = await fetch(url, { method: 'GET', credentials: 'omit' });
  console.log(`📡 [SheetsApi] Response status: ${r.status}`);
  
  const j = await r.json();
  console.log(`📡 [SheetsApi] Response data:`, j);
  
  if (!j.ok) {
    const errorMessage = j.error || 'Sheets API error';
    console.error(`❌ [SheetsApi] Error:`, errorMessage);
    throw new Error(errorMessage);
  }
  
  return j.data || [];
}

async function apiWrite(entity, op, body = {}) {
  console.log(`📡 [SheetsApi] Making ${op} request for ${entity}:`, body);
  
  const payload = JSON.stringify({ entity, op, key: API_KEY, ...body });
  console.log(`📡 [SheetsApi] POST payload:`, payload);
  
  const r = await fetch(API_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    credentials: 'omit',
    body: payload,
  });
  
  console.log(`📡 [SheetsApi] Response status: ${r.status}`);
  
  const j = await r.json();
  console.log(`📡 [SheetsApi] Response data:`, j);
  
  if (!j.ok) {
    const errorMessage = j.error || 'Sheets API error';
    console.error(`❌ [SheetsApi] Error:`, errorMessage);
    throw new Error(errorMessage);
  }
  
  return j.data;
}

function stamp(o) { 
  return { updatedAt: new Date().toISOString(), ...o }; 
}

export const SheetsApi = {
  listMembers: (q, since) => apiList('members', { q, since }),
  createMember: (m) => apiWrite('members', 'create', stamp(m)),
  updateMember: (m) => apiWrite('members', 'update', stamp(m)),
  deleteMember: (id) => apiWrite('members', 'delete', { id }),
  listPayments: (q, since) => apiList('payments', { q, since }),
  addPayment: (p) => apiWrite('payments', 'create', stamp(p)),
};
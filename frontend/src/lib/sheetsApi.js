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
  
  try {
    console.log(`📡 [SheetsApi] Starting fetch request with 10s timeout...`);
    
    // Use shorter timeout and AbortController for debugging
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.error(`❌ [SheetsApi] TIMEOUT after 10 seconds - aborting request`);
      controller.abort();
    }, 10000);
    
    const r = await fetch(url, { 
      method: 'GET', 
      credentials: 'omit',
      signal: controller.signal 
    });
    
    clearTimeout(timeoutId);
    console.log(`📡 [SheetsApi] Response received - status: ${r.status}`);
    
    if (!r.ok) {
      console.error(`📡 [SheetsApi] HTTP Error: ${r.status} ${r.statusText}`);
      throw new Error(`HTTP ${r.status}: ${r.statusText}`);
    }
    
    console.log(`📡 [SheetsApi] Parsing JSON response...`);
    const j = await r.json();
    console.log(`📡 [SheetsApi] Response data:`, j);
    
    if (!j.ok) {
      const errorMessage = j.error || 'Sheets API error';
      console.error(`❌ [SheetsApi] Error:`, errorMessage);
      throw new Error(errorMessage);
    }
    
    console.log(`📡 [SheetsApi] Returning ${j.data?.length || 0} items`);
    return j.data || [];
    
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`❌ [SheetsApi] Request was aborted due to timeout`);
      throw new Error('Request timeout - Google Apps Script not responding');
    } else {
      console.error(`❌ [SheetsApi] Request failed:`, error);
      console.error(`❌ [SheetsApi] Error name:`, error.name);
      console.error(`❌ [SheetsApi] Error message:`, error.message);
      throw new Error(`Network error: ${error.message}`);
    }
  }
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
const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

async function apiRequest(entity, op, body = {}) {
  console.log(`📡 [SheetsApi] Making ${op} request for ${entity}:`, body);
  
  const requestBody = {
    entity,
    op,
    key: API_KEY,
    ...body
  };

  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
    redirect: 'follow' // Important: Follow redirects
  });
  
  console.log(`📡 [SheetsApi] Response status: ${res.status}`);
  const data = await res.json();
  console.log(`📡 [SheetsApi] Response data:`, data);
  
  if (!data.ok) {
    const errorMessage = data.error || 'Sheets API error';
    console.error(`❌ [SheetsApi] Error:`, errorMessage);
    throw new Error(errorMessage);
  }
  
  return data.data;
}

async function apiList(entity, params = {}) {
  console.log(`📡 [SheetsApi] Making list request for ${entity}:`, params);
  
  // Filter out undefined values to prevent "undefined" strings in query params
  const cleanParams = {};
  Object.keys(params).forEach(key => {
    if (params[key] !== undefined && params[key] !== null) {
      cleanParams[key] = params[key];
    }
  });
  
  const queryParams = new URLSearchParams({
    entity,
    key: API_KEY,
    ...cleanParams
  });
  
  const url = `${API_URL}?${queryParams.toString()}`;
  console.log(`📡 [SheetsApi] GET request URL:`, url);
  
  const res = await fetch(url, { 
    method: 'GET',
    redirect: 'follow' // Important: Follow redirects
  });
  console.log(`📡 [SheetsApi] Response status: ${res.status}`);
  
  const data = await res.json();
  console.log(`📡 [SheetsApi] Response data:`, data);
  
  if (!data.ok) {
    const errorMessage = data.error || 'Sheets API error';
    console.error(`❌ [SheetsApi] Error:`, errorMessage);
    throw new Error(errorMessage);
  }
  
  return data.data || [];
}

export const SheetsApi = {
  // members
  listMembers: (q, since) => apiList('members', { q, since }),
  createMember: (m) => apiRequest('members', 'create', stamp(m)),
  updateMember: (m) => apiRequest('members', 'update', stamp(m)),
  deleteMember: (id) => apiRequest('members', 'delete', { id }),

  // payments
  listPayments: (q, since) => apiList('payments', { q, since }),
  addPayment: (p) => apiRequest('payments', 'create', stamp(p)),
};

function stamp(o) {
  // ensure updatedAt exists client-side before send (server also sets it)
  return { updatedAt: new Date().toISOString(), ...o };
}
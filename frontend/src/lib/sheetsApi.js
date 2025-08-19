const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

async function apiRequest(entity, operation, data = {}) {
  console.log(`📡 [SheetsApi] Making ${operation} request for ${entity}:`, data);
  
  const requestBody = {
    operation,
    entity,
    data
  };

  const res = await fetch(`${API_URL}?api_key=${API_KEY}`, {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody)
  });
  
  console.log(`📡 [SheetsApi] Response status: ${res.status}`);
  const responseData = await res.json();
  console.log(`📡 [SheetsApi] Response data:`, responseData);
  
  if (!responseData.success) {
    const errorMessage = responseData.error?.message || responseData.error || 'Sheets API error';
    console.error(`❌ [SheetsApi] Error:`, errorMessage);
    throw new Error(errorMessage);
  }
  
  return responseData.data;
}

async function apiList(entity, operation, params = {}) {
  console.log(`📡 [SheetsApi] Making ${operation} request for ${entity}:`, params);
  
  const queryParams = new URLSearchParams({
    entity,
    operation,
    api_key: API_KEY,
    ...params
  });
  
  const url = `${API_URL}?${queryParams.toString()}`;
  console.log(`📡 [SheetsApi] GET request URL:`, url);
  
  const res = await fetch(url, { method: 'GET' });
  console.log(`📡 [SheetsApi] Response status: ${res.status}`);
  
  const responseData = await res.json();
  console.log(`📡 [SheetsApi] Response data:`, responseData);
  
  if (!responseData.success) {
    const errorMessage = responseData.error?.message || responseData.error || 'Sheets API error';
    console.error(`❌ [SheetsApi] Error:`, errorMessage);
    throw new Error(errorMessage);
  }
  
  return responseData.data || [];
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
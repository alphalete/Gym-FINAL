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

  try {
    // Add timeout for better UX
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout

    // Use text/plain to avoid CORS preflight (OPTIONS) requests
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 
        "Content-Type": "text/plain;charset=UTF-8"  // Simple content type to avoid preflight
      },
      body: JSON.stringify(requestBody), // Send JSON as plain text
      signal: controller.signal,
      credentials: 'omit' // Don't send credentials for CORS
    });
    
    clearTimeout(timeoutId);
    console.log(`📡 [SheetsApi] Response status: ${res.status}`);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    console.log(`📡 [SheetsApi] Response data:`, data);
    
    if (!data.ok) {
      const errorMessage = data.error || 'Sheets API error';
      console.error(`❌ [SheetsApi] Error:`, errorMessage);
      throw new Error(errorMessage);
    }
    
    return data.data;
    
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`❌ [SheetsApi] Request timed out after 15 seconds`);
      throw new Error('Request timed out - please check your internet connection');
    } else {
      console.error(`❌ [SheetsApi] Network error:`, error);
      throw new Error(`Network error: ${error.message}`);
    }
  }
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
  
  try {
    // Add timeout for better UX
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    // Simple GET request - no custom headers to avoid preflight
    const res = await fetch(url, { 
      method: 'GET',
      signal: controller.signal,
      credentials: 'omit' // Don't send credentials for CORS
    });
    
    clearTimeout(timeoutId);
    console.log(`📡 [SheetsApi] Response status: ${res.status}`);
    
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    
    const data = await res.json();
    console.log(`📡 [SheetsApi] Response data:`, data);
    
    if (!data.ok) {
      const errorMessage = data.error || 'Sheets API error';
      console.error(`❌ [SheetsApi] Error:`, errorMessage);
      throw new Error(errorMessage);
    }
    
    return data.data || [];
    
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`❌ [SheetsApi] Request timed out after 15 seconds`);
      throw new Error('Request timed out - please check your internet connection');
    } else {
      console.error(`❌ [SheetsApi] Network error:`, error);
      throw new Error(`Network error: ${error.message}`);
    }
  }
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
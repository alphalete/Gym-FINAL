// frontend/src/lib/sheetsApi.js
// CRA env vars (must be set in Netlify as REACT_APP_SHEETS_API_URL / REACT_APP_SHEETS_API_KEY)
const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

async function apiList(entity, params = {}) {
  console.log(`📡 [SheetsApi] Making list request for ${entity}:`, params);

  // Filter out undefined/null + serialize objects/dates
  const cleanParams = {};
  Object.keys(params).forEach((k) => {
    const v = params[k];
    if (v === undefined || v === null) return;
    cleanParams[k] =
      v instanceof Date ? v.toISOString()
      : typeof v === 'object' ? JSON.stringify(v)
      : v;
  });

  // Build URL safely
  const url = new URL(API_URL);
  url.searchParams.set('entity', entity);
  url.searchParams.set('key', API_KEY);
  for (const [k, v] of Object.entries(cleanParams)) url.searchParams.set(k, v);

  console.log(`📡 [SheetsApi] GET request URL:`, url.toString());

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      console.error(`❌ [SheetsApi] TIMEOUT after 10 seconds - aborting request`);
      controller.abort();
    }, 10000);

    const r = await fetch(url.toString(), {
      method: 'GET',
      credentials: 'omit',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    console.log(`📡 [SheetsApi] Response received - status: ${r.status}`);

    if (!r.ok) {
      console.error(`📡 [SheetsApi] HTTP Error: ${r.status} ${r.statusText}`);
      throw new Error(`HTTP ${r.status}: ${r.statusText}`);
    }

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
      throw new Error(`Network error: ${error.message}`);
    }
  }
}

async function apiWrite(entity, op, body = {}) {
  console.log(`📡 [SheetsApi] Making ${op} request for ${entity}:`, body);

  // Build URL with key+entity to satisfy any GAS deployment (old/new)
  const url = new URL(API_URL);
  url.searchParams.set('key', API_KEY);
  url.searchParams.set('entity', entity);

  const payload = JSON.stringify({ entity, op, key: API_KEY, ...body });
  console.log(`📡 [SheetsApi] POST URL:`, url.toString());
  console.log(`📡 [SheetsApi] POST payload:`, payload);

  const r = await fetch(url.toString(), {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    credentials: 'omit',
    body: payload,
  });

  console.log(`📡 [SheetsApi] Response status: ${r.status}`);

  const j = await r.json().catch(() => ({}));
  console.log(`📡 [SheetsApi] Response data:`, j);

  if (!r.ok || j.ok === false) {
    const errorMessage = j?.error || r.statusText || 'Sheets API error';
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

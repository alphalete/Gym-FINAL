// frontend/src/api/sheetsApi.js

const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

function withTimeout(promise, ms, label = 'request') {
  const controller = new AbortController();
  const t = setTimeout(() => {
    console.error(`❌ [SheetsApi] TIMEOUT after ${ms}ms on ${label}`);
    controller.abort();
  }, ms);
  return {
    signal: controller.signal,
    done: (p) =>
      p.finally(() => clearTimeout(t))
  };
}

function toCleanParams(params = {}) {
  const out = {};
  Object.keys(params).forEach((k) => {
    const v = params[k];
    if (v === undefined || v === null) return;
    if (v instanceof Date) out[k] = v.toISOString();
    else if (typeof v === 'object') out[k] = JSON.stringify(v);
    else out[k] = v;
  });
  return out;
}

/** -------------------------
 * GET: list endpoints
 * ------------------------*/
async function apiList(entity, params = {}) {
  console.log(`📡 [SheetsApi] Making list request for ${entity}:`, params);
  const clean = toCleanParams(params);
  const qs = new URLSearchParams({ entity, key: API_KEY, ...clean }).toString();
  const url = `${API_URL}?${qs}`;
  console.log('📡 [SheetsApi] GET request URL:', url);

  const t = withTimeout(null, 15000, `GET ${entity}`);
  const res = await fetch(url, { method: 'GET', credentials: 'omit', signal: t.signal }).finally(() => {});
  console.log('📡 [SheetsApi] Response received - status:', res.status);

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    console.error('❌ [SheetsApi] GET error body:', text);
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }

  const json = await res.json();
  console.log('📡 [SheetsApi] Response data:', json);
  if (!json.ok) throw new Error(json.error || 'Sheets API error');

  const n = Array.isArray(json.data) ? json.data.length : 0;
  console.log(`📡 [SheetsApi] Returning ${n} items`);
  return json.data || [];
}

/** -------------------------
 * POST: create/update/delete
 * IMPORTANT: also include entity/op/key in the URL
 * ------------------------*/
async function apiWrite(entity, op, body = {}) {
  console.log(`📡 [SheetsApi] Making ${op} request for ${entity}:`, body);

  // Put params in URL (Apps Script likes this) AND keep JSON body
  const url = `${API_URL}?${new URLSearchParams({
    entity,
    op,
    key: API_KEY,
  }).toString()}`;

  // Minimal headers to avoid CORS preflight
  const payload = JSON.stringify({ entity, op, key: API_KEY, ...body });
  console.log('📡 [SheetsApi] POST url:', url);
  console.log('📡 [SheetsApi] POST payload:', payload);

  // 20s timeout — creating can be slower than listing
  const t = withTimeout(null, 20000, `POST ${entity}/${op}`);
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
    credentials: 'omit',
    body: payload,
    signal: t.signal,
  }).finally(() => {});

  console.log('📡 [SheetsApi] Response status:', res.status);

  // Sometimes errors come back as text/html via redirect. Try text first if JSON fails.
  let json;
  try {
    json = await res.json();
  } catch (e) {
    const text = await res.text().catch(() => '');
    console.error('❌ [SheetsApi] Non-JSON response:', text);
    throw new Error(`Unexpected response (${res.status})`);
  }

  console.log('📡 [SheetsApi] Response data:', json);
  if (!json.ok) throw new Error(json.error || 'Sheets API error');

  return json.data;
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

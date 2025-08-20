// frontend/src/lib/sheetsApi.js
// CRA env vars (set in Netlify): REACT_APP_SHEETS_API_URL / REACT_APP_SHEETS_API_KEY
const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

// --- tiny helpers ------------------------------------------------------------
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fetchWithTimeout(input, init = {}, { timeoutMs = 25000 } = {}) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(input, { ...init, signal: controller.signal, redirect: 'follow', cache: 'no-store' });
    return res;
  } finally {
    clearTimeout(id);
  }
}

// Retry on transient failures (timeouts / network)
async function withRetries(fn, { tries = 3, baseDelay = 600 } = {}) {
  let lastErr;
  for (let i = 0; i < tries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      const name = err?.name || '';
      const msg  = err?.message || '';
      // Only retry on AbortError / network-ish issues
      const transient = name === 'AbortError' || /timeout|network|Failed to fetch|TypeError/i.test(msg);
      if (!transient || i === tries - 1) throw err;
      const delay = baseDelay * Math.pow(2, i); // 600ms, 1200ms, 2400ms
      console.warn(`⏳ transient error (${msg}). retrying in ${delay}ms...`);
      await sleep(delay);
    }
  }
  throw lastErr;
}

// --- GET ---------------------------------------------------------------------
async function apiList(entity, params = {}) {
  console.log(`📡 [SheetsApi] Making list request for ${entity}:`, params);

  // Sanitize params: stringify Date/objects, drop nullish
  const cleanParams = {};
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    cleanParams[k] =
      v instanceof Date ? v.toISOString()
      : typeof v === 'object' ? JSON.stringify(v)
      : v;
  }

  const url = new URL(API_URL);
  url.searchParams.set('entity', entity);
  url.searchParams.set('key', API_KEY);
  for (const [k, v] of Object.entries(cleanParams)) url.searchParams.set(k, v);

  console.log(`📡 [SheetsApi] GET request URL:`, url.toString());

  try {
    const r = await withRetries(
      () => fetchWithTimeout(url.toString(), { method: 'GET', credentials: 'omit', mode: 'cors' }, { timeoutMs: 25000 }),
      { tries: 3, baseDelay: 700 }
    );

    console.log(`📡 [SheetsApi] Response received - status: ${r.status}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${r.statusText}`);

    const j = await r.json();
    console.log(`📡 [SheetsApi] Response data:`, j);

    if (!j.ok) throw new Error(j.error || 'Sheets API error');
    console.log(`📡 [SheetsApi] Returning ${j.data?.length || 0} items`);
    return j.data || [];
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error(`❌ [SheetsApi] Request timed out`);
      throw new Error('Request timeout - Google Apps Script not responding');
    }
    console.error(`❌ [SheetsApi] Request failed:`, error.message || error);
    throw error;
  }
}

// --- POST --------------------------------------------------------------------
async function apiWrite(entity, op, body = {}) {
  console.log(`📡 [SheetsApi] Making ${op} request for ${entity}:`, body);

  // Keep key+entity in URL for maximum GAS compatibility (old/new deployments)
  const url = new URL(API_URL);
  url.searchParams.set('key', API_KEY);
  url.searchParams.set('entity', entity);

  const payload = JSON.stringify({ entity, op, key: API_KEY, ...body });
  console.log(`📡 [SheetsApi] POST URL:`, url.toString());
  console.log(`📡 [SheetsApi] POST payload:`, payload);

  const r = await withRetries(
    () =>
      fetchWithTimeout(
        url.toString(),
        {
          method: 'POST',
          headers: { 'Content-Type': 'text/plain;charset=UTF-8' },
          credentials: 'omit',
          mode: 'cors',
          body: payload,
        },
        { timeoutMs: 25000 }
      ),
    { tries: 3, baseDelay: 700 }
  );

  console.log(`📡 [SheetsApi] Response status: ${r.status}`);
  const j = await r.json().catch(() => ({}));
  console.log(`📡 [SheetsApi] Response data:`, j);

  if (!r.ok || j.ok === false) {
    const errorMessage = j?.error || r.statusText || 'Sheets API error';
    throw new Error(errorMessage);
  }
  return j.data;
}

function stamp(o) {
  return { updatedAt: new Date().toISOString(), ...o };
}

export const SheetsApi = {
  listMembers:  (q, since) => apiList('members',  { q, since }),
  createMember: (m)        => apiWrite('members',  'create', stamp(m)),
  updateMember: (m)        => apiWrite('members',  'update', stamp(m)),
  deleteMember: (id)       => apiWrite('members',  'delete', { id }),
  listPayments: (q, since) => apiList('payments', { q, since }),
  addPayment:   (p)        => apiWrite('payments', 'create', stamp(p)),
};

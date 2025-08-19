const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

async function apiRequest(entity, op, body = {}) {
  const res = await fetch(API_URL, {
    method: 'POST',
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity, op, key: API_KEY, ...body })
  });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || 'Sheets API error');
  return data.data;
}

async function apiList(entity, params = {}) {
  const qs = new URLSearchParams({ entity, key: API_KEY, ...params }).toString();
  const res = await fetch(`${API_URL}?${qs}`, { method: 'GET' });
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || 'Sheets API error');
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
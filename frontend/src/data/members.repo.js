import storageDefault, * as storageNamed from "../storage";

const s = storageDefault || storageNamed || {};

const getAllMembers = async () => {
  try {
    // First try to get members from backend (primary source)
    let members = [];
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      if (backendUrl) {
        const response = await fetch(`${backendUrl}/api/clients`);
        if (response.ok) {
          const backendMembers = await response.json();
          if (Array.isArray(backendMembers) && backendMembers.length > 0) {
            members = backendMembers;
            console.log(`✅ Loaded ${members.length} members from backend`);
            return members;
          }
        }
      }
    } catch (backendError) {
      console.warn('⚠️ Backend connection failed, falling back to local storage:', backendError.message);
    }
    
    // If no backend data, try local storage
    const out =
      (await s.getAllMembers?.()) ??
      (await s.getAll?.("members")) ?? [];
    console.log(`📱 Loaded ${out.length} members from local storage`);
    return Array.isArray(out) ? out : [];
  } catch (e) { 
    console.error("[members.repo] getAllMembers", e); 
    return []; 
  }
};

const saveAllMembers = async (arr) => {
  try {
    if (s.saveMembers) return s.saveMembers(arr);
    if (s.saveAll)     return s.saveAll("members", arr);
    // Fallback: if only saveMember exists, write one by one
    if (s.saveMember)  {
      for (const m of arr) { /* eslint-disable no-await-in-loop */ await s.saveMember(m); }
      return;
    }
  } catch (e) { console.error("[members.repo] saveAllMembers", e); }
};

// Normalize ID across different shapes and types
export const pickId = (m) => {
  const raw = m?.id ?? m?._id ?? m?.uuid ?? m?.ID ?? m?.Id;
  return raw == null ? undefined : String(raw);
};
const withId = (m) => {
  const id = pickId(m) ?? (globalThis.crypto?.randomUUID?.() ?? String(Date.now()));
  // Preserve original fields but ensure we always have a comparable id string
  return { id, ...m };
};

export async function listMembers() {
  const arr = (await getAllMembers()).map(withId);
  // Deduplicate by normalized id in case legacy data has duplicates
  const seen = new Set();
  const out = [];
  for (const m of arr) {
    const key = pickId(m);
    if (!seen.has(key)) { seen.add(key); out.push(m); }
  }
  return out;
}

export async function upsertMember(member) {
  const list = await listMembers();
  const norm = withId(member);
  
  // Save to backend first - this must succeed
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  if (backendUrl) {
    const method = norm.id && list.find(x => pickId(x) === pickId(norm)) ? 'PUT' : 'POST';
    const url = method === 'PUT' ? `${backendUrl}/api/clients/${norm.id}` : `${backendUrl}/api/clients`;
    
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(norm)
    });
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => `HTTP ${response.status}`);
      throw new Error(`Backend ${method} failed: ${errorText}`);
    }
    
    console.log(`✅ Member ${method === 'PUT' ? 'updated' : 'created'} in backend:`, norm.id);
  }
  
  // Only update local storage if backend succeeded (or no backend URL)
  const idx = list.findIndex(x => pickId(x) === pickId(norm));
  if (idx >= 0) list[idx] = { ...list[idx], ...norm };
  else list.push(norm);
  
  // Save to local storage as backup
  await saveAllMembers(list);
  return list;
}

export async function removeMember(idLike) {
  const list = await listMembers();
  const target = String(idLike);
  
  // Delete from backend first - this must succeed
  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
  if (backendUrl) {
    const response = await fetch(`${backendUrl}/api/clients/${target}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => `HTTP ${response.status}`);
      throw new Error(`Backend DELETE failed: ${errorText}`);
    }
    
    console.log('✅ Member deleted from backend:', target);
  }
  
  // Only update local storage if backend succeeded (or no backend URL)
  const next = list.filter(x => pickId(x) !== target);
  await saveAllMembers(next);
  
  // Some stores cache; re-read to confirm persistence for /__diag
  const verify = await listMembers();
  return verify;
}

export default { listMembers, upsertMember, removeMember };
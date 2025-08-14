import storageDefault, * as storageNamed from "../storage";

const s = storageDefault || storageNamed || {};

// Sync queue management for offline operations
const getPendingSync = async () => {
  try {
    return (await s.getSetting?.('pendingSync', [])) ?? [];
  } catch (e) {
    console.warn('Failed to get pending sync:', e);
    return [];
  }
};

const addPendingSync = async (operation) => {
  try {
    const pending = await getPendingSync();
    const syncItem = {
      id: crypto?.randomUUID?.() || String(Date.now()),
      timestamp: Date.now(),
      ...operation
    };
    pending.push(syncItem);
    await s.saveSetting?.('pendingSync', pending);
    console.log('📤 Added to sync queue:', syncItem.type, syncItem.data?.id || syncItem.memberId);
  } catch (e) {
    console.warn('Failed to add pending sync:', e);
  }
};

const removePendingSync = async (syncId) => {
  try {
    const pending = await getPendingSync();
    const filtered = pending.filter(item => item.id !== syncId);
    await s.saveSetting?.('pendingSync', filtered);
  } catch (e) {
    console.warn('Failed to remove pending sync:', e);
  }
};

// Client-side validation functions
const validateMember = (member) => {
  const errors = [];
  
  // Required fields
  if (!member.name || !member.name.trim()) {
    errors.push('Name is required');
  }
  
  // Email validation
  if (member.email && member.email.trim()) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(member.email.trim())) {
      errors.push('Please enter a valid email address');
    }
  }
  
  // Monthly fee validation
  if (member.monthly_fee != null && (isNaN(member.monthly_fee) || member.monthly_fee < 0)) {
    errors.push('Monthly fee must be a positive number');
  }
  
  // Phone validation (basic)
  if (member.phone && member.phone.trim()) {
    const phoneRegex = /^\+?[\d\s\-\(\)]{7,}$/;
    if (!phoneRegex.test(member.phone.trim())) {
      errors.push('Please enter a valid phone number');
    }
  }
  
  return errors;
};

// Offline-first data loading: IndexedDB primary, API sync secondary
const getAllMembers = async () => {
  try {
    // OFFLINE-FIRST: Load from local storage first
    let localMembers = [];
    try {
      localMembers = (await s.getAllMembers?.()) ?? (await s.getAll?.("members")) ?? [];
      console.log(`📱 Loaded ${localMembers.length} members from local storage`);
    } catch (localError) {
      console.warn('⚠️ Local storage failed:', localError.message);
    }
    
    // If we have local data, return it immediately for fast UI
    if (Array.isArray(localMembers) && localMembers.length > 0) {
      // Background sync with backend (don't wait for this)
      syncWithBackend(localMembers).catch(console.warn);
      return localMembers;
    }
    
    // Only if no local data, try backend as fallback
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      if (backendUrl) {
        const response = await fetch(`${backendUrl}/api/clients`);
        if (response.ok) {
          const backendMembers = await response.json();
          if (Array.isArray(backendMembers)) {
            console.log(`✅ Loaded ${backendMembers.length} members from backend (fallback)`);
            // Save to local storage for future offline use
            await saveAllMembers(backendMembers);
            return backendMembers;
          }
        }
      }
    } catch (backendError) {
      console.warn('⚠️ Backend connection failed:', backendError.message);
    }
    
    return localMembers; // Return whatever we have locally (even if empty)
  } catch (e) { 
    console.error("[members.repo] getAllMembers", e); 
    return []; 
  }
};

// Background sync function - syncs local changes with backend
const syncWithBackend = async (localMembers) => {
  try {
    const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
    if (!backendUrl || !navigator.onLine) return;
    
    // Get pending sync items
    const pendingSync = await getPendingSync();
    
    // Process each pending sync operation
    for (const operation of pendingSync) {
      try {
        if (operation.type === 'CREATE' || operation.type === 'UPDATE') {
          const method = operation.type === 'CREATE' ? 'POST' : 'PUT';
          const url = method === 'POST' ? 
            `${backendUrl}/api/clients` : 
            `${backendUrl}/api/clients/${operation.data.id}`;
          
          const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(operation.data)
          });
          
          if (response.ok) {
            console.log(`✅ Synced ${operation.type} for member:`, operation.data.id);
            await removePendingSync(operation.id);
          }
        } else if (operation.type === 'DELETE') {
          const response = await fetch(`${backendUrl}/api/clients/${operation.memberId}`, {
            method: 'DELETE'
          });
          
          if (response.ok) {
            console.log(`✅ Synced DELETE for member:`, operation.memberId);
            await removePendingSync(operation.id);
          }
        }
      } catch (syncError) {
        console.warn(`⚠️ Failed to sync operation ${operation.id}:`, syncError.message);
      }
    }
  } catch (e) {
    console.warn('⚠️ Background sync failed:', e.message);
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
  // CLIENT-SIDE VALIDATION FIRST
  const validationErrors = validateMember(member);
  if (validationErrors.length > 0) {
    throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
  }
  
  const list = await listMembers();
  const norm = withId(member);
  const isUpdate = norm.id && list.find(x => pickId(x) === pickId(norm));
  
  console.log(`🔄 ${isUpdate ? 'Updating' : 'Creating'} member:`, norm.name);
  
  // ALWAYS save to local storage first (offline-first)
  const idx = list.findIndex(x => pickId(x) === pickId(norm));
  if (idx >= 0) list[idx] = { ...list[idx], ...norm };
  else list.push(norm);
  
  try {
    await saveAllMembers(list);
    console.log(`✅ Member saved locally:`, norm.id);
  } catch (localError) {
    throw new Error(`Failed to save locally: ${localError.message}`);
  }
  
  // TRY to sync with backend immediately if online
  if (navigator.onLine) {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      if (backendUrl) {
        const method = isUpdate ? 'PUT' : 'POST';
        const url = method === 'PUT' ? `${backendUrl}/api/clients/${norm.id}` : `${backendUrl}/api/clients`;
        
        const response = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(norm)
        });
        
        if (response.ok) {
          console.log(`✅ Member synced to backend:`, norm.id);
          return list; // Success - no need to queue
        } else {
          throw new Error(`Backend ${method} failed: ${response.status}`);
        }
      }
    } catch (backendError) {
      console.warn(`⚠️ Backend sync failed, queuing for later:`, backendError.message);
      // Add to sync queue for later
      await addPendingSync({
        type: isUpdate ? 'UPDATE' : 'CREATE',
        data: norm
      });
    }
  } else {
    console.log(`📴 Offline - queuing member for sync:`, norm.id);
    // Add to sync queue for when we're back online
    await addPendingSync({
      type: isUpdate ? 'UPDATE' : 'CREATE',
      data: norm
    });
  }
  
  return list;
}

export async function removeMember(idLike) {
  const list = await listMembers();
  const target = String(idLike);
  const memberToDelete = list.find(x => pickId(x) === target);
  
  if (!memberToDelete) {
    throw new Error(`Member with ID ${target} not found`);
  }
  
  console.log(`🗑️ Deleting member:`, memberToDelete.name);
  
  // ALWAYS remove from local storage first (offline-first)
  const next = list.filter(x => pickId(x) !== target);
  
  try {
    await saveAllMembers(next);
    console.log(`✅ Member removed locally:`, target);
  } catch (localError) {
    throw new Error(`Failed to delete locally: ${localError.message}`);
  }
  
  // TRY to sync deletion with backend immediately if online
  if (navigator.onLine) {
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      if (backendUrl) {
        const response = await fetch(`${backendUrl}/api/clients/${target}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          console.log(`✅ Member deletion synced to backend:`, target);
          return next; // Success - return immediately
        } else {
          throw new Error(`Backend DELETE failed: ${response.status}`);
        }
      }
    } catch (backendError) {
      console.warn(`⚠️ Backend delete sync failed, queuing for later:`, backendError.message);
      // Add to sync queue for later
      await addPendingSync({
        type: 'DELETE',
        memberId: target,
        memberName: memberToDelete.name
      });
    }
  } else {
    console.log(`📴 Offline - queuing deletion for sync:`, target);
    // Add to sync queue for when we're back online
    await addPendingSync({
      type: 'DELETE',
      memberId: target,
      memberName: memberToDelete.name
    });
  }
  
  // Some stores cache; re-read to confirm persistence for /__diag
  const verify = await listMembers();
  return verify;
}

export default { listMembers, upsertMember, removeMember };
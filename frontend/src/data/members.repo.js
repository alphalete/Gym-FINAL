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

// Client-side validation functions (only for new member creation)
const validateMember = (member, isCreation = true) => {
  const errors = [];
  
  // Only validate for new member creation, not for existing member updates
  if (!isCreation) {
    return errors; // Skip validation for updates/existing members
  }
  
  // Required fields for new members only
  if (!member.name || !member.name.trim()) {
    errors.push('Name is required');
  }
  
  // Email validation (only if provided and for new members)
  if (member.email && member.email.trim()) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(member.email.trim())) {
      errors.push('Please enter a valid email address');
    }
  }
  
  // Monthly fee validation (only if provided and for new members)
  if (member.monthly_fee != null && (isNaN(member.monthly_fee) || member.monthly_fee < 0)) {
    errors.push('Monthly fee must be a positive number');
  }
  
  // Phone validation (only if provided and for new members)
  if (member.phone && member.phone.trim()) {
    const phoneRegex = /^\+?[\d\s\-\(\)]{7,}$/;
    if (!phoneRegex.test(member.phone.trim())) {
      errors.push('Please enter a valid phone number');
    }
  }
  
  return errors;
};

// Utility function to ensure member has proper due date
const ensureMemberDueDate = (member) => {
  if (!member) return member;
  
  // If member already has a due date, keep it
  if (member.nextDue || member.dueDate || member.nextDueDate) {
    return member;
  }
  
  // Calculate due date based on start_date and billing interval
  try {
    const startDate = member.start_date ? new Date(member.start_date) : new Date();
    const billingInterval = member.billing_interval_days || 30;
    const dueDate = new Date(startDate);
    dueDate.setDate(dueDate.getDate() + billingInterval);
    
    console.log(`📅 Auto-calculated due date for ${member.name}:`, dueDate.toISOString().slice(0, 10));
    
    return {
      ...member,
      nextDue: dueDate.toISOString().slice(0, 10),
      dueDate: dueDate.toISOString().slice(0, 10),
      joinedOn: member.joinedOn || member.start_date || startDate.toISOString().slice(0, 10)
    };
  } catch (error) {
    console.warn('Failed to calculate due date for member:', member.name, error);
    return member;
  }
};

// Enhanced data loading: Backend first with local fallback
const getAllMembers = async () => {
  try {
    console.log('🔄 [members.repo] getAllMembers called - loading fresh data');
    
    // TRY BACKEND FIRST for fresh data
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
      if (backendUrl) {
        console.log('🌐 [members.repo] Fetching from backend:', `${backendUrl}/api/clients`);
        const response = await fetch(`${backendUrl}/api/clients`, {
          headers: {
            'Cache-Control': 'no-cache'
          }
        });
        if (response.ok) {
          const backendMembers = await response.json();
          console.log(`✅ [members.repo] Loaded ${backendMembers.length} members from backend`);
          
          if (Array.isArray(backendMembers)) {
            // Ensure all members have proper due dates
            const membersWithDueDates = backendMembers.map(ensureMemberDueDate);
            
            // Save enhanced data to local storage for offline use
            await saveAllMembers(membersWithDueDates);
            console.log(`💾 [members.repo] Saved ${membersWithDueDates.length} members with due dates to local storage`);
            return membersWithDueDates;
          }
        } else {
          console.warn(`⚠️ [members.repo] Backend response not OK: ${response.status}`);
        }
      }
    } catch (backendError) {
      console.warn('⚠️ [members.repo] Backend connection failed:', backendError.message);
    }
    
    // Fallback to local storage if backend fails
    console.log('📱 [members.repo] Falling back to local storage...');
    let localMembers = [];
    try {
      localMembers = (await s.getAllMembers?.()) ?? (await s.getAll?.("members")) ?? [];
      console.log(`📱 [members.repo] Loaded ${localMembers.length} members from local storage`);
      
      // Ensure local members also have proper due dates
      localMembers = localMembers.map(ensureMemberDueDate);
    } catch (localError) {
      console.warn('⚠️ [members.repo] Local storage failed:', localError.message);
    }
    
    return Array.isArray(localMembers) ? localMembers : [];
  } catch (e) { 
    console.error("[members.repo] getAllMembers error:", e); 
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
  const list = await listMembers();
  const norm = withId(member);
  const isUpdate = norm.id && list.find(x => pickId(x) === pickId(norm));
  
  // CLIENT-SIDE VALIDATION ONLY FOR NEW MEMBER CREATION
  const validationErrors = validateMember(member, !isUpdate);
  if (validationErrors.length > 0) {
    throw new Error(`Validation failed: ${validationErrors.join(', ')}`);
  }
  
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

// Manual sync function for when user comes back online
export async function syncPendingChanges() {
  const pendingSync = await getPendingSync();
  
  if (pendingSync.length === 0) {
    console.log('✅ No pending changes to sync');
    return { success: true, synced: 0, failed: 0 };
  }
  
  console.log(`🔄 Syncing ${pendingSync.length} pending changes...`);
  let synced = 0;
  let failed = 0;
  
  for (const operation of pendingSync) {
    try {
      await syncWithBackend([operation]);
      synced++;
    } catch (e) {
      console.warn(`Failed to sync operation ${operation.id}:`, e);
      failed++;
    }
  }
  
  console.log(`✅ Sync completed: ${synced} synced, ${failed} failed`);
  return { success: true, synced, failed };
}

// Get sync status for UI feedback
export async function getSyncStatus() {
  const pendingSync = await getPendingSync();
  return {
    pendingCount: pendingSync.length,
    isOnline: navigator.onLine,
    pendingOperations: pendingSync.map(op => ({
      type: op.type,
      memberName: op.data?.name || op.memberName || 'Unknown',
      timestamp: op.timestamp
    }))
  };
}

export default { listMembers, upsertMember, removeMember, syncPendingChanges, getSyncStatus };
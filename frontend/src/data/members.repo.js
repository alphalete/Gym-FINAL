import storageDefault, * as storageNamed from "../storage";
import { SheetsApi } from "../lib/sheetsApi";
import { computeNextDueDate, countPaymentsInCycle } from "../lib/billing";

const s = storageDefault || storageNamed || {};

// Enhanced data loading: Sheets API first with local fallback
const getAllMembers = async () => {
  try {
    console.log('🔄 [members.repo] getAllMembers called - loading fresh data');
    
    // TRY SHEETS API FIRST for fresh data
    try {
      if (navigator.onLine) {
        console.log('🌐 [members.repo] Fetching from Google Sheets API');
        const sheetsMembers = await SheetsApi.listMembers();
        console.log(`✅ [members.repo] Loaded ${sheetsMembers.length} members from Sheets API`);
        
        if (Array.isArray(sheetsMembers)) {
          // Ensure all members have proper due dates
          const membersWithDueDates = sheetsMembers.map(ensureMemberDueDate);
          
          // Save enhanced data to local storage for offline use
          await saveAllMembers(membersWithDueDates);
          console.log(`💾 [members.repo] Saved ${membersWithDueDates.length} members with due dates to local storage`);
          return membersWithDueDates;
        }
      }
    } catch (sheetsError) {
      console.warn('⚠️ [members.repo] Sheets API connection failed:', sheetsError.message);
    }
    
    // Fallback to local storage if Sheets API fails
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

// CRITICAL FIX: Map backend next_payment_date to frontend nextDue field
const ensureMemberDueDate = (member) => {
  if (!member) return member;
  
  // PRIORITY 1: Use backend next_payment_date field (most reliable)
  if (member.next_payment_date) {
    console.log(`✅ Using backend due date for ${member.name}:`, member.next_payment_date);
    return {
      ...member,
      nextDue: member.next_payment_date,        // Map backend field to frontend field
      dueDate: member.next_payment_date,        // Alternative field name
      nextDueDate: member.next_payment_date,    // Another alternative
      joinedOn: member.joinedOn || member.start_date || new Date().toISOString().slice(0, 10)
    };
  }
  
  // PRIORITY 2: If member already has frontend due date fields, keep them
  if (member.nextDue || member.dueDate || member.nextDueDate) {
    console.log(`✅ Using existing due date for ${member.name}:`, member.nextDue || member.dueDate || member.nextDueDate);
    return member;
  }
  
  // PRIORITY 3: Calculate due date based on start_date (fallback only)
  try {
    const startDate = member.start_date ? new Date(member.start_date) : new Date();
    const billingInterval = member.billing_interval_days || 30;
    const dueDate = new Date(startDate);
    dueDate.setDate(dueDate.getDate() + billingInterval);
    
    console.log(`📅 Fallback calculated due date for ${member.name}:`, dueDate.toISOString().slice(0, 10));
    
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
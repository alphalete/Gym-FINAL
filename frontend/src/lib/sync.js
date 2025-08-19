import { SheetsApi } from './sheetsApi';
import storageDefault from '../storage';

const db = storageDefault;

export async function syncNow() {
  if (!navigator.onLine) {
    console.log('📱 Sync skipped - offline');
    return;
  }

  console.log('🔄 Starting sync with Google Sheets...');

  try {
    await db.init();
    
    const lastSyncAt = (await db.getSetting('lastSyncAt')) || '1970-01-01T00:00:00.000Z';
    console.log('📅 Last sync:', lastSyncAt);

    // PUSH pending members
    const pendingMembers = await db.getAll('members');
    const membersToSync = pendingMembers.filter(m => m.pending === 1);
    
    console.log(`📤 Syncing ${membersToSync.length} pending members...`);
    for (const m of membersToSync) {
      try {
        const opFn = m.id && !m.localId ? SheetsApi.updateMember : SheetsApi.createMember;
        const sent = await opFn(clean(m));
        
        // Update local record with server response
        const updatedMember = { 
          ...m, 
          pending: 0, 
          id: sent.id, 
          updatedAt: sent.updatedAt 
        };
        delete updatedMember.localId;
        
        await db.upsert('members', updatedMember);
        console.log(`✅ Synced member: ${m.name}`);
      } catch (error) {
        console.error(`❌ Failed to sync member ${m.name}:`, error);
      }
    }

    // PUSH pending payments
    const pendingPayments = await db.getAll('payments');
    const paymentsToSync = pendingPayments.filter(p => p.pending === 1);
    
    console.log(`📤 Syncing ${paymentsToSync.length} pending payments...`);
    for (const p of paymentsToSync) {
      try {
        const sent = await SheetsApi.addPayment(clean(p));
        
        // Update local record with server response
        const updatedPayment = { 
          ...p, 
          pending: 0, 
          id: sent.id, 
          updatedAt: sent.updatedAt 
        };
        delete updatedPayment.localId;
        
        await db.upsert('payments', updatedPayment);
        console.log(`✅ Synced payment: ${p.amount} for member ${p.memberId}`);
      } catch (error) {
        console.error(`❌ Failed to sync payment:`, error);
      }
    }

    // PULL updates from server
    const [remoteMembers, remotePayments] = await Promise.all([
      SheetsApi.listMembers(null, lastSyncAt).catch(e => {
        console.warn('Failed to fetch remote members:', e);
        return [];
      }),
      SheetsApi.listPayments(null, lastSyncAt).catch(e => {
        console.warn('Failed to fetch remote payments:', e);
        return [];
      }),
    ]);

    console.log(`📥 Received ${remoteMembers.length} members, ${remotePayments.length} payments from server`);

    // Update local data with remote changes
    for (const rm of remoteMembers) {
      await upsertIfNewer(db, 'members', rm);
    }
    for (const rp of remotePayments) {
      await upsertIfNewer(db, 'payments', rp);
    }

    // Update last sync timestamp
    await db.saveSetting('lastSyncAt', new Date().toISOString());
    
    console.log('✅ Sync completed successfully');
    
    // Trigger data refresh event
    window.dispatchEvent(new CustomEvent('DATA_CHANGED', { detail: 'sync_completed' }));
    
  } catch (error) {
    console.error('❌ Sync failed:', error);
    throw error;
  }
}

// Helper functions
function clean(o) { 
  const x = { ...o }; 
  delete x.localId; 
  delete x.pending; 
  return x; 
}

async function upsertIfNewer(db, storeName, remote) {
  try {
    const local = await db.get(storeName, remote.id);
    if (!local || new Date(remote.updatedAt) > new Date(local.updatedAt || 0)) {
      await db.upsert(storeName, remote);
    }
  } catch (error) {
    console.warn(`Failed to upsert ${storeName} record:`, error);
  }
}

// Auto-sync setup
export function setupAutoSync() {
  // Sync on app start (after a delay to allow for initialization)
  setTimeout(() => {
    syncNow().catch(console.error);
  }, 2000);

  // Sync when coming back online
  window.addEventListener('online', () => {
    console.log('📡 Back online - starting sync...');
    syncNow().catch(console.error);
  });

  // Periodic sync every 5 minutes when online
  setInterval(() => {
    if (navigator.onLine) {
      syncNow().catch(console.error);
    }
  }, 5 * 60 * 1000);
}
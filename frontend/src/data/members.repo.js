import storageDefault, * as storageNamed from "../storage";
import { SheetsApi } from "../lib/sheetsApi";
import { computeNextDueDate, countPaymentsInCycle } from "../lib/billing";

const s = storageDefault || storageNamed || {};

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

// Map Sheets API response to frontend member format
const ensureMemberDueDate = (member) => {
  if (!member) return member;
  
  // Map Google Sheets API fields to frontend format
  const memberName = member.name || (member.firstName && member.lastName ? `${member.firstName} ${member.lastName}` : member.firstName || '');
  
  // Use dueDate from Sheets API or existing due date fields
  const dueDate = member.dueDate || member.next_payment_date || member.nextDue || member.nextDueDate;
  
  if (dueDate) {
    console.log(`✅ Using due date for ${memberName}:`, dueDate);
    const mappedMember = {
      ...member,
      name: memberName,
      nextDue: dueDate,
      dueDate: dueDate,
      nextDueDate: dueDate,
      joinedOn: member.joinDate || member.joinedOn || member.start_date || member.join_date || new Date().toISOString().slice(0, 10)
    };
    console.log(`📋 [members.repo] Mapped member:`, mappedMember);
    return mappedMember;
  }
  
  // Calculate due date based on join date if missing
  try {
    const joinDate = member.joinDate || member.start_date || member.join_date || member.joinedOn || new Date().toISOString().slice(0, 10);
    const calculatedDueDate = computeNextDueDate({ joinDate, currentDueDate: null, paymentsInCycle: 0 });
    
    console.log(`📅 Calculated due date for ${memberName}:`, calculatedDueDate);
    
    const mappedMember = {
      ...member,
      name: memberName,
      nextDue: calculatedDueDate,
      dueDate: calculatedDueDate,
      nextDueDate: calculatedDueDate,
      joinedOn: joinDate
    };
    console.log(`📋 [members.repo] Mapped member with calculated due date:`, mappedMember);
    return mappedMember;
  } catch (error) {
    console.warn('Failed to calculate due date for member:', memberName, error);
    return {
      ...member,
      name: memberName
    };
  }
};

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

// Save all members to local storage
const saveAllMembers = async (members) => {
  try {
    if (s.saveAllMembers) {
      await s.saveAllMembers(members);
    } else if (s.bulkUpsert) {
      await s.bulkUpsert("members", members);
    } else {
      // Fallback: save one by one
      for (const member of members) {
        await s.upsert?.("members", member);
      }
    }
  } catch (error) {
    console.warn('Failed to save members to local storage:', error);
  }
};

// Create a new member (offline-first)
const createMember = async (memberData) => {
  try {
    const errors = validateMember(memberData, true);
    if (errors.length > 0) {
      throw new Error(errors.join(', '));
    }

    // Generate local ID and set up member data
    const localId = crypto?.randomUUID?.() || `member_${Date.now()}`;
    const joinDate = memberData.start_date || memberData.join_date || memberData.joinDate || new Date().toISOString().slice(0, 10);
    const initialDueDate = computeNextDueDate({ joinDate, currentDueDate: null, paymentsInCycle: 0 });
    
    // Map to Google Sheets API format: firstName, lastName, email, phone, joinDate, plan, status, dueDate
    const sheetsApiMember = {
      firstName: memberData.firstName || memberData.name?.split(' ')[0] || memberData.name || '',
      lastName: memberData.lastName || memberData.name?.split(' ').slice(1).join(' ') || '',
      email: memberData.email || '',
      phone: memberData.phone || memberData.phoneNumber || '',
      joinDate: joinDate,
      plan: memberData.plan || memberData.membershipType || memberData.membership_type || 'Basic',
      status: (memberData.status || 'Active').toLowerCase(),
      dueDate: initialDueDate
    };
    
    // Keep local format for storage
    const newMember = {
      ...memberData,
      localId,
      id: null, // Will be set by server
      name: sheetsApiMember.firstName + (sheetsApiMember.lastName ? ' ' + sheetsApiMember.lastName : ''),
      firstName: sheetsApiMember.firstName,
      lastName: sheetsApiMember.lastName,
      email: sheetsApiMember.email,
      phone: sheetsApiMember.phone,
      joinDate: sheetsApiMember.joinDate,
      join_date: joinDate,
      start_date: joinDate,
      plan: sheetsApiMember.plan,
      membershipType: sheetsApiMember.plan,
      membership_type: sheetsApiMember.plan,
      status: memberData.status || 'Active',
      next_payment_date: initialDueDate,
      nextDue: initialDueDate,
      dueDate: initialDueDate,
      pending: 1, // Mark as pending sync
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save to local storage immediately
    await s.upsert?.("members", newMember);
    console.log('✅ [members.repo] Created member locally:', newMember.name);

    // Try to sync to Sheets API if online
    if (navigator.onLine) {
      try {
        console.log('📤 [members.repo] Syncing to Sheets API:', sheetsApiMember);
        const serverMember = await SheetsApi.createMember(sheetsApiMember);
        console.log('📥 [members.repo] Sheets API response:', serverMember);
        
        // Update local record with server data
        const syncedMember = { 
          ...newMember, 
          ...serverMember, 
          id: serverMember.id,
          pending: 0 
        };
        delete syncedMember.localId;
        await s.upsert?.("members", syncedMember);
        console.log('✅ [members.repo] Synced member to Sheets API:', syncedMember.name);
        return syncedMember;
      } catch (syncError) {
        console.warn('⚠️ [members.repo] Failed to sync member to Sheets API:', syncError);
        // Return local member - will be synced later
      }
    }

    return newMember;
  } catch (error) {
    console.error('[members.repo] Error creating member:', error);
    throw error;
  }
};

// Update an existing member (offline-first)
const updateMember = async (updatedMemberData) => {
  try {
    const updatedMember = {
      ...updatedMemberData,
      pending: 1, // Mark as pending sync
      updatedAt: new Date().toISOString()
    };

    // Save to local storage immediately
    await s.upsert?.("members", updatedMember);
    console.log('✅ [members.repo] Updated member locally:', updatedMember.name);

    // Try to sync to Sheets API if online
    if (navigator.onLine) {
      try {
        const serverMember = await SheetsApi.updateMember(updatedMember);
        const syncedMember = { ...updatedMember, ...serverMember, pending: 0 };
        await s.upsert?.("members", syncedMember);
        console.log('✅ [members.repo] Synced member update to Sheets API:', syncedMember.name);
        return syncedMember;
      } catch (syncError) {
        console.warn('⚠️ [members.repo] Failed to sync member update to Sheets API:', syncError);
        // Return local member - will be synced later
      }
    }

    return updatedMember;
  } catch (error) {
    console.error('[members.repo] Error updating member:', error);
    throw error;
  }
};

// Delete a member (offline-first)
const deleteMember = async (memberId) => {
  try {
    // Remove from local storage immediately
    await s.remove?.("members", memberId);
    console.log('✅ [members.repo] Deleted member locally:', memberId);

    // Try to sync deletion to Sheets API if online
    if (navigator.onLine) {
      try {
        await SheetsApi.deleteMember(memberId);
        console.log('✅ [members.repo] Synced member deletion to Sheets API:', memberId);
      } catch (syncError) {
        console.warn('⚠️ [members.repo] Failed to sync member deletion to Sheets API:', syncError);
        // Deletion is already local - will be synced later via sync process
      }
    }

    return true;
  } catch (error) {
    console.error('[members.repo] Error deleting member:', error);
    throw error;
  }
};

// Add payment and update member due date (offline-first)
const addPayment = async (paymentData) => {
  try {
    const localId = crypto?.randomUUID?.() || `payment_${Date.now()}`;
    const newPayment = {
      ...paymentData,
      localId,
      id: null, // Will be set by server
      pending: 1, // Mark as pending sync
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    // Save payment to local storage
    await s.upsert?.("payments", newPayment);
    console.log('✅ [members.repo] Added payment locally:', newPayment.amount);

    // Update member's due date based on billing logic
    if (paymentData.memberId) {
      try {
        const member = await s.get?.("members", paymentData.memberId);
        if (member) {
          // Get all payments for this member to count cycle payments
          const allPayments = (await s.getAll?.("payments")) || [];
          const memberPayments = allPayments.filter(p => p.memberId === paymentData.memberId);
          
          const paymentsInCycle = countPaymentsInCycle(
            memberPayments, 
            member.next_payment_date || member.nextDue, 
            member.join_date || member.start_date
          );
          
          const newDueDate = computeNextDueDate({
            joinDate: member.join_date || member.start_date,
            currentDueDate: member.next_payment_date || member.nextDue,
            paymentsInCycle: paymentsInCycle + 1 // Include the new payment
          });

          const updatedMember = {
            ...member,
            next_payment_date: newDueDate,
            nextDue: newDueDate,
            dueDate: newDueDate,
            pending: 1,
            updatedAt: new Date().toISOString()
          };

          await s.upsert?.("members", updatedMember);
          console.log(`✅ [members.repo] Updated member ${member.name} due date to: ${newDueDate}`);
        }
      } catch (memberUpdateError) {
        console.warn('⚠️ [members.repo] Failed to update member due date:', memberUpdateError);
      }
    }

    // Try to sync to Sheets API if online
    if (navigator.onLine) {
      try {
        const serverPayment = await SheetsApi.addPayment(newPayment);
        const syncedPayment = { ...newPayment, ...serverPayment, pending: 0 };
        delete syncedPayment.localId;
        await s.upsert?.("payments", syncedPayment);
        console.log('✅ [members.repo] Synced payment to Sheets API');
        return syncedPayment;
      } catch (syncError) {
        console.warn('⚠️ [members.repo] Failed to sync payment to Sheets API:', syncError);
        // Return local payment - will be synced later
      }
    }

    return newPayment;
  } catch (error) {
    console.error('[members.repo] Error adding payment:', error);
    throw error;
  }
};

// Get all payments
const getAllPayments = async () => {
  try {
    // Try Sheets API first if online
    if (navigator.onLine) {
      try {
        const sheetsPayments = await SheetsApi.listPayments();
        console.log(`✅ [members.repo] Loaded ${sheetsPayments.length} payments from Sheets API`);
        
        // Save to local storage
        for (const payment of sheetsPayments) {
          await s.upsert?.("payments", { ...payment, pending: 0 });
        }
        
        return sheetsPayments;
      } catch (sheetsError) {
        console.warn('⚠️ [members.repo] Sheets API payments failed:', sheetsError.message);
      }
    }
    
    // Fallback to local storage
    const localPayments = (await s.getAll?.("payments")) ?? [];
    console.log(`📱 [members.repo] Loaded ${localPayments.length} payments from local storage`);
    return localPayments;
  } catch (error) {
    console.error('[members.repo] Error getting payments:', error);
    return [];
  }
};

// Export the repository interface
const membersRepo = {
  listMembers: getAllMembers,
  getAllMembers,
  createMember,
  updateMember: updateMember,
  upsertMember: async (memberData) => {
    // Check if it's an update (has ID) or create (no ID)
    if (memberData.id || memberData._id) {
      console.log('📝 [members.repo] Upserting existing member:', memberData.name);
      return await updateMember(memberData);
    } else {
      console.log('➕ [members.repo] Upserting new member:', memberData.name || 'Unknown');
      return await createMember(memberData);
    }
  },
  deleteMember,
  addPayment,
  getAllPayments,
  // Utility functions
  validateMember,
  ensureMemberDueDate
};

export default membersRepo;
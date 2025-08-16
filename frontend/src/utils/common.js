// Alphalete Athletics Common Utilities - Consolidated from Components.js and other files
// Fixing duplicate function declarations as per requirement Phase D

// Date utilities
export function addDaysISO(iso, days) {
  // Fix timezone issue: parse date safely to avoid UTC conversion issues
  const [year, month, day] = iso.split('-').map(Number);
  const d = new Date(year, month - 1, day); // month is 0-indexed, creates local date
  d.setDate(d.getDate() + Number(days || 0)); 
  return d.toISOString().slice(0, 10);
}

// Option A payment logic - maintain existing cadence by rolling forward in whole cycles
export function computeNextDueOptionA(prevNextDueISO, paidOnISO, cycleDays = 30) {
  const cycle = Number(cycleDays || 30);
  
  // Fix timezone issue: parse dates safely
  const parseDateSafe = (iso) => {
    const [year, month, day] = iso.split('-').map(Number);
    return new Date(year, month - 1, day);
  };
  
  const paid = parseDateSafe(paidOnISO);
  let nextDue = parseDateSafe(prevNextDueISO);
  
  // Roll forward by whole cycles until nextDue > paidOn
  while (nextDue <= paid) {
    nextDue.setDate(nextDue.getDate() + cycle);
  }
  return nextDue.toISOString().slice(0, 10);
}

// ALPHALETE CLUB PAYMENT LOGIC
// Fixed 30-Day Billing Cycle with cycle restart logic

export function calculateAlphaleteNextDue(member, paymentAmount, paymentDate) {
  // Fix timezone issue: parse dates safely
  const parseDateSafe = (dateStr) => {
    if (typeof dateStr === 'string' && dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      const [year, month, day] = dateStr.split('-').map(Number);
      return new Date(year, month - 1, day);
    }
    return new Date(dateStr);
  };
  
  const currentStartDate = parseDateSafe(member.start_date || member.joinDate);
  const paymentDateObj = parseDateSafe(paymentDate);
  const memberMonthlyFee = Number(member.monthly_fee || member.fee || 0);
  
  // Calculate the current due date (30 days from current start date)
  let currentDueDate = new Date(currentStartDate);
  currentDueDate.setDate(currentDueDate.getDate() + 30);
  
  const today = new Date();
  
  // If current due date has passed, we need to start a new cycle
  let newStartDate = new Date(currentStartDate);
  if (currentDueDate < today) {
    // Start date becomes the passed due date
    newStartDate = new Date(currentDueDate);
    currentDueDate.setDate(currentDueDate.getDate() + 30); // New due date is 30 days from new start
  }
  
  // Calculate how many cycles this payment covers
  const cyclesCovered = Math.max(1, Math.floor(paymentAmount / memberMonthlyFee));
  
  // Calculate final due date
  let nextDueDate = new Date(currentDueDate);
  
  // For multiple cycles, advance the due date by additional cycles
  if (cyclesCovered > 1) {
    nextDueDate.setDate(nextDueDate.getDate() + (30 * (cyclesCovered - 1)));
  }
  
  return {
    nextDue: nextDueDate.toISOString().slice(0, 10),
    newStartDate: newStartDate.toISOString().slice(0, 10),
    cyclesCovered,
    cycleRestarted: newStartDate.toISOString().slice(0, 10) !== currentStartDate.toISOString().slice(0, 10)
  };
}

export function updateMemberCycleIfNeeded(member) {
  // Check if member's due date has passed and needs cycle restart
  if (!member.nextDue || !member.start_date) return member;
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const dueDate = new Date(member.nextDue);
  dueDate.setHours(0, 0, 0, 0);
  
  if (dueDate >= today) return member;
  
  // Calculate how many cycles have passed
  const daysPassed = Math.floor((today - dueDate) / (1000 * 60 * 60 * 24));
  const cyclesPassed = Math.ceil(daysPassed / 30);
  
  if (cyclesPassed > 0) {
    // Calculate new start date and due date
    const newStartDate = new Date(dueDate);
    const newDueDate = new Date(newStartDate);
    newDueDate.setDate(newDueDate.getDate() + (30 * cyclesPassed));
    
    return {
      ...member,
      start_date: newStartDate.toISOString().slice(0, 10),
      nextDue: newDueDate.toISOString().slice(0, 10),
      status: 'Overdue',
      cycleRestarted: true
    };
  }
  
  return member;
}

export function calculateAlphaleteOverdue(member) {
  // First check if we need to update the cycle
  const updatedMember = updateMemberCycleIfNeeded(member);
  
  if (!updatedMember.nextDue) return { isOverdue: false, daysPastDue: 0, overdueAmount: 0, updatedMember };
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const dueDate = new Date(updatedMember.nextDue);
  dueDate.setHours(0, 0, 0, 0);
  
  const diffTime = dueDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) {
    const daysPastDue = Math.abs(diffDays);
    const monthlyFee = Number(updatedMember.monthly_fee || updatedMember.fee || 0);
    
    // Calculate cycles overdue (every 30 days = 1 cycle)
    const cyclesOverdue = Math.ceil(daysPastDue / 30);
    const overdueAmount = monthlyFee * cyclesOverdue;
    
    return {
      isOverdue: true,
      daysPastDue,
      overdueAmount,
      cyclesOverdue,
      updatedMember
    };
  }
  
  return { isOverdue: false, daysPastDue: 0, overdueAmount: 0, updatedMember };
}

// Communication utilities
export function openWhatsApp(text, phone) {
  const msg = encodeURIComponent(text || "");
  const pn = phone ? encodeURIComponent(String(phone)) : "";
  const url = `https://wa.me/${pn}?text=${msg}`;
  window.open(url, "_blank");
}

export function openEmail(subject, body, to) {
  const s = encodeURIComponent(subject || "");
  const b = encodeURIComponent(body || "");
  const t = to ? encodeURIComponent(to) : "";
  window.location.href = `mailto:${t}?subject=${s}&body=${b}`;
}

// Reminder message builder
export function buildReminder(member) {
  const due = member.nextDue || "your due date";
  const amt = member.fee != null ? `$${Number(member.fee).toFixed(2)}` : "your fee";
  return `Hi ${member.name || 'there'}! Your gym membership payment of ${amt} is due on ${due}. Please make payment to avoid any interruption. Thank you!`;
}

// Navigation utility
export function navigate(tab) {
  if (typeof window !== 'undefined') {
    window.location.hash = `#tab=${tab}`;
    try {
      window.dispatchEvent(new CustomEvent('NAVIGATE', { detail: tab }));
    } catch (e) {
      console.warn('Could not dispatch navigation event:', e);
    }
  }
}

// Currency formatting utility
export function formatCurrency(amount, currency = 'TTD') {
  const num = Number(amount || 0);
  if (currency === 'TTD') {
    return `TT$${num.toFixed(2)}`;
  }
  return `$${num.toFixed(2)}`;
}

// Date formatting utilities
export function formatDate(dateString, includeYear = true) {
  if (!dateString) return 'Not set';
  try {
    // Fix timezone issue: parse date string manually to avoid UTC conversion
    // For ISO date strings like "2025-08-06", split and create date in local timezone
    let date;
    if (typeof dateString === 'string' && dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      // Parse YYYY-MM-DD format manually to avoid timezone issues
      const [year, month, day] = dateString.split('-').map(Number);
      date = new Date(year, month - 1, day); // month is 0-indexed
    } else {
      // Fallback to regular Date parsing for other formats
      date = new Date(dateString);
    }
    
    const options = { 
      month: 'short', 
      day: 'numeric',
      ...(includeYear && { year: 'numeric' })
    };
    return date.toLocaleDateString('en-US', options);
  } catch (error) {
    console.warn('Date formatting error:', error);
    return dateString;
  }
}

// Payment status calculation using Alphalete Club logic with cycle restart
export function getPaymentStatus(member) {
  if (!member || !member.nextDue) {
    return { status: 'unknown', label: 'No due date', class: 'badge-gray' };
  }
  
  const overdueInfo = calculateAlphaleteOverdue(member);
  
  if (overdueInfo.isOverdue) {
    return {
      status: 'overdue',
      label: `Overdue ${overdueInfo.daysPastDue} days`,
      class: 'badge-danger',
      overdueAmount: overdueInfo.overdueAmount,
      cyclesOverdue: overdueInfo.cyclesOverdue,
      updatedMember: overdueInfo.updatedMember
    };
  }
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const dueDate = new Date(member.nextDue);
  dueDate.setHours(0, 0, 0, 0);
  
  const diffTime = dueDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return { 
      status: 'due-today', 
      label: 'Due Today', 
      class: 'badge-warning',
      updatedMember: overdueInfo.updatedMember
    };
  } else if (diffDays <= 3) {
    return { 
      status: 'due-soon', 
      label: `Due in ${diffDays} days`, 
      class: 'badge-warning',
      updatedMember: overdueInfo.updatedMember
    };
  } else {
    return { 
      status: 'active', 
      label: 'Active', 
      class: 'badge-success',
      updatedMember: overdueInfo.updatedMember
    };
  }
}

// Avatar/initials generator
// Calculate total amount paid by a member
export function calculateTotalPaid(memberId, payments = []) {
  if (!memberId || !payments.length) return 0;
  
  return payments
    .filter(payment => String(payment.memberId) === String(memberId))
    .reduce((total, payment) => total + (Number(payment.amount) || 0), 0);
}

export function getInitials(name) {
  if (!name) return '?';
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .join('')
    .slice(0, 2);
}
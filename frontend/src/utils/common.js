// Alphalete Athletics Common Utilities - Consolidated from Components.js and other files
// Fixing duplicate function declarations as per requirement Phase D

// Date utilities
export function addDaysISO(iso, days) {
  const d = new Date(iso); 
  d.setDate(d.getDate() + Number(days || 0)); 
  return d.toISOString().slice(0, 10);
}

// Option A payment logic - maintain existing cadence by rolling forward in whole cycles
export function computeNextDueOptionA(prevNextDueISO, paidOnISO, cycleDays = 30) {
  const cycle = Number(cycleDays || 30);
  const paid = new Date(paidOnISO);
  let nextDue = new Date(prevNextDueISO);
  
  // Roll forward by whole cycles until nextDue > paidOn
  while (nextDue <= paid) {
    nextDue.setDate(nextDue.getDate() + cycle);
  }
  return nextDue.toISOString().slice(0, 10);
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
    const date = new Date(dateString);
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

// Payment status calculation
export function getPaymentStatus(member) {
  if (!member || !member.nextDue) {
    return { status: 'unknown', label: 'No due date', class: 'badge-gray' };
  }
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const dueDate = new Date(member.nextDue);
  dueDate.setHours(0, 0, 0, 0);
  
  const diffTime = dueDate - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) {
    return { 
      status: 'overdue', 
      label: `Overdue ${Math.abs(diffDays)} days`, 
      class: 'badge-danger' 
    };
  } else if (diffDays === 0) {
    return { 
      status: 'due-today', 
      label: 'Due Today', 
      class: 'badge-warning' 
    };
  } else if (diffDays <= 3) {
    return { 
      status: 'due-soon', 
      label: `Due in ${diffDays} days`, 
      class: 'badge-warning' 
    };
  } else {
    return { 
      status: 'active', 
      label: 'Active', 
      class: 'badge-success' 
    };
  }
}

// Avatar/initials generator
export function getInitials(name) {
  if (!name) return '?';
  return name
    .split(' ')
    .map(word => word.charAt(0).toUpperCase())
    .join('')
    .slice(0, 2);
}
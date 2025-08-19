/**
 * 30-day billing logic for Alphalete Club
 * Preserves the existing billing logic exactly as specified
 */

export function computeNextDueDate({ joinDate, currentDueDate, paymentsInCycle }) {
  // dates as YYYY-MM-DD
  const toDate = (s) => new Date(s + 'T00:00:00');
  const fmt = (d) => d.toISOString().slice(0,10);
  
  if (!currentDueDate) {
    // First due date = joinDate + 30 days
    const d = toDate(joinDate); 
    d.setDate(d.getDate() + 30); 
    return fmt(d);
  }
  
  if (paymentsInCycle <= 1) {
    // First payment within the cycle does NOT change due date
    return currentDueDate;
  }
  
  // If the member makes 2+ payments within the same cycle, extend dueDate by +30 days from the current dueDate
  const d = toDate(currentDueDate); 
  d.setDate(d.getDate() + 30); 
  return fmt(d);
}

/**
 * Count payments in the current billing cycle
 */
export function countPaymentsInCycle(payments, currentDueDate, joinDate) {
  if (!payments || payments.length === 0) return 0;
  
  // Determine cycle start date
  let cycleStart;
  if (currentDueDate) {
    const dueDate = new Date(currentDueDate + 'T00:00:00');
    cycleStart = new Date(dueDate);
    cycleStart.setDate(cycleStart.getDate() - 30);
  } else {
    cycleStart = new Date(joinDate + 'T00:00:00');
  }
  
  // Count payments in this cycle
  return payments.filter(payment => {
    const paymentDate = new Date(payment.date || payment.createdAt);
    return paymentDate >= cycleStart;
  }).length;
}

/**
 * Get the current due date status
 */
export function getDueStatus(dueDate) {
  if (!dueDate) return 'no-due-date';
  
  const today = new Date();
  const due = new Date(dueDate + 'T00:00:00');
  const diffTime = due - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) return 'overdue';
  if (diffDays === 0) return 'due-today';
  if (diffDays <= 3) return 'due-soon';
  return 'current';
}
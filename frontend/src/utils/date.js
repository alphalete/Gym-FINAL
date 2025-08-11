export function toISODate(d = new Date()) {
  return new Date(d).toISOString().split('T')[0];
}

// Strict 30-day increment
export function add30DaysFrom(iso) {
  const d = new Date(iso);
  d.setDate(d.getDate() + 30);
  return toISODate(d);
}

export function daysBetween(aISO, bISO) {
  const a = new Date(aISO);
  const b = new Date(bISO);
  return Math.ceil((a - b) / (1000 * 60 * 60 * 24));
}

export function recomputeStatus(client) {
  const today = toISODate();
  const isOverdue = new Date(client.nextDue) < new Date(today);
  const overdueDays = isOverdue ? Math.max(0, daysBetween(today, client.nextDue)) : 0;
  return { ...client, status: isOverdue ? 'Overdue' : 'Active', overdue: overdueDays };
}

export function advanceNextDueByCycles(currentNextDueISO, cycles = 1) {
  let next = currentNextDueISO;
  const n = Math.max(1, cycles | 0);
  for (let i = 0; i < n; i++) next = add30DaysFrom(next);
  return next;
}
export function parseISO(d) { return new Date(d); }

export function nextDueDateFromJoin(joinISO, ref = new Date(), cycleDays = 30) {
  const join = parseISO(joinISO);
  if (isNaN(join)) return null;
  const msDay = 24 * 60 * 60 * 1000;
  const elapsedDays = Math.floor((ref - join) / msDay);
  const cyclesPassed = Math.max(0, Math.floor(elapsedDays / cycleDays));
  const nextCycleStart = new Date(join.getTime() + (cyclesPassed + 1) * cycleDays * msDay);
  // Due date is the day BEFORE the next cycle starts
  return new Date(nextCycleStart.getTime() - msDay); // e.g. join Jan 4 ⇒ due Feb 3
}

export function isOverdue(joinISO, today = new Date(), cycleDays = 30) {
  const due = nextDueDateFromJoin(joinISO, today, cycleDays);
  return due ? today > due : false;
}

export function currentCycleWindow(joinISO, ref = new Date(), cycleDays = 30) {
  const join = parseISO(joinISO);
  if (isNaN(join)) return { start: null, end: null };
  const msDay = 24 * 60 * 60 * 1000;
  const elapsedDays = Math.floor((ref - join) / msDay);
  const cyclesPassed = Math.max(0, Math.floor(elapsedDays / cycleDays));
  const start = new Date(join.getTime() + cyclesPassed * cycleDays * msDay);
  const end = new Date(start.getTime() + cycleDays * msDay - msDay); // inclusive end
  return { start, end };
}
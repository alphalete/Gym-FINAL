import { addDaysISO } from './utils/common';

/**
 * Compute next due date after a payment.
 * @param {string} joinISO      YYYY-MM-DD
 * @param {string} lastDueISO   YYYY-MM-DD (last scheduled due)
 * @param {string} paidOnISO    YYYY-MM-DD (actual payment date)
 * @param {number} cycleDays    e.g., 30
 * @param {number} graceDays    days after due date still considered "on time"
 * @param {"anchored"|"fromPayment"} mode
 */
export function nextDueAfterPayment({
  joinISO, lastDueISO, paidOnISO, cycleDays, graceDays=0, mode="anchored"
}){
  const msDay = 86400000;
  const paid = new Date(paidOnISO);

  if (mode === "fromPayment") {
    return addDaysISO(paidOnISO, cycleDays);
  }

  // Anchored mode
  let anchor = lastDueISO ? new Date(lastDueISO) : new Date(joinISO);
  if (!lastDueISO && joinISO) {
    anchor = new Date(new Date(joinISO).getTime() + (cycleDays - 1) * msDay);
  }

  const graceLimit = new Date(anchor.getTime() + graceDays * msDay);
  if (paid <= graceLimit) {
    return addDaysISO(anchor.toISOString().slice(0,10), cycleDays);
  }

  let next = new Date(anchor);
  while (next <= paid) {
    next = new Date(next.getTime() + cycleDays * msDay);
  }
  return next.toISOString().slice(0,10);
}

export function parseISO(d){ return new Date(d); }
export function nextDueDateFromJoin(joinISO, ref=new Date(), cycleDays=30){
  const join=parseISO(joinISO); if(isNaN(join)) return null;
  const ms=86400000, elapsed=Math.floor((ref-join)/ms);
  const cyclesPassed=Math.max(0, Math.floor(elapsed/cycleDays));
  const nextStart=new Date(join.getTime()+(cyclesPassed+1)*cycleDays*ms);
  return new Date(nextStart.getTime()-ms); // day before next cycle
}
export function isOverdue(joinISO, today=new Date(), cycleDays=30){
  const due=nextDueDateFromJoin(joinISO,today,cycleDays); return due ? today>due : false;
}
export function currentCycleWindow(joinISO, ref=new Date(), cycleDays=30){
  const join=parseISO(joinISO); if(isNaN(join)) return {start:null,end:null};
  const ms=86400000, elapsed=Math.floor((ref-join)/ms);
  const cycles=Math.max(0, Math.floor(elapsed/cycleDays));
  const start=new Date(join.getTime()+cycles*cycleDays*ms);
  const end=new Date(start.getTime()+cycleDays*ms-ms);
  return {start,end};
}
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
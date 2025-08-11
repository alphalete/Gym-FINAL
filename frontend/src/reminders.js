import { formatMoney } from "./settings.js";

export function buildReminder({ name, dueISO, amount }) {
  const due = dueISO ? new Date(dueISO).toLocaleDateString(undefined, { month: "short", day: "2-digit", year: "numeric" }) : "soon";
  const amt = formatMoney(amount || 0);
  return `Hi ${name}, your Alphalete membership is due on ${due}. Amount: ${amt}. You can reply here with a payment receipt. Thank you!`;
}
export function waLink(message) {
  return `https://wa.me/?text=${encodeURIComponent(message)}`;
}
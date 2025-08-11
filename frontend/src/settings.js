export function getDueSoonDays() {
  const v = localStorage.getItem("dueSoonDays");
  return v ? Number(v) : 5;
}
export function setDueSoonDays(n) {
  localStorage.setItem("dueSoonDays", String(Math.max(1, Number(n) || 5)));
}
export function getCurrency() {
  return localStorage.getItem("currencyCode") || "TTD";
}
export function setCurrency(code) {
  localStorage.setItem("currencyCode", (code || "TTD").toUpperCase());
}

export function formatMoney(amount) {
  const code = getCurrency();
  try {
    return new Intl.NumberFormat('en-TT', { style: 'currency', currency: code, maximumFractionDigits: 0 }).format(amount || 0);
  } catch {
    return `${code} ${Number(amount || 0).toFixed(0)}`;
  }
}
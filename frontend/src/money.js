import { getSetting } from "./settingsStore";
export async function makeMoneyFormatter(){
  const code = await getSetting("currencyCode") || "TTD";
  return (amt)=> new Intl.NumberFormat('en-TT', { style:'currency', currency:code, maximumFractionDigits:0 }).format(amt||0);
}
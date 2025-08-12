export const SETTINGS_DEFAULTS = {
  // Billing
  membershipFeeDefault: 250,
  billingCycleDays: 30,
  dueSoonDays: 5,
  graceDays: 0,
  cycleAnchorMode: "anchored",
  // Reminders
  reminderChannel: "whatsapp",
  reminderSendTime: "08:00",
  reminderTemplate:
    "Hi {NAME}, your Alphalete membership is due on {DUE_DATE}. Amount: {AMOUNT}. Please reply with your receipt. Thank you!",
  // Display
  dashboardView: "auto",        // "auto" | "cards" | "table"
  sortOrder: "status_due_name", // or "name"
  showInactive: false,
  // Currency & Locale
  currencyCode: "TTD",
  dateFormat: "auto",           // "auto" | "DD/MM/YYYY" | "MM/DD/YYYY"
  // Data & Access
  exportFormat: "CSV",
  paymentsPinEnabled: false,    // PIN gate toggle
  pinHash: "",
  autoLogoutMinutes: 0
};
export const SETTINGS_KEYS = Object.keys(SETTINGS_DEFAULTS);
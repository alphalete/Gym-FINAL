const API_URL = process.env.REACT_APP_SHEETS_API_URL;
const API_KEY = process.env.REACT_APP_SHEETS_API_KEY;

// 🔒 Fail fast if misconfigured
(function sanityCheck() {
  if (!API_URL) {
    console.error('[SheetsApi] Missing REACT_APP_SHEETS_API_URL');
    throw new Error('Missing REACT_APP_SHEETS_API_URL');
  }
  if (API_URL.includes('...')) {
    console.error('[SheetsApi] REACT_APP_SHEETS_API_URL looks truncated (contains "..."). Fix env var.');
    throw new Error('Truncated REACT_APP_SHEETS_API_URL');
  }
  if (!API_URL.endsWith('/exec')) {
    console.warn('[SheetsApi] URL does not end with /exec – is this the Web App URL?');
  }
  if (!API_KEY) {
    console.warn('[SheetsApi] Missing REACT_APP_SHEETS_API_KEY – requests will fail auth if your script checks it.');
  }
})();

import React, { useEffect, useState } from "react";
import { getDueSoonDays, setDueSoonDays, getCurrency, setCurrency } from "./settings";

export default function SettingsPanel() {
  const [days, setDays] = useState(getDueSoonDays());
  const [currency, setCurr] = useState(getCurrency());
  const [saved, setSaved] = useState(false);

  useEffect(() => { setSaved(false); }, [days, currency]);

  const save = (e) => {
    e.preventDefault();
    setDueSoonDays(days);
    setCurrency(currency);
    setSaved(true);
    setTimeout(() => setSaved(false), 1200);
  };

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
      <p className="text-sm text-gray-500 mt-1">Billing display and reminder preferences</p>

      <form onSubmit={save} className="mt-6 space-y-5 bg-white rounded-2xl border p-5 shadow-soft">
        <div>
          <label className="block text-sm font-medium text-gray-700">Due-soon window (days)</label>
          <input type="number" min="1" className="mt-1 w-40 rounded-xl border px-3 py-2"
            value={days} onChange={e => setDays(e.target.value)} />
          <p className="text-xs text-gray-500 mt-1">Members due within this many days are highlighted.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Currency code</label>
          <input type="text" className="mt-1 w-40 uppercase rounded-xl border px-3 py-2"
            value={currency} onChange={e => setCurr(e.target.value.toUpperCase())} />
          <p className="text-xs text-gray-500 mt-1">Examples: TTD, USD, GBP.</p>
        </div>

        <div className="flex items-center gap-2">
          <button type="submit" className="btn btn-primary">Save</button>
          {saved && <span className="text-sm text-brand-700">Saved ✓</span>}
        </div>
      </form>
    </div>
  );
}
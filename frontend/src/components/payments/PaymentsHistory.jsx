import React, { useMemo } from 'react';
import { usePayments } from '../../hooks/usePayments';

function toCSV(rows) {
  if (!rows?.length) return '';
  const headers = Object.keys(rows[0]);
  const lines = [headers.join(',')];
  for (const r of rows) {
    lines.push(headers.map(h => JSON.stringify(r[h] ?? '')).join(','));
  }
  return lines.join('\n');
}

export default function PaymentsHistory() {
  const { payments, loading } = usePayments();

  const totals = useMemo(() => {
    const sum = payments.reduce((s, p) => s + Number(p.amount || 0), 0);
    return { count: payments.length, sum };
  }, [payments]);

  const downloadCSV = () => {
    const csv = toCSV(payments);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'payments_history.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <div className="p-4">Loading...</div>;

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Payments History</h1>
        <button onClick={downloadCSV} className="rounded-lg bg-red-600 hover:bg-red-700 text-white px-3 py-2">
          Export CSV
        </button>
      </div>
      <div className="mb-3 text-sm text-gray-700">
        <span className="mr-4">Total records: <strong>{totals.count}</strong></span>
        <span>Total collected: <strong>${totals.sum.toFixed(2)}</strong></span>
      </div>
      <div className="overflow-x-auto bg-white border rounded-xl">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3 text-left">Client ID</th>
              <th className="px-4 py-3 text-left">Amount</th>
              <th className="px-4 py-3 text-left">Months</th>
              <th className="px-4 py-3 text-left">Method</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {payments.map(p => (
              <tr key={p.id}>
                <td className="px-4 py-3">{p.date}</td>
                <td className="px-4 py-3">{p.clientId}</td>
                <td className="px-4 py-3">${Number(p.amount || 0).toFixed(2)}</td>
                <td className="px-4 py-3">{p.monthsCovered}</td>
                <td className="px-4 py-3">{p.method}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
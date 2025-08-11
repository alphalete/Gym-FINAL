import { useEffect, useState } from 'react';
import gymStorage from '../gymStorage';

export function usePayments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);

  async function load() {
    try {
      const data = await gymStorage.getAllPayments?.() || [];
      setPayments(data.sort((a,b) => (a.date < b.date ? 1 : -1)));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);
  return { payments, loading, reload: load };
}
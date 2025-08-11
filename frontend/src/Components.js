import React, { useState, useEffect } from 'react';
import gymStorage from './gymStorage'; // Assuming this is the correct import path

/* === Payment & Status Helpers (30-day cycle) === */
function addDaysFromDate(dateISO, days = 30) {
  const d = new Date(dateISO);
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

function daysBetween(aISO, bISO) {
  const a = new Date(aISO);
  const b = new Date(bISO);
  return Math.ceil((a - b) / (1000 * 60 * 60 * 24));
}

function withRecomputedStatus(client) {
  const todayISO = new Date().toISOString().split('T')[0];
  const isOverdue = new Date(client.nextDue) < new Date(todayISO);
  const overdueDays = isOverdue ? Math.max(0, daysBetween(todayISO, client.nextDue)) : 0;
  return {
    ...client,
    status: isOverdue ? 'Overdue' : 'Active',
    overdue: overdueDays
  };
}
/* === End Helpers === */

// Component with payment logic
const PaymentComponent = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newClient, setNewClient] = useState({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
  const [isAddingClient, setIsAddingClient] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [isRecordingPayment, setIsRecordingPayment] = useState(false);
  const [paymentAmount, setPaymentAmount] = useState('');

  const membershipPricing = {
    'Monthly': 59,
    'Quarterly': 150,
    'Annual': 500
  };

  const loadDashboardData = async () => {
    try {
      const savedClients = await gymStorage.getAllMembers();
      const normalized = savedClients.map(withRecomputedStatus);
      setClients(normalized);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadClientsFromPhone = async () => {
    try {
      setLoading(true);
      const savedClients = await gymStorage.getAllMembers();
      const normalized = savedClients.map(withRecomputedStatus);
      setClients(normalized);
    } catch (error) {
      console.error('Error loading clients from phone:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveClientToPhone = async (client) => {
    try {
      await gymStorage.saveMembers(client);
      await loadClientsFromPhone(); // refreshed with recomputed status
    } catch (error) {
      console.error('Error saving client to phone:', error);
      alert('Error saving client data. Please try again.');
    }
  };

  const handleAddClient = async (e) => {
    e.preventDefault();
    try {
      const todayISO = new Date().toISOString().split('T')[0];
      const client = {
        ...newClient,
        id: Date.now().toString(),
        joinDate: todayISO,
        lastPayment: todayISO, // set to null if you don't want a payment at join
        nextDue: addDaysFromDate(todayISO, 30), // strict 30-day cycle
        status: 'Active',
        overdue: 0,
        amount: membershipPricing[newClient.membershipType] || newClient.amount
      };

      const normalized = withRecomputedStatus(client);
      await gymStorage.saveMembers(normalized);
      await loadClientsFromPhone();

      setNewClient({ name: '', email: '', phone: '', membershipType: 'Monthly', amount: 59 });
      setIsAddingClient(false);
    } catch (error) {
      console.error('Error adding client:', error);
      alert('Error adding client. Please try again.');
    }
  };

  const handleSubmitPayment = async (e) => {
    e.preventDefault();
    if (!selectedClient) return;

    // default to monthly fee if input empty
    const monthlyFee = Number(selectedClient.amount || 0);
    const paid = Number((paymentAmount || '').trim() || monthlyFee);

    // cover at least 1 "month" = 30 days
    const monthsCovered = Math.max(1, Math.floor(paid / (monthlyFee || 1)));

    const todayISO = new Date().toISOString().split('T')[0];

    const updatedClients = await Promise.all(
      clients.map(async (c) => {
        if (c.id !== selectedClient.id) return c;

        // Advance FROM the existing nextDue, not from today
        let nextDueISO = c.nextDue || todayISO;
        for (let i = 0; i < monthsCovered; i++) {
          nextDueISO = addDaysFromDate(nextDueISO, 30);
        }

        const updated = withRecomputedStatus({
          ...c,
          lastPayment: todayISO,
          nextDue: nextDueISO
        });

        // Persist member update
        await gymStorage.saveMembers(updated);

        // Save a payment record (history)
        await gymStorage.savePayment({
          id: Date.now().toString(),
          clientId: c.id,
          date: todayISO,
          amount: paid,
          monthsCovered,
          method: 'cash' // replace if you add a selector
        });

        return updated;
      })
    );

    setClients(updatedClients);
    setIsRecordingPayment(false);
    setSelectedClient(null);
    setPaymentAmount('');
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  return (
    <div>
      {/* Component JSX would go here */}
      <h1>Payment Management Component</h1>
      {/* Add your UI components here */}
    </div>
  );
};

export default PaymentComponent;
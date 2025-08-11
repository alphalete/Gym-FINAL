import React, { useState, useEffect } from 'react';
import gymStorage from './gymStorage'; // Assuming this is the correct import path
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';

/* === Payment Preview Helper (added) === */
function computeNextDuePreview(currentNextDueISO, monthsCovered) {
  return advanceNextDueByCycles(currentNextDueISO, monthsCovered);
}
/* === End Preview Helper === */

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
      const normalized = savedClients.map(recomputeStatus);
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
      const normalized = savedClients.map(recomputeStatus);
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

  // PaymentTracking component with modal
  const PaymentTracking = () => {
    // --- Payment preview computed values ---
    const monthlyFee = Number(selectedClient?.amount || 0);
    const paid = Number((paymentAmount || '').toString().trim() || (monthlyFee || 0));
    const monthsCovered = Number.isFinite(paid) && (monthlyFee || 0) > 0
      ? Math.max(1, Math.floor(paid / monthlyFee))
      : 0;

    const previewNextDue = selectedClient && monthsCovered > 0
      ? computeNextDuePreview(selectedClient.nextDue || new Date().toISOString().split('T')[0], monthsCovered)
      : null;

    const isPaymentInvalid = !selectedClient || !Number.isFinite(paid) || paid <= 0 || (monthlyFee || 0) <= 0;

    if (!isRecordingPayment || !selectedClient) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
          <h3 className="text-lg font-semibold mb-4">Record Payment</h3>
          <p className="text-gray-600 mb-4">
            Recording payment for <strong>{selectedClient.name}</strong>
          </p>
          
          <form onSubmit={handleSubmitPayment}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Payment Amount (${monthlyFee} monthly fee)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={paymentAmount}
                onChange={(e) => setPaymentAmount(e.target.value)}
                placeholder={`Enter amount (default: $${monthlyFee})`}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
              {/* Monthly fee hint */}
              <p className="mt-1 text-xs text-gray-500">
                Monthly fee:&nbsp;
                <span className="font-medium text-gray-900">
                  {Number.isFinite(monthlyFee) && monthlyFee > 0 ? `$${monthlyFee.toFixed(2)}` : '—'}
                </span>
              </p>
            </div>

            {/* Payment Preview (non-blocking UX) */}
            <div className="mt-2 rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Current next due</span>
                <span className="font-medium text-gray-900">
                  {selectedClient?.nextDue || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-gray-600">Months covered</span>
                <span className="font-medium text-gray-900">
                  {monthsCovered > 0 ? monthsCovered : '—'}
                </span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-gray-600">New next due (preview)</span>
                <span className="font-semibold">
                  {previewNextDue || '—'}
                </span>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                type="button"
                onClick={() => {
                  setIsRecordingPayment(false);
                  setSelectedClient(null);
                  setPaymentAmount('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isPaymentInvalid}
                className={`flex-1 rounded-lg px-4 py-2 font-semibold text-white ${isPaymentInvalid ? 'bg-gray-300 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700'}`}
              >
                Record Payment
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* Component JSX would go here */}
      <h1>Payment Management Component</h1>
      {/* Add your UI components here */}
      
      {/* Payment Modal */}
      <PaymentTracking />
    </div>
  );
};

export default PaymentComponent;
import React, { useState, useEffect } from 'react';
import gymStorage from './storage'; // Updated to correct import path
import { toISODate, add30DaysFrom, recomputeStatus, advanceNextDueByCycles, daysBetween } from './utils/date';
import { ClientSchema, PaymentSchema } from './utils/validation';
import PaymentsHistory from './components/payments/PaymentsHistory';
import { nextDueDateFromJoin, isOverdue } from "./billing";
import LockBadge from "./LockBadge";

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
  const [activeTab, setActiveTab] = useState('dashboard');

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

  // Compute clients with billing info
  const clientsWithBilling = (Array.isArray(clients) ? clients : []).map(c => {
    const due = c?.joinDate ? nextDueDateFromJoin(c.joinDate) : null;
    const overdue = c?.joinDate ? isOverdue(c.joinDate) : false;
    return {
      ...c,
      _dueDate: due ? due.toISOString().slice(0, 10) : null,
      _status: overdue ? "Overdue" : "Active"
    };
  });

  // Dashboard counts
  const overdueClients = clientsWithBilling.filter(c => c._status === "Overdue").length;
  const totalClients = clientsWithBilling.length;

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
      const todayISO = toISODate();
      const client = {
        ...newClient,
        id: Date.now().toString(),
        joinDate: todayISO,
        lastPayment: todayISO, // set to null if you don't want a payment at join
        nextDue: add30DaysFrom(todayISO), // strict 30-day cycle
        status: 'Active',
        overdue: 0,
        amount: membershipPricing[newClient.membershipType] || newClient.amount
      };

      const normalized = recomputeStatus(client);
      
      const parseResult = ClientSchema.safeParse(normalized);
      if (!parseResult.success) { 
        alert(parseResult.error.issues[0]?.message || 'Invalid client data'); 
        return; 
      }
      
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

    const todayISO = toISODate();

    const updatedClients = await Promise.all(
      clients.map(async (c) => {
        if (c.id !== selectedClient.id) return c;

        // Advance FROM the existing nextDue, not from today
        const nextDueISO = advanceNextDueByCycles(c.nextDue || todayISO, monthsCovered);

        const updated = recomputeStatus({
          ...c,
          lastPayment: todayISO,
          nextDue: nextDueISO
        });

        // Persist member update
        await gymStorage.saveMembers(updated);

        // Save a payment record (history)
        const payCheck = PaymentSchema.safeParse({
          clientId: c.id,
          date: todayISO,
          amount: paid,
          monthsCovered,
          method: 'cash'
        });
        if (!payCheck.success) { 
          alert(payCheck.error.issues[0]?.message || 'Invalid payment'); 
          return c; 
        }
        
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

    // Focus management for accessibility
    useEffect(() => {
      if (isRecordingPayment && selectedClient) {
        const focusFirstInput = () => {
          const firstInput = document.querySelector('.payment-amount-input');
          if (firstInput) {
            firstInput.focus();
          }
        };
        // Small delay to ensure modal is rendered
        setTimeout(focusFirstInput, 100);
      }
    }, [isRecordingPayment, selectedClient]);

    // ESC key handler
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setIsRecordingPayment(false);
        setSelectedClient(null);
        setPaymentAmount('');
      }
    };

    if (!isRecordingPayment || !selectedClient) return null;

    return (
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        role="dialog" 
        aria-modal="true" 
        aria-labelledby="paymentModalTitle"
        onKeyDown={handleKeyDown}
      >
        <div 
          className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
          tabIndex="-1"
          role="document"
          aria-describedby="paymentModalDesc"
        >
          <h3 id="paymentModalTitle" className="text-xl font-bold text-gray-900 mb-6">Record Payment</h3>
          <p id="paymentModalDesc" className="sr-only">Enter amount to record a payment and review the new next due date.</p>
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
                className="payment-amount-input w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                Record Payment <LockBadge />
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* Tab Navigation */}
      <div className="bg-white border-b">
        <div className="flex space-x-8 px-6">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'dashboard'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('paymentsHistory')}
            className={`py-3 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'paymentsHistory'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Payments History
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <div>
          <h1>Payment Management Component</h1>
          {/* Add your existing dashboard UI components here */}
        </div>
      )}
      
      {activeTab === 'paymentsHistory' && <PaymentsHistory />}
      
      {/* Payment Modal */}
      <PaymentTracking />
    </div>
  );
};

export default PaymentComponent;
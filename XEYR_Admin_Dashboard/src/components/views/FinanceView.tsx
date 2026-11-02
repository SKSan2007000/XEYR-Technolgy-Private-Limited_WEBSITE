import React, { useEffect, useState } from 'react';
import { InvoiceQuote, PaymentRecord, ExpenseRecord } from '../../types';
import { financeApi } from '../../services/api';
import {
  IndianRupee,
  FileText,
  CreditCard,
  DollarSign,
  Plus,
  RefreshCw,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

interface FinanceViewProps {
  searchQuery?: string;
}

export const FinanceView: React.FC<FinanceViewProps> = ({ searchQuery = '' }) => {
  const [invoices, setInvoices] = useState<InvoiceQuote[]>([]);
  const [payments, setPayments] = useState<PaymentRecord[]>([]);
  const [expenses, setExpenses] = useState<ExpenseRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'invoices' | 'payments' | 'expenses'>('invoices');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Invoice Modal
  const [invoiceModal, setInvoiceModal] = useState(false);
  const [requirementId, setRequirementId] = useState<number>(1);
  const [docType, setDocType] = useState<'INVOICE' | 'QUOTE'>('INVOICE');
  const [amountInvoiced, setAmountInvoiced] = useState<number>(50000);
  const [dueDate, setDueDate] = useState('');
  const [invoiceNotes, setInvoiceNotes] = useState('');

  // New Payment Modal
  const [paymentModal, setPaymentModal] = useState(false);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | ''>('');
  const [txRef, setTxRef] = useState('');
  const [payMethod, setPayMethod] = useState('BANK_TRANSFER');
  const [payAmount, setPayAmount] = useState<number>(25000);
  const [payNotes, setPayNotes] = useState('');

  const fetchFinancials = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invData, payData, expData] = await Promise.all([
        financeApi.getInvoices().catch(() => []),
        financeApi.getPayments().catch(() => []),
        financeApi.getExpenses().catch(() => [])
      ]);
      setInvoices(invData);
      setPayments(payData);
      setExpenses(expData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch financial records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinancials();
  }, []);

  const handleCreateInvoice = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await financeApi.createInvoice({
        requirement: requirementId,
        doc_type: docType,
        amount_invoiced: amountInvoiced,
        amount_quoted: amountInvoiced,
        due_date: dueDate || null,
        notes: invoiceNotes
      });
      alert('Financial record created successfully.');
      setInvoiceModal(false);
      await fetchFinancials();
    } catch (err: any) {
      alert('Error creating invoice: ' + err.message);
    }
  };

  const handleCreatePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!txRef.trim()) {
      alert('Transaction reference ID is required.');
      return;
    }
    try {
      await financeApi.createPayment({
        invoice: selectedInvoiceId || null,
        transaction_reference: txRef.trim(),
        payment_method: payMethod,
        amount: payAmount,
        notes: payNotes
      });
      alert('Payment receipt logged and reconciled in PostgreSQL.');
      setPaymentModal(false);
      setTxRef('');
      await fetchFinancials();
    } catch (err: any) {
      alert('Error recording payment: ' + err.message);
    }
  };

  // Verified Financial Calculations
  const totalInvoiced = invoices.reduce((acc, curr) => acc + Number(curr.amount_invoiced || 0), 0);
  const totalReceived = payments.filter((p) => p.payment_status === 'VERIFIED').reduce((acc, curr) => acc + Number(curr.amount || 0), 0);
  const totalExpenses = expenses.reduce((acc, curr) => acc + Number(curr.amount || 0), 0);
  const pendingCollection = Math.max(0, totalInvoiced - totalReceived);

  return (
    <div>
      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card" style={{ background: '#f8fafc' }}>
          <div style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>
            Total Invoiced
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
            ₹{totalInvoiced.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '2px' }}>
            Tax Invoices &amp; Approved Quotes
          </div>
        </div>

        <div className="card" style={{ background: '#ecfdf5', borderColor: '#a7f3d0' }}>
          <div style={{ fontSize: '0.78rem', color: '#047857', fontWeight: 700, textTransform: 'uppercase' }}>
            Gross Received (Reconciled)
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#065f46', marginTop: '4px' }}>
            ₹{totalReceived.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#047857', marginTop: '2px' }}>
            Verified Bank &amp; Gateway Receipts
          </div>
        </div>

        <div className="card" style={{ background: '#fffbeb', borderColor: '#fde68a' }}>
          <div style={{ fontSize: '0.78rem', color: '#b45309', fontWeight: 700, textTransform: 'uppercase' }}>
            Pending Collections
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#92400e', marginTop: '4px' }}>
            ₹{pendingCollection.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#b45309', marginTop: '2px' }}>
            Outstanding Invoice Balances
          </div>
        </div>

        <div className="card" style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
          <div style={{ fontSize: '0.78rem', color: '#b91c1c', fontWeight: 700, textTransform: 'uppercase' }}>
            Operating Expenses
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#991b1b', marginTop: '4px' }}>
            ₹{totalExpenses.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#b91c1c', marginTop: '2px' }}>
            Infra, Tools &amp; Training Costs
          </div>
        </div>
      </div>

      {/* Tabs & Action Bar */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setActiveTab('invoices')}
              className={`btn btn-sm ${activeTab === 'invoices' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Invoices &amp; Quotations ({invoices.length})
            </button>
            <button
              onClick={() => setActiveTab('payments')}
              className={`btn btn-sm ${activeTab === 'payments' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Payment Receipts ({payments.length})
            </button>
            <button
              onClick={() => setActiveTab('expenses')}
              className={`btn btn-sm ${activeTab === 'expenses' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Expenses ({expenses.length})
            </button>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setInvoiceModal(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> New Invoice
            </button>
            <button onClick={() => setPaymentModal(true)} className="btn btn-success btn-sm">
              <CreditCard size={14} /> Record Payment
            </button>
            <button onClick={fetchFinancials} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading accounting ledgers...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : activeTab === 'invoices' ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Reference No</th>
                <th>Type</th>
                <th>Invoiced Amount</th>
                <th>Received</th>
                <th>Pending</th>
                <th>Due Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {invoices.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: '#94a3b8' }}>No invoices created yet.</td></tr>
              ) : (
                invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td><strong style={{ color: '#1465f4' }}>{inv.reference_no}</strong></td>
                    <td><span className="badge badge-gray">{inv.doc_type}</span></td>
                    <td><strong>₹{Number(inv.amount_invoiced).toLocaleString('en-IN')}</strong></td>
                    <td style={{ color: '#059669', fontWeight: 600 }}>₹{Number(inv.amount_received || 0).toLocaleString('en-IN')}</td>
                    <td style={{ color: '#b45309', fontWeight: 600 }}>₹{Number(inv.amount_pending || 0).toLocaleString('en-IN')}</td>
                    <td>{inv.due_date || 'On Delivery'}</td>
                    <td><span className="badge badge-qualified">{inv.status}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : activeTab === 'payments' ? (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Transaction Reference</th>
                <th>Payment Method</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Payment Date</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {payments.length === 0 ? (
                <tr><td colSpan={6} style={{ textAlign: 'center', color: '#94a3b8' }}>No payment records logged.</td></tr>
              ) : (
                payments.map((p) => (
                  <tr key={p.id}>
                    <td><strong>{p.transaction_reference}</strong></td>
                    <td><span className="badge badge-new">{p.payment_method.replace('_', ' ')}</span></td>
                    <td><strong style={{ color: '#059669' }}>₹{Number(p.amount).toLocaleString('en-IN')}</strong></td>
                    <td><span className="badge badge-qualified">{p.payment_status}</span></td>
                    <td>{new Date(p.payment_date).toLocaleDateString('en-IN')}</td>
                    <td><span style={{ fontSize: '0.8rem', color: '#64748b' }}>{p.notes || '-'}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Expense Title</th>
                <th>Category</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {expenses.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#94a3b8' }}>No expense records logged.</td></tr>
              ) : (
                expenses.map((exp) => (
                  <tr key={exp.id}>
                    <td><strong>{exp.title}</strong></td>
                    <td><span className="badge badge-gray">{exp.category.replace('_', ' ')}</span></td>
                    <td><strong style={{ color: '#dc2626' }}>₹{Number(exp.amount).toLocaleString('en-IN')}</strong></td>
                    <td>{exp.date}</td>
                    <td><span style={{ fontSize: '0.8rem', color: '#64748b' }}>{exp.notes || '-'}</span></td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* New Invoice Modal */}
      {invoiceModal && (
        <div className="modal-overlay" onClick={() => setInvoiceModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="card-title">Create Tax Invoice / Quotation</h3>
              <button onClick={() => setInvoiceModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleCreateInvoice}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Document Type</label>
                  <select
                    className="form-select"
                    value={docType}
                    onChange={(e) => setDocType(e.target.value as any)}
                  >
                    <option value="INVOICE">Tax Invoice</option>
                    <option value="QUOTE">Quotation / Commercial Proposal</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Requirement Workspace ID</label>
                  <input
                    type="number"
                    className="form-input"
                    value={requirementId}
                    onChange={(e) => setRequirementId(Number(e.target.value))}
                    required
                    min={1}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Amount (₹ INR) *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={amountInvoiced}
                    onChange={(e) => setAmountInvoiced(Number(e.target.value))}
                    required
                    min={1}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Payment Due Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Notes &amp; Payment Milestones</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={invoiceNotes}
                    onChange={(e) => setInvoiceNotes(e.target.value)}
                    placeholder="Milestone breakdown (e.g. 50% advance, 50% on final handover)..."
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setInvoiceModal(false)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary">Generate Financial Document</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Payment Modal */}
      {paymentModal && (
        <div className="modal-overlay" onClick={() => setPaymentModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="card-title">Record Verified Payment</h3>
              <button onClick={() => setPaymentModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleCreatePayment}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Transaction Reference (UTR / Bank Ref / Gateway ID) *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. UTR1234567890 or pay_XXXXXX"
                    value={txRef}
                    onChange={(e) => setTxRef(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Payment Method</label>
                  <select
                    className="form-select"
                    value={payMethod}
                    onChange={(e) => setPayMethod(e.target.value)}
                  >
                    <option value="BANK_TRANSFER">Bank Transfer (NEFT / RTGS / IMPS)</option>
                    <option value="UPI">UPI / QR</option>
                    <option value="CHEQUE">Cheque / Demand Draft</option>
                    <option value="CARD_RAZORPAY_PREP">Razorpay Gateway Foundation</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Amount Received (₹ INR) *</label>
                  <input
                    type="number"
                    className="form-input"
                    value={payAmount}
                    onChange={(e) => setPayAmount(Number(e.target.value))}
                    required
                    min={1}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Audit Notes</label>
                  <textarea
                    className="form-textarea"
                    rows={2}
                    value={payNotes}
                    onChange={(e) => setPayNotes(e.target.value)}
                    placeholder="Bank account credited, transaction date, or client acknowledgment..."
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setPaymentModal(false)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-success">Save Payment Receipt</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

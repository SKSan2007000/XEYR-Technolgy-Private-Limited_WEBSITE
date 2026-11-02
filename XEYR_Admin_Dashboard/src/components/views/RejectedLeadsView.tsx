import React, { useEffect, useState } from 'react';
import { Enquiry } from '../../types';
import { crmApi, analyticsApi } from '../../services/api';
import { ActiveTab } from '../layout/Sidebar';
import {
  UserX,
  RefreshCw,
  Building,
  Mail,
  Phone,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  FileText,
  PieChart
} from 'lucide-react';

interface RejectedLeadsViewProps {
  searchQuery?: string;
  setActiveTab?: (tab: ActiveTab) => void;
}

export const RejectedLeadsView: React.FC<RejectedLeadsViewProps> = ({ searchQuery = '', setActiveTab }) => {
  const [rejectedLeads, setRejectedLeads] = useState<Enquiry[]>([]);
  const [rejectionAnalytics, setRejectionAnalytics] = useState<Array<{ category: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Reopen modal
  const [reopenModal, setReopenModal] = useState<Enquiry | null>(null);
  const [reopenReason, setReopenReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Details modal
  const [selectedLead, setSelectedLead] = useState<Enquiry | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [leadsData, metricsData] = await Promise.all([
        crmApi.getEnquiries('REJECTED'),
        analyticsApi.getDashboardMetrics('last_30_days').catch(() => null)
      ]);
      setRejectedLeads(Array.isArray(leadsData) ? leadsData : []);
      if (metricsData && metricsData.rejection_reasons) {
        setRejectionAnalytics(metricsData.rejection_reasons);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch rejected leads.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reopenModal) return;
    if (!reopenReason.trim()) {
      alert('A valid reason for reopening is required for compliance.');
      return;
    }
    setActionLoading(true);
    try {
      await crmApi.reopen(reopenModal.id, reopenReason.trim());
      alert(`Enquiry ${reopenModal.reference_id} has been reopened and moved to Under Review.`);
      setReopenModal(null);
      setReopenReason('');
      await fetchData();
    } catch (err: any) {
      alert('Reopen failed: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  };

  const filtered = rejectedLeads.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.reference_id?.toLowerCase().includes(q) ||
      item.client_name?.toLowerCase().includes(q) ||
      item.project_title?.toLowerCase().includes(q) ||
      item.rejection?.reason_detail?.toLowerCase().includes(q) ||
      item.rejection?.category?.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      {/* Analytics Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card" style={{ background: '#fef2f2', borderColor: '#fecaca' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#991b1b', textTransform: 'uppercase' }}>
            Total Rejected Enquiries
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#dc2626', marginTop: '6px' }}>
            {rejectedLeads.length}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#7f1d1d', marginTop: '4px' }}>
            Documented with mandatory compliance reasons
          </div>
        </div>

        <div className="card" style={{ background: '#fffbeb', borderColor: '#fde68a' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#92400e', textTransform: 'uppercase' }}>
            Rejection Categories Recorded
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#b45309', marginTop: '6px' }}>
            {rejectionAnalytics.length}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#78350f', marginTop: '4px' }}>
            Derived directly from PostgreSQL rejection audit log
          </div>
        </div>
      </div>

      {/* Rejection Breakdown Panel if records exist */}
      {rejectionAnalytics.length > 0 && (
        <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
          <h4 style={{ fontSize: '0.92rem', fontWeight: 800, color: '#0f172a', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PieChart size={16} color="#dc2626" /> Verified Rejection Reasons Distribution
          </h4>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {rejectionAnalytics.map((item, idx) => (
              <div
                key={idx}
                style={{
                  background: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '8px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '0.82rem'
                }}
              >
                <span style={{ fontWeight: 600, color: '#334155' }}>
                  {item.category.replace(/_/g, ' ')}:
                </span>
                <span className="badge badge-rejected" style={{ fontSize: '0.75rem' }}>
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Header */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Disqualified / Rejected Leads Audit</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              All rejected leads require verified rejection reasons. Administrators may reopen leads when commercial parameters improve.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={fetchData} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading rejected leads...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px', color: '#64748b' }}>
          <UserX size={44} color="#cbd5e1" style={{ margin: '0 auto 14px' }} />
          <h3 style={{ fontSize: '1.15rem', color: '#1e293b', marginBottom: '6px' }}>No records yet</h3>
          <p style={{ fontSize: '0.88rem' }}>No leads have been rejected or disqualified.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {filtered.map((lead) => {
            const rej = lead.rejection;
            const catLabel = rej?.category ? rej.category.replace(/_/g, ' ') : 'Unspecified Category';
            const reasonDetail = rej?.reason_detail || 'No detailed reason provided.';

            return (
              <div key={lead.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', borderColor: '#fecaca' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <span className="badge badge-rejected">{catLabel}</span>
                    <span style={{ fontSize: '0.76rem', color: '#64748b' }}>
                      Ref: <strong style={{ color: '#1465f4' }}>{lead.reference_id}</strong>
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '6px' }}>
                    {lead.project_title}
                  </h3>

                  <div style={{ fontSize: '0.84rem', color: '#475569', marginBottom: '14px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Building size={14} color="#64748b" /> {lead.client_name} {lead.company_name ? `(${lead.company_name})` : ''}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Mail size={14} color="#64748b" /> {lead.email}
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Phone size={14} color="#64748b" /> {lead.phone}
                    </span>
                  </div>

                  {/* Rejection Audit Box */}
                  <div style={{ background: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#b91c1c', fontWeight: 700, fontSize: '0.8rem', marginBottom: '4px' }}>
                      <AlertTriangle size={14} /> Recorded Disqualification Reason:
                    </div>
                    <p style={{ margin: 0, fontSize: '0.82rem', color: '#7f1d1d', lineHeight: 1.45 }}>
                      {reasonDetail}
                    </p>
                    {rej?.rejected_at && (
                      <div style={{ marginTop: '8px', fontSize: '0.72rem', color: '#991b1b' }}>
                        Rejected on {new Date(rej.rejected_at).toLocaleString('en-IN')}
                      </div>
                    )}
                  </div>
                </div>

                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <button
                    onClick={() => setSelectedLead(lead)}
                    className="btn btn-secondary btn-sm"
                  >
                    <FileText size={14} /> View Scope
                  </button>
                  <button
                    onClick={() => {
                      setReopenModal(lead);
                      setReopenReason('');
                    }}
                    className="btn btn-primary btn-sm"
                  >
                    <RotateCcw size={14} /> Reopen Enquiry
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Reopen Modal */}
      {reopenModal && (
        <div className="modal-overlay" onClick={() => setReopenModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">AUDIT MUTATION</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>
                  Reopen Enquiry: {reopenModal.reference_id}
                </h3>
              </div>
              <button onClick={() => setReopenModal(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleReopenSubmit}>
              <div className="modal-body">
                <p style={{ fontSize: '0.84rem', color: '#64748b', marginBottom: '14px' }}>
                  Reopening will move this enquiry from Rejected back to Under Review status. State transitions are permanently recorded in the immutable audit log.
                </p>

                <div className="form-group">
                  <label className="form-label">Reason for Reopening *</label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    value={reopenReason}
                    onChange={(e) => setReopenReason(e.target.value)}
                    placeholder="e.g. Client agreed to enterprise scope, updated budget, or revised delivery timeline..."
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setReopenModal(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={actionLoading}>
                  {actionLoading ? 'Reopening...' : 'Confirm Reopen'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Scope Details Modal */}
      {selectedLead && (
        <div className="modal-overlay" onClick={() => setSelectedLead(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(640px, 94vw)' }}>
            <div className="modal-header">
              <h3 className="card-title">Enquiry Scope: {selectedLead.reference_id}</h3>
              <button onClick={() => setSelectedLead(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <div className="modal-body">
              <div style={{ marginBottom: '14px' }}>
                <strong>Client:</strong> {selectedLead.client_name}
              </div>
              <div style={{ marginBottom: '14px' }}>
                <strong>Service Requested:</strong> {selectedLead.service_type}
              </div>
              <div style={{ marginBottom: '14px' }}>
                <strong>Proposed Budget:</strong> {selectedLead.budget_range || 'Not Specified'}
              </div>
              <div>
                <strong>Original Description:</strong>
                <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', marginTop: '6px', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
                  {selectedLead.project_description || 'No description provided.'}
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setSelectedLead(null)} className="btn btn-secondary">Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

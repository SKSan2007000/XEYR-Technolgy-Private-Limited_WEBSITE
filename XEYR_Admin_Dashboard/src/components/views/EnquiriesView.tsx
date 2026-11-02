import React, { useEffect, useState } from 'react';
import { Enquiry } from '../../types';
import { crmApi } from '../../services/api';
import {
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Eye,
  RefreshCw,
  Clock,
  Send,
  Building,
  Mail,
  Phone,
  FileText,
  Inbox
} from 'lucide-react';

interface EnquiriesViewProps {
  searchQuery?: string;
  defaultStatus?: string;
}

export const EnquiriesView: React.FC<EnquiriesViewProps> = ({ searchQuery = '', defaultStatus = '' }) => {
  const [enquiries, setEnquiries] = useState<Enquiry[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>(defaultStatus);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Selected enquiry for details modal
  const [selectedEnquiry, setSelectedEnquiry] = useState<Enquiry | null>(null);

  // Qualify modal state
  const [qualifyModal, setQualifyModal] = useState<Enquiry | null>(null);
  const [qualifyEstValue, setQualifyEstValue] = useState<number>(100000);
  const [qualifyBudgetOk, setQualifyBudgetOk] = useState<boolean>(true);
  const [qualifyTimelineOk, setQualifyTimelineOk] = useState<boolean>(true);
  const [qualifyNotes, setQualifyNotes] = useState<string>('');

  // Reject modal state
  const [rejectModal, setRejectModal] = useState<Enquiry | null>(null);
  const [rejectCategory, setRejectCategory] = useState<string>('BUDGET_MISMATCH');
  const [rejectReason, setRejectReason] = useState<string>('');

  // Activity modal state
  const [activityTitle, setActivityTitle] = useState('');
  const [activityType, setActivityType] = useState('NOTE');
  const [activityDesc, setActivityDesc] = useState('');

  const [actionLoading, setActionLoading] = useState(false);

  const fetchEnquiries = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await crmApi.getEnquiries(statusFilter || undefined);
      setEnquiries(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load enquiries from database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEnquiries();
  }, [statusFilter]);

  const handleQualifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qualifyModal) return;
    setActionLoading(true);
    try {
      await crmApi.qualify(qualifyModal.id, {
        estimated_project_value: Number(qualifyEstValue),
        budget_confirmed: qualifyBudgetOk,
        timeline_confirmed: qualifyTimelineOk,
        notes: qualifyNotes
      });
      setQualifyModal(null);
      await fetchEnquiries();
    } catch (err: any) {
      alert('Qualification failed: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectModal) return;
    if (!rejectReason.trim()) {
      alert('A detailed rejection reason is mandatory for compliance audit.');
      return;
    }
    setActionLoading(true);
    try {
      await crmApi.reject(rejectModal.id, {
        category: rejectCategory,
        reason_detail: rejectReason.trim()
      });
      setRejectModal(null);
      setRejectReason('');
      await fetchEnquiries();
    } catch (err: any) {
      alert('Rejection failed: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAddActivity = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEnquiry || !activityTitle.trim()) return;
    try {
      await crmApi.addActivity(selectedEnquiry.id, {
        activity_type: activityType,
        title: activityTitle.trim(),
        description: activityDesc.trim()
      });
      setActivityTitle('');
      setActivityDesc('');
      // Refresh selected enquiry
      const updated = await crmApi.getEnquiry(selectedEnquiry.id);
      setSelectedEnquiry(updated);
      await fetchEnquiries();
    } catch (err: any) {
      alert('Failed to log CRM activity: ' + err.message);
    }
  };

  const filteredEnquiries = enquiries.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.reference_id?.toLowerCase().includes(q) ||
      item.client_name?.toLowerCase().includes(q) ||
      item.email?.toLowerCase().includes(q) ||
      item.project_title?.toLowerCase().includes(q) ||
      item.company_name?.toLowerCase().includes(q)
    );
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'NEW':
        return <span className="badge badge-new">New Enquiry</span>;
      case 'QUALIFIED':
        return <span className="badge badge-qualified">Qualified</span>;
      case 'REJECTED':
        return <span className="badge badge-rejected">Rejected</span>;
      case 'CONTACTED':
      case 'IN_REVIEW':
        return <span className="badge badge-pending">{status.replace('_', ' ')}</span>;
      default:
        return <span className="badge badge-gray">{status}</span>;
    }
  };

  return (
    <div>
      {/* Action Header & Filters */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Filter size={16} color="#64748b" />
            <span style={{ fontSize: '0.84rem', fontWeight: 700, color: '#475569' }}>Filter Status:</span>
            <select
              className="form-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ width: 'auto', padding: '6px 12px', fontSize: '0.82rem' }}
            >
              <option value="">All Statuses</option>
              <option value="NEW">New Enquiries</option>
              <option value="CONTACTED">Contacted</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="QUALIFIED">Qualified</option>
              <option value="REJECTED">Rejected</option>
              <option value="CONVERTED">Converted to Project</option>
            </select>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Showing <strong>{filteredEnquiries.length}</strong> record{filteredEnquiries.length === 1 ? '' : 's'}
            </span>
            <button onClick={fetchEnquiries} className="btn btn-secondary btn-sm" title="Refresh from database">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading pipeline enquiries...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>
          {error}
        </div>
      ) : filteredEnquiries.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <Inbox size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Enquiries Found</h3>
          <p style={{ fontSize: '0.85rem' }}>No enquiries match the current status filter or search parameters.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Client / Company</th>
                <th>Service Type</th>
                <th>Project Title &amp; Budget</th>
                <th>Status</th>
                <th>Date Received</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredEnquiries.map((enq) => (
                <tr key={enq.id}>
                  <td>
                    <strong style={{ color: '#1465f4' }}>{enq.reference_id}</strong>
                  </td>
                  <td>
                    <div style={{ fontWeight: 700 }}>{enq.client_name}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      {enq.company_name ? `${enq.company_name} • ` : ''}{enq.email}
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{enq.service_type}</span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: '#0f172a' }}>{enq.project_title}</div>
                    <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                      Budget: <strong>{enq.budget_range || 'Not Specified'}</strong>
                    </div>
                  </td>
                  <td>{getStatusBadge(enq.status)}</td>
                  <td>
                    <div style={{ fontSize: '0.82rem' }}>
                      {new Date(enq.created_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'inline-flex', gap: '6px' }}>
                      <button
                        onClick={() => setSelectedEnquiry(enq)}
                        className="btn btn-secondary btn-sm"
                        title="View details & log activity"
                      >
                        <Eye size={14} /> View
                      </button>
                      {enq.status !== 'QUALIFIED' && enq.status !== 'REJECTED' && (
                        <>
                          <button
                            onClick={() => setQualifyModal(enq)}
                            className="btn btn-success btn-sm"
                            title="Qualify lead"
                          >
                            <CheckCircle2 size={14} /> Qualify
                          </button>
                          <button
                            onClick={() => setRejectModal(enq)}
                            className="btn btn-danger btn-sm"
                            title="Reject lead with reason"
                          >
                            <XCircle size={14} /> Reject
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* View Enquiry Details & Activity Modal */}
      {selectedEnquiry && (
        <div className="modal-overlay" onClick={() => setSelectedEnquiry(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(760px, 94vw)' }}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new" style={{ marginBottom: '4px' }}>
                  {selectedEnquiry.reference_id}
                </span>
                <h3 className="card-title">{selectedEnquiry.project_title}</h3>
              </div>
              <button onClick={() => setSelectedEnquiry(null)} className="btn btn-secondary btn-sm">
                ✕
              </button>
            </div>
            <div className="modal-body">
              {/* Client Info Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px', background: '#f8fafc', padding: '16px', borderRadius: '10px' }}>
                <div>
                  <small style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Building size={12} /> Client &amp; Company
                  </small>
                  <strong>{selectedEnquiry.client_name}</strong>
                  <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{selectedEnquiry.company_name || 'Individual Client'}</div>
                </div>
                <div>
                  <small style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Mail size={12} /> Contact Email
                  </small>
                  <a href={`mailto:${selectedEnquiry.email}`} style={{ color: '#1465f4', fontSize: '0.85rem' }}>
                    {selectedEnquiry.email}
                  </a>
                </div>
                <div>
                  <small style={{ color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Phone size={12} /> Phone Number
                  </small>
                  <strong>{selectedEnquiry.phone}</strong>
                </div>
                <div>
                  <small style={{ color: '#64748b' }}>Current Status</small>
                  <div>{getStatusBadge(selectedEnquiry.status)}</div>
                </div>
              </div>

              {/* Project Description */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '6px', color: '#334155' }}>Project Description &amp; Scope</h4>
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '14px', fontSize: '0.88rem', color: '#0f172a', whiteSpace: 'pre-wrap' }}>
                  {selectedEnquiry.project_description || 'No description provided.'}
                </div>
              </div>

              {/* Rejection Details if rejected */}
              {selectedEnquiry.rejection && (
                <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '14px', marginBottom: '20px' }}>
                  <h4 style={{ color: '#b91c1c', fontSize: '0.88rem', marginBottom: '4px' }}>
                    Disqualification Reason: {selectedEnquiry.rejection.category.replace('_', ' ')}
                  </h4>
                  <p style={{ fontSize: '0.84rem', color: '#7f1d1d' }}>{selectedEnquiry.rejection.reason_detail}</p>
                </div>
              )}

              {/* Log CRM Activity */}
              <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '20px' }}>
                <h4 style={{ fontSize: '0.9rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={16} color="#1465f4" /> CRM Activity Log &amp; Client Interactions
                </h4>
                <form onSubmit={handleAddActivity} style={{ display: 'grid', gridTemplateColumns: '150px 1fr auto', gap: '10px', marginBottom: '16px' }}>
                  <select
                    className="form-select"
                    value={activityType}
                    onChange={(e) => setActivityType(e.target.value)}
                  >
                    <option value="NOTE">Internal Note</option>
                    <option value="CALL">Phone Call</option>
                    <option value="MEETING">Meeting</option>
                    <option value="EMAIL">Email</option>
                  </select>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Activity title / summary..."
                    value={activityTitle}
                    onChange={(e) => setActivityTitle(e.target.value)}
                    required
                  />
                  <button type="submit" className="btn btn-primary btn-sm">
                    <Send size={14} /> Log
                  </button>
                </form>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setSelectedEnquiry(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Qualify Modal */}
      {qualifyModal && (
        <div className="modal-overlay" onClick={() => setQualifyModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="badge badge-qualified">LEAD QUALIFICATION</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>
                  Qualify Lead: {qualifyModal.reference_id}
                </h3>
              </div>
              <button onClick={() => setQualifyModal(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleQualifySubmit}>
              <div className="modal-body">
                <p style={{ fontSize: '0.84rem', color: '#64748b', marginBottom: '16px' }}>
                  Validating this lead creates a qualified requirement record and moves the enquiry into the engineering pipeline.
                </p>

                <div className="form-group">
                  <label className="form-label">Estimated Project Value (INR ₹)</label>
                  <input
                    type="number"
                    className="form-input"
                    value={qualifyEstValue}
                    onChange={(e) => setQualifyEstValue(Number(e.target.value))}
                    required
                    min={1000}
                    step={5000}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '16px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={qualifyBudgetOk}
                      onChange={(e) => setQualifyBudgetOk(e.target.checked)}
                    />
                    Budget Confirmed with Client
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={qualifyTimelineOk}
                      onChange={(e) => setQualifyTimelineOk(e.target.checked)}
                    />
                    Timeline Feasible
                  </label>
                </div>

                <div className="form-group">
                  <label className="form-label">Qualification Notes / Scope Agreement</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={qualifyNotes}
                    onChange={(e) => setQualifyNotes(e.target.value)}
                    placeholder="Enter agreed project scope, technical stack recommendations, and payment milestone plan..."
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setQualifyModal(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-success" disabled={actionLoading}>
                  <CheckCircle2 size={16} /> Confirm Qualification
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectModal && (
        <div className="modal-overlay" onClick={() => setRejectModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="badge badge-rejected">DISQUALIFICATION AUDIT</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>
                  Reject Enquiry: {rejectModal.reference_id}
                </h3>
              </div>
              <button onClick={() => setRejectModal(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleRejectSubmit}>
              <div className="modal-body">
                <p style={{ fontSize: '0.84rem', color: '#64748b', marginBottom: '16px' }}>
                  In accordance with XEYR compliance policies, a mandatory audit category and detailed explanation are recorded in PostgreSQL.
                </p>

                <div className="form-group">
                  <label className="form-label">Rejection Category *</label>
                  <select
                    className="form-select"
                    value={rejectCategory}
                    onChange={(e) => setRejectCategory(e.target.value)}
                    required
                  >
                    <option value="BUDGET_MISMATCH">Budget Mismatch / Unfeasible Pricing</option>
                    <option value="TIMELINE_INFEASIBLE">Timeline Infeasible</option>
                    <option value="CAPACITY_FULL">Engineering Capacity Full</option>
                    <option value="SCOPE_OUTSIDE_CAPABILITIES">Scope Outside Core Capabilities</option>
                    <option value="CLIENT_RESPONSIVE_FAIL">Client Unresponsive</option>
                    <option value="OTHER">Other Compliance Reason</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Detailed Audit Reason *</label>
                  <textarea
                    className="form-textarea"
                    rows={4}
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                    placeholder="Explain why this enquiry could not be qualified (mandatory)..."
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setRejectModal(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-danger" disabled={actionLoading}>
                  <XCircle size={16} /> Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

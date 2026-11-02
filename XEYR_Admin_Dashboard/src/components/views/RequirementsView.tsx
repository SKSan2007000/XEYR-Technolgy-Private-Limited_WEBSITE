import React, { useEffect, useState } from 'react';
import { ProjectRequirement } from '../../types';
import { requirementsApi } from '../../services/api';
import { ActiveTab } from '../layout/Sidebar';
import {
  FileSpreadsheet,
  CheckCircle,
  AlertCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  Edit,
  Save,
  Plus
} from 'lucide-react';

interface RequirementsViewProps {
  searchQuery?: string;
  setActiveTab: (tab: ActiveTab) => void;
}

export const RequirementsView: React.FC<RequirementsViewProps> = ({ searchQuery = '', setActiveTab }) => {
  const [requirements, setRequirements] = useState<ProjectRequirement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected for editing / readiness
  const [selectedReq, setSelectedReq] = useState<ProjectRequirement | null>(null);
  const [readinessData, setReadinessData] = useState<any>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);

  // Edit fields
  const [editTitle, setEditTitle] = useState('');
  const [editScope, setEditScope] = useState('');
  const [editDeliveryDate, setEditDeliveryDate] = useState('');
  const [newSpec, setNewSpec] = useState('');
  const [newDeliverable, setNewDeliverable] = useState('');
  const [specsList, setSpecsList] = useState<string[]>([]);
  const [deliverablesList, setDeliverablesList] = useState<string[]>([]);
  const [saveLoading, setSaveLoading] = useState(false);

  const fetchRequirements = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await requirementsApi.getRequirements();
      setRequirements(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch requirements workspaces.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequirements();
  }, []);

  const openEditor = (req: ProjectRequirement) => {
    setSelectedReq(req);
    setEditTitle(req.title);
    setEditScope(req.scope_summary);
    setEditDeliveryDate(req.target_delivery_date || '');
    setSpecsList(Array.isArray(req.functional_specs) ? req.functional_specs : []);
    setDeliverablesList(Array.isArray(req.deliverables_list) ? req.deliverables_list : []);
    setReadinessData(null);
  };

  const handleCheckReadiness = async (enquiryId: number) => {
    setReadinessLoading(true);
    try {
      const result = await requirementsApi.checkReadiness(enquiryId);
      setReadinessData(result);
    } catch (err: any) {
      alert('Readiness check error: ' + err.message);
    } finally {
      setReadinessLoading(false);
    }
  };

  const handleSaveRequirement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReq) return;
    setSaveLoading(true);
    try {
      await requirementsApi.saveRequirement(selectedReq.enquiry, {
        title: editTitle,
        scope_summary: editScope,
        target_delivery_date: editDeliveryDate || null,
        functional_specs: specsList,
        deliverables_list: deliverablesList
      });
      alert('Workspace requirements saved successfully.');
      await fetchRequirements();
      setSelectedReq(null);
    } catch (err: any) {
      alert('Save failed: ' + err.message);
    } finally {
      setSaveLoading(false);
    }
  };

  const filtered = requirements.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.requirement_reference?.toLowerCase().includes(q) ||
      item.title?.toLowerCase().includes(q) ||
      item.scope_summary?.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Project Engineering Workspaces</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Functional specifications, deliverables checklist, and technical readiness validation.
            </p>
          </div>
          <button onClick={fetchRequirements} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading requirements...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <FileSpreadsheet size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Requirements Workspaces Yet</h3>
          <p style={{ fontSize: '0.85rem' }}>Qualify an enquiry in CRM to automatically initiate a requirement workspace.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {filtered.map((req) => (
            <div key={req.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <span className="badge badge-new">{req.requirement_reference}</span>
                  <span className={`badge ${req.is_ready_for_handover ? 'badge-qualified' : 'badge-pending'}`}>
                    {req.status.replace('_', ' ')}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '8px' }}>{req.title}</h3>
                <p style={{ fontSize: '0.84rem', color: '#64748b', lineHeight: 1.45, marginBottom: '16px' }}>
                  {req.scope_summary || 'No scope summary defined yet.'}
                </p>

                <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', marginBottom: '16px', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ color: '#64748b' }}>Target Delivery:</span>
                    <strong>{req.target_delivery_date || 'TBD'}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#64748b' }}>Handover Readiness:</span>
                    <strong style={{ color: req.is_ready_for_handover ? '#059669' : '#f59e0b' }}>
                      {req.is_ready_for_handover ? '✅ Ready for ZIP' : '⏳ Pending Validation'}
                    </strong>
                  </div>
                </div>
              </div>

              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button onClick={() => openEditor(req)} className="btn btn-secondary btn-sm">
                  <Edit size={14} /> Edit Specs
                </button>
                <button
                  onClick={() => setActiveTab('handover')}
                  className="btn btn-primary btn-sm"
                  title="Go to developer handover generator"
                >
                  Developer Handover <ArrowRight size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Workspace Editor Modal */}
      {selectedReq && (
        <div className="modal-overlay" onClick={() => setSelectedReq(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(780px, 94vw)' }}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">{selectedReq.requirement_reference}</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>Requirements Workspace Editor</h3>
              </div>
              <button onClick={() => setSelectedReq(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleSaveRequirement}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Project Title</label>
                  <input
                    type="text"
                    className="form-input"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Technical Scope Summary</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={editScope}
                    onChange={(e) => setEditScope(e.target.value)}
                    placeholder="Summary of modules, architecture and deliverables..."
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Target Completion Date</label>
                  <input
                    type="date"
                    className="form-input"
                    value={editDeliveryDate}
                    onChange={(e) => setEditDeliveryDate(e.target.value)}
                  />
                </div>

                {/* Functional Specs Checklist */}
                <div style={{ marginBottom: '16px' }}>
                  <label className="form-label">Functional Specifications</label>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Add functional feature spec..."
                      value={newSpec}
                      onChange={(e) => setNewSpec(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (newSpec.trim()) {
                          setSpecsList([...specsList, newSpec.trim()]);
                          setNewSpec('');
                        }
                      }}
                      className="btn btn-secondary btn-sm"
                    >
                      <Plus size={14} /> Add
                    </button>
                  </div>
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {specsList.map((s, idx) => (
                      <li key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 12px', background: '#f8fafc', borderRadius: '6px', fontSize: '0.84rem' }}>
                        <span>• {s}</span>
                        <button
                          type="button"
                          onClick={() => setSpecsList(specsList.filter((_, i) => i !== idx))}
                          style={{ color: '#ef4444', border: 0, background: 'none', cursor: 'pointer' }}
                        >
                          ✕
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Deliverables Checklist */}
                <div style={{ marginBottom: '16px' }}>
                  <label className="form-label">Engineering Deliverables Checklist</label>
                  <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Add milestone / deliverable (e.g. GitHub Repository, Docker setup)..."
                      value={newDeliverable}
                      onChange={(e) => setNewDeliverable(e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        if (newDeliverable.trim()) {
                          setDeliverablesList([...deliverablesList, newDeliverable.trim()]);
                          setNewDeliverable('');
                        }
                      }}
                      className="btn btn-secondary btn-sm"
                    >
                      <Plus size={14} /> Add
                    </button>
                  </div>
                  <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {deliverablesList.map((d, idx) => (
                      <li key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 12px', background: '#f8fafc', borderRadius: '6px', fontSize: '0.84rem' }}>
                        <span>✓ {d}</span>
                        <button
                          type="button"
                          onClick={() => setDeliverablesList(deliverablesList.filter((_, i) => i !== idx))}
                          style={{ color: '#ef4444', border: 0, background: 'none', cursor: 'pointer' }}
                        >
                          ✕
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Automated Readiness Checker */}
                <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <h4 style={{ fontSize: '0.88rem' }}>Automated Handover Readiness Validator</h4>
                    <button
                      type="button"
                      onClick={() => handleCheckReadiness(selectedReq.enquiry)}
                      className="btn btn-secondary btn-sm"
                      disabled={readinessLoading}
                    >
                      {readinessLoading ? 'Checking...' : 'Run Readiness Audit'}
                    </button>
                  </div>

                  {readinessData && (
                    <div style={{ background: '#f1f5f9', padding: '12px', borderRadius: '8px', fontSize: '0.82rem' }}>
                      <div style={{ fontWeight: 700, color: readinessData.is_ready ? '#059669' : '#b45309', marginBottom: '4px' }}>
                        Overall Readiness: {readinessData.is_ready ? 'READY FOR DEVELOPER HANDOVER' : 'INCOMPLETE REQUIREMENTS'}
                      </div>
                      <div>Scope Defined: {readinessData.has_scope ? '✅ Yes' : '❌ Missing'}</div>
                      <div>Functional Specs Count: {readinessData.specs_count ?? 0}</div>
                      <div>Brand Assets Uploaded: {readinessData.assets_count ?? 0}</div>
                    </div>
                  )}
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" onClick={() => setSelectedReq(null)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={saveLoading}>
                  <Save size={16} /> Save Workspace Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

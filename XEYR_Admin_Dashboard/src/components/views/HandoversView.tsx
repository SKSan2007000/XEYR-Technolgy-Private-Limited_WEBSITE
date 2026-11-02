import React, { useEffect, useState } from 'react';
import { HandoverRecord } from '../../types';
import { handoverApi } from '../../services/api';
import {
  PackageCheck,
  Download,
  ShieldCheck,
  RefreshCw,
  Plus,
  UserCheck,
  Clock,
  AlertTriangle
} from 'lucide-react';

interface HandoversViewProps {
  searchQuery?: string;
}

export const HandoversView: React.FC<HandoversViewProps> = ({ searchQuery = '' }) => {
  const [handovers, setHandovers] = useState<HandoverRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Generate modal
  const [generateModal, setGenerateModal] = useState(false);
  const [requirementId, setRequirementId] = useState<number>(1);
  const [instructions, setInstructions] = useState('');
  const [priority, setPriority] = useState('High');
  const [assignedDevId, setAssignedDevId] = useState<number>(2);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchHandovers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await handoverApi.getHandovers();
      setHandovers(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch handover records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHandovers();
  }, []);

  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await handoverApi.generate(requirementId, {
        handover_instructions: instructions,
        priority,
        assigned_developer_id: assignedDevId
      });
      alert('Developer Handover ZIP package generated successfully with SHA-256 manifest.');
      setGenerateModal(false);
      setInstructions('');
      await fetchHandovers();
    } catch (err: any) {
      alert('Generation error: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const filtered = handovers.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.handover_reference?.toLowerCase().includes(q) ||
      item.zip_filename?.toLowerCase().includes(q) ||
      item.zip_checksum_sha256?.toLowerCase().includes(q)
    );
  });

  const formatSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Developer Handover Packages (ZIP)</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Standardized, clean ZIP archives built from real requirement workspaces with cryptographic checksums.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setGenerateModal(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> Generate Handover ZIP
            </button>
            <button onClick={fetchHandovers} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading handover archives...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <PackageCheck size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Handover Packages Generated Yet</h3>
          <p style={{ fontSize: '0.85rem' }}>Select a qualified requirement workspace to build a verified developer archive.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Package Reference</th>
                <th>Archive Filename</th>
                <th>Package Size</th>
                <th>SHA-256 Checksum</th>
                <th>Readiness Checks</th>
                <th>Downloads</th>
                <th>Generated At</th>
                <th style={{ textAlign: 'right' }}>Download</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong style={{ color: '#1465f4' }}>{item.handover_reference}</strong>
                    <div style={{ fontSize: '0.74rem', color: '#64748b' }}>Version {item.version}</div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: '0.84rem' }}>{item.zip_filename}</div>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.84rem', fontWeight: 600 }}>{formatSize(item.zip_size)}</span>
                  </td>
                  <td>
                    <code style={{ fontSize: '0.74rem', background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', color: '#334155' }}>
                      {item.zip_checksum_sha256 ? `${item.zip_checksum_sha256.substring(0, 16)}...` : 'Verified'}
                    </code>
                  </td>
                  <td>
                    <span className={`badge ${item.all_checks_passed ? 'badge-qualified' : 'badge-pending'}`}>
                      {item.all_checks_passed ? 'All Checks Passed' : 'Conditional Audit'}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.84rem', fontWeight: 700 }}>{item.download_count ?? 0}</span>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.82rem' }}>
                      {new Date(item.generated_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <a
                      href={handoverApi.getDownloadUrl(item.id)}
                      className="btn btn-secondary btn-sm"
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Download clean verified ZIP"
                    >
                      <Download size={14} /> Download ZIP
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Generate Handover Modal */}
      {generateModal && (
        <div className="modal-overlay" onClick={() => setGenerateModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">ENGINEERING ARCHIVE</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>Generate Clean Handover ZIP</h3>
              </div>
              <button onClick={() => setGenerateModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleGenerateSubmit}>
              <div className="modal-body">
                <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '12px', fontSize: '0.82rem', color: '#1e40af', marginBottom: '16px' }}>
                  <ShieldCheck size={16} style={{ display: 'inline', verticalAlign: 'text-bottom', marginRight: '4px' }} />
                  <strong>Security Guardrail Active:</strong> Generated archives bundle functional specifications, brand assets, and manifest data. Proprietary secrets, <code>.env</code> files, passwords, database dumps, and private keys are strictly excluded.
                </div>

                <div className="form-group">
                  <label className="form-label">Requirement Workspace ID *</label>
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
                  <label className="form-label">Sprint Priority</label>
                  <select
                    className="form-select"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    <option value="High">High (Immediate Sprint Allocation)</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Assigned Developer User ID</label>
                  <input
                    type="number"
                    className="form-input"
                    value={assignedDevId}
                    onChange={(e) => setAssignedDevId(Number(e.target.value))}
                    required
                    min={1}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Developer Handover Instructions</label>
                  <textarea
                    className="form-textarea"
                    rows={3}
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    placeholder="Provide architecture instructions, repo scaffolding rules, or milestone targets..."
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setGenerateModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={actionLoading}>
                  <PackageCheck size={16} /> Generate &amp; Compute SHA-256
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

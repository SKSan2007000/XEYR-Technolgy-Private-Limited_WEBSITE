import React, { useEffect, useState } from 'react';
import { DeveloperProject } from '../../types';
import { projectsApi } from '../../services/api';
import {
  Briefcase,
  CheckSquare,
  Square,
  AlertTriangle,
  RefreshCw,
  Plus,
  Calendar,
  Layers,
  FileCode
} from 'lucide-react';

interface ProjectsViewProps {
  searchQuery?: string;
}

export const ProjectsView: React.FC<ProjectsViewProps> = ({ searchQuery = '' }) => {
  const [projects, setProjects] = useState<DeveloperProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected project for milestones & progress
  const [selectedProject, setSelectedProject] = useState<DeveloperProject | null>(null);
  const [newMilestoneTitle, setNewMilestoneTitle] = useState('');
  const [newMilestoneDate, setNewMilestoneDate] = useState('');
  const [milestoneLoading, setMilestoneLoading] = useState(false);

  // Update status modal
  const [statusModal, setStatusModal] = useState<DeveloperProject | null>(null);
  const [newStatus, setNewStatus] = useState('IN_PROGRESS');
  const [newProgress, setNewProgress] = useState(0);
  const [blockerText, setBlockerText] = useState('');

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectsApi.getProjects();
      setProjects(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch developer projects.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleToggleMilestone = async (projectId: number, milestoneId: number, currentCompleted: boolean) => {
    try {
      await projectsApi.toggleMilestone(projectId, milestoneId, !currentCompleted);
      // Refresh project
      const updated = await projectsApi.getProject(projectId);
      setSelectedProject(updated);
      await fetchProjects();
    } catch (err: any) {
      alert('Toggle error: ' + err.message);
    }
  };

  const handleAddMilestone = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject || !newMilestoneTitle.trim()) return;
    setMilestoneLoading(true);
    try {
      await projectsApi.createMilestone(selectedProject.id, {
        title: newMilestoneTitle.trim(),
        due_date: newMilestoneDate || undefined
      });
      setNewMilestoneTitle('');
      setNewMilestoneDate('');
      const updated = await projectsApi.getProject(selectedProject.id);
      setSelectedProject(updated);
      await fetchProjects();
    } catch (err: any) {
      alert('Failed to add milestone: ' + err.message);
    } finally {
      setMilestoneLoading(false);
    }
  };

  const handleStatusSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!statusModal) return;
    try {
      await projectsApi.updateProject(statusModal.id, {
        status: newStatus,
        progress_percentage: Number(newProgress),
        blocker_description: newStatus === 'BLOCKED' ? blockerText : ''
      });
      setStatusModal(null);
      await fetchProjects();
    } catch (err: any) {
      alert('Update failed: ' + err.message);
    }
  };

  const filtered = projects.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.project_code?.toLowerCase().includes(q) ||
      item.title?.toLowerCase().includes(q) ||
      item.status?.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Developer Projects &amp; Sprints</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Milestones, deliverables, blocker management and sprint progress tracking.
            </p>
          </div>
          <button onClick={fetchProjects} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading project workflows...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <Briefcase size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Projects Created Yet</h3>
          <p style={{ fontSize: '0.85rem' }}>Developer projects are instantiated from approved requirements and handovers.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {filtered.map((proj) => (
            <div key={proj.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span className="badge badge-new">{proj.project_code}</span>
                  <span className={`badge ${proj.status === 'COMPLETED' ? 'badge-qualified' : proj.status === 'BLOCKED' ? 'badge-rejected' : 'badge-pending'}`}>
                    {proj.status.replace('_', ' ')}
                  </span>
                </div>

                <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '8px' }}>{proj.title}</h3>

                {proj.status === 'BLOCKED' && proj.blocker_description && (
                  <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '10px', marginBottom: '14px', fontSize: '0.82rem', color: '#991b1b', display: 'flex', gap: '8px' }}>
                    <AlertTriangle size={16} style={{ flexShrink: 0 }} />
                    <div>
                      <strong>Sprint Blocker:</strong> {proj.blocker_description}
                    </div>
                  </div>
                )}

                {/* Progress Bar */}
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: '6px' }}>
                    <span style={{ color: '#64748b' }}>Sprint Progress</span>
                    <strong style={{ color: '#1465f4' }}>{proj.progress_percentage}%</strong>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '99px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${proj.progress_percentage}%`,
                        height: '100%',
                        background: proj.progress_percentage === 100 ? '#10b981' : '#1465f4',
                        borderRadius: '99px',
                        transition: 'width 0.3s'
                      }}
                    />
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: '10px 12px', borderRadius: '8px', fontSize: '0.8rem', color: '#64748b', display: 'flex', justifyContent: 'space-between' }}>
                  <span>Priority: <strong style={{ color: '#0f172a' }}>{proj.priority}</strong></span>
                  <span>Target: <strong style={{ color: '#0f172a' }}>{proj.expected_completion_date || 'Open'}</strong></span>
                </div>
              </div>

              <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '14px', marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button
                  onClick={() => {
                    setSelectedProject(proj);
                  }}
                  className="btn btn-secondary btn-sm"
                >
                  <Layers size={14} /> Milestones ({proj.milestones?.length || 0})
                </button>
                <button
                  onClick={() => {
                    setStatusModal(proj);
                    setNewStatus(proj.status);
                    setNewProgress(proj.progress_percentage);
                    setBlockerText(proj.blocker_description || '');
                  }}
                  className="btn btn-primary btn-sm"
                >
                  Update Progress
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Milestones & Deliverables Modal */}
      {selectedProject && (
        <div className="modal-overlay" onClick={() => setSelectedProject(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(720px, 94vw)' }}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">{selectedProject.project_code}</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>Project Milestones &amp; Deliverables</h3>
              </div>
              <button onClick={() => setSelectedProject(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <div className="modal-body">
              {/* Add Milestone Form */}
              <form onSubmit={handleAddMilestone} style={{ display: 'grid', gridTemplateColumns: '1fr 140px auto', gap: '10px', marginBottom: '20px' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="New milestone title (e.g. Frontend Auth Integration)..."
                  value={newMilestoneTitle}
                  onChange={(e) => setNewMilestoneTitle(e.target.value)}
                  required
                />
                <input
                  type="date"
                  className="form-input"
                  value={newMilestoneDate}
                  onChange={(e) => setNewMilestoneDate(e.target.value)}
                />
                <button type="submit" className="btn btn-primary btn-sm" disabled={milestoneLoading}>
                  <Plus size={14} /> Add
                </button>
              </form>

              {/* Milestones List */}
              <h4 style={{ fontSize: '0.88rem', marginBottom: '10px' }}>Active Sprint Milestones</h4>
              {(!selectedProject.milestones || selectedProject.milestones.length === 0) ? (
                <p style={{ fontSize: '0.84rem', color: '#64748b' }}>No milestones recorded for this project yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' }}>
                  {selectedProject.milestones.map((m) => (
                    <div
                      key={m.id}
                      onClick={() => handleToggleMilestone(selectedProject.id, m.id, m.completed)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '12px 14px',
                        background: m.completed ? '#ecfdf5' : '#f8fafc',
                        border: `1px solid ${m.completed ? '#a7f3d0' : '#e2e8f0'}`,
                        borderRadius: '8px',
                        cursor: 'pointer'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {m.completed ? <CheckSquare size={18} color="#059669" /> : <Square size={18} color="#94a3b8" />}
                        <span style={{ fontSize: '0.88rem', fontWeight: 600, textDecoration: m.completed ? 'line-through' : 'none', color: m.completed ? '#065f46' : '#0f172a' }}>
                          {m.title}
                        </span>
                      </div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                        {m.due_date ? `Due: ${m.due_date}` : 'No deadline'}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Deliverables */}
              <h4 style={{ fontSize: '0.88rem', marginBottom: '10px' }}>Registered Deliverables</h4>
              {(!selectedProject.deliverables || selectedProject.deliverables.length === 0) ? (
                <p style={{ fontSize: '0.84rem', color: '#64748b' }}>No code repository or document deliverables uploaded yet.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {selectedProject.deliverables.map((d) => (
                    <div key={d.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <FileCode size={16} color="#1465f4" />
                        <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{d.title}</span>
                        <span className="badge badge-gray" style={{ fontSize: '0.7rem' }}>{d.deliverable_type}</span>
                      </div>
                      <span className="badge badge-qualified">{d.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button onClick={() => setSelectedProject(null)} className="btn btn-secondary">Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Update Status Modal */}
      {statusModal && (
        <div className="modal-overlay" onClick={() => setStatusModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="card-title">Update Project: {statusModal.project_code}</h3>
              <button onClick={() => setStatusModal(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleStatusSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Workflow Status</label>
                  <select
                    className="form-select"
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value)}
                  >
                    <option value="AWAITING_ASSIGNMENT">Awaiting Assignment</option>
                    <option value="ASSIGNED">Assigned</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="BLOCKED">Blocked</option>
                    <option value="INTERNAL_REVIEW">Internal Review</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="DELIVERED">Delivered to Client</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Progress Percentage: {newProgress}%</label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={newProgress}
                    onChange={(e) => setNewProgress(Number(e.target.value))}
                    style={{ width: '100%', cursor: 'pointer' }}
                  />
                </div>

                {newStatus === 'BLOCKED' && (
                  <div className="form-group">
                    <label className="form-label">Blocker Description *</label>
                    <textarea
                      className="form-textarea"
                      rows={3}
                      value={blockerText}
                      onChange={(e) => setBlockerText(e.target.value)}
                      placeholder="Explain what is blocking progress (API credentials, client feedback, infra)..."
                      required
                    />
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setStatusModal(null)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary">Save Progress</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

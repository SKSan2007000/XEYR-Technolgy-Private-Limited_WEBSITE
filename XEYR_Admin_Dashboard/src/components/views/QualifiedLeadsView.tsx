import React, { useEffect, useState } from 'react';
import { Enquiry } from '../../types';
import { crmApi } from '../../services/api';
import { ActiveTab } from '../layout/Sidebar';
import { UserCheck, ArrowRight, Phone, Mail, Building, RefreshCw, FileText } from 'lucide-react';

interface QualifiedLeadsViewProps {
  searchQuery?: string;
  setActiveTab: (tab: ActiveTab) => void;
}

export const QualifiedLeadsView: React.FC<QualifiedLeadsViewProps> = ({ searchQuery = '', setActiveTab }) => {
  const [leads, setLeads] = useState<Enquiry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQualifiedLeads = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await crmApi.getEnquiries('QUALIFIED');
      setLeads(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch qualified leads.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQualifiedLeads();
  }, []);

  const filtered = leads.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.reference_id?.toLowerCase().includes(q) ||
      item.client_name?.toLowerCase().includes(q) ||
      item.project_title?.toLowerCase().includes(q)
    );
  });

  const totalPipeline = filtered.reduce((acc, curr) => {
    const val = Number(curr.qualification?.estimated_project_value || 0);
    return acc + val;
  }, 0);

  return (
    <div>
      {/* Metrics Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="card" style={{ background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 100%)', borderColor: '#bfdbfe' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1e40af', textTransform: 'uppercase' }}>
            Total Qualified Leads
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#1e3a8a', marginTop: '6px' }}>
            {filtered.length}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>
            Ready for technical requirements definition
          </div>
        </div>

        <div className="card" style={{ background: 'linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%)', borderColor: '#a7f3d0' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#065f46', textTransform: 'uppercase' }}>
            Qualified Pipeline Value
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#047857', marginTop: '6px' }}>
            ₹{totalPipeline.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: '4px' }}>
            Verified client budget allocations
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading qualified leads from PostgreSQL...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <UserCheck size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Qualified Leads Yet</h3>
          <p style={{ fontSize: '0.85rem' }}>Review new submissions in Enquiries &amp; CRM to qualify prospects.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {filtered.map((lead) => {
            const q = lead.qualification;
            return (
              <div key={lead.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                    <span className="badge badge-qualified">QUALIFIED LEAD</span>
                    <span style={{ fontSize: '0.76rem', color: '#64748b' }}>
                      Ref: <strong style={{ color: '#1465f4' }}>{lead.reference_id}</strong>
                    </span>
                  </div>

                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '6px' }}>
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

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', marginBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.82rem' }}>
                      <span style={{ color: '#64748b' }}>Estimated Contract:</span>
                      <strong style={{ color: '#059669', fontSize: '0.95rem' }}>
                        ₹{Number(q?.estimated_project_value || 0).toLocaleString('en-IN')}
                      </strong>
                    </div>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: '#475569' }}>
                      <span>Budget: {q?.budget_confirmed ? '✅ Confirmed' : '⚠️ Pending'}</span>
                      <span>Timeline: {q?.timeline_confirmed ? '✅ Agreed' : '⚠️ Pending'}</span>
                    </div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                    Service: <strong>{lead.service_type}</strong>
                  </span>
                  <button
                    onClick={() => setActiveTab('requirements')}
                    className="btn btn-primary btn-sm"
                  >
                    Open Workspace <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

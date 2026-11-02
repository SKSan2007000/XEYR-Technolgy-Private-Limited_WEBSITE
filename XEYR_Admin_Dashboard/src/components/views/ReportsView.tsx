import React from 'react';
import { analyticsApi } from '../../services/api';
import { FileBarChart, Download, ShieldCheck, FileSpreadsheet, Calendar } from 'lucide-react';

interface ReportsViewProps {
  period: string;
}

export const ReportsView: React.FC<ReportsViewProps> = ({ period }) => {
  const reports = [
    {
      id: 'enquiries',
      title: 'CRM Enquiries & Lead Pipeline Report',
      description: 'Comprehensive extract of all client submissions, qualification decisions, budget brackets and status history.',
      format: 'CSV (UTF-8)',
      frequency: 'Real-time On-demand'
    },
    {
      id: 'financials',
      title: 'Finance & Invoicing Audit Report',
      description: 'Ledger report distinguishing amount quoted, amount invoiced, payment receipts, UTR numbers and pending collections.',
      format: 'CSV (UTF-8)',
      frequency: 'Reconciled Daily'
    },
    {
      id: 'handovers',
      title: 'Developer Handover & Checksum Manifest Export',
      description: 'Verification logs of all engineering ZIP archives with SHA-256 hashes, developer assignments and file sizes.',
      format: 'CSV (UTF-8)',
      frequency: 'Audit Sealed'
    },
    {
      id: 'events',
      title: 'Central Event & Workshop Registrations Extract',
      description: 'Participant attendance, dynamic form questionnaire responses, and Razorpay transaction order IDs.',
      format: 'CSV (UTF-8)',
      frequency: 'Event-driven'
    }
  ];

  return (
    <div>
      <div className="card" style={{ marginBottom: '24px', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <FileBarChart size={24} color="#1465f4" />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 800 }}>Verified Administrative Reports &amp; Exports</h3>
        </div>
        <p style={{ fontSize: '0.86rem', color: '#64748b', lineHeight: 1.5, maxWidth: '800px' }}>
          Generate cryptographically intact CSV data extracts directly from PostgreSQL. Export permissions are audited under corporate governance policies.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {reports.map((rep) => (
          <div key={rep.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <span className="badge badge-new">{rep.format}</span>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>{rep.frequency}</span>
              </div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a', marginBottom: '8px' }}>
                {rep.title}
              </h4>
              <p style={{ fontSize: '0.84rem', color: '#64748b', lineHeight: 1.45 }}>
                {rep.description}
              </p>
            </div>

            <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.78rem', color: '#94a3b8' }}>
                Window: <strong>{period.replace('_', ' ')}</strong>
              </span>
              <a
                href={analyticsApi.getExportUrl(rep.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-primary btn-sm"
              >
                <Download size={14} /> Download CSV
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

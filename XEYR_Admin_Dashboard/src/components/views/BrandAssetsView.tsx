import React, { useEffect, useState } from 'react';
import { ClientBrandAsset } from '../../types';
import { assetsApi } from '../../services/api';
import {
  Palette,
  Upload,
  Download,
  FileCheck,
  RefreshCw,
  File,
  ShieldCheck,
  Plus
} from 'lucide-react';

interface BrandAssetsViewProps {
  searchQuery?: string;
}

export const BrandAssetsView: React.FC<BrandAssetsViewProps> = ({ searchQuery = '' }) => {
  const [assets, setAssets] = useState<ClientBrandAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Upload modal state
  const [uploadModal, setUploadModal] = useState(false);
  const [requirementId, setRequirementId] = useState<number>(1);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('PRIMARY_LOGO');
  const [file, setFile] = useState<File | null>(null);
  const [uploadLoading, setUploadLoading] = useState(false);

  const fetchAssets = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assetsApi.getAssets();
      setAssets(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch brand assets.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAssets();
  }, []);

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a file to upload.');
      return;
    }
    setUploadLoading(true);
    try {
      const formData = new FormData();
      formData.append('requirement_id', String(requirementId));
      formData.append('title', title.trim());
      formData.append('category', category);
      formData.append('file', file);

      await assetsApi.upload(formData);
      alert('Brand asset uploaded and cryptographic SHA-256 checksum recorded.');
      setUploadModal(false);
      setTitle('');
      setFile(null);
      await fetchAssets();
    } catch (err: any) {
      alert('Upload failed: ' + err.message);
    } finally {
      setUploadLoading(false);
    }
  };

  const filtered = assets.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title?.toLowerCase().includes(q) ||
      item.category?.toLowerCase().includes(q) ||
      item.filename?.toLowerCase().includes(q) ||
      item.checksum_sha256?.toLowerCase().includes(q)
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
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Client Brand Assets &amp; Specifications</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Cryptographically verified brand logos, typography, vector assets, and design files.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setUploadModal(true)} className="btn btn-primary btn-sm">
              <Plus size={14} /> Upload Brand Asset
            </button>
            <button onClick={fetchAssets} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading asset repository...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <Palette size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Brand Assets Uploaded Yet</h3>
          <p style={{ fontSize: '0.85rem' }}>Upload logos, brand guidelines, or wireframes for engineering handovers.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Asset Title &amp; Category</th>
                <th>File Name &amp; Type</th>
                <th>File Size</th>
                <th>SHA-256 Checksum</th>
                <th>Version</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Download</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{item.title}</div>
                    <span className="badge badge-new" style={{ marginTop: '3px' }}>
                      {item.category.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <File size={14} color="#64748b" />
                      <span style={{ fontSize: '0.84rem' }}>{item.filename || 'File Attachment'}</span>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.84rem', fontWeight: 600 }}>{formatSize(item.file_size)}</span>
                  </td>
                  <td>
                    <code style={{ fontSize: '0.74rem', background: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', color: '#334155' }}>
                      {item.checksum_sha256 ? `${item.checksum_sha256.substring(0, 16)}...` : 'Pre-computed'}
                    </code>
                  </td>
                  <td>
                    <span className="badge badge-gray">V{item.version}</span>
                  </td>
                  <td>
                    <span className="badge badge-qualified">{item.status}</span>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <a
                      href={assetsApi.getDownloadUrl(item.id)}
                      className="btn btn-secondary btn-sm"
                      target="_blank"
                      rel="noopener noreferrer"
                      title="Download with cryptographic verification"
                    >
                      <Download size={14} /> Download
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Upload Asset Modal */}
      {uploadModal && (
        <div className="modal-overlay" onClick={() => setUploadModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">ASSET INGESTION</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>Upload Verified Brand Asset</h3>
              </div>
              <button onClick={() => setUploadModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleUploadSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label className="form-label">Requirement ID</label>
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
                  <label className="form-label">Asset Title *</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Primary High-Res Transparent Logo"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Asset Category</label>
                  <select
                    className="form-select"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                  >
                    <option value="PRIMARY_LOGO">Primary Brand Logo</option>
                    <option value="SECONDARY_LOGO">Secondary Logo / Wordmark</option>
                    <option value="BRAND_ICON">Brand Icon / Favicon</option>
                    <option value="COLOR_PALETTE">Brand Colour Palette</option>
                    <option value="TYPOGRAPHY">Typography / Font Reference</option>
                    <option value="GUIDELINES_PDF">Brand Guidelines PDF</option>
                    <option value="UI_SCREENSHOT">UI Reference Screenshots</option>
                    <option value="WIREFRAME">Wireframes / Design Files</option>
                    <option value="TECHNICAL_SPEC">Technical Specification / API Doc</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Select File *</label>
                  <input
                    type="file"
                    className="form-input"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setUploadModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary" disabled={uploadLoading}>
                  <Upload size={16} /> Upload &amp; Compute Checksum
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

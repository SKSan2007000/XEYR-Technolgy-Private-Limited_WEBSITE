import React, { useEffect, useState } from 'react';
import { SocialMediaConfig } from '../../types';
import { socialApi } from '../../services/api';
import { QrCode, Upload, Save, RefreshCw, CheckCircle, ExternalLink } from 'lucide-react';

export const SocialMediaView: React.FC = () => {
  const [configs, setConfigs] = useState<SocialMediaConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingKey, setSavingKey] = useState<string | null>(null);

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await socialApi.getConfig();
      setConfigs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch social media configs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSavePlatform = async (platformKey: string, platformName: string) => {
    setSavingKey(platformKey);
    const urlInput = document.getElementById(`url-${platformKey}`) as HTMLInputElement;
    const publicInput = document.getElementById(`public-${platformKey}`) as HTMLInputElement;
    const fileInput = document.getElementById(`file-${platformKey}`) as HTMLInputElement;

    try {
      const formData = new FormData();
      formData.append('platform_key', platformKey);
      formData.append('platform_name', platformName);
      formData.append('platform_url', urlInput?.value || '');
      formData.append('is_public', String(publicInput?.checked ?? true));
      if (fileInput?.files?.[0]) {
        formData.append('qr_code_image', fileInput.files[0]);
      }

      await socialApi.saveConfig(formData);
      alert(`Social settings for ${platformName} updated successfully.`);
      await fetchConfig();
    } catch (err: any) {
      alert('Save failed: ' + err.message);
    } finally {
      setSavingKey(null);
    }
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Official Social Media &amp; Genuine QR Code Assets</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Manage social destinations and upload legitimate QR codes for public footer interaction.
            </p>
          </div>
          <button onClick={fetchConfig} className="btn btn-secondary btn-sm">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading social assets...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {configs.map((c) => (
            <div key={c.platform_key} className="card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h4 style={{ fontSize: '1.05rem', fontWeight: 800 }}>{c.platform_name}</h4>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    id={`public-${c.platform_key}`}
                    defaultChecked={c.is_public}
                  />
                  Show in Public Footer
                </label>
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Official Page URL</label>
                <input
                  type="url"
                  id={`url-${c.platform_key}`}
                  className="form-input"
                  defaultValue={c.platform_url || ''}
                  placeholder={`https://${c.platform_key.toLowerCase()}.com/xeyrtechnologies`}
                />
              </div>

              <div className="form-group" style={{ margin: 0 }}>
                <label className="form-label">Upload Genuine QR Code (PNG / JPG / SVG)</label>
                <input
                  type="file"
                  id={`file-${c.platform_key}`}
                  className="form-input"
                  accept="image/*"
                />
              </div>

              {/* QR Preview */}
              <div style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                padding: '16px',
                textAlign: 'center',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px'
              }}>
                <small style={{ color: '#64748b' }}>Active QR Graphic Preview</small>
                {c.qr_code_image ? (
                  <img
                    src={c.qr_code_image.startsWith('http') ? c.qr_code_image : `http://127.0.0.1:8000${c.qr_code_image}`}
                    alt={`${c.platform_name} QR`}
                    style={{ width: '130px', height: '130px', objectFit: 'contain', background: '#ffffff', padding: '6px', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                  />
                ) : (
                  <div style={{
                    width: '130px',
                    height: '130px',
                    background: '#ffffff',
                    border: '1px dashed #cbd5e1',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#94a3b8',
                    fontSize: '0.78rem'
                  }}>
                    No QR Uploaded
                  </div>
                )}
              </div>

              <button
                onClick={() => handleSavePlatform(c.platform_key, c.platform_name)}
                className="btn btn-primary"
                disabled={savingKey === c.platform_key}
                style={{ width: '100%', justifyContent: 'center' }}
              >
                {savingKey === c.platform_key ? 'Saving...' : 'Save & Publish to Footer'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

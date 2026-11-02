import React, { useState, useEffect } from 'react';
import { CertificateTemplate } from '../../types';
import { certificateTemplatesApi } from '../../services/api';
import {
  Award,
  Plus,
  Copy,
  Archive,
  Eye,
  Save,
  CheckCircle,
  AlertCircle,
  Layout,
  Type,
  Palette,
  ShieldCheck,
  QrCode,
  FileText,
  RotateCcw,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Maximize2
} from 'lucide-react';

export const CertificateDesignerView: React.FC = () => {
  const [templates, setTemplates] = useState<CertificateTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Active Template State
  const [activeTemplate, setActiveTemplate] = useState<CertificateTemplate | null>(null);
  const [editorTab, setEditorTab] = useState<'content' | 'layout' | 'styling' | 'branding'>('content');
  const [isSaving, setIsSaving] = useState(false);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);

  // Live Editable Form Fields
  const [name, setName] = useState('');
  const [status, setStatus] = useState<'DRAFT' | 'PUBLISHED' | 'ARCHIVED'>('PUBLISHED');
  const [orientation, setOrientation] = useState<'LANDSCAPE' | 'PORTRAIT'>('LANDSCAPE');
  const [bgType, setBgType] = useState<'COLOR' | 'GRADIENT' | 'IMAGE'>('COLOR');
  const [bgColor, setBgColor] = useState('#ffffff');
  const [bgGradient, setBgGradient] = useState('linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%)');
  const [bgImageUrl, setBgImageUrl] = useState('');
  const [borderStyle, setBorderStyle] = useState<'classic_gold' | 'modern_blue' | 'double_line' | 'ornamental' | 'minimal_clean' | 'none'>('modern_blue');
  const [borderColor, setBorderColor] = useState('#1465f4');
  const [borderWidth, setBorderWidth] = useState(8);
  const [title, setTitle] = useState('CERTIFICATE OF ACHIEVEMENT');
  const [subtitle, setSubtitle] = useState('PROUDLY PRESENTED TO');
  const [descriptionTemplate, setDescriptionTemplate] = useState(
    'For successfully participating in and completing {{event_name}} organized by {{organizer_name}} on {{issue_date}}.'
  );
  const [logoUrl, setLogoUrl] = useState('/assets/xeyr-symbol.png');
  const [signatoryName, setSignatoryName] = useState('B. Santhosh Kumar');
  const [signatoryTitle, setSignatoryTitle] = useState('Managing Director, XEYR Technologies');
  const [signatureUrl, setSignatureUrl] = useState('');
  const [organizerName, setOrganizerName] = useState('XEYR Technologies Private Limited');
  const [showQrCode, setShowQrCode] = useState(true);

  // Mock Participant for Live Preview
  const mockParticipant = 'Alex Mercer';
  const mockEvent = 'Full-Stack Cloud & AI Engineering Summit';
  const mockDate = 'October 28, 2026';
  const mockCertId = 'XEYR-CERT-2026-98421';

  const fetchTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await certificateTemplatesApi.getTemplates();
      setTemplates(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data.length > 0 && !activeTemplate) {
        selectTemplate(data[0]);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load certificate templates from backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  const selectTemplate = (t: CertificateTemplate) => {
    setActiveTemplate(t);
    setName(t.name);
    setStatus(t.status);
    setOrientation(t.orientation);
    setBgType(t.background_type);
    setBgColor(t.background_color);
    setBgGradient(t.background_gradient || 'linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%)');
    setBgImageUrl(t.background_image_url || '');
    setBorderStyle(t.border_style);
    setBorderColor(t.border_color);
    setBorderWidth(t.border_width);
    setTitle(t.title);
    setSubtitle(t.subtitle);
    setDescriptionTemplate(t.description_template);
    setLogoUrl(t.logo_url);
    setSignatoryName(t.signatory_name);
    setSignatoryTitle(t.signatory_title);
    setSignatureUrl(t.signature_url || '');
    setOrganizerName(t.organizer_name);
    setShowQrCode(t.show_qr_code);
  };

  const handleCreateNew = () => {
    const newDraft: Partial<CertificateTemplate> = {
      name: 'Custom Event Certificate',
      slug: `custom-event-cert-${Date.now()}`,
      status: 'DRAFT',
      orientation: 'LANDSCAPE',
      width: 1120,
      height: 792,
      background_type: 'COLOR',
      background_color: '#ffffff',
      background_gradient: '',
      border_style: 'modern_blue',
      border_color: '#1465f4',
      border_width: 8,
      title: 'CERTIFICATE OF EXCELLENCE',
      subtitle: 'PROUDLY PRESENTED TO',
      description_template: 'For outstanding technical proficiency and successful completion of {{event_name}} organized by {{organizer_name}} on {{issue_date}}.',
      logo_url: '/assets/xeyr-symbol.png',
      signatory_name: 'Authorized Signatory',
      signatory_title: 'Director, XEYR Technologies',
      organizer_name: 'XEYR Technologies Private Limited',
      show_qr_code: true,
      is_default: false,
    };
    setActiveTemplate(newDraft as CertificateTemplate);
    setName(newDraft.name!);
    setStatus('DRAFT');
    setOrientation('LANDSCAPE');
    setBgType('COLOR');
    setBgColor('#ffffff');
    setBorderStyle('modern_blue');
    setBorderColor('#1465f4');
    setBorderWidth(8);
    setTitle(newDraft.title!);
    setSubtitle(newDraft.subtitle!);
    setDescriptionTemplate(newDraft.description_template!);
    setLogoUrl(newDraft.logo_url!);
    setSignatoryName(newDraft.signatory_name!);
    setSignatoryTitle(newDraft.signatory_title!);
    setSignatureUrl('');
    setOrganizerName(newDraft.organizer_name!);
    setShowQrCode(true);
  };

  const handleSave = async (forceStatus?: 'DRAFT' | 'PUBLISHED') => {
    setIsSaving(true);
    setError(null);
    setSuccessMsg(null);

    const payload = {
      name,
      status: forceStatus || status,
      orientation,
      width: orientation === 'PORTRAIT' ? 792 : 1120,
      height: orientation === 'PORTRAIT' ? 1120 : 792,
      background_type: bgType,
      background_color: bgColor,
      background_gradient: bgGradient,
      background_image_url: bgImageUrl,
      border_style: borderStyle,
      border_color: borderColor,
      border_width: borderWidth,
      title,
      subtitle,
      description_template: descriptionTemplate,
      logo_url: logoUrl,
      signatory_name: signatoryName,
      signatory_title: signatoryTitle,
      signature_url: signatureUrl,
      organizer_name: organizerName,
      show_qr_code: showQrCode,
    };

    try {
      let saved: CertificateTemplate;
      if (activeTemplate && activeTemplate.id) {
        saved = await certificateTemplatesApi.updateTemplate(activeTemplate.id, payload);
      } else {
        saved = await certificateTemplatesApi.createTemplate(payload);
      }
      setSuccessMsg(`Template "${saved.name}" saved successfully!`);
      await fetchTemplates();
      selectTemplate(saved);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to save certificate template.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDuplicate = async () => {
    if (!activeTemplate || !activeTemplate.id) return;
    setIsSaving(true);
    try {
      const cloned = await certificateTemplatesApi.duplicateTemplate(activeTemplate.id);
      setSuccessMsg(`Duplicated template "${cloned.name}" as Draft.`);
      await fetchTemplates();
      selectTemplate(cloned);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to duplicate template.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!activeTemplate || !activeTemplate.id) return;
    if (activeTemplate.is_default) {
      alert('System default templates cannot be archived.');
      return;
    }
    if (!confirm(`Are you sure you want to archive "${activeTemplate.name}"?`)) return;

    try {
      await certificateTemplatesApi.deleteTemplate(activeTemplate.id);
      setSuccessMsg(`Template "${activeTemplate.name}" archived.`);
      await fetchTemplates();
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err: any) {
      setError(err.message || 'Failed to archive template.');
    }
  };

  const insertPlaceholder = (token: string) => {
    setDescriptionTemplate(prev => prev + ` ${token}`);
  };

  // Replace placeholders for live WYSIWYG preview
  const previewDescription = descriptionTemplate
    .replace(/\{\{participant_name\}\}/g, mockParticipant)
    .replace(/\{\{event_name\}\}/g, mockEvent)
    .replace(/\{\{event_title\}\}/g, mockEvent)
    .replace(/\{\{issue_date\}\}/g, mockDate)
    .replace(/\{\{event_date\}\}/g, mockDate)
    .replace(/\{\{certificate_id\}\}/g, mockCertId)
    .replace(/\{\{organizer_name\}\}/g, organizerName);

  return (
    <div className="view-container animate-fade-in" style={{ padding: '24px 28px', maxWidth: 1600, margin: '0 auto' }}>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'linear-gradient(135deg, #1465f4 0%, #27d4f4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}>
              <Award size={22} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.45rem', fontWeight: 700, margin: 0, color: '#07132e' }}>
                Certificate Template Designer
              </h1>
              <p style={{ fontSize: '0.86rem', color: '#64748b', margin: '2px 0 0 0' }}>
                Design, preview and customize digital certificates for workshops & events with dynamic placeholders.
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={handleCreateNew}
            className="button"
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#f1f5f9', color: '#07132e', border: '1px solid #cbd5e1', padding: '9px 14px', borderRadius: 8, fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            <Plus size={16} /> New Template
          </button>
          {activeTemplate?.id && (
            <button
              onClick={handleDuplicate}
              className="button"
              style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#f8fafc', color: '#334155', border: '1px solid #e2e8f0', padding: '9px 14px', borderRadius: 8, fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
            >
              <Copy size={16} /> Duplicate
            </button>
          )}
          {activeTemplate?.id && !activeTemplate.is_default && (
            <button
              onClick={handleArchive}
              className="button"
              style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#fff1f2', color: '#e11d48', border: '1px solid #fecdd3', padding: '9px 14px', borderRadius: 8, fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
            >
              <Archive size={16} /> Archive
            </button>
          )}
          <button
            onClick={() => setPreviewModalOpen(true)}
            className="button"
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#eff6ff', color: '#1465f4', border: '1px solid #bfdbfe', padding: '9px 14px', borderRadius: 8, fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            <Eye size={16} /> Full Render Test
          </button>
          <button
            onClick={() => handleSave('PUBLISHED')}
            disabled={isSaving}
            className="button button-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#1465f4', color: '#ffffff', border: 'none', padding: '9px 18px', borderRadius: 8, fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            <Save size={16} /> {isSaving ? 'Saving...' : 'Publish Template'}
          </button>
        </div>
      </div>

      {/* Alert Banners */}
      {error && (
        <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#991b1b', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
          <AlertCircle size={18} /> <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div style={{ padding: '12px 16px', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 8, color: '#065f46', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
          <CheckCircle size={18} /> <span>{successMsg}</span>
        </div>
      )}

      {/* Main Designer Grid (Templates Drawer + Controls Sidebar + WYSIWYG Canvas) */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 380px 1fr', gap: 20, alignItems: 'start' }}>
        
        {/* Left Column: Template Library */}
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 16, boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Template Library ({templates.length})
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 'calc(100vh - 280px)', overflowY: 'auto' }}>
            {templates.map(t => {
              const isSelected = activeTemplate?.id === t.id;
              return (
                <div
                  key={t.id}
                  onClick={() => selectTemplate(t)}
                  style={{
                    padding: '12px 14px',
                    borderRadius: 8,
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(20, 101, 244, 0.08)' : '#f8fafc',
                    border: isSelected ? '1.5px solid #1465f4' : '1px solid #e2e8f0',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <strong style={{ fontSize: '0.9rem', color: isSelected ? '#1465f4' : '#07132e' }}>
                      {t.name}
                    </strong>
                    {t.is_default && (
                      <span style={{ fontSize: '0.68rem', background: '#dbeafe', color: '#1e40af', padding: '2px 6px', borderRadius: 4, fontWeight: 700 }}>
                        DEFAULT
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.74rem', color: '#64748b' }}>
                    <span>{t.orientation}</span>
                    <span>•</span>
                    <span style={{
                      color: t.status === 'PUBLISHED' ? '#10b981' : t.status === 'DRAFT' ? '#f59e0b' : '#94a3b8',
                      fontWeight: 600
                    }}>
                      {t.status}
                    </span>
                    {t.assigned_events_count !== undefined && t.assigned_events_count > 0 && (
                      <>
                        <span>•</span>
                        <span>{t.assigned_events_count} events</span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Center Column: Visual Editor Controls */}
        <div style={{ background: '#ffffff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 20, boxShadow: '0 1px 3px rgba(0,0,0,0.05)', maxHeight: 'calc(100vh - 200px)', overflowY: 'auto' }}>
          {/* Editor Sub-tabs */}
          <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', marginBottom: 18, gap: 12 }}>
            <button
              onClick={() => setEditorTab('content')}
              style={{
                background: 'none',
                border: 'none',
                padding: '8px 4px',
                fontSize: '0.85rem',
                fontWeight: editorTab === 'content' ? 700 : 500,
                color: editorTab === 'content' ? '#1465f4' : '#64748b',
                borderBottom: editorTab === 'content' ? '2px solid #1465f4' : '2px solid transparent',
                cursor: 'pointer'
              }}
            >
              Content & Text
            </button>
            <button
              onClick={() => setEditorTab('styling')}
              style={{
                background: 'none',
                border: 'none',
                padding: '8px 4px',
                fontSize: '0.85rem',
                fontWeight: editorTab === 'styling' ? 700 : 500,
                color: editorTab === 'styling' ? '#1465f4' : '#64748b',
                borderBottom: editorTab === 'styling' ? '2px solid #1465f4' : '2px solid transparent',
                cursor: 'pointer'
              }}
            >
              Border & Colors
            </button>
            <button
              onClick={() => setEditorTab('branding')}
              style={{
                background: 'none',
                border: 'none',
                padding: '8px 4px',
                fontSize: '0.85rem',
                fontWeight: editorTab === 'branding' ? 700 : 500,
                color: editorTab === 'branding' ? '#1465f4' : '#64748b',
                borderBottom: editorTab === 'branding' ? '2px solid #1465f4' : '2px solid transparent',
                cursor: 'pointer'
              }}
            >
              Signatory & Logo
            </button>
            <button
              onClick={() => setEditorTab('layout')}
              style={{
                background: 'none',
                border: 'none',
                padding: '8px 4px',
                fontSize: '0.85rem',
                fontWeight: editorTab === 'layout' ? 700 : 500,
                color: editorTab === 'layout' ? '#1465f4' : '#64748b',
                borderBottom: editorTab === 'layout' ? '2px solid #1465f4' : '2px solid transparent',
                cursor: 'pointer'
              }}
            >
              Page Format
            </button>
          </div>

          {/* TAB 1: Content & Placeholders */}
          {editorTab === 'content' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Template Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Certificate Title
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                  placeholder="e.g. CERTIFICATE OF ACHIEVEMENT"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Subtitle
                </label>
                <input
                  type="text"
                  value={subtitle}
                  onChange={e => setSubtitle(e.target.value)}
                  placeholder="e.g. PROUDLY PRESENTED TO"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <label style={{ fontSize: '0.78rem', fontWeight: 600, color: '#334155' }}>
                    Description Template & Dynamic Placeholders
                  </label>
                </div>
                
                {/* Placeholder chips */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                  {['{{participant_name}}', '{{event_title}}', '{{event_name}}', '{{event_date}}', '{{issue_date}}', '{{certificate_id}}', '{{organizer_name}}'].map(token => (
                    <button
                      key={token}
                      type="button"
                      onClick={() => insertPlaceholder(token)}
                      style={{
                        background: '#eff6ff',
                        color: '#1d4ed8',
                        border: '1px solid #bfdbfe',
                        borderRadius: 4,
                        padding: '3px 8px',
                        fontSize: '0.74rem',
                        cursor: 'pointer',
                        fontFamily: 'monospace'
                      }}
                      title="Click to insert into description"
                    >
                      + {token}
                    </button>
                  ))}
                </div>

                <textarea
                  rows={4}
                  value={descriptionTemplate}
                  onChange={e => setDescriptionTemplate(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.85rem', fontFamily: 'inherit', lineHeight: 1.5 }}
                />
                <span style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4, display: 'block' }}>
                  Placeholders will be safely substituted with validated data from the event and participant registration.
                </span>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Publication Status
                </label>
                <select
                  value={status}
                  onChange={e => setStatus(e.target.value as any)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem', background: '#fff' }}
                >
                  <option value="PUBLISHED">Published (Available for Event Assignment)</option>
                  <option value="DRAFT">Draft (Under Review)</option>
                  <option value="ARCHIVED">Archived</option>
                </select>
              </div>
            </div>
          )}

          {/* TAB 2: Borders & Colors */}
          {editorTab === 'styling' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Border Style
                </label>
                <select
                  value={borderStyle}
                  onChange={e => setBorderStyle(e.target.value as any)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem', background: '#fff' }}
                >
                  <option value="modern_blue">Modern Blue & Cyan Corners</option>
                  <option value="classic_gold">Classic Gold & Filigree Ornaments</option>
                  <option value="double_line">Clean Double Line</option>
                  <option value="minimal_clean">Minimal Single Line</option>
                  <option value="none">No Border (Full Bleed)</option>
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                    Border Accent Color
                  </label>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="color"
                      value={borderColor}
                      onChange={e => setBorderColor(e.target.value)}
                      style={{ width: 36, height: 36, borderRadius: 6, border: 'none', cursor: 'pointer' }}
                    />
                    <input
                      type="text"
                      value={borderColor}
                      onChange={e => setBorderColor(e.target.value)}
                      style={{ flex: 1, padding: '7px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.82rem', fontFamily: 'monospace' }}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                    Border Thickness ({borderWidth}px)
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="20"
                    value={borderWidth}
                    onChange={e => setBorderWidth(parseInt(e.target.value))}
                    style={{ width: '100%', marginTop: 8 }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Background Style
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 8 }}>
                  {(['COLOR', 'GRADIENT', 'IMAGE'] as const).map(type => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setBgType(type)}
                      style={{
                        padding: '6px 10px',
                        borderRadius: 6,
                        border: bgType === type ? '1.5px solid #1465f4' : '1px solid #cbd5e1',
                        background: bgType === type ? '#eff6ff' : '#ffffff',
                        color: bgType === type ? '#1465f4' : '#475569',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {type}
                    </button>
                  ))}
                </div>

                {bgType === 'COLOR' && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <input
                      type="color"
                      value={bgColor}
                      onChange={e => setBgColor(e.target.value)}
                      style={{ width: 36, height: 36, borderRadius: 6, border: 'none', cursor: 'pointer' }}
                    />
                    <input
                      type="text"
                      value={bgColor}
                      onChange={e => setBgColor(e.target.value)}
                      placeholder="#ffffff"
                      style={{ flex: 1, padding: '7px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.82rem', fontFamily: 'monospace' }}
                    />
                  </div>
                )}

                {bgType === 'GRADIENT' && (
                  <input
                    type="text"
                    value={bgGradient}
                    onChange={e => setBgGradient(e.target.value)}
                    placeholder="linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%)"
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.82rem', fontFamily: 'monospace' }}
                  />
                )}

                {bgType === 'IMAGE' && (
                  <input
                    type="text"
                    value={bgImageUrl}
                    onChange={e => setBgImageUrl(e.target.value)}
                    placeholder="https://example.com/certificate-bg.png"
                    style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.82rem' }}
                  />
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Signatory & Branding */}
          {editorTab === 'branding' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Organizer / Company Name
                </label>
                <input
                  type="text"
                  value={organizerName}
                  onChange={e => setOrganizerName(e.target.value)}
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Company Logo URL
                </label>
                <input
                  type="text"
                  value={logoUrl}
                  onChange={e => setLogoUrl(e.target.value)}
                  placeholder="/assets/xeyr-symbol.png"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Authorized Signatory Name
                </label>
                <input
                  type="text"
                  value={signatoryName}
                  onChange={e => setSignatoryName(e.target.value)}
                  placeholder="e.g. B. Santhosh Kumar"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Authorized Signatory Designation
                </label>
                <input
                  type="text"
                  value={signatoryTitle}
                  onChange={e => setSignatoryTitle(e.target.value)}
                  placeholder="e.g. Managing Director, XEYR Technologies"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Signature Image URL (Optional)
                </label>
                <input
                  type="text"
                  value={signatureUrl}
                  onChange={e => setSignatureUrl(e.target.value)}
                  placeholder="Leave empty to use automatic script font"
                  style={{ width: '100%', padding: '8px 12px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0' }}>
                <input
                  type="checkbox"
                  id="show-qr"
                  checked={showQrCode}
                  onChange={e => setShowQrCode(e.target.checked)}
                  style={{ width: 18, height: 18, cursor: 'pointer' }}
                />
                <label htmlFor="show-qr" style={{ fontSize: '0.84rem', fontWeight: 600, color: '#07132e', cursor: 'pointer' }}>
                  Include Verification QR Code for Authenticity
                </label>
              </div>
            </div>
          )}

          {/* TAB 4: Page Format */}
          {editorTab === 'layout' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#334155', marginBottom: 4 }}>
                  Page Orientation (A4 Standard)
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <button
                    type="button"
                    onClick={() => setOrientation('LANDSCAPE')}
                    style={{
                      padding: '12px',
                      borderRadius: 8,
                      border: orientation === 'LANDSCAPE' ? '2px solid #1465f4' : '1px solid #cbd5e1',
                      background: orientation === 'LANDSCAPE' ? '#eff6ff' : '#ffffff',
                      color: orientation === 'LANDSCAPE' ? '#1465f4' : '#475569',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Landscape (A4)
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>1120 × 792 px</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setOrientation('PORTRAIT')}
                    style={{
                      padding: '12px',
                      borderRadius: 8,
                      border: orientation === 'PORTRAIT' ? '2px solid #1465f4' : '1px solid #cbd5e1',
                      background: orientation === 'PORTRAIT' ? '#eff6ff' : '#ffffff',
                      color: orientation === 'PORTRAIT' ? '#1465f4' : '#475569',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Portrait (A4)
                    <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>792 × 1120 px</div>
                  </button>
                </div>
              </div>

              <div style={{ padding: '12px 14px', background: '#f8fafc', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: '0.8rem', color: '#475569', lineHeight: 1.6 }}>
                <strong>Printing & Export:</strong> All templates automatically scale to high-resolution vector A4 for print and PDF generation.
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live WYSIWYG Canvas Preview */}
        <div style={{ background: '#0b1d42', borderRadius: 12, padding: 24, boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginBottom: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#f8fafc', fontSize: '0.85rem', fontWeight: 600 }}>
              <Sparkles size={16} color="#27d4f4" />
              <span>Live Interactive Layout Preview</span>
            </div>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
              Scale: 70% · {orientation}
            </span>
          </div>

          {/* Certificate Canvas Box */}
          <div
            style={{
              width: orientation === 'LANDSCAPE' ? 760 : 520,
              height: orientation === 'LANDSCAPE' ? 520 : 720,
              background: bgType === 'GRADIENT' ? bgGradient : bgType === 'IMAGE' && bgImageUrl ? `url(${bgImageUrl}) center/cover no-repeat` : bgColor,
              border: borderStyle === 'classic_gold' ? `${borderWidth}px solid #d97706` :
                      borderStyle === 'modern_blue' ? `${borderWidth}px solid ${borderColor}` :
                      borderStyle === 'double_line' ? `${borderWidth}px double ${borderColor}` :
                      borderStyle === 'minimal_clean' ? `2px solid ${borderColor}` : 'none',
              outline: borderStyle === 'classic_gold' ? '2px solid #07132e' :
                       borderStyle === 'modern_blue' ? '2px solid #27d4f4' : 'none',
              outlineOffset: -10,
              borderRadius: borderStyle === 'minimal_clean' ? 8 : 0,
              padding: '28px 36px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              position: 'relative',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)',
              transform: 'scale(1)',
              transition: 'all 0.2s ease',
              overflow: 'hidden'
            }}
          >
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(15, 23, 42, 0.08)', paddingBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {logoUrl && (
                  <img src={logoUrl} alt="Logo" style={{ height: 32, width: 'auto', objectFit: 'contain' }} onError={(e: any) => e.target.style.display = 'none'} />
                )}
                <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', color: '#07132e', textTransform: 'uppercase' }}>
                  {organizerName}
                </span>
              </div>
              <span style={{ fontSize: 10, fontWeight: 600, color: '#1465f4', background: 'rgba(20, 101, 244, 0.08)', padding: '2px 8px', borderRadius: 9999, border: '1px solid rgba(20, 101, 244, 0.2)' }}>
                ✓ VERIFIED CREDENTIAL
              </span>
            </div>

            {/* Body */}
            <div style={{ textAlign: 'center', padding: '10px 0' }}>
              <h2 style={{ fontFamily: 'Georgia, serif', fontSize: orientation === 'LANDSCAPE' ? 24 : 20, fontWeight: 700, letterSpacing: '0.1em', color: '#07132e', margin: '0 0 6px 0', textTransform: 'uppercase' }}>
                {title}
              </h2>
              <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: '0.14em', color: '#64748b', textTransform: 'uppercase', marginBottom: 10 }}>
                {subtitle}
              </div>
              <div>
                <div style={{ fontFamily: 'Georgia, serif', fontSize: orientation === 'LANDSCAPE' ? 28 : 24, fontWeight: 700, color: '#07132e', display: 'inline-block', borderBottom: `2px solid ${borderColor}`, paddingBottom: 4, marginBottom: 12 }}>
                  {mockParticipant}
                </div>
              </div>
              <p style={{ fontSize: 12, lineHeight: 1.6, color: '#334155', maxWidth: 600, margin: '0 auto' }}>
                {previewDescription}
              </p>
            </div>

            {/* Footer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderTop: '1px solid rgba(15, 23, 42, 0.08)', paddingTop: 12 }}>
              <div style={{ fontSize: 10, color: '#64748b', lineHeight: 1.5 }}>
                <div>ID: <strong style={{ color: '#07132e', fontFamily: 'monospace' }}>{mockCertId}</strong></div>
                <div>Issued: <strong style={{ color: '#07132e' }}>{mockDate}</strong></div>
              </div>

              {showQrCode && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ width: 44, height: 44, background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 2px auto' }}>
                    <QrCode size={36} color="#07132e" />
                  </div>
                  <span style={{ fontSize: 8, color: '#64748b' }}>Scan to Verify</span>
                </div>
              )}

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontFamily: 'cursive', fontSize: 20, color: '#07132e', lineHeight: 1, marginBottom: 2 }}>
                  {signatoryName}
                </div>
                <div style={{ fontSize: 10, fontWeight: 700, color: '#07132e' }}>{signatoryName}</div>
                <div style={{ fontSize: 9, color: '#64748b' }}>{signatoryTitle}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Full Preview Modal */}
      {previewModalOpen && activeTemplate?.id && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
          <div style={{ background: '#ffffff', borderRadius: 12, width: '90%', maxWidth: 1200, height: '88vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid #e2e8f0' }}>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: '#07132e' }}>
                Server-Rendered Certificate Test — {name}
              </h3>
              <button
                onClick={() => setPreviewModalOpen(false)}
                style={{ background: 'none', border: 'none', fontSize: 20, cursor: 'pointer', color: '#64748b' }}
              >
                ✕
              </button>
            </div>
            <iframe
              src={certificateTemplatesApi.getPreviewUrl(activeTemplate.id)}
              style={{ flex: 1, border: 'none', width: '100%', height: '100%' }}
              title="Certificate Test Rendering"
            />
          </div>
        </div>
      )}
    </div>
  );
};

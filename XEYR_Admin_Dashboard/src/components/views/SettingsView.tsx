import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { systemApi } from '../../services/api';
import {
  Settings,
  Shield,
  User,
  Database,
  Lock,
  LogOut,
  Clock,
  Key,
  Globe,
  Save,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Eye,
  FileText,
  RotateCcw
} from 'lucide-react';

const APPROVED_WHO_WE_ARE =
  'XEYR Technologies Private Limited is focused on delivering technology-driven solutions through software development, artificial intelligence, automation, SaaS products, and innovative digital experiences. Through our Events Portal, we aim to make it easier for participants to discover events, explore learning opportunities, and connect with technology-focused communities.';

export const SettingsView: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'website' | 'infrastructure'>('website');

  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Website Content & Footer Configuration State
  const [companyWebsiteUrl, setCompanyWebsiteUrl] = useState('/');
  const [eventsPortalUrl, setEventsPortalUrl] = useState('/events/');
  const [companyName, setCompanyName] = useState('XEYR Technologies Private Limited');
  const [companyTagline, setCompanyTagline] = useState('Ideas | Technology | Real Impact');
  const [contactEmail, setContactEmail] = useState('xeyrtechnologies@gmail.com');
  const [contactPhone, setContactPhone] = useState('+91 80562 53897');
  const [logoAssetUrl, setLogoAssetUrl] = useState('/assets/xeyr-symbol.png');

  const [whoWeAreHeading, setWhoWeAreHeading] = useState('Who We Are');
  const [whoWeAreDesc, setWhoWeAreDesc] = useState(APPROVED_WHO_WE_ARE);
  const [whatWeDoHeading, setWhatWeDoHeading] = useState('What We Do');

  const [footerTagline, setFooterTagline] = useState('Ideas. Technology. Real Impact.');
  const [footerDesc, setFooterDesc] = useState(
    'XEYR Technologies Private Limited develops enterprise software, intelligent automation, and hands-on learning experiences.'
  );

  // Section Visibility
  const [showWhoWeAre, setShowWhoWeAre] = useState(true);
  const [showWhatWeDo, setShowWhatWeDo] = useState(true);
  const [showContactUs, setShowContactUs] = useState(true);
  const [showQuickLinks, setShowQuickLinks] = useState(true);
  const [showLeaderboard, setShowLeaderboard] = useState(true);
  const [showGallery, setShowGallery] = useState(true);

  const fetchSettingsAndAudit = async () => {
    setLoading(true);
    try {
      const [logs, pubSettings] = await Promise.all([
        systemApi.getAuditLogs().catch(() => []),
        systemApi.getPublicSettings().catch(() => null)
      ]);
      setAuditLogs(logs);

      if (pubSettings) {
        if (pubSettings.company_website_url) setCompanyWebsiteUrl(pubSettings.company_website_url);
        if (pubSettings.events_portal_url) setEventsPortalUrl(pubSettings.events_portal_url);
        if (pubSettings.company_name) setCompanyName(pubSettings.company_name);
        if (pubSettings.tagline) setCompanyTagline(pubSettings.tagline);
        if (pubSettings.contact_email) setContactEmail(pubSettings.contact_email);
        if (pubSettings.contact_phone) setContactPhone(pubSettings.contact_phone);
        if (pubSettings.logo_asset_url) setLogoAssetUrl(pubSettings.logo_asset_url);

        if (pubSettings.who_we_are_heading) setWhoWeAreHeading(pubSettings.who_we_are_heading);
        if (pubSettings.who_we_are_description) setWhoWeAreDesc(pubSettings.who_we_are_description);
        if (pubSettings.what_we_do_heading) setWhatWeDoHeading(pubSettings.what_we_do_heading);

        if (pubSettings.footer_tagline) setFooterTagline(pubSettings.footer_tagline);
        if (pubSettings.footer_description) setFooterDesc(pubSettings.footer_description);

        if (pubSettings.section_visibility) {
          const v = pubSettings.section_visibility;
          setShowWhoWeAre(v.who_we_are !== false);
          setShowWhatWeDo(v.what_we_do !== false);
          setShowContactUs(v.contact_us !== false);
          setShowQuickLinks(v.quick_links !== false);
          setShowLeaderboard(v.leaderboard !== false);
          setShowGallery(v.gallery !== false);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettingsAndAudit();
  }, []);

  const handleSaveWebsiteSettings = async () => {
    setIsSaving(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const payload = {
      COMPANY_WEBSITE_URL: companyWebsiteUrl,
      EVENTS_PORTAL_URL: eventsPortalUrl,
      COMPANY_NAME: companyName,
      COMPANY_TAGLINE: companyTagline,
      CONTACT_EMAIL: contactEmail,
      CONTACT_PHONE: contactPhone,
      LOGO_ASSET_URL: logoAssetUrl,
      WHO_WE_ARE_HEADING: whoWeAreHeading,
      WHO_WE_ARE_DESCRIPTION: whoWeAreDesc,
      WHAT_WE_DO_HEADING: whatWeDoHeading,
      FOOTER_TAGLINE: footerTagline,
      FOOTER_DESCRIPTION: footerDesc,
      SECTION_VISIBILITY: JSON.stringify({
        who_we_are: showWhoWeAre,
        what_we_do: showWhatWeDo,
        contact_us: showContactUs,
        quick_links: showQuickLinks,
        leaderboard: showLeaderboard,
        gallery: showGallery
      })
    };

    try {
      await systemApi.batchUpdateSettings(payload);
      setSuccessMsg('Website content and footer settings saved successfully in database!');
      setTimeout(() => setSuccessMsg(null), 4000);
      await fetchSettingsAndAudit();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to save website content settings.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetWhoWeAre = () => {
    setWhoWeAreHeading('Who We Are');
    setWhoWeAreDesc(APPROVED_WHO_WE_ARE);
  };

  return (
    <div>
      {/* Top Tabs: Website Content vs Infrastructure */}
      <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid #e2e8f0', marginBottom: 24 }}>
        <button
          onClick={() => setActiveTab('website')}
          style={{
            background: 'none',
            border: 'none',
            padding: '10px 16px',
            fontSize: '0.95rem',
            fontWeight: activeTab === 'website' ? 700 : 500,
            color: activeTab === 'website' ? '#1465f4' : '#64748b',
            borderBottom: activeTab === 'website' ? '2.5px solid #1465f4' : '2.5px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}
        >
          <Globe size={18} /> Website &amp; Events Portal Content
        </button>
        <button
          onClick={() => setActiveTab('infrastructure')}
          style={{
            background: 'none',
            border: 'none',
            padding: '10px 16px',
            fontSize: '0.95rem',
            fontWeight: activeTab === 'infrastructure' ? 700 : 500,
            color: activeTab === 'infrastructure' ? '#1465f4' : '#64748b',
            borderBottom: activeTab === 'infrastructure' ? '2.5px solid #1465f4' : '2.5px solid transparent',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}
        >
          <Shield size={18} /> Enterprise Infrastructure &amp; Security
        </button>
      </div>

      {/* Alert Banners */}
      {successMsg && (
        <div style={{ padding: '12px 16px', background: '#ecfdf5', border: '1px solid #a7f3d0', borderRadius: 8, color: '#065f46', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
          <CheckCircle size={18} /> <span>{successMsg}</span>
        </div>
      )}
      {errorMsg && (
        <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, color: '#991b1b', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.88rem' }}>
          <AlertCircle size={18} /> <span>{errorMsg}</span>
        </div>
      )}

      {/* TAB 1: WEBSITE CONTENT & FOOTER MANAGEMENT */}
      {activeTab === 'website' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: '#07132e' }}>
                Website Content &amp; Footer Management
              </h2>
              <p style={{ fontSize: '0.84rem', color: '#64748b', margin: '4px 0 0 0' }}>
                Manage live company information, "Visit Our Website" destinations, Who We Are copy, and footer visibility.
              </p>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <a
                href="/events/"
                target="_blank"
                rel="noreferrer"
                className="button button-outline"
                style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px', borderRadius: 8, fontSize: '0.84rem', fontWeight: 600, color: '#1465f4', border: '1px solid #bfdbfe' }}
              >
                <ExternalLink size={16} /> Preview Events Portal
              </a>
              <button
                onClick={handleSaveWebsiteSettings}
                disabled={isSaving}
                className="button button-primary"
                style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#1465f4', color: '#fff', border: 'none', padding: '9px 18px', borderRadius: 8, fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}
              >
                <Save size={16} /> {isSaving ? 'Saving Changes...' : 'Save Website Settings'}
              </button>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
            {/* Box 1: Routing & Brand Identity */}
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 16, color: '#07132e', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Globe size={18} color="#1465f4" /> Routing &amp; Brand Destinations
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Main Company Homepage URL (Destination for Nav Logo &amp; "Visit Our Website" button)
                  </label>
                  <input
                    type="text"
                    value={companyWebsiteUrl}
                    onChange={e => setCompanyWebsiteUrl(e.target.value)}
                    placeholder="e.g. http://localhost:8080/ or /"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                  />
                  <small style={{ color: '#64748b', fontSize: '0.72rem', marginTop: 4, display: 'block' }}>
                    Used in Events Portal navigation logo and footer "Visit Our Website" button to return to company homepage.
                  </small>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Canonical Events Portal URL
                  </label>
                  <input
                    type="text"
                    value={eventsPortalUrl}
                    onChange={e => setEventsPortalUrl(e.target.value)}
                    placeholder="e.g. http://localhost:8080/events/"
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                  />
                  <small style={{ color: '#64748b', fontSize: '0.72rem', marginTop: 4, display: 'block' }}>
                    Used for primary promotional sharing links and canonical portal QR code generation.
                  </small>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                      Company Name
                    </label>
                    <input
                      type="text"
                      value={companyName}
                      onChange={e => setCompanyName(e.target.value)}
                      style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                      Brand Logo Asset
                    </label>
                    <select
                      value={logoAssetUrl}
                      onChange={e => setLogoAssetUrl(e.target.value)}
                      style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem', background: '#fff' }}
                    >
                      <option value="/assets/xeyr-symbol.png">Official XEYR Symbol (/assets/xeyr-symbol.png)</option>
                      <option value="/assets/xeyr-wordmark.png">Official Wordmark (/assets/xeyr-wordmark.png)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Box 2: Contact Information */}
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 16, color: '#07132e', display: 'flex', alignItems: 'center', gap: 8 }}>
                <User size={18} color="#1465f4" /> Approved Contact Details (Section C)
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Official Contact Email
                  </label>
                  <input
                    type="email"
                    value={contactEmail}
                    onChange={e => setContactEmail(e.target.value)}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                  />
                  <small style={{ color: '#64748b', fontSize: '0.72rem', marginTop: 4, display: 'block' }}>
                    Rendered as clickable mailto link across all portal contact points.
                  </small>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Official Phone Number
                  </label>
                  <input
                    type="text"
                    value={contactPhone}
                    onChange={e => setContactPhone(e.target.value)}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                  />
                  <small style={{ color: '#64748b', fontSize: '0.72rem', marginTop: 4, display: 'block' }}>
                    Rendered as clickable tel link for mobile visitors.
                  </small>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Company Tagline
                  </label>
                  <input
                    type="text"
                    value={companyTagline}
                    onChange={e => setCompanyTagline(e.target.value)}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Box 3: Section A — Who We Are */}
          <div className="card" style={{ padding: 24, marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: '#07132e' }}>
                Section A — Who We Are
              </h3>
              <button
                type="button"
                onClick={handleResetWhoWeAre}
                style={{ background: 'none', border: 'none', color: '#1465f4', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <RotateCcw size={14} /> Reset to Approved Text
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                  Section Heading
                </label>
                <input
                  type="text"
                  value={whoWeAreHeading}
                  onChange={e => setWhoWeAreHeading(e.target.value)}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                  Company Description
                </label>
                <textarea
                  rows={4}
                  value={whoWeAreDesc}
                  onChange={e => setWhoWeAreDesc(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem', lineHeight: 1.6 }}
                />
              </div>
            </div>
          </div>

          {/* Box 4: Footer & Section Visibility */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: 24, marginBottom: 24 }}>
            {/* Footer Copy */}
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 14, color: '#07132e' }}>
                Footer Column &amp; Tagline Settings
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Footer Tagline
                  </label>
                  <input
                    type="text"
                    value={footerTagline}
                    onChange={e => setFooterTagline(e.target.value)}
                    style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: '#334155', marginBottom: 4 }}>
                    Footer Brand Description
                  </label>
                  <textarea
                    rows={3}
                    value={footerDesc}
                    onChange={e => setFooterDesc(e.target.value)}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid #cbd5e1', fontSize: '0.88rem', lineHeight: 1.6 }}
                  />
                </div>
              </div>
            </div>

            {/* Section Visibility Toggles */}
            <div className="card" style={{ padding: 24 }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 14, color: '#07132e' }}>
                Section Visibility Control
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  { label: 'Show "Who We Are" Section', checked: showWhoWeAre, set: setShowWhoWeAre },
                  { label: 'Show "What We Do" Services', checked: showWhatWeDo, set: setShowWhatWeDo },
                  { label: 'Show "Get in Touch" Contact Card', checked: showContactUs, set: setShowContactUs },
                  { label: 'Show "Quick Links" Navigation Card', checked: showQuickLinks, set: setShowQuickLinks },
                  { label: 'Show Community Leaderboard', checked: showLeaderboard, set: setShowLeaderboard },
                  { label: 'Show Event Photo Gallery', checked: showGallery, set: setShowGallery }
                ].map((item, idx) => (
                  <label key={idx} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.86rem', color: '#334155', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={item.checked}
                      onChange={e => item.set(e.target.checked)}
                      style={{ width: 17, height: 17, cursor: 'pointer' }}
                    />
                    <span>{item.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: ENTERPRISE INFRASTRUCTURE & AUDIT TRAIL */}
      {activeTab === 'infrastructure' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', marginBottom: '28px' }}>
            {/* Administrator Profile Card */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Administrator Profile</h3>
                <span className="badge badge-qualified">Active Session</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
                <div style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #1465f4, #38bdf8)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#ffffff',
                  fontSize: '1.4rem',
                  fontWeight: 800
                }}>
                  {user?.username?.charAt(0).toUpperCase() || 'A'}
                </div>
                <div>
                  <h4 style={{ fontSize: '1.1rem', fontWeight: 800 }}>
                    {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}
                  </h4>
                  <span className="badge badge-new" style={{ marginTop: '2px' }}>
                    {user?.role?.replace('_', ' ') || 'Super Administrator'}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.86rem', color: '#475569', marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Username / ID:</span>
                  <strong>{user?.username}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Corporate Email:</span>
                  <strong>{user?.email || 'admin@xeyr.com'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Department:</span>
                  <strong>{user?.department || 'Executive Operations'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#64748b' }}>Privileges:</span>
                  <strong style={{ color: user?.is_superuser ? '#059669' : '#1e40af' }}>
                    {user?.is_superuser ? 'Super Administrator (Full Root Access)' : 'Staff User'}
                  </strong>
                </div>
              </div>

              <button onClick={logout} className="btn btn-danger" style={{ width: '100%', justifyContent: 'center' }}>
                <LogOut size={16} /> Sign Out of Dashboard Session
              </button>
            </div>

            {/* Database & Environment Status Card */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Enterprise Infrastructure</h3>
                <span className="badge badge-qualified">Verified</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.86rem', color: '#475569' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', background: '#f8fafc', borderRadius: '8px' }}>
                  <Database size={20} color="#1465f4" />
                  <div>
                    <strong style={{ display: 'block', color: '#0f172a' }}>Database Engine</strong>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>PostgreSQL 17.10 (msvc-19.44, 64-bit)</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', background: '#f8fafc', borderRadius: '8px' }}>
                  <Shield size={20} color="#059669" />
                  <div>
                    <strong style={{ display: 'block', color: '#0f172a' }}>Session Security</strong>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>HTTP-only Django Session Cookie with CSRF Defense</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px', background: '#f8fafc', borderRadius: '8px' }}>
                  <Lock size={20} color="#b45309" />
                  <div>
                    <strong style={{ display: 'block', color: '#0f172a' }}>Secrets Management</strong>
                    <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Enforced via .env environment variables (No hardcoded keys)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Immutable Security & Audit Log Table */}
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Immutable Security &amp; Audit Trail</h3>
                <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                  Timestamped logs of every administrator action, status mutation, and authentication event.
                </p>
              </div>
              <span className="badge badge-new">{auditLogs.length} Events</span>
            </div>

            {loading ? (
              <p style={{ color: '#64748b', fontSize: '0.85rem' }}>Loading audit logs...</p>
            ) : auditLogs.length === 0 ? (
              <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No audit actions recorded in current window.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Action</th>
                      <th>Entity Type</th>
                      <th>Entity ID</th>
                      <th>IP Address</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {auditLogs.slice(0, 15).map((log, idx) => (
                      <tr key={idx}>
                        <td>
                          <strong style={{ color: '#1465f4', fontSize: '0.84rem' }}>{log.action}</strong>
                        </td>
                        <td>{log.entity_type}</td>
                        <td><code>{log.entity_id}</code></td>
                        <td><span style={{ fontSize: '0.8rem', color: '#64748b' }}>{log.ip_address || '127.0.0.1'}</span></td>
                        <td>
                          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
                            {new Date(log.timestamp).toLocaleString('en-IN')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

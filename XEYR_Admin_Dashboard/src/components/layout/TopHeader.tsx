import React from 'react';
import { ActiveTab } from './Sidebar';
import { useAuth } from '../../context/AuthContext';
import { Bell, Search, Calendar, Menu } from 'lucide-react';

interface TopHeaderProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  period: string;
  setPeriod: (period: string) => void;
  unreadCount?: number;
  toggleMobileMenu?: () => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

const tabTitles: Record<ActiveTab, { title: string; category: string }> = {
  overview: { title: 'Executive Overview & Business Intelligence', category: 'Analytics' },
  reports: { title: 'Verified Reports & CSV Exports', category: 'Analytics' },
  enquiries: { title: 'Client Enquiries & CRM Pipeline', category: 'CRM & Pipeline' },
  qualified: { title: 'Qualified Leads & Feasibility Assessments', category: 'CRM & Pipeline' },
  rejected: { title: 'Disqualified / Rejected Leads Audit', category: 'CRM & Pipeline' },
  requirements: { title: 'Client Requirements Workspaces', category: 'Engineering' },
  assets: { title: 'Brand Assets & Cryptographic Files', category: 'Engineering' },
  handover: { title: 'Developer Handover Packages (ZIP)', category: 'Engineering' },
  projects: { title: 'Projects, Milestones & Sprint Progress', category: 'Engineering' },
  events: { title: 'Central Workshops & Events Management', category: 'Events' },
  registrations: { title: 'Participant Registrations & Attendees', category: 'Events' },
  certificates: { title: 'Certificate Template Designer & Preview', category: 'Events' },
  social: { title: 'Official Social Media & QR Code Graphics', category: 'Events' },
  finance: { title: 'Financial Records, Invoices & Payments', category: 'Finance' },
  notifications: { title: 'System Security Alerts & Notifications', category: 'System' },
  settings: { title: 'Administrative Settings & Audit Trail', category: 'System' },
};

export const TopHeader: React.FC<TopHeaderProps> = ({
  activeTab,
  setActiveTab,
  period,
  setPeriod,
  unreadCount = 0,
  toggleMobileMenu,
  searchQuery,
  setSearchQuery,
}) => {
  const { user } = useAuth();
  const info = tabTitles[activeTab] || { title: 'Administration', category: 'XEYR' };

  return (
    <header className="top-header">
      <div className="header-left">
        {toggleMobileMenu && (
          <button
            onClick={toggleMobileMenu}
            className="btn btn-secondary btn-sm mobile-menu-btn"
            id="mobile-nav-toggle"
            aria-label="Toggle navigation menu"
          >
            <Menu size={18} />
          </button>
        )}
        <div>
          <div className="breadcrumb">
            XEYR Enterprise &gt; {info.category} &gt; <strong style={{ color: '#1465f4' }}>{activeTab.toUpperCase()}</strong>
          </div>
          <h2 className="page-title">{info.title}</h2>
        </div>
      </div>

      <div className="header-right">
        {/* Global Search Bar */}
        <div style={{ position: 'relative', width: '220px' }}>
          <Search
            size={16}
            style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }}
          />
          <input
            type="text"
            className="form-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search records..."
            style={{ paddingLeft: '34px', paddingRight: '12px', height: '38px', fontSize: '0.82rem' }}
          />
        </div>

        {/* Date Filter (visible on overview, reports, finance) */}
        {['overview', 'reports', 'finance'].includes(activeTab) && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#f1f5f9', padding: '4px 10px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
            <Calendar size={14} color="#1465f4" />
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              style={{
                border: 0,
                background: 'transparent',
                fontSize: '0.82rem',
                fontWeight: 600,
                color: '#0f172a',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value="last_30_days">Last 30 Days</option>
              <option value="today">Today</option>
              <option value="yesterday">Yesterday</option>
              <option value="last_7_days">Last 7 Days</option>
              <option value="this_week">This Week</option>
              <option value="this_month">This Month</option>
              <option value="last_month">Last Month</option>
              <option value="this_quarter">This Quarter</option>
              <option value="this_year">This Year</option>
            </select>
          </div>
        )}

        {/* Notification Bell */}
        <button
          onClick={() => setActiveTab('notifications')}
          style={{
            position: 'relative',
            background: 'transparent',
            border: '1px solid #e2e8f0',
            width: '38px',
            height: '38px',
            borderRadius: '9px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          title={`${unreadCount} Unread Notifications`}
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              backgroundColor: '#ef4444',
              color: '#ffffff',
              fontSize: '0.68rem',
              fontWeight: 800,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 6px rgba(239, 68, 68, 0.5)'
            }}>
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          )}
        </button>

        {/* User Chip */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 12px 4px 6px',
          background: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '99px'
        }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#1e40af' }}>
            {user?.username || 'Admin'}
          </span>
        </div>
      </div>
    </header>
  );
};

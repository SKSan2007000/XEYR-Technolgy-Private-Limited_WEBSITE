import React from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  LayoutDashboard,
  Inbox,
  UserCheck,
  UserX,
  FileSpreadsheet,
  Palette,
  PackageCheck,
  Briefcase,
  CalendarDays,
  Users,
  Bell,
  IndianRupee,
  QrCode,
  FileBarChart,
  Settings,
  LogOut,
  ExternalLink,
  Award
} from 'lucide-react';

export type ActiveTab =
  | 'overview'
  | 'enquiries'
  | 'qualified'
  | 'rejected'
  | 'requirements'
  | 'assets'
  | 'handover'
  | 'projects'
  | 'events'
  | 'registrations'
  | 'certificates'
  | 'notifications'
  | 'finance'
  | 'social'
  | 'reports'
  | 'settings';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  unreadCount?: number;
  isOpenMobile?: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  unreadCount = 0,
  isOpenMobile = false
}) => {
  const { logout, user } = useAuth();

  const navSections = [
    {
      title: 'Business Intelligence',
      items: [
        { id: 'overview' as ActiveTab, label: 'Overview', icon: LayoutDashboard },
        { id: 'reports' as ActiveTab, label: 'Reports & Analytics', icon: FileBarChart },
      ]
    },
    {
      title: 'CRM & Pipeline',
      items: [
        { id: 'enquiries' as ActiveTab, label: 'Enquiries & CRM', icon: Inbox },
        { id: 'qualified' as ActiveTab, label: 'Qualified Leads', icon: UserCheck },
        { id: 'rejected' as ActiveTab, label: 'Rejected Leads', icon: UserX },
      ]
    },
    {
      title: 'Operations & Engineering',
      items: [
        { id: 'requirements' as ActiveTab, label: 'Client Requirements', icon: FileSpreadsheet },
        { id: 'assets' as ActiveTab, label: 'Brand Assets', icon: Palette },
        { id: 'handover' as ActiveTab, label: 'Developer Handovers', icon: PackageCheck },
        { id: 'projects' as ActiveTab, label: 'Projects & Sprints', icon: Briefcase },
      ]
    },
    {
      title: 'Events & Engagement',
      items: [
        { id: 'events' as ActiveTab, label: 'Workshops & Events', icon: CalendarDays },
        { id: 'registrations' as ActiveTab, label: 'Registrations', icon: Users },
        { id: 'certificates' as ActiveTab, label: 'Certificate Designer', icon: Award },
        { id: 'social' as ActiveTab, label: 'Social Media & QR', icon: QrCode },
      ]
    },
    {
      title: 'Finance & System',
      items: [
        { id: 'finance' as ActiveTab, label: 'Finance & Payments', icon: IndianRupee },
        { id: 'notifications' as ActiveTab, label: 'Notifications', icon: Bell, badge: unreadCount },
        { id: 'settings' as ActiveTab, label: 'System Settings', icon: Settings },
      ]
    }
  ];

  return (
    <aside className={`sidebar ${isOpenMobile ? 'open' : ''}`}>
      {/* Brand Header */}
      <div className="sidebar-header">
        <img src="/xeyr-symbol.png" alt="XEYR Logo" className="sidebar-logo" />
        <div className="sidebar-brand-text">
          <h1>XEYR</h1>
          <span>ENTERPRISE OS</span>
        </div>
      </div>

      {/* Navigation */}
      <div className="sidebar-nav">
        {navSections.map((sec, idx) => (
          <div key={idx}>
            <div className="sidebar-section-title">{sec.title}</div>
            {sec.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span className="nav-badge" style={{ backgroundColor: '#ef4444' }}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}

        <div className="sidebar-section-title">Navigation Links</div>
        <a
          href="http://127.0.0.1:8000/"
          target="_blank"
          rel="noopener noreferrer"
          className="nav-item"
        >
          <ExternalLink size={18} />
          <span>Public Website</span>
        </a>
        <a
          href="http://127.0.0.1:8000/admin/"
          target="_blank"
          rel="noopener noreferrer"
          className="nav-item"
        >
          <ExternalLink size={18} />
          <span>Django Admin</span>
        </a>
      </div>

      {/* Footer / User Profile & Logout */}
      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #1465f4, #38bdf8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 800,
            fontSize: '0.8rem',
            flexShrink: 0
          }}>
            {user?.username?.charAt(0).toUpperCase() || 'A'}
          </div>
          <div style={{ minWidth: 0, overflow: 'hidden' }}>
            <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#07132e', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.username}
            </div>
            <div style={{ fontSize: '0.68rem', color: '#64748b' }}>
              {user?.role?.replace('_', ' ') || 'Administrator'}
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          title="Sign out securely"
          style={{
            background: '#f1f5f9',
            border: 0,
            color: '#475569',
            padding: '8px',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'background 0.2s, color 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
            e.currentTarget.style.color = '#ef4444';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.08)';
            e.currentTarget.style.color = '#94a3b8';
          }}
        >
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};

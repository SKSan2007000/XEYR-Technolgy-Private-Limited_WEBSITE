import React, { useState, useEffect, useCallback } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginView } from './components/LoginView';
import { Sidebar, ActiveTab } from './components/layout/Sidebar';
import { TopHeader } from './components/layout/TopHeader';

// Management Views
import { OverviewView } from './components/views/OverviewView';
import { EnquiriesView } from './components/views/EnquiriesView';
import { QualifiedLeadsView } from './components/views/QualifiedLeadsView';
import { RejectedLeadsView } from './components/views/RejectedLeadsView';
import { RequirementsView } from './components/views/RequirementsView';
import { BrandAssetsView } from './components/views/BrandAssetsView';
import { HandoversView } from './components/views/HandoversView';
import { ProjectsView } from './components/views/ProjectsView';
import { EventsView } from './components/views/EventsView';
import { RegistrationsView } from './components/views/RegistrationsView';
import { CertificateDesignerView } from './components/views/CertificateDesignerView';
import { NotificationsView } from './components/views/NotificationsView';
import { FinanceView } from './components/views/FinanceView';
import { SocialMediaView } from './components/views/SocialMediaView';
import { ReportsView } from './components/views/ReportsView';
import { SettingsView } from './components/views/SettingsView';

import { notificationService } from './services/api';
import { Loader2 } from 'lucide-react';

const DashboardContent: React.FC = () => {
  const { loading, isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [period, setPeriod] = useState<string>('30d');
  const [unreadNotifications, setUnreadNotifications] = useState<number>(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState<boolean>(false);

  const fetchUnreadCount = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await notificationService.getNotifications();
      const unread = data.filter((n: any) => !n.is_read).length;
      setUnreadNotifications(unread);
    } catch {
      // Graceful fallback if network drops
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchUnreadCount();
      const interval = setInterval(fetchUnreadCount, 45000); // Polling unread alerts
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, fetchUnreadCount]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#07132e',
        color: '#ffffff'
      }}>
        <div style={{
          width: 56,
          height: 56,
          borderRadius: 14,
          background: 'rgba(20, 101, 244, 0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid rgba(20, 101, 244, 0.4)',
          marginBottom: 16
        }}>
          <Loader2 className="animate-spin" size={28} color="#3b82f6" />
        </div>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 600, letterSpacing: '-0.02em', margin: 0 }}>
          Authenticating XEYR Enterprise Portal
        </h2>
        <p style={{ fontSize: '0.82rem', color: '#94a3b8', marginTop: 6 }}>
          Verifying security handshake and administrative permissions...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginView />;
  }

  const renderActiveView = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewView period={period} setActiveTab={setActiveTab} />;
      case 'enquiries':
        return <EnquiriesView searchQuery={searchQuery} />;
      case 'qualified':
        return <QualifiedLeadsView searchQuery={searchQuery} setActiveTab={setActiveTab} />;
      case 'rejected':
        return <RejectedLeadsView searchQuery={searchQuery} setActiveTab={setActiveTab} />;
      case 'requirements':
        return <RequirementsView searchQuery={searchQuery} setActiveTab={setActiveTab} />;
      case 'assets':
        return <BrandAssetsView />;
      case 'handover':
        return <HandoversView />;
      case 'projects':
        return <ProjectsView />;
      case 'events':
        return <EventsView />;
      case 'registrations':
        return <RegistrationsView />;
      case 'certificates':
        return <CertificateDesignerView />;
      case 'notifications':
        return <NotificationsView setActiveTab={setActiveTab} onRefreshUnread={fetchUnreadCount} />;
      case 'finance':
        return <FinanceView />;
      case 'social':
        return <SocialMediaView />;
      case 'reports':
        return <ReportsView period={period} />;
      case 'settings':
        return <SettingsView />;
      default:
        return <OverviewView period={period} setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="dashboard-layout" style={{ display: 'flex', minHeight: '100vh', background: '#f8fafc' }}>
      {/* Primary Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab: ActiveTab) => {
          setActiveTab(tab);
          setSearchQuery(''); // Reset search on tab switch
          setMobileMenuOpen(false);
        }}
        unreadCount={unreadNotifications}
        isOpenMobile={mobileMenuOpen}
      />

      {/* Mobile Backdrop Overlay */}
      {mobileMenuOpen && (
        <div
          className="mobile-backdrop"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Main Container */}
      <div className="main-viewport">
        {/* Top Header */}
        <TopHeader
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          period={period}
          setPeriod={setPeriod}
          unreadCount={unreadNotifications}
          toggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
        />

        {/* Dynamic Viewport */}
        <main style={{
          flex: 1,
          padding: '24px 32px',
          overflowY: 'auto',
          background: '#f8fafc'
        }}>
          <div style={{ maxWidth: 1600, margin: '0 auto' }}>
            {renderActiveView()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}

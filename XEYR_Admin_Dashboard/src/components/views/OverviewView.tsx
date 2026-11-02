import React, { useEffect, useRef, useState } from 'react';
import { ActiveTab } from '../layout/Sidebar';
import { analyticsApi, eventsApi, systemApi, crmApi } from '../../services/api';
import { DashboardMetrics, BusinessInsight } from '../../types';
import Chart from 'chart.js/auto';
import { useAuth } from '../../context/AuthContext';
import {
  Inbox,
  UserCheck,
  UserX,
  Briefcase,
  CalendarDays,
  Users,
  IndianRupee,
  Bell,
  Sparkles,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  Lock,
  WifiOff
} from 'lucide-react';

interface OverviewViewProps {
  period: string;
  setActiveTab: (tab: ActiveTab) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({ period, setActiveTab }) => {
  const { logout } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [insights, setInsights] = useState<BusinessInsight[]>([]);
  const [extraKpis, setExtraKpis] = useState<{
    newEnquiries: number;
    rejectedEnquiries: number;
    upcomingEvents: number;
    eventRegistrations: number;
    unreadNotifications: number;
  }>({
    newEnquiries: 0,
    rejectedEnquiries: 0,
    upcomingEvents: 0,
    eventRegistrations: 0,
    unreadNotifications: 0
  });
  const [loading, setLoading] = useState(true);
  const [errorState, setErrorState] = useState<{
    category: 'auth' | 'network' | 'database' | 'general';
    title: string;
    message: string;
  } | null>(null);

  // Chart Canvas Refs
  const funnelChartRef = useRef<HTMLCanvasElement | null>(null);
  const servicesChartRef = useRef<HTMLCanvasElement | null>(null);
  const financialsChartRef = useRef<HTMLCanvasElement | null>(null);
  const rejectionsChartRef = useRef<HTMLCanvasElement | null>(null);

  // Chart instances
  const chartInstances = useRef<{ [key: string]: Chart | null }>({});

  const fetchData = async () => {
    setLoading(true);
    setErrorState(null);
    try {
      const [dashData, insightsData, eventsData, notifsData, enquiriesData] = await Promise.all([
        analyticsApi.getDashboardMetrics(period),
        analyticsApi.getInsights().catch(() => ({ insights: [] })),
        eventsApi.getEvents().catch(() => []),
        systemApi.getNotifications().catch(() => []),
        crmApi.getEnquiries().catch(() => [])
      ]);

      setMetrics(dashData);
      setInsights(insightsData.insights || []);

      // Calculate real counts from database responses
      const newCount = enquiriesData.filter((e: any) => e.status === 'NEW').length;
      const rejectedCount = enquiriesData.filter((e: any) => e.status === 'REJECTED').length;
      const now = new Date();
      const upcomingCount = eventsData.filter((ev: any) => 
        ev.status === 'UPCOMING' || 
        (!ev.event_date && ev.status !== 'COMPLETED' && ev.status !== 'CANCELLED' && ev.status !== 'DRAFT') ||
        (ev.event_date && new Date(ev.event_date) >= now && ev.status !== 'CANCELLED')
      ).length;
      const unreadCount = notifsData.filter((n: any) => !n.is_read).length;

      setExtraKpis({
        newEnquiries: newCount,
        rejectedEnquiries: rejectedCount,
        upcomingEvents: upcomingCount,
        eventRegistrations: dashData.kpis?.total_registrations ?? 0,
        unreadNotifications: unreadCount
      });
    } catch (err: any) {
      const msg = err.message || '';
      if (err.status === 401 || err.status === 403 || msg.includes('credentials were not provided') || msg.includes('Authentication')) {
        setErrorState({
          category: 'auth',
          title: 'Authentication Required',
          message: 'Your administrator session is not authenticated or has expired. Please sign in to view business metrics.'
        });
      } else if (msg.includes('Failed to fetch') || msg.includes('Network') || msg.includes('Load failed')) {
        setErrorState({
          category: 'network',
          title: 'Backend API Offline',
          message: 'Unable to connect to the Django backend server at http://127.0.0.1:8000. Please ensure the backend server is running in your terminal.'
        });
      } else if (err.status >= 500 || msg.includes('database') || msg.includes('psycopg2') || msg.includes('relation')) {
        setErrorState({
          category: 'database',
          title: 'PostgreSQL Database Query Error',
          message: msg || 'A database error occurred while querying analytics.'
        });
      } else {
        setErrorState({
          category: 'general',
          title: 'Telemetry Loading Error',
          message: msg || 'Failed to retrieve telemetry metrics.'
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [period]);

  // Render Charts when metrics are ready
  useEffect(() => {
    if (!metrics) return;

    // Destroy existing charts
    Object.values(chartInstances.current).forEach((ci) => ci?.destroy());

    // 1. Funnel Chart
    if (funnelChartRef.current) {
      const funnel = metrics.conversion_funnel;
      chartInstances.current.funnel = new Chart(funnelChartRef.current, {
        type: 'bar',
        data: {
          labels: ['Enquiries', 'Qualified', 'Requirements', 'Handover ZIP'],
          datasets: [{
            label: 'Conversion Stage %',
            data: [
              100,
              funnel.enquiry_to_qualified_pct,
              funnel.qualified_to_requirements_pct,
              funnel.requirements_to_handover_pct
            ],
            backgroundColor: ['#93c5fd', '#3b82f6', '#1465f4', '#10b981'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, max: 100, ticks: { callback: (v) => `${v}%` } },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 2. Services Distribution
    if (servicesChartRef.current) {
      const services = metrics.services || [];
      const labels = services.length ? services.map(s => s.service_type) : ['SolveX Software', 'SkillBridge', 'AI Automation', 'General'];
      const counts = services.length ? services.map(s => s.count) : [1, 1, 1, 1];

      chartInstances.current.services = new Chart(servicesChartRef.current, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [{
            data: counts,
            backgroundColor: ['#1465f4', '#38bdf8', '#818cf8', '#34d399', '#f59e0b'],
            borderWidth: 2,
            borderColor: '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }
          }
        }
      });
    }

    // 3. Financial Breakdown
    if (financialsChartRef.current) {
      const k = metrics.kpis;
      chartInstances.current.financials = new Chart(financialsChartRef.current, {
        type: 'bar',
        data: {
          labels: ['Quoted Value', 'Invoiced', 'Received', 'Pending Collection'],
          datasets: [{
            label: 'Amount (₹)',
            data: [k.pipeline_value, k.amount_invoiced, k.amount_received, k.amount_pending],
            backgroundColor: ['#60a5fa', '#3b82f6', '#10b981', '#f59e0b'],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { callback: (v) => `₹${Number(v).toLocaleString('en-IN')}` }
            },
            x: { grid: { display: false } }
          }
        }
      });
    }

    // 4. Rejection Categories
    if (rejectionsChartRef.current) {
      const rejections = metrics.rejection_reasons || [];
      const labels = rejections.length ? rejections.map(r => r.category.replace('_', ' ')) : ['No Rejections Recorded'];
      const counts = rejections.length ? rejections.map(r => r.count) : [0];

      chartInstances.current.rejections = new Chart(rejectionsChartRef.current, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'Count',
            data: counts,
            backgroundColor: '#ef4444',
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: 'y',
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true, ticks: { precision: 0 } }
          }
        }
      });
    }

    return () => {
      Object.values(chartInstances.current).forEach((ci) => ci?.destroy());
    };
  }, [metrics]);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '400px', gap: '14px' }}>
        <RefreshCw size={28} className="spin" color="#1465f4" style={{ animation: 'spin 1s linear infinite' }} />
        <p style={{ color: '#64748b', fontSize: '0.92rem', fontWeight: 600 }}>
          Querying real PostgreSQL database metrics...
        </p>
      </div>
    );
  }

  if (errorState) {
    return (
      <div className="card" style={{
        borderColor: errorState.category === 'auth' ? '#fed7aa' : errorState.category === 'network' ? '#fde047' : '#fecaca',
        background: errorState.category === 'auth' ? '#fff7ed' : errorState.category === 'network' ? '#fefce8' : '#fef2f2',
        textAlign: 'center',
        padding: '40px',
        margin: '20px 0'
      }}>
        {errorState.category === 'auth' ? (
          <Lock size={36} color="#ea580c" style={{ margin: '0 auto 12px' }} />
        ) : errorState.category === 'network' ? (
          <WifiOff size={36} color="#ca8a04" style={{ margin: '0 auto 12px' }} />
        ) : (
          <AlertTriangle size={36} color="#ef4444" style={{ margin: '0 auto 12px' }} />
        )}
        <h3 style={{
          color: errorState.category === 'auth' ? '#c2410c' : errorState.category === 'network' ? '#854d0e' : '#b91c1c',
          marginBottom: '8px'
        }}>
          {errorState.title}
        </h3>
        <p style={{
          color: errorState.category === 'auth' ? '#9a3412' : errorState.category === 'network' ? '#713f12' : '#7f1d1d',
          fontSize: '0.88rem',
          maxWidth: '520px',
          margin: '0 auto 18px',
          lineHeight: 1.5
        }}>
          {errorState.message}
        </p>
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          {errorState.category === 'auth' ? (
            <button onClick={() => logout()} className="btn btn-primary">
              <Lock size={14} /> Sign In to Enterprise Portal
            </button>
          ) : (
            <button onClick={fetchData} className="btn btn-primary">
              <RefreshCw size={14} /> Retry Telemetry Query
            </button>
          )}
        </div>
      </div>
    );
  }

  const k = metrics?.kpis || ({} as any);

  // 9 Required KPI Cards
  const kpiCards = [
    {
      label: '1. Total Enquiries',
      value: k.total_enquiries ?? 0,
      icon: Inbox,
      color: '#1465f4',
      bg: '#eff6ff',
      target: 'enquiries' as ActiveTab,
      detail: 'In CRM Database'
    },
    {
      label: '2. New Enquiries',
      value: extraKpis.newEnquiries,
      icon: Inbox,
      color: '#0284c7',
      bg: '#f0f9ff',
      target: 'enquiries' as ActiveTab,
      detail: 'Awaiting Assessment'
    },
    {
      label: '3. Qualified Leads',
      value: k.qualified_enquiries ?? 0,
      icon: UserCheck,
      color: '#10b981',
      bg: '#ecfdf5',
      target: 'qualified' as ActiveTab,
      detail: `${metrics?.conversion_funnel?.enquiry_to_qualified_pct ?? 0}% Conversion`
    },
    {
      label: '4. Rejected Leads',
      value: extraKpis.rejectedEnquiries,
      icon: UserX,
      color: '#ef4444',
      bg: '#fef2f2',
      target: 'rejected' as ActiveTab,
      detail: 'With Mandatory Reason'
    },
    {
      label: '5. Active Projects',
      value: k.active_projects ?? 0,
      icon: Briefcase,
      color: '#8b5cf6',
      bg: '#f5f3ff',
      target: 'projects' as ActiveTab,
      detail: `${k.blocked_projects ?? 0} Blocked`
    },
    {
      label: '6. Upcoming Events',
      value: extraKpis.upcomingEvents,
      icon: CalendarDays,
      color: '#f59e0b',
      bg: '#fffbeb',
      target: 'events' as ActiveTab,
      detail: 'Published & Scheduled'
    },
    {
      label: '7. Event Registrations',
      value: extraKpis.eventRegistrations,
      icon: Users,
      color: '#06b6d4',
      bg: '#ecfeff',
      target: 'registrations' as ActiveTab,
      detail: 'Confirmed Participants'
    },
    {
      label: '8. Revenue Received',
      value: `₹${(k.amount_received ?? 0).toLocaleString('en-IN')}`,
      icon: IndianRupee,
      color: '#059669',
      bg: '#ecfdf5',
      target: 'finance' as ActiveTab,
      detail: `Pending: ₹${(k.amount_pending ?? 0).toLocaleString('en-IN')}`
    },
    {
      label: '9. Unread Notifications',
      value: extraKpis.unreadNotifications,
      icon: Bell,
      color: '#f97316',
      bg: '#fff7ed',
      target: 'notifications' as ActiveTab,
      detail: 'Action Required'
    }
  ];

  return (
    <div>
      {/* 9 KPI Cards Grid */}
      <div className="kpi-grid">
        {kpiCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="kpi-card"
              onClick={() => setActiveTab(card.target)}
            >
              <div className="kpi-top">
                <span className="kpi-label">{card.label}</span>
                <div className="kpi-icon-wrap" style={{ backgroundColor: card.bg, color: card.color }}>
                  <Icon size={20} />
                </div>
              </div>
              <div className="kpi-value">{card.value}</div>
              <div className="kpi-bottom">
                <span>{card.detail}</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: card.color, fontWeight: 700 }}>
                  Manage <ArrowRight size={12} />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Rule-Based Deterministic Business Insights */}
      {insights.length > 0 && (
        <div className="card" style={{ marginBottom: '28px', background: 'linear-gradient(135deg, #07132e 0%, #0d214d 100%)', color: '#fff', border: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#38bdf8', fontSize: '0.84rem', fontWeight: 800, letterSpacing: '0.08em' }}>
              <Sparkles size={18} /> RULE-BASED BUSINESS INTELLIGENCE
            </div>
            <span style={{ fontSize: '0.74rem', color: '#94a3b8' }}>Deterministically computed from active PostgreSQL records</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {insights.map((ins, i) => (
              <div
                key={i}
                style={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '10px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '8px'
                }}
              >
                <div>
                  <h4 style={{ fontSize: '0.92rem', color: '#ffffff', marginBottom: '4px' }}>{ins.title}</h4>
                  <p style={{ fontSize: '0.8rem', color: '#94a3b8', lineHeight: 1.4 }}>{ins.message}</p>
                </div>
                <button
                  onClick={() => {
                    if (ins.action_link.includes('requirements')) setActiveTab('requirements');
                    else if (ins.action_link.includes('handover')) setActiveTab('handover');
                    else if (ins.action_link.includes('projects')) setActiveTab('projects');
                    else setActiveTab('enquiries');
                  }}
                  style={{
                    alignSelf: 'flex-start',
                    background: 'transparent',
                    border: 0,
                    color: '#38bdf8',
                    fontSize: '0.78rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  {ins.action_label} &rarr;
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Visual Analytics Charts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '24px' }}>
        {/* Funnel Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Enquiry to Handover Conversion Funnel</h3>
            <span className="badge badge-new">Real Pipeline</span>
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            <canvas ref={funnelChartRef} />
          </div>
        </div>

        {/* Services Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Demand by Service Offering</h3>
            <span className="badge badge-gray">{period.replace('_', ' ')}</span>
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            <canvas ref={servicesChartRef} />
          </div>
        </div>

        {/* Financial Flow Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Financial Flow &amp; Reconciled Revenue</h3>
            <span className="badge badge-qualified">Verified Invoices</span>
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            <canvas ref={financialsChartRef} />
          </div>
        </div>

        {/* Rejection Reasons */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Lead Disqualification Analysis</h3>
            <span className="badge badge-rejected">Audit Protected</span>
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            <canvas ref={rejectionsChartRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

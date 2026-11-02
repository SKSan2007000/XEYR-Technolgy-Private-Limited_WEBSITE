import React, { useEffect, useState } from 'react';
import { NotificationItem } from '../../types';
import { systemApi } from '../../services/api';
import { ActiveTab } from '../layout/Sidebar';
import { Bell, Check, CheckCheck, RefreshCw, AlertCircle, Info, ExternalLink } from 'lucide-react';

interface NotificationsViewProps {
  setActiveTab: (tab: ActiveTab) => void;
  onRefreshUnread: () => void;
}

export const NotificationsView: React.FC<NotificationsViewProps> = ({ setActiveTab, onRefreshUnread }) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await systemApi.getNotifications();
      setNotifications(data);
      onRefreshUnread();
    } catch (err: any) {
      setError(err.message || 'Failed to fetch notifications.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await systemApi.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      onRefreshUnread();
    } catch (err: any) {
      alert('Error: ' + err.message);
    }
  };

  const handleMarkAllRead = async () => {
    const unread = notifications.filter((n) => !n.is_read);
    for (const item of unread) {
      try {
        await systemApi.markNotificationRead(item.id);
      } catch {}
    }
    await fetchNotifications();
  };

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 800 }}>Security &amp; Pipeline Notifications</h3>
            <p style={{ fontSize: '0.82rem', color: '#64748b' }}>
              Real-time audit alerts for new enquiries, registrations, and system triggers.
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={handleMarkAllRead} className="btn btn-secondary btn-sm">
              <CheckCheck size={14} /> Mark All Read
            </button>
            <button onClick={fetchNotifications} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading notifications...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : notifications.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <Bell size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Notifications</h3>
          <p style={{ fontSize: '0.85rem' }}>You're all caught up with business operations.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {notifications.map((n) => (
            <div
              key={n.id}
              className="card"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '16px 20px',
                background: n.is_read ? '#ffffff' : '#f0f9ff',
                borderColor: n.is_read ? '#e2e8f0' : '#bae6fd'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: n.is_read ? '#f1f5f9' : '#1465f4',
                  color: n.is_read ? '#64748b' : '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  <Info size={18} />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                    <strong style={{ fontSize: '0.92rem', color: '#0f172a' }}>{n.title}</strong>
                    {!n.is_read && <span className="badge badge-new" style={{ fontSize: '0.65rem' }}>NEW</span>}
                  </div>
                  <p style={{ fontSize: '0.84rem', color: '#475569', marginBottom: '4px' }}>{n.message}</p>
                  <small style={{ color: '#94a3b8', fontSize: '0.74rem' }}>
                    {new Date(n.created_at).toLocaleString('en-IN')}
                  </small>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {!n.is_read && (
                  <button
                    onClick={() => handleMarkAsRead(n.id)}
                    className="btn btn-secondary btn-sm"
                    title="Mark as read"
                  >
                    <Check size={14} /> Read
                  </button>
                )}
                {n.link && (
                  <button
                    onClick={() => {
                      if (n.link?.includes('enquiries')) setActiveTab('enquiries');
                      else if (n.link?.includes('requirements')) setActiveTab('requirements');
                      else if (n.link?.includes('events')) setActiveTab('events');
                      else if (n.link?.includes('projects')) setActiveTab('projects');
                    }}
                    className="btn btn-primary btn-sm"
                  >
                    View <ExternalLink size={12} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

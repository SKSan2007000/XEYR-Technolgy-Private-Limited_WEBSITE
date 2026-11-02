import React, { useEffect, useState } from 'react';
import { EventRegistration, EventListing } from '../../types';
import { eventsApi } from '../../services/api';
import {
  Users,
  Download,
  Filter,
  RefreshCw,
  Mail,
  Phone,
  Building,
  CheckCircle2,
  Clock,
  IndianRupee
} from 'lucide-react';

interface RegistrationsViewProps {
  searchQuery?: string;
}

export const RegistrationsView: React.FC<RegistrationsViewProps> = ({ searchQuery = '' }) => {
  const [registrations, setRegistrations] = useState<EventRegistration[]>([]);
  const [events, setEvents] = useState<EventListing[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRegistrations = async () => {
    setLoading(true);
    setError(null);
    try {
      const [regs, evList] = await Promise.all([
        eventsApi.getRegistrations({
          event_id: selectedEventId ? Number(selectedEventId) : undefined,
          status: selectedStatus || undefined
        }),
        eventsApi.getEvents().catch(() => [])
      ]);
      setRegistrations(regs);
      setEvents(evList);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch event registrations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegistrations();
  }, [selectedEventId, selectedStatus]);

  const filtered = registrations.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.registration_reference?.toLowerCase().includes(q) ||
      item.full_name?.toLowerCase().includes(q) ||
      item.email?.toLowerCase().includes(q) ||
      item.event_name?.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Filter size={16} color="#64748b" />
              <span style={{ fontSize: '0.84rem', fontWeight: 700 }}>Filter by Event:</span>
              <select
                className="form-select"
                value={selectedEventId}
                onChange={(e) => setSelectedEventId(e.target.value)}
                style={{ width: 'auto', padding: '6px 12px', fontSize: '0.82rem' }}
              >
                <option value="">All Events</option>
                {events.map((ev) => (
                  <option key={ev.id} value={ev.id}>{ev.title}</option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '0.84rem', fontWeight: 700 }}>Status:</span>
              <select
                className="form-select"
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                style={{ width: 'auto', padding: '6px 12px', fontSize: '0.82rem' }}
              >
                <option value="">All Statuses</option>
                <option value="CONFIRMED">Confirmed</option>
                <option value="PENDING">Pending</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            {selectedEventId && (
              <a
                href={eventsApi.getRegistrationsCsvUrl(Number(selectedEventId))}
                className="btn btn-secondary btn-sm"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Download size={14} /> Export CSV
              </a>
            )}
            <button onClick={fetchRegistrations} className="btn btn-secondary btn-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading registrations...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>{error}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <Users size={40} color="#cbd5e1" style={{ margin: '0 auto 10px' }} />
          <h3>No Registrations Recorded</h3>
          <p style={{ fontSize: '0.85rem' }}>Participant signups for public events will appear here.</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Registration Ref</th>
                <th>Attendee &amp; College</th>
                <th>Event Title</th>
                <th>Registration Status</th>
                <th>Payment Status</th>
                <th>Fee Paid</th>
                <th>Registered Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.id}>
                  <td>
                    <strong style={{ color: '#1465f4' }}>{r.registration_reference}</strong>
                  </td>
                  <td>
                    <div style={{ fontWeight: 700 }}>{r.full_name}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      {r.company_or_college ? `${r.company_or_college} • ` : ''}{r.email} • {r.phone}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, fontSize: '0.84rem' }}>{r.event_name || 'Event'}</div>
                  </td>
                  <td>
                    <span className={`badge ${r.registration_status === 'CONFIRMED' ? 'badge-qualified' : 'badge-pending'}`}>
                      {r.registration_status}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${r.payment_status === 'PAID' ? 'badge-qualified' : r.payment_status === 'FAILED' ? 'badge-rejected' : 'badge-gray'}`}>
                      {r.payment_status}
                    </span>
                  </td>
                  <td>
                    <strong>₹{Number(r.fee_paid || 0).toLocaleString('en-IN')}</strong>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.82rem' }}>
                      {new Date(r.created_at).toLocaleDateString('en-IN', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

import React, { useEffect, useState } from 'react';
import { EventListing, EventFormField, CertificateTemplate, EventCertificate, EventRegistration } from '../../types';
import { eventsApi, subscribersApi, certificateTemplatesApi, certificatesApi, portalSharingApi } from '../../services/api';
import {
  CalendarDays,
  Plus,
  RefreshCw,
  Edit,
  Trash2,
  Send,
  Eye,
  Sliders,
  CheckCircle,
  MapPin,
  Clock,
  IndianRupee,
  XCircle,
  AlertCircle,
  Users,
  Mail,
  ShieldCheck,
  Award,
  QrCode,
  Share2,
  Copy,
  ExternalLink,
  Download,
  Check,
  FileText,
  Upload,
  Globe,
  ToggleLeft,
  ToggleRight,
  BookOpen,
  UserCheck
} from 'lucide-react';

interface EventsViewProps {
  searchQuery?: string;
}

export const EventsView: React.FC<EventsViewProps> = ({ searchQuery = '' }) => {
  const [events, setEvents] = useState<EventListing[]>([]);
  const [tab, setTab] = useState<'upcoming' | 'completed' | 'cancelled' | 'draft' | 'all' | 'subscribers'>('upcoming');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Portal Sharing & QR Modal State
  const [portalShareModal, setPortalShareModal] = useState(false);
  const [portalSharingInfo, setPortalSharingInfo] = useState<{
    canonical_events_portal_url: string;
    share_title: string;
    share_description: string;
    share_links: { whatsapp: string; linkedin: string; twitter: string; email: string };
  } | null>(null);
  const [portalQrDataUri, setPortalQrDataUri] = useState<string | null>(null);
  const [portalCopied, setPortalCopied] = useState(false);
  const [portalLoading, setPortalLoading] = useState(false);

  // Certificate templates repository
  const [availableTemplates, setAvailableTemplates] = useState<CertificateTemplate[]>([]);

  // Event certificate eligibility state in form
  const [selectedTemplateRef, setSelectedTemplateRef] = useState<number | ''>('');
  const [certRequireAttendance, setCertRequireAttendance] = useState(true);
  const [certMinAttendance, setCertMinAttendance] = useState<number>(75);
  const [certRequireFeedback, setCertRequireFeedback] = useState(false);
  const [certRequireActivities, setCertRequireActivities] = useState(false);
  const [certActivitiesDesc, setCertActivitiesDesc] = useState('');
  const [certReleaseDate, setCertReleaseDate] = useState('');
  const [feedbackEnabled, setFeedbackEnabled] = useState(true);

  // Certificate Management modal per event
  const [certModalEvent, setCertModalEvent] = useState<EventListing | null>(null);
  const [certModalData, setCertModalData] = useState<{
    event_id: number;
    event_title: string;
    certificate_enabled: boolean;
    certificate_template: string;
    issued_count: number;
    issued_certificates: EventCertificate[];
    pending_eligible: Array<{
      registration_id: number;
      registration_reference: string;
      full_name: string;
      email: string;
      phone: string;
      is_eligible: boolean;
      reasons: string[];
    }>;
  } | null>(null);
  const [certModalLoading, setCertModalLoading] = useState(false);
  const [certActionLoading, setCertActionLoading] = useState(false);

  // Certificate Reissue modal
  const [reissueModal, setReissueModal] = useState(false);
  const [reissueCertId, setReissueCertId] = useState('');
  const [reissueName, setReissueName] = useState('');
  const [reissueReason, setReissueReason] = useState('');
  const [reissueLoading, setReissueLoading] = useState(false);

  // Subscribers Management State
  const [subscribersData, setSubscribersData] = useState<{
    kpis: {
      total_subscribers: number;
      active_subscribers: number;
      unsubscribed_subscribers: number;
      total_deliveries: number;
      sent_deliveries: number;
      failed_deliveries: number;
    };
    subscribers: any[];
  } | null>(null);
  const [subscribersLoading, setSubscribersLoading] = useState(false);
  const [subscribersError, setSubscribersError] = useState<string | null>(null);
  const [subscribersFilterStatus, setSubscribersFilterStatus] = useState<string>('all');
  const [subscriberActionLoading, setSubscriberActionLoading] = useState<number | null>(null);

  // Event modal (create / edit)
  const [eventModal, setEventModal] = useState(false);
  const [modalActiveTab, setModalActiveTab] = useState<'basics' | 'media' | 'curriculum' | 'policies' | 'certificates'>('basics');
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [title, setTitle] = useState('');
  const [category, setCategory] = useState('TECHNICAL_WORKSHOP');
  const [organizer, setOrganizer] = useState('XEYR Technologies');
  const [eventDate, setEventDate] = useState('');
  const [startTime, setStartTime] = useState('10:00');
  const [endTime, setEndTime] = useState('13:00');
  const [locationType, setLocationType] = useState('ONLINE');
  const [venueName, setVenueName] = useState('Google Meet / Zoom');

  // Poster & Media
  const [posterUrl, setPosterUrl] = useState('');
  const [posterFile, setPosterFile] = useState<File | null>(null);
  const [posterPreview, setPosterPreview] = useState('');

  // Speaker Profile
  const [speakerName, setSpeakerName] = useState('Alex Chen');
  const [speakerRole, setSpeakerRole] = useState('Principal AI Architect');
  const [speakerCompany, setSpeakerCompany] = useState('XEYR Technologies');
  const [speakerBio, setSpeakerBio] = useState('Specializing in enterprise machine learning and distributed system architectures.');
  const [speakerPhoto, setSpeakerPhoto] = useState('https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80');

  // Descriptions
  const [summary, setSummary] = useState('');
  const [fullDescription, setFullDescription] = useState('');

  // Curriculum & Schedule
  const [topics, setTopics] = useState("Enterprise AI and System Architecture Fundamentals\nScalable Data Pipeline Design and Vector Indexing\nHands-on Production Deployment and CI/CD Automation");
  const [agenda, setAgenda] = useState("10:00 AM - 11:15 AM | Foundations & Architecture | System design patterns and high-performance pipeline architecture\n11:30 AM - 01:00 PM | Hands-on Workshop & Implementation | Interactive code lab, model deployment, and live evaluation");

  // Rules & Policies
  const [eligibility, setEligibility] = useState('Open to engineering students, software professionals, and technology enthusiasts.');
  const [guidelines, setGuidelines] = useState('A laptop with modern browser access is recommended for interactive tasks.');
  const [refundPolicy, setRefundPolicy] = useState('Free registrations may be cancelled anytime before commencement. For paid workshops, cancellation requests submitted at least 48 hours prior to start are eligible for full refund processing.');

  // Pricing & Capacity
  const [isPaid, setIsPaid] = useState(false);
  const [registrationFee, setRegistrationFee] = useState<number>(0);
  const [currency, setCurrency] = useState('INR');
  const [capacity, setCapacity] = useState<number>(100);
  const [isPublished, setIsPublished] = useState(true);
  const [eventStatus, setEventStatus] = useState('UPCOMING');
  const [actionLoading, setActionLoading] = useState(false);

  // Form Fields Builder modal
  const [fieldModalEvent, setFieldModalEvent] = useState<EventListing | null>(null);
  const [eventFields, setEventFields] = useState<EventFormField[]>([]);
  const [newFieldLabel, setNewFieldLabel] = useState('');
  const [newFieldType, setNewFieldType] = useState('text');
  const [newFieldOptions, setNewFieldOptions] = useState('');

  // Registrations Attendee View Modal
  const [regModalEvent, setRegModalEvent] = useState<EventListing | null>(null);
  const [regModalList, setRegModalList] = useState<EventRegistration[]>([]);
  const [regModalLoading, setRegModalLoading] = useState(false);

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await eventsApi.getEvents();
      setEvents(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(err.message || 'Failed to load events repository from database.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSubscribers = async () => {
    setSubscribersLoading(true);
    setSubscribersError(null);
    try {
      const data = await subscribersApi.getSubscribers({
        status: subscribersFilterStatus === 'all' ? undefined : subscribersFilterStatus,
      });
      setSubscribersData(data);
    } catch (err: any) {
      setSubscribersError(err.message || 'Failed to load subscriber list.');
    } finally {
      setSubscribersLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
    subscribersApi.getSubscribers().then(data => setSubscribersData(data)).catch(() => {});
    certificateTemplatesApi.getTemplates().then(data => setAvailableTemplates(Array.isArray(data) ? data : [])).catch(() => {});
  }, []);

  useEffect(() => {
    if (tab === 'subscribers') {
      fetchSubscribers();
    }
  }, [tab, subscribersFilterStatus]);

  const openPortalShareModal = async () => {
    setPortalShareModal(true);
    setPortalLoading(true);
    try {
      const [info, qr] = await Promise.all([
        portalSharingApi.getSharingInfo(),
        portalSharingApi.getPortalQrData()
      ]);
      setPortalSharingInfo(info);
      if (qr && qr.qr_code_data_uri) {
        setPortalQrDataUri(qr.qr_code_data_uri);
      }
    } catch (err: any) {
      console.error('Failed to load portal share info', err);
    } finally {
      setPortalLoading(false);
    }
  };

  const handleCopyPortalLink = () => {
    if (!portalSharingInfo?.canonical_events_portal_url) return;
    navigator.clipboard.writeText(portalSharingInfo.canonical_events_portal_url);
    setPortalCopied(true);
    setTimeout(() => setPortalCopied(false), 2500);
  };

  const openCertModal = async (ev: EventListing) => {
    setCertModalEvent(ev);
    setCertModalLoading(true);
    try {
      const data = await certificatesApi.getEventCertificates(ev.id);
      setCertModalData(data);
    } catch (err: any) {
      alert('Failed to load event certificates: ' + err.message);
    } finally {
      setCertModalLoading(false);
    }
  };

  const handleIssueSingleCert = async (regId: number) => {
    if (!certModalEvent) return;
    setCertActionLoading(true);
    try {
      const res = await certificatesApi.issueCertificates(certModalEvent.id, { registration_ids: [regId] });
      alert(res.message || 'Certificate issued successfully.');
      const data = await certificatesApi.getEventCertificates(certModalEvent.id);
      setCertModalData(data);
    } catch (err: any) {
      alert('Issuance failed: ' + err.message);
    } finally {
      setCertActionLoading(false);
    }
  };

  const handleIssueAllEligibleCerts = async () => {
    if (!certModalEvent) return;
    if (!confirm(`Issue certificates for all attendees meeting eligibility criteria for "${certModalEvent.title}"?`)) return;
    setCertActionLoading(true);
    try {
      const res = await certificatesApi.issueCertificates(certModalEvent.id, { issue_all_eligible: true });
      alert(res.message || 'Eligible certificates issued.');
      const data = await certificatesApi.getEventCertificates(certModalEvent.id);
      setCertModalData(data);
    } catch (err: any) {
      alert('Issuance failed: ' + err.message);
    } finally {
      setCertActionLoading(false);
    }
  };

  const handleOpenReissueModal = (cert: EventCertificate) => {
    setReissueCertId(cert.certificate_id);
    setReissueName(cert.recipient_name);
    setReissueReason('');
    setReissueModal(true);
  };

  const handleReissueSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reissueCertId || !reissueName.trim() || !reissueReason.trim()) {
      alert('Recipient name and reason for reissue are required.');
      return;
    }
    setReissueLoading(true);
    try {
      const res = await certificatesApi.reissueCertificate(reissueCertId, {
        recipient_name: reissueName.trim(),
        reissue_reason: reissueReason.trim(),
      });
      alert(res.message || 'Certificate reissued successfully.');
      setReissueModal(false);
      if (certModalEvent) {
        const data = await certificatesApi.getEventCertificates(certModalEvent.id);
        setCertModalData(data);
      }
    } catch (err: any) {
      alert('Reissue failed: ' + err.message);
    } finally {
      setReissueLoading(false);
    }
  };

  const handleRetryCertEmail = async (certId: string) => {
    try {
      const res = await certificatesApi.retryEmail(certId);
      alert(res.message || 'Email dispatch attempt finished.');
      if (certModalEvent) {
        const data = await certificatesApi.getEventCertificates(certModalEvent.id);
        setCertModalData(data);
      }
    } catch (err: any) {
      alert('Email retry failed: ' + err.message);
    }
  };

  const handleToggleSubscriberStatus = async (subscriberId: number) => {
    setSubscriberActionLoading(subscriberId);
    try {
      const res = await subscribersApi.toggleSubscriberStatus(subscriberId);
      alert(res.message || 'Subscriber status updated.');
      await fetchSubscribers();
    } catch (err: any) {
      alert('Failed to update subscriber status: ' + err.message);
    } finally {
      setSubscriberActionLoading(null);
    }
  };

  const handleRetryDelivery = async (deliveryId: number) => {
    try {
      const res = await subscribersApi.retryDelivery(deliveryId);
      alert(res.message || 'Delivery attempt completed.');
      await fetchSubscribers();
    } catch (err: any) {
      alert('Retry delivery error: ' + err.message);
    }
  };

  // Open Registrations View Modal for a Specific Event
  const openRegistrationsModal = async (ev: EventListing) => {
    setRegModalEvent(ev);
    setRegModalLoading(true);
    try {
      const data = await eventsApi.getRegistrations({ event_id: ev.id });
      setRegModalList(Array.isArray(data) ? data : []);
    } catch (err: any) {
      alert('Failed to load event registrations: ' + err.message);
    } finally {
      setRegModalLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingEventId(null);
    setModalActiveTab('basics');
    setTitle('');
    setCategory('TECHNICAL_WORKSHOP');
    setOrganizer('XEYR Technologies');
    setEventDate('');
    setStartTime('10:00');
    setEndTime('13:00');
    setLocationType('ONLINE');
    setVenueName('Google Meet / Zoom');

    setPosterUrl('');
    setPosterFile(null);
    setPosterPreview('https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=900&q=80');

    setSpeakerName('Alex Chen');
    setSpeakerRole('Principal AI Architect');
    setSpeakerCompany('XEYR Technologies');
    setSpeakerBio('Specializing in enterprise machine learning and distributed system architectures.');
    setSpeakerPhoto('https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=400&q=80');

    setSummary('');
    setFullDescription('');
    setTopics("Enterprise AI and System Architecture Fundamentals\nScalable Data Pipeline Design and Vector Indexing\nHands-on Production Deployment and CI/CD Automation");
    setAgenda("10:00 AM - 11:15 AM | Foundations & Architecture | System design patterns and high-performance pipeline architecture\n11:30 AM - 01:00 PM | Hands-on Workshop & Implementation | Interactive code lab, model deployment, and live evaluation");

    setEligibility('Open to engineering students, software professionals, and technology enthusiasts.');
    setGuidelines('A laptop with modern browser access is recommended for interactive tasks.');
    setRefundPolicy('Free registrations may be cancelled anytime before commencement. For paid workshops, cancellation requests submitted at least 48 hours prior to start are eligible for full refund processing.');

    setIsPaid(false);
    setRegistrationFee(0);
    setCurrency('INR');
    setCapacity(100);
    setIsPublished(true);
    setEventStatus('UPCOMING');

    setSelectedTemplateRef('');
    setCertRequireAttendance(true);
    setCertMinAttendance(75);
    setCertRequireFeedback(false);
    setCertRequireActivities(false);
    setCertActivitiesDesc('');
    setCertReleaseDate('');
    setFeedbackEnabled(true);

    setEventModal(true);
  };

  const openEditModal = (ev: EventListing) => {
    setEditingEventId(ev.id);
    setModalActiveTab('basics');
    setTitle(ev.title || '');
    setCategory(ev.category || (ev as any).event_type || 'TECHNICAL_WORKSHOP');
    setOrganizer((ev as any).organizer || 'XEYR Technologies');
    setEventDate(ev.event_date || '');
    setStartTime(ev.start_time || '');
    setEndTime(ev.end_time || '');
    setLocationType(ev.location_type || (ev as any).mode || 'ONLINE');
    setVenueName(ev.venue_name || (ev as any).venue || '');

    const fee = Number(ev.registration_fee ?? (ev as any).fee_amount ?? 0);
    setIsPaid(fee > 0 || (ev as any).is_paid === true);
    setRegistrationFee(fee);
    setCurrency((ev as any).currency || 'INR');
    setCapacity(ev.capacity ?? (ev as any).max_participants ?? 100);
    setIsPublished(Boolean(ev.is_published));
    setEventStatus(ev.status || 'UPCOMING');

    const pUrl = (ev as any).poster_url || (typeof (ev as any).poster === 'string' ? (ev as any).poster : '');
    setPosterUrl(pUrl);
    setPosterFile(null);
    setPosterPreview(pUrl || 'https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=900&q=80');

    setSummary(ev.short_summary || (ev as any).short_description || '');
    setFullDescription((ev as any).full_description || (ev as any).description || '');

    if (Array.isArray((ev as any).mentors) && (ev as any).mentors.length > 0) {
      const m = (ev as any).mentors[0];
      setSpeakerName(m.name || 'Lead Instructor');
      setSpeakerRole(m.role || 'Technical Mentor');
      setSpeakerCompany(m.company || 'XEYR Technologies');
      setSpeakerBio(m.bio || '');
      setSpeakerPhoto(m.photo || m.image || '');
    } else {
      setSpeakerName('Alex Chen');
      setSpeakerRole('Principal AI Architect');
      setSpeakerCompany('XEYR Technologies');
      setSpeakerBio('');
      setSpeakerPhoto('');
    }

    if (Array.isArray((ev as any).learning_outcomes) && (ev as any).learning_outcomes.length > 0) {
      setTopics((ev as any).learning_outcomes.join('\n'));
    } else {
      setTopics('');
    }

    if (Array.isArray((ev as any).schedule) && (ev as any).schedule.length > 0) {
      setAgenda((ev as any).schedule.map((s: any) => `${s.time || ''} | ${s.title || s.session || ''} | ${s.description || ''}`).join('\n'));
    } else {
      setAgenda('');
    }

    setEligibility((ev as any).eligibility || '');
    setGuidelines((ev as any).guidelines || '');
    setRefundPolicy((ev as any).refund_policy || 'Free event registrations may be cancelled anytime before commencement. For paid workshops, cancellation requests submitted at least 48 hours prior to start are eligible for full refund processing.');

    setSelectedTemplateRef(ev.certificate_template_ref || '');
    setCertRequireAttendance(Boolean(ev.certificate_require_attendance ?? true));
    setCertMinAttendance(ev.certificate_min_attendance ?? 75);
    setCertRequireFeedback(Boolean(ev.certificate_require_feedback ?? false));
    setCertRequireActivities(Boolean(ev.certificate_require_activities ?? false));
    setCertActivitiesDesc(ev.certificate_activities_description || '');
    setCertReleaseDate(ev.certificate_release_date ? ev.certificate_release_date.slice(0, 16) : '');
    setFeedbackEnabled(Boolean(ev.feedback_enabled ?? true));

    setEventModal(true);
  };

  const handlePosterFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setPosterFile(file);
      const objectUrl = URL.createObjectURL(file);
      setPosterPreview(objectUrl);
    }
  };

  const executeEventSave = async (publishedState: boolean, targetStatus: string) => {
    if (!title.trim()) {
      alert('Event title is required.');
      return;
    }
    setActionLoading(true);
    try {
      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('event_type', category);
      formData.append('category', category);
      formData.append('organizer', organizer.trim() || 'XEYR Technologies');

      if (eventDate) formData.append('event_date', eventDate);
      if (startTime) formData.append('start_time', startTime);
      if (endTime) formData.append('end_time', endTime);
      formData.append('mode', locationType);
      formData.append('location_type', locationType);
      formData.append('venue', venueName || 'Online');
      formData.append('venue_name', venueName || 'Online');

      // Poster
      if (posterFile) {
        formData.append('poster', posterFile);
      }
      if (posterUrl) {
        formData.append('poster_url', posterUrl.trim());
      }

      // Pricing & Capacity
      const finalFee = isPaid ? registrationFee : 0;
      formData.append('is_paid', String(isPaid));
      formData.append('fee_amount', String(finalFee));
      formData.append('registration_fee', String(finalFee));
      formData.append('currency', currency || 'INR');
      formData.append('max_participants', String(capacity));
      formData.append('capacity', String(capacity));

      // Publishing state
      formData.append('is_published', String(publishedState));
      formData.append('status', targetStatus);

      // Descriptions
      formData.append('short_description', summary);
      formData.append('short_summary', summary);
      formData.append('description', summary);
      if (fullDescription) {
        formData.append('full_description', fullDescription);
      }

      // Rules & Policies
      if (eligibility) formData.append('eligibility', eligibility);
      if (guidelines) formData.append('guidelines', guidelines);
      if (refundPolicy) formData.append('refund_policy', refundPolicy);

      // Speaker Profile
      const mentorsList = [{
        name: speakerName.trim() || organizer || 'Lead Mentor',
        role: speakerRole.trim() || 'Technical Instructor',
        company: speakerCompany.trim() || organizer || 'XEYR Technologies',
        bio: speakerBio.trim(),
        photo: speakerPhoto.trim()
      }];
      formData.append('mentors', JSON.stringify(mentorsList));

      // Topics Covered / Learning Outcomes
      const outcomesList = topics
        .split('\n')
        .map(t => t.trim())
        .filter(Boolean);
      formData.append('learning_outcomes', JSON.stringify(outcomesList));

      // Agenda / Schedule
      const scheduleList = agenda
        .split('\n')
        .map(line => line.trim())
        .filter(Boolean)
        .map((line, idx) => {
          const parts = line.split('|').map(p => p.trim());
          if (parts.length >= 3) {
            return { time: parts[0], title: parts[1], description: parts[2] };
          } else if (parts.length === 2) {
            return { time: parts[0], title: parts[1], description: '' };
          }
          return { time: `Session ${idx + 1}`, title: line, description: '' };
        });
      formData.append('schedule', JSON.stringify(scheduleList));

      // Certificates configuration
      if (selectedTemplateRef) {
        formData.append('certificate_template_ref', String(selectedTemplateRef));
        formData.append('certificate_enabled', 'true');
      } else {
        formData.append('certificate_enabled', 'false');
      }
      formData.append('certificate_require_attendance', String(certRequireAttendance));
      formData.append('certificate_min_attendance', String(certMinAttendance));
      formData.append('certificate_require_feedback', String(certRequireFeedback));
      formData.append('certificate_require_activities', String(certRequireActivities));
      if (certActivitiesDesc) formData.append('certificate_activities_description', certActivitiesDesc);
      if (certReleaseDate) formData.append('certificate_release_date', certReleaseDate);
      formData.append('feedback_enabled', String(feedbackEnabled));

      if (editingEventId) {
        await eventsApi.updateEvent(editingEventId, formData);
        alert('Event updated successfully in database.');
      } else {
        await eventsApi.createEvent(formData);
        alert('Event created successfully in database.');
      }
      setEventModal(false);
      await fetchEvents();
    } catch (err: any) {
      alert('Event save failed: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteEvent = async (id: number) => {
    if (!confirm('Are you sure you want to archive this event?')) return;
    try {
      await eventsApi.deleteEvent(id);
      await fetchEvents();
    } catch (err: any) {
      alert('Archive failed: ' + err.message);
    }
  };

  const handleTogglePublish = async (ev: EventListing) => {
    const willPublish = !ev.is_published;
    try {
      const formData = new FormData();
      formData.append('is_published', String(willPublish));
      if (willPublish) {
        formData.append('status', 'UPCOMING');
      } else {
        formData.append('status', 'DRAFT');
      }
      await eventsApi.updateEvent(ev.id, formData);
      await fetchEvents();
    } catch (err: any) {
      alert('Publication toggle failed: ' + err.message);
    }
  };

  const handleStatusChange = async (ev: EventListing, newStatus: string) => {
    try {
      const formData = new FormData();
      formData.append('status', newStatus);
      if (newStatus === 'CANCELLED') {
        formData.append('is_published', 'false');
      }
      await eventsApi.updateEvent(ev.id, formData);
      await fetchEvents();
    } catch (err: any) {
      alert('Status update failed: ' + err.message);
    }
  };

  const handleNotifySubscribers = async (eventId: number, eventTitle: string) => {
    if (!confirm(`Dispatch broadcast email notification for "${eventTitle}" to all verified subscribers?`)) return;
    setActionLoading(true);
    try {
      const res = await eventsApi.notifySubscribers(eventId);
      if (res.unconfigured) {
        alert(`Notice: ${res.message}\nTotal eligible subscribers: ${res.total_subscribers}.\n(SMTP credentials must be configured in environment for external dispatch).`);
      } else {
        alert(res.message || `Notification broadcast completed: ${res.sent_count || 0} sent, ${res.failed_count || 0} failed.`);
      }
      if (tab === 'subscribers') {
        await fetchSubscribers();
      }
    } catch (err: any) {
      alert('Notification broadcast error: ' + err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // Form Fields Builder
  const openFieldBuilder = async (ev: EventListing) => {
    setFieldModalEvent(ev);
    try {
      const fields = await eventsApi.getFields(ev.id);
      setEventFields(Array.isArray(fields) ? fields : []);
    } catch {
      setEventFields([]);
    }
  };

  const handleAddFieldSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fieldModalEvent || !newFieldLabel.trim()) return;
    try {
      await eventsApi.addField(fieldModalEvent.id, {
        field_label: newFieldLabel.trim(),
        field_type: newFieldType,
        options: newFieldOptions.trim(),
        is_required: true
      });
      setNewFieldLabel('');
      setNewFieldOptions('');
      const fields = await eventsApi.getFields(fieldModalEvent.id);
      setEventFields(Array.isArray(fields) ? fields : []);
    } catch (err: any) {
      alert('Failed to add custom field: ' + err.message);
    }
  };

  const handleDeleteField = async (fieldId: number) => {
    if (!confirm('Delete this custom question?')) return;
    try {
      await eventsApi.deleteField(fieldId);
      if (fieldModalEvent) {
        const fields = await eventsApi.getFields(fieldModalEvent.id);
        setEventFields(Array.isArray(fields) ? fields : []);
      }
    } catch (err: any) {
      alert('Delete field error: ' + err.message);
    }
  };

  const now = new Date();
  const todayStr = now.toISOString().slice(0, 10);

  const cancelledEvents = events.filter((ev) => ev.status === 'CANCELLED');
  const draftEvents = events.filter((ev) => ev.status === 'DRAFT' || !ev.is_published);
  const completedEvents = events.filter((ev) => {
    if (ev.status === 'CANCELLED' || ev.status === 'DRAFT') return false;
    if (ev.status === 'COMPLETED') return true;
    if (ev.event_date && ev.event_date < todayStr && ev.status !== 'UPCOMING') return true;
    return false;
  });
  const upcomingEvents = events.filter((ev) => {
    if (ev.status === 'CANCELLED' || ev.status === 'COMPLETED' || ev.status === 'ARCHIVED') return false;
    if (ev.status === 'UPCOMING' || ev.status === 'PUBLISHED' || ev.status === 'ONGOING') return true;
    if (ev.event_date && ev.event_date >= todayStr) return true;
    if (!ev.event_date && ev.is_published) return true;
    return false;
  });

  const getActiveTabEvents = () => {
    switch (tab) {
      case 'upcoming':
        return upcomingEvents;
      case 'completed':
        return completedEvents;
      case 'cancelled':
        return cancelledEvents;
      case 'draft':
        return draftEvents;
      case 'all':
      default:
        return events;
    }
  };

  const displayedEvents = getActiveTabEvents().filter((ev) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const titleMatch = ev.title?.toLowerCase().includes(q);
    const catMatch = (ev.category || (ev as any).event_type || '')?.toLowerCase().includes(q);
    const venueMatch = (ev.venue_name || (ev as any).venue || '')?.toLowerCase().includes(q);
    return Boolean(titleMatch || catMatch || venueMatch);
  });

  const renderSubscribersContent = () => {
    const kpis = subscribersData?.kpis || {
      total_subscribers: 0,
      active_subscribers: 0,
      unsubscribed_subscribers: 0,
      total_deliveries: 0,
      sent_deliveries: 0,
      failed_deliveries: 0,
    };
    const subsList = subscribersData?.subscribers || [];

    const filteredSubs = subsList.filter((s) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        s.full_name?.toLowerCase().includes(q) ||
        s.email?.toLowerCase().includes(q) ||
        s.categories_of_interest?.toLowerCase().includes(q)
      );
    });

    return (
      <div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
          <div className="card" style={{ padding: '16px 20px', background: '#f8fafc' }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>TOTAL SUBSCRIBERS</span>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
              {kpis.total_subscribers}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#059669', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
              <ShieldCheck size={12} /> Explicit consent recorded
            </span>
          </div>

          <div className="card" style={{ padding: '16px 20px', background: '#f8fafc' }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>ACTIVE RECIPIENTS</span>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#1465f4', marginTop: '4px' }}>
              {kpis.active_subscribers}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
              Eligible for announcements
            </span>
          </div>

          <div className="card" style={{ padding: '16px 20px', background: '#f8fafc' }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>UNSUBSCRIBED</span>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#64748b', marginTop: '4px' }}>
              {kpis.unsubscribed_subscribers}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '4px', display: 'block' }}>
              Self-service or admin opted out
            </span>
          </div>

          <div className="card" style={{ padding: '16px 20px', background: '#f8fafc' }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>DELIVERIES (SENT / FAILED)</span>
            <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#0f172a', marginTop: '4px' }}>
              {kpis.sent_deliveries} <span style={{ fontSize: '1rem', color: '#94a3b8' }}>/ {kpis.failed_deliveries}</span>
            </div>
            <span style={{ fontSize: '0.75rem', color: kpis.failed_deliveries > 0 ? '#dc2626' : '#64748b', marginTop: '4px', display: 'block' }}>
              Total attempts: {kpis.total_deliveries}
            </span>
          </div>
        </div>

        <div className="card" style={{ marginBottom: '16px', padding: '12px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#475569' }}>Filter by Status:</span>
            <select
              className="form-select"
              style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
              value={subscribersFilterStatus}
              onChange={(e) => setSubscribersFilterStatus(e.target.value)}
            >
              <option value="all">All Subscribers ({kpis.total_subscribers})</option>
              <option value="active">Active Only ({kpis.active_subscribers})</option>
              <option value="unsubscribed">Unsubscribed Only ({kpis.unsubscribed_subscribers})</option>
            </select>
          </div>

          <button onClick={fetchSubscribers} className="btn btn-secondary btn-sm" disabled={subscribersLoading}>
            <RefreshCw size={14} className={subscribersLoading ? 'spin' : ''} /> Refresh List
          </button>
        </div>

        {subscribersLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
            <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
            Loading verified subscriber repository...
          </div>
        ) : subscribersError ? (
          <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <AlertCircle size={20} color="#ef4444" />
              <strong>Error Loading Subscribers</strong>
            </div>
            <p style={{ margin: 0, fontSize: '0.88rem' }}>{subscribersError}</p>
          </div>
        ) : filteredSubs.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
            No subscribers matching current filter.
          </div>
        ) : (
          <div className="card" style={{ overflowX: 'auto', padding: 0 }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.86rem' }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                  <th style={{ padding: '12px 16px' }}>Subscriber</th>
                  <th style={{ padding: '12px 16px' }}>Interest Categories</th>
                  <th style={{ padding: '12px 16px' }}>Status</th>
                  <th style={{ padding: '12px 16px' }}>Deliveries</th>
                  <th style={{ padding: '12px 16px' }}>Subscribed On</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSubs.map((sub: any) => (
                  <tr key={sub.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>{sub.full_name}</div>
                      <div style={{ color: '#64748b', fontSize: '0.78rem' }}>{sub.email}</div>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className="badge badge-gray">{sub.categories_of_interest || 'All Events'}</span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`badge ${sub.is_active ? 'badge-qualified' : 'badge-rejected'}`}>
                        {sub.is_active ? 'Active' : 'Unsubscribed'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{ fontSize: '0.82rem', fontWeight: 600 }}>{sub.delivery_count || 0}</span>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '0.8rem' }}>
                      {sub.subscribed_at ? new Date(sub.subscribed_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <button
                        onClick={() => handleToggleSubscriberStatus(sub.id)}
                        className="btn btn-secondary btn-sm"
                        disabled={subscriberActionLoading === sub.id}
                      >
                        {sub.is_active ? 'Deactivate' : 'Activate'}
                      </button>
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

  return (
    <div>
      {/* Top Header Card */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '14px' }}>
          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setTab('upcoming')}
              className={`btn btn-sm ${tab === 'upcoming' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Upcoming ({upcomingEvents.length})
            </button>
            <button
              onClick={() => setTab('completed')}
              className={`btn btn-sm ${tab === 'completed' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Completed ({completedEvents.length})
            </button>
            <button
              onClick={() => setTab('cancelled')}
              className={`btn btn-sm ${tab === 'cancelled' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Cancelled ({cancelledEvents.length})
            </button>
            <button
              onClick={() => setTab('draft')}
              className={`btn btn-sm ${tab === 'draft' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Drafts ({draftEvents.length})
            </button>
            <button
              onClick={() => setTab('all')}
              className={`btn btn-sm ${tab === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            >
              All Events ({events.length})
            </button>
            <button
              onClick={() => setTab('subscribers')}
              className={`btn btn-sm ${tab === 'subscribers' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ display: 'flex', alignItems: 'center', gap: '5px' }}
            >
              <Users size={14} /> Subscribers ({subscribersData?.kpis?.total_subscribers ?? '...'})
            </button>
          </div>

          {/* Quick Actions */}
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={openCreateModal} className="btn btn-primary btn-sm" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Plus size={14} /> Schedule New Event
            </button>
            <button onClick={openPortalShareModal} className="btn btn-secondary btn-sm" title="Share public events portal">
              <Share2 size={14} /> Share Portal
            </button>
            <button onClick={fetchEvents} className="btn btn-secondary btn-sm" title="Refresh database records">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>
      </div>

      {tab === 'subscribers' ? (
        renderSubscribersContent()
      ) : loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
          <RefreshCw size={24} className="spin" style={{ margin: '0 auto 10px', animation: 'spin 1s linear infinite' }} />
          Loading events repository from database...
        </div>
      ) : error ? (
        <div className="card" style={{ color: '#ef4444', background: '#fef2f2', padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <AlertCircle size={20} color="#ef4444" />
            <strong>API Query Failure</strong>
          </div>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>{error}</p>
          <button onClick={fetchEvents} className="btn btn-primary btn-sm" style={{ marginTop: '14px' }}>
            <RefreshCw size={14} /> Retry Query
          </button>
        </div>
      ) : displayedEvents.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px', color: '#64748b' }}>
          <CalendarDays size={48} color="#cbd5e1" style={{ margin: '0 auto 14px' }} />
          <h3 style={{ fontSize: '1.15rem', color: '#1e293b', marginBottom: '6px' }}>No records yet</h3>
          <p style={{ fontSize: '0.88rem', maxWidth: '420px', margin: '0 auto 18px' }}>
            {tab === 'all'
              ? 'Create your first event to get started.'
              : `No events currently match the "${tab}" status category.`}
          </p>
          <button onClick={openCreateModal} className="btn btn-primary btn-sm">
            <Plus size={14} /> Create Your First Event
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          {displayedEvents.map((ev) => {
            const rawCat = ev.category || (ev as any).event_type || 'WORKSHOP';
            const catLabel = String(rawCat).replace(/_/g, ' ');
            const venue = ev.venue_name || (ev as any).venue || 'Online';
            const locType = ev.location_type || (ev as any).mode || 'Online';
            const fee = Number(ev.registration_fee ?? (ev as any).fee_amount ?? 0);
            const cap = ev.capacity ?? (ev as any).max_participants ?? 100;
            const desc = ev.short_summary || (ev as any).short_description || 'No description provided.';
            const confirmedCount = (ev as any).confirmed_count || 0;
            const posterImg = (ev as any).poster || (ev as any).poster_url;

            const isCancelled = ev.status === 'CANCELLED';
            const isCompleted = ev.status === 'COMPLETED';

            return (
              <div key={ev.id} className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', opacity: isCancelled ? 0.75 : 1, padding: 0, overflow: 'hidden' }}>
                {/* Event Poster Header */}
                {posterImg && (
                  <div style={{ height: '140px', backgroundImage: `url('${posterImg}')`, backgroundSize: 'cover', backgroundPosition: 'center', position: 'relative' }}>
                    <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.7))' }} />
                    <span style={{ position: 'absolute', top: 12, left: 12, background: 'rgba(255,255,255,0.95)', color: '#0f172a', fontWeight: 800, fontSize: '0.72rem', padding: '3px 8px', borderRadius: 4, letterSpacing: '0.05em' }}>
                      {catLabel.toUpperCase()}
                    </span>
                    <span style={{ position: 'absolute', top: 12, right: 12, background: ev.is_published ? '#059669' : '#64748b', color: '#fff', fontWeight: 700, fontSize: '0.7rem', padding: '3px 8px', borderRadius: 4 }}>
                      {ev.is_published ? '● Published' : '○ Draft'}
                    </span>
                  </div>
                )}

                <div style={{ padding: '16px 20px', flex: 1 }}>
                  {!posterImg && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '6px' }}>
                      <span className="badge badge-new">{catLabel}</span>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <span className={`badge ${ev.status === 'CANCELLED' ? 'badge-rejected' : ev.status === 'COMPLETED' ? 'badge-qualified' : 'badge-pending'}`}>
                          {ev.status || 'UPCOMING'}
                        </span>
                        <span className={`badge ${ev.is_published ? 'badge-qualified' : 'badge-gray'}`}>
                          {ev.is_published ? 'Published' : 'Draft'}
                        </span>
                      </div>
                    </div>
                  )}

                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '8px', color: '#0f172a' }}>{ev.title}</h3>
                  <p style={{ fontSize: '0.84rem', color: '#64748b', lineHeight: 1.45, marginBottom: '14px' }}>
                    {desc}
                  </p>

                  <div style={{ background: '#f8fafc', padding: '12px', borderRadius: '8px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.82rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Clock size={14} color="#64748b" />
                      <span>{ev.event_date ? `${ev.event_date}` : 'Date TBA'} {ev.start_time ? `(${ev.start_time} - ${ev.end_time || 'TBA'})` : ''}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <MapPin size={14} color="#64748b" />
                      <span>{locType} • {venue}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <IndianRupee size={14} color="#059669" />
                      <strong>{fee === 0 ? 'Free Attendance' : `₹${fee.toLocaleString('en-IN')}`}</strong>
                      <span style={{ color: '#64748b' }}>• Capacity: {cap} seats</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Users size={14} color="#1465f4" />
                      <span>Confirmed Registrations: <strong>{confirmedCount}</strong></span>
                    </div>
                  </div>
                </div>

                {/* Event Card Bottom Controls */}
                <div style={{ background: '#f8fafc', borderTop: '1px solid #f1f5f9', padding: '12px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {/* Public Preview Button */}
                    <a
                      href={`/events/${ev.slug}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-secondary btn-sm"
                      title="Open public event registration page in new tab"
                      style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                      <Eye size={13} /> Preview
                    </a>

                    {/* Edit Details */}
                    <button onClick={() => openEditModal(ev)} className="btn btn-secondary btn-sm" title="Edit details">
                      <Edit size={13} /> Edit
                    </button>

                    {/* View Registrations List */}
                    <button
                      onClick={() => openRegistrationsModal(ev)}
                      className="btn btn-secondary btn-sm"
                      title="View attendee registrations & payments"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                      <UserCheck size={13} /> Attendees ({confirmedCount})
                    </button>

                    {/* Custom Form Fields */}
                    <button onClick={() => openFieldBuilder(ev)} className="btn btn-secondary btn-sm" title="Configure dynamic form questions">
                      <Sliders size={13} /> Form
                    </button>

                    {/* Certificate Management */}
                    <button onClick={() => openCertModal(ev)} className="btn btn-secondary btn-sm" title="Issue & verify certificates">
                      <Award size={13} /> Certs
                    </button>

                    {/* Publish / Unpublish Toggle */}
                    <button
                      onClick={() => handleTogglePublish(ev)}
                      className={`btn btn-sm ${ev.is_published ? 'btn-secondary' : 'btn-primary'}`}
                      title={ev.is_published ? 'Unpublish from public catalog' : 'Publish to public catalog'}
                    >
                      {ev.is_published ? 'Unpublish' : 'Publish'}
                    </button>

                    {/* Email Notify */}
                    <button
                      onClick={() => handleNotifySubscribers(ev.id, ev.title)}
                      className="btn btn-secondary btn-sm"
                      title="Send email broadcast to subscribers"
                    >
                      <Send size={13} />
                    </button>

                    {!isCancelled && !isCompleted && (
                      <button
                        onClick={() => handleStatusChange(ev, 'CANCELLED')}
                        className="btn btn-secondary btn-sm"
                        style={{ color: '#dc2626' }}
                        title="Mark event as Cancelled"
                      >
                        <XCircle size={13} />
                      </button>
                    )}
                  </div>

                  <button onClick={() => handleDeleteEvent(ev.id)} className="btn btn-danger btn-sm" title="Archive event">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* =====================================================================
          COMPREHENSIVE CREATE / EDIT EVENT MODAL
          ===================================================================== */}
      {eventModal && (
        <div className="modal-overlay" onClick={() => setEventModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(780px, 96vw)', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
            <div className="modal-header" style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
              <div>
                <span className="badge badge-new" style={{ marginBottom: 4 }}>ADMIN EVENT CMS</span>
                <h3 className="card-title" style={{ marginTop: 2 }}>{editingEventId ? 'Edit Event & Workshop' : 'Schedule New Event'}</h3>
              </div>
              <button onClick={() => setEventModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>

            {/* Modal Internal Section Tabs */}
            <div style={{ display: 'flex', gap: '4px', borderBottom: '1px solid #e2e8f0', padding: '8px 16px', background: '#f8fafc', overflowX: 'auto' }}>
              <button
                type="button"
                onClick={() => setModalActiveTab('basics')}
                className={`btn btn-sm ${modalActiveTab === 'basics' ? 'btn-primary' : 'btn-secondary'}`}
              >
                1. Basics &amp; Schedule
              </button>
              <button
                type="button"
                onClick={() => setModalActiveTab('media')}
                className={`btn btn-sm ${modalActiveTab === 'media' ? 'btn-primary' : 'btn-secondary'}`}
              >
                2. Poster &amp; Speaker
              </button>
              <button
                type="button"
                onClick={() => setModalActiveTab('curriculum')}
                className={`btn btn-sm ${modalActiveTab === 'curriculum' ? 'btn-primary' : 'btn-secondary'}`}
              >
                3. Syllabus &amp; Agenda
              </button>
              <button
                type="button"
                onClick={() => setModalActiveTab('policies')}
                className={`btn btn-sm ${modalActiveTab === 'policies' ? 'btn-primary' : 'btn-secondary'}`}
              >
                4. Guidelines &amp; Pricing
              </button>
              <button
                type="button"
                onClick={() => setModalActiveTab('certificates')}
                className={`btn btn-sm ${modalActiveTab === 'certificates' ? 'btn-primary' : 'btn-secondary'}`}
              >
                5. Certificates
              </button>
            </div>

            <div className="modal-body" style={{ overflowY: 'auto', flex: 1, padding: '20px' }}>
              {/* TAB 1: BASICS */}
              {modalActiveTab === 'basics' && (
                <div style={{ display: 'grid', gap: '14px' }}>
                  <div className="form-group">
                    <label className="form-label">Event Title *</label>
                    <input
                      type="text"
                      className="form-input"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      placeholder="e.g. Enterprise AI Systems & Full-Stack Architecture Workshop"
                      required
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                    <div className="form-group">
                      <label className="form-label">Category</label>
                      <select
                        className="form-select"
                        value={category}
                        onChange={(e) => setCategory(e.target.value)}
                      >
                        <option value="TECHNICAL_WORKSHOP">Technical Workshop</option>
                        <option value="AI_BOOTCAMP">AI Bootcamp</option>
                        <option value="SKILLBRIDGE_SEMINAR">SkillBridge College Seminar</option>
                        <option value="HACKATHON">Hackathon</option>
                        <option value="CAREER_TALK">Career Talk</option>
                        <option value="Masterclass">Masterclass</option>
                        <option value="Bootcamp">Bootcamp</option>
                        <option value="Workshop">Workshop</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Organizing Entity</label>
                      <input
                        type="text"
                        className="form-input"
                        value={organizer}
                        onChange={(e) => setOrganizer(e.target.value)}
                        placeholder="e.g. XEYR Technologies"
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                    <div className="form-group">
                      <label className="form-label">Event Date *</label>
                      <input
                        type="date"
                        className="form-input"
                        value={eventDate}
                        onChange={(e) => setEventDate(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Start Time</label>
                      <input
                        type="time"
                        className="form-input"
                        value={startTime}
                        onChange={(e) => setStartTime(e.target.value)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">End Time</label>
                      <input
                        type="time"
                        className="form-input"
                        value={endTime}
                        onChange={(e) => setEndTime(e.target.value)}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                    <div className="form-group">
                      <label className="form-label">Attendance Mode</label>
                      <select
                        className="form-select"
                        value={locationType}
                        onChange={(e) => setLocationType(e.target.value)}
                      >
                        <option value="ONLINE">Online Virtual Session</option>
                        <option value="IN_PERSON">In-Person Campus Venue</option>
                        <option value="HYBRID">Hybrid (Online + Physical)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label className="form-label">Venue / Meeting URL</label>
                      <input
                        type="text"
                        className="form-input"
                        value={venueName}
                        onChange={(e) => setVenueName(e.target.value)}
                        placeholder="Google Meet, Zoom, or Hall A Auditorium"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Short Summary (Event Card Abstract)</label>
                    <textarea
                      className="form-textarea"
                      rows={2}
                      value={summary}
                      onChange={(e) => setSummary(e.target.value)}
                      placeholder="High-level overview displayed on event cards and portal previews..."
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Full Detailed Description / Overview</label>
                    <textarea
                      className="form-textarea"
                      rows={4}
                      value={fullDescription}
                      onChange={(e) => setFullDescription(e.target.value)}
                      placeholder="Comprehensive workshop background, technical scope, objectives, and takeaway value..."
                    />
                  </div>
                </div>
              )}

              {/* TAB 2: POSTER & SPEAKER */}
              {modalActiveTab === 'media' && (
                <div style={{ display: 'grid', gap: '16px' }}>
                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px' }}>
                    <h4 style={{ margin: '0 0 12px 0', fontSize: '0.92rem', color: '#0f172a' }}>Event Poster Image</h4>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '16px', alignItems: 'center' }}>
                      <div style={{ width: '120px', height: '80px', borderRadius: '8px', border: '1px solid #cbd5e1', overflow: 'hidden', background: '#0f172a' }}>
                        {posterPreview ? (
                          <img src={posterPreview} alt="Poster Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        ) : (
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8', fontSize: '0.75rem' }}>No image</div>
                        )}
                      </div>

                      <div style={{ display: 'grid', gap: '8px' }}>
                        <div>
                          <label className="form-label" style={{ fontSize: '0.78rem' }}>Upload Poster Image</label>
                          <input type="file" accept="image/*" onChange={handlePosterFileChange} style={{ fontSize: '0.82rem' }} />
                        </div>
                        <div>
                          <label className="form-label" style={{ fontSize: '0.78rem' }}>Or Direct Poster URL</label>
                          <input
                            type="text"
                            className="form-input"
                            value={posterUrl}
                            onChange={(e) => {
                              setPosterUrl(e.target.value);
                              if (e.target.value) setPosterPreview(e.target.value);
                            }}
                            placeholder="https://images.unsplash.com/..."
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px' }}>
                    <h4 style={{ margin: '0 0 12px 0', fontSize: '0.92rem', color: '#0f172a' }}>Lead Speaker / Instructor Profile</h4>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                      <div className="form-group">
                        <label className="form-label">Speaker Name</label>
                        <input
                          type="text"
                          className="form-input"
                          value={speakerName}
                          onChange={(e) => setSpeakerName(e.target.value)}
                          placeholder="e.g. Alex Chen"
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Speaker Role / Designation</label>
                        <input
                          type="text"
                          className="form-input"
                          value={speakerRole}
                          onChange={(e) => setSpeakerRole(e.target.value)}
                          placeholder="e.g. Principal AI Architect"
                        />
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginTop: '10px' }}>
                      <div className="form-group">
                        <label className="form-label">Company / Affiliation</label>
                        <input
                          type="text"
                          className="form-input"
                          value={speakerCompany}
                          onChange={(e) => setSpeakerCompany(e.target.value)}
                          placeholder="e.g. XEYR Technologies"
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Photo URL</label>
                        <input
                          type="text"
                          className="form-input"
                          value={speakerPhoto}
                          onChange={(e) => setSpeakerPhoto(e.target.value)}
                          placeholder="https://images.unsplash.com/..."
                        />
                      </div>
                    </div>

                    <div className="form-group" style={{ marginTop: '10px' }}>
                      <label className="form-label">Speaker Bio / Credentials</label>
                      <textarea
                        className="form-textarea"
                        rows={2}
                        value={speakerBio}
                        onChange={(e) => setSpeakerBio(e.target.value)}
                        placeholder="Professional background, areas of technical expertise, notable milestones..."
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: SYLLABUS & AGENDA */}
              {modalActiveTab === 'curriculum' && (
                <div style={{ display: 'grid', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">
                      Topics Covered &amp; Learning Outcomes
                      <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 400, marginLeft: 8 }}>(One topic per line)</span>
                    </label>
                    <textarea
                      className="form-textarea"
                      rows={5}
                      value={topics}
                      onChange={(e) => setTopics(e.target.value)}
                      placeholder="Enterprise AI and System Architecture Fundamentals&#10;Scalable Data Pipeline Design and Vector Indexing&#10;Hands-on Production Deployment and CI/CD Automation"
                    />
                    <small style={{ color: '#64748b', fontSize: '0.76rem', display: 'block', marginTop: 4 }}>
                      Each line appears with an official checkmark on the public event page.
                    </small>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Session Agenda &amp; Schedule
                      <span style={{ fontSize: '0.78rem', color: '#64748b', fontWeight: 400, marginLeft: 8 }}>(Format: Time | Title | Description)</span>
                    </label>
                    <textarea
                      className="form-textarea"
                      rows={6}
                      value={agenda}
                      onChange={(e) => setAgenda(e.target.value)}
                      placeholder="10:00 AM - 11:15 AM | Foundations &amp; Architecture | System design patterns and high-performance pipeline architecture&#10;11:30 AM - 01:00 PM | Hands-on Workshop &amp; Implementation | Interactive code lab, model deployment, and live evaluation"
                    />
                    <small style={{ color: '#64748b', fontSize: '0.76rem', display: 'block', marginTop: 4 }}>
                      Separated by vertical bar (|). Rendered as structured timeline blocks on the public view.
                    </small>
                  </div>
                </div>
              )}

              {/* TAB 4: GUIDELINES & PRICING */}
              {modalActiveTab === 'policies' && (
                <div style={{ display: 'grid', gap: '16px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                    <div className="form-group">
                      <label className="form-label">Eligibility / Target Audience</label>
                      <textarea
                        className="form-textarea"
                        rows={2}
                        value={eligibility}
                        onChange={(e) => setEligibility(e.target.value)}
                        placeholder="Open to engineering students, software professionals, and technology enthusiasts."
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Guidelines &amp; Prerequisites</label>
                      <textarea
                        className="form-textarea"
                        rows={2}
                        value={guidelines}
                        onChange={(e) => setGuidelines(e.target.value)}
                        placeholder="A laptop with modern browser access is recommended for interactive tasks."
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Cancellation &amp; Refund Policy</label>
                    <textarea
                      className="form-textarea"
                      rows={2}
                      value={refundPolicy}
                      onChange={(e) => setRefundPolicy(e.target.value)}
                      placeholder="Free registrations may be cancelled anytime before commencement. For paid workshops, cancellation requests submitted at least 48 hours prior to start are eligible for full refund processing."
                    />
                  </div>

                  <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '16px' }}>
                    <h4 style={{ margin: '0 0 12px 0', fontSize: '0.92rem', color: '#0f172a' }}>Pricing &amp; Capacity Control</h4>

                    <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginBottom: '14px' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.88rem', fontWeight: 600 }}>
                        <input
                          type="radio"
                          name="is_paid_radio"
                          checked={!isPaid}
                          onChange={() => {
                            setIsPaid(false);
                            setRegistrationFee(0);
                          }}
                        />
                        Free Attendance
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '0.88rem', fontWeight: 600 }}>
                        <input
                          type="radio"
                          name="is_paid_radio"
                          checked={isPaid}
                          onChange={() => {
                            setIsPaid(true);
                            if (registrationFee === 0) setRegistrationFee(499);
                          }}
                        />
                        Paid Registration (Razorpay Checkout)
                      </label>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
                      <div className="form-group">
                        <label className="form-label">Registration Fee (₹)</label>
                        <input
                          type="number"
                          className="form-input"
                          value={registrationFee}
                          onChange={(e) => setRegistrationFee(Number(e.target.value))}
                          disabled={!isPaid}
                          min={0}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Currency</label>
                        <input
                          type="text"
                          className="form-input"
                          value={currency}
                          onChange={(e) => setCurrency(e.target.value)}
                          disabled
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Seat Limit (Max Participants)</label>
                        <input
                          type="number"
                          className="form-input"
                          value={capacity}
                          onChange={(e) => setCapacity(Number(e.target.value))}
                          min={1}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 5: CERTIFICATES */}
              {modalActiveTab === 'certificates' && (
                <div style={{ display: 'grid', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Assigned Certificate Visual Template</label>
                    <select
                      className="form-select"
                      value={selectedTemplateRef}
                      onChange={(e) => setSelectedTemplateRef(e.target.value ? Number(e.target.value) : '')}
                    >
                      <option value="">No Certificate Template Assigned</option>
                      {availableTemplates.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name} ({t.orientation}) {t.status === 'PUBLISHED' ? '✓' : '(Draft)'}
                        </option>
                      ))}
                    </select>
                    <small style={{ color: '#64748b', fontSize: '0.78rem', marginTop: 4, display: 'block' }}>
                      Visual certificate created in the Certificate Designer module.
                    </small>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'grid', gap: '10px' }}>
                    <h4 style={{ margin: '0 0 6px 0', fontSize: '0.88rem', color: '#0f172a' }}>Eligibility Criteria for Issuance</h4>

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.84rem' }}>
                      <input
                        type="checkbox"
                        checked={certRequireAttendance}
                        onChange={(e) => setCertRequireAttendance(e.target.checked)}
                      />
                      <span>Enforce Minimum Session Attendance</span>
                    </label>

                    {certRequireAttendance && (
                      <div style={{ marginLeft: '26px' }}>
                        <label className="form-label" style={{ fontSize: '0.78rem' }}>Minimum Attendance Percentage</label>
                        <input
                          type="number"
                          className="form-input"
                          style={{ width: '120px' }}
                          value={certMinAttendance}
                          onChange={(e) => setCertMinAttendance(Number(e.target.value))}
                          min={1}
                          max={100}
                        />
                      </div>
                    )}

                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.84rem' }}>
                      <input
                        type="checkbox"
                        checked={certRequireFeedback}
                        onChange={(e) => setCertRequireFeedback(e.target.checked)}
                      />
                      <span>Require Participant Feedback Submission</span>
                    </label>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer with Save as Draft vs Save & Publish */}
            <div className="modal-footer" style={{ borderTop: '1px solid #e2e8f0', padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button type="button" onClick={() => setEventModal(false)} className="btn btn-secondary">
                Cancel
              </button>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => executeEventSave(false, 'DRAFT')}
                  className="btn btn-secondary"
                  disabled={actionLoading}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  Save as Draft
                </button>
                <button
                  type="button"
                  onClick={() => executeEventSave(true, 'UPCOMING')}
                  className="btn btn-primary"
                  disabled={actionLoading}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {actionLoading ? 'Saving...' : 'Save & Publish Event'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* =====================================================================
          EVENT REGISTRATIONS / ATTENDEE LIST MODAL
          ===================================================================== */}
      {regModalEvent && (
        <div className="modal-overlay" onClick={() => setRegModalEvent(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(860px, 96vw)', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
            <div className="modal-header" style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
              <div>
                <span className="badge badge-new">ATTENDEE REGISTRATIONS</span>
                <h3 className="card-title" style={{ marginTop: 2 }}>{regModalEvent.title}</h3>
              </div>
              <button onClick={() => setRegModalEvent(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>

            <div className="modal-body" style={{ overflowY: 'auto', flex: 1, padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ fontSize: '0.88rem', color: '#475569' }}>
                  Total Confirmed Attendees: <strong>{regModalList.length}</strong>
                </div>

                <a
                  href={`/api/events/manage/${regModalEvent.id}/export-csv/`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', textDecoration: 'none' }}
                >
                  <Download size={14} /> Export CSV List
                </a>
              </div>

              {regModalLoading ? (
                <div style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                  <RefreshCw size={20} className="spin" style={{ margin: '0 auto 8px', animation: 'spin 1s linear infinite' }} />
                  Loading attendee records...
                </div>
              ) : regModalList.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8' }}>
                  No participants have registered for this workshop yet.
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0', color: '#64748b' }}>
                        <th style={{ padding: '10px 14px' }}>Reference</th>
                        <th style={{ padding: '10px 14px' }}>Participant Name</th>
                        <th style={{ padding: '10px 14px' }}>Contact</th>
                        <th style={{ padding: '10px 14px' }}>College / Org</th>
                        <th style={{ padding: '10px 14px' }}>Status</th>
                        <th style={{ padding: '10px 14px' }}>Payment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {regModalList.map((reg) => (
                        <tr key={reg.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                          <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontWeight: 700, color: '#1465f4' }}>
                            {reg.registration_reference}
                          </td>
                          <td style={{ padding: '10px 14px', fontWeight: 600, color: '#0f172a' }}>
                            {reg.full_name}
                          </td>
                          <td style={{ padding: '10px 14px', color: '#64748b', fontSize: '0.8rem' }}>
                            <div>{reg.email}</div>
                            <div>{reg.phone}</div>
                          </td>
                          <td style={{ padding: '10px 14px', color: '#475569' }}>
                            {reg.company_or_college || 'Independent'}
                          </td>
                          <td style={{ padding: '10px 14px' }}>
                            <span className="badge badge-qualified">CONFIRMED</span>
                          </td>
                          <td style={{ padding: '10px 14px' }}>
                            <span className={`badge ${reg.fee_paid ? 'badge-qualified' : 'badge-new'}`}>
                              {reg.fee_paid ? `Paid (₹${reg.fee_paid})` : 'Free'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="modal-footer" style={{ borderTop: '1px solid #e2e8f0', padding: '12px 20px' }}>
              <button onClick={() => setRegModalEvent(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dynamic Form Field Builder Modal */}
      {fieldModalEvent && (
        <div className="modal-overlay" onClick={() => setFieldModalEvent(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(640px, 94vw)' }}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">DYNAMIC REGISTRATION FORM BUILDER</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>{fieldModalEvent.title}</h3>
              </div>
              <button onClick={() => setFieldModalEvent(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: '0.82rem', color: '#64748b', marginBottom: '16px' }}>
                Configure custom questions required when attendees register for this specific event. Default contact fields (Name, Email, Phone, Category) are always included automatically.
              </p>

              {/* Add Field Form */}
              <form onSubmit={handleAddFieldSubmit} style={{ display: 'grid', gridTemplateColumns: '1fr 130px auto', gap: '10px', marginBottom: '16px' }}>
                <input
                  type="text"
                  className="form-input"
                  placeholder="Field label (e.g. GitHub URL, Year of Study)..."
                  value={newFieldLabel}
                  onChange={(e) => setNewFieldLabel(e.target.value)}
                  required
                />
                <select
                  className="form-select"
                  value={newFieldType}
                  onChange={(e) => setNewFieldType(e.target.value)}
                >
                  <option value="text">Short Text</option>
                  <option value="textarea">Text Area</option>
                  <option value="dropdown">Dropdown Select</option>
                  <option value="consent">Checkbox Consent</option>
                </select>
                <button type="submit" className="btn btn-primary btn-sm">Add Field</button>
              </form>

              {newFieldType === 'dropdown' && (
                <div style={{ marginBottom: '14px' }}>
                  <label className="form-label" style={{ fontSize: '0.78rem' }}>Dropdown Options (comma separated)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="1st Year, 2nd Year, 3rd Year, Final Year"
                    value={newFieldOptions}
                    onChange={(e) => setNewFieldOptions(e.target.value)}
                  />
                </div>
              )}

              {/* Fields List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {eventFields.length === 0 ? (
                  <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>Only default contact fields are currently required.</p>
                ) : (
                  eventFields.map((f) => (
                    <div key={f.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                      <div>
                        <strong>{f.field_label}</strong> <span style={{ color: '#1465f4', fontSize: '0.78rem' }}>({f.field_type})</span>
                        {f.is_required && (
                          <span style={{ color: '#ef4444', fontSize: '0.72rem', marginLeft: '6px' }}>Required</span>
                        )}
                      </div>
                      <button onClick={() => handleDeleteField(f.id)} className="btn btn-danger btn-sm" style={{ padding: '4px 8px' }}>
                        Delete
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setFieldModalEvent(null)} className="btn btn-secondary">Done</button>
            </div>
          </div>
        </div>
      )}

      {/* Certificate Management Modal per event */}
      {certModalEvent && (
        <div className="modal-overlay" onClick={() => setCertModalEvent(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(780px, 94vw)', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
            <div className="modal-header">
              <div>
                <span className="badge badge-new">CERTIFICATES &amp; CREDENTIALS</span>
                <h3 className="card-title" style={{ marginTop: '4px' }}>{certModalEvent.title}</h3>
              </div>
              <button onClick={() => setCertModalEvent(null)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <div className="modal-body" style={{ overflowY: 'auto', flex: 1 }}>
              {certModalLoading ? (
                <div style={{ textAlign: 'center', padding: '30px', color: '#64748b' }}>
                  <RefreshCw size={20} className="spin" style={{ margin: '0 auto 8px', animation: 'spin 1s linear infinite' }} />
                  Loading event credentials...
                </div>
              ) : certModalData ? (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', background: '#f8fafc', padding: '12px 16px', borderRadius: '8px' }}>
                    <div>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Assigned Template:</span>
                      <strong style={{ marginLeft: 6, color: '#0f172a' }}>{certModalData.certificate_template || 'Default'}</strong>
                    </div>
                    <div>
                      <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Issued Certificates:</span>
                      <strong style={{ marginLeft: 6, color: '#1465f4', fontSize: '1rem' }}>{certModalData.issued_count}</strong>
                    </div>
                  </div>

                  {certModalData.pending_eligible && certModalData.pending_eligible.length > 0 && (
                    <div style={{ marginBottom: '20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <h4 style={{ margin: 0, fontSize: '0.9rem', color: '#0f172a' }}>Eligible Attendees ({certModalData.pending_eligible.length})</h4>
                        <button
                          onClick={handleIssueAllEligibleCerts}
                          className="btn btn-primary btn-sm"
                          disabled={certActionLoading}
                        >
                          Issue All Eligible
                        </button>
                      </div>
                      <div style={{ display: 'grid', gap: '8px' }}>
                        {certModalData.pending_eligible.map((item) => (
                          <div key={item.registration_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px' }}>
                            <div>
                              <strong>{item.full_name}</strong> <span style={{ color: '#64748b', fontSize: '0.78rem' }}>({item.email})</span>
                            </div>
                            <button
                              onClick={() => handleIssueSingleCert(item.registration_id)}
                              className="btn btn-secondary btn-sm"
                              disabled={certActionLoading}
                            >
                              Issue Cert
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <h4 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#0f172a' }}>Issued Certificates</h4>
                  {(!certModalData.issued_certificates || certModalData.issued_certificates.length === 0) ? (
                    <p style={{ fontSize: '0.82rem', color: '#94a3b8' }}>No certificates have been issued yet for this workshop.</p>
                  ) : (
                    <div style={{ display: 'grid', gap: '8px' }}>
                      {certModalData.issued_certificates.map((cert) => (
                        <div key={cert.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}>
                          <div>
                            <div style={{ fontWeight: 700, color: '#0f172a' }}>{cert.recipient_name}</div>
                            <div style={{ fontSize: '0.76rem', color: '#64748b', fontFamily: 'monospace' }}>{cert.certificate_id}</div>
                          </div>
                          <div style={{ display: 'flex', gap: '6px' }}>
                            <a
                              href={`/verify-certificate/${cert.certificate_id}/`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="btn btn-secondary btn-sm"
                              style={{ textDecoration: 'none' }}
                            >
                              Verify
                            </a>
                            <button
                              onClick={() => handleOpenReissueModal(cert)}
                              className="btn btn-secondary btn-sm"
                            >
                              Reissue
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : null}
            </div>
            <div className="modal-footer">
              <button onClick={() => setCertModalEvent(null)} className="btn btn-secondary">Done</button>
            </div>
          </div>
        </div>
      )}

      {/* Reissue Certificate Modal */}
      {reissueModal && (
        <div className="modal-overlay" onClick={() => setReissueModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(480px, 92vw)' }}>
            <div className="modal-header">
              <h3 className="card-title">Reissue Certificate</h3>
              <button onClick={() => setReissueModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <form onSubmit={handleReissueSubmit}>
              <div className="modal-body" style={{ display: 'grid', gap: '12px' }}>
                <div className="form-group">
                  <label className="form-label">Corrected Recipient Name *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={reissueName}
                    onChange={(e) => setReissueName(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Reason for Reissue *</label>
                  <input
                    type="text"
                    className="form-input"
                    value={reissueReason}
                    onChange={(e) => setReissueReason(e.target.value)}
                    placeholder="e.g. Spelling correction requested by attendee"
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" onClick={() => setReissueModal(false)} className="btn btn-secondary">Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={reissueLoading}>
                  {reissueLoading ? 'Reissuing...' : 'Confirm Reissue'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Portal Share Modal */}
      {portalShareModal && (
        <div className="modal-overlay" onClick={() => setPortalShareModal(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 'min(500px, 92vw)' }}>
            <div className="modal-header">
              <h3 className="card-title">Share Public Events Portal</h3>
              <button onClick={() => setPortalShareModal(false)} className="btn btn-secondary btn-sm">✕</button>
            </div>
            <div className="modal-body" style={{ textAlign: 'center', padding: '20px' }}>
              {portalQrDataUri && (
                <img
                  src={portalQrDataUri}
                  alt="Events Portal QR"
                  style={{ width: '180px', height: '180px', margin: '0 auto 16px', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '8px' }}
                />
              )}
              <div style={{ background: '#f8fafc', padding: '10px 14px', borderRadius: '8px', border: '1px solid #e2e8f0', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.84rem', color: '#1465f4', wordBreak: 'break-all', textAlign: 'left' }}>
                  {portalSharingInfo?.canonical_events_portal_url || 'http://127.0.0.1:8000/events/'}
                </span>
                <button onClick={handleCopyPortalLink} className="btn btn-secondary btn-sm" style={{ marginLeft: 8 }}>
                  {portalCopied ? <Check size={14} color="#059669" /> : <Copy size={14} />}
                </button>
              </div>
            </div>
            <div className="modal-footer">
              <button onClick={() => setPortalShareModal(false)} className="btn btn-secondary">Done</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

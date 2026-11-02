// ==============================================================================
// XEYR Technologies Private Limited — API Service Client
// Communicates with Django REST Backend over HTTP / CORS with Session Cookies
// ==============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const name = 'csrftoken';
  const cookieValue = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')[1];
  return cookieValue ? decodeURIComponent(cookieValue) : null;
}

export async function apiFetch<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  // Add CSRF token for state-modifying requests
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf && !headers.has('X-CSRFToken')) {
      headers.set('X-CSRFToken', csrf);
    }
  }

  // Set default JSON Content-Type if not sending FormData
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Ensures Django session cookies are sent/received
  });

  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get('content-type') || '';
  let data: any;
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    // Notify session expiration if unauthenticated on protected routes
    const isAuthRoute = endpoint.includes('/api/auth/login/');
    if (!isAuthRoute && (response.status === 401 || (response.status === 403 && data?.detail?.includes('credentials')))) {
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('xeyr:auth_expired', {
          detail: { status: response.status, message: data?.detail || 'Session expired' }
        }));
      }
    }

    const errorMsg = data?.error || data?.detail || response.statusText || 'API request failed';
    const err: any = new Error(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data as T;
}

// ------------------------------------------------------------------------------
// Authentication API
// ------------------------------------------------------------------------------
export const authApi = {
  login: (credentials: { username: string; password: string }) =>
    apiFetch<{ message: string; user: any }>('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
  logout: () =>
    apiFetch<{ message: string }>('/api/auth/logout/', {
      method: 'POST',
    }),
  getMe: () => apiFetch('/api/auth/me/'),
  getUsers: () => apiFetch('/api/users/'),
};

// ------------------------------------------------------------------------------
// Analytics & Business Intelligence API
// ------------------------------------------------------------------------------
export const analyticsApi = {
  getDashboardMetrics: (period: string = 'last_30_days') =>
    apiFetch(`/api/analytics/dashboard/?period=${period}`),
  getInsights: () => apiFetch('/api/analytics/insights/'),
  getExportUrl: (reportType: string) => `${API_BASE_URL}/api/analytics/export/${reportType}/`,
};

// ------------------------------------------------------------------------------
// CRM & Enquiries API
// ------------------------------------------------------------------------------
export const crmApi = {
  getEnquiries: (status?: string) =>
    apiFetch(`/api/enquiries/${status ? `?status=${status}` : ''}`),
  getEnquiry: (id: number) => apiFetch(`/api/enquiries/${id}/`),
  updateStatus: (id: number, status: string) =>
    apiFetch(`/api/enquiries/${id}/status/`, {
      method: 'POST',
      body: JSON.stringify({ status }),
    }),
  qualify: (id: number, payload: {
    estimated_project_value: number;
    budget_confirmed: boolean;
    timeline_confirmed: boolean;
    notes?: string;
  }) =>
    apiFetch(`/api/enquiries/${id}/qualify/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  reject: (id: number, payload: { category: string; reason_detail: string }) =>
    apiFetch(`/api/enquiries/${id}/reject/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  reopen: (id: number, notes?: string) =>
    apiFetch(`/api/enquiries/${id}/reopen/`, {
      method: 'POST',
      body: JSON.stringify({ notes }),
    }),
  addActivity: (id: number, payload: {
    activity_type: string;
    title: string;
    description: string;
  }) =>
    apiFetch(`/api/enquiries/${id}/activities/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};

// ------------------------------------------------------------------------------
// Requirements Workspace API
// ------------------------------------------------------------------------------
export const requirementsApi = {
  getRequirements: () => apiFetch('/api/requirements/'),
  getByEnquiry: (enquiryId: number) => apiFetch(`/api/requirements/enquiry/${enquiryId}/`),
  saveRequirement: (enquiryId: number, data: any) =>
    apiFetch(`/api/requirements/enquiry/${enquiryId}/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  approve: (enquiryId: number) =>
    apiFetch(`/api/requirements/enquiry/${enquiryId}/approval/`, {
      method: 'POST',
    }),
  checkReadiness: (enquiryId: number) =>
    apiFetch(`/api/requirements/enquiry/${enquiryId}/readiness/`),
};

// ------------------------------------------------------------------------------
// Brand Assets API
// ------------------------------------------------------------------------------
export const assetsApi = {
  getAssets: () => apiFetch('/api/assets/'),
  getByRequirement: (reqId: number) => apiFetch(`/api/assets/requirement/${reqId}/`),
  getChecklist: (reqId: number) => apiFetch(`/api/assets/requirement/${reqId}/checklist/`),
  upload: (formData: FormData) =>
    apiFetch('/api/assets/', {
      method: 'POST',
      body: formData,
    }),
  getDownloadUrl: (id: number) => `${API_BASE_URL}/api/assets/${id}/download/`,
};

// ------------------------------------------------------------------------------
// Developer Handover API
// ------------------------------------------------------------------------------
export const handoverApi = {
  getHandovers: () => apiFetch('/api/handover/'),
  generate: (reqId: number, payload?: any) =>
    apiFetch(`/api/handover/requirement/${reqId}/`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),
  assignDeveloper: (id: number, payload: {
    assigned_developer_id: number;
    handover_instructions?: string;
    priority?: string;
    expected_delivery_date?: string;
  }) =>
    apiFetch(`/api/handover/${id}/assign-developer/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getDownloadUrl: (id: number) => `${API_BASE_URL}/api/handover/${id}/download/`,
};

// ------------------------------------------------------------------------------
// Developer Projects API
// ------------------------------------------------------------------------------
export const projectsApi = {
  getProjects: () => apiFetch('/api/projects/'),
  getProject: (id: number) => apiFetch(`/api/projects/${id}/`),
  updateProject: (id: number, data: any) =>
    apiFetch(`/api/projects/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
  createMilestone: (projectId: number, data: { title: string; due_date?: string; description?: string }) =>
    apiFetch(`/api/projects/${projectId}/milestones/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  toggleMilestone: (projectId: number, milestoneId: number, completed: boolean) =>
    apiFetch(`/api/projects/${projectId}/milestones/`, {
      method: 'PATCH',
      body: JSON.stringify({ milestone_id: milestoneId, completed }),
    }),
  createDeliverable: (projectId: number, formData: FormData) =>
    apiFetch(`/api/projects/${projectId}/deliverables/`, {
      method: 'POST',
      body: formData,
    }),
};

// ------------------------------------------------------------------------------
// Events & Registrations Management API
// ------------------------------------------------------------------------------
export const eventsApi = {
  getEvents: () => apiFetch('/api/events/manage/'),
  getEvent: (id: number) => apiFetch(`/api/events/manage/${id}/`),
  createEvent: (formData: FormData) =>
    apiFetch('/api/events/manage/', {
      method: 'POST',
      body: formData,
    }),
  updateEvent: (id: number, formData: FormData) =>
    apiFetch(`/api/events/manage/${id}/`, {
      method: 'PUT',
      body: formData,
    }),
  deleteEvent: (id: number) =>
    apiFetch(`/api/events/manage/${id}/`, {
      method: 'DELETE',
    }),
  getFields: (eventId: number) => apiFetch(`/api/events/manage/${eventId}/fields/`),
  addField: (eventId: number, data: any) =>
    apiFetch(`/api/events/manage/${eventId}/fields/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  deleteField: (fieldId: number) =>
    apiFetch(`/api/events/manage/fields/${fieldId}/`, {
      method: 'DELETE',
    }),
  notifySubscribers: (eventId: number) =>
    apiFetch(`/api/events/manage/${eventId}/notify-subscribers/`, {
      method: 'POST',
    }),
  getPaymentsDashboard: () => apiFetch('/api/events/payments/dashboard/'),
  getRegistrations: (params: { event_id?: number; status?: string; q?: string } = {}) => {
    const qp = new URLSearchParams();
    if (params.event_id) qp.set('event_id', String(params.event_id));
    if (params.status) qp.set('status', params.status);
    if (params.q) qp.set('q', params.q);
    const qs = qp.toString();
    return apiFetch(`/api/events/registrations/${qs ? `?${qs}` : ''}`);
  },
  getRegistrationsCsvUrl: (eventId: number) =>
    `${API_BASE_URL}/api/events/manage/${eventId}/export-csv/`,
  getSkillBridgeList: () => apiFetch('/api/events/admin/skillbridge/'),
};

// ------------------------------------------------------------------------------
// Event Notification Subscribers Management API
// ------------------------------------------------------------------------------
export const subscribersApi = {
  getSubscribers: (params: { status?: string; search?: string } = {}) => {
    const qp = new URLSearchParams();
    if (params.status) qp.set('status', params.status);
    if (params.search) qp.set('search', params.search);
    const qs = qp.toString();
    return apiFetch(`/api/events/subscribers/${qs ? `?${qs}` : ''}`);
  },
  retryDelivery: (deliveryId: number) =>
    apiFetch(`/api/events/subscribers/deliveries/${deliveryId}/retry/`, {
      method: 'POST',
    }),
  toggleSubscriberStatus: (subscriberId: number) =>
    apiFetch(`/api/events/subscribers/${subscriberId}/toggle-status/`, {
      method: 'POST',
    }),
};

// ------------------------------------------------------------------------------
// Financial Management API
// ------------------------------------------------------------------------------
export const financeApi = {
  getInvoices: () => apiFetch('/api/finance/invoices/'),
  createInvoice: (data: any) =>
    apiFetch('/api/finance/invoices/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getPayments: () => apiFetch('/api/finance/payments/'),
  createPayment: (data: any) =>
    apiFetch('/api/finance/payments/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getExpenses: () => apiFetch('/api/finance/expenses/'),
  createExpense: (data: any) =>
    apiFetch('/api/finance/expenses/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// ------------------------------------------------------------------------------
// Social Media & QR Code API
// ------------------------------------------------------------------------------
export const socialApi = {
  getConfig: () => apiFetch('/api/social-links/manage/'),
  saveConfig: (formData: FormData) =>
    apiFetch('/api/social-links/manage/', {
      method: 'POST',
      body: formData,
    }),
};

// ------------------------------------------------------------------------------
// Notifications & System Audit API
// ------------------------------------------------------------------------------
export const systemApi = {
  getNotifications: () => apiFetch('/api/notifications/'),
  markNotificationRead: (id: number) =>
    apiFetch(`/api/notifications/${id}/read/`, {
      method: 'POST',
    }),
  getAuditLogs: () => apiFetch('/api/audit-logs/'),
  getSettings: () => apiFetch('/api/system-settings/'),
  updateSetting: (key: string, value: string, description?: string) =>
    apiFetch('/api/system-settings/', {
      method: 'POST',
      body: JSON.stringify({ key, value, description }),
    }),
  batchUpdateSettings: (settings: Record<string, any>) =>
    apiFetch('/api/system-settings/', {
      method: 'POST',
      body: JSON.stringify({ settings }),
    }),
  getPublicSettings: () => apiFetch('/api/system-settings/public/'),
};

export const notificationService = systemApi;

// ------------------------------------------------------------------------------
// Certificate Designer & Templates API
// ------------------------------------------------------------------------------
export const certificateTemplatesApi = {
  getTemplates: (params?: { status?: string; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.status) q.append('status', params.status);
    if (params?.search) q.append('search', params.search);
    const qs = q.toString();
    return apiFetch(`/api/certificates/templates/${qs ? `?${qs}` : ''}`);
  },
  getTemplate: (id: number) =>
    apiFetch(`/api/certificates/templates/${id}/`),
  createTemplate: (payload: any) =>
    apiFetch('/api/certificates/templates/', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateTemplate: (id: number, payload: any) =>
    apiFetch(`/api/certificates/templates/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
  deleteTemplate: (id: number) =>
    apiFetch(`/api/certificates/templates/${id}/`, {
      method: 'DELETE',
    }),
  duplicateTemplate: (id: number) =>
    apiFetch(`/api/certificates/templates/${id}/duplicate/`, {
      method: 'POST',
    }),
  getPreviewUrl: (id: number) => `/api/certificates/templates/${id}/preview/`,
};

// ------------------------------------------------------------------------------
// Certificate Issuance, Reissue & Verification API
// ------------------------------------------------------------------------------
export const certificatesApi = {
  getEventCertificates: (eventId: number) =>
    apiFetch(`/api/events/manage/${eventId}/certificates/`),
  issueCertificates: (eventId: number, payload: { registration_ids?: number[]; issue_all_eligible?: boolean }) =>
    apiFetch(`/api/events/manage/${eventId}/certificates/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  reissueCertificate: (certificateId: string, payload: { recipient_name: string; reissue_reason: string }) =>
    apiFetch(`/api/certificates/${certificateId}/reissue/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  retryEmail: (certificateId: string) =>
    apiFetch(`/api/certificates/${certificateId}/retry-email/`, {
      method: 'POST',
    }),
  getRenderUrl: (certificateId: string) => `/api/certificates/${certificateId}/render/`,
  getDownloadUrl: (certificateId: string) => `/api/certificates/download/${certificateId}/`,
};

// ------------------------------------------------------------------------------
// Main Events Portal Sharing & QR API
// ------------------------------------------------------------------------------
export const portalSharingApi = {
  getSharingInfo: () => apiFetch('/api/events/portal-share/'),
  getPortalQrData: () => apiFetch('/api/events/portal-qr/?format=json'),
  getPortalQrImageUrl: () => '/api/events/portal-qr/',
};


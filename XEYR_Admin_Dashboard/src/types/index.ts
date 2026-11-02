export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  department: string;
  phone?: string;
  is_superuser: boolean;
  is_staff: boolean;
}

export interface CRMActivity {
  id: number;
  activity_type: string;
  title: string;
  description: string;
  performed_by: number | string;
  created_at: string;
}

export interface Enquiry {
  id: number;
  reference_id: string;
  client_name: string;
  email: string;
  phone: string;
  company_name: string;
  service_type: string;
  project_title: string;
  project_description: string;
  budget_range: string;
  status: string;
  assigned_to?: number | string | null;
  created_at: string;
  updated_at?: string;
  qualification?: {
    decision: string;
    estimated_project_value: string | number;
    budget_confirmed: boolean;
    timeline_confirmed: boolean;
    qualified_at: string;
    notes: string;
  } | null;
  rejection?: {
    category: string;
    reason_detail: string;
    rejected_at: string;
  } | null;
  activities?: CRMActivity[];
}

export interface ProjectRequirement {
  id: number;
  enquiry: number;
  requirement_reference: string;
  title: string;
  scope_summary: string;
  target_delivery_date?: string | null;
  status: string;
  functional_specs?: string[];
  deliverables_list?: string[];
  is_ready_for_handover?: boolean;
  created_at?: string;
}

export interface ClientBrandAsset {
  id: number;
  requirement: number;
  title: string;
  category: string;
  file?: string;
  filename: string;
  file_type: string;
  file_size: number;
  checksum_sha256: string;
  status: string;
  version: number;
  uploaded_by: number | string;
  created_at: string;
}

export interface HandoverRecord {
  id: number;
  requirement: number;
  handover_reference: string;
  version: number;
  zip_file?: string;
  zip_filename: string;
  zip_size: number;
  zip_checksum_sha256: string;
  manifest_data?: Record<string, any>;
  all_checks_passed: boolean;
  assigned_developer?: number | string | null;
  generated_by?: number | string;
  generated_at: string;
  download_count?: number;
}

export interface Milestone {
  id: number;
  project: number;
  title: string;
  description: string;
  due_date?: string | null;
  completed: boolean;
  completed_at?: string | null;
}

export interface Deliverable {
  id: number;
  project: number;
  title: string;
  deliverable_type: string;
  url_or_ref?: string;
  status: string;
  uploaded_at: string;
}

export interface DeveloperProject {
  id: number;
  requirement: number;
  project_code: string;
  title: string;
  assigned_developer?: number | string | null;
  status: string;
  priority: string;
  progress_percentage: number;
  expected_completion_date?: string | null;
  blocker_description?: string;
  created_at: string;
  updated_at: string;
  milestones?: Milestone[];
  deliverables?: Deliverable[];
}

export interface EventFormField {
  id: number;
  field_label: string;
  field_type: string;
  options?: string;
  is_required: boolean;
}

export interface EventListing {
  id: number;
  title: string;
  slug: string;
  category: string;
  event_date: string;
  start_time?: string;
  end_time?: string;
  location_type: string;
  venue_name?: string;
  registration_fee: number | string;
  currency: string;
  capacity: number;
  is_published: boolean;
  status: string;
  short_summary?: string;
  poster?: string;
  poster_url?: string;
  organizer?: string;
  eligibility?: string;
  guidelines?: string;
  prerequisites?: string;
  refund_policy?: string;
  learning_outcomes?: string[];
  schedule?: Array<{ time?: string; title?: string; description?: string }>;
  mentors?: Array<{ name?: string; role?: string; company?: string; bio?: string; photo?: string; image?: string }>;
  full_description?: string;
  description?: string;
  created_at: string;
  custom_fields?: EventFormField[];
  certificate_enabled?: boolean;
  certificate_template?: string;
  certificate_template_ref?: number | null;
  certificate_template_name?: string | null;
  certificate_min_attendance?: number;
  certificate_require_feedback?: boolean;
  certificate_require_attendance?: boolean;
  certificate_require_activities?: boolean;
  certificate_activities_description?: string;
  certificate_release_date?: string | null;
  feedback_enabled?: boolean;
}

export interface CertificateTemplate {
  id: number;
  name: string;
  slug: string;
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';
  orientation: 'LANDSCAPE' | 'PORTRAIT';
  width: number;
  height: number;
  background_type: 'COLOR' | 'IMAGE' | 'GRADIENT';
  background_color: string;
  background_gradient?: string;
  background_image?: string | null;
  background_image_url?: string;
  border_style: 'classic_gold' | 'modern_blue' | 'double_line' | 'ornamental' | 'minimal_clean' | 'none';
  border_color: string;
  border_width: number;
  title: string;
  subtitle: string;
  description_template: string;
  logo_image?: string | null;
  logo_url: string;
  signatory_name: string;
  signatory_title: string;
  signature_image?: string | null;
  signature_url?: string;
  organizer_name: string;
  show_qr_code: boolean;
  typography?: Record<string, any>;
  layout_elements?: any[];
  is_default: boolean;
  assigned_events_count?: number;
  created_at: string;
  updated_at: string;
}

export interface EventCertificate {
  id: number;
  certificate_id: string;
  event: number;
  event_title: string;
  event_slug?: string;
  event_date?: string;
  registration?: number | null;
  recipient_name: string;
  recipient_email: string;
  status: 'ISSUED' | 'REVOKED';
  issue_date: string;
  template_type: string;
  template_ref?: number | null;
  template_name?: string | null;
  template_snapshot?: Record<string, any>;
  organizer_name: string;
  signatory_title: string;
  verification_token: string;
  reissued_at?: string | null;
  reissue_reason?: string;
  reissued_by_username?: string | null;
  email_delivery_status: string;
  email_sent_at?: string | null;
  email_error?: string;
  download_url: string;
  render_url: string;
  verify_url: string;
  created_at: string;
}

export interface EventRegistration {
  id: number;
  registration_reference: string;
  event: number;
  event_name: string;
  full_name: string;
  company_or_college?: string;
  email: string;
  phone: string;
  registration_status: string;
  payment_status: string;
  fee_paid: number | string;
  created_at: string;
  form_responses?: Record<string, any>;
}

export interface InvoiceQuote {
  id: number;
  requirement?: number | null;
  reference_no: string;
  doc_type: 'QUOTE' | 'INVOICE';
  amount_quoted: number | string;
  amount_invoiced: number | string;
  amount_received: number | string;
  amount_pending: number | string;
  amount_refunded: number | string;
  currency: string;
  status: string;
  due_date?: string | null;
  created_at: string;
}

export interface PaymentRecord {
  id: number;
  invoice?: number | null;
  transaction_reference: string;
  amount: number | string;
  currency: string;
  payment_method: string;
  payment_status: string;
  payment_date: string;
  notes?: string;
}

export interface ExpenseRecord {
  id: number;
  title: string;
  category: string;
  amount: number | string;
  currency: string;
  date: string;
  notes?: string;
}

export interface NotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  link?: string;
  is_read: boolean;
  created_at: string;
}

export interface SocialMediaConfig {
  id: number;
  platform_key: string;
  platform_name: string;
  platform_url: string;
  qr_code_image?: string | null;
  is_public: boolean;
}

export interface DashboardKPIs {
  total_enquiries: number;
  qualified_enquiries: number;
  pipeline_value: number;
  handovers_generated: number;
  active_projects: number;
  blocked_projects: number;
  amount_invoiced: number;
  amount_received: number;
  amount_pending: number;
  new_enquiries?: number;
  rejected_enquiries?: number;
  upcoming_events?: number;
  event_registrations?: number;
  unread_notifications?: number;
}

export interface DashboardMetrics {
  kpis: DashboardKPIs;
  conversion_funnel: {
    enquiry_to_qualified_pct: number;
    qualified_to_requirements_pct: number;
    requirements_to_handover_pct: number;
  };
  services: Array<{ service_type: string; count: number }>;
  rejection_reasons: Array<{ category: string; count: number }>;
}

export interface BusinessInsight {
  title: string;
  message: string;
  severity: 'info' | 'warning' | 'danger' | 'success';
  action_label: string;
  action_link: string;
}

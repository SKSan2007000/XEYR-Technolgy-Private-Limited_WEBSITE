from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

# Core views
from core.views import (
    CurrentUserView, LoginView, LogoutView, UserListView,
    AuditLogListView, NotificationListView, NotificationMarkReadView, SystemSettingListView,
    HealthCheckView, ParticipantSignupView, ParticipantProfileView,
    ChangePasswordView, PublicLeaderboardView, PublicSystemSettingsView
)
from core.dashboard_views import (
    PublicWebsiteView, AdminDashboardView, EventsPortalView,
    EventDetailPageView, ParticipantDashboardPageView, CertificateVerifyPageView
)

# CRM views
from crm.views import (
    PublicEnquirySubmitView, EnquiryListCreateView, EnquiryDetailView,
    EnquiryStatusUpdateView, EnquiryQualifyView, EnquiryRejectView,
    EnquiryReopenView, CRMActivityCreateView
)

# Requirements views
from requirements.views import (
    RequirementWorkspaceView, RequirementApprovalView, RequirementReadinessView
)

# Assets views
from assets_mgmt.views import (
    AssetListCreateView, AssetDetailView, AssetSecureDownloadView, AssetChecklistView
)

# Handover views
from handover.views import (
    HandoverListCreateView, HandoverDownloadView, HandoverAssignDeveloperView
)

# Projects views
from projects.views import (
    ProjectListView, ProjectDetailView, MilestoneCreateToggleView, DeliverableCreateView
)

# Analytics views
from analytics.views import (
    BusinessIntelligenceDashboardView, RuleBasedInsightsView, ExportCSVView
)

# Finance views
from finance.views import (
    InvoiceQuoteListCreateView, PaymentRecordListCreateView, ExpenseListCreateView
)

# Events views
from events_mgmt.views import (
    PublicEventsFeedView, PublicEventDetailView, PublicEventDynamicRegisterView,
    PublicEventVerifyPaymentView, PublicRazorpayWebhookView,
    PublicEventSubscribeView, PublicEventUnsubscribeView,
    PublicSocialMediaLinksView, AdminEventCRUDView, AdminEventDetailManageView,
    AdminEventFormFieldConfigView, AdminEventFormFieldDeleteView,
    AdminEventNotifySubscribersView, AdminEventPaymentsDashboardView,
    AdminSocialMediaConfigView, AdminExportEventRegistrationsCSVView,
    PublicEventRegisterView, PublicCollegeEnquiryView, PublicSkillBridgeTrainerView,
    AdminEventsListView, AdminSkillBridgeListView, AdminRegistrationsListView,
    AdminSubscribersListView, AdminSubscriberDeliveryRetryView, AdminSubscriberToggleStatusView,
    ParticipantDashboardOverviewView, ParticipantRegistrationsView, ParticipantPaymentsView,
    ParticipantCertificatesView, ParticipantFeedbackSubmitView,
    PublicCertificateVerifyView, AdminEventCertificatesView, AdminEventAttendanceView,
    AdminFeedbackListView, PublicEventGalleryView, AdminEventGalleryManageView,
    AdminEventGalleryDetailView,
    AdminCertificateTemplateCRUDView, AdminCertificateTemplateDetailView,
    AdminCertificateTemplateDuplicateView, AdminCertificateTemplatePreviewView,
    CertificateRenderView, CertificateDownloadView,
    AdminCertificateReissueView, AdminCertificateEmailRetryView,
    MainPortalQRView, MainPortalSharingInfoView
)

urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # Frontend & Admin Dashboard
    path('', PublicWebsiteView.as_view(), name='public-website'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('events/', EventsPortalView.as_view(), name='events-portal'),
    path('event/', EventDetailPageView.as_view(), name='event-detail-page'),
    path('events/<str:slug>/', EventDetailPageView.as_view(), name='event-detail-page-slug'),
    path('participant-dashboard/', ParticipantDashboardPageView.as_view(), name='participant-dashboard-page'),
    path('verify-certificate/', CertificateVerifyPageView.as_view(), name='certificate-verify-page'),
    path('verify-certificate/<str:certificate_id>/', CertificateVerifyPageView.as_view(), name='certificate-verify-page-id'),

    # Direct static assets from XEYR_Website_Frontend
    path('styles.css', static_serve, {'document_root': settings.STATICFILES_DIRS[0], 'path': 'styles.css'}),
    path('script.js', static_serve, {'document_root': settings.STATICFILES_DIRS[0], 'path': 'script.js'}),
    path('portal.js', static_serve, {'document_root': settings.STATICFILES_DIRS[0], 'path': 'portal.js'}),
    path('assets/<path:path>', static_serve, {'document_root': settings.STATICFILES_DIRS[0] / 'assets'}),

    # Core & Authentication
    path('api/health/', HealthCheckView.as_view(), name='api-health'),
    path('api/auth/login/', LoginView.as_view(), name='api-login'),
    path('api/auth/register/', ParticipantSignupView.as_view(), name='api-participant-register'),
    path('api/auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('api/auth/me/', CurrentUserView.as_view(), name='api-me'),
    path('api/auth/profile/', ParticipantProfileView.as_view(), name='api-participant-profile'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='api-auth-change-password'),
    path('api/users/', UserListView.as_view(), name='api-users'),
    path('api/audit-logs/', AuditLogListView.as_view(), name='api-audit-logs'),
    path('api/notifications/', NotificationListView.as_view(), name='api-notifications'),
    path('api/notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='api-notification-read'),
    path('api/system-settings/', SystemSettingListView.as_view(), name='api-system-settings'),
    path('api/system-settings/public/', PublicSystemSettingsView.as_view(), name='api-public-system-settings'),
    path('api/leaderboard/public/', PublicLeaderboardView.as_view(), name='api-public-leaderboard'),

    # CRM & Enquiries
    path('api/enquiries/submit/', PublicEnquirySubmitView.as_view(), name='api-public-enquiry-submit'),
    path('api/enquiries/', EnquiryListCreateView.as_view(), name='api-enquiries-list'),
    path('api/enquiries/<int:pk>/', EnquiryDetailView.as_view(), name='api-enquiry-detail'),
    path('api/enquiries/<int:pk>/status/', EnquiryStatusUpdateView.as_view(), name='api-enquiry-status'),
    path('api/enquiries/<int:pk>/qualify/', EnquiryQualifyView.as_view(), name='api-enquiry-qualify'),
    path('api/enquiries/<int:pk>/reject/', EnquiryRejectView.as_view(), name='api-enquiry-reject'),
    path('api/enquiries/<int:pk>/reopen/', EnquiryReopenView.as_view(), name='api-enquiry-reopen'),
    path('api/enquiries/<int:pk>/activities/', CRMActivityCreateView.as_view(), name='api-enquiry-activities'),

    # Client Requirements Workspace & Approvals
    path('api/requirements/', RequirementWorkspaceView.as_view(), name='api-requirements-list'),
    path('api/requirements/enquiry/<int:enquiry_id>/', RequirementWorkspaceView.as_view(), name='api-requirements-workspace'),
    path('api/requirements/enquiry/<int:enquiry_id>/approval/', RequirementApprovalView.as_view(), name='api-requirements-approval'),
    path('api/requirements/enquiry/<int:enquiry_id>/readiness/', RequirementReadinessView.as_view(), name='api-requirements-readiness'),

    # Brand Assets & Secure Downloads
    path('api/assets/', AssetListCreateView.as_view(), name='api-assets-list'),
    path('api/assets/requirement/<int:requirement_id>/', AssetListCreateView.as_view(), name='api-assets-requirement'),
    path('api/assets/requirement/<int:requirement_id>/checklist/', AssetChecklistView.as_view(), name='api-assets-checklist'),
    path('api/assets/<int:pk>/', AssetDetailView.as_view(), name='api-asset-detail'),
    path('api/assets/<int:pk>/download/', AssetSecureDownloadView.as_view(), name='api-asset-download'),

    # Developer Handover & ZIP Generation
    path('api/handover/', HandoverListCreateView.as_view(), name='api-handover-list'),
    path('api/handover/requirement/<int:requirement_id>/', HandoverListCreateView.as_view(), name='api-handover-generate'),
    path('api/handover/<int:pk>/download/', HandoverDownloadView.as_view(), name='api-handover-download'),
    path('api/handover/<int:pk>/assign-developer/', HandoverAssignDeveloperView.as_view(), name='api-handover-assign'),

    # Developer Projects & Progress Tracking
    path('api/projects/', ProjectListView.as_view(), name='api-projects-list'),
    path('api/projects/<int:pk>/', ProjectDetailView.as_view(), name='api-project-detail'),
    path('api/projects/<int:project_id>/milestones/', MilestoneCreateToggleView.as_view(), name='api-project-milestones'),
    path('api/projects/<int:project_id>/deliverables/', DeliverableCreateView.as_view(), name='api-project-deliverables'),

    # Business Intelligence, Analytics & Reports
    path('api/analytics/dashboard/', BusinessIntelligenceDashboardView.as_view(), name='api-analytics-dashboard'),
    path('api/analytics/insights/', RuleBasedInsightsView.as_view(), name='api-analytics-insights'),
    path('api/analytics/export/csv/', ExportCSVView.as_view(), name='api-analytics-export-csv-query'),
    path('api/analytics/export/<str:report_type>/', ExportCSVView.as_view(), name='api-analytics-export-csv'),

    # Financial Management
    path('api/finance/invoices/', InvoiceQuoteListCreateView.as_view(), name='api-finance-invoices'),
    path('api/finance/payments/', PaymentRecordListCreateView.as_view(), name='api-finance-payments'),
    path('api/finance/expenses/', ExpenseListCreateView.as_view(), name='api-finance-expenses'),

    # Public Event APIs
    path('api/events/public/', PublicEventsFeedView.as_view(), name='api-public-events-feed'),
    path('api/events/public/<str:slug_or_id>/', PublicEventDetailView.as_view(), name='api-public-event-detail'),
    path('api/events/<int:event_id>/register-dynamic/', PublicEventDynamicRegisterView.as_view(), name='api-public-event-register-dynamic'),
    path('api/events/verify-payment/', PublicEventVerifyPaymentView.as_view(), name='api-public-event-verify-payment'),
    path('api/events/subscribe/', PublicEventSubscribeView.as_view(), name='api-public-event-subscribe'),
    path('api/events/subscribers/unsubscribe/<str:token>/', PublicEventUnsubscribeView.as_view(), name='api-public-event-unsubscribe'),
    path('api/events/razorpay-webhook/', PublicRazorpayWebhookView.as_view(), name='api-public-razorpay-webhook'),
    path('api/social-links/public/', PublicSocialMediaLinksView.as_view(), name='api-public-social-links'),

    # Participant Dashboard APIs
    path('api/participant/dashboard/', ParticipantDashboardOverviewView.as_view(), name='api-participant-dashboard'),
    path('api/participant/registrations/', ParticipantRegistrationsView.as_view(), name='api-participant-registrations'),
    path('api/participant/payments/', ParticipantPaymentsView.as_view(), name='api-participant-payments'),
    path('api/participant/certificates/', ParticipantCertificatesView.as_view(), name='api-participant-certificates'),
    path('api/participant/feedback/', ParticipantFeedbackSubmitView.as_view(), name='api-participant-feedback'),

    # Public Certificates & Gallery APIs
    path('api/certificates/verify/<str:certificate_id>/', PublicCertificateVerifyView.as_view(), name='api-public-certificate-verify'),
    path('api/certificates/<str:certificate_id>/render/', CertificateRenderView.as_view(), name='api-certificate-render'),
    path('api/certificates/download/<str:certificate_id>/', CertificateDownloadView.as_view(), name='api-certificate-download'),
    path('api/certificates/<str:certificate_id>/download/', CertificateDownloadView.as_view(), name='api-certificate-download-alt'),
    path('api/events/gallery/', PublicEventGalleryView.as_view(), name='api-public-events-gallery'),

    # Certificate Template Designer Management APIs
    path('api/certificates/templates/', AdminCertificateTemplateCRUDView.as_view(), name='api-admin-certificate-templates'),
    path('api/certificates/templates/<int:pk>/', AdminCertificateTemplateDetailView.as_view(), name='api-admin-certificate-template-detail'),
    path('api/certificates/templates/<int:pk>/duplicate/', AdminCertificateTemplateDuplicateView.as_view(), name='api-admin-certificate-template-duplicate'),
    path('api/certificates/templates/<int:pk>/preview/', AdminCertificateTemplatePreviewView.as_view(), name='api-admin-certificate-template-preview'),
    path('api/certificates/<str:certificate_id>/reissue/', AdminCertificateReissueView.as_view(), name='api-admin-certificate-reissue'),
    path('api/certificates/<str:certificate_id>/retry-email/', AdminCertificateEmailRetryView.as_view(), name='api-admin-certificate-retry-email'),

    # Main Events Portal Canonical URL & QR Code Sharing APIs
    path('api/events/portal-qr/', MainPortalQRView.as_view(), name='api-events-portal-qr'),
    path('api/events/portal-share/', MainPortalSharingInfoView.as_view(), name='api-events-portal-share'),

    # Admin Event & Social Media Management APIs
    path('api/events/manage/', AdminEventCRUDView.as_view(), name='api-admin-events-manage'),
    path('api/events/manage/<int:pk>/', AdminEventDetailManageView.as_view(), name='api-admin-event-detail-manage'),
    path('api/events/manage/<int:event_id>/fields/', AdminEventFormFieldConfigView.as_view(), name='api-admin-event-fields'),
    path('api/events/manage/fields/<int:pk>/', AdminEventFormFieldDeleteView.as_view(), name='api-admin-event-field-delete'),
    path('api/events/manage/<int:event_id>/notify-subscribers/', AdminEventNotifySubscribersView.as_view(), name='api-admin-event-notify'),
    path('api/events/manage/<int:event_id>/export-csv/', AdminExportEventRegistrationsCSVView.as_view(), name='api-admin-event-export-csv'),
    path('api/events/manage/<int:event_id>/certificates/', AdminEventCertificatesView.as_view(), name='api-admin-event-certificates'),
    path('api/events/manage/<int:event_id>/attendance/', AdminEventAttendanceView.as_view(), name='api-admin-event-attendance'),
    path('api/events/manage/<int:event_id>/feedback/', AdminFeedbackListView.as_view(), name='api-admin-event-feedback'),
    path('api/events/manage/feedback/', AdminFeedbackListView.as_view(), name='api-admin-feedback-all'),
    path('api/events/gallery/manage/', AdminEventGalleryManageView.as_view(), name='api-admin-gallery-manage'),
    path('api/events/gallery/manage/<int:pk>/', AdminEventGalleryDetailView.as_view(), name='api-admin-gallery-detail'),
    path('api/events/payments/dashboard/', AdminEventPaymentsDashboardView.as_view(), name='api-admin-event-payments-dashboard'),
    path('api/events/registrations/', AdminRegistrationsListView.as_view(), name='api-admin-events-registrations'),
    path('api/events/subscribers/', AdminSubscribersListView.as_view(), name='api-admin-subscribers-list'),
    path('api/events/subscribers/deliveries/<int:pk>/retry/', AdminSubscriberDeliveryRetryView.as_view(), name='api-admin-subscriber-delivery-retry'),
    path('api/events/subscribers/<int:pk>/toggle-status/', AdminSubscriberToggleStatusView.as_view(), name='api-admin-subscriber-toggle-status'),
    path('api/social-links/manage/', AdminSocialMediaConfigView.as_view(), name='api-admin-social-links-manage'),

    # Backward Compatibility SkillBridge & General Events
    path('api/events/register/', PublicEventRegisterView.as_view(), name='api-events-register'),
    path('api/events/college-enquiry/', PublicCollegeEnquiryView.as_view(), name='api-college-enquiry'),
    path('api/events/trainer-apply/', PublicSkillBridgeTrainerView.as_view(), name='api-trainer-apply'),
    path('api/events/admin/events/', AdminEventsListView.as_view(), name='api-admin-events'),
    path('api/events/admin/skillbridge/', AdminSkillBridgeListView.as_view(), name='api-admin-skillbridge'),
]

# Static & media file serving for local development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

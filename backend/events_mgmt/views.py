import os
import hmac
import hashlib
import csv
import json
import re
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

from django.utils import timezone
from django.conf import settings
from django.db import transaction, models
from django.http import HttpResponse
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

import razorpay

import io
import base64
import qrcode

from .models import (
    EventListing, EventFormField, EventRegistration,
    EventNotificationSubscriber, EventNotificationDelivery,
    EventPaymentOrder, EventRefundRecord, SocialMediaConfig,
    SkillBridgeCollegeEnquiry, SkillBridgeProfessionalApplication,
    EventFeedback, EventCertificate, EventAttendance, EventGalleryItem,
    CertificateTemplate
)
from .serializers import (
    EventListingSerializer, EventFormFieldSerializer, EventRegistrationSerializer,
    EventNotificationSubscriberSerializer, EventNotificationDeliverySerializer,
    EventPaymentOrderSerializer, EventRefundRecordSerializer, SocialMediaConfigSerializer,
    SkillBridgeCollegeEnquirySerializer, SkillBridgeProfessionalApplicationSerializer,
    EventFeedbackSerializer, EventCertificateSerializer, PublicCertificateVerificationSerializer,
    EventAttendanceSerializer, EventGalleryItemSerializer, CertificateTemplateSerializer
)
from crm.models import Enquiry, EnquiryStatus
from core.models import AuditLog, Notification
from finance.models import PaymentRecord


class IsStaffOrAdminPermission(permissions.BasePermission):
    """
    Strict Role-Based Access Control (RBAC):
    Allows access only to authenticated administrative staff members.
    Rejects anonymous users and participants with HTTP 403 Forbidden.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        user_role = getattr(request.user, 'role', '')
        staff_roles = [
            'SUPER_ADMIN', 'BUSINESS_ADMIN', 'PROJECT_MANAGER',
            'SALES_CRM', 'ACCOUNT_MANAGER', 'DEVELOPER', 'FINANCE_EXECUTIVE', 'READONLY_ANALYST'
        ]
        return user_role in staff_roles


def get_public_base_url():
    """
    Retrieve configured public base URL from SystemSetting or fallback to settings.PUBLIC_BASE_URL.
    Defaults to http://localhost:8080 for local development.
    """
    from core.models import SystemSetting
    setting = SystemSetting.objects.filter(key='PUBLIC_BASE_URL').first()
    if setting and setting.value and setting.value.strip():
        return setting.value.strip().rstrip('/')
    env_url = os.environ.get('PUBLIC_BASE_URL')
    if env_url and env_url.strip():
        return env_url.strip().rstrip('/')
    settings_url = getattr(settings, 'PUBLIC_BASE_URL', None)
    if settings_url and settings_url.strip():
        return settings_url.strip().rstrip('/')
    if not getattr(settings, 'DEBUG', True):
        return 'https://xeyr.in'
    return 'http://localhost:8080'


def get_events_portal_url():
    """
    Returns the canonical public Events Portal URL.
    Used for all primary promotional sharing (posters, WhatsApp, LinkedIn, main QR code).
    """
    from core.models import SystemSetting
    custom_portal = SystemSetting.objects.filter(key='EVENTS_PORTAL_URL').first()
    if custom_portal and custom_portal.value and custom_portal.value.strip():
        return custom_portal.value.strip().rstrip('/')
    return f"{get_public_base_url()}/events/"


def get_company_website_url():
    """
    Returns the configured primary company homepage URL (e.g. http://localhost:8080/ or http://127.0.0.1:8000/).
    Used across navigation logo and 'Visit Our Website' footer links.
    """
    from core.models import SystemSetting
    custom_company = SystemSetting.objects.filter(key='COMPANY_WEBSITE_URL').first()
    if custom_company and custom_company.value and custom_company.value.strip():
        return custom_company.value.strip().rstrip('/')
    return get_public_base_url()


def generate_qr_code_data_uri(content_url):
    """
    Generates a high-quality base64 PNG data URI for a QR code pointing to content_url.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2
    )
    qr.add_data(content_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#07132e", back_color="#ffffff")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')


def render_certificate_document(
    template_data, event_name, participant_name, issue_date,
    certificate_id, organizer_name, verification_url,
    signatory_name=None, signatory_title=None, is_preview=False
):
    """
    Renders high-fidelity, printable, professional HTML/CSS certificate.
    Supports A4 Landscape (1120x792) and Portrait (792x1120), border themes,
    and replaces dynamic placeholders {{participant_name}}, {{event_name}},
    {{issue_date}}, {{certificate_id}}, {{organizer_name}}.
    """
    if hasattr(template_data, 'to_snapshot'):
        t = template_data.to_snapshot()
    elif isinstance(template_data, dict):
        t = template_data
    else:
        t = {}

    orientation = t.get('orientation', 'LANDSCAPE')
    is_portrait = orientation == 'PORTRAIT'
    width = t.get('width', 792 if is_portrait else 1120)
    height = t.get('height', 1120 if is_portrait else 792)

    bg_type = t.get('background_type', 'COLOR')
    bg_color = t.get('background_color', '#ffffff')
    bg_gradient = t.get('background_gradient', '')
    bg_img = t.get('background_image_url', '')

    bg_css = f"background-color: {bg_color};"
    if bg_type == 'GRADIENT' and bg_gradient:
        bg_css = f"background: {bg_gradient};"
    elif bg_type == 'IMAGE' and bg_img:
        bg_css = f"background: url('{bg_img}') center/cover no-repeat;"

    border_style = t.get('border_style', 'classic_gold')
    border_color = t.get('border_color', '#1465f4')
    border_width = t.get('border_width', 8)

    title = t.get('title', 'CERTIFICATE OF ACHIEVEMENT')
    subtitle = t.get('subtitle', 'PROUDLY PRESENTED TO')
    raw_desc = t.get('description_template', 'For successfully participating in and completing {{event_name}} organized by {{organizer_name}} on {{issue_date}}.')

    # Replace placeholders
    desc = raw_desc.replace('{{participant_name}}', str(participant_name))\
                   .replace('{{event_name}}', str(event_name))\
                   .replace('{{event_title}}', str(event_name))\
                   .replace('{{issue_date}}', str(issue_date))\
                   .replace('{{event_date}}', str(issue_date))\
                   .replace('{{certificate_id}}', str(certificate_id))\
                   .replace('{{organizer_name}}', str(organizer_name))

    title_rendered = title.replace('{{event_name}}', str(event_name))\
                          .replace('{{event_title}}', str(event_name))\
                          .replace('{{organizer_name}}', str(organizer_name))

    logo_url = t.get('logo_url', '/assets/xeyr-symbol.png') or '/assets/xeyr-symbol.png'
    signatory = signatory_name or t.get('signatory_name', 'Authorized Director')
    sig_title = signatory_title or t.get('signatory_title', 'Director, XEYR Technologies')
    sig_img = t.get('signature_url', '')
    show_qr = t.get('show_qr_code', True)

    qr_data_uri = generate_qr_code_data_uri(verification_url) if (show_qr and verification_url) else ''

    # Border frame HTML
    border_frame_style = "border: 2px solid rgba(20, 101, 244, 0.2);"
    corner_decorations = ""

    if border_style == 'classic_gold':
        border_frame_style = f"border: {border_width}px solid #d97706; outline: 3px solid #07132e; outline-offset: -12px;"
        corner_decorations = """
            <div style="position: absolute; top: 18px; left: 18px; width: 40px; height: 40px; border-top: 3px solid #d97706; border-left: 3px solid #d97706;"></div>
            <div style="position: absolute; top: 18px; right: 18px; width: 40px; height: 40px; border-top: 3px solid #d97706; border-right: 3px solid #d97706;"></div>
            <div style="position: absolute; bottom: 18px; left: 18px; width: 40px; height: 40px; border-bottom: 3px solid #d97706; border-left: 3px solid #d97706;"></div>
            <div style="position: absolute; bottom: 18px; right: 18px; width: 40px; height: 40px; border-bottom: 3px solid #d97706; border-right: 3px solid #d97706;"></div>
        """
    elif border_style == 'modern_blue':
        border_frame_style = f"border: {border_width}px solid {border_color}; outline: 2px solid #27d4f4; outline-offset: -14px; box-shadow: inset 0 0 40px rgba(20, 101, 244, 0.08);"
        corner_decorations = """
            <div style="position: absolute; top: 20px; left: 20px; width: 32px; height: 32px; border-top: 3px solid #27d4f4; border-left: 3px solid #27d4f4;"></div>
            <div style="position: absolute; top: 20px; right: 20px; width: 32px; height: 32px; border-top: 3px solid #27d4f4; border-right: 3px solid #27d4f4;"></div>
            <div style="position: absolute; bottom: 20px; left: 20px; width: 32px; height: 32px; border-bottom: 3px solid #27d4f4; border-left: 3px solid #27d4f4;"></div>
            <div style="position: absolute; bottom: 20px; right: 20px; width: 32px; height: 32px; border-bottom: 3px solid #27d4f4; border-right: 3px solid #27d4f4;"></div>
        """
    elif border_style == 'double_line':
        border_frame_style = f"border: {border_width}px double {border_color};"
    elif border_style == 'minimal_clean':
        border_frame_style = f"border: 2px solid {border_color}; border-radius: 12px;"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Certificate - {participant_name} - {certificate_id}</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Great+Vibes&display=swap">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #04091a;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }}
    .certificate-container {{
      width: {width}px;
      height: {height}px;
      max-width: 100%;
      position: relative;
      {bg_css}
      {border_frame_style}
      padding: 48px 56px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      color: #07132e;
      overflow: hidden;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);
    }}
    .cert-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      border-bottom: 1px solid rgba(15, 23, 42, 0.08);
      padding-bottom: 18px;
    }}
    .cert-logo-wrap {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}
    .cert-logo-img {{
      height: 48px;
      width: auto;
      object-fit: contain;
    }}
    .cert-org-name {{
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #07132e;
    }}
    .cert-seal-badge {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 600;
      color: #1465f4;
      background: rgba(20, 101, 244, 0.08);
      padding: 4px 10px;
      border-radius: 9999px;
      border: 1px solid rgba(20, 101, 244, 0.2);
    }}
    .cert-body {{
      text-align: center;
      margin: auto 0;
      padding: 10px 20px;
    }}
    .cert-title {{
      font-family: 'Cinzel', serif;
      font-size: 32px;
      font-weight: 700;
      letter-spacing: 0.12em;
      color: #07132e;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .cert-subtitle {{
      font-size: 14px;
      font-weight: 600;
      letter-spacing: 0.18em;
      color: #64748b;
      text-transform: uppercase;
      margin-bottom: 14px;
    }}
    .cert-recipient-name {{
      font-family: 'Cinzel', serif;
      font-size: 38px;
      font-weight: 700;
      color: #07132e;
      margin: 12px 0 16px 0;
      padding-bottom: 6px;
      display: inline-block;
      border-bottom: 2px solid {border_color};
    }}
    .cert-desc {{
      font-size: 16px;
      line-height: 1.6;
      color: #334155;
      max-width: 820px;
      margin: 0 auto;
    }}
    .cert-event-highlight {{
      font-weight: 700;
      color: #1465f4;
    }}
    .cert-footer {{
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      width: 100%;
      border-top: 1px solid rgba(15, 23, 42, 0.08);
      padding-top: 20px;
    }}
    .cert-meta {{
      font-size: 12px;
      color: #64748b;
      line-height: 1.6;
    }}
    .cert-meta strong {{
      color: #07132e;
      font-family: monospace;
    }}
    .cert-qr-wrap {{
      text-align: center;
    }}
    .cert-qr-img {{
      width: 72px;
      height: 72px;
      display: block;
      margin: 0 auto 4px auto;
      border: 1px solid rgba(15, 23, 42, 0.1);
      border-radius: 4px;
      padding: 2px;
      background: #ffffff;
    }}
    .cert-qr-caption {{
      font-size: 10px;
      color: #64748b;
      text-decoration: none;
    }}
    .cert-signature-wrap {{
      text-align: right;
    }}
    .cert-sig-script {{
      font-family: 'Great Vibes', cursive;
      font-size: 30px;
      color: #07132e;
      line-height: 1;
      margin-bottom: 4px;
    }}
    .cert-sig-img {{
      max-height: 44px;
      max-width: 140px;
      object-fit: contain;
      margin-bottom: 4px;
    }}
    .cert-sig-name {{
      font-size: 13px;
      font-weight: 700;
      color: #07132e;
    }}
    .cert-sig-title {{
      font-size: 11px;
      color: #64748b;
    }}
    @media print {{
      body {{ background: transparent; padding: 0; }}
      .certificate-container {{ box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <div class="certificate-container">
    {corner_decorations}
    
    <div class="cert-header">
      <div class="cert-logo-wrap">
        <img src="{logo_url}" alt="Logo" class="cert-logo-img" onerror="this.style.display='none'">
        <span class="cert-org-name">{organizer_name}</span>
      </div>
      <div class="cert-seal-badge">
        <span>✓ VERIFIED CREDENTIAL</span>
      </div>
    </div>

    <div class="cert-body">
      <div class="cert-title">{title_rendered}</div>
      <div class="cert-subtitle">{subtitle}</div>
      <div>
        <div class="cert-recipient-name">{participant_name}</div>
      </div>
      <p class="cert-desc">{desc}</p>
    </div>

    <div class="cert-footer">
      <div class="cert-meta">
        <div>Certificate ID: <strong>{certificate_id}</strong></div>
        <div>Issue Date: <strong>{issue_date}</strong></div>
        <div>Authorized By: <strong>{organizer_name}</strong></div>
      </div>

      {"<div class='cert-qr-wrap'><a href='" + verification_url + "' target='_blank'><img src='" + qr_data_uri + "' alt='Verification QR Code' class='cert-qr-img'></a><a href='" + verification_url + "' target='_blank' class='cert-qr-caption'>Scan to Verify Authenticity</a></div>" if show_qr and qr_data_uri else ""}

      <div class="cert-signature-wrap">
        {"<img src='" + sig_img + "' alt='Signature' class='cert-sig-img'>" if sig_img else "<div class='cert-sig-script'>" + signatory + "</div>"}
        <div class="cert-sig-name">{signatory}</div>
        <div class="cert-sig-title">{sig_title}</div>
      </div>
    </div>
  </div>
</body>
</html>"""
    return html



# ==============================================================================
# PUBLIC EVENTS & WEBPAGE INTEGRATION
# ==============================================================================

class PublicEventsFeedView(APIView):
    """
    Public feed for upcoming, featured, and completed events with dynamic filtering.
    Enforces business logic:
    - If no upcoming events match, has_upcoming is False (frontend shows single Get Notified CTA).
    - If upcoming events exist, notification CTA is hidden.
    - Completed events automatically segregated.
    - Supports query parameters: category, mode, is_paid, search.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        today = timezone.now().date()

        # Auto-update status for past events if not manually locked
        past_events = EventListing.objects.filter(
            status__in=['UPCOMING', 'PUBLISHED'],
            event_date__lt=today
        )
        for pe in past_events:
            pe.status = EventListing.EventStatus.COMPLETED
            pe.save(update_fields=['status'])

        # Base upcoming query
        upcoming = EventListing.objects.filter(
            is_published=True,
            is_active=True,
            status__in=['UPCOMING', 'PUBLISHED', 'ONGOING'],
            event_date__gte=today
        ).exclude(status__in=['COMPLETED', 'CANCELLED', 'ARCHIVED', 'DRAFT']).distinct().order_by('event_date', 'id')

        # Optional filters
        category = request.query_params.get('category')
        mode = request.query_params.get('mode')
        is_paid = request.query_params.get('is_paid')
        search = request.query_params.get('search')

        if category and category.strip().upper() != 'ALL':
            upcoming = upcoming.filter(event_type__iexact=category.strip())
        if mode and mode.strip().upper() != 'ALL':
            upcoming = upcoming.filter(mode__icontains=mode.strip())
        if is_paid is not None and is_paid != '':
            if is_paid.lower() in ['true', '1', 'paid']:
                upcoming = upcoming.filter(is_paid=True)
            elif is_paid.lower() in ['false', '0', 'free']:
                upcoming = upcoming.filter(is_paid=False)
        if search and search.strip():
            s = search.strip()
            upcoming = upcoming.filter(
                models.Q(title__icontains=s) |
                models.Q(short_description__icontains=s) |
                models.Q(venue__icontains=s) |
                models.Q(event_type__icontains=s)
            )

        # Completed: marked completed or event_date in the past
        completed = EventListing.objects.filter(
            is_published=True,
            is_active=True,
            status=EventListing.EventStatus.COMPLETED
        )

        # Featured events
        featured = EventListing.objects.filter(
            is_published=True,
            is_active=True,
            is_featured=True
        ).exclude(status__in=['CANCELLED', 'ARCHIVED', 'DRAFT']).distinct()[:6]

        categories = list(EventListing.objects.filter(is_published=True, is_active=True).values_list('event_type', flat=True).distinct())

        return Response({
            'has_upcoming': upcoming.exists(),
            'empty_state_cta': not upcoming.exists(),
            'upcoming_count': upcoming.count(),
            'upcoming_events': EventListingSerializer(upcoming[:4], many=True).data,
            'featured_events': EventListingSerializer(featured, many=True).data,
            'categories': categories,
            'has_completed': completed.exists(),
            'completed_count': completed.count(),
            'completed_events': EventListingSerializer(completed, many=True).data
        })


class PublicEventDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug_or_id):
        if str(slug_or_id).isdigit():
            event = EventListing.objects.filter(id=int(slug_or_id)).first()
        else:
            event = EventListing.objects.filter(slug=slug_or_id).first()

        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        # Draft / Unpublished safeguard: only staff can preview unpublished events
        if not event.is_published:
            is_admin_preview = request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request.user, 'role', '') in ['SUPER_ADMIN', 'BUSINESS_ADMIN'])
            if not is_admin_preview:
                return Response({'error': 'This event is currently in draft mode and not publicly available.'}, status=status.HTTP_404_NOT_FOUND)

        base_url = get_public_base_url()
        event_data = EventListingSerializer(event).data
        canonical_url = f"{base_url}/event.html?slug={event.slug}"

        event_data['canonical_public_url'] = canonical_url
        event_data['share_url'] = canonical_url
        event_data['qr_code_target_url'] = canonical_url
        event_data['is_registration_open'] = event.is_registration_open
        event_data['confirmed_count'] = event.confirmed_count
        event_data['available_seats'] = (event.max_participants - event.confirmed_count) if event.max_participants else None

        return Response(event_data)


class PublicEventDynamicRegisterView(APIView):
    """
    Handles dynamic registration for free and paid events.
    1. Validates event capacity with concurrency lock.
    2. Validates configured dynamic form fields.
    3. Saves EventRegistration.
    4. If free -> Confirmed immediately.
    5. If paid -> Generates Razorpay Order and returns checkout payload.
    """
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request, event_id):
        try:
            event = EventListing.objects.select_for_update().get(id=event_id)
        except EventListing.DoesNotExist:
            return Response({'error': 'Event does not exist.'}, status=status.HTTP_404_NOT_FOUND)

        if not event.is_registration_open:
            return Response({'error': 'Registrations for this event are closed or capacity is full.'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        full_name = data.get('full_name') or data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        company_or_college = data.get('company_or_college') or data.get('company', '')
        participant_category = data.get('participant_category') or data.get('category')

        if not full_name or not str(full_name).strip():
            return Response({'error': 'Full name is required.'}, status=status.HTTP_400_BAD_REQUEST)

        clean_email = str(email).strip().lower() if email else ''
        if not clean_email or '@' not in clean_email or '.' not in clean_email.split('@')[-1]:
            return Response({'error': 'A valid email address is required.'}, status=status.HTTP_400_BAD_REQUEST)

        clean_phone = re.sub(r'[^0-9]', '', str(phone or ''))
        if len(clean_phone) < 7:
            return Response({'error': 'A valid phone number with at least 7 digits is required.'}, status=status.HTTP_400_BAD_REQUEST)

        if not participant_category and isinstance(data.get('custom_fields'), dict):
            participant_category = data['custom_fields'].get('participant_category')

        if not participant_category:
            participant_category = 'Student'
        elif str(participant_category).strip() not in ['Student', 'Working Professional']:
            return Response({'error': "Participant Category must be either 'Student' or 'Working Professional'."}, status=status.HTTP_400_BAD_REQUEST)

        normalized_email = clean_email

        # Enforce uniqueness: Prevent duplicate confirmed registrations for the same event
        if EventRegistration.objects.filter(
            event=event,
            email__iexact=normalized_email,
            registration_status=EventRegistration.RegistrationStatus.CONFIRMED
        ).exists():
            return Response({
                'error': 'A confirmed registration with this email address already exists for this event.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Enforce seat capacity limit safely under atomic lock
        if event.max_participants and event.confirmed_count >= event.max_participants:
            return Response({
                'error': 'This event has reached maximum capacity. Registrations are currently closed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate dynamic fields configured for this event
        custom_dict = data.get('custom_fields') if isinstance(data.get('custom_fields'), dict) else {}
        form_responses = {
            'participant_category': str(participant_category).strip()
        }
        for field in event.form_fields.all():
            val = data.get(field.field_name) or data.get(field.field_label) or custom_dict.get(field.field_name) or custom_dict.get(field.field_label)
            if field.is_required and not val:
                return Response({'error': f"Field '{field.field_label}' is required."}, status=status.HTTP_400_BAD_REQUEST)
            form_responses[field.field_name] = val

        # Create registration record
        is_paid_event = event.is_paid and event.fee_amount > 0

        user_to_link = None
        if request.user and request.user.is_authenticated:
            user_to_link = request.user
        else:
            from core.models import User
            user_to_link = User.objects.filter(email__iexact=normalized_email).first()

        reg = EventRegistration.objects.create(
            event=event,
            user=user_to_link,
            event_name=event.title,
            full_name=full_name.strip(),
            email=normalized_email,
            phone=phone.strip(),
            company_or_college=company_or_college.strip(),
            form_responses=form_responses,
            registration_status=EventRegistration.RegistrationStatus.PENDING_PAYMENT if is_paid_event else EventRegistration.RegistrationStatus.CONFIRMED,
            payment_status=EventRegistration.PaymentStatus.PENDING if is_paid_event else EventRegistration.PaymentStatus.NOT_REQUIRED,
            fee_paid=Decimal('0.00'),
            status='Confirmed' if not is_paid_event else 'Pending Payment'
        )

        if user_to_link and hasattr(user_to_link, 'profile') and not is_paid_event:
            user_to_link.profile.verified_points += 10
            user_to_link.profile.save()


        # Central CRM Enquiry logging
        Enquiry.objects.create(
            client_name=company_or_college or full_name,
            contact_person=full_name,
            email=email,
            phone=phone,
            service_type=f"Event Registration: {event.title}",
            project_title=f"Event Registration - {event.title}",
            project_description=f"Registration Reference: {reg.registration_reference}\nEvent: {event.title}\nResponses: {form_responses}",
            source="Website (dynamic-event-registration)",
            status=EnquiryStatus.NEW
        )

        AuditLog.log('EVENT_REGISTRATION_CREATED', 'EventRegistration', reg.id, details={
            'event': event.title,
            'ref': reg.registration_reference,
            'is_paid': is_paid_event
        }, request=request)

        # If Free Event -> Confirmation immediate
        if not is_paid_event:
            # Send confirmation email if configured
            try:
                send_mail(
                    subject=f"Registration Confirmed: {event.title} - XEYR Technologies",
                    message=(
                        f"Hello {full_name},\n\n"
                        f"Your registration for '{event.title}' is CONFIRMED!\n\n"
                        f"Registration Reference: {reg.registration_reference}\n"
                        f"Date: {event.date_time or event.event_date}\n"
                        f"Venue / Mode: {event.venue} ({event.mode})\n\n"
                        f"Thank you,\nXEYR Technologies Private Limited\nhttps://xeyr.in"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True
                )
            except Exception:
                pass

            return Response({
                'success': True,
                'is_paid': False,
                'payment_required': False,
                'registration_id': reg.id,
                'registration_status': reg.registration_status,
                'payment_status': reg.payment_status,
                'registration_reference': reg.registration_reference,
                'message': 'Your registration has been confirmed! We look forward to seeing you.',
                'event_title': event.title
            }, status=status.HTTP_201_CREATED)

        # If Paid Event -> Create Razorpay Order
        amount_paise = int(event.fee_amount * 100)
        rzp_order_id = f"order_{reg.registration_reference.replace('-', '_')}"

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            rzp_order = client.order.create({
                'amount': amount_paise,
                'currency': event.currency or 'INR',
                'receipt': reg.registration_reference,
                'notes': {
                    'event_id': str(event.id),
                    'registration_ref': reg.registration_reference,
                    'participant': full_name
                }
            })
            rzp_order_id = rzp_order.get('id', rzp_order_id)
        except Exception as e:
            # Fallback for local testing / unconfigured credentials
            # Still generates a deterministic test order ID
            rzp_order_id = f"order_test_{reg.registration_reference.replace('-', '_')}"

        pay_order = EventPaymentOrder.objects.create(
            registration=reg,
            event=event,
            razorpay_order_id=rzp_order_id,
            amount=event.fee_amount,
            currency=event.currency or 'INR',
            status='CREATED'
        )

        reg.payment_status = EventRegistration.PaymentStatus.ORDER_CREATED
        reg.save(update_fields=['payment_status'])

        return Response({
            'success': True,
            'is_paid': True,
            'payment_required': True,
            'registration_id': reg.id,
            'registration_status': reg.registration_status,
            'payment_status': reg.payment_status,
            'registration_reference': reg.registration_reference,
            'razorpay_order_id': rzp_order_id,
            'amount': float(event.fee_amount),
            'amount_in_paise': amount_paise,
            'currency': event.currency or 'INR',
            'key_id': settings.RAZORPAY_KEY_ID,
            'event_title': event.title,
            'participant_name': full_name,
            'participant_email': email,
            'participant_phone': phone
        }, status=status.HTTP_201_CREATED)


class PublicEventVerifyPaymentView(APIView):
    """
    Verifies Razorpay payment signature securely on the server.
    Ensures payment is NOT trusted from mere browser redirect.
    On valid signature:
    - Marks payment as PAID
    - Confirms registration
    - Generates financial ledger payment record
    - Sends transactional confirmation email
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        registration_ref = data.get('registration_reference')
        order_id = data.get('razorpay_order_id')
        payment_id = data.get('razorpay_payment_id')
        signature = data.get('razorpay_signature')

        if not order_id or not payment_id:
            return Response({'error': 'Missing payment credentials.'}, status=status.HTTP_400_BAD_REQUEST)

        order = EventPaymentOrder.objects.filter(razorpay_order_id=order_id).first()
        if not order:
            return Response({'error': 'Payment order not found.'}, status=status.HTTP_404_NOT_FOUND)

        reg = order.registration

        # Server-side HMAC SHA256 Signature Verification
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '') or 'rzp_test_placeholder_secret'
        generated_signature = hmac.new(
            key_secret.encode('utf-8'),
            f"{order_id}|{payment_id}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Strict constant-time signature verification (prevents timing attacks and bypasses)
        is_valid = bool(signature and hmac.compare_digest(generated_signature, signature))

        if not is_valid:
            order.status = 'FAILED'
            order.save(update_fields=['status'])
            reg.payment_status = EventRegistration.PaymentStatus.FAILED
            reg.save(update_fields=['payment_status'])
            AuditLog.log('EVENT_PAYMENT_FAILED', 'EventPaymentOrder', order.id, details={'order_id': order_id, 'payment_id': payment_id}, request=request)
            return Response({'error': 'Payment signature verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Idempotent confirmation: if already verified, return success
        if order.status == 'PAID' and reg.registration_status == 'CONFIRMED':
            return Response({
                'success': True,
                'message': 'Payment already verified.',
                'registration_reference': reg.registration_reference
            })

        # Update records
        order.status = 'PAID'
        order.razorpay_payment_id = payment_id
        order.razorpay_signature = signature or generated_signature
        order.verified_at = timezone.now()
        order.save()

        reg.registration_status = EventRegistration.RegistrationStatus.CONFIRMED
        reg.payment_status = EventRegistration.PaymentStatus.PAID
        reg.fee_paid = order.amount
        reg.status = 'Confirmed'
        reg.save()

        # Record in central financial ledger
        PaymentRecord.objects.create(
            transaction_reference=payment_id,
            payment_method=PaymentRecord.PaymentMethod.CARD_RAZORPAY_PREP,
            amount=order.amount,
            currency=order.currency,
            payment_status=PaymentRecord.PaymentStatus.VERIFIED,
            notes=f"Event fee for {order.event.title} - Reg Ref: {reg.registration_reference}"
        )

        AuditLog.log('EVENT_PAYMENT_VERIFIED', 'EventPaymentOrder', order.id, details={
            'order_id': order_id,
            'payment_id': payment_id,
            'amount': str(order.amount),
            'reg_ref': reg.registration_reference
        }, request=request)

        # Send confirmation email
        try:
            send_mail(
                subject=f"Payment Verified & Registration Confirmed: {order.event.title}",
                message=(
                    f"Hello {reg.full_name},\n\n"
                    f"Your payment of ₹{order.amount} has been verified.\n"
                    f"Your registration for '{order.event.title}' is fully CONFIRMED!\n\n"
                    f"Registration Reference: {reg.registration_reference}\n"
                    f"Payment Transaction ID: {payment_id}\n"
                    f"Date: {order.event.date_time or order.event.event_date}\n"
                    f"Venue: {order.event.venue} ({order.event.mode})\n\n"
                    f"Thank you,\nXEYR Technologies Private Limited"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[reg.email],
                fail_silently=True
            )
        except Exception:
            pass

        return Response({
            'success': True,
            'message': 'Payment successfully verified! Your event registration is confirmed.',
            'registration_reference': reg.registration_reference,
            'registration_status': reg.registration_status,
            'payment_status': reg.payment_status,
            'transaction_id': payment_id,
            'amount_paid': float(order.amount)
        })


class PublicRazorpayWebhookView(APIView):
    """
    Validates Razorpay payment webhooks server-side via HMAC SHA-256.
    Idempotently handles payment.captured and order.paid.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')
        raw_body = request.body
        received_signature = request.headers.get('X-Razorpay-Signature') or request.META.get('HTTP_X_RAZORPAY_SIGNATURE')

        if webhook_secret:
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()

            if not received_signature or not hmac.compare_digest(expected_signature, received_signature):
                return Response({'error': 'Invalid webhook signature.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event_payload = json.loads(raw_body.decode('utf-8'))
        except Exception:
            return Response({'error': 'Malformed JSON body.'}, status=status.HTTP_400_BAD_REQUEST)

        event_name = event_payload.get('event')
        entity = event_payload.get('payload', {}).get('payment', {}).get('entity', {})
        order_id = entity.get('order_id')
        payment_id = entity.get('id')

        if event_name in ['payment.captured', 'order.paid'] and order_id:
            order = EventPaymentOrder.objects.filter(razorpay_order_id=order_id).first()
            if order and order.status != 'PAID':
                reg = order.registration
                order.status = 'PAID'
                order.razorpay_payment_id = payment_id
                order.verified_at = timezone.now()
                order.raw_response = event_payload
                order.save()

                reg.registration_status = EventRegistration.RegistrationStatus.CONFIRMED
                reg.payment_status = EventRegistration.PaymentStatus.PAID
                reg.fee_paid = order.amount
                reg.status = 'Confirmed'
                reg.save()

                PaymentRecord.objects.get_or_create(
                    transaction_reference=payment_id,
                    defaults={
                        'payment_method': PaymentRecord.PaymentMethod.CARD_RAZORPAY_PREP,
                        'amount': order.amount,
                        'currency': order.currency,
                        'payment_status': PaymentRecord.PaymentStatus.VERIFIED,
                        'notes': f"Webhook confirmed fee for {order.event.title} - Reg: {reg.registration_reference}"
                    }
                )
                AuditLog.log('WEBHOOK_PAYMENT_CAPTURED', 'EventPaymentOrder', order.id, details={'order_id': order_id, 'payment_id': payment_id})

        return Response({'status': 'ok'})


class PublicEventSubscribeView(APIView):
    """
    Subscribes visitor to 'Events Are Coming Up — Get Notified'.
    Features:
    - Bot / spam honeypot rejection.
    - IP-based rate limiting (5 req / min).
    - Explicit consent verification.
    - Idempotent storage in PostgreSQL.
    - Privacy protection: avoids revealing existing email subscriptions to prevent enumeration.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # 1. Bot Honeypot check: reject bots filling hidden field
        honeypot = request.data.get('website_url') or request.data.get('phone_hp')
        if honeypot:
            # Silently accept to mislead automated spam bots
            return Response({
                'success': True,
                'message': 'Thank you! You are subscribed to receive XEYR Technologies event announcements.'
            }, status=status.HTTP_200_OK)

        # 2. Rate limiting per client IP (max 5 requests per minute)
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
        cache_key = f"rate_sub_{ip}"
        sub_count = cache.get(cache_key, 0)
        if sub_count >= 5:
            return Response({
                'error': 'Too many subscription attempts from your IP. Please try again in a few minutes.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        cache.set(cache_key, sub_count + 1, 60)

        # 3. Input validation
        name = request.data.get('name') or request.data.get('full_name')
        email = request.data.get('email')
        category = request.data.get('categories') or request.data.get('category', 'ALL')
        consent = request.data.get('consent')

        if not name or not email:
            return Response({'error': 'Full name and a valid email address are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate explicit consent (rejects if explicitly false; accepts True/'true'/'1'/'on', or defaults to True if omitted for API compatibility)
        if consent is not None and consent is not True and str(consent).lower() not in ('true', '1', 'on'):
            return Response({'error': 'Explicit consent is required to receive event notifications.'}, status=status.HTTP_400_BAD_REQUEST)

        clean_name = name.strip()
        clean_email = email.strip().lower()

        # Basic email syntax sanity check
        if '@' not in clean_email or '.' not in clean_email.split('@')[-1]:
            return Response({'error': 'Please provide a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Idempotent persistence
        subscriber, created = EventNotificationSubscriber.objects.get_or_create(
            email=clean_email,
            defaults={
                'full_name': clean_name,
                'categories_of_interest': category,
                'consent_given': True,
                'is_active': True
            }
        )

        if not created:
            subscriber.full_name = clean_name
            subscriber.consent_given = True
            subscriber.is_active = True
            subscriber.categories_of_interest = category
            subscriber.save(update_fields=['full_name', 'consent_given', 'is_active', 'categories_of_interest'])

        AuditLog.log(
            'EVENT_SUBSCRIBER_REGISTERED',
            'EventNotificationSubscriber',
            subscriber.id,
            details={'email': subscriber.email, 'is_new': created},
            request=request
        )

        # 5. Privacy: Uniform confirmation message prevents email enumeration
        return Response({
            'success': True,
            'message': 'Thank you! You are subscribed to receive XEYR Technologies event announcements.',
            'subscriber_id': subscriber.id
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PublicEventUnsubscribeView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        subscriber = EventNotificationSubscriber.objects.filter(unsubscribe_token=token).first()
        if not subscriber:
            return Response({'error': 'Invalid unsubscribe token.'}, status=status.HTTP_404_NOT_FOUND)

        subscriber.is_active = False
        subscriber.save(update_fields=['is_active'])
        return Response({'success': True, 'message': 'You have been unsubscribed from XEYR event notifications.'})


class PublicSocialMediaLinksView(APIView):
    """
    Returns public social links and QR code image URLs for the footer.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        configs = SocialMediaConfig.objects.filter(is_public=True)
        data = []
        for c in configs:
            if c.platform_url or c.qr_code_image:
                data.append({
                    'platform_key': c.platform_key,
                    'platform_name': c.platform_name,
                    'platform_url': c.platform_url,
                    'qr_code_url': c.qr_code_image.url if c.qr_code_image else None
                })
        return Response(data)


# ==============================================================================
# ADMIN EVENT MANAGEMENT APIS
# ==============================================================================

def _normalize_event_data(data, files=None):
    if hasattr(data, 'dict'):
        norm = data.dict()
    elif hasattr(data, 'items'):
        norm = {k: v for k, v in data.items()}
    else:
        norm = dict(data)
    if files:
        for k, v in files.items():
            norm[k] = v
    if 'category' in norm and not norm.get('event_type'):
        norm['event_type'] = norm['category']
    if 'location_type' in norm and not norm.get('mode'):
        norm['mode'] = norm['location_type']
    if 'venue_name' in norm and not norm.get('venue'):
        norm['venue'] = norm['venue_name']
    if 'registration_fee' in norm and not norm.get('fee_amount'):
        norm['fee_amount'] = norm['registration_fee']
    if 'capacity' in norm and not norm.get('max_participants'):
        norm['max_participants'] = norm['capacity']
    if 'short_summary' in norm and not norm.get('short_description'):
        norm['short_description'] = norm['short_summary']

    try:
        raw_fee = norm.get('fee_amount') or norm.get('registration_fee') or '0'
        fee_amt = Decimal(str(raw_fee))
        if fee_amt > 0:
            norm['is_paid'] = True
            if not norm.get('fee'):
                norm['fee'] = f"₹{fee_amt}"
        else:
            norm['is_paid'] = False
            if not norm.get('fee'):
                norm['fee'] = 'Free'
    except Exception:
        pass

    if 'is_published' in norm:
        norm['is_published'] = str(norm['is_published']).lower() in ('true', '1', 't')

    for json_field in ['mentors', 'schedule', 'learning_outcomes', 'faqs', 'appearance', 'gallery_urls']:
        if json_field in norm and isinstance(norm[json_field], str):
            try:
                norm[json_field] = json.loads(norm[json_field])
            except Exception:
                pass

    if norm.get('event_date') and not norm.get('date_time'):
        dt_str = str(norm['event_date'])
        if norm.get('start_time'):
            dt_str += f" ({norm['start_time']}"
            if norm.get('end_time'):
                dt_str += f" - {norm['end_time']}"
            dt_str += ")"
        norm['date_time'] = dt_str

    return norm


DEFAULT_REGISTRATION_FIELDS = [
    {
        'field_label': 'Full Name',
        'field_name': 'full_name',
        'field_type': 'text',
        'is_required': True,
        'placeholder': 'Your full name',
        'display_order': 1,
    },
    {
        'field_label': 'Email Address',
        'field_name': 'email',
        'field_type': 'email',
        'is_required': True,
        'placeholder': 'you@example.com',
        'display_order': 2,
    },
    {
        'field_label': 'Phone Number',
        'field_name': 'phone',
        'field_type': 'phone',
        'is_required': True,
        'placeholder': '+91 00000 00000',
        'display_order': 3,
    },
    {
        'field_label': 'Participant Category',
        'field_name': 'participant_category',
        'field_type': 'dropdown',
        'is_required': True,
        'placeholder': 'Select your category',
        'options': "Student\nWorking Professional",
        'display_order': 4,
    },
]


def ensure_default_event_form_fields(event):
    """
    Ensures that every event automatically has the mandatory default registration fields:
    1. Full Name
    2. Email Address
    3. Phone Number
    4. Participant Category (Student / Working Professional)
    Preserves all existing dynamic fields and does not duplicate fields.
    """
    for df in DEFAULT_REGISTRATION_FIELDS:
        if not EventFormField.objects.filter(event=event, field_name=df['field_name']).exists():
            EventFormField.objects.create(
                event=event,
                field_label=df['field_label'],
                field_name=df['field_name'],
                field_type=df['field_type'],
                is_required=df['is_required'],
                placeholder=df.get('placeholder', ''),
                options=df.get('options', ''),
                display_order=df['display_order']
            )


class AdminEventCRUDView(APIView):
    permission_classes = [IsStaffOrAdminPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        events = EventListing.objects.all()
        return Response(EventListingSerializer(events, many=True).data)

    def post(self, request):
        data = _normalize_event_data(request.data, getattr(request, 'FILES', None))
        # Basic validation
        title = data.get('title')
        if not title:
            return Response({'error': 'Event title is required.'}, status=status.HTTP_400_BAD_REQUEST)

        slug = data.get('slug')
        if not slug:
            slug = title.lower().replace(' ', '-').replace('&', 'and')[:190]
            base_slug = slug
            idx = 1
            while EventListing.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{idx}"
                idx += 1
            data['slug'] = slug

        serializer = EventListingSerializer(data=data)
        if serializer.is_valid():
            event = serializer.save()
            ensure_default_event_form_fields(event)
            AuditLog.log('EVENT_CREATED', 'EventListing', event.id, details={'title': event.title}, request=request)

            # Trigger subscriber announcements automatically if created published
            if event.is_published and event.status in ['UPCOMING', 'PUBLISHED', 'ONGOING']:
                try:
                    send_event_notification_to_subscribers(event, request=request)
                except Exception as e:
                    logger.error(f"Error dispatching automatic subscriber notification for event {event.id}: {e}")

            return Response(EventListingSerializer(event).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminEventDetailManageView(APIView):
    permission_classes = [IsStaffOrAdminPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, pk):
        try:
            return EventListing.objects.get(pk=pk)
        except EventListing.DoesNotExist:
            return None

    def get(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(EventListingSerializer(event).data)

    def put(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        was_published = bool(event.is_published and event.status in ['UPCOMING', 'PUBLISHED', 'ONGOING'])
        data = _normalize_event_data(request.data, getattr(request, 'FILES', None))
        serializer = EventListingSerializer(event, data=data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            ensure_default_event_form_fields(updated)
            is_now_published = bool(updated.is_published and updated.status in ['UPCOMING', 'PUBLISHED', 'ONGOING'])

            # Only trigger announcement when transitioning to published status
            # Safeguard: Do not send the same announcement repeatedly when an administrator edits an already-published event.
            if not was_published and is_now_published:
                try:
                    send_event_notification_to_subscribers(updated, request=request)
                except Exception as e:
                    logger.error(f"Error dispatching publication subscriber notification for event {updated.id}: {e}")

            AuditLog.log('EVENT_UPDATED', 'EventListing', updated.id, details={'title': updated.title, 'status': updated.status}, request=request)
            return Response(EventListingSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        event = self.get_object(pk)
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        hard_delete = request.query_params.get('hard_delete') == 'true'
        if hard_delete:
            if not event.can_safely_delete:
                # Automatically safeguard by archiving rather than allowing data loss
                event.status = EventListing.EventStatus.ARCHIVED
                event.is_active = False
                event.save(update_fields=['status', 'is_active'])
                return Response({
                    'error': 'Cannot permanently delete event with existing registrations, payments, certificates, or feedback. The event has been archived instead to preserve historical participant data.'
                }, status=status.HTTP_400_BAD_REQUEST)

            title = event.title
            event.delete()
            AuditLog.log('EVENT_DELETED', 'EventListing', pk, details={'title': title}, request=request)
            return Response({'success': True, 'message': f"Draft event '{title}' was permanently deleted."})

        # Default safe behavior: Archive event so registrations, certificates and payments remain intact
        event.status = EventListing.EventStatus.ARCHIVED
        event.is_active = False
        event.save(update_fields=['status', 'is_active'])
        AuditLog.log('EVENT_ARCHIVED', 'EventListing', event.id, details={'title': event.title}, request=request)
        return Response({'success': True, 'message': 'Event successfully archived. Participant history and payment records are preserved.'})



class AdminEventFormFieldConfigView(APIView):
    """
    Dynamic Form Builder: Add/delete/reorder fields for an event.
    Automatically ensures standard default fields are configured.
    """
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if event:
            ensure_default_event_form_fields(event)
        fields = EventFormField.objects.filter(event_id=event_id)
        return Response(EventFormFieldSerializer(fields, many=True).data)

    def post(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        field = EventFormField.objects.create(
            event=event,
            field_label=data.get('field_label', 'New Field'),
            field_name=data.get('field_name') or data.get('field_label', 'field').lower().replace(' ', '_'),
            field_type=data.get('field_type', 'text'),
            is_required=data.get('is_required', True),
            placeholder=data.get('placeholder', ''),
            help_text=data.get('help_text', ''),
            options=data.get('options', ''),
            display_order=data.get('display_order', 0)
        )
        AuditLog.log('EVENT_FORM_FIELD_ADDED', 'EventFormField', field.id, details={'label': field.field_label, 'event': event.title}, request=request)
        return Response(EventFormFieldSerializer(field).data, status=status.HTTP_201_CREATED)


class AdminEventFormFieldDeleteView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def delete(self, request, pk):
        field = EventFormField.objects.filter(pk=pk).first()
        if not field:
            return Response({'error': 'Field not found'}, status=status.HTTP_404_NOT_FOUND)

        if field.field_name in ['full_name', 'email', 'phone', 'participant_category']:
            return Response({
                'error': 'Cannot delete mandatory default registration fields (Full Name, Email, Phone, Participant Category).'
            }, status=status.HTTP_400_BAD_REQUEST)

        event_id = field.event_id
        field.delete()
        AuditLog.log('EVENT_FORM_FIELD_DELETED', 'EventFormField', pk, details={'event_id': event_id}, request=request)
        return Response({'success': True, 'message': 'Field removed.'})


def send_event_notification_to_subscribers(event, request=None, force_resend=False):
    """
    Sends event notification email to active, consented subscribers.
    Checks SMTP / provider configuration:
    - If SMTP is configured without valid password, marks deliveries as FAILED
      with 'Email delivery not configured: SMTP credentials are not set.'
      and truthfully returns configured=False.
    - Prevents duplicate sends if already SENT unless force_resend=True.
    - Records every attempt in EventNotificationDelivery.
    """
    if not event.is_published or event.status in ['DRAFT', 'CANCELLED', 'ARCHIVED']:
        return {
            'success': False,
            'configured': True,
            'message': 'Cannot send announcements for unpublished, draft, or cancelled events.',
            'sent_count': 0,
            'failed_count': 0
        }

    all_subscribers = EventNotificationSubscriber.objects.filter(is_active=True, consent_given=True)
    if not all_subscribers.exists():
        return {
            'success': True,
            'configured': True,
            'message': 'No active subscribers found in the database.',
            'eligible_subscribers': 0,
            'sent_count': 0,
            'failed_count': 0
        }

    # Match subscribers by category if specific preferences are set
    subscribers = []
    event_category = (event.event_type or '').strip().lower()
    for sub in all_subscribers:
        prefs = (sub.categories_of_interest or '').strip().lower()
        if not prefs or prefs == 'all' or 'all' in [p.strip() for p in prefs.split(',')]:
            subscribers.append(sub)
        elif event_category and (event_category in prefs or any(p.strip() == event_category for p in prefs.split(','))):
            subscribers.append(sub)
        elif not event_category:
            subscribers.append(sub)

    if not subscribers:
        return {
            'success': True,
            'configured': True,
            'message': f"No active subscribers matched event category '{event.event_type}'.",
            'eligible_subscribers': 0,
            'sent_count': 0,
            'failed_count': 0
        }

    # Determine email provider configuration truthfully
    is_smtp = settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
    has_smtp_password = bool(getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
    email_configured = not (is_smtp and not has_smtp_password)

    if not email_configured:
        failed_count = 0
        for sub in subscribers:
            delivery, created = EventNotificationDelivery.objects.get_or_create(
                event=event,
                subscriber=sub,
                defaults={'status': EventNotificationDelivery.DeliveryStatus.FAILED}
            )
            if force_resend or created or delivery.status != 'SENT':
                delivery.status = EventNotificationDelivery.DeliveryStatus.FAILED
                delivery.error_message = 'Email delivery not configured: SMTP credentials (EMAIL_HOST_PASSWORD) are not set.'
                delivery.save(update_fields=['status', 'error_message'])
                failed_count += 1
        return {
            'success': False,
            'configured': False,
            'message': 'Email delivery is not configured on this server. SMTP password (EMAIL_HOST_PASSWORD) is missing.',
            'eligible_subscribers': len(subscribers),
            'sent_count': 0,
            'failed_count': failed_count
        }

    sent_count = 0
    failed_count = 0

    for sub in subscribers:
        delivery, created = EventNotificationDelivery.objects.get_or_create(
            event=event,
            subscriber=sub,
            defaults={'status': EventNotificationDelivery.DeliveryStatus.PENDING}
        )
        if not force_resend and not created and delivery.status == 'SENT':
            continue

        try:
            unsub_url = f"https://xeyr.in/api/events/subscribers/unsubscribe/{sub.unsubscribe_token}/"
            price_str = f"INR {event.fee_amount}" if event.is_paid else "Free Entry"
            body_text = (
                f"Hello {sub.full_name},\n\n"
                f"We are excited to announce an upcoming event at XEYR Technologies:\n\n"
                f"Event: {event.title}\n"
                f"Category: {event.event_type}\n"
                f"Date & Time: {event.date_time or event.event_date}\n"
                f"Mode & Venue: {event.mode} ({event.venue})\n"
                f"Registration Fee: {price_str}\n\n"
                f"Overview:\n{event.short_description or event.description}\n\n"
                f"View details & register: https://xeyr.in/#events\n\n"
                f"---\n"
                f"You received this email because you subscribed to event notifications from XEYR Technologies Private Limited.\n"
                f"To unsubscribe at any time: {unsub_url}\n"
            )

            send_mail(
                subject=f"New Event Announcement: {event.title} - XEYR Technologies",
                message=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sub.email],
                fail_silently=False
            )
            delivery.status = EventNotificationDelivery.DeliveryStatus.SENT
            delivery.sent_at = timezone.now()
            delivery.error_message = ''
            delivery.save(update_fields=['status', 'sent_at', 'error_message'])
            sent_count += 1
        except Exception as e:
            delivery.status = EventNotificationDelivery.DeliveryStatus.FAILED
            delivery.error_message = str(e)
            delivery.save(update_fields=['status', 'error_message'])
            failed_count += 1

    if request:
        AuditLog.log('EVENT_SUBSCRIBERS_NOTIFIED', 'EventListing', event.id, details={
            'event': event.title,
            'sent': sent_count,
            'failed': failed_count,
            'configured': email_configured
        }, request=request)

    return {
        'success': True,
        'configured': True,
        'message': f"Notifications processed: {sent_count} sent, {failed_count} failed.",
        'eligible_subscribers': len(subscribers),
        'sent_count': sent_count,
        'failed_count': failed_count
    }


class AdminEventNotifySubscribersView(APIView):
    """
    Sends event announcement email to all opted-in subscribers.
    Records delivery status for every subscriber truthfully.
    """
    permission_classes = [IsStaffOrAdminPermission]

    def post(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        force_resend = str(request.data.get('force_resend', 'false')).lower() in ('true', '1')
        result = send_event_notification_to_subscribers(event, request=request, force_resend=force_resend)
        return Response(result)


class AdminSubscribersListView(APIView):
    """
    Authorized admin view for event subscribers:
    - Total active subscribers
    - Subscription dates
    - Consent status
    - Unsubscribed status
    - Notification delivery outcomes
    - Search and pagination
    """
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN', 'PROJECT_MANAGER', 'SALES_CRM']):
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        qs = EventNotificationSubscriber.objects.all().order_by('-subscribed_at')

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter == 'active':
            qs = qs.filter(is_active=True)
        elif status_filter == 'unsubscribed':
            qs = qs.filter(is_active=False)

        # Search
        q = request.query_params.get('search') or request.query_params.get('q')
        if q:
            qs = qs.filter(
                models.Q(full_name__icontains=q) |
                models.Q(email__icontains=q) |
                models.Q(categories_of_interest__icontains=q)
            )

        total_count = EventNotificationSubscriber.objects.count()
        active_count = EventNotificationSubscriber.objects.filter(is_active=True).count()
        unsubscribed_count = total_count - active_count

        total_deliveries = EventNotificationDelivery.objects.count()
        sent_deliveries = EventNotificationDelivery.objects.filter(status='SENT').count()
        failed_deliveries = EventNotificationDelivery.objects.filter(status='FAILED').count()

        serializer = EventNotificationSubscriberSerializer(qs[:100], many=True)

        return Response({
            'kpis': {
                'total_subscribers': total_count,
                'active_subscribers': active_count,
                'unsubscribed_subscribers': unsubscribed_count,
                'total_deliveries': total_deliveries,
                'sent_deliveries': sent_deliveries,
                'failed_deliveries': failed_deliveries,
            },
            'subscribers': serializer.data
        })


class AdminSubscriberDeliveryRetryView(APIView):
    """
    Allows safe retries for a failed notification delivery.
    """
    permission_classes = [IsStaffOrAdminPermission]

    def post(self, request, pk):
        delivery = EventNotificationDelivery.objects.select_related('event', 'subscriber').filter(pk=pk).first()
        if not delivery:
            return Response({'error': 'Delivery record not found.'}, status=status.HTTP_404_NOT_FOUND)

        sub = delivery.subscriber
        event = delivery.event

        if not sub.is_active:
            return Response({'error': 'Cannot retry delivery for an unsubscribed recipient.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check SMTP configuration
        is_smtp = settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
        has_smtp_password = bool(getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
        if is_smtp and not has_smtp_password:
            delivery.status = 'FAILED'
            delivery.error_message = 'Email delivery not configured: SMTP credentials (EMAIL_HOST_PASSWORD) are not set.'
            delivery.save(update_fields=['status', 'error_message'])
            return Response({
                'success': False,
                'message': 'Email delivery is not configured on this server. SMTP password is missing.'
            }, status=status.HTTP_200_OK)

        try:
            unsub_url = f"https://xeyr.in/api/events/subscribers/unsubscribe/{sub.unsubscribe_token}/"
            price_str = f"INR {event.fee_amount}" if event.is_paid else "Free Entry"
            body_text = (
                f"Hello {sub.full_name},\n\n"
                f"We are excited to announce an upcoming event at XEYR Technologies:\n\n"
                f"Event: {event.title}\n"
                f"Category: {event.event_type}\n"
                f"Date & Time: {event.date_time or event.event_date}\n"
                f"Mode & Venue: {event.mode} ({event.venue})\n"
                f"Registration Fee: {price_str}\n\n"
                f"Overview:\n{event.short_description or event.description}\n\n"
                f"View details & register: https://xeyr.in/#events\n\n"
                f"---\n"
                f"You received this email because you subscribed to event notifications from XEYR Technologies Private Limited.\n"
                f"To unsubscribe at any time: {unsub_url}\n"
            )

            send_mail(
                subject=f"New Event Announcement: {event.title} - XEYR Technologies",
                message=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[sub.email],
                fail_silently=False
            )
            delivery.status = EventNotificationDelivery.DeliveryStatus.SENT
            delivery.sent_at = timezone.now()
            delivery.error_message = ''
            delivery.save(update_fields=['status', 'sent_at', 'error_message'])
            return Response({'success': True, 'message': f'Notification re-sent successfully to {sub.email}.'})
        except Exception as e:
            delivery.status = EventNotificationDelivery.DeliveryStatus.FAILED
            delivery.error_message = str(e)
            delivery.save(update_fields=['status', 'error_message'])
            return Response({'success': False, 'error': f'Failed to send: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminSubscriberToggleStatusView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def post(self, request, pk):
        sub = EventNotificationSubscriber.objects.filter(pk=pk).first()
        if not sub:
            return Response({'error': 'Subscriber not found.'}, status=status.HTTP_404_NOT_FOUND)
        sub.is_active = not sub.is_active
        sub.save(update_fields=['is_active'])
        AuditLog.log('SUBSCRIBER_STATUS_TOGGLED', 'EventNotificationSubscriber', sub.id, details={'email': sub.email, 'is_active': sub.is_active}, request=request)
        return Response({
            'success': True,
            'is_active': sub.is_active,
            'message': f"Subscriber {'activated' if sub.is_active else 'unsubscribed'}."
        })


class AdminEventPaymentsDashboardView(APIView):
    """
    Summary view of event registrations and verified payments.
    """
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        total_regs = EventRegistration.objects.count()
        confirmed_regs = EventRegistration.objects.filter(registration_status='CONFIRMED').count()
        pending_payments = EventRegistration.objects.filter(payment_status='ORDER_CREATED').count()
        paid_payments = EventPaymentOrder.objects.filter(status='PAID').count()
        failed_payments = EventPaymentOrder.objects.filter(status='FAILED').count()

        gross_received = sum(order.amount for order in EventPaymentOrder.objects.filter(status='PAID'))
        refunds_total = sum(r.refund_amount for r in EventRefundRecord.objects.filter(status='PROCESSED'))
        net_received = gross_received - refunds_total

        recent_orders = EventPaymentOrder.objects.all().order_by('-created_at')[:30]
        subscribers_count = EventNotificationSubscriber.objects.filter(is_active=True).count()

        return Response({
            'kpis': {
                'total_registrations': total_regs,
                'confirmed_registrations': confirmed_regs,
                'pending_payments': pending_payments,
                'paid_payments': paid_payments,
                'successful_payments': paid_payments,
                'failed_payments': failed_payments,
                'gross_revenue': float(gross_received),
                'gross_received': float(gross_received),
                'refunds_total': float(refunds_total),
                'net_received': float(net_received),
                'active_subscribers': subscribers_count
            },
            'recent_orders': EventPaymentOrderSerializer(recent_orders, many=True).data
        })


class AdminSocialMediaConfigView(APIView):
    """
    Manages platform URLs and actual uploaded QR codes for Instagram and LinkedIn.
    """
    permission_classes = [IsStaffOrAdminPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        configs = SocialMediaConfig.objects.all()
        # Seed defaults if empty
        if not configs.exists():
            defaults = [
                ('INSTAGRAM', 'Instagram', 'https://instagram.com/xeyrtechnologies', 1),
                ('LINKEDIN', 'LinkedIn', 'https://linkedin.com/company/xeyrtechnologies', 2),
                ('TWITTER_X', 'Twitter / X', '', 3),
                ('GITHUB', 'GitHub', '', 4),
            ]
            for key, name, url, order in defaults:
                SocialMediaConfig.objects.create(
                    platform_key=key,
                    platform_name=name,
                    platform_url=url,
                    display_order=order
                )
            configs = SocialMediaConfig.objects.all()

        return Response(SocialMediaConfigSerializer(configs, many=True).data)

    def post(self, request):
        data = request.data
        key = data.get('platform_key')
        if key:
            config, _ = SocialMediaConfig.objects.get_or_create(
                platform_key=key,
                defaults={'platform_name': data.get('platform_name', key.capitalize())}
            )
            if 'platform_url' in data:
                config.platform_url = data['platform_url']
            if 'is_public' in data:
                config.is_public = str(data['is_public']).lower() in ('true', '1')
            if 'qr_code_image' in request.FILES:
                config.qr_code_image = request.FILES['qr_code_image']
            config.save()
            AuditLog.log('SOCIAL_CONFIG_UPDATED', 'SocialMediaConfig', config.id, details={'platform': key}, request=request)
            return Response(SocialMediaConfigSerializer(config).data)

        # Bulk or multi-key update support
        known_platforms = ['instagram', 'linkedin', 'github', 'youtube', 'twitter']
        updated = []
        for p in known_platforms:
            url_key = f"{p}_url"
            pub_key = f"{p}_public"
            qr_key = f"{p}_qr"
            if url_key in data or pub_key in data or qr_key in request.FILES:
                config, _ = SocialMediaConfig.objects.get_or_create(
                    platform_key=p,
                    defaults={'platform_name': p.capitalize()}
                )
                if url_key in data:
                    config.platform_url = data[url_key]
                if pub_key in data:
                    config.is_public = str(data[pub_key]).lower() in ('true', '1')
                if qr_key in request.FILES:
                    config.qr_code_image = request.FILES[qr_key]
                config.save()
                updated.append(config)

        if updated:
            configs = SocialMediaConfig.objects.all()
            return Response(SocialMediaConfigSerializer(configs, many=True).data)

        return Response({'error': 'Platform key or platform configuration fields required.'}, status=status.HTTP_400_BAD_REQUEST)


class AdminExportEventRegistrationsCSVView(APIView):
    """
    Exports participant registrations for an event as CSV.
    """
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        regs = EventRegistration.objects.filter(event=event).order_by('-created_at')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="xeyr_event_{event.slug}_participants.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Registration Ref', 'Full Name', 'Email', 'Phone',
            'College / Org', 'Status', 'Payment Status', 'Fee Paid', 'Date Registered', 'Form Responses'
        ])

        for r in regs:
            writer.writerow([
                r.registration_reference,
                r.full_name,
                r.email,
                r.phone,
                r.company_or_college,
                r.registration_status,
                r.payment_status,
                r.fee_paid,
                r.created_at.strftime('%Y-%m-%d %H:%M'),
                str(r.form_responses)
            ])

        return response


# ==============================================================================
# EXISTING SKILLBRIDGE & EVENT VIEWS (PRESERVED FOR BACKWARD COMPATIBILITY)
# ==============================================================================

class PublicEventRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        event_name = data.get('event') or data.get('event_name', 'General Workshop')
        name = data.get('name') or data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')

        if not name or not email or not phone:
            return Response({'error': 'Name, email and phone number are required.'}, status=status.HTTP_400_BAD_REQUEST)

        reg = EventRegistration.objects.create(
            event_name=event_name,
            full_name=name,
            company_or_college=data.get('company', ''),
            email=email,
            phone=phone,
            status='Interested'
        )

        enquiry = Enquiry.objects.create(
            client_name=data.get('company') or name,
            contact_person=name,
            email=email,
            phone=phone,
            service_type=f"Event Registration: {event_name}",
            project_title=f"Workshop Interest - {event_name}",
            project_description=f"Registered interest for event: {event_name}. Company/College: {data.get('company', 'N/A')}",
            source="Website (event-registration-interest)",
            status=EnquiryStatus.NEW
        )

        AuditLog.log('EVENT_REGISTRATION_SUBMITTED', 'EventRegistration', reg.id, details={'event': event_name, 'name': name}, request=request)
        Notification.objects.create(
            title=f"New Event Registration: {event_name}",
            message=f"{name} registered interest for '{event_name}'.",
            notification_type='EVENT_REGISTRATION',
            link="/dashboard/#events"
        )

        return Response({
            'success': True,
            'message': 'Thank you! You are on our list. We will send confirmed event details.',
            'registration_id': reg.id,
            'registration_reference': reg.registration_reference,
            'enquiry_ref': enquiry.reference_id
        }, status=status.HTTP_201_CREATED)


class PublicCollegeEnquiryView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        name = data.get('name') or data.get('contact_name')
        org = data.get('organisation') or data.get('college_name') or 'College / University'
        email = data.get('email')
        phone = data.get('phone')

        if not name or not email or not phone:
            return Response({'error': 'Name, email and phone are required.'}, status=status.HTTP_400_BAD_REQUEST)

        enquiry = Enquiry.objects.create(
            client_name=org,
            contact_person=name,
            email=email,
            phone=phone,
            organisation_type='College / University',
            service_type='SkillBridge - College Workshop',
            project_title=f"SkillBridge Training for {org}",
            project_description=f"College training request from {name} at {org}.",
            source="Website (college-service-enquiry)",
            status=EnquiryStatus.NEW
        )

        college_req = SkillBridgeCollegeEnquiry.objects.create(
            enquiry=enquiry,
            contact_name=name,
            college_name=org,
            email=email,
            phone=phone,
            preferred_service='College Training Workshop'
        )

        AuditLog.log('COLLEGE_ENQUIRY_SUBMITTED', 'SkillBridgeCollegeEnquiry', college_req.id, details={'college': org, 'contact': name}, request=request)
        Notification.objects.create(
            title=f"College Service Request: {org}",
            message=f"{name} requested practical training for {org}.",
            notification_type='COLLEGE_REQUEST',
            link=f"/dashboard/#enquiry-{enquiry.id}"
        )

        return Response({
            'success': True,
            'message': 'Thank you for your enquiry. XEYR team will reach out to discuss scope and availability.',
            'reference_id': enquiry.reference_id
        }, status=status.HTTP_201_CREATED)


class PublicSkillBridgeTrainerView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        data = request.data
        name = data.get('name') or data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        skills = data.get('skills') or data.get('skills_can_teach', 'General Technical Training')
        profile = data.get('profile') or data.get('profile_type', 'Working professional')
        resume = request.FILES.get('resume') or request.FILES.get('resume_file')

        if not name or not email or not phone:
            return Response({'error': 'Name, email and phone are required.'}, status=status.HTTP_400_BAD_REQUEST)

        app = SkillBridgeProfessionalApplication.objects.create(
            full_name=name,
            email=email,
            phone=phone,
            skills_can_teach=skills,
            profile_type=profile,
            resume_file=resume,
            status='Received'
        )

        enquiry = Enquiry.objects.create(
            client_name=f"{name} ({profile})",
            contact_person=name,
            email=email,
            phone=phone,
            organisation_type='Individual / Professional',
            service_type='SkillBridge - Trainer Application',
            project_title=f"Trainer Application: {name}",
            project_description=f"Profile: {profile}\nSkills: {skills}",
            source="Website (skillbridge-professional-application)",
            status=EnquiryStatus.NEW
        )

        AuditLog.log('TRAINER_APPLICATION_SUBMITTED', 'SkillBridgeProfessionalApplication', app.id, details={'name': name, 'profile': profile}, request=request)
        Notification.objects.create(
            title=f"Trainer Application: {name}",
            message=f"{name} applied as a {profile} to teach: {skills[:40]}...",
            notification_type='TRAINER_APP',
            link="/dashboard/#skillbridge"
        )

        return Response({
            'success': True,
            'message': 'Your application is ready! Thank you for offering your expertise to learners.',
            'application_id': app.id,
            'reference_id': enquiry.reference_id
        }, status=status.HTTP_201_CREATED)


class AdminEventsListView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        events = EventListing.objects.all()
        regs = EventRegistration.objects.all()[:50]
        return Response({
            'events': EventListingSerializer(events, many=True).data,
            'registrations': EventRegistrationSerializer(regs, many=True).data
        })


class AdminSkillBridgeListView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        colleges = SkillBridgeCollegeEnquiry.objects.all()[:50]
        trainers = SkillBridgeProfessionalApplication.objects.all()[:50]
        return Response({
            'college_enquiries': SkillBridgeCollegeEnquirySerializer(colleges, many=True).data,
            'professional_applications': SkillBridgeProfessionalApplicationSerializer(trainers, many=True).data
        })


class AdminRegistrationsListView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        qs = EventRegistration.objects.all().order_by('-created_at')
        event_id = request.query_params.get('event_id')
        if event_id and str(event_id).strip() not in ('', 'None', 'null', 'undefined'):
            try:
                qs = qs.filter(event_id=int(event_id))
            except (ValueError, TypeError):
                pass
        reg_status = request.query_params.get('status')
        if reg_status:
            qs = qs.filter(registration_status=reg_status)
        search = request.query_params.get('q')
        if search:
            qs = qs.filter(
                models.Q(full_name__icontains=search) |
                models.Q(email__icontains=search) |
                models.Q(registration_reference__icontains=search) |
                models.Q(event_name__icontains=search)
            )
        return Response(EventRegistrationSerializer(qs[:100], many=True).data)


# ==============================================================================
# PARTICIPANT DASHBOARD APIS (Authenticated Participant / Student)
# ==============================================================================

class ParticipantDashboardOverviewView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        user = request.user
        email = user.email.strip().lower()

        regs = EventRegistration.objects.filter(
            models.Q(user=user) | models.Q(email__iexact=email)
        )
        confirmed_regs = regs.filter(registration_status=EventRegistration.RegistrationStatus.CONFIRMED)

        today = timezone.now().date()
        upcoming_count = confirmed_regs.filter(
            event__event_date__gte=today
        ).exclude(event__status__in=['COMPLETED', 'CANCELLED', 'ARCHIVED']).count()

        completed_count = confirmed_regs.filter(
            models.Q(event__status='COMPLETED') | models.Q(event__event_date__lt=today)
        ).count()

        certs_count = EventCertificate.objects.filter(
            models.Q(user=user) | models.Q(recipient_email__iexact=email),
            status=EventCertificate.CertificateStatus.ISSUED
        ).count()

        pending_payments = EventPaymentOrder.objects.filter(
            registration__in=regs,
            status__in=['CREATED', 'PENDING']
        ).count()

        unread_notifs = Notification.objects.filter(
            models.Q(user=user) | models.Q(user__isnull=True),
            is_read=False
        ).count()

        return Response({
            'total_registered': confirmed_regs.count(),
            'upcoming_registered': upcoming_count,
            'completed_registered': completed_count,
            'certificates_count': certs_count,
            'pending_payments_count': pending_payments,
            'unread_notifications_count': unread_notifs,
            'verified_points': getattr(user, 'profile', None).verified_points if hasattr(user, 'profile') else 0
        })


class ParticipantRegistrationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        email = user.email.strip().lower()

        regs = EventRegistration.objects.filter(
            models.Q(user=user) | models.Q(email__iexact=email)
        ).select_related('event').order_by('-created_at')

        results = []
        for r in regs:
            cert = EventCertificate.objects.filter(registration=r, status='ISSUED').first()
            if not cert and r.event:
                cert = EventCertificate.objects.filter(
                    models.Q(user=user) | models.Q(recipient_email__iexact=email),
                    event=r.event,
                    status='ISSUED'
                ).first()

            feedback = EventFeedback.objects.filter(registration=r).first()
            if not feedback and r.event:
                feedback = EventFeedback.objects.filter(
                    models.Q(user=user) | models.Q(email__iexact=email),
                    event=r.event
                ).first()

            item = EventRegistrationSerializer(r).data
            item['event_slug'] = r.event.slug if r.event else None
            item['event_mode'] = r.event.mode if r.event else 'Online'
            item['event_venue'] = r.event.venue if r.event else 'TBA'
            item['event_date'] = r.event.event_date if r.event else None
            item['event_status'] = r.event.status if r.event else 'UNKNOWN'
            item['poster_url'] = (r.event.poster.url if r.event.poster else r.event.poster_url) if r.event else ''
            item['has_certificate'] = bool(cert)
            item['certificate_id'] = cert.certificate_id if cert else None
            item['certificate_download_url'] = f"/api/certificates/download/{cert.certificate_id}/" if cert else None
            item['has_feedback'] = bool(feedback)
            item['feedback_id'] = feedback.id if feedback else None
            results.append(item)

        return Response(results)


class ParticipantPaymentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        email = user.email.strip().lower()

        orders = EventPaymentOrder.objects.filter(
            models.Q(registration__user=user) | models.Q(registration__email__iexact=email)
        ).select_related('event', 'registration').order_by('-created_at')

        return Response(EventPaymentOrderSerializer(orders, many=True).data)


class ParticipantCertificatesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        email = user.email.strip().lower()

        certs = EventCertificate.objects.filter(
            models.Q(user=user) | models.Q(recipient_email__iexact=email),
            status=EventCertificate.CertificateStatus.ISSUED
        ).select_related('event').order_by('-issue_date')

        return Response(EventCertificateSerializer(certs, many=True).data)


def try_send_certificate_email(cert):
    """
    Safely dispatches certificate email if SMTP credentials are configured.
    Updates email_delivery_status accurately and preserves the valid certificate record on failure.
    Idempotent: retries do not generate a new certificate ID.
    """
    from django.conf import settings
    from django.core.mail import send_mail

    email_host_password = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    verify_url = f"{get_public_base_url()}/verify-certificate/{cert.certificate_id}/"
    download_url = f"{get_public_base_url()}/api/certificates/download/{cert.certificate_id}/"

    subject = f"Your Verified Certificate for {cert.event.title} — XEYR Technologies"
    body = f"""Dear {cert.recipient_name},

Congratulations on completing {cert.event.title}!

Your official verified digital certificate has been issued by {cert.organizer_name}.

Certificate ID: {cert.certificate_id}
Issue Date: {cert.issue_date}

View & Verify Online:
{verify_url}

Download Certificate:
{download_url}

Best regards,
{cert.organizer_name}
"""
    if not email_host_password:
        cert.email_delivery_status = 'NOT_CONFIGURED'
        cert.email_error = 'Live SMTP credentials (EMAIL_HOST_PASSWORD) not configured.'
        cert.save(update_fields=['email_delivery_status', 'email_error'])
        return False

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@xeyrtechnologies.com'),
            recipient_list=[cert.recipient_email],
            fail_silently=False
        )
        cert.email_delivery_status = 'SENT'
        cert.email_sent_at = timezone.now()
        cert.email_error = ''
        cert.save(update_fields=['email_delivery_status', 'email_sent_at', 'email_error'])
        return True
    except Exception as e:
        logger.warning(f"Failed to dispatch certificate email to {cert.recipient_email}: {e}")
        cert.email_delivery_status = 'FAILED'
        cert.email_error = str(e)
        cert.save(update_fields=['email_delivery_status', 'email_error'])
        return False


def evaluate_certificate_eligibility(event, registration):
    """
    Evaluates whether a participant satisfies all configured eligibility conditions for an event certificate:
    - Valid confirmed registration
    - Successful payment (for paid events)
    - Verified attendance meeting minimum attendance percentage (if enabled)
    - Mandatory feedback submission (if enabled)
    - Release date timing (must not be in the future)
    """
    if not event.certificate_enabled:
        return False, ['Certificates are not enabled for this event.']

    reasons = []

    # 1. Registration Confirmation
    if registration.registration_status != EventRegistration.RegistrationStatus.CONFIRMED:
        reasons.append('Registration is not confirmed.')

    # 2. Payment verification for paid events
    if event.is_paid:
        if registration.payment_status != 'PAID' and registration.fee_paid < event.fee_amount:
            reasons.append('Event payment has not been completed.')

    # 3. Attendance verification
    if getattr(event, 'certificate_require_attendance', True) and event.certificate_min_attendance > 0:
        att = EventAttendance.objects.filter(event=event, registration=registration).first()
        current_pct = att.attendance_percentage if att else 0
        if not att or current_pct < event.certificate_min_attendance:
            reasons.append(f'Attendance below required threshold ({current_pct}% < {event.certificate_min_attendance}%).')

    # 4. Mandatory Feedback Check
    if event.certificate_require_feedback:
        has_fb = EventFeedback.objects.filter(event=event).filter(
            models.Q(registration=registration) | models.Q(email__iexact=registration.email)
        ).exists()
        if not has_fb:
            reasons.append('Mandatory post-event feedback has not been submitted.')

    # 5. Future Release Timing Check
    if event.certificate_release_date and timezone.now() < event.certificate_release_date:
        reasons.append(f'Certificate release scheduled for {event.certificate_release_date.strftime("%B %d, %Y %H:%M UTC")}.')

    is_eligible = len(reasons) == 0
    return is_eligible, reasons


def issue_certificate_for_registration(event, registration, user=None, reissued_by=None, reissue_reason=''):
    """
    Issues or reissues an EventCertificate using the event's assigned template snapshot.
    Guarantees idempotency and prevents duplicate certificate issuance.
    """
    user = user or registration.user
    email = registration.email.strip().lower()

    existing = EventCertificate.objects.filter(event=event, registration=registration).first()
    if existing and not reissue_reason:
        return existing, False

    # Resolve Certificate Template
    template = event.certificate_template_ref
    if not template:
        template = CertificateTemplate.objects.filter(
            models.Q(is_default=True) | models.Q(status=CertificateTemplate.TemplateStatus.PUBLISHED)
        ).first()

    snapshot = template.to_snapshot() if template else {}
    if event.certificate_custom_settings:
        snapshot.update(event.certificate_custom_settings)

    if existing and reissue_reason:
        existing.recipient_name = registration.full_name
        existing.recipient_email = email
        existing.template_ref = template
        existing.template_snapshot = snapshot
        existing.reissued_at = timezone.now()
        existing.reissue_reason = reissue_reason
        existing.reissued_by = reissued_by
        existing.save()
        cert = existing
        is_new = False
    else:
        cert = EventCertificate.objects.create(
            event=event,
            registration=registration,
            user=user,
            recipient_name=registration.full_name,
            recipient_email=email,
            status='ISSUED',
            issue_date=timezone.now().date(),
            template_type=template.slug if template else (event.certificate_template or 'standard'),
            template_ref=template,
            template_snapshot=snapshot,
            organizer_name=template.organizer_name if template else (event.organizer or 'XEYR Technologies'),
            signatory_title=template.signatory_title if template else 'Director, XEYR Technologies'
        )
        is_new = True

    if user:
        Notification.objects.create(
            user=user,
            title=f"Certificate Available: {event.title}",
            message=f"Congratulations! Your digital certificate for {event.title} is now available.",
            notification_type='CERTIFICATE',
            link=f"/dashboard.html?tab=certificates"
        )
        if hasattr(user, 'profile') and is_new:
            user.profile.verified_points += 50
            user.profile.save()

    try_send_certificate_email(cert)
    return cert, is_new


class ParticipantFeedbackSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data
        event_id = data.get('event_id')
        if not event_id:
            return Response({'error': 'Event ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        email = user.email.strip().lower()

        reg = EventRegistration.objects.filter(
            event=event,
            registration_status='CONFIRMED'
        ).filter(models.Q(user=user) | models.Q(email__iexact=email)).first()

        if not reg:
            return Response({
                'error': 'Feedback can only be submitted by registered attendees for this event.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Prevent duplicate feedback submissions
        if EventFeedback.objects.filter(
            event=event
        ).filter(models.Q(registration=reg) | models.Q(user=user) | models.Q(email__iexact=email)).exists():
            return Response({'error': 'You have already submitted feedback for this event.'}, status=status.HTTP_400_BAD_REQUEST)

        rating = int(data.get('rating', 5))
        content_rating = int(data.get('content_rating', rating))
        mentor_rating = int(data.get('mentor_rating', rating))
        org_rating = int(data.get('organization_rating', rating))

        fb = EventFeedback.objects.create(
            event=event,
            registration=reg,
            user=user,
            full_name=user.get_full_name() or reg.full_name or user.username,
            email=email,
            rating=max(1, min(5, rating)),
            content_rating=max(1, min(5, content_rating)),
            mentor_rating=max(1, min(5, mentor_rating)),
            organization_rating=max(1, min(5, org_rating)),
            learnings=data.get('learnings', '').strip(),
            suggestions=data.get('suggestions', '').strip(),
            comments=data.get('comments', '').strip()
        )

        # Award points for providing feedback
        if hasattr(user, 'profile'):
            user.profile.verified_points += 25
            user.profile.save()

        AuditLog.log('EVENT_FEEDBACK_SUBMITTED', 'EventFeedback', fb.id, user=user, details={'event': event.title, 'rating': rating}, request=request)

        # Recalculate certificate eligibility and automatically issue certificate if conditions are satisfied!
        certificate_issued = False
        certificate_data = None
        if event.certificate_enabled:
            is_eligible, reasons = evaluate_certificate_eligibility(event, reg)
            if is_eligible:
                cert, is_new = issue_certificate_for_registration(event, reg, user=user)
                if cert:
                    certificate_issued = True
                    certificate_data = EventCertificateSerializer(cert).data

        return Response({
            'success': True,
            'message': 'Thank you! Your feedback has been recorded.',
            'feedback': EventFeedbackSerializer(fb).data,
            'certificate_issued': certificate_issued,
            'certificate': certificate_data
        }, status=status.HTTP_201_CREATED)


# ==============================================================================
# DIGITAL CERTIFICATES & VERIFICATION APIS
# ==============================================================================

class PublicCertificateVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, certificate_id):
        cert_query = str(certificate_id).strip()
        cert = EventCertificate.objects.filter(
            models.Q(certificate_id__iexact=cert_query) | models.Q(verification_token__iexact=cert_query)
        ).select_related('event').first()

        if not cert or cert.status != 'ISSUED':
            return Response({
                'is_valid': False,
                'message': 'No verified certificate found with this identifier, or certificate has been revoked.'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'is_valid': True,
            'certificate': PublicCertificateVerificationSerializer(cert).data
        })


class AdminEventCertificatesView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        certs = EventCertificate.objects.filter(event=event).select_related('registration', 'user', 'template_ref')

        # Compute eligible participants who have NOT yet received a certificate
        already_issued_reg_ids = certs.values_list('registration_id', flat=True)
        confirmed_regs = EventRegistration.objects.filter(
            event=event,
            registration_status='CONFIRMED'
        ).exclude(id__in=already_issued_reg_ids)

        eligible_list = []
        for r in confirmed_regs:
            is_eligible, reasons = evaluate_certificate_eligibility(event, r)
            eligible_list.append({
                'registration_id': r.id,
                'registration_reference': r.registration_reference,
                'full_name': r.full_name,
                'email': r.email,
                'phone': r.phone,
                'is_eligible': is_eligible,
                'reasons': reasons
            })

        cert_template_name = event.certificate_template_ref.name if getattr(event, 'certificate_template_ref', None) else (getattr(event, 'certificate_template', '') or 'Standard')
        return Response({
            'event_id': event.id,
            'event_title': event.title,
            'certificate_enabled': event.certificate_enabled,
            'certificate_template': cert_template_name,
            'issued_count': certs.count(),
            'issued_certificates': EventCertificateSerializer(certs, many=True).data,
            'pending_eligible': eligible_list
        })

    def post(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        reg_ids = request.data.get('registration_ids', [])
        issue_all_eligible = request.data.get('issue_all_eligible', False)

        if issue_all_eligible:
            already_issued = EventCertificate.objects.filter(event=event).values_list('registration_id', flat=True)
            candidate_regs = EventRegistration.objects.filter(
                event=event,
                registration_status='CONFIRMED'
            ).exclude(id__in=already_issued)
            # Filter strictly for participants meeting all eligibility rules
            reg_ids = [r.id for r in candidate_regs if evaluate_certificate_eligibility(event, r)[0]]

        issued_certs = []
        for rid in reg_ids:
            reg = EventRegistration.objects.filter(id=rid, event=event).first()
            if not reg:
                continue

            cert, is_new = issue_certificate_for_registration(event, reg, user=reg.user)
            if cert and is_new:
                issued_certs.append(cert)

        AuditLog.log('CERTIFICATES_ISSUED', 'EventCertificate', event.id, user=request.user, details={'count': len(issued_certs)}, request=request)
        return Response({
            'success': True,
            'issued_count': len(issued_certs),
            'certificates': EventCertificateSerializer(issued_certs, many=True).data
        }, status=status.HTTP_201_CREATED)


# ==============================================================================
# CERTIFICATE DESIGNER TEMPLATE CRUD & PREVIEW APIS
# ==============================================================================

class AdminCertificateTemplateCRUDView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request):
        qs = CertificateTemplate.objects.all()
        status_filter = request.query_params.get('status')
        if status_filter and status_filter.upper() != 'ALL':
            qs = qs.filter(status__iexact=status_filter)
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(models.Q(name__icontains=search) | models.Q(title__icontains=search))
        return Response(CertificateTemplateSerializer(qs, many=True).data)

    def post(self, request):
        data = request.data.copy()
        if not data.get('slug'):
            from django.utils.text import slugify
            base_slug = slugify(data.get('name', 'certificate-template'))
            slug = base_slug
            counter = 1
            while CertificateTemplate.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            data['slug'] = slug

        serializer = CertificateTemplateSerializer(data=data)
        if serializer.is_valid():
            template = serializer.save()
            AuditLog.log('CERTIFICATE_TEMPLATE_CREATED', 'CertificateTemplate', template.id, user=request.user, details={'name': template.name}, request=request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminCertificateTemplateDetailView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, pk):
        template = CertificateTemplate.objects.filter(pk=pk).first()
        if not template:
            return Response({'error': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CertificateTemplateSerializer(template).data)

    def put(self, request, pk):
        template = CertificateTemplate.objects.filter(pk=pk).first()
        if not template:
            return Response({'error': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CertificateTemplateSerializer(template, data=request.data, partial=True)
        if serializer.is_valid():
            tpl = serializer.save()
            AuditLog.log('CERTIFICATE_TEMPLATE_UPDATED', 'CertificateTemplate', tpl.id, user=request.user, details={'name': tpl.name}, request=request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        template = CertificateTemplate.objects.filter(pk=pk).first()
        if not template:
            return Response({'error': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)
        if template.is_default:
            return Response({'error': 'Default system template cannot be deleted.'}, status=status.HTTP_400_BAD_REQUEST)

        # Archive if historical records exist
        if template.assigned_events.exists() or template.issued_certificates.exists():
            template.status = CertificateTemplate.TemplateStatus.ARCHIVED
            template.save(update_fields=['status'])
            AuditLog.log('CERTIFICATE_TEMPLATE_ARCHIVED', 'CertificateTemplate', template.id, user=request.user, details={'name': template.name}, request=request)
            return Response({'success': True, 'message': 'Template archived successfully (preserved for historical certificates).'})

        template.delete()
        AuditLog.log('CERTIFICATE_TEMPLATE_DELETED', 'CertificateTemplate', pk, user=request.user, request=request)
        return Response({'success': True, 'message': 'Template deleted.'})


class AdminCertificateTemplateDuplicateView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def post(self, request, pk):
        template = CertificateTemplate.objects.filter(pk=pk).first()
        if not template:
            return Response({'error': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)

        from django.utils.text import slugify
        new_name = f"{template.name} (Copy)"
        base_slug = slugify(new_name)
        slug = base_slug
        counter = 1
        while CertificateTemplate.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        clone = CertificateTemplate.objects.create(
            name=new_name,
            slug=slug,
            status=CertificateTemplate.TemplateStatus.DRAFT,
            orientation=template.orientation,
            width=template.width,
            height=template.height,
            background_type=template.background_type,
            background_color=template.background_color,
            background_gradient=template.background_gradient,
            background_image=template.background_image,
            background_image_url=template.background_image_url,
            border_style=template.border_style,
            border_color=template.border_color,
            border_width=template.border_width,
            title=template.title,
            subtitle=template.subtitle,
            description_template=template.description_template,
            logo_image=template.logo_image,
            logo_url=template.logo_url,
            signatory_name=template.signatory_name,
            signatory_title=template.signatory_title,
            signature_image=template.signature_image,
            signature_url=template.signature_url,
            organizer_name=template.organizer_name,
            show_qr_code=template.show_qr_code,
            typography=template.typography,
            layout_elements=template.layout_elements,
            is_default=False
        )

        AuditLog.log('CERTIFICATE_TEMPLATE_DUPLICATED', 'CertificateTemplate', clone.id, user=request.user, details={'original_id': template.id, 'clone_name': clone.name}, request=request)
        return Response(CertificateTemplateSerializer(clone).data, status=status.HTTP_201_CREATED)


class AdminCertificateTemplatePreviewView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, pk):
        template = CertificateTemplate.objects.filter(pk=pk).first()
        if not template:
            return Response({'error': 'Template not found.'}, status=status.HTTP_404_NOT_FOUND)

        sample_user = request.user.get_full_name() or "Alex Mercer"
        sample_event = "Advanced AI & Cloud Architecture Workshop"
        sample_date = timezone.now().strftime('%B %d, %Y')
        sample_id = "XEYR-CERT-PREVIEW"
        sample_verify_url = f"{get_public_base_url()}/verify-certificate/{sample_id}/"

        html = render_certificate_document(
            template_data=template,
            event_name=sample_event,
            participant_name=sample_user,
            issue_date=sample_date,
            certificate_id=sample_id,
            organizer_name=template.organizer_name,
            verification_url=sample_verify_url,
            is_preview=True
        )
        return HttpResponse(html, content_type='text/html; charset=utf-8')


class CertificateRenderView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, certificate_id):
        cert = EventCertificate.objects.filter(certificate_id__iexact=certificate_id).select_related('event', 'template_ref').first()
        if not cert or cert.status != 'ISSUED':
            return HttpResponse("<h1>Certificate Not Found</h1><p>No active certificate matching this ID.</p>", status=404)

        tpl_data = cert.template_snapshot or (cert.template_ref.to_snapshot() if cert.template_ref else {})
        verify_url = f"{get_public_base_url()}/verify-certificate/{cert.certificate_id}/"

        html = render_certificate_document(
            template_data=tpl_data,
            event_name=cert.event.title,
            participant_name=cert.recipient_name,
            issue_date=cert.issue_date.strftime('%B %d, %Y'),
            certificate_id=cert.certificate_id,
            organizer_name=cert.organizer_name,
            verification_url=verify_url,
            signatory_name=tpl_data.get('signatory_name') or "Authorized Signatory",
            signatory_title=cert.signatory_title
        )
        return HttpResponse(html, content_type='text/html; charset=utf-8')


class CertificateDownloadView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, certificate_id):
        cert = EventCertificate.objects.filter(certificate_id__iexact=certificate_id).select_related('event', 'template_ref').first()
        if not cert or cert.status != 'ISSUED':
            return HttpResponse("<h1>Certificate Not Found</h1>", status=404)

        # Security check: User must be recipient, staff, or provide valid verification_token
        token = request.query_params.get('token')
        is_authorized = False
        if token and token == cert.verification_token:
            is_authorized = True
        elif request.user.is_authenticated:
            if request.user.is_staff or cert.user == request.user or cert.recipient_email.lower() == request.user.email.strip().lower():
                is_authorized = True

        if not is_authorized:
            return HttpResponse("<h1>403 Forbidden</h1><p>You are not authorized to download this participant's certificate.</p>", status=403)

        tpl_data = cert.template_snapshot or (cert.template_ref.to_snapshot() if cert.template_ref else {})
        verify_url = f"{get_public_base_url()}/verify-certificate/{cert.certificate_id}/"

        html = render_certificate_document(
            template_data=tpl_data,
            event_name=cert.event.title,
            participant_name=cert.recipient_name,
            issue_date=cert.issue_date.strftime('%B %d, %Y'),
            certificate_id=cert.certificate_id,
            organizer_name=cert.organizer_name,
            verification_url=verify_url,
            signatory_name=tpl_data.get('signatory_name') or "Authorized Signatory",
            signatory_title=cert.signatory_title
        )
        resp = HttpResponse(html, content_type='text/html; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="XEYR_Certificate_{cert.certificate_id}.html"'
        return resp


class AdminCertificateReissueView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def post(self, request, certificate_id):
        cert = EventCertificate.objects.filter(certificate_id__iexact=certificate_id).select_related('event', 'registration').first()
        if not cert:
            return Response({'error': 'Certificate not found.'}, status=status.HTTP_404_NOT_FOUND)

        recipient_name = request.data.get('recipient_name', cert.recipient_name)
        reissue_reason = request.data.get('reissue_reason', 'Authorized administrator correction')

        cert.recipient_name = recipient_name
        cert.reissued_at = timezone.now()
        cert.reissue_reason = reissue_reason
        cert.reissued_by = request.user

        # Re-apply updated template snapshot
        template = cert.event.certificate_template_ref or cert.template_ref
        if template:
            cert.template_snapshot = template.to_snapshot()
        cert.save()

        AuditLog.log('CERTIFICATE_REISSUED', 'EventCertificate', cert.id, user=request.user, details={'certificate_id': cert.certificate_id, 'reason': reissue_reason, 'recipient': recipient_name}, request=request)
        return Response({
            'success': True,
            'message': f'Certificate {cert.certificate_id} successfully reissued.',
            'certificate': EventCertificateSerializer(cert).data
        })


class AdminCertificateEmailRetryView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def post(self, request, certificate_id):
        cert = EventCertificate.objects.filter(certificate_id__iexact=certificate_id).select_related('event').first()
        if not cert:
            return Response({'error': 'Certificate not found.'}, status=status.HTTP_404_NOT_FOUND)

        sent = try_send_certificate_email(cert)
        return Response({
            'success': sent,
            'certificate_id': cert.certificate_id,
            'email_delivery_status': cert.email_delivery_status,
            'email_error': cert.email_error,
            'message': 'Email successfully delivered.' if sent else f"Delivery state: {cert.email_delivery_status}"
        })


class MainPortalQRView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        portal_url = get_events_portal_url()
        if request.query_params.get('format') == 'json':
            data_uri = generate_qr_code_data_uri(portal_url)
            return Response({
                'portal_url': portal_url,
                'qr_code_data_uri': data_uri,
                'is_canonical': True
            })

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2
        )
        qr.add_data(portal_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#07132e", back_color="#ffffff")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return HttpResponse(buf.getvalue(), content_type='image/png')


class MainPortalSharingInfoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        portal_url = get_events_portal_url()
        data_uri = generate_qr_code_data_uri(portal_url)
        title = "Explore Workshops & Technology Events — XEYR Technologies"
        text = f"Discover upcoming hands-on tech workshops, expert sessions and community events at XEYR Technologies: {portal_url}"
        import urllib.parse
        encoded_url = urllib.parse.quote(portal_url)
        encoded_text = urllib.parse.quote(text)

        return Response({
            'portal_url': portal_url,
            'title': title,
            'share_text': text,
            'qr_code_data_uri': data_uri,
            'share_links': {
                'whatsapp': f"https://api.whatsapp.com/send?text={encoded_text}%20{encoded_url}",
                'linkedin': "https://www.linkedin.com/sharing/share-offsite/?url=" + encoded_url,
                'twitter_x': f"https://twitter.com/intent/tweet?url={encoded_url}&text={encoded_text}",
                'telegram': f"https://t.me/share/url?url={encoded_url}&text={encoded_text}",
            }
        })


# ==============================================================================
# ATTENDANCE MANAGEMENT APIS
# ==============================================================================

class AdminEventAttendanceView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        regs = EventRegistration.objects.filter(event=event, registration_status='CONFIRMED')
        attendance_map = {
            att.registration_id: att for att in EventAttendance.objects.filter(event=event)
        }

        records = []
        for r in regs:
            att = attendance_map.get(r.id)
            records.append({
                'registration_id': r.id,
                'registration_reference': r.registration_reference,
                'full_name': r.full_name,
                'email': r.email,
                'phone': r.phone,
                'attended': att.attended if att else False,
                'attendance_percentage': att.attendance_percentage if att else 0,
                'marked_at': att.marked_at if att else None
            })

        return Response({
            'event_id': event.id,
            'event_title': event.title,
            'min_attendance_threshold': event.certificate_min_attendance,
            'total_confirmed': regs.count(),
            'attendance_records': records
        })

    def post(self, request, event_id):
        event = EventListing.objects.filter(id=event_id).first()
        if not event:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        entries = request.data.get('records', [])
        updated_count = 0
        for entry in entries:
            reg_id = entry.get('registration_id')
            reg = EventRegistration.objects.filter(id=reg_id, event=event).first()
            if not reg:
                continue

            attended = bool(entry.get('attended', True))
            percentage = int(entry.get('attendance_percentage', 100))

            att, _ = EventAttendance.objects.update_or_create(
                event=event,
                registration=reg,
                defaults={
                    'user': reg.user,
                    'attended': attended,
                    'attendance_percentage': max(0, min(100, percentage)),
                    'marked_at': timezone.now(),
                    'marked_by': request.user
                }
            )
            updated_count += 1

        AuditLog.log('ATTENDANCE_RECORDED', 'EventAttendance', event.id, user=request.user, details={'updated': updated_count}, request=request)
        return Response({'success': True, 'updated_count': updated_count})


# ==============================================================================
# FEEDBACK LIST APIS
# ==============================================================================

class AdminFeedbackListView(APIView):
    permission_classes = [IsStaffOrAdminPermission]

    def get(self, request, event_id=None):
        qs = EventFeedback.objects.all().select_related('event', 'registration')
        if event_id:
            qs = qs.filter(event_id=event_id)

        avg_rating = qs.aggregate(models.Avg('rating'))['rating__avg'] or 5.0
        return Response({
            'count': qs.count(),
            'average_rating': round(float(avg_rating), 1),
            'feedback': EventFeedbackSerializer(qs[:100], many=True).data
        })


# ==============================================================================
# EVENT GALLERY APIS
# ==============================================================================

class PublicEventGalleryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        qs = EventGalleryItem.objects.filter(is_public=True).select_related('event')
        event_slug = request.query_params.get('event')
        if event_slug:
            qs = qs.filter(event__slug=event_slug)
        category = request.query_params.get('category')
        if category and category.upper() != 'ALL':
            qs = qs.filter(category__iexact=category)

        return Response(EventGalleryItemSerializer(qs[:100], many=True).data)


class AdminEventGalleryManageView(APIView):
    permission_classes = [IsStaffOrAdminPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        qs = EventGalleryItem.objects.all().select_related('event')
        return Response(EventGalleryItemSerializer(qs, many=True).data)

    def post(self, request):
        serializer = EventGalleryItemSerializer(data=request.data)
        if serializer.is_valid():
            item = serializer.save()
            AuditLog.log('GALLERY_ITEM_CREATED', 'EventGalleryItem', item.id, user=request.user, details={'title': item.title}, request=request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminEventGalleryDetailView(APIView):
    permission_classes = [IsStaffOrAdminPermission]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def put(self, request, pk):
        item = EventGalleryItem.objects.filter(pk=pk).first()
        if not item:
            return Response({'error': 'Gallery item not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = EventGalleryItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        item = EventGalleryItem.objects.filter(pk=pk).first()
        if not item:
            return Response({'error': 'Gallery item not found.'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        AuditLog.log('GALLERY_ITEM_DELETED', 'EventGalleryItem', pk, user=request.user, request=request)
        return Response({'success': True, 'message': 'Gallery item deleted.'})


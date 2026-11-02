import uuid
import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from crm.models import Enquiry


def generate_registration_ref():
    year = timezone.now().year
    rand_seq = random.randint(1000, 9999)
    return f"XEYR-REG-{year}-{rand_seq}"



class CertificateTemplate(models.Model):
    class TemplateStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'

    class Orientation(models.TextChoices):
        LANDSCAPE = 'LANDSCAPE', 'Landscape (A4)'
        PORTRAIT = 'PORTRAIT', 'Portrait (A4)'

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=TemplateStatus.choices, default=TemplateStatus.PUBLISHED, db_index=True)
    orientation = models.CharField(max_length=20, choices=Orientation.choices, default=Orientation.LANDSCAPE)
    width = models.PositiveIntegerField(default=1120)  # px preview width (A4 ratio)
    height = models.PositiveIntegerField(default=792)  # px preview height

    # Background & Themes
    background_type = models.CharField(max_length=20, default='COLOR')  # 'COLOR', 'IMAGE', 'GRADIENT'
    background_color = models.CharField(max_length=50, default='#ffffff')
    background_gradient = models.CharField(max_length=255, blank=True, default='linear-gradient(135deg, #ffffff 0%, #f0f7ff 100%)')
    background_image = models.ImageField(upload_to='certificate_bg/', blank=True, null=True)
    background_image_url = models.CharField(max_length=500, blank=True, default='')

    # Borders & Decorative Elements
    border_style = models.CharField(max_length=50, default='classic_gold')  # 'classic_gold', 'modern_blue', 'double_line', 'ornamental', 'minimal_clean', 'none'
    border_color = models.CharField(max_length=50, default='#1465f4')
    border_width = models.PositiveIntegerField(default=8)

    # Content Titles & Defaults
    title = models.CharField(max_length=200, default='CERTIFICATE OF ACHIEVEMENT')
    subtitle = models.CharField(max_length=200, default='PROUDLY PRESENTED TO')
    description_template = models.TextField(
        default='For successfully participating in and completing {{event_name}} organized by {{organizer_name}} on {{issue_date}}.'
    )

    # Branding & Signatory
    logo_image = models.ImageField(upload_to='certificate_logos/', blank=True, null=True)
    logo_url = models.CharField(max_length=500, blank=True, default='/assets/xeyr-symbol.png')
    signatory_name = models.CharField(max_length=150, default='Authorized Director')
    signatory_title = models.CharField(max_length=150, default='Director, XEYR Technologies')
    signature_image = models.ImageField(upload_to='certificate_signatures/', blank=True, null=True)
    signature_url = models.CharField(max_length=500, blank=True, default='')
    organizer_name = models.CharField(max_length=150, default='XEYR Technologies Private Limited')

    # Security & Verification
    show_qr_code = models.BooleanField(default=True)

    # Visual Layout & Typography (JSON)
    typography = models.JSONField(default=dict, blank=True)
    layout_elements = models.JSONField(default=list, blank=True)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} [{self.get_orientation_display()}] ({self.status})"

    def to_snapshot(self):
        """Generates a complete immutable snapshot for issued certificates."""
        return {
            'template_id': self.id,
            'name': self.name,
            'orientation': self.orientation,
            'width': self.width,
            'height': self.height,
            'background_type': self.background_type,
            'background_color': self.background_color,
            'background_gradient': self.background_gradient,
            'background_image_url': self.background_image.url if self.background_image else self.background_image_url,
            'border_style': self.border_style,
            'border_color': self.border_color,
            'border_width': self.border_width,
            'title': self.title,
            'subtitle': self.subtitle,
            'description_template': self.description_template,
            'logo_url': self.logo_image.url if self.logo_image else self.logo_url,
            'signatory_name': self.signatory_name,
            'signatory_title': self.signatory_title,
            'signature_url': self.signature_image.url if self.signature_image else self.signature_url,
            'organizer_name': self.organizer_name,
            'show_qr_code': self.show_qr_code,
            'typography': self.typography,
            'layout_elements': self.layout_elements,
        }


class EventListing(models.Model):
    class EventStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published'
        UPCOMING = 'UPCOMING', 'Upcoming'
        ONGOING = 'ONGOING', 'Ongoing'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        ARCHIVED = 'ARCHIVED', 'Archived'

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, db_index=True)
    event_type = models.CharField(max_length=50, default='Workshop')  # 'WORKSHOP', 'EXPERT_SESSION', 'COMMUNITY'
    poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)
    poster_url = models.CharField(max_length=500, blank=True, default='')  # Direct image URL or uploaded file

    short_description = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')
    full_description = models.TextField(blank=True, default='')

    event_date = models.DateField(null=True, blank=True, db_index=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    date_time = models.CharField(max_length=150, default='Upcoming Session')

    mode = models.CharField(max_length=50, default='Online / Offline')  # 'Online', 'Offline', 'Hybrid'
    venue = models.CharField(max_length=200, blank=True, default='TBA')
    organizer = models.CharField(max_length=150, default='XEYR Technologies')
    eligibility = models.CharField(max_length=200, blank=True, default='Open to all students and professionals')

    registration_deadline = models.DateTimeField(null=True, blank=True)
    max_participants = models.PositiveIntegerField(null=True, blank=True)  # Seat limit

    # Pricing & Razorpay
    is_paid = models.BooleanField(default=False)
    fee = models.CharField(max_length=50, default='Free')
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=10, default='INR')
    refund_policy = models.TextField(
        blank=True,
        default='Refundable if cancelled at least 24 hours prior to event start.'
    )

    status = models.CharField(
        max_length=30,
        choices=EventStatus.choices,
        default=EventStatus.UPCOMING,
        db_index=True
    )
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)

    # Archive details
    highlights = models.TextField(blank=True, default='')
    results_summary = models.TextField(blank=True, default='')
    gallery_urls = models.JSONField(default=list, blank=True)

    terms_and_conditions = models.TextField(blank=True, default='')
    contact_email = models.CharField(max_length=100, blank=True, default='xeyrtechnologies@gmail.com')
    contact_phone = models.CharField(max_length=30, blank=True, default='+91 80562 53897')

    # Rich Content & Media
    mentors = models.JSONField(default=list, blank=True)
    schedule = models.JSONField(default=list, blank=True)
    learning_outcomes = models.JSONField(default=list, blank=True)
    prerequisites = models.TextField(blank=True, default='')
    target_audience = models.TextField(blank=True, default='')
    guidelines = models.TextField(blank=True, default='')
    faqs = models.JSONField(default=list, blank=True)
    appearance = models.JSONField(default=dict, blank=True)
    joining_instructions = models.TextField(blank=True, default='')
    attendance_requirements = models.TextField(blank=True, default='')

    # Certificates configuration & visual template designer assignment
    certificate_enabled = models.BooleanField(default=False)
    certificate_template = models.CharField(max_length=100, default='standard_completion', blank=True)
    certificate_template_ref = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_events'
    )
    certificate_custom_settings = models.JSONField(default=dict, blank=True)  # Event-specific overrides
    certificate_require_attendance = models.BooleanField(default=True)
    certificate_min_attendance = models.PositiveIntegerField(default=80)
    certificate_require_feedback = models.BooleanField(default=False)
    certificate_require_activities = models.BooleanField(default=False)
    certificate_activities_description = models.CharField(max_length=255, blank=True, default='')
    certificate_other_conditions = models.CharField(max_length=255, blank=True, default='')
    certificate_release_date = models.DateTimeField(null=True, blank=True)

    # Post-Event Feedback Configuration
    feedback_enabled = models.BooleanField(default=True)
    feedback_questions = models.JSONField(default=list, blank=True)

    # Portal layout
    is_featured = models.BooleanField(default=False, db_index=True)
    public_visibility = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event_date', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def can_safely_delete(self):
        return not (
            self.registrations.exists() or
            self.payment_orders.exists() or
            self.certificates.exists() or
            self.feedback_entries.exists()
        )

    @property
    def is_completed(self):
        if self.status == self.EventStatus.COMPLETED:
            return True
        if self.event_date and self.event_date < timezone.now().date():
            return True
        return False

    @property
    def confirmed_count(self):
        return self.registrations.filter(registration_status='CONFIRMED').count()

    @property
    def is_registration_open(self):
        if not self.is_published or self.status in [self.EventStatus.COMPLETED, self.EventStatus.CANCELLED, self.EventStatus.ARCHIVED]:
            return False
        if self.registration_deadline and timezone.now() > self.registration_deadline:
            return False
        if self.max_participants and self.confirmed_count >= self.max_participants:
            return False
        return True


class EventFormField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = 'text', 'Single Line Text'
        TEXTAREA = 'textarea', 'Multi-Line Text Area'
        EMAIL = 'email', 'Email Address'
        PHONE = 'phone', 'Phone Number'
        DROPDOWN = 'dropdown', 'Dropdown Select'
        RADIO = 'radio', 'Radio Options'
        CHECKBOX = 'checkbox', 'Checkboxes'
        DATE = 'date', 'Date'
        COLLEGE = 'college', 'College / Organisation'
        DEPARTMENT = 'department', 'Department / Branch'
        YEAR = 'year', 'Year of Study'
        TEAM_NAME = 'team_name', 'Team Name'
        TEAM_SIZE = 'team_size', 'Team Size'
        CONSENT = 'consent', 'Consent Checkbox'

    event = models.ForeignKey(EventListing, on_delete=models.CASCADE, related_name='form_fields')
    field_label = models.CharField(max_length=150)
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=30, choices=FieldType.choices, default=FieldType.TEXT)
    is_required = models.BooleanField(default=True)
    placeholder = models.CharField(max_length=150, blank=True, default='')
    help_text = models.CharField(max_length=255, blank=True, default='')
    options = models.TextField(blank=True, default='')  # Comma or newline separated for select/radio
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.event.title} -> {self.field_label} ({self.field_type})"


class EventRegistration(models.Model):
    class RegistrationStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        WAITLISTED = 'WAITLISTED', 'Waitlisted'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    class PaymentStatus(models.TextChoices):
        NOT_REQUIRED = 'NOT_REQUIRED', 'Not Required (Free Event)'
        PENDING = 'PENDING', 'Pending'
        ORDER_CREATED = 'ORDER_CREATED', 'Order Created'
        PAID = 'PAID', 'Paid & Verified'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUND_PENDING = 'REFUND_PENDING', 'Refund Pending'
        REFUNDED = 'REFUNDED', 'Refunded'

    event = models.ForeignKey(
        EventListing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registrations'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_registrations'
    )
    registration_reference = models.CharField(
        max_length=40,
        blank=True,
        default='',
        db_index=True
    )
    event_name = models.CharField(max_length=200)
    full_name = models.CharField(max_length=150)
    company_or_college = models.CharField(max_length=200, blank=True, default='')
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30)

    # Dynamic responses from event-configured form
    form_responses = models.JSONField(default=dict, blank=True)

    registration_status = models.CharField(
        max_length=30,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.CONFIRMED,
        db_index=True
    )
    payment_status = models.CharField(
        max_length=30,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_REQUIRED,
        db_index=True
    )
    fee_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=30, default='Confirmed')  # Backward compatibility
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.registration_reference:
            self.registration_reference = generate_registration_ref()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration_reference}: {self.full_name} -> {self.event_name} [{self.registration_status}]"


class EventNotificationSubscriber(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, db_index=True)
    categories_of_interest = models.CharField(max_length=255, blank=True, default='ALL')
    is_active = models.BooleanField(default=True)
    consent_given = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(max_length=64, blank=True, default='', db_index=True)
    subscribed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-subscribed_at']

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            self.unsubscribe_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class EventNotificationDelivery(models.Model):
    class DeliveryStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    event = models.ForeignKey(EventListing, on_delete=models.CASCADE, related_name='notifications_sent')
    subscriber = models.ForeignKey(EventNotificationSubscriber, on_delete=models.CASCADE, related_name='received_notifications')
    status = models.CharField(max_length=20, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('event', 'subscriber')
        ordering = ['-created_at']

    def __str__(self):
        return f"Notice: {self.event.title} -> {self.subscriber.email} [{self.status}]"


class EventPaymentOrder(models.Model):
    class PaymentOrderStatus(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='payment_orders'
    )
    event = models.ForeignKey(
        EventListing,
        on_delete=models.CASCADE,
        related_name='payment_orders'
    )
    razorpay_order_id = models.CharField(max_length=100, unique=True, db_index=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(
        max_length=30,
        choices=PaymentOrderStatus.choices,
        default=PaymentOrderStatus.CREATED,
        db_index=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Razorpay Order {self.razorpay_order_id} (₹{self.amount}) [{self.status}]"


class EventRefundRecord(models.Model):
    payment_order = models.ForeignKey(EventPaymentOrder, on_delete=models.CASCADE, related_name='refunds')
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, related_name='refunds')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_reason = models.TextField()
    razorpay_refund_id = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, default='PENDING')  # PENDING, PROCESSED, FAILED
    created_at = models.DateTimeField(default=timezone.now)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund ₹{self.refund_amount} for {self.registration.registration_reference}"


class SocialMediaConfig(models.Model):
    class Platform(models.TextChoices):
        INSTAGRAM = 'INSTAGRAM', 'Instagram'
        LINKEDIN = 'LINKEDIN', 'LinkedIn'
        TWITTER_X = 'TWITTER_X', 'Twitter / X'
        YOUTUBE = 'YOUTUBE', 'YouTube'
        GITHUB = 'GITHUB', 'GitHub'
        OTHER = 'OTHER', 'Other Platform'

    platform_key = models.CharField(max_length=30, unique=True, choices=Platform.choices)
    platform_name = models.CharField(max_length=60)
    platform_url = models.URLField(blank=True, default='')
    qr_code_image = models.ImageField(upload_to='social_qr/', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'platform_name']

    def __str__(self):
        return f"{self.platform_name}: {self.platform_url or 'No URL'}"


# Existing models for SkillBridge
class SkillBridgeCollegeEnquiry(models.Model):
    enquiry = models.OneToOneField(
        Enquiry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='college_details'
    )
    contact_name = models.CharField(max_length=150)
    college_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    preferred_service = models.CharField(max_length=150, default='College Training Workshop')
    status = models.CharField(max_length=30, default='Received')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.college_name} - {self.contact_name}"


class SkillBridgeProfessionalApplication(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    skills_can_teach = models.TextField()
    profile_type = models.CharField(max_length=100)
    resume_file = models.FileField(upload_to='resumes/', blank=True, null=True)
    status = models.CharField(max_length=30, default='Received')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.profile_type})"


# ==============================================================================
# EVENT FEEDBACK & RATINGS
# ==============================================================================
class EventFeedback(models.Model):
    event = models.ForeignKey(
        EventListing,
        on_delete=models.CASCADE,
        related_name='feedback_entries'
    )
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='feedback_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='event_feedbacks'
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField(db_index=True)
    rating = models.PositiveSmallIntegerField(default=5)  # Overall 1-5
    content_rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    mentor_rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    organization_rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    learnings = models.TextField(blank=True, default='')
    suggestions = models.TextField(blank=True, default='')
    comments = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Feedback for {self.event.title} by {self.full_name} ({self.rating}/5)"


# ==============================================================================
# DIGITAL CERTIFICATES & VERIFICATION
# ==============================================================================
def generate_certificate_id():
    year = timezone.now().year
    rand_seq = random.randint(10000, 99999)
    return f"XEYR-CERT-{year}-{rand_seq}"


class EventCertificate(models.Model):
    class CertificateStatus(models.TextChoices):
        ISSUED = 'ISSUED', 'Issued'
        REVOKED = 'REVOKED', 'Revoked'

    certificate_id = models.CharField(
        max_length=60,
        unique=True,
        default=generate_certificate_id,
        db_index=True
    )
    event = models.ForeignKey(
        EventListing,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates'
    )
    recipient_name = models.CharField(max_length=150)
    recipient_email = models.EmailField(db_index=True)
    status = models.CharField(
        max_length=20,
        choices=CertificateStatus.choices,
        default=CertificateStatus.ISSUED,
        db_index=True
    )
    issue_date = models.DateField(default=timezone.now)
    template_type = models.CharField(max_length=50, default='standard')
    template_ref = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates'
    )
    template_snapshot = models.JSONField(default=dict, blank=True)  # Immutable snapshot of the design at issuance time

    organizer_name = models.CharField(max_length=150, default='XEYR Technologies')
    signatory_title = models.CharField(max_length=150, default='Director, XEYR Technologies')
    verification_token = models.CharField(max_length=64, unique=True, db_index=True)

    # Reissue & Revocation Tracking (Audit History)
    reissued_at = models.DateTimeField(null=True, blank=True)
    reissue_reason = models.TextField(blank=True, default='')
    reissued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reissued_certificates'
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.TextField(blank=True, default='')

    # Email Delivery State & Safe Retries
    email_delivery_status = models.CharField(max_length=20, default='NOT_SENT')  # 'NOT_SENT', 'SENT', 'FAILED'
    email_sent_at = models.DateTimeField(null=True, blank=True)
    email_error = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = generate_certificate_id()
        if not self.verification_token:
            self.verification_token = str(uuid.uuid4()).replace('-', '')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.recipient_name} ({self.event.title})"


# ==============================================================================
# EVENT ATTENDANCE TRACKING
# ==============================================================================
class EventAttendance(models.Model):
    event = models.ForeignKey(
        EventListing,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    registration = models.ForeignKey(
        EventRegistration,
        on_delete=models.CASCADE,
        related_name='attendance'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records'
    )
    attended = models.BooleanField(default=True)
    attendance_percentage = models.PositiveIntegerField(default=100)
    marked_at = models.DateTimeField(default=timezone.now)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_attendances'
    )

    class Meta:
        unique_together = ('event', 'registration')
        ordering = ['-marked_at']

    def __str__(self):
        return f"Attendance: {self.registration.full_name} for {self.event.title} ({self.attendance_percentage}%)"


# ==============================================================================
# EVENT GALLERY MEDIA
# ==============================================================================
class EventGalleryItem(models.Model):
    event = models.ForeignKey(
        EventListing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='gallery_media'
    )
    title = models.CharField(max_length=200)
    image_url = models.CharField(max_length=500, blank=True, default='')
    image = models.ImageField(upload_to='event_gallery/', blank=True, null=True)
    caption = models.TextField(blank=True, default='')
    alt_text = models.CharField(max_length=255, blank=True, default='')
    category = models.CharField(max_length=50, default='HIGHLIGHTS')
    display_order = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"Gallery: {self.title} ({self.category})"

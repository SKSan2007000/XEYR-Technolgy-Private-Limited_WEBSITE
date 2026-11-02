import random
from django.db import models
from django.utils import timezone
from django.conf import settings


class EnquiryStatus(models.TextChoices):
    NEW = 'NEW', 'New'
    UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
    CONTACTED = 'CONTACTED', 'Contacted'
    FOLLOWUP_REQUIRED = 'FOLLOWUP_REQUIRED', 'Follow-up Required'
    QUALIFIED = 'QUALIFIED', 'Qualified'
    REQUIREMENTS_PENDING = 'REQUIREMENTS_PENDING', 'Requirements Pending'
    REQUIREMENTS_COMPLETED = 'REQUIREMENTS_COMPLETED', 'Requirements Completed'
    AWAITING_CLIENT_APPROVAL = 'AWAITING_CLIENT_APPROVAL', 'Awaiting Client Approval'
    READY_FOR_HANDOVER = 'READY_FOR_HANDOVER', 'Ready for Handover'
    PROJECT_CREATED = 'PROJECT_CREATED', 'Project Created'
    REJECTED = 'REJECTED', 'Rejected'
    CLOSED = 'CLOSED', 'Closed'


class RejectionCategory(models.TextChoices):
    BUDGET_MISMATCH = 'BUDGET_MISMATCH', 'Budget Mismatch'
    SERVICE_NOT_OFFERED = 'SERVICE_NOT_OFFERED', 'Service Not Offered'
    TECHNICAL_INFEASIBILITY = 'TECHNICAL_INFEASIBILITY', 'Technical Infeasibility'
    TIMELINE_NOT_FEASIBLE = 'TIMELINE_NOT_FEASIBLE', 'Timeline Not Feasible'
    INCOMPLETE_INFO = 'INCOMPLETE_INFO', 'Incomplete Information'
    DUPLICATE = 'DUPLICATE', 'Duplicate Enquiry'
    CLIENT_UNRESPONSIVE = 'CLIENT_UNRESPONSIVE', 'Client Unresponsive'
    OUTSIDE_SCOPE = 'OUTSIDE_SCOPE', 'Outside Business Scope'
    RESOURCE_UNAVAILABLE = 'RESOURCE_UNAVAILABLE', 'Resource Unavailability'
    COMMERCIAL_TERMS_REJECTED = 'COMMERCIAL_TERMS_REJECTED', 'Commercial Terms Not Accepted'
    OTHER = 'OTHER', 'Other'


def generate_enquiry_ref():
    year = timezone.now().year
    rand_seq = random.randint(1000, 9999)
    return f"XEYR-ENQ-{year}-{rand_seq}"


class Enquiry(models.Model):
    reference_id = models.CharField(
        max_length=30,
        unique=True,
        default=generate_enquiry_ref,
        db_index=True
    )
    client_name = models.CharField(max_length=200, help_text="Client or Organisation Name")
    contact_person = models.CharField(max_length=150, blank=True, default='')
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=30)
    organisation_type = models.CharField(max_length=100, blank=True, default='Business / Corporate')
    service_type = models.CharField(max_length=150, default='SolveX - Business Solution')
    project_title = models.CharField(max_length=255, blank=True, default='New Project Enquiry')
    project_description = models.TextField(blank=True, default='')
    budget_range = models.CharField(max_length=100, blank=True, default='To be discussed')
    expected_timeline = models.CharField(max_length=100, blank=True, default='Flexible')
    preferred_contact_method = models.CharField(max_length=50, blank=True, default='Email')
    source = models.CharField(max_length=100, default='Website', db_index=True)

    status = models.CharField(
        max_length=35,
        choices=EnquiryStatus.choices,
        default=EnquiryStatus.NEW,
        db_index=True
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_enquiries'
    )
    internal_notes = models.TextField(blank=True, default='')
    follow_up_date = models.DateTimeField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['source', 'status']),
        ]

    def __str__(self):
        return f"{self.reference_id} - {self.client_name} ({self.get_status_display()})"


class EnquiryQualification(models.Model):
    enquiry = models.OneToOneField(
        Enquiry,
        on_delete=models.CASCADE,
        related_name='qualification'
    )
    decision = models.CharField(max_length=200, default='Qualified for Development')
    business_opportunity = models.TextField(blank=True, default='')
    client_needs = models.TextField(blank=True, default='')
    service_fit = models.TextField(blank=True, default='')
    estimated_project_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    budget_confirmed = models.BooleanField(default=False)
    timeline_confirmed = models.BooleanField(default=False)
    decision_maker_details = models.TextField(blank=True, default='')
    technical_feasibility = models.TextField(blank=True, default='')
    internal_assessment = models.TextField(blank=True, default='')
    account_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_qualifications'
    )
    next_action = models.TextField(blank=True, default='')
    follow_up_date = models.DateTimeField(null=True, blank=True)
    qualified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='qualifications_made'
    )
    qualified_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Qualification for {self.enquiry.reference_id}"


class EnquiryRejection(models.Model):
    enquiry = models.ForeignKey(
        Enquiry,
        on_delete=models.CASCADE,
        related_name='rejections'
    )
    category = models.CharField(
        max_length=40,
        choices=RejectionCategory.choices,
        db_index=True
    )
    reason_detail = models.TextField(
        help_text="Detailed explanation of the rejection (mandatory if category is Other)"
    )
    internal_notes = models.TextField(blank=True, default='')
    previous_status = models.CharField(max_length=35, default=EnquiryStatus.NEW)
    future_followup_appropriate = models.BooleanField(default=False)

    rejected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='enquiry_rejections'
    )
    rejected_at = models.DateTimeField(default=timezone.now, db_index=True)

    reopened = models.BooleanField(default=False)
    reopen_reason = models.TextField(blank=True, default='')
    reopened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reopened_enquiries'
    )
    reopened_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-rejected_at']

    def __str__(self):
        return f"Rejection #{self.id} for {self.enquiry.reference_id}: {self.get_category_display()}"


class CRMActivity(models.Model):
    class ActivityType(models.TextChoices):
        CALL = 'CALL', 'Phone Call'
        MEETING = 'MEETING', 'Client Meeting'
        NOTE = 'NOTE', 'Internal Note'
        EMAIL = 'EMAIL', 'Email Interaction'
        STATUS_CHANGE = 'STATUS_CHANGE', 'Status Update'
        FOLLOWUP = 'FOLLOWUP', 'Follow-up Task'

    enquiry = models.ForeignKey(
        Enquiry,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=25,
        choices=ActivityType.choices,
        default=ActivityType.NOTE
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='crm_activities'
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} - {self.title} ({self.enquiry.reference_id})"

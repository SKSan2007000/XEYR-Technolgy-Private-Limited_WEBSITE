import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from crm.models import Enquiry


class RequirementStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    IN_PROGRESS = 'IN_PROGRESS', 'Requirements Collection In Progress'
    INTERNAL_REVIEW = 'INTERNAL_REVIEW', 'Internal Review'
    AWAITING_CLIENT_REVIEW = 'AWAITING_CLIENT_REVIEW', 'Awaiting Client Review'
    CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
    APPROVED = 'APPROVED', 'Approved'
    READY_FOR_HANDOVER = 'READY_FOR_HANDOVER', 'Ready for Developer Handover'


def generate_req_ref():
    year = timezone.now().year
    rand_seq = random.randint(1000, 9999)
    return f"XEYR-REQ-{year}-{rand_seq}"


class ProjectRequirement(models.Model):
    enquiry = models.OneToOneField(
        Enquiry,
        on_delete=models.CASCADE,
        related_name='requirement_workspace'
    )
    requirement_reference = models.CharField(
        max_length=35,
        unique=True,
        default=generate_req_ref,
        db_index=True
    )
    status = models.CharField(
        max_length=35,
        choices=RequirementStatus.choices,
        default=RequirementStatus.DRAFT,
        db_index=True
    )

    # Section A: Client Information
    legal_business_name = models.CharField(max_length=200, blank=True, default='')
    client_contact_person = models.CharField(max_length=150, blank=True, default='')
    official_email = models.EmailField(blank=True, default='')
    official_phone = models.CharField(max_length=30, blank=True, default='')
    business_address = models.TextField(blank=True, default='')
    industry_category = models.CharField(max_length=100, blank=True, default='')
    website_and_socials = models.TextField(blank=True, default='')

    # Section B: Project Overview
    project_name = models.CharField(max_length=255)
    project_type = models.CharField(max_length=100, default='Web Application')
    business_problem = models.TextField(blank=True, default='')
    project_goals = models.TextField(blank=True, default='')
    target_audience = models.TextField(blank=True, default='')
    expected_deliverables = models.JSONField(default=list, blank=True)
    scope_of_work = models.TextField(blank=True, default='')
    features_required = models.JSONField(default=list, blank=True)
    functional_requirements = models.TextField(blank=True, default='')
    non_functional_requirements = models.TextField(blank=True, default='')
    technical_preferences = models.TextField(blank=True, default='')
    integrations_required = models.TextField(blank=True, default='')
    accessibility_responsive_reqs = models.TextField(blank=True, default='')
    hosting_deployment_reqs = models.TextField(blank=True, default='')
    maintenance_reqs = models.TextField(blank=True, default='')

    # Section C: Commercial Details
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    approved_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_milestones = models.JSONField(default=list, blank=True)
    expected_start_date = models.DateField(null=True, blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    contract_proposal_ref = models.CharField(max_length=100, blank=True, default='')
    commercial_approval_status = models.CharField(max_length=50, default='Pending')

    # Section D: Design Requirements
    design_style = models.CharField(max_length=100, blank=True, default='Modern Premium / Dark & Light Modes')
    color_preferences = models.CharField(max_length=200, blank=True, default='XEYR Navy (#07132e), Electric Blue (#1465f4), Cyan (#27d4f4)')
    typography_preferences = models.CharField(max_length=150, blank=True, default='DM Sans / Manrope')
    reference_websites = models.TextField(blank=True, default='')
    wireframe_notes = models.TextField(blank=True, default='')
    ui_ux_requirements = models.TextField(blank=True, default='')
    brand_guidelines_notes = models.TextField(blank=True, default='')
    required_page_list = models.JSONField(default=list, blank=True)
    device_requirements = models.CharField(max_length=150, blank=True, default='Desktop, Tablet, Mobile responsive')

    # Section E: Technical Requirements
    preferred_framework = models.CharField(max_length=100, blank=True, default='Python Django + DRF')
    backend_requirements = models.TextField(blank=True, default='')
    database_requirements = models.CharField(max_length=100, blank=True, default='PostgreSQL 17')
    api_integrations = models.TextField(blank=True, default='')
    auth_requirements = models.TextField(blank=True, default='Role-Based Authentication with Session & JWT')
    user_roles_req = models.TextField(blank=True, default='')
    security_requirements = models.TextField(blank=True, default='CSRF, Rate Limiting, Input Validation, Protected File Storage')
    deployment_platform = models.CharField(max_length=100, blank=True, default='Linux VPS / Cloud Platform')
    repository_details = models.CharField(max_length=255, blank=True, default='')
    testing_requirements = models.TextField(blank=True, default='Unit and Integration Tests for Critical Workflows')
    documentation_requirements = models.TextField(blank=True, default='README, Architecture Summary, API Docs, Setup Guide')

    # Section F: Project Management & Custom Fields
    project_owner = models.CharField(max_length=150, blank=True, default='')
    project_manager_assigned = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_requirements'
    )
    developer_assigned = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_requirements'
    )
    priority = models.CharField(max_length=20, default='Medium')
    milestones = models.JSONField(default=list, blank=True)
    tasks = models.JSONField(default=list, blank=True)
    dependencies = models.TextField(blank=True, default='')
    risks = models.JSONField(default=list, blank=True)
    client_approval_checkpoints = models.TextField(blank=True, default='')
    delivery_checklist = models.JSONField(default=list, blank=True)
    acceptance_criteria = models.TextField(blank=True, default='')
    custom_fields = models.JSONField(default=dict, blank=True)

    # Tracking & Audit
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_requirements'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_requirements'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.requirement_reference} - {self.project_name} ({self.get_status_display()})"


class RequirementApproval(models.Model):
    class ApprovalStatus(models.TextChoices):
        AWAITING_REVIEW = 'AWAITING_REVIEW', 'Awaiting Client Review'
        APPROVED = 'APPROVED', 'Approved'
        CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'

    requirement = models.ForeignKey(
        ProjectRequirement,
        on_delete=models.CASCADE,
        related_name='approvals'
    )
    version = models.PositiveIntegerField(default=1)
    approval_status = models.CharField(
        max_length=30,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.AWAITING_REVIEW
    )
    approver_name = models.CharField(max_length=150)
    approver_email = models.EmailField()
    client_feedback = models.TextField(blank=True, default='')
    revisions_requested = models.TextField(blank=True, default='')
    internal_comments = models.TextField(blank=True, default='')
    approved_at = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_approvals'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Approval V{self.version} for {self.requirement.requirement_reference} - {self.approval_status}"

import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from requirements.models import ProjectRequirement
from handover.models import HandoverRecord


class ProjectStatus(models.TextChoices):
    AWAITING_ASSIGNMENT = 'AWAITING_ASSIGNMENT', 'Awaiting Assignment'
    ASSIGNED = 'ASSIGNED', 'Assigned'
    NOT_STARTED = 'NOT_STARTED', 'Not Started'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    BLOCKED = 'BLOCKED', 'Blocked'
    INTERNAL_REVIEW = 'INTERNAL_REVIEW', 'Internal Review'
    CLIENT_REVIEW = 'CLIENT_REVIEW', 'Client Review'
    CHANGES_REQUESTED = 'CHANGES_REQUESTED', 'Changes Requested'
    COMPLETED = 'COMPLETED', 'Completed'
    DELIVERED = 'DELIVERED', 'Delivered'
    CLOSED = 'CLOSED', 'Closed'


def generate_project_code():
    year = timezone.now().year
    rand_seq = random.randint(1000, 9999)
    return f"XEYR-PRJ-{year}-{rand_seq}"


class DeveloperProject(models.Model):
    requirement = models.OneToOneField(
        ProjectRequirement,
        on_delete=models.CASCADE,
        related_name='developer_project'
    )
    handover = models.ForeignKey(
        HandoverRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects'
    )
    project_code = models.CharField(
        max_length=35,
        unique=True,
        default=generate_project_code,
        db_index=True
    )
    title = models.CharField(max_length=255)
    assigned_developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_dev_projects'
    )
    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_dev_projects'
    )
    status = models.CharField(
        max_length=35,
        choices=ProjectStatus.choices,
        default=ProjectStatus.AWAITING_ASSIGNMENT,
        db_index=True
    )
    priority = models.CharField(max_length=25, default='High')
    progress_percentage = models.PositiveSmallIntegerField(default=0)

    start_date = models.DateField(null=True, blank=True)
    expected_completion_date = models.DateField(null=True, blank=True, db_index=True)
    actual_completion_date = models.DateField(null=True, blank=True)

    developer_notes = models.TextField(blank=True, default='')
    blocker_description = models.TextField(blank=True, default='')
    testing_checklist = models.JSONField(default=list, blank=True)
    qa_status = models.CharField(max_length=50, default='Pending')
    client_acceptance_status = models.CharField(max_length=50, default='Pending')
    final_handover_notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.project_code} - {self.title} [{self.get_status_display()}] ({self.progress_percentage}%)"


class ProjectMilestone(models.Model):
    project = models.ForeignKey(
        DeveloperProject,
        on_delete=models.CASCADE,
        related_name='milestones'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['due_date', 'id']

    def __str__(self):
        return f"{self.title} - {'Done' if self.completed else 'Pending'}"


class ProjectDeliverable(models.Model):
    project = models.ForeignKey(
        DeveloperProject,
        on_delete=models.CASCADE,
        related_name='deliverables'
    )
    title = models.CharField(max_length=200)
    deliverable_type = models.CharField(max_length=100, default='Source Code Repository')
    url_or_ref = models.CharField(max_length=255, blank=True, default='')
    file = models.FileField(upload_to='deliverables/', blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_deliverables'
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='Submitted')

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.title} ({self.deliverable_type}) for {self.project.project_code}"

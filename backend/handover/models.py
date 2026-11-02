import os
import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from requirements.models import ProjectRequirement


def handover_upload_path(instance, filename):
    req_ref = instance.requirement.requirement_reference if instance.requirement else 'general'
    safe_name = os.path.basename(filename).replace(' ', '_')
    return f"handover_archives/{req_ref}/{safe_name}"


def generate_handover_ref():
    year = timezone.now().year
    rand_seq = random.randint(1000, 9999)
    return f"XEYR-HO-{year}-{rand_seq}"


class HandoverRecord(models.Model):
    requirement = models.ForeignKey(
        ProjectRequirement,
        on_delete=models.CASCADE,
        related_name='handover_records'
    )
    handover_reference = models.CharField(
        max_length=40,
        unique=True,
        default=generate_handover_ref,
        db_index=True
    )
    version = models.PositiveIntegerField(default=1)

    zip_file = models.FileField(upload_to=handover_upload_path, blank=True, null=True)
    zip_filename = models.CharField(max_length=255)
    zip_size = models.BigIntegerField(default=0, help_text="Size of ZIP file in bytes")
    zip_checksum_sha256 = models.CharField(max_length=64, blank=True, default='')

    manifest_data = models.JSONField(default=dict, blank=True)
    readiness_checklist = models.JSONField(default=dict, blank=True)
    all_checks_passed = models.BooleanField(default=False)
    has_documented_exception = models.BooleanField(default=False)
    exception_notes = models.TextField(blank=True, default='')

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='generated_handovers'
    )
    generated_at = models.DateTimeField(default=timezone.now, db_index=True)

    download_count = models.PositiveIntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    last_downloaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='downloaded_handovers'
    )

    # Developer Assignment & Instructions
    assigned_developer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_handovers'
    )
    developer_team = models.CharField(max_length=150, blank=True, default='Core Engineering Team')
    handover_instructions = models.TextField(blank=True, default='')
    priority = models.CharField(max_length=25, default='High')
    expected_delivery_date = models.DateField(null=True, blank=True)
    developer_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-version', '-generated_at']

    def __str__(self):
        return f"{self.handover_reference} V{self.version} for {self.requirement.requirement_reference}"

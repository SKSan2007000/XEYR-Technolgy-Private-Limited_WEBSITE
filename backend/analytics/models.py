from django.db import models
from django.utils import timezone
from django.conf import settings


class ReportExportLog(models.Model):
    class ReportType(models.TextChoices):
        ENQUIRIES_CSV = 'ENQUIRIES_CSV', 'Enquiries Export (CSV)'
        REJECTIONS_CSV = 'REJECTIONS_CSV', 'Rejections Report (CSV)'
        PROJECTS_CSV = 'PROJECTS_CSV', 'Projects Status Export (CSV)'
        FINANCIAL_CSV = 'FINANCIAL_CSV', 'Financial Performance (CSV)'
        EXECUTIVE_SUMMARY = 'EXECUTIVE_SUMMARY', 'Executive Analytics Summary (Printable)'

    report_type = models.CharField(max_length=40, choices=ReportType.choices)
    parameters = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='report_exports'
    )
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_report_type_display()} by {self.generated_by.username} at {self.timestamp}"

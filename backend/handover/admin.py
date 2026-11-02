from django.contrib import admin
from .models import HandoverRecord


@admin.register(HandoverRecord)
class HandoverRecordAdmin(admin.ModelAdmin):
    list_display = ('handover_reference', 'requirement', 'version', 'zip_checksum_sha256', 'generated_by', 'assigned_developer', 'download_count', 'generated_at')
    list_filter = ('version', 'generated_at')
    search_fields = ('handover_reference', 'requirement__requirement_reference', 'zip_checksum_sha256')
    readonly_fields = ('handover_reference', 'zip_checksum_sha256', 'generated_at', 'download_count')


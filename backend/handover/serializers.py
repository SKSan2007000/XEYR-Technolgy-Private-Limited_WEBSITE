from rest_framework import serializers
from .models import HandoverRecord


class HandoverRecordSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    assigned_developer_name = serializers.CharField(source='assigned_developer.get_full_name', read_only=True)
    requirement_reference = serializers.CharField(source='requirement.requirement_reference', read_only=True)
    project_name = serializers.CharField(source='requirement.project_name', read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = HandoverRecord
        fields = [
            'id', 'requirement', 'requirement_reference', 'project_name',
            'handover_reference', 'version', 'zip_filename', 'zip_size',
            'zip_checksum_sha256', 'manifest_data', 'readiness_checklist',
            'all_checks_passed', 'has_documented_exception', 'exception_notes',
            'generated_by', 'generated_by_name', 'generated_at',
            'download_count', 'last_downloaded_at', 'last_downloaded_by',
            'assigned_developer', 'assigned_developer_name', 'developer_team',
            'handover_instructions', 'priority', 'expected_delivery_date',
            'developer_acknowledged', 'acknowledged_at', 'download_url'
        ]
        read_only_fields = ['id', 'handover_reference', 'generated_by', 'generated_at', 'zip_checksum_sha256', 'zip_size']

    def get_download_url(self, obj):
        return f"/api/handover/{obj.id}/download/"

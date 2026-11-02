from rest_framework import serializers
from .models import Enquiry, EnquiryQualification, EnquiryRejection, CRMActivity, EnquiryStatus, RejectionCategory
from core.serializers import UserSerializer


class EnquiryQualificationSerializer(serializers.ModelSerializer):
    qualified_by_name = serializers.CharField(source='qualified_by.get_full_name', read_only=True)
    account_manager_name = serializers.CharField(source='account_manager.get_full_name', read_only=True)

    class Meta:
        model = EnquiryQualification
        fields = [
            'id', 'decision', 'business_opportunity', 'client_needs', 'service_fit',
            'estimated_project_value', 'budget_confirmed', 'timeline_confirmed',
            'decision_maker_details', 'technical_feasibility', 'internal_assessment',
            'account_manager', 'account_manager_name', 'next_action', 'follow_up_date',
            'qualified_by', 'qualified_by_name', 'qualified_at'
        ]
        read_only_fields = ['id', 'qualified_by', 'qualified_at']


class EnquiryRejectionSerializer(serializers.ModelSerializer):
    rejected_by_name = serializers.CharField(source='rejected_by.get_full_name', read_only=True)
    reopened_by_name = serializers.CharField(source='reopened_by.get_full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = EnquiryRejection
        fields = [
            'id', 'enquiry', 'category', 'category_display', 'reason_detail',
            'internal_notes', 'previous_status', 'future_followup_appropriate',
            'rejected_by', 'rejected_by_name', 'rejected_at',
            'reopened', 'reopen_reason', 'reopened_by', 'reopened_by_name', 'reopened_at'
        ]
        read_only_fields = ['id', 'rejected_by', 'rejected_at', 'previous_status', 'reopened', 'reopened_by', 'reopened_at']

    def validate(self, data):
        category = data.get('category')
        reason_detail = data.get('reason_detail', '').strip()

        if not category:
            raise serializers.ValidationError({'category': 'Rejection category is strictly required.'})

        if category == RejectionCategory.OTHER and not reason_detail:
            raise serializers.ValidationError({'reason_detail': 'Detailed explanation is mandatory when category is Other.'})

        if not reason_detail:
            raise serializers.ValidationError({'reason_detail': 'A written rejection reason must be provided.'})

        return data


class CRMActivitySerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = CRMActivity
        fields = [
            'id', 'enquiry', 'activity_type', 'title', 'description',
            'scheduled_at', 'completed_at', 'performed_by', 'performed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'performed_by', 'created_at']


class EnquirySerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    qualification = EnquiryQualificationSerializer(read_only=True)
    rejections = EnquiryRejectionSerializer(many=True, read_only=True)
    activities = CRMActivitySerializer(many=True, read_only=True)
    has_requirement_workspace = serializers.SerializerMethodField()
    requirement_reference = serializers.SerializerMethodField()

    class Meta:
        model = Enquiry
        fields = [
            'id', 'reference_id', 'client_name', 'contact_person', 'email', 'phone',
            'organisation_type', 'service_type', 'project_title', 'project_description',
            'budget_range', 'expected_timeline', 'preferred_contact_method', 'source',
            'status', 'assigned_to', 'assigned_to_name', 'internal_notes', 'follow_up_date',
            'created_at', 'updated_at', 'qualification', 'rejections', 'activities',
            'has_requirement_workspace', 'requirement_reference'
        ]
        read_only_fields = ['id', 'reference_id', 'created_at', 'updated_at']

    def get_has_requirement_workspace(self, obj):
        return hasattr(obj, 'requirement_workspace')

    def get_requirement_reference(self, obj):
        if hasattr(obj, 'requirement_workspace'):
            return obj.requirement_workspace.requirement_reference
        return None

    def validate_client_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Client or organisation name is required.")
        return value.strip()

    def validate_phone(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Phone number is required.")
        return value.strip()

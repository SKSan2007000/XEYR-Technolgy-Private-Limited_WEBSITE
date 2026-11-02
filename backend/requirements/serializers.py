from rest_framework import serializers
from .models import ProjectRequirement, RequirementApproval
from assets_mgmt.models import ClientBrandAsset


class BrandAssetSummarySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = ClientBrandAsset
        fields = ['id', 'title', 'category', 'category_display', 'filename', 'file_size', 'status', 'status_display', 'version', 'checksum_sha256']


class RequirementApprovalSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)

    class Meta:
        model = RequirementApproval
        fields = [
            'id', 'version', 'approval_status', 'approver_name', 'approver_email',
            'client_feedback', 'revisions_requested', 'internal_comments',
            'approved_at', 'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']


class ProjectRequirementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    enquiry_reference = serializers.CharField(source='enquiry.reference_id', read_only=True)
    enquiry_client_name = serializers.CharField(source='enquiry.client_name', read_only=True)
    approvals = RequirementApprovalSerializer(many=True, read_only=True)
    brand_assets = BrandAssetSummarySerializer(many=True, read_only=True)

    class Meta:
        model = ProjectRequirement
        fields = [
            'id', 'enquiry', 'enquiry_reference', 'enquiry_client_name',
            'requirement_reference', 'status', 'version',

            # Section A: Client Information
            'legal_business_name', 'client_contact_person', 'official_email',
            'official_phone', 'business_address', 'industry_category', 'website_and_socials',

            # Section B: Project Overview
            'project_name', 'project_type', 'business_problem', 'project_goals',
            'target_audience', 'expected_deliverables', 'scope_of_work', 'features_required',
            'functional_requirements', 'non_functional_requirements', 'technical_preferences',
            'integrations_required', 'accessibility_responsive_reqs', 'hosting_deployment_reqs',
            'maintenance_reqs',

            # Section C: Commercial Details
            'quoted_price', 'approved_budget', 'payment_milestones', 'expected_start_date',
            'expected_delivery_date', 'contract_proposal_ref', 'commercial_approval_status',

            # Section D: Design Requirements
            'design_style', 'color_preferences', 'typography_preferences',
            'reference_websites', 'wireframe_notes', 'ui_ux_requirements',
            'brand_guidelines_notes', 'required_page_list', 'device_requirements',

            # Section E: Technical Requirements
            'preferred_framework', 'backend_requirements', 'database_requirements',
            'api_integrations', 'auth_requirements', 'user_roles_req', 'security_requirements',
            'deployment_platform', 'repository_details', 'testing_requirements',
            'documentation_requirements',

            # Section F: Project Management & Custom Fields
            'project_owner', 'project_manager_assigned', 'developer_assigned', 'priority',
            'milestones', 'tasks', 'dependencies', 'risks', 'client_approval_checkpoints',
            'delivery_checklist', 'acceptance_criteria', 'custom_fields',

            # Audit
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at', 'approvals', 'brand_assets'
        ]
        read_only_fields = ['id', 'requirement_reference', 'created_by', 'created_at', 'updated_at']

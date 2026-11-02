from rest_framework import serializers
from .models import DeveloperProject, ProjectMilestone, ProjectDeliverable


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = ['id', 'project', 'title', 'description', 'due_date', 'completed', 'completed_at']


class ProjectDeliverableSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)

    class Meta:
        model = ProjectDeliverable
        fields = ['id', 'project', 'title', 'deliverable_type', 'url_or_ref', 'file', 'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'status']
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at']


class DeveloperProjectSerializer(serializers.ModelSerializer):
    assigned_developer_name = serializers.CharField(source='assigned_developer.get_full_name', read_only=True)
    project_manager_name = serializers.CharField(source='project_manager.get_full_name', read_only=True)
    requirement_reference = serializers.CharField(source='requirement.requirement_reference', read_only=True)
    client_name = serializers.CharField(source='requirement.legal_business_name', read_only=True)
    milestones = ProjectMilestoneSerializer(many=True, read_only=True)
    deliverables = ProjectDeliverableSerializer(many=True, read_only=True)

    class Meta:
        model = DeveloperProject
        fields = [
            'id', 'requirement', 'requirement_reference', 'client_name',
            'project_code', 'title', 'assigned_developer', 'assigned_developer_name',
            'project_manager', 'project_manager_name', 'status', 'priority',
            'progress_percentage', 'start_date', 'expected_completion_date',
            'actual_completion_date', 'developer_notes', 'blocker_description',
            'testing_checklist', 'qa_status', 'client_acceptance_status',
            'final_handover_notes', 'milestones', 'deliverables', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'project_code', 'created_at', 'updated_at']

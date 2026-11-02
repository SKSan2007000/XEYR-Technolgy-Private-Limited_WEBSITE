from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import DeveloperProject, ProjectMilestone, ProjectDeliverable, ProjectStatus
from .serializers import DeveloperProjectSerializer, ProjectMilestoneSerializer, ProjectDeliverableSerializer
from core.models import AuditLog, Notification


class ProjectListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        projects = DeveloperProject.objects.select_related('requirement', 'assigned_developer', 'project_manager').prefetch_related('milestones', 'deliverables').all()

        # Role filtering: developers only see assigned projects
        if request.user.role == 'DEVELOPER':
            projects = projects.filter(assigned_developer=request.user)

        status_filter = request.query_params.get('status')
        if status_filter:
            projects = projects.filter(status=status_filter)

        serializer = DeveloperProjectSerializer(projects, many=True)
        return Response(serializer.data)


class ProjectDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            project = DeveloperProject.objects.select_related('requirement', 'assigned_developer', 'project_manager').prefetch_related('milestones', 'deliverables').get(pk=pk)
        except DeveloperProject.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'DEVELOPER' and project.assigned_developer != request.user:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = DeveloperProjectSerializer(project)
        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            project = DeveloperProject.objects.get(pk=pk)
        except DeveloperProject.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == 'DEVELOPER' and project.assigned_developer != request.user:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        old_status = project.status
        serializer = DeveloperProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()

            if updated.status != old_status:
                AuditLog.log('PROJECT_STATUS_CHANGED', 'DeveloperProject', updated.id, user=request.user, details={'from': old_status, 'to': updated.status}, request=request)
                if updated.status == ProjectStatus.BLOCKED:
                    Notification.objects.create(
                        title=f"Project Blocked: {updated.project_code}",
                        message=f"Project '{updated.title}' was marked as BLOCKED: {updated.blocker_description}",
                        notification_type='PROJECT_BLOCKED',
                        link=f"/dashboard/#projects-{updated.id}"
                    )

            return Response(DeveloperProjectSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MilestoneCreateToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id):
        try:
            project = DeveloperProject.objects.get(pk=project_id)
        except DeveloperProject.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        milestone_id = request.data.get('milestone_id')
        if milestone_id:
            try:
                ms = ProjectMilestone.objects.get(pk=milestone_id, project=project)
                ms.completed = request.data.get('completed', not ms.completed)
                ms.completed_at = timezone.now() if ms.completed else None
                ms.save()
                return Response(ProjectMilestoneSerializer(ms).data)
            except ProjectMilestone.DoesNotExist:
                return Response({'error': 'Milestone not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectMilestoneSerializer(data={**request.data, 'project': project.id})
        if serializer.is_valid():
            ms = serializer.save()
            return Response(ProjectMilestoneSerializer(ms).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeliverableCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id):
        try:
            project = DeveloperProject.objects.get(pk=project_id)
        except DeveloperProject.DoesNotExist:
            return Response({'error': 'Project not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        deliverable = ProjectDeliverable.objects.create(
            project=project,
            title=data.get('title', 'Deliverable Submission'),
            deliverable_type=data.get('deliverable_type', 'Source Code Repository'),
            url_or_ref=data.get('url_or_ref', ''),
            file=request.FILES.get('file'),
            uploaded_by=request.user,
            status='Submitted'
        )
        AuditLog.log('DELIVERABLE_SUBMITTED', 'DeveloperProject', project.id, user=request.user, details={'title': deliverable.title, 'type': deliverable.deliverable_type}, request=request)
        return Response(ProjectDeliverableSerializer(deliverable).data, status=status.HTTP_201_CREATED)

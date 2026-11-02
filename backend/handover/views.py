import os
from django.http import FileResponse, Http404
from django.utils import timezone
from django.db import transaction
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import HandoverRecord
from .serializers import HandoverRecordSerializer
from .generator import HandoverZipGenerator
from requirements.models import ProjectRequirement
from projects.models import DeveloperProject, ProjectStatus
from core.models import AuditLog, Notification


class HandoverListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, requirement_id=None):
        records = HandoverRecord.objects.select_related('requirement', 'generated_by', 'assigned_developer')
        if requirement_id:
            records = records.filter(requirement_id=requirement_id)
        serializer = HandoverRecordSerializer(records, many=True)
        return Response(serializer.data)

    def post(self, request, requirement_id):
        """
        Generate a real Developer Handover ZIP package.
        Checks readiness checklist, validates files, executes HandoverZipGenerator.
        """
        if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN', 'PROJECT_MANAGER']):
            return Response({'error': 'Permission denied. Only Administrators and Project Managers can generate developer handover packages.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            req = ProjectRequirement.objects.get(pk=requirement_id)
        except ProjectRequirement.DoesNotExist:
            return Response({'error': 'Requirement workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

        force_exception = request.data.get('force_with_exception', False)
        exception_notes = request.data.get('exception_notes', '')

        generator = HandoverZipGenerator(req, request.user, exception_notes=exception_notes)

        try:
            record = generator.generate(force_with_exception=force_exception)
        except ValueError as e:
            return Response({'error': str(e), 'checklist': generator.validate_readiness()[0]}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Failed to generate handover ZIP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        AuditLog.log(
            'HANDOVER_ZIP_GENERATED',
            'HandoverRecord',
            record.id,
            user=request.user,
            details={
                'handover_reference': record.handover_reference,
                'version': record.version,
                'zip_filename': record.zip_filename,
                'size_bytes': record.zip_size,
                'checksum': record.zip_checksum_sha256
            },
            request=request
        )

        Notification.objects.create(
            title=f"Developer Handover ZIP Generated: {record.handover_reference}",
            message=f"ZIP archive V{record.version} created for {req.project_name}.",
            notification_type='HANDOVER_READY',
            link=f"/dashboard/#handover-{req.id}"
        )

        return Response(HandoverRecordSerializer(record).data, status=status.HTTP_201_CREATED)


class HandoverDownloadView(APIView):
    """
    Real ZIP download view with tracking and authorization checks.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            record = HandoverRecord.objects.select_related('requirement', 'assigned_developer').get(pk=pk)
        except HandoverRecord.DoesNotExist:
            raise Http404("Handover record not found.")

        # Check permissions: Devs can only download their assigned packages
        if request.user.role == 'DEVELOPER':
            if record.assigned_developer != request.user and record.requirement.developer_assigned != request.user:
                return Response({'error': 'You are not authorized to download this project package.'}, status=status.HTTP_403_FORBIDDEN)

        if not record.zip_file or not os.path.exists(record.zip_file.path):
            raise Http404("Handover archive not found on disk.")

        # Update download tracking
        record.download_count += 1
        record.last_downloaded_at = timezone.now()
        record.last_downloaded_by = request.user
        record.save(update_fields=['download_count', 'last_downloaded_at', 'last_downloaded_by'])

        AuditLog.log(
            'HANDOVER_ZIP_DOWNLOADED',
            'HandoverRecord',
            record.id,
            user=request.user,
            details={'handover_reference': record.handover_reference, 'download_count': record.download_count},
            request=request
        )

        return FileResponse(
            open(record.zip_file.path, 'rb'),
            as_attachment=True,
            filename=record.zip_filename,
            content_type='application/zip'
        )


class HandoverAssignDeveloperView(APIView):
    """
    Assign a developer to the handover project and activate/create DeveloperProject.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            record = HandoverRecord.objects.select_related('requirement').get(pk=pk)
        except HandoverRecord.DoesNotExist:
            return Response({'error': 'Handover record not found.'}, status=status.HTTP_404_NOT_FOUND)

        developer_id = request.data.get('developer_id')
        developer_team = request.data.get('developer_team', 'Core Engineering Team')
        instructions = request.data.get('instructions', '')
        priority = request.data.get('priority', record.priority)
        expected_date = request.data.get('expected_delivery_date')

        with transaction.atomic():
            if developer_id:
                record.assigned_developer_id = developer_id
            record.developer_team = developer_team
            record.handover_instructions = instructions
            record.priority = priority
            if expected_date:
                record.expected_delivery_date = expected_date
            record.save()

            # Update requirement assignment
            req = record.requirement
            if developer_id:
                req.developer_assigned_id = developer_id
                req.save(update_fields=['developer_assigned'])

            # Create or activate DeveloperProject record
            dev_project, prj_created = DeveloperProject.objects.update_or_create(
                requirement=req,
                defaults={
                    'handover': record,
                    'title': req.project_name,
                    'assigned_developer_id': developer_id or req.developer_assigned_id,
                    'project_manager': request.user,
                    'status': ProjectStatus.ASSIGNED if developer_id else ProjectStatus.AWAITING_ASSIGNMENT,
                    'priority': priority,
                    'expected_completion_date': expected_date or req.expected_delivery_date,
                    'developer_notes': instructions
                }
            )

            AuditLog.log(
                'DEVELOPER_ASSIGNED_TO_PROJECT',
                'HandoverRecord',
                record.id,
                user=request.user,
                details={'developer_id': developer_id, 'project_code': dev_project.project_code},
                request=request
            )

            if developer_id:
                Notification.objects.create(
                    user_id=developer_id,
                    title=f"Project Assigned: {dev_project.title}",
                    message=f"You have been assigned to project {dev_project.project_code} ({req.project_name}).",
                    notification_type='DEVELOPER_ASSIGNED',
                    link=f"/dashboard/#projects-{dev_project.id}"
                )

        return Response({
            'message': 'Developer assigned and project activated successfully.',
            'handover': HandoverRecordSerializer(record).data,
            'project_code': dev_project.project_code
        })

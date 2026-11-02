from django.db import transaction
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ProjectRequirement, RequirementApproval, RequirementStatus
from .serializers import ProjectRequirementSerializer, RequirementApprovalSerializer
from crm.models import Enquiry, EnquiryStatus
from core.models import AuditLog, Notification
from handover.generator import HandoverZipGenerator


class RequirementWorkspaceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enquiry_id=None):
        if enquiry_id:
            try:
                enquiry = Enquiry.objects.get(pk=enquiry_id)
            except Enquiry.DoesNotExist:
                return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

            req, created = ProjectRequirement.objects.get_or_create(
                enquiry=enquiry,
                defaults={
                    'project_name': enquiry.project_title or f"{enquiry.client_name} Solution",
                    'legal_business_name': enquiry.client_name,
                    'client_contact_person': enquiry.contact_person,
                    'official_email': enquiry.email,
                    'official_phone': enquiry.phone,
                    'scope_of_work': enquiry.project_description,
                    'created_by': request.user
                }
            )
            serializer = ProjectRequirementSerializer(req)
            return Response(serializer.data)

        # List all requirements
        requirements = ProjectRequirement.objects.select_related('enquiry', 'created_by', 'updated_by').all()
        serializer = ProjectRequirementSerializer(requirements, many=True)
        return Response(serializer.data)

    def patch(self, request, enquiry_id):
        try:
            req = ProjectRequirement.objects.get(enquiry_id=enquiry_id)
        except ProjectRequirement.DoesNotExist:
            return Response({'error': 'Requirement workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        serializer = ProjectRequirementSerializer(req, data=data, partial=True)
        if serializer.is_valid():
            with transaction.atomic():
                updated_req = serializer.save(
                    updated_by=request.user,
                    version=req.version + 1
                )
                AuditLog.log('REQUIREMENTS_UPDATED', 'ProjectRequirement', updated_req.id, user=request.user, details={'version': updated_req.version}, request=request)
            return Response(ProjectRequirementSerializer(updated_req).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequirementApprovalView(APIView):
    """
    Stage 7 - Client Requirements Review & Approval Process.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, enquiry_id):
        try:
            req = ProjectRequirement.objects.get(enquiry_id=enquiry_id)
        except ProjectRequirement.DoesNotExist:
            return Response({'error': 'Requirement workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        new_status = data.get('approval_status')  # 'AWAITING_REVIEW', 'APPROVED', 'CHANGES_REQUESTED'

        if not new_status:
            return Response({'error': 'approval_status is required.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            approval = RequirementApproval.objects.create(
                requirement=req,
                version=req.version,
                approval_status=new_status,
                approver_name=data.get('approver_name', req.client_contact_person or 'Client Lead'),
                approver_email=data.get('approver_email', req.official_email or 'client@example.com'),
                client_feedback=data.get('client_feedback', ''),
                revisions_requested=data.get('revisions_requested', ''),
                internal_comments=data.get('internal_comments', ''),
                approved_at=timezone.now() if new_status == 'APPROVED' else None,
                recorded_by=request.user
            )

            # Update requirement status
            if new_status == 'APPROVED':
                req.status = RequirementStatus.APPROVED
                req.commercial_approval_status = 'Approved'
                req.enquiry.status = EnquiryStatus.REQUIREMENTS_COMPLETED
                req.enquiry.save(update_fields=['status'])
            elif new_status == 'CHANGES_REQUESTED':
                req.status = RequirementStatus.CHANGES_REQUESTED
            else:
                req.status = RequirementStatus.AWAITING_CLIENT_REVIEW
            req.save()

            AuditLog.log('REQUIREMENT_APPROVAL_RECORDED', 'ProjectRequirement', req.id, user=request.user, details={'approval_status': new_status, 'version': req.version}, request=request)

            Notification.objects.create(
                title=f"Requirements Approval Update: {req.requirement_reference}",
                message=f"Requirements for {req.project_name} were marked as '{new_status}'.",
                notification_type='APPROVAL_PENDING',
                link=f"/dashboard/#requirements-{req.enquiry_id}"
            )

        return Response({
            'message': f"Approval record created: {new_status}",
            'requirement': ProjectRequirementSerializer(req).data,
            'approval': RequirementApprovalSerializer(approval).data
        })


class RequirementReadinessView(APIView):
    """
    Check readiness criteria for Developer Handover ZIP Generation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, enquiry_id):
        try:
            req = ProjectRequirement.objects.get(enquiry_id=enquiry_id)
        except ProjectRequirement.DoesNotExist:
            return Response({'error': 'Requirement workspace not found.'}, status=status.HTTP_404_NOT_FOUND)

        generator = HandoverZipGenerator(req, request.user)
        checks, all_passed = generator.validate_readiness()

        return Response({
            'requirement_reference': req.requirement_reference,
            'project_name': req.project_name,
            'all_checks_passed': all_passed,
            'checks': checks,
            'can_generate_zip': all_passed or request.user.role in ['SUPER_ADMIN', 'BUSINESS_ADMIN']
        })

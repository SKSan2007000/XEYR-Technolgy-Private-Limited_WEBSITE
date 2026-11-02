from django.db import transaction
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Enquiry, EnquiryQualification, EnquiryRejection, CRMActivity, EnquiryStatus, RejectionCategory
from .serializers import EnquirySerializer, EnquiryQualificationSerializer, EnquiryRejectionSerializer, CRMActivitySerializer
from core.models import AuditLog, Notification
from requirements.models import ProjectRequirement


class PublicEnquirySubmitView(APIView):
    """
    Public API endpoint to receive enquiries from the existing XEYR website forms.
    Rate limited, CSRF-exempt for public API access, validated server-side.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data.copy()

        # Map frontend form variations
        name = data.get('name') or data.get('contact_person') or data.get('client_name')
        email = data.get('email')
        phone = data.get('phone')
        organisation = data.get('organisation') or data.get('company') or name or 'Individual / Organization'
        form_type = data.get('form_type') or data.get('type') or 'website-enquiry'

        service_map = {
            'solvex-enquiry': 'SolveX - Business Solution',
            'college-service': 'SkillBridge - College Workshop',
            'college-service-enquiry': 'SkillBridge - College Workshop',
            'skillbridge-professional': 'SkillBridge - Professional Application',
            'skillbridge-professional-application': 'SkillBridge - Professional Application',
            'event-registration-interest': 'Event Registration',
        }
        service_type = service_map.get(form_type, data.get('service_type', 'General Business Enquiry'))

        project_desc = data.get('project_description') or data.get('skills') or data.get('message') or f"Submitted via public website ({form_type})"

        if not name or not email or not phone:
            return Response(
                {'error': 'Name, email, and phone number are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            enquiry = Enquiry.objects.create(
                client_name=organisation,
                contact_person=name,
                email=email,
                phone=phone,
                service_type=service_type,
                project_title=data.get('project_title', f"New {service_type}"),
                project_description=project_desc,
                budget_range=data.get('budget_range', 'To be discussed'),
                source=f"Website ({form_type})",
                status=EnquiryStatus.NEW
            )

            # Record internal audit log
            AuditLog.log(
                'PUBLIC_ENQUIRY_SUBMITTED',
                'Enquiry',
                enquiry.id,
                details={
                    'reference_id': enquiry.reference_id,
                    'client_name': enquiry.client_name,
                    'service': enquiry.service_type,
                    'form_type': form_type
                },
                request=request
            )

            # Dispatch notification to business administrators
            Notification.objects.create(
                title=f"New Enquiry: {enquiry.reference_id}",
                message=f"{enquiry.client_name} submitted a new enquiry for '{enquiry.service_type}'.",
                notification_type='NEW_ENQUIRY',
                link=f"/dashboard/#enquiry-{enquiry.id}"
            )

        return Response({
            'success': True,
            'message': 'Thank you for reaching out to XEYR Technologies. Your enquiry has been received.',
            'reference_id': enquiry.reference_id,
            'client_name': enquiry.client_name,
            'status': enquiry.status
        }, status=status.HTTP_201_CREATED)


class EnquiryListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')
        source_filter = request.query_params.get('source')
        search_query = request.query_params.get('search')

        enquiries = Enquiry.objects.select_related('assigned_to').prefetch_related('rejections', 'activities').all()

        if status_filter:
            enquiries = enquiries.filter(status=status_filter)
        if source_filter:
            enquiries = enquiries.filter(source__icontains=source_filter)
        if search_query:
            enquiries = enquiries.filter(
                models.Q(client_name__icontains=search_query) |
                models.Q(contact_person__icontains=search_query) |
                models.Q(email__icontains=search_query) |
                models.Q(phone__icontains=search_query) |
                models.Q(reference_id__icontains=search_query)
            )

        serializer = EnquirySerializer(enquiries, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EnquirySerializer(data=request.data)
        if serializer.is_valid():
            enquiry = serializer.save()
            AuditLog.log('ENQUIRY_CREATED_MANUAL', 'Enquiry', enquiry.id, user=request.user, details={'reference_id': enquiry.reference_id}, request=request)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnquiryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            enquiry = Enquiry.objects.select_related('assigned_to').prefetch_related('rejections', 'activities').get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EnquirySerializer(enquiry)
        return Response(serializer.data)

    def patch(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EnquirySerializer(enquiry, data=request.data, partial=True)
        if serializer.is_valid():
            enquiry = serializer.save()
            AuditLog.log('ENQUIRY_UPDATED', 'Enquiry', enquiry.id, user=request.user, details=request.data, request=request)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnquiryStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status or new_status not in EnquiryStatus.values:
            return Response({'error': f'Invalid status. Allowed values: {EnquiryStatus.values}'}, status=status.HTTP_400_BAD_REQUEST)

        # Rejection must be handled via EnquiryRejectView
        if new_status == EnquiryStatus.REJECTED:
            return Response({'error': 'To reject an enquiry, you must provide a mandatory rejection reason through the rejection endpoint.'}, status=status.HTTP_400_BAD_REQUEST)

        old_status = enquiry.status
        enquiry.status = new_status
        if 'assigned_to' in request.data:
            enquiry.assigned_to_id = request.data.get('assigned_to')
        if 'follow_up_date' in request.data:
            enquiry.follow_up_date = request.data.get('follow_up_date')
        if 'internal_notes' in request.data:
            enquiry.internal_notes = request.data.get('internal_notes')
        enquiry.save()

        AuditLog.log('ENQUIRY_STATUS_CHANGED', 'Enquiry', enquiry.id, user=request.user, details={'from': old_status, 'to': new_status}, request=request)
        CRMActivity.objects.create(
            enquiry=enquiry,
            activity_type=CRMActivity.ActivityType.STATUS_CHANGE,
            title=f"Status changed from {old_status} to {new_status}",
            description=request.data.get('notes', ''),
            performed_by=request.user
        )

        return Response(EnquirySerializer(enquiry).data)


class EnquiryQualifyView(APIView):
    """
    Stage 3 - Enquiry Qualification Workflow.
    Saves qualification decision, business opportunity, estimated value,
    updates status to QUALIFIED, and can initialize the Client Requirements Workspace.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        decision = data.get('decision', 'Qualified for Development')
        try:
            est_val = float(data.get('estimated_project_value') or 0.00)
        except (ValueError, TypeError):
            est_val = 0.00

        with transaction.atomic():
            qual, created = EnquiryQualification.objects.update_or_create(
                enquiry=enquiry,
                defaults={
                    'decision': decision,
                    'business_opportunity': data.get('business_opportunity', ''),
                    'client_needs': data.get('client_needs', ''),
                    'service_fit': data.get('service_fit', ''),
                    'estimated_project_value': est_val,
                    'budget_confirmed': data.get('budget_confirmed', False),
                    'timeline_confirmed': data.get('timeline_confirmed', False),
                    'decision_maker_details': data.get('decision_maker_details', ''),
                    'technical_feasibility': data.get('technical_feasibility', ''),
                    'internal_assessment': data.get('internal_assessment', ''),
                    'account_manager_id': data.get('account_manager') or request.user.id,
                    'next_action': data.get('next_action', 'Start Client Requirements Collection'),
                    'follow_up_date': data.get('follow_up_date'),
                    'qualified_by': request.user,
                    'qualified_at': timezone.now()
                }
            )

            old_status = enquiry.status
            enquiry.status = EnquiryStatus.QUALIFIED
            enquiry.save()

            # Ensure Requirements Workspace exists or initialize it
            req_workspace, req_created = ProjectRequirement.objects.get_or_create(
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

            AuditLog.log('ENQUIRY_QUALIFIED', 'Enquiry', enquiry.id, user=request.user, details={'decision': decision, 'estimated_value': float(est_val)}, request=request)
            CRMActivity.objects.create(
                enquiry=enquiry,
                activity_type=CRMActivity.ActivityType.STATUS_CHANGE,
                title=f"Enquiry Qualified: {decision}",
                description=f"Estimated project value: ₹{est_val:,.2f}. Next action: {qual.next_action}",
                performed_by=request.user
            )

            Notification.objects.create(
                title=f"Enquiry Qualified: {enquiry.reference_id}",
                message=f"{enquiry.client_name} was qualified by {request.user.get_full_name() or request.user.username}.",
                notification_type='QUALIFIED',
                link=f"/dashboard/#requirements-{enquiry.id}"
            )

        return Response({
            'message': 'Enquiry qualified successfully.',
            'enquiry': EnquirySerializer(enquiry).data,
            'requirement_reference': req_workspace.requirement_reference
        })


class EnquiryRejectView(APIView):
    """
    Stage 6 - Rejection Workflow with Mandatory Reasons.
    Blocks rejection if category or reason detail is missing.
    Keeps historical records and logs audit trail.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        category = request.data.get('category')
        reason_detail = request.data.get('reason_detail', '').strip()
        internal_notes = request.data.get('internal_notes', '').strip()
        future_followup = request.data.get('future_followup_appropriate', False)

        if not category or category not in RejectionCategory.values:
            return Response({
                'error': f'Rejection category is mandatory. Must be one of: {RejectionCategory.values}'
            }, status=status.HTTP_400_BAD_REQUEST)

        if category == RejectionCategory.OTHER and not reason_detail:
            return Response({
                'error': 'When category is Other, a detailed written explanation is mandatory.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not reason_detail:
            return Response({
                'error': 'A detailed rejection reason is required before rejecting an enquiry.'
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            old_status = enquiry.status

            rejection = EnquiryRejection.objects.create(
                enquiry=enquiry,
                category=category,
                reason_detail=reason_detail,
                internal_notes=internal_notes,
                previous_status=old_status,
                future_followup_appropriate=future_followup,
                rejected_by=request.user,
                rejected_at=timezone.now()
            )

            enquiry.status = EnquiryStatus.REJECTED
            enquiry.save()

            AuditLog.log(
                'ENQUIRY_REJECTED',
                'Enquiry',
                enquiry.id,
                user=request.user,
                details={
                    'category': category,
                    'reason_detail': reason_detail,
                    'previous_status': old_status
                },
                request=request
            )

            CRMActivity.objects.create(
                enquiry=enquiry,
                activity_type=CRMActivity.ActivityType.STATUS_CHANGE,
                title=f"Enquiry Rejected: {rejection.get_category_display()}",
                description=f"Reason: {reason_detail}\nInternal Notes: {internal_notes}",
                performed_by=request.user
            )

        return Response({
            'message': 'Enquiry rejected with documented reason.',
            'enquiry': EnquirySerializer(enquiry).data,
            'rejection': EnquiryRejectionSerializer(rejection).data
        })


class EnquiryReopenView(APIView):
    """
    Reopen a previously rejected enquiry with a mandatory justification.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        if enquiry.status != EnquiryStatus.REJECTED:
            return Response({'error': 'Only rejected enquiries can be reopened.'}, status=status.HTTP_400_BAD_REQUEST)

        reopen_reason = (request.data.get('reopen_reason') or request.data.get('notes') or '').strip()
        if not reopen_reason:
            return Response({'error': 'Reopen justification reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Mark latest rejection as reopened
            latest_rejection = enquiry.rejections.filter(reopened=False).first()
            if latest_rejection:
                latest_rejection.reopened = True
                latest_rejection.reopen_reason = reopen_reason
                latest_rejection.reopened_by = request.user
                latest_rejection.reopened_at = timezone.now()
                latest_rejection.save()

            enquiry.status = EnquiryStatus.UNDER_REVIEW
            enquiry.save()

            AuditLog.log('ENQUIRY_REOPENED', 'Enquiry', enquiry.id, user=request.user, details={'reopen_reason': reopen_reason}, request=request)
            CRMActivity.objects.create(
                enquiry=enquiry,
                activity_type=CRMActivity.ActivityType.STATUS_CHANGE,
                title="Enquiry Reopened from Rejection",
                description=f"Justification: {reopen_reason}",
                performed_by=request.user
            )

        return Response({
            'message': 'Enquiry reopened successfully and moved to Under Review.',
            'enquiry': EnquirySerializer(enquiry).data
        })


class CRMActivityCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            enquiry = Enquiry.objects.get(pk=pk)
        except Enquiry.DoesNotExist:
            return Response({'error': 'Enquiry not found.'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        activity = CRMActivity.objects.create(
            enquiry=enquiry,
            activity_type=data.get('activity_type', CRMActivity.ActivityType.NOTE),
            title=data.get('title', 'Follow-up Note'),
            description=data.get('description', ''),
            scheduled_at=data.get('scheduled_at'),
            completed_at=data.get('completed_at', timezone.now()),
            performed_by=request.user
        )

        AuditLog.log('CRM_ACTIVITY_ADDED', 'Enquiry', enquiry.id, user=request.user, details={'activity_type': activity.activity_type, 'title': activity.title}, request=request)
        return Response(CRMActivitySerializer(activity).data, status=status.HTTP_201_CREATED)

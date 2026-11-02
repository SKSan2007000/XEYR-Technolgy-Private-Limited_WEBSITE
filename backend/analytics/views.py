import csv
import io
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q, Avg
from django.http import HttpResponse
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from crm.models import Enquiry, EnquiryStatus, EnquiryRejection, RejectionCategory
from requirements.models import ProjectRequirement, RequirementStatus
from handover.models import HandoverRecord
from projects.models import DeveloperProject, ProjectStatus
from finance.models import InvoiceQuote, PaymentRecord, ExpenseRecord
from events_mgmt.models import EventListing, EventRegistration, SkillBridgeCollegeEnquiry, SkillBridgeProfessionalApplication
from core.models import AuditLog


def get_date_range(filter_key, start_str=None, end_str=None):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if filter_key == 'today':
        return today_start, now
    elif filter_key == 'yesterday':
        yesterday_start = today_start - timedelta(days=1)
        return yesterday_start, today_start
    elif filter_key == 'last_7_days':
        return today_start - timedelta(days=7), now
    elif filter_key == 'this_week':
        start_of_week = today_start - timedelta(days=today_start.weekday())
        return start_of_week, now
    elif filter_key == 'last_week':
        start_of_last_week = today_start - timedelta(days=today_start.weekday() + 7)
        end_of_last_week = start_of_last_week + timedelta(days=7)
        return start_of_last_week, end_of_last_week
    elif filter_key == 'last_30_days':
        return today_start - timedelta(days=30), now
    elif filter_key == 'this_month':
        start_of_month = today_start.replace(day=1)
        return start_of_month, now
    elif filter_key == 'last_month':
        first_this_month = today_start.replace(day=1)
        last_month_end = first_this_month - timedelta(days=1)
        start_last_month = last_month_end.replace(day=1)
        return start_last_month, first_this_month
    elif filter_key == 'this_quarter':
        quarter_month = ((today_start.month - 1) // 3) * 3 + 1
        start_quarter = today_start.replace(month=quarter_month, day=1)
        return start_quarter, now
    elif filter_key == 'this_year':
        return today_start.replace(month=1, day=1), now
    elif filter_key == 'custom' and start_str and end_str:
        try:
            start_dt = datetime.strptime(start_str, '%Y-%m-%d').replace(tzinfo=timezone.get_current_timezone())
            end_dt = datetime.strptime(end_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, tzinfo=timezone.get_current_timezone())
            return start_dt, end_dt
        except Exception:
            pass

    # Default to all-time / last 1 year
    return today_start - timedelta(days=365), now


class BusinessIntelligenceDashboardView(APIView):
    """
    Computes all KPI cards, conversion funnels, demand breakdowns,
    and developer handover metrics for the selected date period.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if getattr(request.user, 'role', '') == 'PARTICIPANT' and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'Participants do not have access to internal Business Intelligence.'}, status=status.HTTP_403_FORBIDDEN)
        filter_key = request.query_params.get('period', 'last_30_days')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        start_dt, end_dt = get_date_range(filter_key, start_date_str, end_date_str)

        # 1. Enquiry Analytics
        enquiries_qs = Enquiry.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        total_enquiries = enquiries_qs.count()

        status_counts = dict(enquiries_qs.values_list('status').annotate(c=Count('id')))

        new_count = status_counts.get(EnquiryStatus.NEW, 0)
        under_review = status_counts.get(EnquiryStatus.UNDER_REVIEW, 0)
        qualified_count = status_counts.get(EnquiryStatus.QUALIFIED, 0) + status_counts.get(EnquiryStatus.REQUIREMENTS_PENDING, 0) + status_counts.get(EnquiryStatus.REQUIREMENTS_COMPLETED, 0) + status_counts.get(EnquiryStatus.READY_FOR_HANDOVER, 0) + status_counts.get(EnquiryStatus.PROJECT_CREATED, 0)
        req_completed = status_counts.get(EnquiryStatus.REQUIREMENTS_COMPLETED, 0) + status_counts.get(EnquiryStatus.READY_FOR_HANDOVER, 0) + status_counts.get(EnquiryStatus.PROJECT_CREATED, 0)
        handed_over = status_counts.get(EnquiryStatus.READY_FOR_HANDOVER, 0) + status_counts.get(EnquiryStatus.PROJECT_CREATED, 0)
        rejected_count = status_counts.get(EnquiryStatus.REJECTED, 0)
        closed_count = status_counts.get(EnquiryStatus.CLOSED, 0)

        rejection_rate = round((rejected_count / total_enquiries * 100), 1) if total_enquiries > 0 else 0.0

        # Source breakdown
        sources = list(enquiries_qs.values('source').annotate(count=Count('id')).order_by('-count'))
        # Service demand
        services = list(enquiries_qs.values('service_type').annotate(count=Count('id')).order_by('-count'))

        # 2. Conversion Funnel
        conv_enquiry_to_qualified = round((qualified_count / total_enquiries * 100), 1) if total_enquiries > 0 else 0.0
        conv_qualified_to_req = round((req_completed / qualified_count * 100), 1) if qualified_count > 0 else 0.0
        conv_req_to_handover = round((handed_over / req_completed * 100), 1) if req_completed > 0 else 0.0
        conv_total_pipeline = round((handed_over / total_enquiries * 100), 1) if total_enquiries > 0 else 0.0

        # Pipeline value
        pipeline_val = enquiries_qs.filter(qualification__isnull=False).aggregate(total=Sum('qualification__estimated_project_value'))['total'] or 0.0

        # Rejection Reasons breakdown
        rejections_qs = EnquiryRejection.objects.filter(rejected_at__gte=start_dt, rejected_at__lte=end_dt)
        rejection_reasons = list(rejections_qs.values('category').annotate(count=Count('id')).order_by('-count'))

        # 3. Developer Handover & Projects
        handovers_qs = HandoverRecord.objects.filter(generated_at__gte=start_dt, generated_at__lte=end_dt)
        total_handovers = handovers_qs.count()

        projects_qs = DeveloperProject.objects.all()
        active_projects = projects_qs.filter(status__in=[ProjectStatus.IN_PROGRESS, ProjectStatus.ASSIGNED, ProjectStatus.INTERNAL_REVIEW]).count()
        blocked_projects = projects_qs.filter(status=ProjectStatus.BLOCKED).count()
        overdue_projects = projects_qs.filter(expected_completion_date__lt=timezone.now().date(), status__in=[ProjectStatus.IN_PROGRESS, ProjectStatus.BLOCKED, ProjectStatus.ASSIGNED]).count()
        completed_projects = projects_qs.filter(status__in=[ProjectStatus.COMPLETED, ProjectStatus.DELIVERED, ProjectStatus.CLOSED]).count()

        # 4. Financial Analytics
        fin_docs = InvoiceQuote.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        quoted_val = fin_docs.aggregate(s=Sum('amount_quoted'))['s'] or 0.0
        approved_val = fin_docs.aggregate(s=Sum('amount_approved'))['s'] or 0.0
        invoiced_val = fin_docs.aggregate(s=Sum('amount_invoiced'))['s'] or 0.0
        received_val = fin_docs.aggregate(s=Sum('amount_received'))['s'] or 0.0
        pending_val = fin_docs.aggregate(s=Sum('amount_pending'))['s'] or 0.0
        refunded_val = fin_docs.aggregate(s=Sum('amount_refunded'))['s'] or 0.0

        expenses_val = ExpenseRecord.objects.filter(date__gte=start_dt.date(), date__lte=end_dt.date()).aggregate(s=Sum('amount'))['s'] or 0.0
        net_profit = float(received_val) - float(expenses_val)

        # 5. Marketing & Registrations
        event_regs = EventRegistration.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt).count()
        college_apps = SkillBridgeCollegeEnquiry.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt).count()
        pro_apps = SkillBridgeProfessionalApplication.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt).count()

        return Response({
            'period': {
                'key': filter_key,
                'start': start_dt.isoformat(),
                'end': end_dt.isoformat()
            },
            'kpis': {
                'total_enquiries': total_enquiries,
                'new_enquiries': new_count,
                'under_review': under_review,
                'qualified_enquiries': qualified_count,
                'requirements_completed': req_completed,
                'projects_handed_over': handed_over,
                'rejected_enquiries': rejected_count,
                'rejection_rate': rejection_rate,
                'pipeline_value': float(pipeline_val),
                'active_projects': active_projects,
                'blocked_projects': blocked_projects,
                'overdue_projects': overdue_projects,
                'completed_projects': completed_projects,
                'handovers_generated': total_handovers,
                'amount_invoiced': float(invoiced_val),
                'amount_received': float(received_val),
                'amount_pending': float(pending_val),
                'expenses': float(expenses_val),
                'net_profit': net_profit,
                'event_registrations': event_regs,
                'skillbridge_college_requests': college_apps,
                'skillbridge_professional_applications': pro_apps
            },
            'conversion_funnel': {
                'enquiry_to_qualified_pct': conv_enquiry_to_qualified,
                'qualified_to_requirements_pct': conv_qualified_to_req,
                'requirements_to_handover_pct': conv_req_to_handover,
                'overall_conversion_pct': conv_total_pipeline
            },
            'sources': sources,
            'services': services,
            'rejection_reasons': rejection_reasons
        })


class RuleBasedInsightsView(APIView):
    """
    Computes actionable, deterministic rule-based insights directly from stored records.
    Explicitly labeled as Rule-Based Business Intelligence (no fabricated AI claims).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        insights = []
        now = timezone.now()

        # Rule 1: Qualified enquiries awaiting requirements completion
        qual_awaiting_req = ProjectRequirement.objects.filter(
            status__in=[RequirementStatus.DRAFT, RequirementStatus.IN_PROGRESS]
        ).count()
        if qual_awaiting_req > 0:
            insights.append({
                'id': 'qual_awaiting_req',
                'severity': 'warning' if qual_awaiting_req > 2 else 'info',
                'title': 'Qualified Enquiries Awaiting Requirements',
                'message': f"{qual_awaiting_req} qualified project{'s are' if qual_awaiting_req > 1 else ' is'} awaiting requirements completion before handover can be prepared.",
                'action_label': 'Open Requirements Workspace',
                'action_link': '/dashboard/#requirements'
            })

        # Rule 2: Projects ready for handover with no developer assigned
        ready_no_dev = HandoverRecord.objects.filter(assigned_developer__isnull=True).count()
        if ready_no_dev > 0:
            insights.append({
                'id': 'ready_no_dev',
                'severity': 'warning',
                'title': 'Handover Packages Ready for Assignment',
                'message': f"{ready_no_dev} developer handover package{'s have' if ready_no_dev > 1 else ' has'} been generated but currently have no developer assigned.",
                'action_label': 'Assign Developers',
                'action_link': '/dashboard/#handover'
            })

        # Rule 3: Overdue projects based on recorded delivery dates
        overdue_prjs = DeveloperProject.objects.filter(
            expected_completion_date__lt=now.date(),
            status__in=[ProjectStatus.IN_PROGRESS, ProjectStatus.ASSIGNED, ProjectStatus.BLOCKED]
        ).count()
        if overdue_prjs > 0:
            insights.append({
                'id': 'overdue_prjs',
                'severity': 'danger',
                'title': 'Overdue Development Projects',
                'message': f"{overdue_prjs} active project{'s are' if overdue_prjs > 1 else ' is'} past their scheduled delivery date.",
                'action_label': 'Review Overdue Projects',
                'action_link': '/dashboard/#projects'
            })

        # Rule 4: Overdue Follow-ups
        overdue_followups = Enquiry.objects.filter(
            follow_up_date__lt=now,
            status__in=[EnquiryStatus.NEW, EnquiryStatus.UNDER_REVIEW, EnquiryStatus.CONTACTED, EnquiryStatus.FOLLOWUP_REQUIRED]
        ).count()
        if overdue_followups > 0:
            insights.append({
                'id': 'overdue_followups',
                'severity': 'warning',
                'title': 'Follow-ups Overdue',
                'message': f"Follow-up is overdue for {overdue_followups} client enquir{'ies' if overdue_followups > 1 else 'y'}.",
                'action_label': 'View Follow-ups',
                'action_link': '/dashboard/#enquiries'
            })

        # Rule 5: Most common rejection reason in the last 30 days
        last_30_rejections = EnquiryRejection.objects.filter(rejected_at__gte=now - timedelta(days=30))
        top_reason = last_30_rejections.values('category').annotate(c=Count('id')).order_by('-c').first()
        if top_reason:
            cat_display = dict(RejectionCategory.choices).get(top_reason['category'], top_reason['category'])
            insights.append({
                'id': 'top_rejection_reason',
                'severity': 'info',
                'title': 'Primary Rejection Category',
                'message': f"'{cat_display}' is the most recorded rejection reason this month ({top_reason['c']} occurrences).",
                'action_label': 'View Rejection Analytics',
                'action_link': '/dashboard/#analytics'
            })

        # Fallback if no specific warnings triggered
        if not insights:
            insights.append({
                'id': 'system_healthy',
                'severity': 'success',
                'title': 'All Business Pipelines Operating Smoothly',
                'message': 'No overdue follow-ups, blocked development projects, or unassigned packages detected in current records.',
                'action_label': 'View Analytics',
                'action_link': '/dashboard/#analytics'
            })

        return Response({
            'source': 'Deterministic Rule-Based Intelligence Engine',
            'calculated_at': now.isoformat(),
            'total_insights': len(insights),
            'insights': insights
        })


class ExportCSVView(APIView):
    """
    Generates real downloadable CSV reports for authorized staff.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_type=None):
        if not report_type:
            report_type = request.GET.get('type') or request.GET.get('report_type')
        timestamp_str = timezone.now().strftime('%Y%m%d_%H%M%S')
        response = HttpResponse(content_type='text/csv')

        if report_type == 'enquiries':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Enquiries_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Reference ID', 'Client Name', 'Contact Person', 'Email', 'Phone', 'Service Type', 'Status', 'Source', 'Submitted Date'])
            for enq in Enquiry.objects.all().order_by('-created_at'):
                writer.writerow([enq.reference_id, enq.client_name, enq.contact_person, enq.email, enq.phone, enq.service_type, enq.get_status_display(), enq.source, enq.created_at.strftime('%Y-%m-%d %H:%M')])

        elif report_type == 'rejections':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Rejections_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Enquiry Ref', 'Client Name', 'Category', 'Reason Detail', 'Internal Notes', 'Rejected By', 'Rejected Date', 'Reopened'])
            for rej in EnquiryRejection.objects.select_related('enquiry', 'rejected_by').all().order_by('-rejected_at'):
                writer.writerow([rej.enquiry.reference_id, rej.enquiry.client_name, rej.get_category_display(), rej.reason_detail, rej.internal_notes, rej.rejected_by.username, rej.rejected_at.strftime('%Y-%m-%d %H:%M'), 'Yes' if rej.reopened else 'No'])

        elif report_type == 'projects':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Projects_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Project Code', 'Project Title', 'Client Name', 'Developer', 'Status', 'Progress %', 'Priority', 'Expected Delivery Date'])
            for p in DeveloperProject.objects.select_related('requirement', 'assigned_developer').all():
                dev_name = p.assigned_developer.get_full_name() if p.assigned_developer else 'Unassigned'
                writer.writerow([p.project_code, p.title, p.requirement.legal_business_name, dev_name, p.get_status_display(), f"{p.progress_percentage}%", p.priority, str(p.expected_completion_date or 'N/A')])

        elif report_type == 'financials':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Financials_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Reference No', 'Type', 'Quoted', 'Approved', 'Invoiced', 'Received', 'Pending', 'Status', 'Created Date'])
            for doc in InvoiceQuote.objects.all():
                writer.writerow([doc.reference_no, doc.get_doc_type_display(), doc.amount_quoted, doc.amount_approved, doc.amount_invoiced, doc.amount_received, doc.amount_pending, doc.get_status_display(), doc.created_at.strftime('%Y-%m-%d')])

        elif report_type == 'handovers':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Handovers_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Handover Ref', 'Requirement', 'Version', 'Zip Filename', 'Size Bytes', 'SHA256 Checksum', 'Assigned Developer', 'Checks Passed', 'Generated Date'])
            for h in HandoverRecord.objects.select_related('requirement', 'assigned_developer').all().order_by('-generated_at'):
                dev = h.assigned_developer.username if h.assigned_developer else 'Unassigned'
                writer.writerow([h.handover_reference, h.requirement.requirement_reference, h.version, h.zip_filename, h.zip_size, h.zip_checksum_sha256, dev, 'Yes' if h.all_checks_passed else 'No', h.generated_at.strftime('%Y-%m-%d %H:%M')])

        elif report_type == 'events':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Events_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Title', 'Category', 'Date', 'Mode', 'Venue', 'Fee', 'Fee Amount', 'Capacity', 'Confirmed Registrations', 'Status', 'Published'])
            for ev in EventListing.objects.all().order_by('-created_at'):
                writer.writerow([ev.title, ev.event_type, str(ev.event_date or 'TBA'), ev.mode, ev.venue, ev.fee, ev.fee_amount, ev.max_participants or 'Open', ev.confirmed_count, ev.status, 'Yes' if ev.is_published else 'No'])

        elif report_type == 'registrations':
            response['Content-Disposition'] = f'attachment; filename="XEYR_Registrations_{timestamp_str}.csv"'
            writer = csv.writer(response)
            writer.writerow(['Registration Ref', 'Event Title', 'Attendee Name', 'Email', 'Phone', 'College / Company', 'Status', 'Payment Status', 'Fee Paid', 'Date Registered'])
            for reg in EventRegistration.objects.all().order_by('-created_at'):
                writer.writerow([reg.registration_reference, reg.event_name, reg.full_name, reg.email, reg.phone, reg.company_or_college, reg.registration_status, reg.payment_status, reg.fee_paid, reg.created_at.strftime('%Y-%m-%d %H:%M')])

        else:
            return Response({'error': 'Invalid report type.'}, status=status.HTTP_400_BAD_REQUEST)

        AuditLog.log('REPORT_EXPORTED_CSV', 'Report', 0, user=request.user, details={'report_type': report_type}, request=request)
        return response

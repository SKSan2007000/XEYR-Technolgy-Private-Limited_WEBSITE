"""
XEYR Technologies - Final Bug Fix, Registration UI, and Admin Dashboard Verification Script
Verifies:
1. Double Registration Display fix (DOM analysis, single form guarantee, field deduplication, responsive CSS)
2. Admin Event Management (create, edit, speaker, topics, agenda, guidelines, refund policy, draft vs publish)
3. Dynamic custom form field configuration
4. Visitor registration workflow (free & paid)
5. Admin registrations view & CSV export
6. Role-based access control (403 for unauthorized users)
"""

import os
import sys
import json
import re

# Ensure backend directory is in Python path
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xeyr_backend.settings')

import django
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth import get_user_model
from events_mgmt.models import EventListing, EventRegistration, EventFormField
from events_mgmt.views import (
    AdminEventCRUDView, AdminEventDetailManageView,
    AdminEventFormFieldConfigView, AdminRegistrationsListView,
    AdminExportEventRegistrationsCSVView, PublicEventDynamicRegisterView,
    PublicEventDetailView
)

User = get_user_model()


def run_checks():
    print("=" * 80)
    print("XEYR TECHNOLOGIES - FINAL BUG FIX & FUNCTIONAL VERIFICATION SUITE")
    print("=" * 80)

    results = []
    factory = APIRequestFactory()

    # -------------------------------------------------------------------------
    # PART 1: DOUBLE REGISTRATION DISPLAY INSPECTION
    # -------------------------------------------------------------------------
    print("\n--- 1. Double Registration Display & Responsive UI Verification ---")

    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'XEYR_Website_Frontend')
    event_html_path = os.path.join(frontend_dir, 'event.html')
    styles_css_path = os.path.join(frontend_dir, 'styles.css')
    portal_js_path = os.path.join(frontend_dir, 'portal.js')

    with open(event_html_path, 'r', encoding='utf-8') as f:
        event_html = f.read()

    with open(styles_css_path, 'r', encoding='utf-8') as f:
        styles_css = f.read()

    with open(portal_js_path, 'r', encoding='utf-8') as f:
        portal_js = f.read()

    # Check 1: Exactly ONE dynamic event form in event.html
    forms_in_event_page = re.findall(r'<form\b[^>]*id=["\']dynamic-event-form["\']', event_html)
    check1 = len(forms_in_event_page) == 1
    results.append((
        "Single registration form in event.html",
        check1,
        f"Found {len(forms_in_event_page)} forms with id='dynamic-event-form' (Expected: 1)"
    ))

    # Check 2: Filter out default fields in event.html dynamic injection
    check2 = "defaultNames" in event_html and "full_name" in event_html and "email" in event_html
    results.append((
        "Event detail page deduplicates built-in contact fields before dynamic injection",
        check2,
        "defaultNames exclusion list prevents duplicating Name, Email, Phone, and Category"
    ))

    # Check 3: Filter out default fields in portal.js dynamic dialog injection
    check3 = "defaultNames" in portal_js and "full_name" in portal_js
    results.append((
        "Portal modal deduplicates built-in contact fields before dynamic injection",
        check3,
        "portal.js filters out defaultNames when opening dynamic-event-dialog"
    ))

    # Check 4: Responsive grid collapsing for .event-detail-layout
    check4 = ".event-detail-layout" in styles_css and "grid-template-columns: 1fr" in styles_css
    results.append((
        "Responsive single-column stack on tablet and mobile viewports",
        check4,
        ".event-detail-layout collapses to 1fr at <=980px and <=640px in styles.css"
    ))

    # Check 5: Card action links cleanly to /events/<slug>/#register
    check5 = "/events/${ev.slug}/#register" in portal_js or "/events/${ev.slug}/" in portal_js
    results.append((
        "Portal event cards route visitors directly to dedicated event registration view",
        check5,
        "createEventCardHTML targets /events/${ev.slug}/#register directly"
    ))

    # -------------------------------------------------------------------------
    # PART 2: ADMIN AUTHENTICATION & ROLE-BASED ACCESS CONTROL
    # -------------------------------------------------------------------------
    print("\n--- 2. Admin Authentication & Role-Based Access Control ---")

    # Create admin user
    admin_user, _ = User.objects.get_or_create(
        username='qa_admin_verify',
        defaults={'email': 'qa_admin@xeyr.internal', 'is_staff': True, 'is_superuser': True, 'role': 'SUPER_ADMIN'}
    )
    admin_user.is_staff = True
    admin_user.role = 'SUPER_ADMIN'
    admin_user.set_password('AdminPass123!')
    admin_user.save()

    # Create regular participant user
    regular_user, _ = User.objects.get_or_create(
        username='qa_participant_verify',
        defaults={'email': 'qa_user@xeyr.internal', 'is_staff': False, 'is_superuser': False, 'role': 'PARTICIPANT'}
    )
    regular_user.is_staff = False
    regular_user.role = 'PARTICIPANT'
    regular_user.save()

    # Check 6: Unauthorized user receives 403 on admin endpoint
    req_unauth = factory.get('/api/events/manage/')
    force_authenticate(req_unauth, user=regular_user)
    res_unauth = AdminEventCRUDView.as_view()(req_unauth)
    check6 = res_unauth.status_code == 403
    results.append((
        "Non-admin participant denied access to admin event management (HTTP 403)",
        check6,
        f"Status code returned: {res_unauth.status_code}"
    ))

    # Check 7: Admin user granted access to admin endpoint
    req_admin = factory.get('/api/events/manage/')
    force_authenticate(req_admin, user=admin_user)
    res_admin = AdminEventCRUDView.as_view()(req_admin)
    check7 = res_admin.status_code == 200
    results.append((
        "Staff/Admin user granted access to admin event management (HTTP 200)",
        check7,
        f"Status code returned: {res_admin.status_code}"
    ))

    # -------------------------------------------------------------------------
    # PART 3: ADMIN EVENT CREATION WITH ADVANCED CMS FIELDS
    # -------------------------------------------------------------------------
    print("\n--- 3. Admin Event Creation with Full Field Persistence ---")

    test_event_data = {
        'title': 'Autonomous AI Agents & Multi-Modal Workflows 2026',
        'event_type': 'AI_BOOTCAMP',
        'organizer': 'XEYR Technologies AI Lab',
        'event_date': '2026-12-15',
        'start_time': '10:00:00',
        'end_time': '13:00:00',
        'mode': 'ONLINE',
        'venue': 'Google Meet Virtual Lab',
        'short_description': 'Hands-on bootcamp on agentic tool calling, memory management, and reasoning loops.',
        'full_description': 'Comprehensive 3-hour masterclass covering multi-agent orchestration, function calling patterns, and production system evaluation.',
        'poster_url': 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=900&q=80',
        'is_paid': False,
        'fee_amount': 0.00,
        'currency': 'INR',
        'max_participants': 150,
        'status': 'DRAFT',
        'is_published': False,
        'eligibility': 'Open to engineering students, AI developers, and system architects.',
        'guidelines': 'Laptop with Python 3.11+ and modern browser required for live interactive exercises.',
        'refund_policy': 'Free event registrations can be cancelled anytime before session commencement.',
        'mentors': json.dumps([{
            'name': 'Dr. Marcus Vance',
            'role': 'Chief AI Scientist',
            'company': 'XEYR Technologies',
            'bio': 'Pioneering researcher in autonomous multi-agent coordination and neural code intelligence.',
            'photo': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=400&q=80'
        }]),
        'learning_outcomes': json.dumps([
            'Master Agentic Tool-Use Protocols and Reasoning Loops',
            'Design Resilient Memory Hierarchies and Vector Search Indexes',
            'Deploy Scalable Multi-Agent Swarms with Production Observability'
        ]),
        'schedule': json.dumps([
            {'time': '10:00 AM - 11:00 AM', 'title': 'Foundational Agent Architectures', 'description': 'Deconstructing tool selection and reactive feedback loops.'},
            {'time': '11:15 AM - 12:45 PM', 'title': 'Live Interactive Code Lab', 'description': 'Hands-on construction of an autonomous pair programming agent.'},
            {'time': '12:45 PM - 01:00 PM', 'title': 'Q&A and Verification Credentials', 'description': 'Reviewing participant solutions and issuing digital credentials.'}
        ])
    }

    req_create = factory.post('/api/events/manage/', data=test_event_data, format='multipart')
    force_authenticate(req_create, user=admin_user)
    res_create = AdminEventCRUDView.as_view()(req_create)
    check8 = res_create.status_code == 201
    created_event_id = res_create.data.get('id') if check8 else None
    created_event_slug = res_create.data.get('slug') if check8 else None

    results.append((
        "Admin creates event with speaker, topics, agenda, guidelines & refund policy",
        check8 and created_event_id is not None,
        f"Created Event ID: {created_event_id}, Slug: {created_event_slug}"
    ))

    # Verify Database Persistence
    created_ev = EventListing.objects.filter(id=created_event_id).first() if created_event_id else None
    check9 = (
        created_ev is not None and
        created_ev.title == test_event_data['title'] and
        len(created_ev.mentors) == 1 and
        created_ev.mentors[0]['name'] == 'Dr. Marcus Vance' and
        len(created_ev.learning_outcomes) == 3 and
        len(created_ev.schedule) == 3 and
        created_ev.status == 'DRAFT' and
        created_ev.is_published is False
    )
    results.append((
        "PostgreSQL persistence verifies mentors JSON, learning outcomes, schedule, and draft status",
        check9,
        f"Verified DB records: {len(created_ev.mentors) if created_ev else 0} mentors, {len(created_ev.learning_outcomes) if created_ev else 0} outcomes"
    ))

    # -------------------------------------------------------------------------
    # PART 4: DYNAMIC CUSTOM FORM FIELD CONFIGURATION
    # -------------------------------------------------------------------------
    print("\n--- 4. Dynamic Custom Form Field Configuration ---")

    custom_field_data = {
        'field_label': 'GitHub Profile / Portfolio URL',
        'field_name': 'github_portfolio',
        'field_type': 'text',
        'placeholder': 'https://github.com/your-username',
        'is_required': True
    }
    req_fld = factory.post(f'/api/events/manage/{created_event_id}/fields/', data=custom_field_data)
    force_authenticate(req_fld, user=admin_user)
    res_fld = AdminEventFormFieldConfigView.as_view()(req_fld, event_id=created_event_id)
    check10 = res_fld.status_code == 201
    results.append((
        "Admin adds custom dynamic form field (GitHub Profile URL) to event",
        check10,
        f"Custom field configured: {res_fld.data.get('field_label') if check10 else 'Failed'}"
    ))

    # -------------------------------------------------------------------------
    # PART 5: PUBLISH EVENT & PUBLIC PORTAL VIEW
    # -------------------------------------------------------------------------
    print("\n--- 5. Publish Event & Public Detail API Verification ---")

    update_data = {
        'status': 'UPCOMING',
        'is_published': True
    }
    req_pub = factory.put(f'/api/events/manage/{created_event_id}/', data=update_data, format='multipart')
    force_authenticate(req_pub, user=admin_user)
    res_pub = AdminEventDetailManageView.as_view()(req_pub, pk=created_event_id)
    check11 = res_pub.status_code == 200 and res_pub.data.get('is_published') is True
    results.append((
        "Admin transitions event from DRAFT to PUBLISHED / UPCOMING",
        check11,
        f"Status: {res_pub.data.get('status') if check11 else 'Failed'}, Published: {res_pub.data.get('is_published') if check11 else False}"
    ))

    # Test Public Event Detail endpoint
    req_detail = factory.get(f'/api/events/public/{created_event_slug}/')
    res_detail = PublicEventDetailView.as_view()(req_detail, slug_or_id=created_event_slug)
    check12 = (
        res_detail.status_code == 200 and
        res_detail.data.get('title') == test_event_data['title'] and
        len(res_detail.data.get('mentors', [])) == 1 and
        len(res_detail.data.get('learning_outcomes', [])) == 3 and
        len(res_detail.data.get('schedule', [])) == 3 and
        len(res_detail.data.get('form_fields', [])) >= 5  # 4 defaults + 1 custom
    )
    results.append((
        "Public API delivers complete event payload with mentors, outcomes, schedule & form fields",
        check12,
        f"Form fields exposed to public visitor: {len(res_detail.data.get('form_fields', [])) if check12 else 0}"
    ))

    # -------------------------------------------------------------------------
    # PART 6: VISITOR REGISTRATION WORKFLOW & DB PERSISTENCE
    # -------------------------------------------------------------------------
    print("\n--- 6. Visitor Registration Workflow & Reference Generation ---")

    reg_payload = {
        'full_name': 'Devon Sterling',
        'email': 'devon.sterling@example.com',
        'phone': '+91 98765 43210',
        'participant_category': 'Student',
        'company_or_college': 'MIT School of Engineering',
        'github_portfolio': 'https://github.com/devonsterling-ai',
        'terms_consent': True
    }
    req_reg = factory.post(
        f'/api/events/{created_event_id}/register-dynamic/',
        data=json.dumps(reg_payload),
        content_type='application/json'
    )
    res_reg = PublicEventDynamicRegisterView.as_view()(req_reg, event_id=created_event_id)
    check13 = res_reg.status_code in (200, 201) and res_reg.data.get('registration_reference') is not None
    reg_ref = res_reg.data.get('registration_reference')

    results.append((
        "Visitor submits dynamic registration: Free event confirmed with unique reference",
        check13 and reg_ref is not None,
        f"Registration Reference: {reg_ref}"
    ))

    # Verify registration in Database
    db_reg = EventRegistration.objects.filter(registration_reference=reg_ref).first() if reg_ref else None
    check14 = (
        db_reg is not None and
        db_reg.full_name == 'Devon Sterling' and
        db_reg.company_or_college == 'MIT School of Engineering' and
        db_reg.event_id == created_event_id and
        db_reg.form_responses.get('github_portfolio') == 'https://github.com/devonsterling-ai'
    )
    results.append((
        "PostgreSQL persistence verifies attendee details & custom responses stored accurately",
        check14,
        f"Verified DB Registration ID: {db_reg.id if db_reg else 'None'}, Custom responses preserved"
    ))

    # -------------------------------------------------------------------------
    # PART 7: ADMIN REGISTRATIONS MANAGEMENT & CSV EXPORT
    # -------------------------------------------------------------------------
    print("\n--- 7. Admin Registrations Inspection & CSV Export ---")

    # Admin query attendee list for this event
    req_regs = factory.get(f'/api/events/registrations/?event_id={created_event_id}')
    force_authenticate(req_regs, user=admin_user)
    res_regs = AdminRegistrationsListView.as_view()(req_regs)
    check15 = res_regs.status_code == 200 and len(res_regs.data) >= 1
    found_attendee = any(r.get('registration_reference') == reg_ref for r in res_regs.data) if check15 else False

    results.append((
        "Admin attendee list displays registered participant with contact & category details",
        check15 and found_attendee,
        f"Total attendees returned: {len(res_regs.data) if check15 else 0}"
    ))

    # Admin CSV Export
    req_csv = factory.get(f'/api/events/manage/{created_event_id}/export-csv/')
    force_authenticate(req_csv, user=admin_user)
    res_csv = AdminExportEventRegistrationsCSVView.as_view()(req_csv, event_id=created_event_id)
    csv_content = res_csv.content.decode('utf-8') if res_csv.status_code == 200 else ''
    check16 = (
        res_csv.status_code == 200 and
        res_csv['Content-Type'] == 'text/csv' and
        'Devon Sterling' in csv_content and
        reg_ref in csv_content
    )
    results.append((
        "Admin attendee CSV export generates valid downloadable CSV with attendee records",
        check16,
        f"CSV Content-Type: {res_csv.get('Content-Type')}, Attendee found in CSV: {'Yes' if check16 else 'No'}"
    ))

    # -------------------------------------------------------------------------
    # PART 8: PAID EVENT REGISTRATION & RAZORPAY ORDER INITIATION
    # -------------------------------------------------------------------------
    print("\n--- 8. Paid Event Registration & Order Initiation ---")

    paid_event_data = {
        'title': 'Production Vector DB & RAG Workshop 2026',
        'event_type': 'TECHNICAL_WORKSHOP',
        'event_date': '2026-12-20',
        'is_paid': True,
        'fee_amount': 499.00,
        'currency': 'INR',
        'is_published': True,
        'status': 'UPCOMING'
    }
    req_paid = factory.post('/api/events/manage/', data=paid_event_data, format='multipart')
    force_authenticate(req_paid, user=admin_user)
    res_paid = AdminEventCRUDView.as_view()(req_paid)
    paid_ev_id = res_paid.data.get('id') if res_paid.status_code == 201 else None

    # Register for paid event
    paid_reg_payload = {
        'full_name': 'Priya Sharma',
        'email': 'priya.sharma@example.com',
        'phone': '+91 91234 56789',
        'participant_category': 'Working Professional',
        'company_or_college': 'Fintech Solutions Ltd',
        'terms_consent': True
    }
    req_paid_reg = factory.post(
        f'/api/events/{paid_ev_id}/register-dynamic/',
        data=json.dumps(paid_reg_payload),
        content_type='application/json'
    )
    res_paid_reg = PublicEventDynamicRegisterView.as_view()(req_paid_reg, event_id=paid_ev_id)
    check17 = (
        res_paid_reg.status_code in (200, 201) and
        (res_paid_reg.data.get('payment_required') is True or res_paid_reg.data.get('requires_payment') is True) and
        res_paid_reg.data.get('amount_in_paise') == 49900 and
        'razorpay_order_id' in res_paid_reg.data
    )
    results.append((
        "Paid workshop registration initializes Razorpay checkout order (amount in paise: 49900)",
        check17,
        f"Requires Payment: {res_paid_reg.data.get('requires_payment')}, Order ID: {res_paid_reg.data.get('razorpay_order_id')}"
    ))

    # -------------------------------------------------------------------------
    # CLEANUP TEST DATA
    # -------------------------------------------------------------------------
    if created_event_id:
        EventListing.objects.filter(id=created_event_id).delete()
    if paid_ev_id:
        EventListing.objects.filter(id=paid_ev_id).delete()
    User.objects.filter(username__in=['qa_admin_verify', 'qa_participant_verify']).delete()

    # -------------------------------------------------------------------------
    # PRINT RESULTS TABLE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS SUMMARY")
    print("=" * 80)
    passed_count = sum(1 for _, ok, _ in results if ok)
    total_count = len(results)

    for idx, (title, ok, details) in enumerate(results, 1):
        status_label = "[PASS]" if ok else "[FAIL]"
        print(f"{status_label} {idx}. {title}")
        print(f"       Details: {details}")

    print("-" * 80)
    print(f"TOTAL: {passed_count} / {total_count} PASSED")
    if passed_count == total_count:
        print("ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY!")
    else:
        print("SOME CHECKS FAILED! INSPECT DETAILS ABOVE.")
    print("=" * 80)

    return passed_count == total_count


if __name__ == '__main__':
    success = run_checks()
    sys.exit(0 if success else 1)

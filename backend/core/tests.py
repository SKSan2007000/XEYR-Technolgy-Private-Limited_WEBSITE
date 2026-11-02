import os
import json
import zipfile
from io import BytesIO
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from core.models import User, UserRole, AuditLog, Notification
from crm.models import Enquiry, EnquiryStatus, EnquiryQualification, EnquiryRejection, RejectionCategory
from requirements.models import ProjectRequirement, RequirementStatus
from assets_mgmt.models import ClientBrandAsset, AssetCategory, AssetStatus
from handover.models import HandoverRecord
from handover.generator import HandoverZipGenerator
from projects.models import DeveloperProject, ProjectStatus
from finance.models import InvoiceQuote, PaymentRecord, ExpenseRecord
import hmac
import hashlib
import datetime
from django.conf import settings
from events_mgmt.models import (
    EventListing, EventFormField, EventRegistration,
    EventNotificationSubscriber, EventNotificationDelivery,
    EventPaymentOrder, SocialMediaConfig
)


class XeyrBusinessOSTestCase(TestCase):
    """
    Automated Test Suite for XEYR Technologies Business Operating System.
    Validates all 20 critical business workflows required by the specification.
    """

    def setUp(self):
        self.client = APIClient()

        # Users
        self.super_admin = User.objects.create_superuser(
            username='admin_test',
            email='admin@test.xeyr.in',
            password='Password@123',
            role=UserRole.SUPER_ADMIN
        )
        self.business_admin = User.objects.create_user(
            username='biz_admin',
            email='biz@test.xeyr.in',
            password='Password@123',
            role=UserRole.BUSINESS_ADMIN
        )
        self.developer = User.objects.create_user(
            username='dev_test',
            email='dev@test.xeyr.in',
            password='Password@123',
            role=UserRole.DEVELOPER
        )
        self.other_dev = User.objects.create_user(
            username='other_dev',
            email='other@test.xeyr.in',
            password='Password@123',
            role=UserRole.DEVELOPER
        )

        # Baseline Enquiry
        self.enquiry = Enquiry.objects.create(
            client_name='Test Client Corporation',
            contact_person='Sundar Pitchai',
            email='sundar@testcorp.com',
            phone='+91 98840 99887',
            service_type='SolveX - AI & Automation',
            project_title='Automated Lead Ingestion Engine',
            project_description='Need enterprise lead routing with CRM synchronization.',
            source='Website (solvex-enquiry)',
            status=EnquiryStatus.NEW
        )

    # 1. Public enquiry submission
    def test_01_public_enquiry_submission(self):
        payload = {
            'name': 'Priya Ramesh',
            'email': 'priya@acme.org',
            'phone': '+91 98401 22334',
            'organisation': 'Acme Global Healthcare',
            'form_type': 'solvex-enquiry',
            'project_description': 'Emergency workflow coordination platform.'
        }
        res = self.client.post('/api/enquiries/submit/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data.get('success'))
        self.assertIn('reference_id', res.data)
        self.assertTrue(res.data['reference_id'].startswith('XEYR-ENQ-'))

    # 2. Enquiry persistence in PostgreSQL
    def test_02_enquiry_persistence_in_db(self):
        enq = Enquiry.objects.get(id=self.enquiry.id)
        self.assertEqual(enq.client_name, 'Test Client Corporation')
        self.assertEqual(enq.email, 'sundar@testcorp.com')
        self.assertEqual(enq.status, EnquiryStatus.NEW)
        self.assertTrue(enq.reference_id.startswith('XEYR-ENQ-'))

    # 3. Qualification by an authorised administrator
    def test_03_qualification_by_authorised_admin(self):
        self.client.force_authenticate(user=self.business_admin)
        payload = {
            'decision': 'High Fit for SolveX Automation',
            'estimated_project_value': 650000.00,
            'business_opportunity': 'Automate lead scoring and routing',
            'client_needs': 'CRM sync and SMS OTPs',
            'budget_confirmed': True,
            'timeline_confirmed': True,
            'technical_feasibility': 'High feasibility on Django and PostgreSQL'
        }
        res = self.client.post(f'/api/enquiries/{self.enquiry.id}/qualify/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.status, EnquiryStatus.QUALIFIED)
        self.assertTrue(hasattr(self.enquiry, 'qualification'))
        self.assertEqual(self.enquiry.qualification.estimated_project_value, 650000.00)
        self.assertTrue(ProjectRequirement.objects.filter(enquiry=self.enquiry).exists())

    # 4. Requirements creation and editing
    def test_04_requirements_creation_and_editing(self):
        self.client.force_authenticate(user=self.business_admin)
        req = ProjectRequirement.objects.create(
            enquiry=self.enquiry,
            project_name='Lead Ingestion Engine V1',
            created_by=self.business_admin
        )
        update_payload = {
            'project_name': 'Lead Ingestion Engine Enterprise Suite',
            'scope_of_work': 'Complete backend, API suite and web dispatcher console.',
            'approved_budget': 650000.00,
            'preferred_framework': 'Python Django + DRF',
            'database_requirements': 'PostgreSQL 17'
        }
        res = self.client.patch(f'/api/requirements/enquiry/{self.enquiry.id}/', update_payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        req.refresh_from_db()
        self.assertEqual(req.project_name, 'Lead Ingestion Engine Enterprise Suite')
        self.assertEqual(req.version, 2)
        self.assertEqual(req.approved_budget, 650000.00)

    # 5. Brand asset upload and access permissions
    def test_05_brand_asset_upload_and_access_permissions(self):
        self.client.force_authenticate(user=self.business_admin)
        req = ProjectRequirement.objects.create(
            enquiry=self.enquiry,
            project_name='Asset Test Project',
            created_by=self.business_admin
        )
        dummy_file = SimpleUploadedFile("brand_logo.png", b"PNG_FAKE_IMAGE_DATA", content_type="image/png")
        res = self.client.post(f'/api/assets/requirement/{req.id}/', {
            'file': dummy_file,
            'title': 'Official Client Vector Logo',
            'category': AssetCategory.PRIMARY_LOGO
        }, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        asset_id = res.data['id']

        asset = ClientBrandAsset.objects.get(id=asset_id)
        self.assertTrue(bool(asset.checksum_sha256))
        self.assertEqual(asset.file_size, len(b"PNG_FAKE_IMAGE_DATA"))

        # Test Permissions: Unauthorized developer cannot download unassigned project asset
        self.client.force_authenticate(user=self.other_dev)
        dl_res = self.client.get(f'/api/assets/{asset_id}/download/')
        self.assertEqual(dl_res.status_code, status.HTTP_403_FORBIDDEN)

        # Authorized admin can download
        self.client.force_authenticate(user=self.business_admin)
        dl_res_admin = self.client.get(f'/api/assets/{asset_id}/download/')
        self.assertEqual(dl_res_admin.status_code, status.HTTP_200_OK)

    # 6. Rejection without a reason being blocked
    def test_06_rejection_without_reason_blocked(self):
        self.client.force_authenticate(user=self.business_admin)
        # Attempt rejection without reason
        res1 = self.client.post(f'/api/enquiries/{self.enquiry.id}/reject/', {
            'category': RejectionCategory.BUDGET_MISMATCH,
            'reason_detail': ''
        })
        self.assertEqual(res1.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempt rejection without category
        res2 = self.client.post(f'/api/enquiries/{self.enquiry.id}/reject/', {
            'category': '',
            'reason_detail': 'Infeasible'
        })
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

        self.enquiry.refresh_from_db()
        self.assertNotEqual(self.enquiry.status, EnquiryStatus.REJECTED)

    # 7. Rejection with a valid reason being saved
    def test_07_rejection_with_valid_reason_saved(self):
        self.client.force_authenticate(user=self.business_admin)
        res = self.client.post(f'/api/enquiries/{self.enquiry.id}/reject/', {
            'category': RejectionCategory.BUDGET_MISMATCH,
            'reason_detail': 'Client proposed ₹20,000 budget for a full enterprise cloud portal, which is commercially infeasible.',
            'internal_notes': 'Offered standardized template, but client declined.'
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.status, EnquiryStatus.REJECTED)
        self.assertTrue(self.enquiry.rejections.filter(category=RejectionCategory.BUDGET_MISMATCH).exists())

    # 8. Reopening a rejected enquiry with an audit record
    def test_08_reopening_rejected_enquiry_with_audit(self):
        self.client.force_authenticate(user=self.business_admin)
        # First reject
        self.client.post(f'/api/enquiries/{self.enquiry.id}/reject/', {
            'category': RejectionCategory.CLIENT_UNRESPONSIVE,
            'reason_detail': 'Client did not respond to 3 follow-up emails.'
        })
        # Reopen without reason should fail
        res_fail = self.client.post(f'/api/enquiries/{self.enquiry.id}/reopen/', {'reopen_reason': ''})
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)

        # Reopen with reason
        res_ok = self.client.post(f'/api/enquiries/{self.enquiry.id}/reopen/', {'reopen_reason': 'Client phoned back, approved increased budget.'})
        self.assertEqual(res_ok.status_code, status.HTTP_200_OK)
        self.enquiry.refresh_from_db()
        self.assertEqual(self.enquiry.status, EnquiryStatus.UNDER_REVIEW)
        self.assertTrue(AuditLog.objects.filter(action='ENQUIRY_REOPENED', entity_id=str(self.enquiry.id)).exists())

    # 9. Requirements readiness validation
    def test_09_requirements_readiness_validation(self):
        req = ProjectRequirement.objects.create(
            enquiry=self.enquiry,
            project_name='Readiness Validation Project',
            created_by=self.super_admin
        )
        generator = HandoverZipGenerator(req, self.super_admin)
        checks, all_passed = generator.validate_readiness()
        # Fresh requirement without scope or budget will not pass all criteria
        self.assertFalse(all_passed)
        self.assertIn('scope_documented', checks)

    # 10, 11, 12. Handover ZIP generation, structure, and uploaded assets inclusion
    def test_10_11_12_handover_zip_generation_and_structure(self):
        self.client.force_authenticate(user=self.super_admin)
        req = ProjectRequirement.objects.create(
            enquiry=self.enquiry,
            project_name='Handover Test Engine',
            legal_business_name='Test Corp',
            scope_of_work='Build full automated backend.',
            approved_budget=500000.00,
            preferred_framework='Python Django',
            database_requirements='PostgreSQL 17',
            acceptance_criteria='Pass unit tests.',
            created_by=self.super_admin
        )
        # Add brand asset
        asset = ClientBrandAsset.objects.create(
            requirement=req,
            title='Primary Brand Logo',
            category=AssetCategory.PRIMARY_LOGO,
            filename='logo.svg',
            status=AssetStatus.APPROVED,
            uploaded_by=self.super_admin
        )

        generator = HandoverZipGenerator(req, self.super_admin)
        record = generator.generate(force_with_exception=True)
        self.assertTrue(os.path.exists(record.zip_file.path))

        with zipfile.ZipFile(record.zip_file.path, 'r') as zf:
            namelist = zf.namelist()
            prefix = f"XEYR_Project_Handover_{req.requirement_reference}/"

            # Check required structure
            self.assertIn(f"{prefix}README.md", namelist)
            self.assertIn(f"{prefix}PROJECT_SUMMARY.md", namelist)
            self.assertIn(f"{prefix}CLIENT_INFORMATION/client_profile.json", namelist)
            self.assertIn(f"{prefix}REQUIREMENTS/requirements_summary.pdf", namelist)
            self.assertIn(f"{prefix}REQUIREMENTS/requirements_summary.md", namelist)
            self.assertIn(f"{prefix}TECHNICAL_DOCUMENTATION/architecture_requirements.md", namelist)
            self.assertIn(f"{prefix}PROJECT_MANAGEMENT/task_checklist.csv", namelist)
            self.assertIn(f"{prefix}COMMERCIAL_SUMMARY/approved_commercial_summary.pdf", namelist)
            self.assertIn(f"{prefix}HANDOVER_METADATA/manifest.json", namelist)
            self.assertIn(f"{prefix}HANDOVER_METADATA/asset_inventory.csv", namelist)

            # Check manifest data
            manifest_str = zf.read(f"{prefix}HANDOVER_METADATA/manifest.json").decode('utf-8')
            manifest = json.loads(manifest_str)
            self.assertEqual(manifest['project_reference'], req.requirement_reference)
            self.assertTrue(len(manifest['files']) > 5)

    # 13. Prevention of cross-client data leakage
    def test_13_prevention_of_cross_client_data_leakage(self):
        # Create Project A
        enq_a = Enquiry.objects.create(client_name='Client A', email='a@a.com', phone='111', status=EnquiryStatus.QUALIFIED)
        req_a = ProjectRequirement.objects.create(enquiry=enq_a, project_name='Project A', scope_of_work='Scope A', approved_budget=100000, created_by=self.super_admin)
        ClientBrandAsset.objects.create(requirement=req_a, title='Logo A', category=AssetCategory.PRIMARY_LOGO, filename='logo_a.png', status=AssetStatus.APPROVED, uploaded_by=self.super_admin)

        # Create Project B
        enq_b = Enquiry.objects.create(client_name='Client B', email='b@b.com', phone='222', status=EnquiryStatus.QUALIFIED)
        req_b = ProjectRequirement.objects.create(enquiry=enq_b, project_name='Project B', scope_of_work='Scope B', approved_budget=200000, created_by=self.super_admin)
        ClientBrandAsset.objects.create(requirement=req_b, title='Secret Document B', category=AssetCategory.TECHNICAL_SPEC, filename='secret_spec_b.pdf', status=AssetStatus.APPROVED, uploaded_by=self.super_admin)

        # Generate Handover ZIP for Project A
        rec_a = HandoverZipGenerator(req_a, self.super_admin).generate(force_with_exception=True)

        with zipfile.ZipFile(rec_a.zip_file.path, 'r') as zf:
            zip_contents = " ".join(zf.namelist())
            self.assertNotIn("secret_spec_b", zip_contents)
            self.assertNotIn("Client B", zip_contents)

    # 14. Prevention of credentials entering handover ZIPs
    def test_14_prevention_of_credentials_entering_handover_zips(self):
        req = ProjectRequirement.objects.create(
            enquiry=self.enquiry,
            project_name='Security Audit Project',
            scope_of_work='Ensure zero secrets.',
            approved_budget=300000,
            created_by=self.super_admin
        )
        rec = HandoverZipGenerator(req, self.super_admin).generate(force_with_exception=True)

        with zipfile.ZipFile(rec.zip_file.path, 'r') as zf:
            for item in zf.namelist():
                self.assertFalse(item.endswith('.env'))
                self.assertFalse('credentials' in item.lower())
                self.assertFalse('password' in item.lower())

    # 15. Developer assignment
    def test_15_developer_assignment(self):
        self.client.force_authenticate(user=self.super_admin)
        req = ProjectRequirement.objects.create(enquiry=self.enquiry, project_name='Assignment Project', scope_of_work='Scope', approved_budget=400000, created_by=self.super_admin)
        rec = HandoverZipGenerator(req, self.super_admin).generate(force_with_exception=True)

        payload = {
            'developer_id': self.developer.id,
            'priority': 'Urgent',
            'developer_team': 'Backend Team Alpha',
            'expected_delivery_date': '2026-12-31',
            'instructions': 'Follow architecture requirements strictly.'
        }
        res = self.client.post(f'/api/handover/{rec.id}/assign-developer/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        rec.refresh_from_db()
        self.assertEqual(rec.assigned_developer, self.developer)
        self.assertEqual(rec.priority, 'Urgent')

        # Check DeveloperProject is created
        self.assertTrue(DeveloperProject.objects.filter(requirement=req, assigned_developer=self.developer).exists())

    # 16. Project status updates
    def test_16_project_status_updates(self):
        self.client.force_authenticate(user=self.developer)
        req = ProjectRequirement.objects.create(enquiry=self.enquiry, project_name='Project Status Test', created_by=self.super_admin)
        prj = DeveloperProject.objects.create(
            requirement=req,
            title='Project Status Test',
            assigned_developer=self.developer,
            status=ProjectStatus.IN_PROGRESS,
            progress_percentage=20
        )
        res = self.client.patch(f'/api/projects/{prj.id}/', {
            'progress_percentage': 60,
            'status': ProjectStatus.INTERNAL_REVIEW
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        prj.refresh_from_db()
        self.assertEqual(prj.progress_percentage, 60)
        self.assertEqual(prj.status, ProjectStatus.INTERNAL_REVIEW)

    # 17. Analytics date filtering
    def test_17_analytics_date_filtering(self):
        self.client.force_authenticate(user=self.super_admin)
        # Test today filter
        res_today = self.client.get('/api/analytics/dashboard/?period=today')
        self.assertEqual(res_today.status_code, status.HTTP_200_OK)
        self.assertIn('kpis', res_today.data)

        # Test last 30 days filter
        res_30 = self.client.get('/api/analytics/dashboard/?period=last_30_days')
        self.assertEqual(res_30.status_code, status.HTTP_200_OK)
        self.assertIn('total_enquiries', res_30.data['kpis'])

    # 18. Financial metric correctness
    def test_18_financial_metric_correctness(self):
        self.client.force_authenticate(user=self.super_admin)
        inv = InvoiceQuote.objects.create(
            reference_no='XEYR-INV-TEST-01',
            doc_type=InvoiceQuote.DocType.INVOICE,
            amount_invoiced=100000.00,
            amount_received=40000.00,
            amount_pending=60000.00,
            status=InvoiceQuote.Status.PARTIALLY_PAID,
            created_by=self.super_admin
        )
        exp = ExpenseRecord.objects.create(
            title='Cloud Infrastructure',
            amount=15000.00,
            date=timezone.now().date(),
            recorded_by=self.super_admin
        )
        res = self.client.get('/api/analytics/dashboard/?period=last_30_days')
        k = res.data['kpis']
        self.assertEqual(k['amount_invoiced'], 100000.00)
        self.assertEqual(k['amount_received'], 40000.00)
        self.assertEqual(k['amount_pending'], 60000.00)
        self.assertEqual(k['expenses'], 15000.00)
        self.assertEqual(k['net_profit'], 25000.00)  # 40000 - 15000

    # 19. Role-based access controls
    def test_19_role_based_access_controls(self):
        # Developer cannot generate handover ZIP
        self.client.force_authenticate(user=self.developer)
        req = ProjectRequirement.objects.create(enquiry=self.enquiry, project_name='RBAC Test', created_by=self.super_admin)
        res = self.client.post(f'/api/handover/requirement/{req.id}/', {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Developer cannot create invoices
        res_fin = self.client.post('/api/finance/invoices/', {'amount_invoiced': 1000})
        self.assertEqual(res_fin.status_code, status.HTTP_403_FORBIDDEN)

    # 20. API validation and error handling
    def test_20_api_validation_and_error_handling(self):
        self.client.force_authenticate(user=self.super_admin)
        # Non-existent enquiry
        res404 = self.client.get('/api/enquiries/999999/')
        self.assertEqual(res404.status_code, status.HTTP_404_NOT_FOUND)

        # Invalid status
        res_invalid_status = self.client.post(f'/api/enquiries/{self.enquiry.id}/status/', {'status': 'RANDOM_STATUS'})
        self.assertEqual(res_invalid_status.status_code, status.HTTP_400_BAD_REQUEST)


class XeyrEventManagementAndRazorpayTestCase(TestCase):
    """
    Automated Test Suite for Event Management, Notification Workflow,
    Dynamic Forms, Razorpay Verification, and Social Links.
    """
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username='event_admin',
            email='admin@events.xeyr.in',
            password='Password@123',
            role=UserRole.SUPER_ADMIN
        )
        self.staff_user = User.objects.create_user(
            username='event_staff',
            email='staff@events.xeyr.in',
            password='Password@123',
            role=UserRole.SALES_CRM
        )

        now = timezone.now()
        # Upcoming Free Event
        self.free_event = EventListing.objects.create(
            title='Open Source AI Bootcamp',
            slug='open-source-ai-bootcamp',
            event_type='Bootcamp',
            status='UPCOMING',
            event_date=(now + datetime.timedelta(days=10)).date(),
            start_time=datetime.time(10, 0),
            end_time=datetime.time(13, 0),
            mode='Online Webinar',
            venue='Virtual Auditorium',
            is_paid=False,
            fee='Free',
            fee_amount=0.00,
            max_participants=50,
            is_published=True,
            description='Free hands-on session on open source AI.'
        )
        # Dynamic fields for Free Event
        EventFormField.objects.create(
            event=self.free_event,
            field_name='college',
            field_label='College / Institute',
            field_type='college',
            is_required=True,
            display_order=1
        )

        # Upcoming Paid Event
        self.paid_event = EventListing.objects.create(
            title='Production Cloud & Kubernetes Masterclass',
            slug='production-cloud-k8s',
            event_type='Masterclass',
            status='UPCOMING',
            event_date=(now + datetime.timedelta(days=20)).date(),
            start_time=datetime.time(14, 0),
            end_time=datetime.time(18, 0),
            mode='Online Live Lab',
            venue='Cloud Lab',
            is_paid=True,
            fee='₹499.00',
            fee_amount=499.00,
            currency='INR',
            max_participants=2,  # Set small limit to test capacity enforcement!
            is_published=True,
            description='Intensive paid masterclass on Kubernetes architecture.'
        )
        EventFormField.objects.create(
            event=self.paid_event,
            field_name='github_handle',
            field_label='GitHub Profile URL',
            field_type='text',
            is_required=True,
            display_order=1
        )

        # Completed Event Archive
        self.completed_event = EventListing.objects.create(
            title='Full-Stack Architecture 2025',
            slug='full-stack-arch-2025',
            event_type='Workshop',
            status='COMPLETED',
            event_date=(now - datetime.timedelta(days=40)).date(),
            is_paid=False,
            fee='Free',
            max_participants=100,
            is_published=True,
            description='Past architectural workshop.'
        )

    # 1. Test Public Events Feed Segregation (Upcoming vs Completed)
    def test_01_public_events_feed_segregation(self):
        res = self.client.get('/api/events/public/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        upcoming = res.data.get('upcoming_events', [])
        completed = res.data.get('completed_events', [])

        # Both free_event and paid_event are upcoming
        upcoming_slugs = [e['slug'] for e in upcoming]
        self.assertIn('open-source-ai-bootcamp', upcoming_slugs)
        self.assertIn('production-cloud-k8s', upcoming_slugs)
        self.assertNotIn('full-stack-arch-2025', upcoming_slugs)

        # Completed event is in completed_events archive
        completed_slugs = [e['slug'] for e in completed]
        self.assertIn('full-stack-arch-2025', completed_slugs)
        self.assertNotIn('open-source-ai-bootcamp', completed_slugs)

    # 2. Test Empty State / Notification CTA rule
    def test_02_empty_state_notification_cta_rule(self):
        # When upcoming events exist
        res = self.client.get('/api/events/public/')
        self.assertGreater(len(res.data['upcoming_events']), 0)
        self.assertFalse(res.data.get('empty_state_cta'))

        # When all upcoming events are unpublished
        EventListing.objects.filter(status='UPCOMING').update(is_published=False)
        res_empty = self.client.get('/api/events/public/')
        self.assertEqual(len(res_empty.data['upcoming_events']), 0)
        self.assertTrue(res_empty.data.get('empty_state_cta'))

    # 3. Test Event Notification Subscriber Signup & Duplicate Prevention
    def test_03_subscriber_signup_and_duplicate_prevention(self):
        payload = {
            'full_name': 'Test Subscriber',
            'email': 'sub.test@example.com',
            'categories': 'Workshop, Masterclass'
        }
        res1 = self.client.post('/api/events/subscribe/', payload)
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res1.data.get('success'))

        sub = EventNotificationSubscriber.objects.get(email='sub.test@example.com')
        self.assertEqual(sub.full_name, 'Test Subscriber')
        self.assertTrue(sub.consent_given)
        self.assertTrue(len(sub.unsubscribe_token) > 0)

        # Duplicate subscription should not duplicate record, returns 200 OK
        res2 = self.client.post('/api/events/subscribe/', payload)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(EventNotificationSubscriber.objects.filter(email='sub.test@example.com').count(), 1)

    # 4. Test Subscriber Unsubscribe Flow
    def test_04_subscriber_unsubscribe_flow(self):
        sub = EventNotificationSubscriber.objects.create(
            full_name='Unsub User',
            email='unsub@example.com',
            consent_given=True
        )
        self.assertTrue(sub.is_active)
        res = self.client.get(f'/api/events/subscribers/unsubscribe/{sub.unsubscribe_token}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sub.refresh_from_db()
        self.assertFalse(sub.is_active)

    # 5. Test Free Event Dynamic Registration
    def test_05_free_event_dynamic_registration(self):
        payload = {
            'full_name': 'Rajesh Sharma',
            'email': 'rajesh@techuniv.edu',
            'phone': '+91 98401 55667',
            'custom_fields': {
                'college': 'Anna University Chennai'
            }
        }
        res = self.client.post(f'/api/events/{self.free_event.id}/register-dynamic/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data.get('success'))
        self.assertEqual(res.data.get('registration_status'), 'CONFIRMED')
        self.assertFalse(res.data.get('payment_required'))
        self.assertTrue(res.data.get('registration_reference').startswith('XEYR-REG-'))

        # Check DB persistence
        reg = EventRegistration.objects.get(registration_reference=res.data['registration_reference'])
        self.assertEqual(reg.full_name, 'Rajesh Sharma')
        self.assertEqual(reg.form_responses.get('college'), 'Anna University Chennai')
        self.assertEqual(reg.registration_status, 'CONFIRMED')
        self.assertEqual(reg.payment_status, 'NOT_REQUIRED')

    # 6. Test Paid Event Dynamic Registration & Razorpay Order Creation
    def test_06_paid_event_registration_creates_razorpay_order(self):
        payload = {
            'full_name': 'Ananya Roy',
            'email': 'ananya@cloudeng.io',
            'phone': '+91 97102 88990',
            'custom_fields': {
                'github_handle': 'https://github.com/ananya-eng'
            }
        }
        res = self.client.post(f'/api/events/{self.paid_event.id}/register-dynamic/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data.get('success'))
        self.assertTrue(res.data.get('payment_required'))
        self.assertEqual(res.data.get('registration_status'), 'PENDING_PAYMENT')
        self.assertIn('razorpay_order_id', res.data)
        self.assertEqual(res.data.get('amount_in_paise'), 49900)  # 499 INR * 100

        # Check EventPaymentOrder record in DB
        order_rec = EventPaymentOrder.objects.get(razorpay_order_id=res.data['razorpay_order_id'])
        self.assertEqual(order_rec.amount, 499.00)
        self.assertEqual(order_rec.status, EventPaymentOrder.PaymentOrderStatus.CREATED)

    # 7. Test Razorpay Payment Signature Verification & Confirmation
    def test_07_razorpay_signature_verification_and_confirmation(self):
        # Register for paid event
        payload = {
            'full_name': 'Karthik V',
            'email': 'karthik@enterprise.com',
            'phone': '+91 99401 11223',
            'custom_fields': {'github_handle': 'https://github.com/karthikv'}
        }
        res_reg = self.client.post(f'/api/events/{self.paid_event.id}/register-dynamic/', payload, format='json')
        order_id = res_reg.data['razorpay_order_id']
        reg_id = res_reg.data['registration_id']
        payment_id = 'pay_test_karthik_123'

        # Compute valid HMAC SHA256 signature
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'test_secret')
        msg = f"{order_id}|{payment_id}"
        valid_signature = hmac.new(key_secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()

        # Submit verification payload
        verify_payload = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': valid_signature,
            'registration_id': reg_id
        }
        res_verify = self.client.post('/api/events/verify-payment/', verify_payload, format='json')
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)
        self.assertTrue(res_verify.data.get('success'))
        self.assertEqual(res_verify.data.get('payment_status'), 'PAID')
        self.assertEqual(res_verify.data.get('registration_status'), 'CONFIRMED')

        # Check DB update
        reg = EventRegistration.objects.get(id=reg_id)
        self.assertEqual(reg.registration_status, 'CONFIRMED')
        self.assertEqual(reg.payment_status, 'PAID')
        self.assertEqual(reg.fee_paid, 499.00)

        # Check Ledger PaymentRecord creation
        self.assertTrue(PaymentRecord.objects.filter(transaction_reference=payment_id).exists())

    # 8. Test Invalid Signature Rejection
    def test_08_invalid_payment_signature_rejection(self):
        res_reg = self.client.post(f'/api/events/{self.paid_event.id}/register-dynamic/', {
            'full_name': 'Hacker Test',
            'email': 'hacker@test.com',
            'phone': '+91 98840 00000',
            'custom_fields': {'github_handle': 'https://github.com/hacker'}
        }, format='json')
        order_id = res_reg.data['razorpay_order_id']
        reg_id = res_reg.data['registration_id']

        verify_payload = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': 'pay_invalid_456',
            'razorpay_signature': 'invalid_tampered_signature_string',
            'registration_id': reg_id
        }
        res_verify = self.client.post('/api/events/verify-payment/', verify_payload, format='json')
        self.assertEqual(res_verify.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res_verify.data.get('success'))

        # Registration must NOT be confirmed
        reg = EventRegistration.objects.get(id=reg_id)
        self.assertNotEqual(reg.registration_status, 'CONFIRMED')
        self.assertEqual(reg.payment_status, 'FAILED')

    # 9. Test Event Capacity Limit Enforcement
    def test_09_event_capacity_limit_enforcement(self):
        # paid_event has max_participants=2
        # Fill capacity with 2 confirmed registrations
        for i in range(2):
            EventRegistration.objects.create(
                event=self.paid_event,
                event_name=self.paid_event.title,
                full_name=f'Participant {i+1}',
                email=f'p{i+1}@test.com',
                registration_status='CONFIRMED',
                payment_status='PAID'
            )
        self.assertEqual(self.paid_event.confirmed_count, 2)

        # Attempt 3rd registration
        res = self.client.post(f'/api/events/{self.paid_event.id}/register-dynamic/', {
            'full_name': 'Over Capacity User',
            'email': 'over@test.com',
            'phone': '+91 98840 99999',
            'custom_fields': {'github_handle': 'https://github.com/over'}
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('capacity', res.data.get('error', '').lower())

    # 10. Test Social Media Config Management & Public Visibility
    def test_10_social_media_config_and_public_visibility(self):
        self.client.force_authenticate(user=self.admin)
        # Update Instagram and LinkedIn
        res = self.client.post('/api/social-links/manage/', {
            'instagram_url': 'https://instagram.com/xeyrtechnologies',
            'instagram_public': True,
            'linkedin_url': 'https://linkedin.com/company/xeyrtechnologies',
            'linkedin_public': True,
            'github_url': '',
            'github_public': False
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Check public endpoint
        res_pub = self.client.get('/api/social-links/public/')
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        social_items = res_pub.data if isinstance(res_pub.data, list) else res_pub.data.get('social_links', [])
        platforms = [p['platform_key'] for p in social_items]
        self.assertIn('instagram', platforms)
        self.assertIn('linkedin', platforms)
        # Empty or non-public URLs should be excluded
        self.assertNotIn('github', platforms)

    # 11. Test Subscriber Notification Broadcast
    def test_11_subscriber_notification_broadcast(self):
        self.client.force_authenticate(user=self.admin)
        EventNotificationSubscriber.objects.create(full_name='Sub 1', email='sub1@broadcast.com', consent_given=True)
        EventNotificationSubscriber.objects.create(full_name='Sub 2', email='sub2@broadcast.com', consent_given=True)

        res = self.client.post(f'/api/events/manage/{self.free_event.id}/notify-subscribers/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data.get('success'))
        self.assertEqual(res.data.get('eligible_subscribers'), 2)
        # Notifications delivered/recorded
        self.assertEqual(EventNotificationDelivery.objects.filter(event=self.free_event).count(), 2)

    # 12. Test Admin Payment Dashboard KPIs
    def test_12_admin_payment_dashboard_kpis(self):
        self.client.force_authenticate(user=self.admin)
        # Create a paid order in DB
        reg = EventRegistration.objects.create(
            event=self.paid_event,
            event_name=self.paid_event.title,
            full_name='KPI Test User',
            email='kpi@test.com',
            registration_status='CONFIRMED',
            payment_status='PAID',
            fee_paid=499.00
        )
        EventPaymentOrder.objects.create(
            event=self.paid_event,
            registration=reg,
            razorpay_order_id='order_kpi_123',
            razorpay_payment_id='pay_kpi_123',
            amount=499.00,
            status=EventPaymentOrder.PaymentOrderStatus.PAID
        )

        res = self.client.get('/api/events/payments/dashboard/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        kpi = res.data.get('kpis', {})
        self.assertEqual(kpi.get('paid_payments'), 1)
        self.assertEqual(float(kpi.get('gross_revenue')), 499.00)

    # 13. Test CSV Participant Export
    def test_13_admin_export_registrations_csv(self):
        self.client.force_authenticate(user=self.admin)
        EventRegistration.objects.create(
            event=self.free_event,
            event_name=self.free_event.title,
            full_name='CSV Export User',
            email='csv@test.com',
            phone='+91 99999 88888',
            registration_status='CONFIRMED',
            form_responses={'college': 'Loyola College'}
        )
        res = self.client.get(f'/api/events/manage/{self.free_event.id}/export-csv/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertIn('CSV Export User', res.content.decode('utf-8'))
        self.assertIn('Loyola College', res.content.decode('utf-8'))

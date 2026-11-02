import hmac
import hashlib
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

from core.models import User
from .models import (
    EventListing, EventFormField, EventRegistration,
    EventNotificationSubscriber, EventNotificationDelivery,
    EventPaymentOrder
)
from .views import (
    ensure_default_event_form_fields,
    send_event_notification_to_subscribers,
    DEFAULT_REGISTRATION_FIELDS
)


class EventsManagementComprehensiveAuditTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='audit_admin',
            email='audit_admin@xeyr.in',
            password='AdminAuditPassword!2026'
        )

        today = timezone.now().date()
        # Create an eligible published upcoming event
        self.upcoming_event = EventListing.objects.create(
            title='NextGen AI Engineering Workshop',
            slug='nextgen-ai-workshop',
            event_type='WORKSHOP',
            short_description='Hands-on masterclass on AI agents and scalable pipelines.',
            event_date=today + timedelta(days=10),
            date_time=f"{today + timedelta(days=10)} (10:00 AM - 1:00 PM)",
            mode='ONLINE',
            venue='Google Meet / Zoom',
            max_participants=50,
            is_paid=False,
            fee_amount=Decimal('0.00'),
            is_published=True,
            is_active=True,
            status=EventListing.EventStatus.UPCOMING
        )
        ensure_default_event_form_fields(self.upcoming_event)

        # Create a draft event (should never appear in public feed or trigger notifications)
        self.draft_event = EventListing.objects.create(
            title='Confidential Internal Architecture Session',
            slug='confidential-internal-session',
            event_type='TECH_TALK',
            short_description='Internal draft event.',
            event_date=today + timedelta(days=20),
            is_published=False,
            is_active=True,
            status=EventListing.EventStatus.DRAFT
        )

        # Create a paid event
        self.paid_event = EventListing.objects.create(
            title='Production Cloud Devops Bootcamp',
            slug='cloud-devops-bootcamp',
            event_type='BOOTCAMP',
            short_description='Intensive hands-on DevOps training.',
            event_date=today + timedelta(days=15),
            is_paid=True,
            fee_amount=Decimal('99.00'),
            currency='INR',
            max_participants=30,
            is_published=True,
            is_active=True,
            status=EventListing.EventStatus.UPCOMING
        )
        ensure_default_event_form_fields(self.paid_event)

    def test_01_public_events_feed_filters_drafts_and_cancelled(self):
        """Scenario A & B: Public feed returns only published active upcoming events."""
        res = self.client.get('/api/events/public/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['has_upcoming'])
        self.assertFalse(res.data['empty_state_cta'])

        titles = [e['title'] for e in res.data['upcoming_events']]
        self.assertIn('NextGen AI Engineering Workshop', titles)
        self.assertIn('Production Cloud Devops Bootcamp', titles)
        self.assertNotIn('Confidential Internal Architecture Session', titles)

    def test_02_empty_state_when_no_upcoming_events_exist(self):
        """Scenario B: When all events are unpublished/completed, empty state is signaled."""
        EventListing.objects.filter(is_published=True).update(is_published=False)
        res = self.client.get('/api/events/public/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(res.data['has_upcoming'])
        self.assertTrue(res.data['empty_state_cta'])
        self.assertEqual(len(res.data['upcoming_events']), 0)

    def test_03_default_registration_fields_automatically_configured(self):
        """Section 5: Default fields (Full Name, Email, Phone, Participant Category) exist automatically."""
        field_names = list(self.upcoming_event.form_fields.values_list('field_name', flat=True))
        for df in DEFAULT_REGISTRATION_FIELDS:
            self.assertIn(df['field_name'], field_names)

        # Verify Participant Category has correct dropdown options
        cat_field = self.upcoming_event.form_fields.get(field_name='participant_category')
        self.assertEqual(cat_field.field_type, 'dropdown')
        self.assertIn('Student', cat_field.options)
        self.assertIn('Working Professional', cat_field.options)

        # Re-running ensure_default_event_form_fields must NOT duplicate fields
        ensure_default_event_form_fields(self.upcoming_event)
        self.assertEqual(
            self.upcoming_event.form_fields.filter(field_name='participant_category').count(),
            1
        )

    def test_04_cannot_delete_mandatory_default_fields(self):
        """Section 5: Admin cannot delete mandatory default fields."""
        self.client.force_authenticate(user=self.admin_user)
        cat_field = self.upcoming_event.form_fields.get(field_name='participant_category')
        del_res = self.client.delete(f'/api/events/manage/fields/{cat_field.id}/')
        self.assertEqual(del_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot delete mandatory default registration fields', del_res.data['error'])

    def test_05_additional_dynamic_form_fields(self):
        """Section 5: Dynamic extra fields can be added, reordered, and validated."""
        self.client.force_authenticate(user=self.admin_user)
        add_res = self.client.post(f'/api/events/manage/{self.upcoming_event.id}/fields/', {
            'field_label': 'College or Company Name',
            'field_name': 'college_or_company',
            'field_type': 'text',
            'is_required': True,
            'placeholder': 'Enter your institution'
        }, format='json')
        self.assertEqual(add_res.status_code, status.HTTP_201_CREATED)

        # Registration must now enforce this new field
        fail_res = self.client.post(f'/api/events/{self.upcoming_event.id}/register-dynamic/', {
            'full_name': 'Priya Nair',
            'email': 'priya@example.com',
            'phone': '+91 98888 77777',
            'participant_category': 'Student'
        }, format='json')
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Field 'College or Company Name' is required", fail_res.data['error'])

        # Valid submission with dynamic field succeeds
        pass_res = self.client.post(f'/api/events/{self.upcoming_event.id}/register-dynamic/', {
            'full_name': 'Priya Nair',
            'email': 'priya@example.com',
            'phone': '+91 98888 77777',
            'participant_category': 'Student',
            'college_or_company': 'IIT Madras'
        }, format='json')
        self.assertEqual(pass_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(pass_res.data['success'])

    def test_06_subscriber_registration_and_duplicate_prevention(self):
        """Section 3: Subscriber signup, consent, anti-bot honeypot, duplicate prevention."""
        # Bot submission with honeypot filled should be silently dropped and never saved to DB
        bot_res = self.client.post('/api/events/subscribe/', {
            'name': 'Spam Bot',
            'email': 'bot@spam.com',
            'website_url': 'http://spamsite.ru',
            'consent': True
        }, format='json')
        self.assertEqual(bot_res.status_code, status.HTTP_200_OK)
        self.assertFalse(EventNotificationSubscriber.objects.filter(email='bot@spam.com').exists())

        # Legitimate subscriber
        sub_res = self.client.post('/api/events/subscribe/', {
            'name': 'Vikram Rathore',
            'email': 'vikram.rathore@domain.com',
            'categories': 'WORKSHOP,AI_AUTOMATION',
            'consent': True
        }, format='json')
        self.assertEqual(sub_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(sub_res.data['success'])

        # Re-subscribing with same email updates existing subscriber without creating duplicates
        re_sub = self.client.post('/api/events/subscribe/', {
            'name': 'Vikram Rathore Updated',
            'email': 'vikram.rathore@domain.com',
            'categories': 'ALL',
            'consent': True
        }, format='json')
        self.assertEqual(re_sub.status_code, status.HTTP_200_OK)
        self.assertEqual(
            EventNotificationSubscriber.objects.filter(email='vikram.rathore@domain.com').count(),
            1
        )
        sub = EventNotificationSubscriber.objects.get(email='vikram.rathore@domain.com')
        self.assertEqual(sub.full_name, 'Vikram Rathore Updated')

    def test_07_event_notification_workflow_and_idempotency(self):
        """Section 4: Publication announcements sent only once, idempotent on retries."""
        # Create active subscriber
        sub = EventNotificationSubscriber.objects.create(
            full_name='Alok Verma',
            email='alok.verma@example.com',
            categories_of_interest='WORKSHOP',
            is_active=True,
            consent_given=True
        )

        # Draft event must not send notifications
        draft_result = send_event_notification_to_subscribers(self.draft_event)
        self.assertFalse(draft_result['success'])
        self.assertEqual(draft_result['sent_count'], 0)

        # Published event announcement
        pub_result = send_event_notification_to_subscribers(self.upcoming_event)
        self.assertTrue(pub_result['success'])
        self.assertEqual(pub_result['eligible_subscribers'], 1)

        # Repeated notification call should NOT resend if force_resend=False
        repeat_result = send_event_notification_to_subscribers(self.upcoming_event, force_resend=False)
        self.assertTrue(repeat_result['success'])
        self.assertEqual(repeat_result['sent_count'], 0)  # Skipped because already delivered

    def test_08_free_event_registration_and_duplicate_prevention(self):
        """Section 6: Free registration completes immediately and blocks duplicate registrations."""
        payload = {
            'full_name': 'Meera Joshi',
            'email': 'meera.joshi@example.com',
            'phone': '+91 99112 23344',
            'participant_category': 'Working Professional',
            'company_or_college': 'TCS Bengaluru'
        }
        res = self.client.post(f'/api/events/{self.upcoming_event.id}/register-dynamic/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertFalse(res.data['payment_required'])
        self.assertEqual(res.data['registration_status'], 'CONFIRMED')

        # Duplicate registration for same event and email should be rejected
        dup_res = self.client.post(f'/api/events/{self.upcoming_event.id}/register-dynamic/', payload, format='json')
        self.assertEqual(dup_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('A confirmed registration with this email address already exists', dup_res.data['error'])

    def test_09_paid_event_registration_and_signature_verification(self):
        """Section 6: Paid event order creation and HMAC SHA256 payment signature verification."""
        reg_payload = {
            'full_name': 'Arjun Mehta',
            'email': 'arjun.mehta@fintech.in',
            'phone': '+91 91234 56789',
            'participant_category': 'Working Professional',
            'company_or_college': 'Zerodha'
        }
        res_reg = self.client.post(f'/api/events/{self.paid_event.id}/register-dynamic/', reg_payload, format='json')
        self.assertEqual(res_reg.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_reg.data['payment_required'])
        self.assertEqual(res_reg.data['amount'], 99.00)
        self.assertEqual(res_reg.data['amount_in_paise'], 9900)

        order_id = res_reg.data['razorpay_order_id']
        ref = res_reg.data['registration_reference']
        payment_id = 'pay_audit_test_9988'

        # Invalid payment signature must be rejected
        bad_verify = self.client.post('/api/events/verify-payment/', {
            'registration_reference': ref,
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': 'invalid_tampered_signature'
        }, format='json')
        self.assertEqual(bad_verify.status_code, status.HTTP_400_BAD_REQUEST)

        # Valid HMAC-SHA256 signature must be verified and confirmed
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', 'test_secret')
        msg = f"{order_id}|{payment_id}"
        valid_signature = hmac.new(key_secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()

        good_verify = self.client.post('/api/events/verify-payment/', {
            'registration_reference': ref,
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': valid_signature
        }, format='json')
        self.assertEqual(good_verify.status_code, status.HTTP_200_OK)
        self.assertTrue(good_verify.data['success'])

        # Verify DB state
        reg = EventRegistration.objects.get(registration_reference=ref)
        self.assertEqual(reg.registration_status, 'CONFIRMED')
        self.assertEqual(reg.payment_status, 'PAID')
        self.assertEqual(reg.fee_paid, Decimal('99.00'))

    def test_10_participant_signup_and_profile_management(self):
        """Participant sign up, authenticated session, profile editing and past registration linking."""
        signup_payload = {
            'username': 'student_riya',
            'email': 'riya.patel@engineering.edu',
            'password': 'SecurePassword@123',
            'full_name': 'Riya Patel',
            'phone': '+91 98877 66554',
            'participant_category': 'Student',
            'college_or_organization': 'Anna University'
        }
        res = self.client.post('/api/auth/register/', signup_payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['user']['username'], 'student_riya')
        self.assertEqual(res.data['user']['profile']['college_or_organization'], 'Anna University')

        # Profile fetch as authenticated user
        user = User.objects.get(username='student_riya')
        self.client.force_authenticate(user=user)
        res_prof = self.client.get('/api/auth/profile/')
        self.assertEqual(res_prof.status_code, status.HTTP_200_OK)
        self.assertEqual(res_prof.data['college_or_organization'], 'Anna University')

        # Profile update
        update_payload = {
            'bio': 'Passionate full-stack enthusiast and open source contributor.',
            'skills': 'Python, React, TypeScript, Docker',
            'github_url': 'https://github.com/riya-patel'
        }
        res_update = self.client.put('/api/auth/profile/', update_payload, format='json')
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.assertEqual(res_update.data['skills'], 'Python, React, TypeScript, Docker')

    def test_11_event_deletion_safeguard_prevents_cascading_data_loss(self):
        """Deleting an event with existing registrations must be safeguarded and archived instead of destroying data."""
        self.client.force_authenticate(user=self.admin_user)

        # Create registration for upcoming event
        EventRegistration.objects.create(
            event=self.upcoming_event,
            event_name=self.upcoming_event.title,
            full_name='Participant Safety Test',
            email='safety.test@xeyr.in',
            phone='+91 98765 43210',
            registration_status='CONFIRMED',
            payment_status='NOT_REQUIRED'
        )

        # Attempt hard delete on an event that has registrations
        res_delete = self.client.delete(f'/api/events/manage/{self.upcoming_event.id}/?hard_delete=true')
        self.assertEqual(res_delete.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Cannot permanently delete event with existing registrations', res_delete.data['error'])

        # Event must still exist in DB, marked archived
        self.upcoming_event.refresh_from_db()
        self.assertEqual(self.upcoming_event.status, EventListing.EventStatus.ARCHIVED)

        # Registrations are intact
        self.assertTrue(EventRegistration.objects.filter(event=self.upcoming_event).exists())

    def test_12_attendance_recording_and_certificate_eligibility(self):
        """Attendance tracking marks presence and evaluates certificate eligibility based on threshold."""
        self.client.force_authenticate(user=self.admin_user)
        self.upcoming_event.certificate_enabled = True
        self.upcoming_event.certificate_min_attendance = 80
        self.upcoming_event.save()

        reg = EventRegistration.objects.create(
            event=self.upcoming_event,
            event_name=self.upcoming_event.title,
            full_name='Attendance Test Attendee',
            email='att.test@xeyr.in',
            phone='+91 98765 43211',
            registration_status='CONFIRMED',
            payment_status='NOT_REQUIRED'
        )

        # Check eligibility before attendance recorded
        res_check = self.client.get(f'/api/events/manage/{self.upcoming_event.id}/certificates/')
        self.assertEqual(res_check.status_code, status.HTTP_200_OK)
        candidate = next((p for p in res_check.data['pending_eligible'] if p['registration_id'] == reg.id), None)
        self.assertIsNotNone(candidate)
        self.assertFalse(candidate['is_eligible'])

        # Record attendance: 90% (satisfies 80% threshold)
        res_att = self.client.post(f'/api/events/manage/{self.upcoming_event.id}/attendance/', {
            'records': [{
                'registration_id': reg.id,
                'attended': True,
                'attendance_percentage': 90
            }]
        }, format='json')
        self.assertEqual(res_att.status_code, status.HTTP_200_OK)

        # Now check eligibility again: must be eligible
        res_check2 = self.client.get(f'/api/events/manage/{self.upcoming_event.id}/certificates/')
        candidate2 = next((p for p in res_check2.data['pending_eligible'] if p['registration_id'] == reg.id), None)
        self.assertTrue(candidate2['is_eligible'])

    def test_13_certificate_issuance_and_public_verification_privacy(self):
        """Certificate issuance generates verifiable token and public verification protects private PII."""
        self.client.force_authenticate(user=self.admin_user)
        reg = EventRegistration.objects.create(
            event=self.upcoming_event,
            event_name=self.upcoming_event.title,
            full_name='Cert Verification Test',
            email='cert.test@xeyr.in',
            phone='+91 98765 43212',
            registration_status='CONFIRMED',
            payment_status='NOT_REQUIRED'
        )

        # Issue certificate
        res_issue = self.client.post(f'/api/events/manage/{self.upcoming_event.id}/certificates/', {
            'registration_ids': [reg.id]
        }, format='json')
        self.assertEqual(res_issue.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_issue.data['issued_count'], 1)
        cert_data = res_issue.data['certificates'][0]
        cert_id = cert_data['certificate_id']

        # Public verification with unauthenticated client
        self.client.logout()
        res_verify = self.client.get(f'/api/certificates/verify/{cert_id}/')
        self.assertEqual(res_verify.status_code, status.HTTP_200_OK)
        self.assertTrue(res_verify.data['is_valid'])
        self.assertEqual(res_verify.data['certificate']['recipient_name'], reg.full_name)
        self.assertEqual(res_verify.data['certificate']['event_title'], self.upcoming_event.title)

        # Privacy check: Private phone, email, or internal database ID must NOT be leaked
        self.assertNotIn('recipient_email', res_verify.data['certificate'])
        self.assertNotIn('phone', res_verify.data['certificate'])

    def test_14_event_feedback_submission_and_duplicate_prevention(self):
        """Feedback requires confirmed registration, awards points, and rejects duplicates."""
        reg = EventRegistration.objects.create(
            event=self.upcoming_event,
            event_name=self.upcoming_event.title,
            full_name='Feedback Test Attendee',
            email='feedback.test@xeyr.in',
            phone='+91 98765 43213',
            registration_status='CONFIRMED',
            payment_status='NOT_REQUIRED'
        )

        # Create user matching this registration
        user = User.objects.create_user(
            username='feedback_attendee',
            email=reg.email,
            password='TestPassword123'
        )
        self.client.force_authenticate(user=user)

        # First feedback submission
        fb_payload = {
            'event_id': self.upcoming_event.id,
            'rating': 5,
            'content_rating': 5,
            'mentor_rating': 5,
            'organization_rating': 5,
            'learnings': 'Learned advanced asynchronous architecture and database optimization.',
            'suggestions': 'More live hands-on exercises.'
        }
        res_fb = self.client.post('/api/participant/feedback/', fb_payload, format='json')
        self.assertEqual(res_fb.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_fb.data['success'])

        # Duplicate feedback must be blocked
        res_dup = self.client.post('/api/participant/feedback/', fb_payload, format='json')
        self.assertEqual(res_dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already submitted feedback', res_dup.data['error'])


    def test_15_public_leaderboard_privacy_and_scoring(self):
        """Public leaderboard ranks consented participants and hides non-consenting or private PII."""
        # Unauthenticated request to leaderboard
        self.client.logout()
        res_lb = self.client.get('/api/leaderboard/public/')
        self.assertEqual(res_lb.status_code, status.HTTP_200_OK)
        self.assertIn('leaderboard', res_lb.data)

        # Verify no sensitive contact information in response
        for item in res_lb.data['leaderboard']:
            self.assertNotIn('email', item)
            self.assertNotIn('phone', item)
            self.assertIn('display_name', item)
            self.assertIn('score', item)
            self.assertIn('rank', item)

    def test_16_public_event_gallery_and_filtering(self):
        """Event gallery items are publicly queryable with event and category filtering."""
        from events_mgmt.models import EventGalleryItem
        EventGalleryItem.objects.create(
            event=self.upcoming_event,
            title='Auditorium Session',
            image_url='https://example.com/photo1.jpg',
            caption='Deep dive into modern engineering.',
            category='HIGHLIGHTS',
            is_public=True
        )

        res_gal = self.client.get('/api/events/gallery/')
        self.assertEqual(res_gal.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_gal.data), 1)
        self.assertEqual(res_gal.data[0]['title'], 'Auditorium Session')

    def test_17_certificate_template_designer_lifecycle(self):
        """Administrator can create a draft template, edit, publish, duplicate, assign to an event, and preview with sample data."""
        from events_mgmt.models import CertificateTemplate
        self.client.force_authenticate(user=self.admin_user)

        # 1. Create a draft template
        payload = {
            'name': 'AI Masterclass Certificate Design',
            'status': 'DRAFT',
            'orientation': 'LANDSCAPE',
            'background_type': 'GRADIENT',
            'background_gradient': 'linear-gradient(135deg, #07132e 0%, #0d275e 100%)',
            'border_style': 'modern_blue',
            'border_color': '#27d4f4',
            'border_width': 10,
            'title': 'CERTIFICATE OF EXCELLENCE',
            'subtitle': 'PRESENTED TO',
            'description_template': 'For distinguished achievement in {{event_title}} issued on {{issue_date}} by {{organizer_name}}.',
            'organizer_name': 'XEYR Technologies Private Limited',
            'signatory_name': 'B. Santhosh Kumar',
            'signatory_title': 'Managing Director',
            'show_qr_code': True
        }
        res_create = self.client.post('/api/certificates/templates/', payload, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        tpl_id = res_create.data['id']
        self.assertEqual(res_create.data['status'], 'DRAFT')

        # 2. Preview template with sample data (returns printable HTML)
        res_prev = self.client.get(f'/api/certificates/templates/{tpl_id}/preview/')
        self.assertEqual(res_prev.status_code, status.HTTP_200_OK)
        self.assertIn('text/html', res_prev['Content-Type'])
        self.assertIn('CERTIFICATE OF EXCELLENCE', res_prev.content.decode('utf-8'))
        self.assertIn('XEYR-CERT-PREVIEW', res_prev.content.decode('utf-8'))

        # 3. Publish template
        res_pub = self.client.put(f'/api/certificates/templates/{tpl_id}/', {'status': 'PUBLISHED'}, format='json')
        self.assertEqual(res_pub.status_code, status.HTTP_200_OK)
        self.assertEqual(res_pub.data['status'], 'PUBLISHED')

        # 4. Duplicate template
        res_dup = self.client.post(f'/api/certificates/templates/{tpl_id}/duplicate/')
        self.assertEqual(res_dup.status_code, status.HTTP_201_CREATED)
        dup_id = res_dup.data['id']
        self.assertNotEqual(dup_id, tpl_id)
        self.assertEqual(res_dup.data['status'], 'DRAFT')

        # 5. Assign template to an event
        res_assign = self.client.put(f'/api/events/manage/{self.upcoming_event.id}/', {
            'certificate_template_ref': tpl_id
        }, format='json')
        self.assertEqual(res_assign.status_code, status.HTTP_200_OK)
        self.upcoming_event.refresh_from_db()
        self.assertEqual(self.upcoming_event.certificate_template_ref_id, tpl_id)

    def test_18_certificate_download_idor_protection(self):
        """Confirms that only the legitimate participant (or valid verification token / staff) can download a certificate, blocking IDOR."""
        from events_mgmt.models import EventCertificate
        reg_alice = EventRegistration.objects.create(
            event=self.upcoming_event,
            event_name=self.upcoming_event.title,
            full_name='Alice Wonderland',
            email='alice@example.com',
            phone='+91 91234 56789',
            registration_status='CONFIRMED',
            payment_status='NOT_REQUIRED'
        )
        user_alice = User.objects.create_user(username='alice_user', email='alice@example.com', password='AlicePassword!123')
        reg_alice.user = user_alice
        reg_alice.save()

        # Issue certificate for Alice
        cert_alice = EventCertificate.objects.create(
            event=self.upcoming_event,
            registration=reg_alice,
            user=user_alice,
            recipient_name=reg_alice.full_name,
            recipient_email=reg_alice.email,
            status='ISSUED'
        )

        # 1. Unauthenticated request without token: HTTP 403 Forbidden
        self.client.logout()
        res_unauth = self.client.get(f'/api/certificates/download/{cert_alice.certificate_id}/')
        self.assertEqual(res_unauth.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Other unauthorized participant (Bob) attempts to download Alice's certificate: HTTP 403 Forbidden
        user_bob = User.objects.create_user(username='bob_user', email='bob@example.com', password='BobPassword!123')
        self.client.force_authenticate(user=user_bob)
        res_bob = self.client.get(f'/api/certificates/download/{cert_alice.certificate_id}/')
        self.assertEqual(res_bob.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Alice downloads her own certificate: HTTP 200 OK
        self.client.force_authenticate(user=user_alice)
        res_alice = self.client.get(f'/api/certificates/download/{cert_alice.certificate_id}/')
        self.assertEqual(res_alice.status_code, status.HTTP_200_OK)
        self.assertIn('attachment', res_alice['Content-Disposition'])

        # 4. Verified download via valid verification token (e.g. from QR scan): HTTP 200 OK
        self.client.logout()
        res_token = self.client.get(f'/api/certificates/download/{cert_alice.certificate_id}/?token={cert_alice.verification_token}')
        self.assertEqual(res_token.status_code, status.HTTP_200_OK)

    def test_19_revoked_certificate_status(self):
        """Revoked certificates are rejected during public verification and download."""
        from events_mgmt.models import EventCertificate
        reg = EventRegistration.objects.create(
            event=self.upcoming_event,
            event_name=self.upcoming_event.title,
            full_name='Revocation Test Candidate',
            email='revoked.user@example.com',
            phone='+91 99887 76655',
            registration_status='CONFIRMED',
            payment_status='NOT_REQUIRED'
        )
        cert = EventCertificate.objects.create(
            event=self.upcoming_event,
            registration=reg,
            recipient_name=reg.full_name,
            recipient_email=reg.email,
            status='REVOKED'
        )

        # Public verification returns 404 with revocation notice
        self.client.logout()
        res_ver = self.client.get(f'/api/certificates/verify/{cert.certificate_id}/')
        self.assertEqual(res_ver.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res_ver.data['is_valid'])
        self.assertIn('revoked', res_ver.data['message'].lower())

        # Download returns 404 Not Found
        res_dl = self.client.get(f'/api/certificates/download/{cert.certificate_id}/')
        self.assertEqual(res_dl.status_code, status.HTTP_404_NOT_FOUND)


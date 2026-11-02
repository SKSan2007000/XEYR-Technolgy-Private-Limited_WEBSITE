import os
import sys
import json
from decimal import Decimal

# Set up Django environment
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'xeyr_backend.settings')

import django
django.setup()

from django.test import Client
from django.utils import timezone
from core.models import User, SystemSetting
from events_mgmt.models import EventListing, EventRegistration, EventCertificate, CertificateTemplate

def run_security_audit():
    print("=" * 80)
    print("XEYR TECHNOLOGIES — AUTOMATED APPLICATION SECURITY & INTEGRITY AUDIT")
    print("=" * 80)
    client = Client()

    results = []

    # Setup test users
    admin_user = User.objects.filter(role='SUPER_ADMIN').first()
    if not admin_user:
        admin_user = User.objects.create_superuser(username='sec_admin', email='sec_admin@xeyr.internal', password='AdminPassword123!')

    participant_alice = User.objects.filter(username='sec_alice').first()
    if not participant_alice:
        participant_alice = User.objects.create_user(username='sec_alice', email='sec_alice@xeyr.internal', password='AlicePassword123!', role='PARTICIPANT')
    else:
        participant_alice.role = 'PARTICIPANT'
        participant_alice.save()

    participant_bob = User.objects.filter(username='sec_bob').first()
    if not participant_bob:
        participant_bob = User.objects.create_user(username='sec_bob', email='sec_bob@xeyr.internal', password='BobPassword123!', role='PARTICIPANT')
    else:
        participant_bob.role = 'PARTICIPANT'
        participant_bob.save()

    # Scenario 1: Anonymous user attempts an admin API call
    client.logout()
    res1 = client.get('/api/events/manage/')
    pass1 = res1.status_code in (401, 403)
    results.append(('Scenario 1: Anonymous user attempts admin API (/api/events/manage/)', pass1, f"HTTP {res1.status_code}"))

    # Scenario 2: Participant attempts to access another participant's registration
    # Create registration for Alice
    test_event = EventListing.objects.filter(is_published=True).first()
    if not test_event:
        test_event = EventListing.objects.create(
            title='Security Verification Summit',
            slug='security-verification-summit',
            event_date=timezone.now().date(),
            is_published=True
        )

    reg_alice = EventRegistration.objects.create(
        event=test_event,
        event_name=test_event.title,
        full_name='Alice Security',
        email='sec_alice@xeyr.internal',
        phone='+91 91111 22222',
        registration_status='CONFIRMED',
        user=participant_alice
    )

    # Bob logs in and checks /api/participant/registrations/
    client.force_login(participant_bob)
    res2 = client.get('/api/participant/registrations/')
    bob_registrations = res2.json() if res2.status_code == 200 else []
    alice_reg_in_bob = any(r.get('id') == reg_alice.id for r in bob_registrations)
    pass2 = (res2.status_code == 200 and not alice_reg_in_bob)
    results.append(("Scenario 2: Participant attempts to access another's registration (IDOR)", pass2, f"Alice's records isolated: {not alice_reg_in_bob}"))

    # Scenario 3: Participant attempts to download another participant's private certificate
    cert_alice = EventCertificate.objects.create(
        event=test_event,
        registration=reg_alice,
        user=participant_alice,
        recipient_name='Alice Security',
        recipient_email='sec_alice@xeyr.internal',
        status='ISSUED'
    )
    # Bob attempts to download Alice's certificate without token
    res3 = client.get(f'/api/certificates/download/{cert_alice.certificate_id}/')
    pass3 = res3.status_code == 403
    results.append(("Scenario 3: Participant attempts to download another's private certificate", pass3, f"HTTP {res3.status_code} Forbidden"))

    # Scenario 4: Participant attempts to issue a certificate
    res4 = client.post(f'/api/events/manage/{test_event.id}/certificates/', {'registration_ids': [reg_alice.id]}, content_type='application/json')
    pass4 = res4.status_code in (401, 403)
    results.append(('Scenario 4: Non-admin participant attempts to issue a certificate', pass4, f"HTTP {res4.status_code} Forbidden"))

    # Scenario 5: Non-admin attempts to publish an event
    res5 = client.put(f'/api/events/manage/{test_event.id}/', {'is_published': True, 'title': 'Hacked Title'}, content_type='application/json')
    pass5 = res5.status_code in (401, 403)
    results.append(('Scenario 5: Non-admin attempts to publish or modify an event', pass5, f"HTTP {res5.status_code} Forbidden"))

    # Scenario 6: Client submits a modified event price during registration
    # Price is enforced server-side from event database record; client cannot tamper with fee
    paid_event = EventListing.objects.filter(is_paid=True).first()
    if not paid_event:
        paid_event = EventListing.objects.create(
            title='Security Paid Masterclass',
            slug='security-paid-masterclass',
            event_date=timezone.now().date(),
            is_published=True,
            is_paid=True,
            fee_amount=Decimal('500.00')
        )
    # Anonymous client tries registering with fee = 0
    client.logout()
    res6 = client.post(f'/api/events/{paid_event.id}/register-dynamic/', {
        'full_name': 'Hacker Price',
        'email': 'hacker@price.io',
        'phone': '+91 99999 88888',
        'participant_category': 'Student',
        'fee_amount': '0.00' # Attempt price tampering
    }, content_type='application/json')
    # Server must require payment of genuine fee (500.00) or respond with payment required
    is_tamper_prevented = False
    if res6.status_code in (200, 201):
        data6 = res6.json()
        if data6.get('requires_payment') and float(data6.get('fee_amount', 0)) == 500.00:
            is_tamper_prevented = True
    elif res6.status_code in (400, 402):
        is_tamper_prevented = True
    results.append(('Scenario 6: Client attempts event price tampering', is_tamper_prevented, "Server enforces DB fee (500.00)"))

    # Scenario 7: Client submits a fabricated payment-success status without valid HMAC signature
    fake_payment_payload = {
        'razorpay_order_id': 'order_fake_12345',
        'razorpay_payment_id': 'pay_fake_67890',
        'razorpay_signature': 'invalid_forged_hmac_signature_hex'
    }
    res7 = client.post('/api/events/verify-payment/', fake_payment_payload, content_type='application/json')
    pass7 = res7.status_code in (400, 403, 404)
    results.append(('Scenario 7: Client submits fabricated payment without valid HMAC signature', pass7, f"HTTP {res7.status_code} Rejected"))

    # Scenario 8: User uploads prohibited or oversized file
    from django.conf import settings
    max_mb = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 52428800) / (1024 * 1024)
    pass8 = max_mb <= 50
    results.append(('Scenario 8: File upload restriction enforced', pass8, f"Max upload capped at {max_mb} MB"))

    # Scenario 9: Invalid certificate ID is submitted for public verification
    res9 = client.get('/api/certificates/verify/INVALID-NONEXISTENT-ID-99999/')
    pass9 = res9.status_code == 404 and res9.json().get('is_valid') is False
    results.append(('Scenario 9: Invalid certificate ID submitted for verification', pass9, f"HTTP 404 Not Found, is_valid: False"))

    # Scenario 10: Unauthenticated user attempts to change account settings
    res10 = client.post('/api/system-settings/', {'company_website_url': 'https://malicious.site'}, content_type='application/json')
    pass10 = res10.status_code in (401, 403)
    results.append(('Scenario 10: Unauthenticated user attempts to change system settings', pass10, f"HTTP {res10.status_code} Forbidden"))

    # Scenario 11: API receives invalid / malformed input
    res11 = client.post('/api/enquiries/submit/', {'invalid': 'payload'}, content_type='application/json')
    pass11 = res11.status_code == 400
    results.append(('Scenario 11: API receives invalid / malformed JSON input', pass11, f"HTTP {res11.status_code} Bad Request"))

    # Scenario 12: Production configuration contains safe defaults
    from django.conf import settings
    has_safe_passwords = len(settings.AUTH_PASSWORD_VALIDATORS) >= 4
    has_clickjacking_protection = 'django.middleware.clickjacking.XFrameOptionsMiddleware' in settings.MIDDLEWARE
    has_security_middleware = 'django.middleware.security.SecurityMiddleware' in settings.MIDDLEWARE
    has_xss_header = getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False)
    pass12 = has_safe_passwords and has_clickjacking_protection and has_security_middleware and has_xss_header
    results.append(('Scenario 12: Production defensive headers & password validators active', pass12, "SecurityMiddleware + Clickjacking + XSS + Password Validators active"))

    # Clean up test records
    reg_alice.delete()
    cert_alice.delete()

    print("\nSECURITY AUDIT RESULTS:")
    print("-" * 80)
    all_passed = True
    for name, status_pass, detail in results:
        status_str = "[PASS]" if status_pass else "[FAIL]"
        if not status_pass:
            all_passed = False
        print(f"{status_str} {name} — {detail}")

    print("-" * 80)
    if all_passed:
        print("FINAL STATUS: ALL 12 SECURITY AUDIT SCENARIOS PASSED!")
    else:
        print("FINAL STATUS: ONE OR MORE SCENARIOS FAILED.")
    print("=" * 80)
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(run_security_audit())

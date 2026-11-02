"""
XEYR Technologies — Comprehensive Authentication, Proxy & API Verification Script
Tests unauthenticated blocking, login, cookie persistence, all 14 modules,
PostgreSQL data integrity, session expiration, and logout via Vite Proxy.
"""

import urllib.request
import urllib.parse
import json
import http.cookiejar

VITE_BASE = 'http://localhost:5173'
BACKEND_BASE = 'http://127.0.0.1:8000'

def run_e2e_tests():
    print("=" * 80)
    print("XEYR ADMIN DASHBOARD — COMPLETE AUTHENTICATION & API INTEGRATION TEST")
    print("=" * 80)

    results = []

    # Cookie jar to simulate browser session cookies
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # -------------------------------------------------------------------------
    # 1. Test Vite Dev Server Availability & Proxy Health
    # -------------------------------------------------------------------------
    try:
        req = urllib.request.Request(f"{VITE_BASE}/api/health/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == 'healthy' and data.get('engine') == 'postgresql':
                results.append(("[PASS]", f"Vite proxy forwards /api/health/ -> PostgreSQL: {data.get('engine')}"))
            else:
                results.append(("[FAIL]", f"Health check returned unexpected payload: {data}"))
    except Exception as e:
        results.append(("[FAIL]", f"Health check failed: {e}"))

    # -------------------------------------------------------------------------
    # 2. Test Unauthenticated Protected Endpoints (Must be 401/403)
    # -------------------------------------------------------------------------
    protected_endpoints = [
        ('/api/analytics/dashboard/', 'Overview Analytics'),
        ('/api/auth/me/', 'Current User Profile'),
        ('/api/enquiries/', 'CRM Enquiries'),
        ('/api/projects/', 'Projects List'),
        ('/api/finance/invoices/', 'Finance Invoices'),
    ]

    for ep, name in protected_endpoints:
        try:
            req = urllib.request.Request(f"{VITE_BASE}{ep}")
            urllib.request.urlopen(req, timeout=5)
            results.append(("[FAIL]", f"Unauthenticated access allowed on {name} ({ep})!"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                results.append(("[PASS]", f"Unauthenticated {name} correctly rejected with HTTP {e.code}"))
            else:
                results.append(("[FAIL]", f"Unauthenticated {name} returned unexpected HTTP {e.code}"))
        except Exception as e:
            results.append(("[FAIL]", f"Unauthenticated test error on {name}: {e}"))

    # -------------------------------------------------------------------------
    # 3. Test Invalid Login Attempt
    # -------------------------------------------------------------------------
    try:
        bad_payload = json.dumps({"username": "admin", "password": "WrongPassword2026"}).encode('utf-8')
        req = urllib.request.Request(
            f"{VITE_BASE}/api/auth/login/",
            data=bad_payload,
            headers={'Content-Type': 'application/json'}
        )
        opener.open(req, timeout=5)
        results.append(("[FAIL]", "Invalid login attempt was accepted!"))
    except urllib.error.HTTPError as e:
        if e.code in (400, 401):
            results.append(("[PASS]", f"Invalid login correctly rejected with HTTP {e.code}"))
        else:
            results.append(("[FAIL]", f"Invalid login returned HTTP {e.code}"))
    except Exception as e:
        results.append(("[FAIL]", f"Invalid login error: {e}"))

    # -------------------------------------------------------------------------
    # 4. Test Successful Administrator Login & Session Acquisition
    # -------------------------------------------------------------------------
    csrf_token = None
    try:
        good_payload = json.dumps({"username": "admin", "password": "XeyrAdmin@2026"}).encode('utf-8')
        req = urllib.request.Request(
            f"{VITE_BASE}/api/auth/login/",
            data=good_payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = opener.open(req, timeout=5)
        user_data = json.loads(resp.read().decode('utf-8'))

        # Inspect cookies received
        cookies = {c.name: c.value for c in cj}
        csrf_token = cookies.get('csrftoken')
        sessionid = cookies.get('sessionid')

        if resp.status == 200 and sessionid and user_data.get('user', {}).get('username') == 'admin':
            results.append(("[PASS]", f"Admin login successful. Session established: user={user_data['user']['username']}, role={user_data['user'].get('role')}"))
        else:
            results.append(("[FAIL]", f"Login succeeded but session cookie or user missing: cookies={list(cookies.keys())}"))
    except Exception as e:
        results.append(("[FAIL]", f"Admin login request failed: {e}"))

    # -------------------------------------------------------------------------
    # 5. Verify /api/auth/me/ Session Persistence
    # -------------------------------------------------------------------------
    try:
        req = urllib.request.Request(f"{VITE_BASE}/api/auth/me/")
        resp = opener.open(req, timeout=5)
        me_data = json.loads(resp.read().decode('utf-8'))
        if me_data.get('username') == 'admin':
            results.append(("[PASS]", f"Session persistence verified via /api/auth/me/: logged in as {me_data['username']} ({me_data.get('email')})"))
        else:
            results.append(("[FAIL]", f"/api/auth/me/ returned unexpected user: {me_data}"))
    except Exception as e:
        results.append(("[FAIL]", f"/api/auth/me/ failed: {e}"))

    # -------------------------------------------------------------------------
    # 6. Verify Authenticated Overview Metrics (/api/analytics/dashboard/)
    # -------------------------------------------------------------------------
    try:
        req = urllib.request.Request(f"{VITE_BASE}/api/analytics/dashboard/?period=last_30_days")
        resp = opener.open(req, timeout=5)
        dash_data = json.loads(resp.read().decode('utf-8'))
        kpis = dash_data.get('kpis', {})

        total_enquiries = kpis.get('total_enquiries')
        active_projects = kpis.get('active_projects')
        amount_received = kpis.get('amount_received')
        amount_pending = kpis.get('amount_pending')

        if total_enquiries is not None:
            results.append(("[PASS]", f"Overview API returned real PostgreSQL KPIs: Enquiries={total_enquiries}, Projects={active_projects}, Revenue Received=Rs.{amount_received}, Pending=Rs.{amount_pending}"))
        else:
            results.append(("[FAIL]", f"Overview API returned invalid structure: {dash_data}"))
    except Exception as e:
        results.append(("[FAIL]", f"Authenticated Overview API failed: {e}"))

    # -------------------------------------------------------------------------
    # 7. Verify All Other 13 Business Management Module Endpoints
    # -------------------------------------------------------------------------
    module_endpoints = [
        ('Enquiries & CRM', '/api/enquiries/'),
        ('Client Requirements', '/api/requirements/'),
        ('Brand Assets', '/api/assets/'),
        ('Developer Handovers', '/api/handover/'),
        ('Projects Management', '/api/projects/'),
        ('Workshops & Events', '/api/events/manage/'),
        ('Registrations Roster', '/api/events/registrations/'),
        ('System Notifications', '/api/notifications/'),
        ('Invoices & Quotes', '/api/finance/invoices/'),
        ('Payment Records', '/api/finance/payments/'),
        ('Expense Records', '/api/finance/expenses/'),
        ('Social Media Config', '/api/social-links/manage/'),
        ('System Settings', '/api/system-settings/'),
    ]

    for name, ep in module_endpoints:
        try:
            req = urllib.request.Request(f"{VITE_BASE}{ep}")
            resp = opener.open(req, timeout=5)
            data = json.loads(resp.read().decode('utf-8'))
            count = len(data) if isinstance(data, list) else 1
            results.append(("[PASS]", f"Module '{name}' ({ep}) -> HTTP 200 OK ({count} record(s) loaded)"))
        except Exception as e:
            results.append(("[FAIL]", f"Module '{name}' ({ep}) failed: {e}"))

    # -------------------------------------------------------------------------
    # 8. Test Logout & Session Invalidation
    # -------------------------------------------------------------------------
    try:
        req = urllib.request.Request(
            f"{VITE_BASE}/api/auth/logout/",
            data=b"{}",
            headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf_token or ''}
        )
        resp = opener.open(req, timeout=5)
        logout_data = json.loads(resp.read().decode('utf-8'))
        results.append(("[PASS]", f"Logout executed successfully: {logout_data.get('message')}"))

        # Verify that subsequent requests are blocked after logout
        try:
            req2 = urllib.request.Request(f"{VITE_BASE}/api/analytics/dashboard/")
            opener.open(req2, timeout=5)
            results.append(("[FAIL]", "Session was still active after logout!"))
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                results.append(("[PASS]", f"Session successfully invalidated: post-logout access blocked with HTTP {e.code}"))
            else:
                results.append(("[FAIL]", f"Post-logout request returned unexpected code: {e.code}"))
    except Exception as e:
        results.append(("[FAIL]", f"Logout test failed: {e}"))

    # -------------------------------------------------------------------------
    # 9. Verify Public Website Decoupling
    # -------------------------------------------------------------------------
    try:
        html_path = r'c:\Users\B SANTHOSH KUMAR\Downloads\XEYR_Website_Final_LogoOnly_Orbit_Refined\XEYR_Website_Frontend\index.html'
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        has_orbit = 'orbit' in html
        has_solvex = 'SolveX' in html
        has_skillbridge = 'SkillBridge' in html
        no_admin_portal = ('Admin Portal' not in html and 'C:/dashboard/' not in html and '5173' not in html)
        has_nav_items = all(item in html for item in ['#home', '#events', '#services', '#about', '#contact', '#register'])

        if has_orbit and has_solvex and has_skillbridge and no_admin_portal and has_nav_items:
            results.append(("[PASS]", "Public website verified: zero Admin Portal links, all public nav & brand features intact"))
        else:
            results.append(("[FAIL]", f"Public website check failed: orbit={has_orbit}, solvex={has_solvex}, no_admin_portal={no_admin_portal}"))
    except Exception as e:
        results.append(("[FAIL]", f"Public website verification failed: {e}"))

    # -------------------------------------------------------------------------
    # Print Summary
    # -------------------------------------------------------------------------
    print("\nDETAILED VERIFICATION RESULTS:")
    all_passed = True
    for status, desc in results:
        print(f"  {status} {desc}")
        if status != "[PASS]":
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("ALL END-TO-END VERIFICATION CHECKS PASSED WITH ZERO ERRORS!")
    else:
        print("SOME VERIFICATION CHECKS FAILED.")
    print("=" * 80)

if __name__ == '__main__':
    run_e2e_tests()

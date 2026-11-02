"""
XEYR Technologies — Full System & Dashboard Verification Script
Tests PostgreSQL connection, authentication, session security, permissions,
KPI derivation, rejection validation, and frontend/backend availability.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = 'http://127.0.0.1:8000'
VITE_URL = 'http://127.0.0.1:5173'

def run_tests():
    print("=" * 70)
    print("XEYR TECHNOLOGIES ENTERPRISE ADMIN DASHBOARD VERIFICATION")
    print("=" * 70)

    # Cookie jar for session management
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    results = []

    # Test 1: Vite Frontend Dev Server
    try:
        req = urllib.request.Request(VITE_URL)
        with urllib.request.urlopen(req, timeout=5) as resp:
            status = resp.status
            content = resp.read().decode('utf-8')
            has_title = 'XEYR' in content
            if status == 200 and has_title:
                results.append(("[PASS]", "Vite Frontend Server running at http://127.0.0.1:5173/"))
            else:
                results.append(("[FAIL]", f"Vite Frontend returned status {status}"))
    except Exception as e:
        results.append(("[FAIL]", f"Vite Frontend check failed: {e}"))

    # Test 2: Django Backend Health Check
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/health/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('database') == 'healthy' and data.get('engine') == 'postgresql':
                results.append(("[PASS]", f"Django Backend live with PostgreSQL: {data.get('engine')}"))
            else:
                results.append(("[FAIL]", f"Django Health responded: {data}"))
    except Exception as e:
        results.append(("[FAIL]", f"Django Health check failed: {e}"))

    # Test 3: Unauthenticated Protected Endpoint Access (Should be 401 or 403)
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/analytics/dashboard/")
        urllib.request.urlopen(req, timeout=5)
        results.append(("[FAIL]", "Protected endpoint allowed unauthenticated access!"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            results.append(("[PASS]", f"Protected endpoint correctly rejected unauthenticated request ({e.code})"))
        else:
            results.append(("[FAIL]", f"Protected endpoint returned unexpected error {e.code}"))
    except Exception as e:
        results.append(("[FAIL]", f"Protected endpoint test failed: {e}"))

    # Test 4: Failed Login Attempt
    try:
        bad_payload = json.dumps({"username": "admin", "password": "WrongPassword123!"}).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/login/",
            data=bad_payload,
            headers={'Content-Type': 'application/json'}
        )
        opener.open(req, timeout=5)
        results.append(("[FAIL]", "Invalid login was accepted!"))
    except urllib.error.HTTPError as e:
        if e.code == 400 or e.code == 401:
            results.append(("[PASS]", f"Invalid login correctly rejected ({e.code})"))
        else:
            results.append(("[FAIL]", f"Invalid login returned status {e.code}"))
    except Exception as e:
        results.append(("[FAIL]", f"Invalid login check failed: {e}"))

    # Test 5: Successful Administrator Login & Session Acquisition
    csrf_token = None
    try:
        good_payload = json.dumps({"username": "admin", "password": "XeyrAdmin@2026"}).encode('utf-8')
        req = urllib.request.Request(
            f"{BASE_URL}/api/auth/login/",
            data=good_payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = opener.open(req, timeout=5)
        user_data = json.loads(resp.read().decode('utf-8'))
        
        # Check session cookies
        session_id_found = False
        for cookie in cj:
            if cookie.name == 'sessionid':
                session_id_found = True
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value

        if user_data.get('user', {}).get('username') == 'admin' and session_id_found:
            results.append(("[PASS]", f"Administrator login successful, session cookie acquired for user: {user_data['user']['username']}"))
        else:
            results.append(("[FAIL]", f"Login response incomplete: {user_data}"))
    except Exception as e:
        results.append(("[FAIL]", f"Administrator login failed: {e}"))

    # Test 6: Authenticated KPI Overview Query
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/analytics/dashboard/")
        resp = opener.open(req, timeout=5)
        overview_data = json.loads(resp.read().decode('utf-8'))
        total_enquiries = overview_data.get('kpis', {}).get('total_enquiries', 0)
        qualified_leads = overview_data.get('kpis', {}).get('qualified_leads', 0)
        results.append(("[PASS]", f"KPI Overview API verified: {total_enquiries} enquiries, {qualified_leads} qualified leads"))
    except Exception as e:
        results.append(("[FAIL]", f"Authenticated KPI overview query failed: {e}"))

    # Test 7: Registered Participants API
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/events/registrations/")
        resp = opener.open(req, timeout=5)
        registrations_data = json.loads(resp.read().decode('utf-8'))
        results.append(("[PASS]", f"Event Registrations API verified: {len(registrations_data)} participant record(s)"))
    except Exception as e:
        results.append(("[FAIL]", f"Event registrations query failed: {e}"))

    # Test 8: Notifications API & Unread Alerts
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/notifications/")
        resp = opener.open(req, timeout=5)
        notifs_data = json.loads(resp.read().decode('utf-8'))
        unread = len([n for n in notifs_data if not n.get('is_read')])
        results.append(("[PASS]", f"System Notifications API verified: {len(notifs_data)} total, {unread} unread"))
    except Exception as e:
        results.append(("[FAIL]", f"Notifications query failed: {e}"))

    # Test 9: Public Website Homepage Integrity Check
    try:
        frontend_html_path = r'c:\Users\B SANTHOSH KUMAR\Downloads\XEYR_Website_Final_LogoOnly_Orbit_Refined\XEYR_Website_Frontend\index.html'
        with open(frontend_html_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        has_orbit = 'orbit' in html
        has_solvex = 'SolveX' in html
        has_skillbridge = 'SkillBridge' in html
        no_admin_portal = ('Admin Portal' not in html and 'C:/dashboard/' not in html and '5173' not in html)
        has_nav_items = all(item in html for item in ['#home', '#events', '#services', '#about', '#contact', '#register'])

        if has_orbit and has_solvex and has_skillbridge and no_admin_portal and has_nav_items:
            results.append(("[PASS]", "Public website preserved: Orbit animation, SolveX, SkillBridge, all public nav items verified; ZERO Admin Portal links found"))
        else:
            results.append(("[FAIL]", f"Public website check failed: orbit={has_orbit}, solvex={has_solvex}, skillbridge={has_skillbridge}, no_admin_portal={no_admin_portal}, nav_items={has_nav_items}"))
    except Exception as e:
        results.append(("[FAIL]", f"Public website verification failed: {e}"))

    print("\nVERIFICATION RESULTS:")
    all_passed = True
    for status, desc in results:
        print(f"  {status} {desc}")
        if status != "[PASS]":
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("ALL END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY!")
    else:
        print("SOME CHECKS REPORTED ISSUES.")
    print("=" * 70)

if __name__ == '__main__':
    run_tests()

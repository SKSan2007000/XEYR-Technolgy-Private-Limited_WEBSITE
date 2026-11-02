"""
Test CRM enquiry qualification and rejection validation
"""
import urllib.request
import urllib.parse
import json
import http.cookiejar

BASE_URL = 'http://127.0.0.1:8000'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login
login_payload = json.dumps({"username": "admin", "password": "XeyrAdmin@2026"}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/api/auth/login/", data=login_payload, headers={'Content-Type': 'application/json'})
resp = opener.open(req)

# Get CSRF
csrf_token = ''
for cookie in cj:
    if cookie.name == 'csrftoken':
        csrf_token = cookie.value

headers = {'Content-Type': 'application/json', 'X-CSRFToken': csrf_token}

# 2. Submit a test enquiry
enquiry_data = json.dumps({
    "name": "Validation Test Lead",
    "email": "testlead@example.com",
    "phone": "+91 9876543210",
    "company_name": "Acme Test Corp",
    "service_type": "WEB_DEV",
    "project_title": "Automated Rule Test Project",
    "project_description": "Testing rejection validation and qualification workflows.",
    "budget_range": "INR 50,000 - 1,00,000"
}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/api/enquiries/submit/", data=enquiry_data, headers=headers)
resp = opener.open(req)
created_enquiry = json.loads(resp.read().decode('utf-8'))
ref_id = created_enquiry['reference_id']
print(f"Created Test Enquiry Reference: {ref_id}")

# Fetch enquiry ID from CRM list
req = urllib.request.Request(f"{BASE_URL}/api/enquiries/?q={ref_id}")
resp = opener.open(req)
enquiries_list = json.loads(resp.read().decode('utf-8'))
enquiry_id = enquiries_list[0]['id']
print(f"Retrieved Enquiry Database ID: {enquiry_id}")

# 3. Attempt rejection WITHOUT reason (should fail with 400)
try:
    bad_reject = json.dumps({"category": "BUDGET_MISMATCH", "reason_detail": ""}).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}/api/enquiries/{enquiry_id}/reject/", data=bad_reject, headers=headers)
    opener.open(req)
    print("[FAIL] Rejection without reason was accepted!")
except urllib.error.HTTPError as e:
    if e.code == 400:
        print("[PASS] Rejection without mandatory reason rejected with 400 Bad Request.")
    else:
        print(f"[FAIL] Unexpected error code: {e.code}")

# 4. Attempt rejection WITH reason
good_reject = json.dumps({
    "category": "BUDGET_MISMATCH",
    "reason_detail": "Client budget is below the minimum threshold required for custom engineering."
}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/api/enquiries/{enquiry_id}/reject/", data=good_reject, headers=headers)
resp = opener.open(req)
rej_data = json.loads(resp.read().decode('utf-8'))
enq_obj = rej_data.get('enquiry', {})
rej_obj = rej_data.get('rejection', {})
print(f"[PASS] Rejection with reason succeeded: status is now '{enq_obj.get('status')}', reason recorded: '{rej_obj.get('reason_detail')}'")

# 5. Reopen enquiry
reopen_data = json.dumps({"notes": "Client revised budget up to enterprise tier."}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/api/enquiries/{enquiry_id}/reopen/", data=reopen_data, headers=headers)
resp = opener.open(req)
reopen_res = json.loads(resp.read().decode('utf-8'))
print(f"[PASS] Reopened enquiry: status is now '{reopen_res.get('status')}'")

# 6. Qualify enquiry
qualify_data = json.dumps({
    "estimated_project_value": 150000.00,
    "budget_confirmed": True,
    "timeline_confirmed": True,
    "notes": "Budget and delivery timeline verified by sales lead."
}).encode('utf-8')
req = urllib.request.Request(f"{BASE_URL}/api/enquiries/{enquiry_id}/qualify/", data=qualify_data, headers=headers)
resp = opener.open(req)
qual_res = json.loads(resp.read().decode('utf-8'))
print(f"[PASS] Qualified enquiry: status is now '{qual_res.get('status')}', estimated value: Rs. {qual_res.get('estimated_project_value')}")

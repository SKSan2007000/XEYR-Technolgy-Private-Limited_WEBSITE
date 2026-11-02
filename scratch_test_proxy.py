"""
Test Vite dev server proxy forwarding to Django backend
"""
import urllib.request
import json
import http.cookiejar

VITE_URL = 'http://127.0.0.1:5173'
VITE_LOCALHOST = 'http://localhost:5173'

def test_proxy(base_url):
    print(f"\nTesting Proxy via {base_url}/api/health/ ...")
    try:
        req = urllib.request.Request(f"{base_url}/api/health/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"  [SUCCESS] {base_url}/api/health/ returned: {data}")
    except Exception as e:
        print(f"  [FAIL] {base_url}/api/health/ error: {e}")

    print(f"\nTesting Login via {base_url}/api/auth/login/ ...")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        payload = json.dumps({"username": "admin", "password": "XeyrAdmin@2026"}).encode('utf-8')
        req = urllib.request.Request(
            f"{base_url}/api/auth/login/",
            data=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp = opener.open(req, timeout=5)
        data = json.loads(resp.read().decode('utf-8'))
        cookies = [c.name for c in cj]
        print(f"  [SUCCESS] Login returned message: '{data.get('message')}', cookies received: {cookies}")

        # Now test protected request through proxy with cookies
        print(f"Testing Protected Request via {base_url}/api/analytics/dashboard/ ...")
        req2 = urllib.request.Request(f"{base_url}/api/analytics/dashboard/")
        resp2 = opener.open(req2, timeout=5)
        data2 = json.loads(resp2.read().decode('utf-8'))
        print(f"  [SUCCESS] Protected endpoint returned data! kpis={list(data2.get('kpis', {}).keys())}")
    except Exception as e:
        print(f"  [FAIL] Login error: {e}")

if __name__ == '__main__':
    test_proxy(VITE_URL)
    test_proxy(VITE_LOCALHOST)

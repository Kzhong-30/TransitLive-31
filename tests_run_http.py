"""Full HTTP API test suite - 23 cases including happy + error paths."""
import sys
import os
import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000/api"
PASS = 0
FAIL = 0
FAILURES = []


def test(name, url, method="GET", data=None, expect_status=None):
    global PASS, FAIL
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
            req.data = json.dumps(data).encode()
        with urllib.request.urlopen(req) as r:
            body = json.loads(r.read())
            if expect_status and r.status != expect_status:
                raise AssertionError(f"status {r.status} != expected {expect_status}")
            PASS += 1
            print(f"  [PASS] {name}")
            return body
    except urllib.error.HTTPError as e:
        if expect_status and e.code == expect_status:
            PASS += 1
            print(f"  [PASS] {name} (HTTP {e.code} as expected)")
            return None
        FAIL += 1
        FAILURES.append((name, f"HTTP {e.code}: {e.read().decode()[:100]}"))
        print(f"  [FAIL] {name} HTTP {e.code}")
        return None
    except Exception as e:
        FAIL += 1
        FAILURES.append((name, f"{type(e).__name__}: {e}"))
        print(f"  [FAIL] {name} {type(e).__name__}: {e}")
        return None


print("=" * 60)
print("HTTP API TEST SUITE (23 tests)")
print("=" * 60)

print("\n--- Happy paths (12) ---")
r = test("T01 GET /stocks list", f"{BASE}/stocks")
assert isinstance(r, list) and len(r) == 15, "stock count mismatch"
test("T02 GET /stocks/AAPL/quote", f"{BASE}/stocks/AAPL/quote")
test("T03 GET /stocks/600519/depth (A-share)", f"{BASE}/stocks/600519/depth")
test("T04 Kline interval=1m", f"{BASE}/stocks/AAPL/history?interval=1m&limit=3")
test("T05 Kline interval=1d", f"{BASE}/stocks/AAPL/history?interval=1d&limit=3")
test("T06 Kline interval=1w", f"{BASE}/stocks/AAPL/history?interval=1w&limit=3")
test("T07 Kline interval=1M (month)", f"{BASE}/stocks/AAPL/history?interval=1M&limit=3")
test("T08 Kline limit=1 (min)", f"{BASE}/stocks/AAPL/history?limit=1")
test("T09 Kline limit=500 (max)", f"{BASE}/stocks/AAPL/history?limit=500")
alert = test("T10 POST create alert (gt)", f"{BASE}/alerts", "POST",
             {"symbol":"AAPL","condition":"gt","target_price":99999,"user_id":"test","note":"never"})
assert isinstance(alert, dict) and "id" in alert, "alert create response missing id"
test("T11 GET alerts list", f"{BASE}/alerts")
test("T12 DELETE created alert", f"{BASE}/alerts/{alert['id']}", "DELETE")

print("\n--- Error / boundary paths (11) ---")
test("E01 Unknown symbol quote -> 404", f"{BASE}/stocks/INVALID/quote", expect_status=404)
test("E02 Unknown symbol history -> 404", f"{BASE}/stocks/INVALID/history", expect_status=404)
test("E03 Unknown symbol depth -> 404", f"{BASE}/stocks/INVALID/depth", expect_status=404)
test("E04 Invalid interval -> 422", f"{BASE}/stocks/AAPL/history?interval=nope", expect_status=422)
test("E05 limit=501 out of range -> 422", f"{BASE}/stocks/AAPL/history?limit=501", expect_status=422)
test("E06 limit=0 invalid -> 422", f"{BASE}/stocks/AAPL/history?limit=0", expect_status=422)
test("E07 Alert bad symbol -> 404", f"{BASE}/alerts", "POST",
     {"symbol":"XXX","condition":"gt","target_price":10,"user_id":"u1"}, expect_status=404)
test("E08 Alert negative price -> 422", f"{BASE}/alerts", "POST",
     {"symbol":"AAPL","condition":"gt","target_price":-5,"user_id":"u1"}, expect_status=422)
test("E09 Alert zero price -> 422", f"{BASE}/alerts", "POST",
     {"symbol":"AAPL","condition":"gt","target_price":0,"user_id":"u1"}, expect_status=422)
test("E10 Alert missing fields -> 422", f"{BASE}/alerts", "POST",
     {"symbol":"AAPL"}, expect_status=422)
test("E11 Delete nonexistent alert -> 404", f"{BASE}/alerts/fake_id_123", "DELETE", expect_status=404)

total = PASS + FAIL
print("\n" + "=" * 60)
print(f"HTTP RESULT: {PASS}/{total} passed" + ("  OK" if FAIL == 0 else "  FAILURES:"))
if FAILURES:
    for n, r in FAILURES:
        print(f"  - {n}: {r}")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)

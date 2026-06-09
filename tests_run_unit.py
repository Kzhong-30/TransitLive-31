"""Pure-function unit tests (no HTTP/WS/IO needed for core logic).

Covers: random walk bounds, Kline schema/limit enforcement, order book 5-level depth,
alert condition evaluation (gt/lt), exceptiongroup batch semantics, Self typing.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

PASS = 0
FAIL = 0
FAILURES = []


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  [FAIL] {name}" + (f"  -> {detail}" if detail else ""))


print("=" * 60)
print("PURE-FUNCTION UNIT TESTS (no network required)")
print("=" * 60)

# --- Random walk tests ---
print("\n--- Random walk (4) ---")
from app.services.stock_service import StockDataService

svc = StockDataService.__new__(StockDataService)
svc._stock_state = {}
svc._alerts = {}
svc._alert_callbacks = []

rw = svc._random_walk
# T1 always > 0.01 even with huge volatility
results = [rw(1.0, 1000.0) for _ in range(1000)]
check("U01 Random walk never negative", all(x > 0 for x in results),
      f"min={min(results):.6f}")
check("U02 Random walk bounded floor at 0.01", all(x >= 0.01 for x in results))
# T2 deterministic-ish: same seed reproduces (monotonic contract check)
import random
random.seed(42)
v1 = rw(100.0, 0.01)
random.seed(42)
v2 = rw(100.0, 0.01)
check("U03 Random walk reproducible given seed", abs(v1 - v2) < 1e-10, f"v1={v1} v2={v2}")
check("U04 Zero volatility => near-zero change", abs(rw(50.0, 0.0) - 50.0) < 1e-9)

# --- Kline tests ---
print("\n--- Kline generation (6) ---")
svc._stock_state["TEST"] = {"base_price": 100.0, "current_price": 100.0, "volatility": 0.005}
from app.core.models import KlineInterval

k1m = svc.generate_kline_history("TEST", KlineInterval.MINUTE, 3)
check("U05 Minute kline count respects limit", len(k1m) == 3, f"got {len(k1m)}")
k1d = svc.generate_kline_history("TEST", KlineInterval.DAY, 10)
check("U06 Day kline count respects limit", len(k1d) == 10, f"got {len(k1d)}")
check("U07 Kline record OHLCV schema complete",
      all(hasattr(r, "time") and hasattr(r, "open") and hasattr(r, "high")
          and hasattr(r, "low") and hasattr(r, "close") and hasattr(r, "volume")
          for r in k1d))
check("U08 High >= max(open, close) and Low <= min(open, close)",
      all(r.high >= max(r.open, r.close) and r.low <= min(r.open, r.close) for r in k1d))
check("U09 Volume is positive integer", all(isinstance(r.volume, int) and r.volume > 0 for r in k1d + k1m))
k_cap = svc.generate_kline_history("TEST", KlineInterval.MINUTE, 99999)
check("U10 Minute kline cap at 240 (not unbounded)", len(k_cap) == 240, f"got {len(k_cap)}")

# --- Order book tests ---
print("\n--- Order book (5) ---")
svc._stock_state["BOOK"] = {"current_price": 100.0}
ob = svc.generate_order_book("BOOK")
check("U11 Symbol match", ob.symbol == "BOOK")
check("U12 Exactly 5 bid levels", len(ob.bids) == 5)
check("U13 Exactly 5 ask levels", len(ob.asks) == 5)
check("U14 Bids strictly descending (proper ladder)",
      all(ob.bids[i].price > ob.bids[i + 1].price for i in range(4)))
check("U15 Asks strictly ascending (proper ladder)",
      all(ob.asks[i].price < ob.asks[i + 1].price for i in range(4)))

# --- Unknown symbol errors ---
print("\n--- Symbol validation (2) ---")
try:
    svc.generate_order_book("NOPE")
    check("U16 Unknown orderbook raises", False, "no exception!")
except ValueError:
    check("U16 Unknown orderbook raises ValueError", True)
try:
    import asyncio
    asyncio.run(svc.generate_quote("NOPE"))
    check("U17 Unknown quote raises", False, "no exception!")
except ValueError:
    check("U17 Unknown quote raises ValueError", True)

# --- Alert condition logic ---
print("\n--- Alert condition evaluation (7) ---")
svc._alerts = {}
svc._stock_state["ALGO"] = {"base_price": 50.0, "current_price": 50.0, "volatility": 0.001,
                            "prev_close": 50.0, "open_price": 50.0, "high_price": 50.0,
                            "low_price": 50.0, "volume": 1000}
import uuid

def make_alert(symbol, condition, target, uid="tester"):
    aid = f"alert_{uuid.uuid4().hex[:10]}"
    from app.core.models import Alert
    svc._alerts[aid] = Alert(id=aid, symbol=symbol, condition=condition,
                              target_price=target, user_id=uid, note="",
                              created_at="", triggered=False)
    return aid

aid_gt_hit = make_alert("ALGO", "gt", 40.0)  # current=50 >= 40 => triggers
aid_gt_miss = make_alert("ALGO", "gt", 60.0)  # no trigger
aid_lt_hit = make_alert("ALGO", "lt", 60.0)   # 50 <= 60 => triggers
aid_lt_miss = make_alert("ALGO", "lt", 40.0)  # no trigger
aid_eq_edge = make_alert("ALGO", "gt", 50.0)  # 50 >= 50 => triggers exactly

callback_called = []
async def fake_cb(n):
    callback_called.append(n.alert_id)
svc._alert_callbacks = [fake_cb]

asyncio.run(svc._check_alerts("ALGO", 50.0))

check("U18 gt triggers when current >= target", svc._alerts[aid_gt_hit].triggered)
check("U19 gt does NOT trigger below target", not svc._alerts[aid_gt_miss].triggered)
check("U20 lt triggers when current <= target", svc._alerts[aid_lt_hit].triggered)
check("U21 lt does NOT trigger above target", not svc._alerts[aid_lt_miss].triggered)
check("U22 Edge equality triggers correctly", svc._alerts[aid_eq_edge].triggered)
check("U23 Callback invoked 3 times (once per triggered)", len(callback_called) == 3,
      f"called={len(callback_called)} ids={callback_called}")
_ = asyncio.run(svc._check_alerts("ALGO", 50.0))
check("U24 Triggered alerts fire exactly once (recheck same price)",
      len(callback_called) == 3,
      "same-price recheck didn't increase callback count")

# --- ExceptionGroup correct usage (raise, not raise+catch in same scope) ---
print("\n--- ExceptionGroup semantics (3) ---")
from exceptiongroup import ExceptionGroup

def batch_divide(nums):
    errs = []
    for n in nums:
        try:
            1 / n
        except Exception as e:
            errs.append(e)
    if errs:
        raise ExceptionGroup("batch divide errors", errs)
    return True

try:
    batch_divide([1, 2, 0, 3, 0])
    check("U25 ExceptionGroup raises on errors", False, "no group raised")
except ExceptionGroup as eg:
    check("U25 ExceptionGroup aggregates multiple errors",
          len(eg.exceptions) == 2, f"sub_errors={len(eg.exceptions)}")

# Not in same scope: caller handles, not the function itself
try:
    batch_divide([1, 2, 3])
    check("U26 Clean batch => no exception raised", True)
except Exception:
    check("U26 Clean batch => no exception raised", False, "unexpected exception")

# --- typing_extensions Self ---
print("\n--- Self typing singleton contract (2) ---")
inst_a = StockDataService()
inst_b = StockDataService()
check("U27 Singleton via Self annotated __new__", inst_a is inst_b)
check("U28 isinstance matches Self return type", isinstance(inst_a, StockDataService))

total = PASS + FAIL
print("\n" + "=" * 60)
print(f"UNIT TEST RESULT: {PASS}/{total} passed" + ("  OK" if FAIL == 0 else "  FAILED:"))
if FAILURES:
    for f in FAILURES:
        print(f"  - {f}")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)

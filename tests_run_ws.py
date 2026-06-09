"""WebSocket E2E tests - 16 cases including broadcast lifecycle validation."""
import sys
import os
import asyncio
import json
import time
import urllib.request

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

WS_URL = "ws://localhost:8000/ws"
HEALTH_URL = "http://localhost:8000/health"
PASS = 0
FAIL = 0
FAILURES = []


def mark(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAIL += 1
        FAILURES.append(name)
        print(f"  [FAIL] {name}" + (f"  -> {detail}" if detail else ""))


def create_alert(symbol, user_id, target=0.01, cond="gt"):
    url = "http://localhost:8000/api/alerts"
    data = json.dumps({"symbol": symbol, "condition": cond, "target_price": target,
                       "user_id": user_id, "note": "WS_TEST"}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["id"]


def health():
    with urllib.request.urlopen(HEALTH_URL) as r:
        return json.loads(r.read())["components"]



async def run_all():
    print("=" * 60)
    print("WebSocket E2E + LIFECYCLE TEST SUITE (16 tests)")
    print("=" * 60)

    # --- Basic 6 tests ---
    print("\n--- Basic connect / subscribe / unsubscribe / invalid (6) ---")
    try:
        async with websockets.connect(WS_URL, close_timeout=2) as ws:
            await ws.send(json.dumps({"type": "ping"}))
            r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            mark("T01 Connect + ping/pong", r.get("type") == "pong")
    except Exception as e:
        mark("T01 Connect + ping/pong", False, str(e))

    try:
        async with websockets.connect(WS_URL, close_timeout=2) as ws:
            await ws.send(json.dumps({"type": "subscribe", "symbols": ["AAPL", "TSLA", "BADX"]}))
            r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            subs = r.get("symbols", [])
            mark("T02 Sub valid+invalid filters bad",
                 r.get("type") == "subscribed" and "AAPL" in subs and "TSLA" in subs and "BADX" not in subs,
                 f"subs={subs}")
    except Exception as e:
        mark("T02 Sub filter", False, str(e))

    try:
        async with websockets.connect(WS_URL, close_timeout=2) as ws:
            await ws.send(json.dumps({"type": "subscribe", "symbols": ["AAPL", "600519"]}))
            await asyncio.wait_for(ws.recv(), timeout=5)
            t0 = time.time()
            quotes = []
            try:
                for _ in range(12):
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=2.2))
                    if m.get("type") == "quote":
                        quotes.append(m["data"])
                        if len(quotes) >= 4:
                            break
            except asyncio.TimeoutError:
                pass
            elapsed = time.time() - t0
            syms = set(q["symbol"] for q in quotes)
            mark("T03 1s push loop timing OK",
                 len(quotes) >= 3 and elapsed < 5.0,
                 f"{len(quotes)} quotes in {elapsed:.1f}s symbols={syms}")
            required = {"symbol", "price", "open", "high", "low", "volume", "change", "change_percent", "timestamp"}
            if quotes:
                mark("T04 Quote schema (9 fields + types)",
                     required.issubset(set(quotes[0].keys()))
                     and isinstance(quotes[0]["price"], (int, float))
                     and isinstance(quotes[0]["volume"], int),
                     f"keys={list(quotes[0].keys())}")
    except Exception as e:
        mark("T03 Push timing", False, str(e))
        mark("T04 Quote schema", False, str(e))

    try:
        async with websockets.connect(WS_URL, close_timeout=2) as ws:
            await ws.send(json.dumps({"type": "subscribe", "symbols": ["TSLA"]}))
            await asyncio.wait_for(ws.recv(), timeout=5)
            await ws.send(json.dumps({"type": "unsubscribe", "symbols": ["TSLA"]}))
            r = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            mark("T05 Unsubscribe reply", r.get("type") == "unsubscribed")
            got = False
            try:
                for _ in range(4):
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.8))
                    if m.get("type") == "quote" and m["data"]["symbol"] == "TSLA":
                        got = True
            except asyncio.TimeoutError:
                pass
            mark("T06 Silence after unsubscribe", not got, "(no TSLA quotes after unsub)")
    except Exception as e:
        mark("T05 Unsubscribe", False, str(e))
        mark("T06 Silence", False, str(e))

    # --- Invalid messages ---
    print("\n--- Invalid message handling (2) ---")
    try:
        async with websockets.connect(WS_URL, close_timeout=2) as ws:
            await ws.send("NOT JSON AT ALL!!!")
            r1 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            await ws.send(json.dumps({"type": "nonexistent_xyz"}))
            r2 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            await ws.send(json.dumps({"no_type_field": True}))
            r3 = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
            mark("T07 Bad JSON handled", r1.get("type") == "error")
            mark("T08 Unknown type + missing type handled",
                 r2.get("type") == "error" and r3.get("type") == "error",
                 f"unknown={r2.get('message')[:40]} missing={r3.get('message')[:40]}")
    except Exception as e:
        mark("T07 Bad JSON", False, str(e))
        mark("T08 Unknown/missing type", False, str(e))

    # --- Alert notification via WS (1) ---
    print("\n--- Alert trigger + WS push (1) ---")
    aid = create_alert("NVDA", user_id="ws_lifecycle")
    try:
        alerts_seen = 0
        async with websockets.connect(WS_URL + "?user_id=ws_lifecycle", close_timeout=2) as ws:
            await ws.send(json.dumps({"type": "subscribe", "symbols": ["NVDA"]}))
            await asyncio.wait_for(ws.recv(), timeout=5)
            t0 = time.time()
            try:
                while time.time() - t0 < 5 and alerts_seen < 1:
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                    if m.get("type") == "alert":
                        alerts_seen += 1
                        mark("T09 Alert WS notification schema+ID",
                             all(k in m for k in ("alert_id", "symbol", "condition", "target_price",
                                                   "current_price", "timestamp"))
                             and m.get("alert_id") == aid,
                             f"id_match={m.get('alert_id')==aid} fields={list(m.keys())}")
            except asyncio.TimeoutError:
                pass
        if alerts_seen == 0:
            mark("T09 Alert WS notification", False, "no alert notification received in 5s")
    except Exception as e:
        mark("T09 Alert WS notification", False, str(e))

    # --- Broadcast lifecycle tests (7 new) ---
    print("\n--- Broadcast lifecycle task management (7) ---")

    # T10: before any connection, no task running
    try:
        import random
        h = health()
        mark("T10 Idle state: no running task initially",
             not h["broadcast_running"] and h["websocket_connections"] == 0,
             f"running={h['broadcast_running']} conns={h['websocket_connections']}")
    except Exception as e:
        mark("T10 Idle pre-check", False, str(e))

    # T11: after 1 connect, task starts
    try:
        ws1 = await asyncio.wait_for(websockets.connect(WS_URL, close_timeout=2), timeout=5)
        ws1 = ws1[0] if isinstance(ws1, tuple) else ws1
        await ws1.send(json.dumps({"type": "subscribe", "symbols": ["MSFT"]}))
        await asyncio.wait_for(ws1.recv(), timeout=5)
        await asyncio.sleep(0.4)
        h = health()
        task_id_1 = h["broadcast_task_id"]
        mark("T11 After connect: broadcast task starts",
             h["broadcast_running"] and h["websocket_connections"] >= 1,
             f"running={h['broadcast_running']} conns={h['websocket_connections']} task={task_id_1}")
    except Exception as e:
        mark("T11 Start task on connect", False, str(e))
        ws1 = None
        task_id_1 = None

    # T12: task object is same while active
    try:
        ws2 = await asyncio.wait_for(websockets.connect(WS_URL, close_timeout=2), timeout=5)
        ws2 = ws2[0] if isinstance(ws2, tuple) else ws2
        await ws2.send(json.dumps({"type": "subscribe", "symbols": ["GOOGL"]}))
        await asyncio.wait_for(ws2.recv(), timeout=5)
        await asyncio.sleep(0.3)
        h = health()
        task_id_2 = h["broadcast_task_id"]
        mark("T12 Concurrent shares same task (no double-start)",
             task_id_1 == task_id_2 and h["websocket_connections"] == 2,
             f"task_ids_equal={task_id_1==task_id_2} conns={h['websocket_connections']}")
    except Exception as e:
        mark("T12 No double task creation", False, str(e))
        ws2 = None

    # T13: disconnect 1 of 2 keeps task running
    try:
        if ws2:
            await ws2.close()
        await asyncio.sleep(0.5)
        h = health()
        mark("T13 Disconnect 1/2 keeps task alive",
             h["broadcast_running"] and h["websocket_connections"] == 1,
             f"running={h['broadcast_running']} conns={h['websocket_connections']}")
    except Exception as e:
        mark("T13 Partial disconnect keeps task", False, str(e))

    # T14: disconnect last connection cancels task
    try:
        if ws1:
            await ws1.close()
        await asyncio.sleep(0.8)
        h = health()
        mark("T14 Disconnect last => task cancelled (lifecycle core fix)",
             not h["broadcast_running"] and h["websocket_connections"] == 0,
             f"running={h['broadcast_running']} conns={h['websocket_connections']}")
    except Exception as e:
        mark("T14 Zero-connections cancels task", False, str(e))

    # T15: reconnect after full disconnect restarts task with NEW task id
    try:
        ws3 = await asyncio.wait_for(websockets.connect(WS_URL, close_timeout=2), timeout=5)
        ws3 = ws3[0] if isinstance(ws3, tuple) else ws3
        await ws3.send(json.dumps({"type": "subscribe", "symbols": ["JPM"]}))
        await asyncio.wait_for(ws3.recv(), timeout=5)
        await asyncio.sleep(0.4)
        h = health()
        mark("T15 Reconnect => NEW task spawns (restart works)",
             h["broadcast_running"] and h["websocket_connections"] == 1
             and h["broadcast_task_id"] != task_id_1,
             f"running={h['broadcast_running']} new_task={h['broadcast_task_id'] != task_id_1}")
        # cleanup
        await ws3.close()
        await asyncio.sleep(0.5)
    except Exception as e:
        mark("T15 Reconnect restarts task", False, str(e))

    # T16: final sanity - idle after all disconnects
    try:
        await asyncio.sleep(0.3)
        h = health()
        mark("T16 Final idle state (conns=0 running=False)",
             not h["broadcast_running"] and h["websocket_connections"] == 0,
             f"running={h['broadcast_running']} conns={h['websocket_connections']}")
    except Exception as e:
        mark("T16 Final idle check", False, str(e))


    total = PASS + FAIL
    print("\n" + "=" * 60)
    print(f"WS RESULT: {PASS}/{total} passed" + ("  OK" if FAIL == 0 else "  FAILED:"))
    if FAILURES:
        for f in FAILURES:
            print(f"  - {f}")
    print("=" * 60)
    return FAIL == 0

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    ok = asyncio.run(run_all())
    sys.exit(0 if ok else 1)

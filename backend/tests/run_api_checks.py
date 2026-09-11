"""API contract checks over the full app (TestClient, no server needed):
    cd backend && .venv/Scripts/python.exe tests/run_api_checks.py
Runs with no keys and no Mongo -> exercises template fallback + memory store,
i.e. exactly the venue-wifi-died configuration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

import fixtures as FX  # noqa: E402
import main  # noqa: E402

c = TestClient(main.app)
P = 0


def ok(name, cond):
    global P
    print(("ok  " if cond else "FAIL"), name)
    if not cond:
        sys.exit(f"FAILED: {name}")
    P += 1


h = c.get("/api/health").json()
ok("health", h["ok"] is True and h["store"] in ("memory", "atlas"))

# beat 1 — full check shape per CONTRACTS
r = c.post("/api/check", json={"type": "text", "payload": FX.KYC_SCAM_TEXT}).json()
ok("check verdict danger", r["verdict"] == "danger" and r["score"] >= 60)
ok("check shape", all(k in r for k in (
    "_id", "input", "verdict", "score", "signals", "explanation_hi",
    "explanation_en", "scam_category", "tts_audio_b64", "mocked", "created_at")))
ok("explanations non-empty", bool(r["explanation_hi"]) and bool(r["explanation_en"]))
ok("llm has zero verdict weight",
   sum(s["weight"] for s in r["signals"] if s["source"] == "llm_pattern") == 0)

# contrast beat — legit SMS stays clean
r3 = c.post("/api/check", json={"type": "text", "payload": FX.LEGIT_BANK_TEXT}).json()
ok("legit SMS no_known_risk", r3["verdict"] == "no_known_risk" and r3["signals"] == [])

# flywheel — report -> verify -> instant danger, count increments
num = "+919899000111"
pre = c.post("/api/check", json={"type": "text", "payload": num}).json()
rep = c.post("/api/reports", json={"payload": num, "category": "customer_care",
                                   "note": "", "city": "Jaipur"}).json()
pend = c.get("/api/reports?status=pending").json()["reports"]
ver = c.post(f"/api/reports/{rep['_id']}/verify", json={"action": "verify"}).json()
post = c.post("/api/check", json={"type": "text",
                                  "payload": f"is number se call aaya {num}"}).json()
ok("flywheel", pre["verdict"] == "no_known_risk" and ver["status"] == "verified"
   and post["verdict"] == "danger"
   and any(s["id"] == "community_blocklist" for s in post["signals"]))
ok("pending queue served", any(x["_id"] == rep["_id"] for x in pend))

# second verified report on same number increments the indicator
rep2 = c.post("/api/reports", json={"payload": num, "category": "customer_care",
                                    "note": "", "city": "Kota"}).json()
c.post(f"/api/reports/{rep2['_id']}/verify", json={"action": "verify"})
tr = c.get("/api/intel/trends").json()
counts = {i["value"]: i["report_count"] for i in tr["top_indicators"]}
ok("indicator upsert increments", counts.get(num) == 2)
ok("trends totals", tr["total_reports"] == FX.SEED_TRENDS["total_reports"] + 2
   and tr["live_reports"] == 2)
cat = {x["category"]: x["count"] for x in tr["by_category"]}
city = {x["city"]: x["count"] for x in tr["cities"]}
base_cat = {x["category"]: x["count"] for x in FX.SEED_TRENDS["by_category"]}
base_city = {x["city"]: x["count"] for x in FX.SEED_TRENDS["cities"]}
ok("trends category overlay", cat["customer_care"] == base_cat["customer_care"] + 2)
ok("trends city overlay", city["Jaipur"] == base_city["Jaipur"] + 1
   and city["Kota"] == base_city["Kota"] + 1)
ok("trends today bumped", tr["by_day"][-1]["count"]
   == FX.SEED_TRENDS["by_day"][-1]["count"] + 2
   or tr["by_day"][-1]["count"] == 2)  # holds even when demo day != fixture window

# guardian loop: pair -> danger check with ward link -> pending -> block -> ward sees it
gl = c.post("/api/guardian/links", json={"ward_name": "Sunita Devi",
                                         "guardian_name": "Rahul"}).json()
ok("pair code", gl["pair_code"].startswith("DHAAL-"))
chk = c.post("/api/check", json={"type": "qr_text", "payload": FX.QR_COLLECT_URI,
                                 "ward_link_id": gl["_id"]}).json()
grid = chk.get("guardian_request_id")
ok("guardian request auto-created", bool(grid))
inbox = c.get(f"/api/guardian/requests?link_id={gl['_id']}").json()["requests"]
ok("guardian inbox", any(x["_id"] == grid and x["status"] == "pending" for x in inbox))
dec = c.post(f"/api/guardian/requests/{grid}/decision",
             json={"decision": "blocked", "note": "beta, mat bhejo"}).json()
ward = c.get(f"/api/guardian/requests/{grid}").json()
ok("guardian decision persists", dec["status"] == "blocked"
   and ward["status"] == "blocked" and ward["guardian_note"] == "beta, mat bhejo")

# no-risk check with ward link must NOT ping the guardian
chk2 = c.post("/api/check", json={"type": "text", "payload": FX.LEGIT_BANK_TEXT,
                                  "ward_link_id": gl["_id"]}).json()
ok("no guardian ping on clean check", "guardian_request_id" not in chk2)

# recovery kit template path
kit = c.post("/api/recovery/kit", json={"what": "paid", "amount": 15000,
                                        "channel": "upi", "bank": "SBI"}).json()
ok("recovery kit", "1930" in kit["call_script_1930"] and len(kit["checklist"]) >= 4)

# transcribe typed fallback
t = c.post("/api/transcribe", json={"typed_text": "hello", "lang_hint": "hi-IN"}).json()
ok("transcribe typed fallback", t["transcript"] == "hello")

print(f"\nALL {P} API CHECKS PASSED (store={h['store']})")

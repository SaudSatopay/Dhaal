"""API contract checks over the full app (TestClient, no server needed):
    cd backend && .venv/Scripts/python.exe tests/run_api_checks.py
Runs with no keys and no Mongo -> exercises template fallback + memory store,
i.e. exactly the venue-wifi-died configuration.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Pin the offline configuration BEFORE importing main — this suite must stay
# deterministic even when .env carries live keys (set-but-empty beats dotenv).
for var in ("MONGODB_URI", "ANTHROPIC_API_KEY", "SARVAM_API_KEY"):
    os.environ[var] = ""
os.environ["MOCK_MODE"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

import fixtures as FX  # noqa: E402
import main  # noqa: E402

# main's dotenv load pulls the real MOD_KEY into this process — moderation auth
# is asserted explicitly below; every other check runs with the gate open.
os.environ["MOD_KEY"] = ""

c = TestClient(main.app)

# --- moderation gate (H12): key required when MOD_KEY is set ---
os.environ["MOD_KEY"] = "test-mod-key"
r_noauth = c.get("/api/reports?status=pending")
r_auth = c.get("/api/reports?status=pending", headers={"X-Mod-Key": "test-mod-key"})
os.environ["MOD_KEY"] = ""
def _ok0(name, cond):  # local ok() is defined later; assert directly here
    if not cond:
        print(f"FAILED: {name}")
        sys.exit(1)
    print(f"ok   {name}")
_ok0("moderation 401 without key", r_noauth.status_code == 401)
_ok0("moderation 200 with key", r_auth.status_code == 200 and "reports" in r_auth.json())
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
             json={"decision": "blocked", "note": "beta, mat bhejo", "link_id": gl["_id"]}).json()
ward = c.get(f"/api/guardian/requests/{grid}").json()
ok("guardian decision persists", dec["status"] == "blocked"
   and ward["status"] == "blocked" and ward["guardian_note"] == "beta, mat bhejo")

# contract v2 (H11, PO): EVERY ward check reaches the guardian — clean ones as
# informational "noted" rows (no decision needed), risky ones stay "pending".
chk2 = c.post("/api/check", json={"type": "text", "payload": FX.LEGIT_BANK_TEXT,
                                  "ward_link_id": gl["_id"]}).json()
gr2 = c.get(f"/api/guardian/requests/{chk2.get('guardian_request_id', 'missing')}").json()
ok("clean ward check appears as 'noted'", "guardian_request_id" in chk2
   and gr2.get("status") == "noted" and gr2.get("verdict") == "no_known_risk")

# resolve-by-code: exact, lowercase, bare code, unknown
code = gl["pair_code"]
r1 = c.get(f"/api/guardian/links/resolve?pair_code={code}").json()
r2 = c.get(f"/api/guardian/links/resolve?pair_code={code.lower()}").json()
r3 = c.get(f"/api/guardian/links/resolve?pair_code={code.split('-', 1)[1]}").json()
r4 = c.get("/api/guardian/links/resolve?pair_code=DHAAL-ZZZZ").json()
ok("resolve by pair code", r1.get("_id") == gl["_id"] and r2.get("_id") == gl["_id"]
   and r3.get("_id") == gl["_id"] and r4 == {"error": "code not found"})

# recovery kit template path
kit = c.post("/api/recovery/kit", json={"what": "paid", "amount": 15000,
                                        "channel": "upi", "bank": "SBI"}).json()
ok("recovery kit", "1930" in kit["call_script_1930"] and len(kit["checklist"]) >= 4)

# transcribe typed fallback
t = c.post("/api/transcribe", json={"typed_text": "hello", "lang_hint": "hi-IN"}).json()
ok("transcribe typed fallback", t["transcript"] == "hello")

# transcribe multipart with no Sarvam key -> fixture transcript, mocked: true
t2 = c.post("/api/transcribe",
            files={"audio": ("clip.webm", b"\x1aE\xdf\xa3fake-webm-bytes", "audio/webm")},
            data={"lang_hint": "hi-IN"}).json()
ok("transcribe multipart fallback", t2["transcript"] == FX.DIGITAL_ARREST_TRANSCRIPT
   and t2["mocked"] is True)

# speak:true offline -> null audio, never an error
spk = c.post("/api/check", json={"type": "text", "payload": FX.KYC_SCAM_TEXT,
                                 "speak": True}).json()
ok("speak offline yields null audio", spk["verdict"] == "danger"
   and spk["tts_audio_b64"] is None)

# --- H12 external review: decision auth + verification reversal ---
gr_noauth = c.post(f"/api/guardian/requests/{ward['_id']}/decision",
                   json={"decision": "allowed", "note": "", "link_id": "gl_wrong"})
ok("guardian decision rejects wrong link_id", gr_noauth.status_code == 403)

rev = c.post("/api/reports", json={"payload": "+919999888771", "category": "digital_arrest",
                                   "note": "", "city": "Jaipur"}).json()
os.environ["MOD_KEY"] = ""
c.post(f"/api/reports/{rev['_id']}/verify", json={"action": "verify"})
c.post(f"/api/reports/{rev['_id']}/verify", json={"action": "verify"})  # idempotent
chk_a = c.post("/api/check", json={"type": "text", "payload": "+919999888771"}).json()
one_hit = [s for s in chk_a["signals"] if s["id"] == "community_blocklist"]
ok("verified once despite double-verify", bool(one_hit) and "1" in one_hit[0]["title_en"])
c.post(f"/api/reports/{rev['_id']}/verify", json={"action": "reject"})  # withdraw
chk_b = c.post("/api/check", json={"type": "text", "payload": "+919999888771"}).json()
ok("rejecting a verified report withdraws it",
   not any(s["id"] == "community_blocklist" for s in chk_b["signals"]))

print(f"\nALL {P} API CHECKS PASSED (store={h['store']})")

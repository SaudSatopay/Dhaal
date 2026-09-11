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
ok("flywheel", pre["assessment"] == "needs_context" and pre["verdict"] is None
   and ver["status"] == "verified" and post["verdict"] == "danger"
   and any(s["id"] == "community_blocklist" for s in post["signals"]))
ok("pending queue served", any(x["_id"] == rep["_id"] for x in pend))

# second verified report on same number increments the indicator
rep2 = c.post("/api/reports", json={"payload": num, "category": "customer_care",
                                    "note": "", "city": "Kota"}).json()
c.post(f"/api/reports/{rep2['_id']}/verify", json={"action": "verify"})
tr = c.get("/api/intel/trends").json()
counts = {i["value"]: i["report_count"] for i in tr["top_indicators"]}
# H14: phone indicators live in canonical last-10 form ('+91 98…' == '98…')
ok("indicator upsert increments (canonical)", counts.get("9899000111") == 2)
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

# guardian loop (H14 token model): create -> ward claims code -> danger check
# with ward TOKEN -> pending -> guardian TOKEN blocks -> ward sees it
gl = c.post("/api/guardian/links", json={"ward_name": "Sunita Devi",
                                         "guardian_name": "Rahul"}).json()
ok("pair code", gl["pair_code"].startswith("DHAAL-") and "guardian_token" in gl)
wt = c.post("/api/guardian/links/claim", json={"pair_code": gl["pair_code"].lower()}).json()
ok("claim accepts case-insensitive code", wt.get("link_id") == gl["link_id"])
chk = c.post("/api/check", json={"type": "qr_text", "payload": FX.QR_COLLECT_URI,
                                 "ward_token": wt["ward_token"]}).json()
grid = chk.get("guardian_request_id")
ok("guardian request auto-created", bool(grid))
GH = {"X-Guardian-Token": gl["guardian_token"]}
WH = {"X-Ward-Token": wt["ward_token"]}
inbox = c.get("/api/guardian/requests", headers=GH).json()["requests"]
ok("guardian inbox", any(x["_id"] == grid and x["status"] == "pending" for x in inbox))
dec = c.post(f"/api/guardian/requests/{grid}/decision",
             json={"decision": "blocked", "note": "beta, mat bhejo"}, headers=GH).json()
ward = c.get(f"/api/guardian/requests/{grid}", headers=WH).json()
ok("guardian decision persists", dec["status"] == "blocked"
   and ward["status"] == "blocked" and ward["guardian_note"] == "beta, mat bhejo")

# contract v2 (H11, PO): EVERY ward check reaches the guardian — clean ones as
# informational "noted" rows (no decision needed), risky ones stay "pending".
chk2 = c.post("/api/check", json={"type": "text", "payload": FX.LEGIT_BANK_TEXT,
                                  "ward_token": wt["ward_token"]}).json()
gr2 = c.get(f"/api/guardian/requests/{chk2.get('guardian_request_id', 'missing')}",
            headers=GH).json()
ok("clean ward check appears as 'noted'", "guardian_request_id" in chk2
   and gr2.get("status") == "noted" and gr2.get("verdict") == "no_known_risk")

# recovery kit: the incident type genuinely changes the kit; date never assumed
kit = c.post("/api/recovery/kit", json={"what": "paid", "amount": 15000,
                                        "channel": "upi", "bank": "SBI",
                                        "incident_date": "10-09-2026"}).json()
ok("recovery kit (paid)", "1930" in kit["call_script_1930"]
   and "10-09-2026" in kit["call_script_1930"] and len(kit["checklist"]) >= 4)
kit_otp = c.post("/api/recovery/kit", json={"what": "shared_otp"}).json()
kit_link = c.post("/api/recovery/kit", json={"what": "clicked_link"}).json()
ok("recovery kits differ by incident type",
   kit["bank_letter"] != kit_otp["bank_letter"] != kit_link["bank_letter"]
   and "freeze/block" in kit_otp["checklist"][0])
ok("recovery date never assumed", "____" in kit_otp["call_script_1930"])

# transcribe typed fallback
t = c.post("/api/transcribe", json={"typed_text": "hello", "lang_hint": "hi-IN"}).json()
ok("transcribe typed fallback", t["transcript"] == "hello")

# H17 field bug: browsers upload Blob.type VERBATIM — "audio/mp4;codecs=opus"
# on Chromium — and Saarika 4xxes on parameterized types while accepting the
# same bytes bare. The endpoint must sanitize before forwarding.
_seen_ct = {}
_stub_real = main.sarvam.speech_to_text
def _stub_ct(blob, filename="x", content_type="audio/webm"):
    _seen_ct["ct"] = content_type
    return {"transcript": "बोलने की जाँच", "language_code": "hi-IN"}
main.sarvam.speech_to_text = _stub_ct
rct = c.post("/api/transcribe",
             files={"audio": ("clip.m4a", b"\x00\x00\x00 ftypisom-opusdata", "audio/mp4;codecs=opus")})
ok("transcribe sanitizes parameterized content type before ASR",
   rct.status_code == 200 and rct.json()["transcript"] == "बोलने की जाँच"
   and _seen_ct.get("ct") == "audio/mp4")
main.sarvam.speech_to_text = _stub_real

# H17 contract change: real audio + no ASR must be an HONEST 503 — the
# fixture-substitution this test used to assert was the fabrication pattern
# retired alongside the IVR fallback (fixture remains only under MOCK_MODE).
r2 = c.post("/api/transcribe",
            files={"audio": ("clip.webm", b"\x1aE\xdf\xa3fake-webm-bytes", "audio/webm")},
            data={"lang_hint": "hi-IN"})
ok("transcribe multipart: dead ASR -> 503 no_transcript (no fixture)",
   r2.status_code == 503 and r2.json().get("status") == "no_transcript")

# speak:true offline -> null audio, never an error
spk = c.post("/api/check", json={"type": "text", "payload": FX.KYC_SCAM_TEXT,
                                 "speak": True}).json()
ok("speak offline yields null audio", spk["verdict"] == "danger"
   and spk["tts_audio_b64"] is None)

# --- H12/H14: verification reversal with identifier extraction ---
# full message -> extracted identifier -> verify -> DIFFERENTLY-WORDED message
# hits that identifier -> withdrawal updates future checks (external review).
scam_msg = ("Bijli bill overdue hai, aaj raat cut jayega. Turant is number par "
            "call karein 9999888771 ya bhugtan karein bijli-pay.xyz par")
rev = c.post("/api/reports", json={"payload": scam_msg, "category": "electricity",
                                   "note": "", "city": "Jaipur"}).json()
ok("candidate identifiers extracted at submission",
   {c_["value"] for c_ in rev["candidate_indicators"]} >= {"bijli-pay.xyz", "9999888771"})
os.environ["MOD_KEY"] = ""
c.post(f"/api/reports/{rev['_id']}/verify", json={"action": "verify"})
c.post(f"/api/reports/{rev['_id']}/verify", json={"action": "verify"})  # idempotent
reworded = c.post("/api/check", json={
    "type": "text", "payload": "Meter update ke liye 99998 88771 par turant call karo"}).json()
one_hit = [s for s in reworded["signals"] if s["id"] == "community_blocklist"]
ok("reworded message hits the extracted identifier",
   bool(one_hit) and "1" in one_hit[0]["title_en"])
c.post(f"/api/reports/{rev['_id']}/verify", json={"action": "reject"})  # withdraw
chk_b = c.post("/api/check", json={
    "type": "text", "payload": "Meter update ke liye 99998 88771 par call karo"}).json()
ok("rejecting a verified report withdraws exactly its identifiers",
   not any(s["id"] == "community_blocklist" for s in chk_b["signals"]))

# independent second report on the same identifier survives the other's reversal
repA = c.post("/api/reports", json={"payload": "9999888771", "category": "electricity"}).json()
repB = c.post("/api/reports", json={"payload": "fraud call from 9999888771",
                                    "category": "electricity"}).json()
c.post(f"/api/reports/{repA['_id']}/verify", json={"action": "verify"})
c.post(f"/api/reports/{repB['_id']}/verify", json={"action": "verify"})
c.post(f"/api/reports/{repA['_id']}/verify", json={"action": "reject"})
still = c.post("/api/check", json={"type": "text",
                                   "payload": "9999888771 se call aaya kya karun"}).json()
ok("withdrawing one report preserves the other's contribution",
   any(s["id"] == "community_blocklist" for s in still["signals"]))

# --- H13/H14: WhatsApp webhook (TwiML) + assessment semantics ---
wa = c.post("/api/whatsapp", data={"From": "whatsapp:+911234567890",
                                   "Body": FX.KYC_SCAM_TEXT})
ok("whatsapp twiml verdict", wa.status_code == 200
   and wa.text.startswith("<?xml") and "DANGER" in wa.text and "<Message>" in wa.text)
wa2 = c.post("/api/whatsapp", data={"From": "whatsapp:+911234567890", "Body": "join sturdy-lion"})
ok("whatsapp join welcome", "Dhaal" in wa2.text and "<Message>" in wa2.text)
wa3 = c.post("/api/whatsapp", data={"From": "whatsapp:+911234567890", "Body": "9876512345"})
ok("whatsapp needs-context: question leads, NO green verdict",
   "और जानकारी चाहिए" in wa3.text and "NO KNOWN RISK" not in wa3.text)
wa4 = c.post("/api/whatsapp", data={"From": "whatsapp:+911234567890",
                                    "Body": "", "NumMedia": "1",
                                    "MediaUrl0": "https://example.com/x.jpg"})
ok("whatsapp media honestly unsupported", "photo/qr/voice" in wa4.text.lower())
# signature validation: with a token configured, unsigned requests are refused
os.environ["TWILIO_AUTH_TOKEN"] = "test-token-abc"
wa5 = c.post("/api/whatsapp", data={"From": "whatsapp:+911", "Body": "hi"})
import base64 as _b64
import hmac as _hmac
import hashlib as _hashlib
_params = {"Body": "hi", "From": "whatsapp:+911"}
_url = "http://testserver/api/whatsapp"
_sig = _b64.b64encode(_hmac.new(b"test-token-abc",
                                (_url + "".join(k + _params[k] for k in sorted(_params))).encode(),
                                _hashlib.sha1).digest()).decode()
wa6 = c.post("/api/whatsapp", data=_params, headers={"X-Twilio-Signature": _sig})
os.environ["TWILIO_AUTH_TOKEN"] = ""
ok("whatsapp signature enforced when configured",
   wa5.status_code == 403 and wa6.status_code == 200)

# --- H14 assessment outcomes on /api/check ---
nc = c.post("/api/check", json={"type": "text", "payload": "9876512345"}).json()
ok("bare number: needs_context, verdict null (no green card)",
   nc["assessment"] == "needs_context" and nc["verdict"] is None
   and "question_hi" in nc["needs_context"])
ncv = c.post("/api/check", json={"type": "text", "payload": "sunita.devi55@ybl"}).json()
ok("bare VPA: targeted question", ncv["assessment"] == "needs_context"
   and "UPI ID" in ncv["needs_context"]["question_hi"])
nc2 = c.post("/api/check", json={"type": "text", "payload": FX.KYC_SCAM_TEXT}).json()
ok("rich input assessed", nc2["assessment"] == "assessed" and nc2["needs_context"] is None)
# A parsed upi:// URI is real evidence, never "too short" (Parva's H13 flag)
nc3 = c.post("/api/check", json={"type": "qr",
                                 "payload": "upi://pay?pa=ramlal@okaxis&pn=Ramlal%20Kirana"}).json()
ok("clean upi qr assessed", nc3["assessment"] == "assessed"
   and nc3["verdict"] == "no_known_risk")
bad_uri = c.post("/api/check", json={"type": "qr", "payload": "upi://pay?pn=Store"}).json()
ok("payee-less URI: unsupported_input, no clearance",
   bad_uri["assessment"] == "unsupported_input" and bad_uri["verdict"] is None)
bare_uri = c.post("/api/check", json={"type": "qr", "payload": "upi://"}).json()
ok("bare upi:// string: no reassuring clearance",
   bare_uri["assessment"] == "unsupported_input" and bare_uri["verdict"] is None)
# short but DECISIVE input stays assessed (blocklisted number alone)
dec_short = c.post("/api/check", json={"type": "text", "payload": FX.BLOCKLISTED_PHONE}).json()
ok("blocklisted bare number is assessed danger, not a context ask",
   dec_short["assessment"] == "assessed" and dec_short["verdict"] == "danger")

# --- H14 facts consistency at the API layer (the money_direction bug) ---
qr = "upi://pay?pa=ramlal@okaxis&pn=Ramlal%20Kirana&am=120"
f_pay = c.post("/api/check", json={"type": "qr", "payload": qr,
                                   "expected_intent": "pay"}).json()
f_rec = c.post("/api/check", json={"type": "qr", "payload": qr,
                                   "expected_intent": "receive"}).json()
ok("same QR ⇒ same money_direction for pay and receive",
   f_pay["analysis"]["money_direction"] == "out_of_your_account"
   and f_rec["analysis"]["money_direction"] == "out_of_your_account")
ok("same QR ⇒ same parsed amount/payee both ways",
   f_pay["facts"]["parse"]["amount"] == f_rec["facts"]["parse"]["amount"] == "120"
   and f_pay["facts"]["parse"]["payee_vpa"] == "ramlal@okaxis")
ok("expectation changes ONLY the mismatch",
   f_pay["verdict"] == "no_known_risk" and f_rec["verdict"] == "suspicious"
   and any(s["id"] == "intent_mismatch" for s in f_rec["signals"]))
ok("timings reported separately",
   all(k in f_pay["timings"] for k in ("engine_ms", "narration_ms", "tts_ms", "total_ms")))
ok("explanation source labelled", f_pay["explanation_source"] in ("rules", "llm"))
# grounded fallback: sub-threshold signal must be mentioned, not denied
sub = c.post("/api/check", json={
    "type": "text",
    "payload": "Maine SBI branch jaakar KYC karwa liya hai, ab tension nahi"}).json()
ok("sub-threshold signals surfaced in clean explanation",
   sub["verdict"] == "no_known_risk"
   and (not [s for s in sub["signals"] if s["weight"] > 0]
        or "ध्यान" in sub["explanation_hi"] or "note" in sub["explanation_en"].lower()))

gl2 = c.post("/api/guardian/links", json={"ward_name": "W", "guardian_name": "G",
                                          "guardian_phone": "+919812300000"}).json()
ok("guardian phone stored", gl2.get("guardian_phone") == "+919812300000")

print(f"\nALL {P} API CHECKS PASSED (store={h['store']})")

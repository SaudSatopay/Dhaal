"""Channel suite (H15) — Meta WhatsApp Cloud API webhook + Exotel IVR, fully
offline (no keys, no network: outbound senders are monkeypatched/captured):
    cd backend && python tests/run_channel_checks.py
"""

import base64
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

for var in ("MONGODB_URI", "ANTHROPIC_API_KEY", "SARVAM_API_KEY",
            "WA_ACCESS_TOKEN", "WA_PHONE_NUMBER_ID", "META_APP_SECRET",
            "EXOTEL_SID", "EXOTEL_API_KEY", "EXOTEL_API_TOKEN", "EXOTEL_SMS_FROM"):
    os.environ[var] = ""
os.environ["MOCK_MODE"] = "false"
os.environ["WA_VERIFY_TOKEN"] = "test-verify-tok"

from fastapi.testclient import TestClient  # noqa: E402

import fixtures as FX  # noqa: E402
import main  # noqa: E402

os.environ["MOD_KEY"] = ""
c = TestClient(main.app)
P = 0


def ok(name, cond, detail=""):
    global P
    print(("ok  " if cond else "FAIL"), name, detail if not cond else "")
    if not cond:
        sys.exit(f"FAILED: {name} {detail}")
    P += 1


# capture outbound sends instead of hitting Meta/Exotel
SENT: list[tuple[str, str]] = []
main.wa_meta.send_text = lambda to, body: (SENT.append((to, body)) or True)
main.wa_meta.mark_read = lambda mid: None
SMS: list[tuple[str, str]] = []
main.exotel.send_sms = lambda to, body: (SMS.append((to, body)) or True)
_orig_fetch_recording = main.exotel.fetch_recording  # kept for the https test


def wa_event(msg: dict) -> dict:
    return {"entry": [{"changes": [{"value": {
        "messaging_product": "whatsapp",
        "metadata": {"phone_number_id": "123"},
        "messages": [msg],
    }}]}]}


# ---- verification handshake -------------------------------------------------
r = c.get("/api/wa/webhook?hub.mode=subscribe&hub.verify_token=test-verify-tok&hub.challenge=42xyz")
ok("wa verify handshake echoes challenge", r.status_code == 200 and r.text == "42xyz")
r = c.get("/api/wa/webhook?hub.mode=subscribe&hub.verify_token=WRONG&hub.challenge=42")
ok("wa verify rejects wrong token", r.status_code == 403)

# ---- signature enforcement --------------------------------------------------
os.environ["META_APP_SECRET"] = "shh-secret"
body = json.dumps(wa_event({"id": "wamid.SIG1", "from": "919811110000",
                            "type": "text", "text": {"body": "hello"}})).encode()
r_unsigned = c.post("/api/wa/webhook", content=body,
                    headers={"Content-Type": "application/json"})
sig = "sha256=" + hmac.new(b"shh-secret", body, hashlib.sha256).hexdigest()
r_signed = c.post("/api/wa/webhook", content=body,
                  headers={"Content-Type": "application/json",
                           "X-Hub-Signature-256": sig})
os.environ["META_APP_SECRET"] = ""
ok("wa unsigned refused when secret set", r_unsigned.status_code == 403)
ok("wa signed accepted", r_signed.status_code == 200)

# ---- scam text -> engine -> reply -------------------------------------------
SENT.clear()
r = c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.A1", "from": "919811110001", "type": "text",
     "text": {"body": FX.KYC_SCAM_TEXT}}))
ok("wa scam handled", r.status_code == 200 and r.json().get("replied") is True)
ok("wa reply carries verdict, score-as-risk (not probability)",
   len(SENT) == 1 and SENT[0][0] == "919811110001"
   and "खतरा · DANGER" in SENT[0][1] and "/100 risk signals" in SENT[0][1]
   and "probability" not in SENT[0][1].lower())

# Meta retries: identical message id must not double-reply
r2 = c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.A1", "from": "919811110001", "type": "text",
     "text": {"body": FX.KYC_SCAM_TEXT}}))
ok("wa duplicate delivery deduped", r2.json().get("deduped") is True and len(SENT) == 1)

# needs-context: question leads, no green verdict line
SENT.clear()
c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.A2", "from": "919811110001", "type": "text",
     "text": {"body": "9876512345"}}))
ok("wa needs-context reply asks, never green",
   "और जानकारी चाहिए" in SENT[0][1] and "NO KNOWN RISK" not in SENT[0][1])

# clean text stays calm
SENT.clear()
c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.A3", "from": "919811110001", "type": "text",
     "text": {"body": FX.LEGIT_BANK_TEXT}}))
ok("wa clean reply", "कोई ज्ञात खतरा नहीं" in SENT[0][1])

# media -> honest unsupported, not a silent drop or empty-caption check
SENT.clear()
c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.A4", "from": "919811110001", "type": "image",
     "image": {"id": "media123"}}))
ok("wa media honestly unsupported", "photo/qr/voice" in SENT[0][1].lower())

# delivery receipts (statuses) must never be checked or replied to
SENT.clear()
r = c.post("/api/wa/webhook", json={"entry": [{"changes": [{"value": {
    "statuses": [{"id": "wamid.A1", "status": "delivered"}]}}]}]})
ok("wa status updates ignored", r.json().get("ignored") == "status_update"
   and len(SENT) == 0)

# junk body -> 200 (Meta must not retry-storm us), nothing sent
r = c.post("/api/wa/webhook", content=b"not-json",
           headers={"Content-Type": "application/json"})
ok("wa junk body acked without action", r.status_code == 200 and len(SENT) == 0)

# ---- Exotel IVR --------------------------------------------------------------
# Passthru ACK is instant and stores the job
r = c.get("/api/ivr/recording?CallSid=CA-test-1&CallFrom=09811110002"
          "&RecordingUrl=https://recordings.exotel.com/x/rec1.mp3")
ok("ivr passthru acks", r.status_code == 200 and r.json()["ok"] is True)
ok("ivr passthru requires CallSid",
   c.get("/api/ivr/recording").status_code == 422)

# result: recording fetch + ASR are offline here -> fixture transcript path;
# TTS is monkeypatched to a tiny valid WAV so the audio contract is asserted.
_TINY_WAV = (b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
             b"\x40\x1f\x00\x00\x80>\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
main.exotel.fetch_recording = lambda url: (b"\xff\xf3fake-mp3", "audio/mpeg")
main.sarvam.text_to_speech = (
    lambda text, lang="hi-IN", sample_rate=None:
    base64.b64encode(_TINY_WAV).decode() if sample_rate == 8000 else None)

SMS.clear()
r = c.get("/api/ivr/result?CallSid=CA-test-1")
ok("ivr result returns playable wav", r.status_code == 200
   and r.headers["content-type"].startswith("audio/wav")
   and r.content.startswith(b"RIFF"))
os.environ["MOD_KEY"] = "mk-test"
job = c.get("/api/ivr/jobs/CA-test-1", headers={"X-Mod-Key": "mk-test"}).json()
ok("ivr job gated + recorded", job["verdict"] == "danger"
   and job.get("mocked_transcript") is True and "audio_b64" not in job)
ok("ivr job endpoint 401 without mod key",
   c.get("/api/ivr/jobs/CA-test-1").status_code == 401)
os.environ["MOD_KEY"] = ""
ok("ivr result sms attempted to caller",
   len(SMS) == 1 and SMS[0][0] == "09811110002" and "1930" in SMS[0][1])

# replay serves the cache (no second SMS, no reprocessing)
r2 = c.get("/api/ivr/result?CallSid=CA-test-1")
ok("ivr result idempotent on replay", r2.status_code == 200 and len(SMS) == 1)

# spoken script branches: danger vs needs-context differ and stay short
d_danger = c.post("/api/check", json={"type": "voice_transcript",
                                      "payload": FX.DIGITAL_ARREST_TRANSCRIPT}).json()
d_ctx = c.post("/api/check", json={"type": "text", "payload": "9812345678"}).json()
s1, m1 = main._ivr_script(d_danger)
s2, m2 = main._ivr_script(d_ctx)
ok("ivr scripts branch by outcome", s1 != s2 and "1930" in s1
   and "दुबारा call" in s2 and max(len(s1), len(s2)) < 300)

# TTS down -> 503 (Exotel plays its static fallback), SMS still attempted
main.sarvam.text_to_speech = lambda *a, **k: None
SMS.clear()
r = c.get("/api/ivr/result?CallSid=CA-test-2&CallFrom=09811110003"
          "&RecordingUrl=https://recordings.exotel.com/x/rec2.mp3")
ok("ivr tts-down degrades to 503 + sms", r.status_code == 503 and len(SMS) == 1)

# recording URL scheme is validated — no plaintext/relative fetches, ever
ok("ivr recording fetch refuses non-https",
   _orig_fetch_recording("http://recordings.exotel.com/x.mp3") is None
   and _orig_fetch_recording("//evil/x.mp3") is None)

# H15 hardening (external review round 2) ------------------------------------
# SSRF/credential-spray: only Exotel's own hosts are fetchable
ok("ivr recording fetch refuses non-exotel hosts",
   _orig_fetch_recording("https://evil.example.com/rec.mp3") is None
   and _orig_fetch_recording("https://recordings.exotel.com.evil.io/x.mp3") is None)
import exotel as _ex  # noqa: E402
ok("ivr recording host allowlist logic",
   _ex._recording_host_ok("https://recordings.exotel.com/a/b.mp3")
   and not _ex._recording_host_ok("https://exotel.com.attacker.dev/x"))

# fresh IVR computation is rate-limited; cached replays are exempt
main._IVR_WINDOW.clear()
main._IVR_MAX_PER_MIN = 2
codes = [c.get(f"/api/ivr/result?CallSid=CA-rate-{i}").status_code for i in range(4)]
main._IVR_MAX_PER_MIN = 6
ok("ivr fresh compute rate-limited (429 after burst)", 429 in codes)
cached = c.get("/api/ivr/result?CallSid=CA-test-1")  # cached from earlier
ok("ivr cached replay bypasses the limit", cached.status_code == 200)

# WA: missing secret on prod (VERCEL) fails closed
os.environ["VERCEL"] = "1"
os.environ["META_APP_SECRET"] = ""
wa_closed = c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.V1", "from": "919811110009", "type": "text",
     "text": {"body": "hi"}}))
os.environ["VERCEL"] = ""
ok("wa missing secret fails closed on prod", wa_closed.status_code == 403)

# WA: failed send -> redelivery retries ONLY the send (no double engine work)
SENT.clear()
_real_send = main.wa_meta.send_text
main.wa_meta.send_text = lambda to, body: False  # first send fails
r1 = c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.RETRY1", "from": "919811110004", "type": "text",
     "text": {"body": FX.KYC_SCAM_TEXT}}))
main.wa_meta.send_text = lambda to, body: (SENT.append((to, body)) or True)
r2 = c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.RETRY1", "from": "919811110004", "type": "text",
     "text": {"body": FX.KYC_SCAM_TEXT}}))
ok("wa failed send retried on redelivery, send-only",
   r1.json().get("replied") is False and r2.json().get("resent") is True
   and len(SENT) == 1 and "खतरा · DANGER" in SENT[0][1])
r3 = c.post("/api/wa/webhook", json=wa_event(
    {"id": "wamid.RETRY1", "from": "919811110004", "type": "text",
     "text": {"body": FX.KYC_SCAM_TEXT}}))
ok("wa retry never double-sends after success",
   r3.json().get("deduped") is True and "resent" not in r3.json() and len(SENT) == 1)

# assessment gaps from held-out v3 (post-publication fixes) -------------------
th = c.post("/api/check", json={"type": "text", "payload": "अंजाम भुगतना पड़ेगा, सोच लेना।"}).json()
ok("bare threat: asks for the ask, never green",
   th["assessment"] == "needs_context" and th["verdict"] is None
   and th["needs_context"]["reason"] == "threat_no_ask")
acct = c.post("/api/check", json={"type": "text",
                                  "payload": "खाता संख्या 123456789012, IFSC SBIN0001234"}).json()
ok("bank account+IFSC alone: identifier ask",
   acct["assessment"] == "needs_context"
   and acct["needs_context"]["reason"] == "bare_identifier")
q1 = c.post("/api/check", json={"type": "text", "payload": "Can you send it now?"}).json()
q2 = c.post("/api/check", json={"type": "text", "payload": "yeh upi id sahi hai na"}).json()
ok("referent-less questions ask what 'it' is",
   q1["assessment"] == "needs_context" and q1["needs_context"]["reason"] == "no_referent"
   and q2["assessment"] == "needs_context")
# threats WITH an ask still convict, and rich clean texts stay assessed
coer = c.post("/api/check", json={"type": "text",
                                  "payload": "50 हज़ार भेजो नहीं तो अंजाम भुगतना पड़ेगा"}).json()
ok("threat + money ask still convicts", coer["assessment"] == "assessed"
   and coer["verdict"] in ("suspicious", "danger"))
benign_q = c.post("/api/check", json={"type": "text",
                                      "payload": "Bhai kal match ke tickets book kar liye, tera hissa 850 hua, jab time mile bhej dena. No rush."}).json()
ok("rich benign text unaffected by new gates",
   benign_q["assessment"] == "assessed" and benign_q["verdict"] == "no_known_risk")

print(f"\nALL {P} CHANNEL CHECKS PASSED")

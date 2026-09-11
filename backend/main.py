"""Dhaal (ढाल) — backend stub API. Serves every contract in docs/CONTRACTS.md from minute 1.

Engine lane (Harsh) replaces the marked sections with the real signal engine, Claude,
Sarvam and Atlas — the shapes here are the contract, do not drift from CONTRACTS.md.
Stub keeps a deterministic mini-engine so the golden path demos end-to-end immediately.
"""
import hashlib
import os
import re
import secrets
import time
import uuid
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # repo-root .env (local dev)
load_dotenv()  # backend/.env; real env vars (Vercel) always win

from xml.sax.saxutils import escape as _xml_escape

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

import fixtures as FX
import llm
import sarvam
import engine as engine_mod
from engine import run_signal_engine
from engine.common import extract_phones, extract_vpas
from engine.urls import first_host
from store import get_store

MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

app = FastAPI(title="Dhaal API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------- store
# Atlas when MONGODB_URI is set (serverless-durable), else in-memory; per-call
# failover to memory so a wifi/Atlas outage degrades instead of 500ing.
STORE = get_store()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------- signal engine
# Real deterministic engine lives in engine/ (+ seed lists in data/brands.py).
# Rules + community intel only — the LLM never touches the verdict.
# Regression: cd backend && .venv/Scripts/python.exe tests/run_engine_checks.py


def _grounded_explanation(assessment, verdict, signals, facts, needs_context):
    """Template-free fallback narration (H14): composed ONLY from parsed facts
    and detected signals — what was observed, why it matters, what is unknown,
    one next action. No invented banks, threats, amounts or accusations."""
    real = [s for s in signals if s["weight"] > 0]
    top = real[0] if real else None
    p = facts.get("parse") or {}

    if assessment == "unsupported_input":
        return (
            "यह payment code ठीक से पढ़ा नहीं जा सका — payee नहीं मिला या format टूटा है। "
            "जाँच अधूरी है। साफ़ रोशनी में दुबारा scan करें, या जो message आया था वह paste करें।",
            "This payment code could not be read — no payee found or the format is broken, "
            "so no assessment was made. Rescan in better light, or paste the message you received.",
        )
    if assessment == "needs_context":
        found_hi = f" अभी तक दिखा: {top['title_hi']}।" if top else ""
        found_en = f" Noted so far: {top['title_en']}." if top else ""
        q_hi = (needs_context or {}).get("question_hi", "")
        q_en = (needs_context or {}).get("question_en", "")
        return (
            f"सिर्फ़ इतने से पक्की जाँच नहीं हो सकती — यह ठीक भी हो सकता है और ठगी भी।{found_hi} {q_hi}",
            f"This alone is not enough for a real check — it could be fine or a scam.{found_en} {q_en}",
        )

    if verdict == "no_known_risk":
        if real:  # sub-threshold findings: NEVER claim "no signals found"
            return (
                f"कोई ज्ञात खतरा नहीं — पर एक बात दिखी: {top['title_hi']}। {top['detail_hi']} "
                "फिर भी पैसे भेजने से पहले नाम और नंबर खुद जाँच लें।",
                f"No known risk — but one thing was noted: {top['title_en']}. {top['detail_en']} "
                "Still verify the name and number yourself before paying.",
            )
        if p.get("status") == "valid":
            amt_hi = f"₹{p['amount']} का " if p.get("amount") else ""
            amt_en = f"a ₹{p['amount']} " if p.get("amount") else "a "
            payee = p.get("payee_vpa") or ""
            return (
                f"यह QR {amt_hi}payment request खोलता है (payee: {payee})। कोई ज्ञात खतरे का संकेत नहीं मिला। "
                "authorize करने से पहले app में payee का नाम खुद जाँच लें।",
                f"This QR opens {amt_en}payment request (payee: {payee}). No known risk signals found. "
                "Check the payee name in your app before authorizing.",
            )
        return (
            "इसमें कोई ज्ञात खतरे का संकेत नहीं मिला। फिर भी पैसे भेजने से पहले नाम और नंबर खुद जाँच लें।",
            "No known risk signals found. Still verify the name and number yourself before paying.",
        )

    # suspicious / danger — observed → also-seen → action
    obs_hi = f"{top['title_hi']}: {top['detail_hi']}" if top else ""
    obs_en = f"{top['title_en']}: {top['detail_en']}" if top else ""
    more_hi = f" साथ में: {real[1]['title_hi']}।" if len(real) > 1 else ""
    more_en = f" Also seen: {real[1]['title_en']}." if len(real) > 1 else ""
    if verdict == "danger":
        act_hi = " पैसे न भेजें, OTP/PIN किसी को न बताएं, कोई link न खोलें। ठगे गए हों तो 1930 पर call करें।"
        act_en = " Do not send money, share any OTP/PIN, or open links. If money already went, call 1930."
    else:
        act_hi = " अभी कुछ भी न भेजें — पहले official app या जाने-पहचाने नंबर से खुद पक्का करें।"
        act_en = " Send nothing yet — first confirm yourself via the official app or a number you already know."
    return (obs_hi + more_hi + act_hi, obs_en + more_en + act_en)


# ---------------------------------------------------------------- endpoints
@app.get("/api/health")
def health():
    return {"ok": True, "mock_mode": MOCK_MODE, "store": STORE.active_name()}


class CheckIn(BaseModel):
    type: str = "text"
    payload: str
    lang: str = "hi-IN"
    speak: bool = False
    ward_link_id: str | None = None  # legacy pre-H14 field: never authorizes
    ward_token: str | None = None    # H14: the ward's capability token
    expected_intent: str | None = None  # "pay" | "receive" | "verify" — user's stated goal


_PRESSURE_TAGS = {"urgency_framing": ("urgency", "जल्दबाज़ी"),
                  "secrecy_pressure": ("secrecy", "अलग-थलग करने का दबाव"),
                  "threat_framing": ("threat", "धमकी"),
                  "coercion_extortion": ("coercion", "ज़बरदस्ती")}

_ASKS = {  # requested_action fact → user-facing "what they want" row
    "approve_payment": ("approve a payment", "payment approve कराना", True),
    "disclose_credential": ("your OTP/PIN/password", "आपका OTP/PIN/पासवर्ड", False),
    "grant_remote_access": ("access to your screen", "आपकी screen का access", False),
    "pay_fee": ("an upfront fee", "पहले फीस", False),
    "send_money": ("you to send money", "आपसे पैसे भिजवाना", True),
    "install_app_file": ("install an app file", "app file install कराना", False),
}


def _analysis(facts: dict) -> dict:
    """Structured 'what they want' — read straight off the parsed FACTS.
    Same input ⇒ same facts, whatever the user expected (H14: expectation
    feeds only mismatch detection, never the parsed transaction)."""
    p = facts.get("parse") or {}
    asking = []
    for act in facts.get("requested_actions", []):
        row = _ASKS.get(act)
        if row:
            what, hi, carries_amount = row
            asking.append({"what": what, "hi": hi,
                           "amount": p.get("amount") if carries_amount else None})
    pressure = [{"tag": _PRESSURE_TAGS[k][0], "hi": _PRESSURE_TAGS[k][1]}
                for k in facts.get("pressure", []) if k in _PRESSURE_TAGS]
    return {"claimed_identity": facts.get("claimed_identity"),
            "asking_for": asking,
            "money_direction": facts.get("money_direction", "none_detected"),
            "pressure": pressure,
            "expectation": facts.get("expectation", "unknown"),
            "missing": facts.get("missing", [])}


_ONLY_URI_RE = re.compile(r"^(?:\s*upi://\S*\s*)+$", re.I)
_BARE_PHONE_RE = re.compile(r"\+?[\d\s\-]{8,15}")
_BARE_VPA_RE = re.compile(r"[a-z0-9.\-_]{2,}@[a-z][a-z0-9]{1,64}", re.I)


def _assess(payload: str, score: int, facts: dict):
    """Assessment outcome (H14, first-class): assessed | needs_context |
    unsupported_input. A green verdict must never sit on an input that was
    not actually assessable; a sub-threshold score on a bare identifier is a
    question, not reassurance. Short-but-decisive inputs (e.g. a blocklisted
    number, a fully parsed payment URI) ARE assessed."""
    p = facts.get("parse")
    t = payload.strip()
    only_uri = bool(p) and bool(_ONLY_URI_RE.fullmatch(t))

    if only_uri and p.get("status") in ("malformed", "unsupported", "incomplete") \
            and score < engine_mod.SUSPICIOUS_AT:
        return "unsupported_input", {
            "reason": "unreadable_payment_code",
            "question_hi": "QR/link में payee नहीं मिला या format टूटा है — साफ़ photo से दुबारा scan करें, या पूरा message paste करें।",
            "question_en": "No payee found in this QR/link, or the format is broken — rescan a clearer photo, or paste the full message.",
        }
    if p and p.get("status") == "valid" and only_uri:
        return "assessed", None  # a parsed payment request is real evidence
    if score >= engine_mod.SUSPICIOUS_AT:
        return "assessed", None  # decisive regardless of length

    if _BARE_PHONE_RE.fullmatch(t):
        return "needs_context", {
            "reason": "bare_identifier",
            "question_hi": "यह नंबर आपसे क्या करवाना चाहता है? जो call/message आया, वह पूरा paste करें या बताइए — तब सही जाँच होगी।",
            "question_en": "What did this number ask you to do? Paste the message or describe the call — then the check means something.",
        }
    if _BARE_VPA_RE.fullmatch(t):
        return "needs_context", {
            "reason": "bare_identifier",
            "question_hi": "इस UPI ID से किसने, क्या करने को कहा? वह message paste करें — तभी पक्की जाँच होगी।",
            "question_en": "Who asked you to do what with this UPI ID? Paste that message — then a real check is possible.",
        }
    if len(t.split()) < 4 and not (p and p.get("status") == "valid"):
        return "needs_context", {
            "reason": "too_short",
            "question_hi": "यह किस बारे में है? जो message/call आया था, वह पूरा paste करें — तब सही जाँच होगी।",
            "question_en": "What is this about? Paste the full message or describe the call — then the check means something.",
        }
    return "assessed", None


@app.post("/api/check")
def check(body: CheckIn):
    t0 = time.perf_counter()
    payload = body.payload[:4000]  # bound input; nothing meaningful needs more
    verdict, score, signals, category, facts = run_signal_engine(
        payload, body.type, STORE.indicators_map(), allow_network=not MOCK_MODE,
        expected_intent=body.expected_intent,
    )
    engine_ms = round((time.perf_counter() - t0) * 1000)

    # H14 first-class assessment: needs_context / unsupported_input carry NO
    # risk verdict — no green card, no score presented as an analysis result.
    assessment, needs_context = _assess(payload, score, facts)
    if assessment != "assessed":
        verdict = None

    # Claude narrates FROM the detected signals (zero verdict weight); any
    # failure or MOCK_MODE -> grounded rule-composed fallback (never generic
    # accusations). Narration may explain; it may not change validated facts,
    # the verdict, or the transaction-type label.
    exp_hi = exp_en = None
    mocked = True
    narration_ms = 0
    if not MOCK_MODE and assessment == "assessed":
        t1 = time.perf_counter()
        out = llm.narrate(payload, body.type, verdict, score, signals, category,
                          facts=facts)
        narration_ms = round((time.perf_counter() - t1) * 1000)
        if out:
            exp_hi, exp_en = out["explanation_hi"], out["explanation_en"]
            llm_cat = out.get("category")
            # transaction-type labels come from validated parsing only: the
            # model may fill a missing SCRIPT category, never collect mechanics
            if category is None and llm_cat and llm_cat != "fake_collect":
                category = llm_cat
            if out.get("pattern_note_en") or out.get("pattern_note_hi"):
                signals.append({
                    "id": "llm_pattern_note", "source": "llm_pattern", "weight": 0,
                    "title_en": "Pattern read", "title_hi": "पैटर्न की पहचान",
                    "detail_en": out.get("pattern_note_en", ""),
                    "detail_hi": out.get("pattern_note_hi", ""),
                })
            mocked = False
    if exp_hi is None:
        exp_hi, exp_en = _grounded_explanation(assessment, verdict, signals,
                                               facts, needs_context)

    doc = {
        "_id": _id("chk"),
        "input": {"type": body.type, "payload": payload, "lang": body.lang},
        "assessment": assessment,
        "verdict": verdict, "score": score, "signals": signals,
        "explanation_hi": exp_hi, "explanation_en": exp_en,
        "explanation_source": "rules" if mocked else "llm",
        "scam_category": category if assessment == "assessed" else None,
        "facts": facts,
        "analysis": _analysis(facts),
        "expected_intent": body.expected_intent,
        "needs_context": needs_context,
        "tts_audio_b64": None,
        "mocked": mocked,
        "community_data": "degraded" if STORE_DEGRADED() else "live",
        "created_at": _now(),
    }
    # Bulbul speaks the Hindi explanation (for needs_context that IS the
    # question); cached on the stored check. Failure -> null audio, never 500.
    tts_ms = 0
    if body.speak and not MOCK_MODE:
        t2 = time.perf_counter()
        doc["tts_audio_b64"] = sarvam.text_to_speech(exp_hi, lang="hi-IN")
        tts_ms = round((time.perf_counter() - t2) * 1000)
    doc["timings"] = {"engine_ms": engine_ms, "narration_ms": narration_ms,
                      "tts_ms": tts_ms,
                      "total_ms": round((time.perf_counter() - t0) * 1000)}
    STORE.insert("checks", doc)
    # Every ward check reaches the guardian (H11) — but ONLY through the
    # ward's capability token (H14). A bare link_id never authorizes writes
    # into a family's inbox; legacy pairings must re-pair.
    link = _link_by_token(body.ward_token or "", "ward")
    if link:
        gr = {
            "_id": _id("gr"), "link_id": link["_id"], "check_id": doc["_id"],
            "summary_hi": exp_hi[:140], "verdict": verdict, "score": score,
            "assessment": assessment,
            "status": "pending" if (assessment == "assessed"
                                    and verdict != "no_known_risk") else "noted",
            "guardian_note": "", "created_at": _now(),
        }
        STORE.insert("guardian_requests", gr)
        doc["guardian_request_id"] = gr["_id"]
        doc["guardian_delivery"] = "sent" if not STORE_DEGRADED() else "sent_not_durable"
    elif body.ward_token or body.ward_link_id:
        doc["guardian_delivery"] = "unlinked"  # token invalid/revoked/legacy → re-pair
    return doc


@app.post("/api/transcribe")
async def transcribe(request: Request):
    # JSON typed fallback OR multipart audio (webm/m4a/wav from MediaRecorder).
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("application/json"):
        data = await request.json()
        typed = (data or {}).get("typed_text", "")
        return {"transcript": typed, "lang": (data or {}).get("lang_hint", "hi-IN"), "mocked": False}
    form = await request.form()
    audio = form.get("audio")
    lang_hint = str(form.get("lang_hint") or "hi-IN")
    if audio is not None and not isinstance(audio, str) and not MOCK_MODE:
        blob = await audio.read()
        out = await run_in_threadpool(
            sarvam.speech_to_text, blob,
            audio.filename or "audio.webm", audio.content_type or "audio/webm",
        )
        if out:
            return {"transcript": out["transcript"],
                    "lang": out["language_code"] or lang_hint, "mocked": False}
    # Sarvam down / no key / MOCK_MODE — rehearsed fixture keeps the beat alive
    return {"transcript": FX.DIGITAL_ARREST_TRANSCRIPT, "lang": "hi-IN", "mocked": True}


# ---------------------------------------------------------------- guardian auth
# H14 rebuild (external security review): a pairing identifier is NOT guardian
# authentication. Two role-scoped capability tokens per pairing, minted once,
# stored ONLY as SHA-256 hashes, carried ONLY in headers (never URLs/QRs/logs):
#   guardian_token (X-Guardian-Token) — returned once at link creation; the sole
#     authority for reading the inbox and deciding requests.
#   ward_token (X-Ward-Token) — returned once when the ward claims the pair
#     code; the sole authority for submitting checks to the guardian and
#     polling one's own request status.
# Pair codes are the ONLY thing that travels (QR/spoken): 8 chars from a
# 31-char alphabet (~8×10^11), single-use, 30-min expiry. Old pre-token links
# have no stored hashes, so their credentials simply never authenticate —
# insecure pairings are NOT migrated; both sides re-pair.

_PAIR_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/1/I/L lookalikes
PAIR_CODE_TTL_MIN = 30


def _sha(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new_pair_code() -> str:
    return "DHAAL-" + "".join(secrets.choice(_PAIR_ALPHABET) for _ in range(8))


def _link_by_token(token: str, role: str) -> dict | None:
    """Pairing doc for a role capability token, or None. Revoked links never
    authenticate; neither do pre-token (legacy) links — no silent migration."""
    token = (token or "").strip()
    if not token:
        return None
    field = "guardian_token_sha256" if role == "guardian" else "ward_token_sha256"
    hits = STORE.list("guardian_links", {field: _sha(token)})
    link = hits[0] if hits else None
    if link and link.get(field) and not link.get("revoked"):
        return link
    return None


def _auth_link(request: Request, role: str) -> dict | None:
    header = "x-guardian-token" if role == "guardian" else "x-ward-token"
    return _link_by_token(request.headers.get(header, ""), role)


def STORE_DEGRADED() -> bool:
    """True while writes may be landing in the in-memory fallback instead of
    Atlas — callers surface this instead of implying durability."""
    fn = getattr(STORE, "recently_degraded", None)
    return bool(fn()) if fn else False


def _request_view(gr: dict) -> dict:
    """What either paired side may see about a request. Never the link_id —
    it is an internal key, and nothing public should teach it."""
    return {k: gr.get(k) for k in (
        "_id", "check_id", "summary_hi", "verdict", "score", "status",
        "guardian_note", "created_at", "assessment",
    )}


# Claim-endpoint rate limit — blunts pair-code guessing. Per-instance sliding
# window (serverless: per warm instance; the real defense is the 8×10^11 code
# space + 30-min single-use codes, this just makes online guessing loud).
_CLAIM_WINDOW: deque = deque()
_CLAIM_MAX_PER_MIN = 12


def _claim_rate_ok() -> bool:
    now = time.monotonic()
    while _CLAIM_WINDOW and now - _CLAIM_WINDOW[0] > 60:
        _CLAIM_WINDOW.popleft()
    if len(_CLAIM_WINDOW) >= _CLAIM_MAX_PER_MIN:
        return False
    _CLAIM_WINDOW.append(now)
    return True


class LinkIn(BaseModel):
    ward_name: str
    guardian_name: str
    guardian_phone: str = ""  # H12+: "call my trusted person" uses THIS stored
    #                           number — never one supplied by a suspicious message


@app.post("/api/guardian/links")
def create_link(body: LinkIn):
    guardian_token = "dgt_" + secrets.token_urlsafe(24)
    doc = {
        "_id": _id("gl"), "ward_name": body.ward_name[:80],
        "guardian_name": body.guardian_name[:80],
        "guardian_phone": body.guardian_phone.strip()[:20],
        "pair_code": _new_pair_code(),
        "pair_code_expires_at": (datetime.now(timezone.utc)
                                 + timedelta(minutes=PAIR_CODE_TTL_MIN)).isoformat(),
        "pair_code_claimed": False,
        "guardian_token_sha256": _sha(guardian_token),
        "ward_token_sha256": None,
        "revoked": False, "created_at": _now(),
    }
    STORE.insert("guardian_links", doc)
    # The plaintext guardian token exists only in THIS response — store hashes.
    return {
        "link_id": doc["_id"], "ward_name": doc["ward_name"],
        "guardian_name": doc["guardian_name"], "guardian_phone": doc["guardian_phone"],
        "pair_code": doc["pair_code"], "pair_code_expires_at": doc["pair_code_expires_at"],
        "guardian_token": guardian_token, "created_at": doc["created_at"],
    }


class ClaimIn(BaseModel):
    pair_code: str


@app.post("/api/guardian/links/claim")
def claim_link(body: ClaimIn):
    """Ward redeems a pair code — single-use, expiring, rate-limited. Returns
    the minimum the ward role needs (incl. the stored trusted number for the
    'call my person' button) plus the ward's own capability token, once."""
    if not _claim_rate_ok():
        return JSONResponse({"error": "too many attempts — wait a minute"}, status_code=429)
    code = body.pair_code.strip().upper()
    if code and not code.startswith("DHAAL-"):
        code = f"DHAAL-{code}"
    hits = STORE.list("guardian_links", {"pair_code": code})
    link = hits[0] if hits else None
    if not link:
        return JSONResponse({"error": "code not found"}, status_code=404)
    if link.get("revoked"):
        return JSONResponse({"error": "pairing was revoked — ask for a new code"}, status_code=410)
    if link.get("pair_code_claimed"):
        return JSONResponse({"error": "code already used — ask your guardian for a fresh pairing"},
                            status_code=409)
    exp = link.get("pair_code_expires_at")
    try:
        expired = exp is not None and datetime.fromisoformat(exp) < datetime.now(timezone.utc)
    except ValueError:
        expired = True
    if exp is None or expired:  # legacy no-expiry codes are dead too: re-pair
        return JSONResponse({"error": "code expired — ask your guardian for a fresh pairing"},
                            status_code=410)
    ward_token = "dwt_" + secrets.token_urlsafe(24)
    STORE.update("guardian_links", link["_id"], {
        "pair_code_claimed": True, "claimed_at": _now(),
        "ward_token_sha256": _sha(ward_token),
    })
    return {
        "link_id": link["_id"], "ward_token": ward_token,
        "ward_name": link.get("ward_name", ""),
        "guardian_name": link.get("guardian_name", ""),
        "guardian_phone": link.get("guardian_phone", ""),
    }


@app.get("/api/guardian/links/resolve")
def resolve_link_gone(pair_code: str = ""):
    # Pre-H14 pairing flow — returned the deciding credential to anyone with a
    # guessable 4-hex code. Dead on purpose; clients must POST /claim.
    return JSONResponse(
        {"error": "pairing flow upgraded — update the app and pair again"}, status_code=410)


class RevokeIn(BaseModel):
    reason: str = ""


@app.post("/api/guardian/links/revoke")
def revoke_link(body: RevokeIn, request: Request):
    """Either side may sever the pairing (consent works both ways). All tokens
    and the pair code die with it."""
    link = _auth_link(request, "guardian")
    role = "guardian"
    if not link:
        link = _auth_link(request, "ward")
        role = "ward"
    if not link:
        return JSONResponse({"error": "valid pairing token required"}, status_code=401)
    STORE.update("guardian_links", link["_id"], {
        "revoked": True, "revoked_at": _now(), "revoked_by": role,
        "revoke_reason": body.reason[:200],
    })
    return {"ok": True, "revoked": True, "link_id": link["_id"]}


@app.get("/api/guardian/requests")
def list_requests(request: Request):
    link = _auth_link(request, "guardian")
    if not link:
        return JSONResponse({"error": "guardian token required"}, status_code=401)
    out = STORE.list("guardian_requests", {"link_id": link["_id"]})
    return {"requests": [_request_view(r) for r in
                         sorted(out, key=lambda r: r["created_at"], reverse=True)],
            "ward_name": link.get("ward_name", "")}


@app.get("/api/guardian/requests/{rid}")
def get_request(rid: str, request: Request):
    link = _auth_link(request, "guardian") or _auth_link(request, "ward")
    if not link:
        return JSONResponse({"error": "pairing token required"}, status_code=401)
    gr = STORE.get("guardian_requests", rid)
    if not gr or gr.get("link_id") != link["_id"]:
        # out-of-pairing ids look identical to missing ones — don't confirm existence
        return JSONResponse({"error": "request not found"}, status_code=404)
    return _request_view(gr)


class DecisionIn(BaseModel):
    decision: str  # allowed | blocked
    note: str = ""


@app.post("/api/guardian/requests/{rid}/decision")
def decide(rid: str, body: DecisionIn, request: Request):
    # H14: only the guardian capability token authorizes a decision. Knowing a
    # request id — or anything readable without a token — is never enough.
    link = _auth_link(request, "guardian")
    if not link:
        return JSONResponse({"error": "guardian token required"}, status_code=401)
    gr = STORE.get("guardian_requests", rid)
    if not gr or gr.get("link_id") != link["_id"]:
        return JSONResponse({"error": "request not found"}, status_code=404)
    if body.decision not in ("allowed", "blocked"):
        return JSONResponse({"error": "decision must be allowed|blocked"}, status_code=422)
    r = STORE.update("guardian_requests", rid,
                     {"status": body.decision, "guardian_note": body.note[:300],
                      "decided_at": _now()})
    out = _request_view(r or gr)
    out["durable"] = not STORE_DEGRADED()
    return out


class ReportIn(BaseModel):
    payload: str
    category: str = "other"
    note: str = ""
    city: str = "Jaipur"


def _indicator_type(value: str) -> str:
    v = value.strip().lower()
    if re.fullmatch(r"\+?\d[\d\s-]{8,14}", v):
        return "phone"
    if "@" in v and " " not in v:
        return "upi"
    if "." in v and " " not in v:
        return "domain"
    return "script"


def _extract_indicators(payload: str) -> list[dict]:
    """Reusable identifiers inside a reported message (H14): domains, phones
    and VPAs in canonical form. A verified full message contributes ITS
    IDENTIFIERS to the blocklist — never the whole sentence — so a
    differently-worded message carrying the same scam number still hits."""
    from engine.urls import _host_of, extract_urls  # local import: no cycle at module load
    out, seen = [], set()

    def add(value: str, itype: str):
        v = value.strip().lower()
        if v and v not in seen and len(out) < 5:
            seen.add(v)
            out.append({"value": v, "type": itype})

    for u in extract_urls(payload):
        h = _host_of(u)
        if h:
            add(h, "domain")
    for vpa in sorted(extract_vpas(payload)):
        add(vpa, "upi")
    for ph in sorted(extract_phones(payload)):
        add(ph, "phone")
    return out


@app.post("/api/reports")
def create_report(body: ReportIn):
    payload = body.payload.strip()[:2000]
    doc = {
        "_id": _id("rep"), "payload": payload, "category": body.category[:40],
        "note": body.note[:500], "city": body.city[:60], "status": "pending",
        "indicator_type": _indicator_type(payload),
        # extracted at submission so the moderator sees EXACTLY which
        # identifiers verification would publish (evidence-first moderation)
        "candidate_indicators": _extract_indicators(payload),
        "created_at": _now(),
    }
    return STORE.insert("reports", doc)


# Moderation is a WRITE into everyone's shield — it must not be open to anyone
# with the URL (H12, external review: "make the trust model defensible").
# When MOD_KEY is set (prod), the queue and verify require the X-Mod-Key header;
# unset (local dev/tests) they stay open.
def _mod_ok(request: Request) -> bool:
    key = os.getenv("MOD_KEY", "").strip()
    if not key:
        # fail closed in production (H12 review): a missing key must never
        # silently open moderation. Local dev (no VERCEL env) stays open.
        return not os.getenv("VERCEL")
    return request.headers.get("x-mod-key", "") == key


@app.get("/api/reports")
def list_reports(request: Request, status: str = "pending"):
    if status == "pending" and not _mod_ok(request):
        return JSONResponse({"error": "moderator key required"}, status_code=401)
    out = STORE.list("reports", {"status": status})
    return {"reports": sorted(out, key=lambda r: r["created_at"], reverse=True)}


class VerifyIn(BaseModel):
    action: str  # verify | reject


def _report_contributions(r: dict) -> list[dict]:
    """What THIS report publishes to the blocklist when verified. Identifier
    reports publish their canonical identifier; full-message reports publish
    their extracted identifiers (never the sentence); a message with no
    extractable identifier falls back to one script snippet."""
    itype = r.get("indicator_type", "script")
    value = r["payload"].strip()
    if itype == "phone":
        from engine.common import norm_phone
        return [{"value": norm_phone(value) or value.lower(), "type": "phone"}]
    if itype == "upi":
        return [{"value": value.lower(), "type": "upi"}]
    if itype == "domain":
        return [{"value": (first_host(value) or value).lower(), "type": "domain"}]
    cands = r.get("candidate_indicators") or _extract_indicators(value)
    if cands:
        return cands
    return [{"value": value.lower()[:200], "type": "script"}]


@app.post("/api/reports/{rid}/verify")
def verify_report(rid: str, body: VerifyIn, request: Request):
    if not _mod_ok(request):
        return JSONResponse({"error": "moderator key required"}, status_code=401)
    r = STORE.get("reports", rid)
    if not r:
        return {"error": "report not found"}
    status = "verified" if body.action == "verify" else "rejected"
    if r.get("status") == status:
        return r  # idempotent: repeating the same decision changes nothing
    was_verified = r.get("status") == "verified"
    contributions = _report_contributions(r)
    # record the decision AND the exact contributions BEFORE mutating the
    # blocklist, so reversal always withdraws exactly what this report added
    # even if a later write fails partway (H14: no silent divergence).
    r = STORE.update("reports", rid, {
        "status": status, "decided_at": _now(), "decided_via": "mod-key",
        "indicator_values": [c["value"] for c in contributions],
    }) or r
    if status == "verified":
        for c in contributions:
            STORE.upsert_indicator(c["value"], c["type"], r["category"])
    elif was_verified:
        # H12: a mistaken verification must be reversible — withdraw exactly
        # the values this report contributed (other reports' counts survive).
        for value in (r.get("indicator_values")
                      or [c["value"] for c in contributions]):
            STORE.decrement_indicator(value)
    return r


@app.get("/api/intel/trends")
def trends():
    # Fixture baseline + live overlay per category/city/day. Totals stay
    # baseline+live (seed.py numbers were rehearsed against that semantics).
    verified = STORE.list("reports", {"status": "verified"})
    cat_counts: dict[str, int] = {}
    city_counts: dict[str, int] = {}
    for r in verified:
        cat_counts[r.get("category") or "other"] = cat_counts.get(r.get("category") or "other", 0) + 1
        city_counts[r.get("city") or "Jaipur"] = city_counts.get(r.get("city") or "Jaipur", 0) + 1

    by_category = [dict(x) for x in FX.SEED_TRENDS["by_category"]]
    for row in by_category:
        row["count"] += cat_counts.pop(row["category"], 0)
    by_category += [{"category": c, "count": n} for c, n in cat_counts.items()]
    by_category.sort(key=lambda x: x["count"], reverse=True)

    cities = [dict(x) for x in FX.SEED_TRENDS["cities"]]
    for row in cities:
        row["count"] += city_counts.pop(row["city"], 0)
    cities += [{"city": c, "count": n} for c, n in city_counts.items()]
    cities.sort(key=lambda x: x["count"], reverse=True)

    today = _now()[:10]
    by_day = [dict(x) for x in FX.SEED_TRENDS["by_day"]]
    todays_live = sum(1 for r in verified if (r.get("created_at") or "").startswith(today))
    if by_day and by_day[-1]["day"] == today:
        by_day[-1]["count"] += todays_live
    elif todays_live:
        by_day.append({"day": today, "count": todays_live})

    return {
        "total_reports": FX.SEED_TRENDS["total_reports"] + len(verified),
        "by_category": by_category,
        "by_day": by_day[-7:],
        "top_indicators": sorted(
            STORE.indicators_map().values(),
            key=lambda i: i["report_count"], reverse=True)[:10],
        "cities": cities[:6],
        "live_reports": len(verified),
    }


class RecoveryIn(BaseModel):
    what: str = "paid"  # paid | shared_otp | clicked_link — changes the kit
    amount: int = 0
    channel: str = "upi"
    bank: str = ""
    incident_date: str = ""  # user-entered; NEVER assumed to be today
    lang: str = "hi-IN"


@app.post("/api/recovery/kit")
def recovery_kit(body: RecoveryIn):
    """H14: the incident type genuinely changes the guidance. Unknown facts
    stay blank ("____"), the date is the user's (never assumed today), and a
    fraud-induced payment is described as exactly that — the victim was
    deceived into authorizing it (not an 'unauthorized transaction', which
    would misstate what the bank will see). No promises of recovery."""
    what = body.what if body.what in ("paid", "shared_otp", "clicked_link") else "paid"
    date = re.sub(r"[^\w\s:\-/.]", "", body.incident_date.strip())[:30] or "____"
    amount = body.amount if 0 < body.amount < 10**9 else None
    amt = f"₹{amount}" if amount else "₹____"
    bank = body.bank.strip()[:60] or "आपका बैंक"
    channel = re.sub(r"\W", "", body.channel.upper())[:15] or "UPI"

    if what == "paid":
        call_1930 = (
            f"1930 पर कॉल करके बोलें: 'मेरे साथ online fraud हुआ है। दिनांक {date} को {amt} "
            f"{bank} खाते से {channel} द्वारा गए हैं — मुझसे धोखे से यह payment करवाया गया। "
            "कृपया complaint दर्ज करें और transaction पर hold का अनुरोध करें।' "
            "मिलने वाला acknowledgement/ref number लिखना न भूलें।"
        )
        complaint = (
            f"cybercrime.gov.in → Report → Financial Fraud चुनें। विवरण: दिनांक {date}, राशि {amt}, "
            f"माध्यम {channel}, बैंक {bank}। जो message/number/UPI ID मिला वह attach करें। "
            "Complaint number संभाल कर रखें।"
        )
        letter = (
            f"सेवा में, शाखा प्रबंधक, {bank}। विषय: धोखे से करवाया गया {channel} भुगतान {amt} (दिनांक {date})। "
            "महोदय, मुझसे fraud द्वारा उक्त भुगतान करवाया गया है। कृपया मेरी लिखित शिकायत दर्ज कर "
            "transaction dispute प्रक्रिया शुरू करें और खाते पर अस्थायी सुरक्षा (freeze/limit) लगाएँ। "
            "1930/cybercrime complaint number: ____। — खाताधारक"
        )
        checklist = [
            "सबसे पहले 1930 पर कॉल करें — जितनी जल्दी, hold की संभावना उतनी बेहतर",
            "cybercrime.gov.in पर complaint दर्ज करें",
            f"{bank} की app/branch में transaction dispute दर्ज करें",
            "Message, number, UPI ID के screenshot सुरक्षित रखें — कुछ delete न करें",
            "उसी scammer से दोबारा बात न करें — 'refund दिलाने वाले' भी ठग होते हैं",
        ]
    elif what == "shared_otp":
        call_1930 = (
            f"1930 पर कॉल करके बोलें: 'दिनांक {date} को मैंने धोखे में अपना OTP/PIN बता दिया। "
            f"खाता {bank} में है। अभी तक कटी राशि: {amt if amount else 'जाँच रहा/रही हूँ'}। "
            "कृपया complaint दर्ज करें।' कोई राशि कटी हो तो transaction details साथ रखें।"
        )
        complaint = (
            f"पहले app/netbanking से UPI और cards को TEMPORARILY FREEZE/BLOCK करें, फिर "
            f"cybercrime.gov.in पर complaint करें। विवरण: दिनांक {date}, OTP/PIN साझा हुआ, बैंक {bank}। "
            "जो भी transaction दिखे उसका screenshot जोड़ें।"
        )
        letter = (
            f"सेवा में, शाखा प्रबंधक, {bank}। विषय: OTP/PIN compromise (दिनांक {date}) — खाता सुरक्षा। "
            "महोदय, धोखे से मेरा OTP/PIN किसी और के हाथ लगा है। कृपया मेरा debit card व UPI तुरंत block कर "
            "नया PIN जारी करें, और खाते की हाल की गतिविधि की जाँच करें। — खाताधारक"
        )
        checklist = [
            "बैंक app से UPI + cards तुरंत freeze/block करें (सबसे पहला काम)",
            "बैंक के official नंबर पर call करके card block confirm करें",
            "net-banking/UPI PIN और बैंक से जुड़े passwords बदलें",
            "statement देखें — कोई राशि कटी हो तो तुरंत 1930 पर कॉल करें",
            "अनजान 'bank वाले' की दोबारा call आए तो काट दें — बैंक OTP कभी नहीं माँगता",
        ]
    else:  # clicked_link
        call_1930 = (
            f"अगर कोई राशि कटी है तो 1930 पर बोलें: 'दिनांक {date} को fraud link के ज़रिए "
            f"{amt if amount else '____'} कटे हैं, खाता {bank}।' कुछ नहीं कटा है तो 1930 ज़रूरी नहीं — "
            "पहले नीचे की सुरक्षा checklist पूरी करें।"
        )
        complaint = (
            f"cybercrime.gov.in → Report Suspect URL/Fraud पर वह link report करें। विवरण: दिनांक {date}। "
            "Link पर जो भी भरा हो (number, card, OTP) वह complaint में लिखें — पर यहाँ किसी और को न भेजें।"
        )
        letter = (
            f"सेवा में, शाखा प्रबंधक, {bank}। विषय: phishing link (दिनांक {date}) — एहतियातन खाता सुरक्षा। "
            "महोदय, मैंने धोखे वाले link पर विवरण भर दिया है। कृपया एहतियातन मेरा card/UPI block कर नया जारी "
            "करें और खाते पर नज़र रखें। — खाताधारक"
        )
        checklist = [
            "link पर कुछ भरा था? → वे passwords/PIN अभी दूसरे device से बदलें",
            "कोई app/APK install हुई हो तो तुरंत uninstall करें, फिर phone restart करें",
            "बैंक app से card/UPI temporarily freeze करें अगर card details भरी थीं",
            "statement पर 48 घंटे नज़र रखें — कुछ कटे तो तुरंत 1930",
            "वह link किसी को forward न करें — cybercrime.gov.in पर report करें",
        ]

    return {
        "call_script_1930": call_1930,
        "complaint_draft": complaint,
        "bank_letter": letter,
        "checklist": checklist,
        "what": what, "incident_date": date,
        # deterministic template kit — personalised by branching, not by AI
        "mocked": True,
    }


# ---------------------------------------------------------------- WhatsApp bot
# Twilio WhatsApp sandbox webhook (H13): scams arrive on WhatsApp, so the
# shield answers there. Reply is TwiML; latency sits inside Twilio's ~15s
# webhook window. H14 hardening: request-signature validation (HMAC-SHA1 per
# Twilio spec) enforced whenever TWILIO_AUTH_TOKEN is configured; in prod
# (VERCEL) with WA_REQUIRE_SIGNATURE=1 an unsigned webhook is rejected even
# without the token (fail closed). The sandbox itself is PARKED on a trial
# account — transport auth is verified by unit test, not by live Twilio.
_WA_VERDICT = {
    "danger": ("🛑", "खतरा", "DANGER"),
    "suspicious": ("⚠️", "सावधान", "SUSPICIOUS"),
    "no_known_risk": ("🟢", "कोई ज्ञात खतरा नहीं", "NO KNOWN RISK"),
}
_WA_MAX_BODY = 2000


def _twilio_signature_ok(request: Request, form: dict) -> bool:
    """Twilio X-Twilio-Signature: base64(HMAC-SHA1(auth_token, url + sorted
    concatenated POST params)). No token configured -> gated by env policy."""
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    if not token:
        # fail closed only when explicitly required (the sandbox is parked;
        # local tests and the curl demo run without transport auth)
        return not (os.getenv("VERCEL") and os.getenv("WA_REQUIRE_SIGNATURE") == "1")
    import base64
    import hmac
    url = os.getenv("WA_PUBLIC_URL", "").strip() or str(request.url)
    payload = url + "".join(k + form[k] for k in sorted(form))
    digest = base64.b64encode(
        hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()
    return hmac.compare_digest(digest, request.headers.get("x-twilio-signature", ""))


def _wa_reply(msg: str) -> Response:
    twiml = ('<?xml version="1.0" encoding="UTF-8"?><Response><Message>'
             + _xml_escape(msg) + "</Message></Response>")
    return Response(content=twiml, media_type="application/xml")


@app.post("/api/whatsapp")
async def whatsapp_webhook(request: Request):
    form_raw = await request.form()
    form = {k: str(v) for k, v in form_raw.items() if isinstance(v, str)}
    if not _twilio_signature_ok(request, form):
        return JSONResponse({"error": "invalid signature"}, status_code=403)

    body_text = form.get("Body", "").strip()[:_WA_MAX_BODY]
    num_media = form.get("NumMedia", "0")
    if num_media not in ("", "0"):
        # honesty: image/QR/voice over WhatsApp is NOT implemented — say so
        # instead of silently checking an empty caption.
        return _wa_reply(
            "📷 अभी WhatsApp पर photo/QR/voice जाँच नहीं होती — QR की जाँच के लिए "
            "dhaal-delta.vercel.app/check खोलें, या message का TEXT यहाँ paste करें।\n"
            "Photo/QR/voice checks are not supported on WhatsApp yet — use "
            "dhaal-delta.vercel.app/check, or paste the message text here.")
    if not body_text or body_text.lower().startswith("join "):
        return _wa_reply(
            "🛡️ ढाल Dhaal में आपका स्वागत है!\n"
            "कोई भी suspicious message, link, UPI ID या number यहाँ forward करें — "
            "तुरंत बताएँगे कि ठगी है या नहीं।\n"
            "Forward any suspicious message — Dhaal checks it instantly.")

    doc = check(CheckIn(type="text", payload=body_text, lang="hi-IN"))
    # Same assessment semantics as the web app (H14): an unassessed input
    # leads with the QUESTION — never a green verdict above a context ask.
    if doc["assessment"] != "assessed":
        lines = ["❓ *और जानकारी चाहिए · More info needed*", "",
                 doc["explanation_hi"]]
        lines += ["", "— ढाल Dhaal · dhaal-delta.vercel.app"]
        return _wa_reply("\n".join(lines))

    icon, v_hi, v_en = _WA_VERDICT[doc["verdict"]]
    lines = [f"{icon} *{v_hi} · {v_en}*", "", doc["explanation_hi"]]
    top = [s for s in doc["signals"] if s["source"] != "llm_pattern" and s["weight"] > 0][:3]
    if top:
        lines += ["", "*संकेत · Signals:*"]
        lines += [f"• {s['title_hi']} (+{s['weight']})" for s in top]
    if doc["verdict"] == "danger":
        lines += ["", "🚑 ठगे गए हों तो पहले घंटे में 1930 पर call करें · dhaal-delta.vercel.app/recover"]
    lines += ["", "— ढाल Dhaal · dhaal-delta.vercel.app"]
    return _wa_reply("\n".join(lines))

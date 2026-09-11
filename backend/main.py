"""Dhaal (ढाल) — backend stub API. Serves every contract in docs/CONTRACTS.md from minute 1.

Engine lane (Harsh) replaces the marked sections with the real signal engine, Claude,
Sarvam and Atlas — the shapes here are the contract, do not drift from CONTRACTS.md.
Stub keeps a deterministic mini-engine so the golden path demos end-to-end immediately.
"""
import hashlib
import json
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

import exotel
import fixtures as FX
import llm
import sarvam
import wa_meta
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
    # H15 verdict-first: fast=true returns the deterministic result immediately
    # (grounded rules explanation, no LLM/TTS wait); the client then calls
    # POST /api/check/{id}/narration to enrich in place. The verdict is
    # already final either way — narration can never change it.
    fast: bool = False


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
# H15 (held-out v3 misses — post-publication fixes; published scores stand):
_ACCOUNT_RE = re.compile(r"\b\d{9,18}\b")           # bank a/c number shape
_IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")  # IFSC shape
_REFERENT_RE = re.compile(  # "send IT", "yeh sahi hai na" — pronoun, no object
    r"\b(?:it|this|that|yeh|ye|woh|wo|isko|usko|iska|uska)\b|यह|वह|इसे|उसे|इसको|उसको",
    re.I)


# H16 §4B: per-reason clarification options — a CONTROLLED decision tree, not
# a chatbot. Each option maps to a deterministic, source-labelled context
# signal (weight applied ADDITIVELY — user answers can add risk or leave it,
# never subtract engine evidence). "dont_know" keeps the question open with a
# next step instead of fake certainty.
_CLARIFY_OPTIONS: dict[str, list[dict]] = {
    "bare_identifier": [
        {"id": "asked_money", "hi": "पैसे माँगे गए", "en": "They asked for money"},
        {"id": "asked_otp", "hi": "OTP/PIN माँगा", "en": "They asked for an OTP/PIN"},
        {"id": "says_refund", "hi": "Refund/इनाम देने की बात है", "en": "They promise a refund/prize"},
        {"id": "just_contact", "hi": "बस call/message आया, कुछ माँगा नहीं", "en": "Just a call/message, no ask"},
        {"id": "dont_know", "hi": "पता नहीं", "en": "I don't know"},
    ],
    "threat_no_ask": [
        {"id": "asked_money", "hi": "पैसे माँगे", "en": "They demanded money"},
        {"id": "asked_otp", "hi": "OTP/password माँगा", "en": "They demanded an OTP/password"},
        {"id": "no_demand", "hi": "कुछ नहीं माँगा (अभी)", "en": "No demand (yet)"},
        {"id": "dont_know", "hi": "पता नहीं", "en": "I don't know"},
    ],
    "no_referent": [],
    "too_short": [],
    "unreadable_payment_code": [],
}

_CLARIFY_SIGNALS: dict[str, tuple[int, str, str, str, str]] = {
    "asked_money": (30, "You reported: money was demanded", "आपने बताया: पैसे माँगे गए",
                    "A demand for money from an unknown contact is the core scam move — do not send anything.",
                    "अनजान से पैसों की माँग ही ठगी की असली चाल है — कुछ न भेजें।"),
    "asked_otp": (35, "You reported: OTP/PIN was demanded", "आपने बताया: OTP/PIN माँगा गया",
                  "Nobody legitimate asks for your OTP/PIN — refuse and disconnect.",
                  "OTP/PIN कोई भी सही संस्था नहीं माँगती — मना करें, call काटें।"),
    "says_refund": (25, "You reported: a refund/prize is promised", "आपने बताया: refund/इनाम का वादा",
                    "Refund/prize promises from unknown identifiers are bait — real refunds arrive without your help.",
                    "अनजान पते से refund/इनाम का वादा चारा है — असली refund अपने-आप आता है।"),
}


def _clarify_options(reason: str) -> list[dict]:
    return list(_CLARIFY_OPTIONS.get(reason, []))


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
    # bank a/c (+IFSC) alone — identifier, not evidence (v3-060)
    if len(t.split()) <= 8 and _ACCOUNT_RE.search(t) \
            and (_IFSC_RE.search(t) or ("खाता" in t or "account" in t.lower())):
        return "needs_context", {
            "reason": "bare_identifier",
            "question_hi": "यह खाता किसने, किस लिए भेजा? साथ आया message paste करें — तभी जाँच का मतलब है।",
            "question_en": "Who sent this account, and for what? Paste the message that came with it — then the check means something.",
        }
    # a threat with NO ask cannot be cleared OR convicted — ask for the ask
    # (v3-059: "अंजाम भुगतना पड़ेगा" scored low and read as clean)
    pressure = facts.get("pressure", [])
    if pressure and not facts.get("requested_actions") \
            and any(k in pressure for k in ("threat_framing", "coercion_extortion")):
        return "needs_context", {
            "reason": "threat_no_ask",
            "question_hi": "यह धमकी है — पर वे आपसे करवाना क्या चाहते हैं? पैसे, OTP, कोई link? जो कहा गया वह paste करें। डर लगे तो 1930 भी है।",
            "question_en": "This reads as a threat — but what are they asking you to DO? Money, OTP, a link? Paste what they said. If you feel unsafe, 1930 is there too.",
        }
    # payment-shaped gibberish: mentions upi/pa=/am= in a broken shape that
    # never parsed — unreadable, never clean (v4-106/108 shapes)
    if p is None and len(t.split()) <= 10 \
            and re.search(r"\bupi\b|\bupi:?/", t, re.I) \
            and re.search(r"pa\s*=|am\s*=|amount|@ok[a-z]{2,}|scan", t, re.I):
        return "unsupported_input", {
            "reason": "unreadable_payment_code",
            "question_hi": "यह payment code टूटा हुआ लग रहा है — original QR दुबारा scan करें या पूरा message paste करें।",
            "question_en": "This looks like a broken payment code — rescan the original QR or paste the full message.",
        }
    # a bare short DEMAND with no identifier/context: whose demand? for what?
    # ("paisa bhej do bhai" must ask, not clear — v4-088/089)
    if len(t.split()) <= 6 and score < engine_mod.SUSPICIOUS_AT \
            and re.search(r"paise?|पैसे|₹|bhej|भेज|transfer|send", t, re.I) \
            and re.search(r"bhej|भेज|send|transfer|de\s+do|दे\s+दो", t, re.I) \
            and not (_BARE_VPA_RE.search(t) or re.search(r"\d{6,}", t)
                     or "http" in t.lower()):
        return "needs_context", {
            "reason": "bare_demand",
            "question_hi": "कौन माँग रहा है, और किस लिए? जो message/call आया था वह पूरा paste करें — माँग अकेले जाँच नहीं होती।",
            "question_en": "WHO is asking, and for what? Paste the full message/call — a demand alone can't be checked.",
        }
    # qr/scan referent fragments: "QR scan karke bata" names nothing checkable
    if len(t.split()) <= 7 and re.search(r"\bqr\b|scan", t, re.I) \
            and not (p or "http" in t.lower()) \
            and re.search(r"bata|बता|sahi|सही|check|karu|karun|\?", t, re.I):
        return "needs_context", {
            "reason": "no_referent",
            "question_hi": "कौन-सा QR? उसकी photo QR tab में डालें या उसमें लिखा upi:// text paste करें — तभी जाँच होगी।",
            "question_en": "WHICH QR? Upload its photo in the QR tab or paste its upi:// text — then it can be checked.",
        }
    # a bare bank account (+IFSC) with no story: an identifier is not a
    # message — ask what came WITH it (v5-105 family; same treatment a bare
    # phone number already gets)
    if len(t.split()) <= 10 and score < engine_mod.SUSPICIOUS_AT \
            and (re.search(r"(?:खाता|a/?c|account)[^0-9]{0,6}[\d\s]{8,22}", t, re.I)
                 or (_ACCOUNT_RE.search(t)
                     and re.search(r"ifsc|आईएफ़?एससी", t, re.I))) \
            and not re.search(r"debit|credit|balance|txn|ref\b", t, re.I):
        return "needs_context", {
            "reason": "bare_identifier",
            "question_hi": "यह खाता नंबर किसने भेजा, और किस लिए? साथ आया पूरा message paste करें — अकेला नंबर जाँचा नहीं जा सकता।",
            "question_en": "WHO sent this account number, and for what? Paste the message that came with it — a bare number can't be judged.",
        }
    words = len(t.split())
    if words < 4 and not (p and p.get("status") == "valid"):
        return "needs_context", {
            "reason": "too_short",
            "question_hi": "यह किस बारे में है? जो message/call आया था, वह पूरा paste करें — तब सही जाँच होगी।",
            "question_en": "What is this about? Paste the full message or describe the call — then the check means something.",
        }
    # short question about an unnamed "it" — nothing to check yet (v3-061/062)
    if words <= 7 and _REFERENT_RE.search(t) \
            and ("?" in t or re.search(r"\b(na|kya|क्या|sahi|सही)\b", t, re.I)) \
            and not (_BARE_VPA_RE.search(t) or _ACCOUNT_RE.search(t)
                     or "http" in t.lower() or (p and p.get("status") == "valid")):
        return "needs_context", {
            "reason": "no_referent",
            "question_hi": "किसकी बात हो रही है? वह link/QR/UPI ID या message यहाँ paste करें — तब बताएँगे सही है या नहीं।",
            "question_en": "Checking WHAT, exactly? Paste that link/QR/UPI ID or message here — then we can actually answer.",
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
        if needs_context is not None:  # H16: the smallest useful question,
            # with a controlled option tree where one exists
            needs_context["options"] = _clarify_options(needs_context["reason"])

    # Claude narrates FROM the detected signals (zero verdict weight); any
    # failure or MOCK_MODE -> grounded rule-composed fallback (never generic
    # accusations). Narration may explain; it may not change validated facts,
    # the verdict, or the transaction-type label.
    exp_hi = exp_en = None
    mocked = True
    narration_ms = 0
    if not MOCK_MODE and assessment == "assessed" and not body.fast:
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
    if body.speak and not MOCK_MODE and not body.fast:
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


class ClarifyIn(BaseModel):
    answer_id: str | None = None  # one of needs_context.options[].id
    text: str | None = None       # or a free-text answer


@app.post("/api/check/{cid}/clarify")
def clarify_check(cid: str, body: ClarifyIn):
    """H16 §4B targeted clarification. The original message is preserved; the
    answer is stored as STRUCTURED user-provided context and scored as
    source="user_context" signals — additive only. Engine evidence from the
    original text always persists (a reassuring answer never erases a direct
    dangerous demand). One round only; "dont_know" keeps honest uncertainty
    with a next step instead of a verdict."""
    doc = STORE.get("checks", cid)
    if not doc:
        return JSONResponse({"error": "check not found"}, status_code=404)
    if doc.get("assessment") != "needs_context":
        return JSONResponse({"error": "nothing to clarify on this check"},
                            status_code=409)
    if doc.get("user_context"):
        return JSONResponse(
            {"error": "already clarified — run a fresh check with the full message"},
            status_code=409)
    answer_id = (body.answer_id or "").strip()
    free_text = (body.text or "").strip()[:500]
    if not answer_id and not free_text:
        return JSONResponse({"error": "answer_id or text required"}, status_code=422)
    reason = (doc.get("needs_context") or {}).get("reason", "")
    valid_ids = {o["id"] for o in _clarify_options(reason)}
    if answer_id and answer_id not in valid_ids:
        return JSONResponse({"error": "unknown answer_id for this question"},
                            status_code=422)

    # re-run the engine on the ORIGINAL payload — original evidence persists
    payload = doc["input"]["payload"]
    verdict, score, signals, category, facts = run_signal_engine(
        payload, doc["input"]["type"], STORE.indicators_map(),
        allow_network=not MOCK_MODE, expected_intent=doc.get("expected_intent"))

    ctx_signals = []
    if answer_id in _CLARIFY_SIGNALS:
        w, t_en, t_hi, d_en, d_hi = _CLARIFY_SIGNALS[answer_id]
        ctx_signals.append({"id": f"user_context_{answer_id}",
                            "source": "user_context", "weight": w,
                            "title_en": t_en, "title_hi": t_hi,
                            "detail_en": d_en, "detail_hi": d_hi})
    elif free_text:
        # the user's own description is genuine added evidence: run the engine
        # over the ANSWER alone and carry its findings, relabelled by source —
        # never pretending they appeared in the original message.
        _v2, _s2, ans_signals, _c2, _f2 = run_signal_engine(
            free_text, "text", STORE.indicators_map(), allow_network=not MOCK_MODE)
        for s in ans_signals:
            if s["weight"] > 0:
                ctx_signals.append({**s, "id": f"user_context_{s['id']}",
                                    "source": "user_context"})

    new_score = min(100, score + sum(s["weight"] for s in ctx_signals))
    all_signals = sorted(signals + ctx_signals,
                         key=lambda s: s["weight"], reverse=True)

    if answer_id in ("dont_know",):
        assessment, verdict2 = "needs_context", None
        exp_hi = ("ठीक है — बिना पूरी बात के हम अंदाज़ा नहीं लगाएँगे। सबसे सुरक्षित कदम: "
                  "कुछ भी न भेजें, और जो message/call आया था वह किसी भरोसेमंद को दिखाएँ "
                  "या पूरा paste करके दुबारा जाँचें। शक बना रहे तो 1930 है।")
        exp_en = ("Okay — without the full story we won't guess. Safest step: send "
                  "nothing, show the message/call to someone you trust, or paste the "
                  "full text and re-check. If worry stays, 1930 exists.")
    else:
        assessment = "assessed"
        verdict2 = ("danger" if new_score >= engine_mod.DANGER_AT
                    else "suspicious" if new_score >= engine_mod.SUSPICIOUS_AT
                    else "no_known_risk")
        top_ctx = ctx_signals[0] if ctx_signals else None
        base_hi, base_en = _grounded_explanation(assessment, verdict2,
                                                 all_signals, facts, None)
        if top_ctx:
            exp_hi = f"आपके जवाब के बाद ({top_ctx['title_hi']}): {base_hi}"
            exp_en = f"After your answer ({top_ctx['title_en']}): {base_en}"
        else:
            exp_hi = f"आपके जवाब के बाद भी नई जानकारी नहीं मिली। {base_hi}"
            exp_en = f"Your answer added no new evidence. {base_en}"

    user_context = [{"question_reason": reason, "answer_id": answer_id or None,
                     "text": free_text or None, "at": _now()}]
    what_changed = {
        "before": {"assessment": "needs_context", "verdict": None},
        "after": {"assessment": assessment, "verdict": verdict2, "score": new_score},
        "because_hi": (ctx_signals[0]["title_hi"] if ctx_signals
                       else "जवाब से कोई नया संकेत नहीं जुड़ा"),
        "because_en": (ctx_signals[0]["title_en"] if ctx_signals
                       else "the answer added no new signal"),
    }
    updates = {
        "assessment": assessment, "verdict": verdict2, "score": new_score,
        "signals": all_signals, "explanation_hi": exp_hi, "explanation_en": exp_en,
        "explanation_source": "rules", "user_context": user_context,
        "needs_context": (doc.get("needs_context") if assessment == "needs_context"
                          else None),
        "what_changed": what_changed, "clarified_at": _now(),
    }
    STORE.update("checks", cid, updates)
    # guardian view follows the clarified state — UPDATE the existing request
    # (never a duplicate notification)
    if doc.get("_id") and assessment == "assessed":
        for gr in STORE.list("guardian_requests", {"check_id": cid}):
            STORE.update("guardian_requests", gr["_id"], {
                "verdict": verdict2, "score": new_score, "assessment": assessment,
                "status": ("pending" if verdict2 != "no_known_risk"
                           and gr.get("status") == "noted" else gr.get("status")),
                "summary_hi": exp_hi[:140],
            })
    return {**doc, **updates}


class NarrateIn(BaseModel):
    speak: bool = False


@app.post("/api/check/{cid}/narration")
def narrate_check(cid: str, body: NarrateIn):
    """H15 verdict-first enrichment: upgrade a stored check's explanation to
    LLM narration (+TTS when asked) IN PLACE. Idempotent per check; never
    touches verdict/score/signals/category/guardian state — those were final
    when the check ran. Unknown id -> 404; unassessed checks keep their
    question; narration failure keeps the grounded rules text (no downgrade)."""
    doc = STORE.get("checks", cid)
    if not doc:
        return JSONResponse({"error": "check not found"}, status_code=404)

    def view(d, cached):
        return {"check_id": cid, "cached": cached,
                "explanation_hi": d["explanation_hi"],
                "explanation_en": d["explanation_en"],
                "explanation_source": d.get("explanation_source", "rules"),
                "tts_audio_b64": d.get("tts_audio_b64")}

    already_llm = doc.get("explanation_source") == "llm"
    if already_llm and (doc.get("tts_audio_b64") or not body.speak):
        return view(doc, True)

    updates = {}
    if not already_llm and not MOCK_MODE and doc.get("assessment") == "assessed":
        # H16 §7: SINGLE-FLIGHT — concurrent enrichment must not duplicate
        # paid LLM work. CAS claims the run; a racer gets the current grounded
        # text back untouched. Stale claims (dead instance) self-expire; total
        # attempts bounded so failures can't loop the meter forever.
        if int(doc.get("narration_attempts", 0)) >= 3:
            return view(doc, False)
        claim = STORE.update_if("checks", cid, {"narration_state": None},
                                {"narration_state": time.time(),
                                 "narration_attempts":
                                     int(doc.get("narration_attempts", 0)) + 1})
        if not claim:
            running_since = doc.get("narration_state")
            if isinstance(running_since, (int, float)) \
                    and time.time() - running_since > 60:
                claim = STORE.update_if("checks", cid,
                                        {"narration_state": running_since},
                                        {"narration_state": time.time()})
            if not claim:
                return view(doc, False)  # someone else is enriching — no dup
        t0 = time.perf_counter()
        out = llm.narrate(doc["input"]["payload"], doc["input"]["type"],
                          doc["verdict"], doc["score"], doc["signals"],
                          doc.get("scam_category"), facts=doc.get("facts"))
        print(f"[latency] narration_enrich_ms={round((time.perf_counter() - t0) * 1000)}")
        updates["narration_state"] = None  # release; retry allowed on failure
        if out:
            updates.update({"explanation_hi": out["explanation_hi"],
                            "explanation_en": out["explanation_en"],
                            "explanation_source": "llm", "mocked": False})
    merged = {**doc, **updates}
    if body.speak and not MOCK_MODE and not merged.get("tts_audio_b64"):
        audio = sarvam.text_to_speech(merged["explanation_hi"], lang="hi-IN")
        if audio:
            updates["tts_audio_b64"] = audio
            merged["tts_audio_b64"] = audio
    if updates:
        STORE.update("checks", cid, updates)
    return view(merged, False)


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
        # H17 field bug (the "speak is broken everywhere" report): browsers set
        # the multipart part type from Blob.type VERBATIM — Chromium records
        # "audio/mp4;codecs=opus" — and Saarika 4xxes on any ";codecs=..."
        # parameter while accepting the SAME bytes under the bare base type.
        # Strip parameters; never forward a parameterized content type.
        raw_ct = audio.content_type or "audio/webm"
        clean_ct = raw_ct.split(";")[0].strip() or "audio/webm"
        out = await run_in_threadpool(
            sarvam.speech_to_text, blob,
            audio.filename or "audio.webm", clean_ct,
        )
        if out:
            return {"transcript": out["transcript"],
                    "lang": out["language_code"] or lang_hint, "mocked": False}
        # H17 (same rule that retired the IVR fallback): the user SPOKE real
        # words — a failed transcription must be an honest error, never a
        # fixture passed off as what they said. The client offers typed input.
        return JSONResponse(status_code=503,
                            content={"status": "no_transcript",
                                     "detail": "transcription unavailable — type the message instead"})
    # MOCK_MODE only (explicit demo env, never prod): rehearsed fixture,
    # flagged mocked=true and rendered with a DEMO label client-side.
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
    # H16: ATOMIC single-use claim — the check-and-set makes exactly one
    # concurrent claimant win; every other racer sees claimed=True and 409s.
    won = STORE.update_if(
        "guardian_links", link["_id"], {"pair_code_claimed": False},
        {"pair_code_claimed": True, "claimed_at": _now(),
         "ward_token_sha256": _sha(ward_token)})
    if not won:
        return JSONResponse({"error": "code already used — ask your guardian for a fresh pairing"},
                            status_code=409)
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


def _contrib_id(rid: str, value: str) -> str:
    return f"ctb::{rid}::{re.sub(r'[.$ ]', '_', value)[:120]}"


@app.post("/api/reports/{rid}/verify")
def verify_report(rid: str, body: VerifyIn, request: Request):
    """H16 §6 — verification with a DURABLE contribution ledger. Every
    (report, identifier) pair is one ledger doc created exactly once
    (insert_new = single winner); apply marks done, reject marks reversed —
    each transition a CAS, so repeats and races cannot double-count, and
    rejection withdraws exactly this report's applied contributions. A crash
    between ledger and counter is DETECTABLE (ledger is truth) and repaired
    by POST /api/reports/reconcile, which recounts counters from the ledger.
    Verify on an already-verified report RESUMES missing contributions
    instead of pretending completion."""
    if not _mod_ok(request):
        return JSONResponse({"error": "moderator key required"}, status_code=401)
    r = STORE.get("reports", rid)
    if not r:
        return {"error": "report not found"}
    status = "verified" if body.action == "verify" else "rejected"
    contributions = _report_contributions(r)

    if status == "verified":
        if r.get("status") != "verified":
            r = STORE.update_if("reports", rid, {"status": r.get("status")}, {
                "status": "verified", "decided_at": _now(),
                "decided_via": "mod-key",
                "indicator_values": [c["value"] for c in contributions],
            }) or STORE.get("reports", rid) or r
            if r.get("status") != "verified":
                return r  # a concurrent decision won; report it as-is
        applied = 0
        for c in contributions:
            cid_ = _contrib_id(rid, c["value"])
            created = STORE.insert_new("contribs", {
                "_id": cid_, "report_id": rid, "value": c["value"],
                "type": c["type"], "category": r.get("category"),
                "done": False, "reversed": False, "created_at": _now(),
            })
            existing = STORE.get("contribs", cid_)
            if not created and existing and existing.get("done"):
                continue  # already applied exactly once
            # apply, then mark done. A crash between the two leaves done=False
            # with the counter bumped — reconcile recounts from the ledger.
            STORE.upsert_indicator(c["value"], c["type"], r.get("category"))
            STORE.update_if("contribs", cid_, {"done": False},
                            {"done": True, "applied_at": _now()})
            applied += 1
        out = STORE.get("reports", rid) or r
        out["contributions_applied_now"] = applied
        out["durable"] = not STORE_DEGRADED()
        return out

    # ---- reject: reverse exactly what THIS report applied ----
    if r.get("status") != "rejected":
        r = STORE.update_if("reports", rid, {"status": r.get("status")}, {
            "status": "rejected", "decided_at": _now(), "decided_via": "mod-key",
        }) or STORE.get("reports", rid) or r
    reversed_n = 0
    for c in contributions:
        cid_ = _contrib_id(rid, c["value"])
        won = STORE.update_if("contribs", cid_,
                              {"done": True, "reversed": False},
                              {"reversed": True, "reversed_at": _now()})
        if won:
            STORE.decrement_indicator(c["value"])
            reversed_n += 1
    out = STORE.get("reports", rid) or r
    out["contributions_reversed_now"] = reversed_n
    out["durable"] = not STORE_DEGRADED()
    return out


@app.post("/api/reports/reconcile")
def reconcile_reports(request: Request):
    """H16 §6 repair path: the ledger is the source of truth for LIVE
    contributions — recount every ledgered identifier's report_count as
    (#done && !reversed) and repair drift from crashes between ledger and
    counter. Also finishes half-applied entries (done=False on a verified
    report -> apply now). Seeded demo indicators (ind_seed_*) carry a fixture
    baseline with no ledger and are intentionally out of scope."""
    if not _mod_ok(request):
        return JSONResponse({"error": "moderator key required"}, status_code=401)
    contribs = STORE.list("contribs")
    repaired, completed = [], []
    # finish interrupted applications first
    for cb in contribs:
        if not cb.get("done") and not cb.get("reversed"):
            rep = STORE.get("reports", cb["report_id"])
            if rep and rep.get("status") == "verified":
                won = STORE.update_if("contribs", cb["_id"], {"done": False},
                                      {"done": True, "applied_at": _now(),
                                       "via": "reconcile"})
                if won:
                    completed.append(cb["_id"])
    contribs = STORE.list("contribs")
    by_value: dict[str, int] = {}
    for cb in contribs:
        by_value.setdefault(cb["value"], 0)
        if cb.get("done") and not cb.get("reversed"):
            by_value[cb["value"]] += 1
    ind = STORE.indicators_map()
    for value, want in by_value.items():
        row = ind.get(value)
        have = row["report_count"] if row else 0
        if row and str(row.get("_id", "")).startswith("ind_seed"):
            continue  # fixture baseline — not ledgered, documented exclusion
        if have != want:
            if row is None and want > 0:
                first = next(cb for cb in contribs if cb["value"] == value)
                STORE.upsert_indicator(value, first["type"], first.get("category"))
                STORE.set_indicator_count(value, want)
            else:
                STORE.set_indicator_count(value, want)
            repaired.append({"value": value, "from": have, "to": want})
    return {"ok": True, "completed_pending": completed, "repaired": repaired,
            "ledger_size": len(contribs), "durable": not STORE_DEGRADED()}


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


_WA_WELCOME = (
    "🛡️ ढाल Dhaal में आपका स्वागत है!\n"
    "कोई भी suspicious message, link, UPI ID या number यहाँ forward करें — "
    "तुरंत बताएँगे कि ठगी है या नहीं।\n"
    "Forward any suspicious message — Dhaal checks it instantly.")
_WA_MEDIA_UNSUPPORTED = (
    "📷 अभी WhatsApp पर photo/QR/voice जाँच नहीं होती — QR की जाँच के लिए "
    "dhaal-delta.vercel.app/check खोलें, या message का TEXT यहाँ paste करें।\n"
    "Photo/QR/voice checks are not supported on WhatsApp yet — use "
    "dhaal-delta.vercel.app/check, or paste the message text here.")


def _wa_text(doc: dict) -> str:
    """One WhatsApp answer for a check — shared verbatim by the Twilio TwiML
    path and the Meta Cloud API path so both channels carry the SAME
    assessment semantics: a question is never crowned with a green verdict,
    and the score is a rule-weight, never presented as a probability."""
    if doc["assessment"] != "assessed":
        lines = ["❓ *और जानकारी चाहिए · More info needed*", "",
                 doc["explanation_hi"]]
        lines += ["", "— ढाल Dhaal · dhaal-delta.vercel.app"]
        return "\n".join(lines)
    icon, v_hi, v_en = _WA_VERDICT[doc["verdict"]]
    lines = [f"{icon} *{v_hi} · {v_en}* — {doc['score']}/100 risk signals",
             "", doc["explanation_hi"]]
    top = [s for s in doc["signals"]
           if s["source"] != "llm_pattern" and s["weight"] > 0][:3]
    if top:
        lines += ["", "*संकेत · Signals:*"]
        lines += [f"• {s['title_hi']} (+{s['weight']})" for s in top]
    if doc["verdict"] == "danger":
        lines += ["", "🚑 ठगे गए हों तो पहले घंटे में 1930 पर call करें · dhaal-delta.vercel.app/recover"]
    lines += ["", "— ढाल Dhaal · dhaal-delta.vercel.app"]
    return "\n".join(lines)


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
        return _wa_reply(_WA_MEDIA_UNSUPPORTED)
    if not body_text or body_text.lower().startswith("join "):
        return _wa_reply(_WA_WELCOME)
    doc = check(CheckIn(type="text", payload=body_text, lang="hi-IN"))
    return _wa_reply(_wa_text(doc))


# ---------------------------------------------------------------- WhatsApp (Meta Cloud API)
# H15: the production WhatsApp lane. Meta's Cloud API test number allows
# custom webhooks on the free tier (what Twilio's trial blocked). Flow:
# victim forwards a message -> Meta POSTs here -> engine verdict -> reply in
# the same chat via the Graph API. Replies are inside Meta's 24h service
# window (we only ever answer an inbound message), so no template approvals.


@app.get("/api/wa/webhook")
def wa_webhook_verify(request: Request):
    """Meta's one-time subscription handshake: echo hub.challenge iff the
    verify token matches ours. Anything else -> 403."""
    q = request.query_params
    if (q.get("hub.mode") == "subscribe"
            and q.get("hub.verify_token", "") == os.getenv("WA_VERIFY_TOKEN", "").strip()
            and os.getenv("WA_VERIFY_TOKEN", "").strip()):
        return Response(content=q.get("hub.challenge", ""), media_type="text/plain")
    return JSONResponse({"error": "verification failed"}, status_code=403)


# --- H16 §5: durable inbound + outbox with real retries ----------------------
# Serverless truth (Vercel Python): nothing survives the response — so retry
# scheduling is DATA, not threads. Every accepted message is persisted BEFORE
# analysis; every reply lives in a per-event outbox with attempt history and
# next_attempt_at; delivery is driven by (a) the immediate in-request attempt,
# (b) opportunistic drains piggybacked on later webhook traffic, (c) the
# drain endpoint hit by Vercel Cron (Hobby tier: DAILY — minute-level cadence
# honestly requires an external pinger or paid cron; documented in CHANNELS).
# Delivery guarantee is AT-LEAST-ONCE: a transport timeout is ambiguous, we
# retry, and a rare duplicate reply is preferred over a silent drop.
_WA_BACKOFF_S = [60, 300, 900, 3600, 10800]
_WA_MAX_ATTEMPTS = 6
_WA_BATCH_INLINE = 4  # analyze at most this many messages inside one webhook
_WA_LEASE_STALE_S = 120
_WA_ACCEPT_STALE_S = 60
_WA_CONVO_TTL_S = 30 * 60


def _wa_classify(status: int) -> str:
    if 200 <= status < 300:
        return "sent"
    if status == 429 or status >= 500 or status == 0:
        return "transient"   # 0 = transport error/timeout — AMBIGUOUS, retry
    if status in (401, 403):
        return "config"      # bad/expired token: retry slowly once env fixed
    return "permanent"       # other 4xx: this message will never send


def _wa_outbox_attempt(ev: dict) -> dict:
    """One leased delivery attempt for an event's pending outbox. The CAS
    lease makes concurrent drains single-flight; stale leases (dead instance)
    are recovered by _wa_recover_stale."""
    now = _now()
    leased = STORE.update_if("wa_events", ev["_id"],
                             {"outbox_state": "pending"},
                             {"outbox_state": "sending", "lease_at": now})
    if not leased:
        return {"id": ev["_id"], "skipped": "not_pending_or_leased"}
    status = wa_meta.send_text(leased["from"], leased.get("reply_text", ""))
    attempts = list(leased.get("attempts", []))
    attempts.append({"at": now, "status": status,
                     "ambiguous_timeout": status == 0})
    klass = _wa_classify(status)
    n = len(attempts)
    if klass == "sent":
        fields = {"outbox_state": "sent", "replied": True, "sent_at": _now()}
    elif klass == "permanent" or n >= _WA_MAX_ATTEMPTS:
        fields = {"outbox_state": "failed_permanent", "replied": False}
    else:
        delay = (_WA_BACKOFF_S[min(n - 1, len(_WA_BACKOFF_S) - 1)]
                 if klass != "config" else 1800)
        fields = {"outbox_state": "pending",
                  "next_attempt_at": time.time() + delay}
    fields["attempts"] = attempts
    STORE.update("wa_events", ev["_id"], fields)
    return {"id": ev["_id"], "result": fields["outbox_state"], "status": status}


def _wa_queue_reply(msg_id: str, reply: str, check_id: str | None) -> dict:
    """Persist the reply into the event's outbox, then attempt immediately."""
    STORE.update("wa_events", msg_id, {
        "status": "analyzed", "check_id": check_id, "reply_text": reply,
        "outbox_state": "pending", "attempts": [],
        "next_attempt_at": time.time(),
    })
    return _wa_outbox_attempt(STORE.get("wa_events", msg_id))


def _wa_analyze_event(ev: dict) -> dict:
    """Analysis for one accepted event — runs inline OR from a drain
    (recovering work abandoned by a dead instance). Expensive engine/LLM work
    happens at most once per event (status CAS accepted->analyzing)."""
    won = STORE.update_if("wa_events", ev["_id"], {"status": "accepted"},
                          {"status": "analyzing"})
    if not won:
        return {"id": ev["_id"], "skipped": "already_analyzed"}
    sender, mtype = ev["from"], ev.get("mtype", "text")
    body_text = (ev.get("body_text") or "").strip()[:_WA_MAX_BODY]
    wa_meta.mark_read(ev["_id"])
    if mtype not in ("text", "button"):
        return _wa_queue_reply(ev["_id"], _WA_MEDIA_UNSUPPORTED, None)
    if not body_text or body_text.lower().startswith("join "):
        return _wa_queue_reply(ev["_id"], _WA_WELCOME, None)

    # sender-scoped clarification (expiring): a short answer after our
    # question routes into the SAME check instead of a fresh one
    convo = STORE.get("wa_convo", sender)
    if convo and convo.get("expires_at", 0) > time.time():
        answer_id = None
        low = body_text.lower()
        if re.search(r"paise|पैसे|money|₹|rupay", low):
            answer_id = "asked_money"
        elif re.search(r"\botp\b|pin|password|पासवर्ड|ओटीपी", low):
            answer_id = "asked_otp"
        elif re.search(r"refund|रिफंड|इनाम|prize|cashback", low):
            answer_id = "says_refund"
        elif re.search(r"pata nahi|पता नहीं|nahi pata|don'?t know|idk", low):
            answer_id = "dont_know"
        body = ClarifyIn(answer_id=answer_id,
                         text=None if answer_id else body_text)
        out = clarify_check(convo["check_id"], body)
        STORE.update("wa_convo", sender, {"expires_at": 0})
        if isinstance(out, dict):  # clarified (JSONResponse means fall through)
            return _wa_queue_reply(ev["_id"], _wa_text(out), out["_id"])

    doc = check(CheckIn(type="text", payload=body_text, lang="hi-IN"))
    if doc["assessment"] == "needs_context":
        row = {"_id": sender, "check_id": doc["_id"],
               "reason": (doc.get("needs_context") or {}).get("reason"),
               "expires_at": time.time() + _WA_CONVO_TTL_S}
        if not STORE.insert_new("wa_convo", row):
            STORE.update("wa_convo", sender, row)
    return _wa_queue_reply(ev["_id"], _wa_text(doc), doc["_id"])


def _wa_recover_stale() -> dict:
    """Recover work abandoned mid-processing: stuck 'sending' leases back to
    pending; 'accepted'/'analyzing' events older than the stale window get
    (re)analyzed. Analysis re-run after an 'analyzing' crash may repeat the
    engine once — acceptable; outbox sends stay single-flight-leased."""
    now_t = time.time()
    recovered = {"leases": 0, "analyzed": 0}
    for ev in STORE.list("wa_events", {"outbox_state": "sending"}):
        try:
            stale = (datetime.now(timezone.utc)
                     - datetime.fromisoformat(ev.get("lease_at"))).total_seconds()
        except (TypeError, ValueError):
            stale = _WA_LEASE_STALE_S + 1
        if stale > _WA_LEASE_STALE_S or stale < 0:
            if STORE.update_if("wa_events", ev["_id"],
                               {"outbox_state": "sending"},
                               {"outbox_state": "pending",
                                "next_attempt_at": now_t}):
                recovered["leases"] += 1
    for status in ("accepted", "analyzing"):
        for ev in STORE.list("wa_events", {"status": status}):
            try:
                age = (datetime.now(timezone.utc)
                       - datetime.fromisoformat(ev["created_at"])).total_seconds()
            except (TypeError, ValueError):
                age = _WA_ACCEPT_STALE_S + 1
            if age > _WA_ACCEPT_STALE_S or age < 0:  # future-dated = skewed clock, recover anyway
                if status == "analyzing":  # dead mid-analysis: rewind first
                    if not STORE.update_if("wa_events", ev["_id"],
                                           {"status": "analyzing"},
                                           {"status": "accepted"}):
                        continue
                    ev = STORE.get("wa_events", ev["_id"])
                _wa_analyze_event(ev)
                recovered["analyzed"] += 1
    return recovered


def _wa_drain(cap: int = 10) -> dict:
    """Attempt every due pending outbox row (bounded)."""
    now_t = time.time()
    due = [ev for ev in STORE.list("wa_events", {"outbox_state": "pending"})
           if ev.get("next_attempt_at", 0) <= now_t]
    results = [_wa_outbox_attempt(ev) for ev in due[:cap]]
    return {"due": len(due), "attempted": len(results), "results": results}


@app.get("/api/wa/outbox/drain")   # Vercel Cron requests are GETs
@app.post("/api/wa/outbox/drain")
def wa_outbox_drain(request: Request):
    """Retry driver. Auth: moderator key, OR Vercel Cron's own
    `Authorization: Bearer $CRON_SECRET`, OR open locally."""
    auth = request.headers.get("authorization", "")
    cron_ok = (os.getenv("CRON_SECRET", "").strip()
               and auth == f"Bearer {os.getenv('CRON_SECRET').strip()}")
    if not (cron_ok or _mod_ok(request)):
        return JSONResponse({"error": "not authorized"}, status_code=401)
    recovered = _wa_recover_stale()
    drained = _wa_drain(cap=10)
    return {"ok": True, "recovered": recovered, **drained,
            "durable": not STORE_DEGRADED()}


@app.post("/api/wa/webhook")
async def wa_webhook(request: Request):
    raw = await request.body()
    # Meta signs every delivery with the app secret. Secret configured ->
    # invalid/missing signature is refused; unset locally -> open for tests.
    # H15 (external review): on Vercel a MISSING secret fails closed too — an
    # env regression must never silently disable transport auth in prod.
    if os.getenv("VERCEL") and not os.getenv("META_APP_SECRET", "").strip():
        return JSONResponse({"error": "webhook not configured"}, status_code=403)
    if not wa_meta.verify_signature(raw, request.headers.get("x-hub-signature-256", "")):
        return JSONResponse({"error": "invalid signature"}, status_code=403)
    try:
        payload = json.loads(raw.decode("utf-8"))
        entries = payload.get("entry") or []
    except Exception:
        return {"ok": True, "ignored": "unparseable"}  # 200: Meta must not retry junk

    accepted, deduped, ignored = [], [], 0
    inline_budget = _WA_BATCH_INLINE
    for entry in entries[:10]:
        for change in (entry.get("changes") or [])[:10]:
            value = change.get("value") or {}
            if "messages" not in value:
                ignored += 1  # delivery/read receipts — never analyzed
                continue
            for msg in (value.get("messages") or [])[:10]:
                msg_id = str(msg.get("id", ""))[:120]
                sender = str(msg.get("from", ""))[:20]
                if not msg_id or not sender:
                    continue
                mtype = msg.get("type", "")
                body_text = ""
                if mtype == "text":
                    body_text = str(msg.get("text", {}).get("body", ""))
                elif mtype == "button":
                    body_text = str(msg.get("button", {}).get("text", ""))
                # DURABLE ACCEPT before any analysis; atomic first-writer-wins
                # dedupe on the provider message id.
                fresh = STORE.insert_new("wa_events", {
                    "_id": msg_id, "from": sender, "mtype": mtype,
                    "body_text": body_text[:_WA_MAX_BODY],
                    "status": "accepted", "created_at": _now(),
                })
                if not fresh:
                    deduped.append(msg_id)
                    continue
                if inline_budget > 0:
                    inline_budget -= 1
                    _wa_analyze_event(STORE.get("wa_events", msg_id))
                accepted.append(msg_id)
    # opportunistic drain: webhook traffic doubles as the retry heartbeat
    piggy = _wa_drain(cap=3)
    return {"ok": True, "accepted": accepted, "deduped": deduped,
            "ignored_changes": ignored, "drained": piggy["attempted"]}


# ---------------------------------------------------------------- IVR (Exotel)
# H16: FEATURE DROPPED (owner decision). The lane stays in the codebase as
# retired reference, but production routes are DISABLED before any storage,
# fetching, inference, TTS or SMS can happen — a request to a retired route
# must never trigger paid compute, external calls, or a fabricated assessment.
# Re-enable deliberately with IVR_ENABLED=1 (plus Exotel env) if ever revived.
def IVR_ENABLED() -> bool:  # dynamic: tests exercise both states in-process
    return os.getenv("IVR_ENABLED", "").strip() == "1"


def _ivr_retired() -> JSONResponse:
    return JSONResponse(
        {"error": "IVR lane retired — feature dropped; see docs/CHANNELS.md"},
        status_code=410)


# H15 (historical design, retained for the retired lane):
#   Greeting (static prompt) -> Record (caller explains, beep-terminated)
#   -> Passthru  GET {API}/api/ivr/recording   (we ACK instantly, store the job)
#   -> Play/dynamic-greeting  GET {API}/api/ivr/result?CallSid=...
#      (THIS request does the work: fetch recording -> Saarika ASR -> engine
#       -> short spoken guidance -> Bulbul TTS @8kHz -> returns audio/wav)
# The split keeps the Passthru under Exotel's response deadline and is
# serverless-safe (no post-response background work on Vercel). A result SMS
# goes out best-effort so the caller keeps the guidance in hand. On any
# failure the result endpoint returns non-200 and the Exotel flow falls back
# to its static "call 1930 if worried" branch — the caller never hears dead air.

_IVR_MAX_AUDIO = 4 * 1024 * 1024  # 60s of call audio is ~0.5MB; 4MB is ample

# H15 hardening (external review): /api/ivr/result runs ASR+LLM+TTS — an
# unauthenticated compute path must not be free to hammer. Same per-instance
# sliding window as pair-code claims; real calls arrive far slower than this.
_IVR_WINDOW: deque = deque()
_IVR_MAX_PER_MIN = 6


def _ivr_rate_ok() -> bool:
    now = time.monotonic()
    while _IVR_WINDOW and now - _IVR_WINDOW[0] > 60:
        _IVR_WINDOW.popleft()
    if len(_IVR_WINDOW) >= _IVR_MAX_PER_MIN:
        return False
    _IVR_WINDOW.append(now)
    return True


def _ivr_script(doc: dict) -> tuple[str, str]:
    """(spoken_hi, sms_text) — SHORT by design: one verdict sentence + one
    action, phone-listenable; the SMS carries the same content + 1930."""
    if doc["assessment"] != "assessed":
        spoken = ("आपकी बात पूरी समझ नहीं आई। जो message या call आया था, उसकी पूरी बात "
                  "बताते हुए दुबारा call करें। तब तक किसी को पैसे या OTP न दें।")
        sms = "ढाल Dhaal: पूरी जानकारी के बिना जाँच अधूरी है। दुबारा call करके पूरी बात बताएँ। तब तक पैसे/OTP किसी को न दें। धोखा हो तो 1930 पर call करें।"
        return spoken, sms
    if doc["verdict"] == "danger":
        top = next((s for s in doc["signals"] if s["weight"] > 0), None)
        why = f" {top['title_hi']}।" if top else ""
        spoken = (f"सावधान! यह ठगी लगती है।{why} पैसे बिल्कुल न भेजें, OTP किसी को न बताएं, "
                  "और फोन काट दें। ठगी हो चुकी हो तो तुरंत 1930 पर call करें।")
        sms = f"ढाल Dhaal: 🛑 खतरा ({doc['score']}/100 risk)।{why} पैसे न भेजें, OTP न बताएं। ठगी होने पर पहले घंटे में 1930 पर call करें।"
    elif doc["verdict"] == "suspicious":
        spoken = ("सावधान रहें — इसमें शक की बातें मिली हैं। अभी कुछ भी न भेजें। "
                  "पहले बैंक या उस संस्था के official नंबर पर खुद call करके पक्का करें।")
        sms = f"ढाल Dhaal: ⚠️ सावधान ({doc['score']}/100 risk)। अभी कुछ न भेजें — official नंबर से खुद पक्का करें। धोखा लगे तो 1930।"
    else:
        spoken = ("इसमें कोई जाना-पहचाना खतरा नहीं मिला। फिर भी पैसे भेजने से पहले "
                  "नाम और नंबर खुद जाँच लें। शक हो तो 1930 पर call करें।")
        sms = "ढाल Dhaal: 🟢 कोई ज्ञात खतरा नहीं। फिर भी भेजने से पहले नाम-नंबर खुद जाँचें। शक हो तो 1930।"
    return spoken, sms


def _ivr_params(request: Request, form: dict | None = None) -> dict:
    """Exotel sends params as query (Passthru/greeting) or form (callbacks);
    accept both, tolerate their naming variants."""
    p = {**{k: v for k, v in request.query_params.items()}, **(form or {})}
    return {
        "call_sid": (p.get("CallSid") or p.get("callSid") or "").strip()[:80],
        "from": (p.get("CallFrom") or p.get("From") or "").strip()[:20],
        "recording_url": (p.get("RecordingUrl") or p.get("recording_url") or "").strip()[:500],
    }


@app.get("/api/ivr/recording")
@app.post("/api/ivr/recording")
async def ivr_recording(request: Request):
    """Exotel Passthru after the Record applet — ACK fast, store the job."""
    if not IVR_ENABLED():
        return _ivr_retired()
    form = {}
    if request.method == "POST":
        try:
            form = {k: str(v) for k, v in (await request.form()).items()}
        except Exception:
            form = {}
    p = _ivr_params(request, form)
    if not p["call_sid"]:
        return JSONResponse({"error": "CallSid required"}, status_code=422)
    existing = STORE.get("ivr_jobs", p["call_sid"])
    if not existing:
        STORE.insert("ivr_jobs", {
            "_id": p["call_sid"], "from": p["from"],
            "recording_url": p["recording_url"], "status": "received",
            "created_at": _now(),
        })
    elif p["recording_url"] and not existing.get("recording_url"):
        STORE.update("ivr_jobs", p["call_sid"],
                     {"recording_url": p["recording_url"]})
    return {"ok": True}


@app.get("/api/ivr/result")
def ivr_result(request: Request):
    """The dynamic-greeting fetch: does ASR -> engine -> TTS and returns the
    8 kHz WAV Exotel plays to the caller. Idempotent: replays serve the cache."""
    if not IVR_ENABLED():
        return _ivr_retired()
    p = _ivr_params(request)
    if not p["call_sid"]:
        return JSONResponse({"error": "CallSid required"}, status_code=422)
    job = STORE.get("ivr_jobs", p["call_sid"])
    # rate-limit only fresh computation — cached replays stay free
    if not (job and job.get("audio_b64")) and not _ivr_rate_ok():
        return JSONResponse({"error": "busy — retry shortly"}, status_code=429)
    if not job:  # result hit without a prior Passthru — build from own params
        job = {"_id": p["call_sid"], "from": p["from"],
               "recording_url": p["recording_url"], "status": "received",
               "created_at": _now()}
        STORE.insert("ivr_jobs", job)
    if job.get("audio_b64"):  # cached — Exotel retries/replays are free
        import base64 as _b64
        return Response(content=_b64.b64decode(job["audio_b64"]),
                        media_type="audio/wav")

    rec_url = job.get("recording_url") or p["recording_url"]
    transcript = None
    if rec_url:
        got = exotel.fetch_recording(rec_url)
        if got and len(got[0]) <= _IVR_MAX_AUDIO:
            blob, ctype = got
            out = sarvam.speech_to_text(
                blob, filename=rec_url.rsplit("/", 1)[-1][:60] or "call.mp3",
                content_type=ctype)
            transcript = out["transcript"] if out else None
    if not transcript:
        # H16: a missing recording or failed ASR must NEVER become a fabricated
        # transcript — assessing words the caller never said is worse than no
        # answer. Non-200 -> Exotel's static fallback branch speaks instead.
        STORE.update("ivr_jobs", p["call_sid"],
                     {"status": "no_transcript", "decided_at": _now()})
        return JSONResponse({"error": "recording could not be transcribed"},
                            status_code=503)

    doc = check(CheckIn(type="voice_transcript", payload=transcript, lang="hi-IN"))
    spoken, sms_text = _ivr_script(doc)
    audio_b64 = sarvam.text_to_speech(spoken, lang="hi-IN", sample_rate=8000)

    sms_sent = False
    if job.get("from"):
        sms_sent = exotel.send_sms(job["from"], sms_text)
    STORE.update("ivr_jobs", p["call_sid"], {
        "status": "done" if audio_b64 else "no_tts",
        "transcript": transcript[:500], "check_id": doc["_id"],
        "verdict": doc["verdict"], "assessment": doc["assessment"],
        "spoken": spoken, "sms_sent": sms_sent, "audio_b64": audio_b64,
        "decided_at": _now(),
    })
    if not audio_b64:
        # no TTS -> non-200 so the Exotel flow plays its static fallback
        # branch instead of dead air; the SMS (if configured) still went out.
        return JSONResponse({"error": "tts unavailable", "sms_sent": sms_sent},
                            status_code=503)
    import base64 as _b64
    return Response(content=_b64.b64decode(audio_b64), media_type="audio/wav")


@app.get("/api/ivr/jobs/{call_sid}")
def ivr_job(call_sid: str, request: Request):
    """Debug/inspection — transcript is caller PII, so moderator-gated."""
    if not IVR_ENABLED():
        return _ivr_retired()
    if not _mod_ok(request):
        return JSONResponse({"error": "moderator key required"}, status_code=401)
    job = STORE.get("ivr_jobs", call_sid)
    if not job:
        return JSONResponse({"error": "not found"}, status_code=404)
    return {k: v for k, v in job.items() if k != "audio_b64"}

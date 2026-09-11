"""Dhaal (ढाल) — backend stub API. Serves every contract in docs/CONTRACTS.md from minute 1.

Engine lane (Harsh) replaces the marked sections with the real signal engine, Claude,
Sarvam and Atlas — the shapes here are the contract, do not drift from CONTRACTS.md.
Stub keeps a deterministic mini-engine so the golden path demos end-to-end immediately.
"""
import os
import re
import uuid
from datetime import datetime, timezone
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
from engine import run_signal_engine
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


def canned_explanation(verdict, category):
    fx = FX.CANNED_EXPLANATIONS
    if category == "fake_collect":
        return fx["collect_hi"], fx["collect_en"]
    if category == "digital_arrest":
        return fx["arrest_hi"], fx["arrest_en"]
    if verdict == "no_known_risk":
        return fx["ok_hi"], fx["ok_en"]
    return fx["danger_hi"], fx["danger_en"]


# ---------------------------------------------------------------- endpoints
@app.get("/api/health")
def health():
    return {"ok": True, "mock_mode": MOCK_MODE, "store": STORE.active_name()}


class CheckIn(BaseModel):
    type: str = "text"
    payload: str
    lang: str = "hi-IN"
    speak: bool = False
    ward_link_id: str | None = None
    expected_intent: str | None = None  # "pay" | "receive" | "verify" — user's stated goal


_PRESSURE_IDS = {"urgency_framing": ("urgency", "जल्दबाज़ी"),
                 "secrecy_pressure": ("secrecy", "गोपनीयता का दबाव"),
                 "threat_framing": ("threat", "धमकी"),
                 "coercion_extortion": ("coercion", "ज़बरदस्ती")}


def _analysis(payload: str, signals: list) -> dict:
    """Structured 'what they want' — derived deterministically from the parsed
    signals (H12+ intermediate representation; no extra LLM call, no guesses)."""
    ids = {s["id"]: s for s in signals}
    claimed = None
    for sid in ("payee_impersonation", "lookalike_domain"):
        if sid in ids:
            m = re.search(r"(poses as|imitates the real|imitates) ([A-Z0-9]+)",
                          ids[sid]["detail_en"] + " " + ids[sid]["title_en"])
            claimed = (m.group(2) if m else None) or claimed
    asking = []
    if "upi_collect_request" in ids or "intent_mismatch" in ids:
        am = re.search(r"[?&]am=([\d.]+)", payload)
        asking.append({"what": "approve a payment", "hi": "payment approve कराना",
                       "amount": am.group(1) if am else None})
    if "credential_request" in ids:
        asking.append({"what": "your OTP/PIN/password", "hi": "आपका OTP/PIN/पासवर्ड", "amount": None})
    if "fee_demand" in ids or "advance_fee_refund" in ids:
        asking.append({"what": "an upfront fee", "hi": "पहले फीस", "amount": None})
    money_out = "upi_collect_request" in ids or "intent_mismatch" in ids \
        or "advance_fee_refund" in ids or "fee_demand" in ids
    pressure = [{"tag": v[0], "hi": v[1]} for k, v in _PRESSURE_IDS.items() if k in ids]
    return {"claimed_identity": claimed,
            "asking_for": asking,
            "money_direction": "out_of_your_account" if money_out else "none_detected",
            "pressure": pressure}


@app.post("/api/check")
def check(body: CheckIn):
    verdict, score, signals, category = run_signal_engine(
        body.payload, body.type, STORE.indicators_map(), allow_network=not MOCK_MODE,
        expected_intent=body.expected_intent,
    )

    # Claude narrates FROM the detected signals (zero verdict weight);
    # any failure or MOCK_MODE -> canned templates with mocked: true.
    exp_hi = exp_en = None
    mocked = True
    if not MOCK_MODE:
        out = llm.narrate(body.payload, body.type, verdict, score, signals, category)
        if out:
            exp_hi, exp_en = out["explanation_hi"], out["explanation_en"]
            category = category or out.get("category")
            if out.get("pattern_note_en") or out.get("pattern_note_hi"):
                signals.append({
                    "id": "llm_pattern_note", "source": "llm_pattern", "weight": 0,
                    "title_en": "Pattern read", "title_hi": "पैटर्न की पहचान",
                    "detail_en": out.get("pattern_note_en", ""),
                    "detail_hi": out.get("pattern_note_hi", ""),
                })
            mocked = False
    if exp_hi is None:
        exp_hi, exp_en = canned_explanation(verdict, category)

    # Insufficient information (H12+ review): a bare unknown number/VPA or a
    # few stray words carries no verdict-worthy evidence — say so and ask ONE
    # follow-up instead of implying safety with a green card.
    # A parsed upi:// URI is NOT context-less — we read the actual payee/amount,
    # so its verdict stands even though the string has no spaces (Parva, H13).
    needs_context = None
    _t = body.payload.strip()
    if score == 0 and not _t.lower().startswith("upi://") and (
        re.fullmatch(r"\+?[\d\s\-]{8,15}", _t)
        or re.fullmatch(r"[a-z0-9.\-_]{2,}@[a-z]{2,}", _t, re.I)
        or len(_t.split()) < 4
    ):
        needs_context = {
            "reason": "bare_identifier" if "@" in _t or _t[:1].isdigit() or _t[:1] == "+" else "too_short",
            "question_hi": "यह किस बारे में है? जो message/call आया था, वह पूरा paste करें — तब सही जाँच होगी।",
            "question_en": "What is this about? Paste the full message or describe the call — then the check means something.",
        }

    doc = {
        "_id": _id("chk"),
        "input": {"type": body.type, "payload": body.payload, "lang": body.lang},
        "verdict": verdict, "score": score, "signals": signals,
        "explanation_hi": exp_hi, "explanation_en": exp_en,
        "scam_category": category,
        "analysis": _analysis(body.payload, signals),
        "expected_intent": body.expected_intent,
        "needs_context": needs_context,
        "tts_audio_b64": None,
        "mocked": mocked,
        "created_at": _now(),
    }
    # Bulbul speaks the Hindi explanation; cached on the stored check so a
    # replay never re-synthesises. Failure -> null audio, never an error.
    if body.speak and not MOCK_MODE:
        doc["tts_audio_b64"] = sarvam.text_to_speech(exp_hi, lang="hi-IN")
    STORE.insert("checks", doc)
    # Every ward check reaches the guardian (Saud/PO, H11): risky ones need a
    # decision ("pending"); clean ones appear as info rows ("noted").
    if body.ward_link_id and STORE.get("guardian_links", body.ward_link_id):
        gr = {
            "_id": _id("gr"), "link_id": body.ward_link_id, "check_id": doc["_id"],
            "summary_hi": exp_hi[:140], "verdict": verdict, "score": score,
            "status": "pending" if verdict != "no_known_risk" else "noted",
            "guardian_note": "", "created_at": _now(),
        }
        STORE.insert("guardian_requests", gr)
        doc["guardian_request_id"] = gr["_id"]
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


class LinkIn(BaseModel):
    ward_name: str
    guardian_name: str
    guardian_phone: str = ""  # H12+: "call my trusted person" uses THIS stored
    #                           number — never one supplied by a suspicious message


@app.post("/api/guardian/links")
def create_link(body: LinkIn):
    doc = {
        "_id": _id("gl"), "ward_name": body.ward_name, "guardian_name": body.guardian_name,
        "guardian_phone": body.guardian_phone.strip(),
        "pair_code": f"DHAAL-{uuid.uuid4().hex[:4].upper()}", "created_at": _now(),
    }
    return STORE.insert("guardian_links", doc)


@app.get("/api/guardian/links/resolve")
def resolve_link(pair_code: str):
    code = pair_code.strip().upper()
    for candidate in (code, f"DHAAL-{code}") if not code.startswith("DHAAL-") else (code,):
        hits = STORE.list("guardian_links", {"pair_code": candidate})
        if hits:
            return hits[0]
    return {"error": "code not found"}


@app.get("/api/guardian/requests")
def list_requests(link_id: str):
    out = STORE.list("guardian_requests", {"link_id": link_id})
    return {"requests": sorted(out, key=lambda r: r["created_at"], reverse=True)}


@app.get("/api/guardian/requests/{rid}")
def get_request(rid: str):
    return STORE.get("guardian_requests", rid) or {"error": "request not found"}


class DecisionIn(BaseModel):
    decision: str  # allowed | blocked
    note: str = ""
    link_id: str = ""  # H12: decision must come from the paired guardian


@app.post("/api/guardian/requests/{rid}/decision")
def decide(rid: str, body: DecisionIn):
    gr = STORE.get("guardian_requests", rid)
    if not gr:
        return {"error": "request not found"}
    # H12 review: knowing a request id must not be enough to decide for a
    # family — the caller must hold the pairing's link_id (capability check).
    if body.link_id != gr.get("link_id"):
        return JSONResponse({"error": "link_id mismatch"}, status_code=403)
    status = "allowed" if body.decision == "allowed" else "blocked"
    r = STORE.update("guardian_requests", rid, {"status": status, "guardian_note": body.note})
    return r or {"error": "request not found"}


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


@app.post("/api/reports")
def create_report(body: ReportIn):
    doc = {
        "_id": _id("rep"), "payload": body.payload, "category": body.category,
        "note": body.note, "city": body.city, "status": "pending",
        "indicator_type": _indicator_type(body.payload), "created_at": _now(),
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
    value = r["payload"].strip()
    if r["indicator_type"] == "domain":
        value = first_host(value) or value
    was_verified = r.get("status") == "verified"
    r = STORE.update("reports", rid, {
        "status": status, "decided_at": _now(), "decided_via": "mod-key",
    }) or r
    if status == "verified":
        STORE.upsert_indicator(value, r["indicator_type"], r["category"])
    elif was_verified:
        # H12 review: a mistaken verification must be reversible — rejecting a
        # verified report withdraws its blocklist contribution.
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
    what: str = "paid"
    amount: int = 0
    channel: str = "upi"
    bank: str = ""
    lang: str = "hi-IN"


@app.post("/api/recovery/kit")
def recovery_kit(body: RecoveryIn):
    # Harsh H10-H12: Claude personalises; template = mocked fallback.
    ctx = {
        "date": datetime.now().strftime("%d-%m-%Y"),
        "amount": body.amount or "____",
        "bank": body.bank or "आपका बैंक",
        "channel": body.channel.upper(),
    }
    t = FX.RECOVERY_KIT_TEMPLATE
    return {
        "call_script_1930": t["call_script_1930"].format(**ctx),
        "complaint_draft": t["complaint_draft"].format(**ctx),
        "bank_letter": t["bank_letter"].format(**ctx),
        "checklist": list(t["checklist"]),
        "mocked": True,
    }


# ---------------------------------------------------------------- WhatsApp bot
# Twilio WhatsApp sandbox webhook (H13, Saud's ask): scams arrive on WhatsApp,
# so the shield answers there — forward any message to the Dhaal number and the
# verdict comes back in the same chat. Reply is TwiML; latency budget: our p50
# 5.4s check sits well inside Twilio's ~15s webhook window.
_WA_VERDICT = {
    "danger": ("🛑", "खतरा", "DANGER"),
    "suspicious": ("⚠️", "सावधान", "SUSPICIOUS"),
    "no_known_risk": ("🟢", "कोई ज्ञात खतरा नहीं", "NO KNOWN RISK"),
}


@app.post("/api/whatsapp")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    body_text = str(form.get("Body") or "").strip()
    if not body_text or body_text.lower().startswith("join "):
        msg = ("🛡️ ढाल Dhaal में आपका स्वागत है!\n"
               "कोई भी suspicious message, link, UPI ID या number यहाँ forward करें — "
               "तुरंत बताएँगे कि ठगी है या नहीं।\n"
               "Forward any suspicious message — Dhaal checks it instantly.")
    else:
        doc = check(CheckIn(type="text", payload=body_text, lang="hi-IN"))
        icon, v_hi, v_en = _WA_VERDICT[doc["verdict"]]
        lines = [f"{icon} *{v_hi} · {v_en}*", "", doc["explanation_hi"]]
        top = [s for s in doc["signals"] if s["source"] != "llm_pattern"][:3]
        if top:
            lines += ["", "*संकेत · Signals:*"]
            lines += [f"• {s['title_hi']} (+{s['weight']})" for s in top]
        if doc.get("needs_context"):
            lines += ["", "❓ " + doc["needs_context"]["question_hi"]]
        if doc["verdict"] == "danger":
            lines += ["", "🚑 ठगे गए हों तो पहले घंटे में 1930 पर call करें · dhaal-delta.vercel.app/recover"]
        lines += ["", "— ढाल Dhaal · dhaal-delta.vercel.app"]
        msg = "\n".join(lines)
    twiml = ('<?xml version="1.0" encoding="UTF-8"?><Response><Message>'
             + _xml_escape(msg) + "</Message></Response>")
    return Response(content=twiml, media_type="application/xml")

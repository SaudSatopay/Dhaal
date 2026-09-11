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

from fastapi import FastAPI, Request
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


@app.post("/api/check")
def check(body: CheckIn):
    verdict, score, signals, category = run_signal_engine(
        body.payload, body.type, STORE.indicators_map(), allow_network=not MOCK_MODE
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

    doc = {
        "_id": _id("chk"),
        "input": {"type": body.type, "payload": body.payload, "lang": body.lang},
        "verdict": verdict, "score": score, "signals": signals,
        "explanation_hi": exp_hi, "explanation_en": exp_en,
        "scam_category": category,
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


@app.post("/api/guardian/links")
def create_link(body: LinkIn):
    doc = {
        "_id": _id("gl"), "ward_name": body.ward_name, "guardian_name": body.guardian_name,
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


@app.post("/api/guardian/requests/{rid}/decision")
def decide(rid: str, body: DecisionIn):
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
    return (not key) or request.headers.get("x-mod-key", "") == key


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
    if r.get("status") == "verified":
        return r  # idempotent: re-verifying must not re-increment the blocklist
    status = "verified" if body.action == "verify" else "rejected"
    r = STORE.update("reports", rid, {"status": status}) or r
    if status == "verified":
        # extract the indicator value: phone/upi/domain inside payload, else script text
        value = r["payload"].strip()
        if r["indicator_type"] == "domain":
            value = first_host(value) or value
        STORE.upsert_indicator(value, r["indicator_type"], r["category"])
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

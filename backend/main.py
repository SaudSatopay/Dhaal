"""Dhaal (ढाल) — backend stub API. Serves every contract in docs/CONTRACTS.md from minute 1.

Engine lane (Harsh) replaces the marked sections with the real signal engine, Claude,
Sarvam and Atlas — the shapes here are the contract, do not drift from CONTRACTS.md.
Stub keeps a deterministic mini-engine so the golden path demos end-to-end immediately.
"""
import os
import re
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import fixtures as FX
from engine import run_signal_engine
from engine.urls import first_host

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

# ---------------------------------------------------------------- in-memory store
# Harsh H6-H8: swap to Mongo Atlas when MONGODB_URI is set; keep this fallback.
DB = {
    "checks": {},
    "reports": {},
    "indicators": {i["value"]: dict(i) for i in FX.SEED_INDICATORS},
    "guardian_links": {},
    "guardian_requests": {},
}


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
    return {"ok": True, "mock_mode": MOCK_MODE, "store": "memory"}


class CheckIn(BaseModel):
    type: str = "text"
    payload: str
    lang: str = "hi-IN"
    speak: bool = False
    ward_link_id: str | None = None


@app.post("/api/check")
def check(body: CheckIn):
    verdict, score, signals, category = run_signal_engine(
        body.payload, body.type, DB["indicators"], allow_network=not MOCK_MODE
    )
    # Harsh H4-H6: Claude writes explanation FROM detected signals; canned = mocked.
    exp_hi, exp_en = canned_explanation(verdict, category)
    doc = {
        "_id": _id("chk"),
        "input": {"type": body.type, "payload": body.payload, "lang": body.lang},
        "verdict": verdict, "score": score, "signals": signals,
        "explanation_hi": exp_hi, "explanation_en": exp_en,
        "scam_category": category,
        "tts_audio_b64": None,  # Harsh H8-H10: Sarvam TTS when speak=true
        "mocked": True,
        "created_at": _now(),
    }
    DB["checks"][doc["_id"]] = doc
    if body.ward_link_id and verdict != "no_known_risk" and body.ward_link_id in DB["guardian_links"]:
        gr = {
            "_id": _id("gr"), "link_id": body.ward_link_id, "check_id": doc["_id"],
            "summary_hi": exp_hi[:140], "status": "pending", "guardian_note": "",
            "created_at": _now(),
        }
        DB["guardian_requests"][gr["_id"]] = gr
        doc["guardian_request_id"] = gr["_id"]
    return doc


@app.post("/api/transcribe")
async def transcribe(request: Request):
    # JSON typed fallback OR multipart audio. Harsh H8-H10: Sarvam ASR for audio.
    ctype = request.headers.get("content-type", "")
    if ctype.startswith("application/json"):
        data = await request.json()
        typed = (data or {}).get("typed_text", "")
        return {"transcript": typed, "lang": (data or {}).get("lang_hint", "hi-IN"), "mocked": False}
    form = await request.form()
    _audio = form.get("audio")  # stub ignores bytes, returns fixture transcript
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
    DB["guardian_links"][doc["_id"]] = doc
    return doc


@app.get("/api/guardian/requests")
def list_requests(link_id: str):
    out = [r for r in DB["guardian_requests"].values() if r["link_id"] == link_id]
    return {"requests": sorted(out, key=lambda r: r["created_at"], reverse=True)}


@app.get("/api/guardian/requests/{rid}")
def get_request(rid: str):
    r = DB["guardian_requests"].get(rid)
    return r or {"error": "request not found"}


class DecisionIn(BaseModel):
    decision: str  # allowed | blocked
    note: str = ""


@app.post("/api/guardian/requests/{rid}/decision")
def decide(rid: str, body: DecisionIn):
    r = DB["guardian_requests"].get(rid)
    if not r:
        return {"error": "request not found"}
    r["status"] = "allowed" if body.decision == "allowed" else "blocked"
    r["guardian_note"] = body.note
    return r


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
    DB["reports"][doc["_id"]] = doc
    return doc


@app.get("/api/reports")
def list_reports(status: str = "pending"):
    out = [r for r in DB["reports"].values() if r["status"] == status]
    return {"reports": sorted(out, key=lambda r: r["created_at"], reverse=True)}


class VerifyIn(BaseModel):
    action: str  # verify | reject


@app.post("/api/reports/{rid}/verify")
def verify_report(rid: str, body: VerifyIn):
    r = DB["reports"].get(rid)
    if not r:
        return {"error": "report not found"}
    r["status"] = "verified" if body.action == "verify" else "rejected"
    if r["status"] == "verified":
        # extract the indicator value: phone/upi/domain inside payload, else script text
        value = r["payload"].strip()
        if r["indicator_type"] == "domain":
            value = first_host(value) or value
        ind = DB["indicators"].get(value)
        if ind:
            ind["report_count"] += 1
        else:
            DB["indicators"][value] = {
                "_id": _id("ind"), "type": r["indicator_type"], "value": value,
                "report_count": 1, "first_seen": _now(), "category": r["category"],
            }
    return r


@app.get("/api/intel/trends")
def trends():
    live_verified = [r for r in DB["reports"].values() if r["status"] == "verified"]
    data = {k: (v.copy() if isinstance(v, dict) else list(v)) if isinstance(v, (dict, list)) else v
            for k, v in FX.SEED_TRENDS.items()}
    data["total_reports"] = FX.SEED_TRENDS["total_reports"] + len(live_verified)
    data["top_indicators"] = sorted(
        DB["indicators"].values(), key=lambda i: i["report_count"], reverse=True
    )[:10]
    data["live_reports"] = len(live_verified)
    return data


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

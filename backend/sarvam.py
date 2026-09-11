"""Sarvam AI client — Saarika ASR (voice in) + Bulbul TTS (warning out).

Contract with callers: return None on ANY failure — no exceptions escape, the
endpoint falls back (fixture transcript / null audio) and the demo never 500s.
Every attempt prints a `[latency] sarvam_*` line (PPT numbers). Retry policy:
one retry on transport errors / 5xx / 429; a 4xx instead retries once with the
previous-generation API shape (payload naming drifted between Sarvam versions).
"""

import base64
import os
import time

import httpx

BASE = "https://api.sarvam.ai"
_client = httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0))


def _key() -> str:
    return os.getenv("SARVAM_API_KEY", "").strip()


def available() -> bool:
    return bool(_key())


def _post(path: str, **kw) -> httpx.Response | None:
    tag = "sarvam_" + path.strip("/").replace("-", "_")
    resp = None
    for attempt in (1, 2):
        t0 = time.perf_counter()
        try:
            resp = _client.post(f"{BASE}{path}",
                                headers={"api-subscription-key": _key()}, **kw)
            ms = (time.perf_counter() - t0) * 1000
            print(f"[latency] {tag}_ms={ms:.0f} status={resp.status_code} try={attempt}")
            if resp.status_code < 400:
                return resp
            if 400 <= resp.status_code < 500 and resp.status_code != 429:
                return resp  # config/shape problem — retrying same payload won't help
        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            print(f"[latency] {tag}_ms={ms:.0f} error={type(e).__name__} try={attempt}")
            resp = None
    return resp


def speech_to_text(blob: bytes, filename: str = "audio.webm",
                   content_type: str = "audio/webm") -> dict | None:
    """-> {'transcript', 'language_code'} or None. language 'unknown' lets
    Saarika auto-detect (Hindi/English code-mixed speech is the demo norm)."""
    if not available() or not blob:
        return None
    r = _post("/speech-to-text",
              data={"model": "saarika:v2.5", "language_code": "unknown"},
              files={"file": (filename, blob, content_type)})
    if r is None or r.status_code >= 400:
        r = _post("/speech-to-text",  # previous-gen shape
                  data={"model": "saarika:v2", "language_code": "hi-IN"},
                  files={"file": (filename, blob, content_type)})
    if r is None or r.status_code >= 400:
        return None
    try:
        j = r.json()
        transcript = (j.get("transcript") or "").strip()
        if not transcript:
            return None
        return {"transcript": transcript,
                "language_code": j.get("language_code") or "hi-IN"}
    except Exception:
        return None


def text_to_speech(text: str, lang: str = "hi-IN",
                   sample_rate: int | None = None) -> str | None:
    """-> base64 WAV string (contract field tts_audio_b64) or None.
    sample_rate: telephony callers (Exotel IVR) pass 8000 — PSTN playback is
    8 kHz mono; web callers omit it (Sarvam default, richer audio)."""
    if not available() or not text.strip():
        return None
    snippet = text.strip()[:450]  # TTS input cap; explanations are 2-3 sentences
    extra = {"speech_sample_rate": sample_rate} if sample_rate else {}
    # bulbul:v2 deprecated 2026 (Sarvam 400s with "use bulbul:v3"); v3 speaker
    # roster replaced the old names — ritu/priya are current-valid.
    r = _post("/text-to-speech",
              json={"text": snippet, "target_language_code": lang,
                    "speaker": "ritu", "model": "bulbul:v3", **extra})
    if r is None or r.status_code >= 400:
        r = _post("/text-to-speech",  # alt field naming, same model gen
                  json={"inputs": [snippet], "target_language_code": lang,
                        "speaker": "priya", "model": "bulbul:v3", **extra})
    if r is None or r.status_code >= 400:
        return None
    try:
        audios = r.json().get("audios") or []
        if not audios:
            return None
        base64.b64decode(audios[0], validate=True)  # sanity: decodable audio
        return audios[0]
    except Exception:
        return None

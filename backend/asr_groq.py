"""Groq Whisper ASR — the second server-side engine behind Saarika.

Same contract as sarvam.speech_to_text: return a dict or None, never raise.
whisper-large-v3-turbo: fast, Hindi/Hinglish capable, OpenAI-compatible API.
"""

import os
import time

import httpx

_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
_client = httpx.Client(timeout=httpx.Timeout(25.0, connect=5.0))


def _key() -> str:
    # keys travel through consoles and shells that smuggle BOMs/CRLF into the
    # stored value; a non-latin-1 char in the Authorization header makes httpx
    # raise UnicodeEncodeError before any network happens. Keep printable
    # ASCII only — API keys are ASCII by construction.
    raw = os.getenv("GROQ_API_KEY", "")
    return "".join(ch for ch in raw if 32 < ord(ch) < 127)


def available() -> bool:
    return bool(_key())


def speech_to_text(blob: bytes, filename: str = "audio.webm",
                   content_type: str = "audio/webm",
                   lang_hint: str = "hi-IN") -> dict | None:
    """-> {'transcript', 'language_code'} or None. Language is hinted only for
    Hindi (Whisper then writes Devanagari for Hinglish speech); anything else
    auto-detects."""
    if not available() or not blob:
        return None
    content_type = (content_type or "audio/webm").split(";")[0].strip() or "audio/webm"
    # ALWAYS pin Hindi: Whisper's auto-detect routinely labels spoken Hindi
    # as Urdu and emits Urdu script (H17 field report). Hindi-pinned Whisper
    # still transcribes English speech fine for this bilingual audience.
    data = {"model": "whisper-large-v3-turbo", "response_format": "json",
            "temperature": "0", "language": "hi"}
    for attempt in (1, 2):
        t0 = time.perf_counter()
        try:
            r = _client.post(
                _URL,
                headers={"Authorization": f"Bearer {_key()}"},
                data=data,
                files={"file": (filename, blob, content_type)},
            )
            ms = (time.perf_counter() - t0) * 1000
            print(f"[latency] groq_whisper_ms={ms:.0f} status={r.status_code} try={attempt}")
            if r.status_code < 400:
                text = (r.json().get("text") or "").strip()
                if not text:
                    return None
                return {"transcript": text,
                        "language_code": "hi-IN" if data.get("language") == "hi" else (lang_hint or "hi-IN")}
            if 400 <= r.status_code < 500 and r.status_code != 429:
                return None  # config/shape problem — same payload won't heal
        except Exception as e:
            ms = (time.perf_counter() - t0) * 1000
            print(f"[latency] groq_whisper_ms={ms:.0f} error={type(e).__name__} try={attempt}")
    return None

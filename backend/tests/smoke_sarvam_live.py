"""LIVE Sarvam smoke — run once SARVAM_API_KEY is in the repo-root .env:
    cd backend && .venv/Scripts/python.exe tests/smoke_sarvam_live.py
Closes the loop with zero external files: TTS speaks a Hindi line -> the WAV
is fed straight back into ASR -> transcript must come back non-empty. Costs
three tiny API calls. Exit code 0 = the voice beat is live end-to-end.
"""

import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
load_dotenv()

import sarvam  # noqa: E402

if not sarvam.available():
    sys.exit("SKIP: SARVAM_API_KEY not set (.env at repo root) — nothing tested")

LINE = "यह एक डिजिटल अरेस्ट ठगी है, फोन काटिए और 1930 पर सूचना दीजिए।"

b64 = sarvam.text_to_speech(LINE, lang="hi-IN")
if not b64:
    sys.exit("FAIL: TTS returned no audio — check [latency] lines above for status")
wav = base64.b64decode(b64)
out_path = Path(__file__).with_name("smoke_tts_output.wav")
out_path.write_bytes(wav)
print(f"ok  TTS: {len(wav)} bytes -> {out_path.name} (play it to hear Bulbul)")

asr = sarvam.speech_to_text(wav, filename="smoke.wav", content_type="audio/wav")
if not asr:
    sys.exit("FAIL: ASR returned nothing on Bulbul's own WAV — check status lines")
print(f"ok  ASR ({asr['language_code']}): {asr['transcript']}")

print("\nSARVAM VOICE LOOP LIVE — TTS and ASR both answering")

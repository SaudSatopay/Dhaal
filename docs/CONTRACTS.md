# Contracts — single source of truth

API shapes, data models, env names. **Owning lane pushes the contract change BEFORE the code.** Frontend builds against these (the stub API already serves them). Re-read after every rebase.

## Env vars

| Name | Used by | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | backend | script classification + explanation + recovery drafts |
| `SARVAM_API_KEY` | backend | ASR (voice in) + TTS (warning out) |
| `MONGODB_URI` | backend | Atlas; **unset ⇒ in-memory store** (works with zero setup) |
| `NEXT_PUBLIC_API_URL` | frontend | FastAPI base (local `http://localhost:8000`) |
| `MOCK_MODE` | backend | `true` ⇒ canned fixtures; backend ALSO auto-falls-back per call on external failure; canned responses carry `"mocked": true` |
| `CORS_ORIGINS` | backend | comma-separated, default `*` |

## Core enums

- `verdict`: `"danger" | "suspicious" | "no_known_risk"` (UI: खतरा / सावधान / कोई ज्ञात खतरा नहीं — never render the word "safe")
- `input type`: `"text" | "url" | "upi" | "qr_text" | "voice_transcript"` (QR images are decoded **client-side with jsQR**; backend receives the decoded string as `qr_text`)
- `signal.source`: `"deterministic" | "community" | "llm_pattern"` — verdict scoring uses deterministic + community only; `llm_pattern` signals display but carry zero verdict weight

## Data models (Mongo collections; in-memory fallback mirrors shapes)

### `checks` — owner: Engine
```json
{
  "_id": "chk_xxx",
  "input": {"type": "text", "payload": "आपका SBI खाता…", "lang": "hi-IN"},
  "verdict": "danger",
  "score": 87,
  "signals": [
    {"id": "lookalike_domain", "source": "deterministic", "weight": 40,
     "title_en": "Lookalike domain", "title_hi": "नकली मिलती-जुलती वेबसाइट",
     "detail_en": "sbi-kyc-update.xyz imitates sbi.co.in", "detail_hi": "…"},
    {"id": "community_blocklist", "source": "community", "weight": 50,
     "title_en": "Reported by 43 users", "title_hi": "43 लोगों ने रिपोर्ट किया", "detail_en": "…", "detail_hi": "…"}
  ],
  "explanation_hi": "यह message बैंक से नहीं है…",
  "explanation_en": "…",
  "scam_category": "kyc_expiry | lottery | digital_arrest | fake_collect | electricity | olx_army | customer_care | other | null",
  "tts_audio_b64": null,
  "mocked": false,
  "created_at": "ISO8601"
}
```

### `reports` — owner: Engine
```json
{"_id": "rep_xxx", "payload": "9876543210 / upi id / url / message text", "category": "kyc_expiry",
 "note": "free text", "city": "Jaipur", "status": "pending | verified | rejected",
 "indicator_type": "phone | upi | domain | script", "created_at": "ISO8601"}
```

### `indicators` (the shared blocklist) — owner: Engine
```json
{"_id": "ind_xxx", "type": "phone | upi | domain | script", "value": "sbi-kyc-update.xyz",
 "report_count": 43, "first_seen": "ISO8601", "category": "kyc_expiry"}
```

### `guardian_links` / `guardian_requests` — owner: Engine
```json
{"_id": "gl_xxx", "ward_name": "Sunita Devi", "guardian_name": "Rahul", "pair_code": "DHAAL-4821", "created_at": "…"}
{"_id": "gr_xxx", "link_id": "gl_xxx", "check_id": "chk_xxx", "summary_hi": "₹15,000 collect request…",
 "status": "pending | allowed | blocked", "guardian_note": "", "created_at": "…"}
```

## API endpoints (owner: Engine · all **stubbed** at kickoff → flip to `live` here as implemented)

### `GET /api/health` — live → `{"ok": true, "mock_mode": false, "store": "memory|atlas"}`

### `POST /api/check` — **live** (deterministic engine + Claude narration; Claude down/no key ⇒ template explanations with `mocked: true`. Persistence: Atlas when `MONGODB_URI` set, per-call memory failover)
```json
{"type": "text|url|upi|qr_text|voice_transcript", "payload": "...", "lang": "hi-IN", "speak": false, "ward_link_id": null}
```
→ full `check` object. If `speak:true`, include `tts_audio_b64`. If `ward_link_id` set and verdict ≠ `no_known_risk`, backend auto-creates a `guardian_request` and includes `"guardian_request_id"` in the response.

### `POST /api/transcribe` — stubbed
multipart `audio` + `lang_hint`, or JSON `{"typed_text": "..."}` → `{"transcript": "...", "lang": "hi-IN", "mocked": false}` (then frontend calls `/api/check` with `voice_transcript`)

### Guardian — live (store-backed)
- `POST /api/guardian/links` `{"ward_name","guardian_name"}` → link with `pair_code`
- `GET /api/guardian/links/resolve?pair_code=DHAAL-XXXX` → link object, or `{"error":"code not found"}`. Matching is case-insensitive, whitespace-trimmed, and accepts the bare code without the `DHAAL-` prefix ("ward types the code" flow).
- `GET /api/guardian/requests?link_id=` → pending+recent for guardian screen (poll 3s)
- `GET /api/guardian/requests/{id}` → ward polls decision
- `POST /api/guardian/requests/{id}/decision` `{"decision":"allowed|blocked","note":""}` → updated request

### Intel — stubbed
- `POST /api/reports` `{"payload","category","note","city"}` → report (status pending)
- `GET /api/reports?status=pending` → moderation queue
- `POST /api/reports/{id}/verify` `{"action":"verify|reject"}` → verified ⇒ indicator upserted into blocklist **immediately live for every /api/check**
- `GET /api/intel/trends` → `{"total_reports": n, "by_category": [...], "by_day": [...], "top_indicators": [...], "cities": [...]}`

### `POST /api/recovery/kit` — stubbed
```json
{"what": "paid | shared_otp | clicked_link", "amount": 15000, "channel": "upi", "bank": "SBI", "lang": "hi-IN"}
```
→ `{"call_script_1930": "...", "complaint_draft": "...", "bank_letter": "...", "checklist": ["…"], "mocked": false}`

Errors, all endpoints: `{"error": "human-readable message"}`.

## Demo fixtures (Glue owns; Engine keeps stubs serving them)

1. **KYC scam SMS** (lookalike `sbi-kyc-update.xyz`) → danger
2. **Collect-request QR** (upi://…collect, ₹15,000) → danger, collect-vs-pay explained; plus **legit pay QR** contrast
3. **Genuine SBI SMS** → no_known_risk (false-positive control beat)
4. **Digital-arrest call script** (Hindi, for voice beat) → danger
5. **Community flywheel number** `+91-98XXX…` — pre-seeded 43 reports so the second-device check hits blocklist instantly
6. **Seeded intel**: ~200 verified reports across Jaipur/Jodhpur/Udaipur, 7 categories, last 7 days (trends board)

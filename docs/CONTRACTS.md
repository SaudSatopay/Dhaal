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
  "scam_category": "kyc_expiry | lottery | digital_arrest | fake_collect | electricity | olx_army | customer_care | job_scam | loan_fee | other | null",
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
{"_id": "gl_xxx", "ward_name": "Sunita Devi", "guardian_name": "Rahul", "guardian_phone": "+91…",
 "pair_code": "DHAAL-K7M2P4XQ", "pair_code_expires_at": "ISO8601", "pair_code_claimed": false,
 "guardian_token_sha256": "…", "ward_token_sha256": null, "revoked": false, "created_at": "…"}
{"_id": "gr_xxx", "link_id": "gl_xxx", "check_id": "chk_xxx", "summary_hi": "₹15,000 collect request…",
 "verdict": "danger|suspicious|no_known_risk|null", "score": 87, "assessment": "assessed|needs_context|unsupported_input",
 "status": "pending | allowed | blocked | noted", "guardian_note": "", "created_at": "…"}
```
Tokens are stored ONLY as hashes; API responses never include `link_id` or any hash. Ward-facing copy says the guardian **advises** — Dhaal cannot block a payment in another app and never claims to.
**Guardian contract v2 (H11, PO decision):** EVERY ward check creates a request — risky verdicts arrive as `pending` (need Allow/Block), clean ones as `noted` (informational activity row, no decision). Guardian UI renders both groups.
```json
```

## API endpoints (owner: Engine · all **stubbed** at kickoff → flip to `live` here as implemented)

### `GET /api/health` — live → `{"ok": true, "mock_mode": false, "store": "memory|atlas"}`

### `POST /api/check` — **live** (deterministic engine + Claude narration; Claude down/no key ⇒ template explanations with `mocked: true`. Persistence: Atlas when `MONGODB_URI` set, per-call memory failover)
```json
{"type": "text|url|upi|qr_text|voice_transcript", "payload": "...", "lang": "hi-IN", "speak": false, "ward_token": null, "expected_intent": "pay|receive|verify|null"}
```
→ full `check` object. **H14 assessment outcome (first-class):** `"assessment": "assessed" | "needs_context" | "unsupported_input"`; whenever assessment ≠ `assessed`, **`verdict` is `null`** — no green card, no risk label, `explanation_*` carries the targeted question / parse-failure guidance instead, and `needs_context {reason, question_hi, question_en}` is set for `needs_context`. `"facts"` is the suspicion-free parsed block (`parse.status: valid|incomplete|unsupported|malformed|multiple`, payee/amount/action, `money_direction`, `evidence` spans, `missing`) — the SAME input yields the SAME facts regardless of `expected_intent`; expectation gates only `intent_mismatch`. Also: `explanation_source: "llm"|"rules"`, `community_data: "live"|"degraded"`, `timings {engine_ms, narration_ms, tts_ms, total_ms}`. If `speak:true`, `tts_audio_b64` = base64 WAV of `explanation_hi` (Bulbul), cached; failure ⇒ `null`, never an error. If a VALID `ward_token` is sent, every check creates a `guardian_request` (risky+assessed ⇒ `pending`, else `noted`) and the response carries `guardian_request_id` + `guardian_delivery: "sent"|"sent_not_durable"`; an invalid/legacy token ⇒ `guardian_delivery: "unlinked"` (re-pair). The legacy `ward_link_id` field is accepted but NEVER authorizes anything.

### `POST /api/transcribe` — **live** (Saarika ASR, auto-detects code-mixed hi/en)
multipart `audio` + `lang_hint`, or JSON `{"typed_text": "..."}` → `{"transcript": "...", "lang": "hi-IN", "mocked": false}` (then frontend calls `/api/check` with `voice_transcript`). Sarvam down / no key / MOCK_MODE ⇒ fixture transcript with `mocked: true` — never an error.

### Guardian — live (store-backed) · **H14 capability-token model**
A pairing identifier is NOT authentication. Two role tokens per pairing, minted once, stored ONLY as SHA-256 hashes, carried ONLY in headers (never URLs/QRs/logs/responses after minting). Pair codes: `DHAAL-` + 8 chars (31-char alphabet), **single-use, 30-min expiry**, claim endpoint rate-limited. Pre-H14 pairings never authenticate — both sides re-pair (no silent migration).
- `POST /api/guardian/links` `{"ward_name","guardian_name","guardian_phone"}` → `{link_id, pair_code, pair_code_expires_at, guardian_token, …}` — `guardian_token` appears ONLY here
- `POST /api/guardian/links/claim` `{"pair_code"}` (case-insensitive, bare code ok) → `{link_id, ward_token, ward_name, guardian_name, guardian_phone}` — the minimum the ward role needs (incl. the stored trusted number for the tel: button). 404 unknown · 409 already used · 410 expired/revoked · 429 rate-limited
- `GET /api/guardian/links/resolve` — **DEAD (410)**: the pre-H14 flow returned the deciding credential to anyone with a guessable 4-hex code
- `POST /api/guardian/links/revoke` `{"reason"}` + either role header → kills the pairing (both tokens + code); consent works both ways
- `GET /api/guardian/requests` + `X-Guardian-Token` → that pairing's requests (401 without; the old `?link_id=` param is ignored)
- `GET /api/guardian/requests/{id}` + `X-Guardian-Token` OR `X-Ward-Token` → request view **without `link_id`** (401 no token; 404 for out-of-pairing ids — existence not confirmed)
- `POST /api/guardian/requests/{id}/decision` `{"decision":"allowed|blocked","note"}` + `X-Guardian-Token` → updated request + `"durable": bool` (false while the store is degraded to memory). Ward tokens, link_ids, and request ids alone can never decide.

### Intel — live (store-backed; trends = fixture baseline + live per-category/city/day overlay)
- `POST /api/reports` `{"payload","category","note","city"}` → report (status pending)
- `GET /api/reports?status=pending` → moderation queue
- `POST /api/reports/{id}/verify` `{"action":"verify|reject"}` → verified ⇒ indicator upserted into blocklist **immediately live for every /api/check**
- `GET /api/intel/trends` → `{"total_reports": n, "by_category": [...], "by_day": [...], "top_indicators": [...], "cities": [...]}`

### `POST /api/recovery/kit` — live (deterministic branch templates; H14)
```json
{"what": "paid | shared_otp | clicked_link", "amount": 15000, "channel": "upi", "bank": "SBI", "incident_date": "10-09-2026", "lang": "hi-IN"}
```
→ `{"call_script_1930", "complaint_draft", "bank_letter", "checklist": ["…"], "what", "incident_date", "mocked": true}` — the `what` choice genuinely changes all four blocks (paid ⇒ 1930/dispute · shared_otp ⇒ freeze/PIN-rotation first · clicked_link ⇒ device+credential hygiene, 1930 only if money moved). Unknown facts stay `____`; the date is the user's, never assumed today; payments are described as fraud-INDUCED, not "unauthorized"; no recovery promises.

### WhatsApp (Meta Cloud API) — H15, the production WhatsApp lane
- `GET /api/wa/webhook` — Meta subscription handshake: echoes `hub.challenge` iff `hub.verify_token` == `WA_VERIFY_TOKEN` (403 otherwise).
- `POST /api/wa/webhook` — validates `X-Hub-Signature-256` (HMAC-SHA256, `META_APP_SECRET`; refused when set and invalid), ignores `statuses` receipts, **dedupes by Meta message id** (their retries never double-reply), then engine-checks the text and replies via Graph API (`WA_ACCESS_TOKEN` + `WA_PHONE_NUMBER_ID`). Media → honest unsupported reply. Message content identical to the Twilio path (`_wa_text`): H14 assessment semantics, score shown as rule-weight risk — never a probability. Events stored in `wa_events`.

### IVR (Exotel) — H15, the dumbphone lane
- `GET|POST /api/ivr/recording` — Exotel Passthru after the Record applet: instant ACK, stores job by `CallSid` (`ivr_jobs`), no processing (Passthru deadline + serverless).
- `GET /api/ivr/result?CallSid=` — the dynamic-greeting fetch does the work: recording download (https-only, basic auth) → Saarika ASR (fallback: rehearsed fixture transcript, recorded as `mocked_transcript`) → engine → short spoken guidance → Bulbul TTS @8 kHz → `audio/wav`. Cached per CallSid (replays free, SMS once). TTS unavailable → **503** (Exotel plays its static fallback). Result SMS best-effort via Exotel (`EXOTEL_*` env).
- `GET /api/ivr/jobs/{CallSid}` — moderator-gated (transcript = caller PII; audio excluded).
- Setup runbook + call-flow diagram: `docs/CHANNELS.md`.

### `POST /api/whatsapp` — Twilio webhook (TwiML) · H14 hardened (legacy/parked)
Same assessment semantics as the web app (question leads when unassessed — never a green line above it). `NumMedia>0` ⇒ honest "photo/QR/voice not supported here" reply. Body capped at 2000 chars. `X-Twilio-Signature` (HMAC-SHA1) VALIDATED whenever `TWILIO_AUTH_TOKEN` is set (403 on mismatch); with `VERCEL` + `WA_REQUIRE_SIGNATURE=1` unsigned webhooks are refused even without the token. `WA_PUBLIC_URL` pins the signed URL behind proxies. (Sandbox transport itself is parked on the Twilio trial tier — auth verified by test, not live Twilio.)

Errors, all endpoints: `{"error": "human-readable message"}`.

## Demo fixtures (Glue owns; Engine keeps stubs serving them)

1. **KYC scam SMS** (lookalike `sbi-kyc-update.xyz`) → danger
2. **Collect-request QR** (upi://…collect, ₹15,000) → danger, collect-vs-pay explained; plus **legit pay QR** contrast
3. **Genuine SBI SMS** → no_known_risk (false-positive control beat)
4. **Digital-arrest call script** (Hindi, for voice beat) → danger
5. **Community flywheel number** `+91-98XXX…` — pre-seeded 43 reports so the second-device check hits blocklist instantly
6. **Seeded intel**: ~200 verified reports across Jaipur/Jodhpur/Udaipur, 7 categories, last 7 days (trends board)


## H12+ additions (additive, backward-compatible)

- **`expected_intent`** on `POST /api/check` ("pay"|"receive"|"verify"|null): the user's stated goal, asked by the UI on QR/UPI checks. When "receive" meets ANY upi:// payload (pay or collect — both move money OUT on approval), the engine fires **`intent_mismatch` (+40, deterministic)** — catches keyword-free traps ("scan this QR to receive your refund" on a clean pay-QR).
- **`analysis`** on every check response — the structured "what they want" panel, read straight off the parsed FACTS (H14: never regex-mined from prose, never expectation-dependent): `{claimed_identity, asking_for: [{what, hi, amount}], money_direction: "out_of_your_account"|"none_detected"|"unknown", pressure: [{tag, hi}], expectation, missing}`. `intent_mismatch` fires only against a VALID parsed payment request (parse.status="valid"); incomplete/malformed/unsupported URIs never claim to be a PAY QR and a bare `upi://` never gets clearance.
- Verify is idempotent per decision AND reversible: reject-after-verify withdraws **exactly the identifiers that report contributed** (`indicator_values` recorded at decision time; other reports' counts survive). Full-message reports contribute their EXTRACTED identifiers (canonical host / last-10 phone / lowercased VPA — shown to the moderator as `candidate_indicators` at submission), never the whole sentence. Indicators carry `last_seen` freshness. Moderation endpoints require `X-Mod-Key` when `MOD_KEY` is set; on Vercel a missing key fails CLOSED. (H14 replaced the H12 `link_id`-based decision auth with guardian tokens — see Guardian section.)

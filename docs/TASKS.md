# Task Board — the live coordination file

Claim: `[ ]` → `[WIP-saud]` / `[WIP-parva]` / `[WIP-harsh]`, **push immediately** (push = lock). Done: `[x]`, un-WIP, push. Re-read after every `git pull --rebase`. P0 = golden path, P1 = wow, P2 = nice.

## Ownership map (who may edit what)

| Lane | Owner | Owns |
|---|---|---|
| **Product** | Parva | `frontend/**` · PPT · demo choreography |
| **Engine** | Harsh (@harshh-2505) | `backend/**` · signal engine + AI pipelines · Data/API sections of `docs/CONTRACTS.md` |
| **Glue** | Saud (@SaudSatopay) | root configs · deploys · `scripts/` · fixtures/seed data · `README.md` · rest of `docs/` |

## Board

### Product — Parva (`frontend/`)
- [x] **P0 H1–H3** `/check`: input card with 3 tabs — paste text/URL/UPI · QR image upload (**decode client-side with `jsqr`**, send `qr_text`) · mic (MediaRecorder → `/api/transcribe`) with typed fallback → POST `/api/check` → render verdict card: big verdict state (danger/suspicious/no_known_risk in Hindi+English), signal list with per-signal weight + detail, category chip. Stub API answers already.
- [x] **P0 H3–H5** Report flow on verdict card ("Report scam" → POST `/api/reports`) + `/intel` console: moderation queue (poll `?status=pending`, verify/reject buttons) + trends board (`/api/intel/trends`: category bars, 7-day line, top indicators, city chips).
- [x] **P0 H5–H7** `/guardian`: pairing screen (create link → show `pair_code`), guardian inbox (poll 3s, request cards with reason summary, Allow/Block), ward waiting/decision states. Two-browser demo works.
- [x] **P1 H7–H10** Voice polish: record UX, spoken-verdict playback (`tts_audio_b64`), Hindi-first labels with English subtitles; `/recover` flow (form → render kit: 1930 script, complaint draft, bank letter, checklist, copy buttons). *(voice-path verdicts auto-speak once TTS lands — plays `tts_audio_b64` on mount; test again when Sarvam is live)*
- [WIP-parva] **P1 H10–H12** Golden-path polish mobile-first: loading/error/empty states, contrast beat styling, demo choreography pass with Saud.
- [WIP-parva] **H12+** PPT + pitch script (own it); rehearse ×3. *(started early — deliverables land in `pitch/`; choreography pass with Saud still pending from H10–H12 item)*

### Engine — Harsh (`backend/`)
- [x] **P0 H1–H4** Deterministic **signal engine** in code (this is the product's spine): UPI URI parser (collect vs pay, amount, payee), lookalike-domain detector (levenshtein vs seeded brand/bank domain list in `backend/data/brands.py`), URL heuristics (shorteners, IP literals, punycode, suspicious TLDs, redirect unwrap via httpx), scam-script keyword patterns (KYC expiry, lottery, digital arrest, electricity, OLX/army, fake customer care), blocklist lookup. Scoring function → verdict. **LLM has zero verdict weight.**
- [x] **P0 H4–H6** Claude layer: scam-category classification + `explanation_hi/en` generated FROM detected signals only (template fallback when API down) · wire `/api/check` fully to CONTRACTS shape · Mongo persistence (in-memory fallback stays). *(Mongo done early per Saud's request: `store.py` — Atlas + per-call memory failover; needs `MONGODB_URI` in Vercel env. Claude live path needs `ANTHROPIC_API_KEY`; untested until keys land. Tests: `backend/tests/run_api_checks.py`.)*
- [x] **P0 H6–H8** Reports → verify → indicator upsert → live blocklist in `/api/check` *(done + tested in H4–H6 store work)* · `/api/intel/trends` aggregations *(per-category/per-city/per-day live overlay on the fixture baseline — totals semantics unchanged so seed.py numbers hold)*.
- [WIP-harsh] **P1 H8–H10** Sarvam: `/api/transcribe` (ASR) + TTS on `speak:true` (base64 wav) with auto-fallback.
- [ ] **P1 H10–H12** Guardian endpoints end-to-end · `/api/recovery/kit` (Claude + fixed templates fallback). *(resolve-by-code folded in — see Parva's request)*
- [WIP-harsh] **H12+** Harden: timeouts, retry-once, per-call latency log (numbers for PPT), kill flaky paths. *(starting early: latency lines + retry-once land with the Sarvam commit)*

### Glue — Saud (root, `scripts/`, deploys, fixtures)
- [x] Kickoff: PS locked · docs rewritten · scaffold + stub API serving all contracts
- [x] **P0 H1–H3** Deploy DONE: frontend **https://dhaal-delta.vercel.app** · backend **https://dhaal-api.vercel.app** (Railway trial expired → backend runs as a Vercel Python service; `backend/vercel.json`). `NEXT_PUBLIC_API_URL` set in Vercel prod env. Deployment protection disabled on both. Redeploy: `vercel --prod --yes` inside `frontend/` or `backend/`. QR card for the live URL still to make (H12–H15 packaging).
- [x] **P0 H3–H5** Fixtures + seeds DONE: `backend/data/brands.py` (brand domains, UPI PSP suffixes, shorteners, TLDs — **Harsh: import, don't recreate**) · `demo/qr_collect_15000.png` + `demo/qr_legit_pay.png` · `demo/RUNSHEET.md` (8 beats, exact paste strings, failure drill) · `scripts/seed.py` tested against live API (43× flywheel + weighted intel reports, all verified; **re-run once after Atlas lands**).
- [ ] **Hourly** Golden-path QA walk; breakages → Blockers; unblocking Parva/Harsh beats own tasks.
- [ ] **P1 H8** Judge-mode dry run on venue network; decide live-vs-mock default per external call; rehearse "judge's own inbox" beat + fixture fallback.
- [ ] **H12–H15** Backup demo video · freeze enforcement · README rewrite.
- [ ] **H15+** Submission package + QR cards · rehearsal timekeeping · submit 30 min early.

## Requests (cross-lane asks — add, push, ping in person)

- [ ] FOR harsh, FROM saud — brands.py merged at rebase (your structure won; my entries folded in; ALL 20 checks pass). Heads-up: fuzzy/prefix token matching is collision-prone with everyday payment words — I dropped "federal"/"delhivery"/"cred"/"idbi"/"discom" as tokens (see comment in brands.py). Suggest a common-word stoplist or per-token `exact_only` flag in engine/common.py when you harden (H12+), then we can re-add them.
- [x] FOR harsh, FROM saud — **bump Mongo/Atlas (H6–H8) in priority** — DONE (`backend/store.py`). Saud: set `MONGODB_URI` (+ `ANTHROPIC_API_KEY`) in the backend Vercel env and **redeploy backend** (`vercel --prod --yes`) — deployed API still runs the pre-engine stub.
- [x] FOR saud, FROM harsh — `backend/data/brands.py` is seeded (~30 official domains, brand tokens, shorteners, scam TLDs); extend it during your fixtures pass (H3–H5). After ANY edit to `backend/engine/` or `backend/data/`, run `backend/tests/run_engine_checks.py` — all golden-path beats are asserted there. *(done — extended at H3–H5, both suites run on every backend-touching change since)*
- [x] FOR saud, FROM harsh — deploy latest backend + env keys → **deploys are CURRENT** (backend w/ engine + Claude/Atlas fallback paths, frontend w/ real /check) and reseeded; all 4 beats verified live (mocked=true explanations as expected). Env keys themselves = Blocker below.

- [x] FOR saud, FROM parva — **frontend redeploy** — DONE, all your surfaces are live on dhaal-delta.vercel.app (landing verified in browser, "shield online").
- [ ] FOR harsh, FROM saud — **H9 sweep: 4 engine tuning targets before freeze** — full repro + suggested fixes in `docs/SWEEP-H9.md`. Priority: (1) legit OTP-delivery SMS false-positives as `suspicious` (judges WILL paste this), (2) job-scam pattern missing, (3) loan-fee pattern missing, (4) olx_army under-threshold at 25. Add the payloads to your regression suite when fixed.
- [ ] FOR harsh, FROM saud — **SARVAM_API_KEY is live** in root `.env` (local) and backend Vercel prod env (key validated: 200 on /translate). Your H8–H10 ASR/TTS layer is fully unblocked — ship it and it works with zero env steps.
- [WIP-harsh] FOR harsh, FROM parva — guardian pairing UX: frontend hands the ward a link/QR carrying `link_id` (works today, demo-safe, live on `/guardian`). For the product-grade "ward types the code" flow, add `GET /api/guardian/links/resolve?pair_code=DHAAL-XXXX` → link object (contract change yours to push). NOT demo-blocking — fold into your P1 H10–H12 guardian pass if there's room.

## Blockers (Saud clears these first)

- [x] ~~KEYS~~ **ALL 3 KEYS DONE** — `MONGODB_URI` (Atlas live, `store:"atlas"`), `ANTHROPIC_API_KEY` (**Claude narration live in prod**, `mocked:false`, ~5.5s warm, explanations cite detected signals), `SARVAM_API_KEY` (validated 200, staged in prod env — activates the moment Harsh's ASR/TTS code lands). Local `.env` + Vercel prod env both complete. 🔐 rotate all three after the event (they passed through chat).
- [x] ~~MONGODB_URI~~ **ATLAS IS LIVE + DURABLE** (`store:"atlas"` on prod health): M0 cluster, 0.0.0.0/0 active, sample dataset dropped (quota freed), full seed done — flywheel number carries **86 verified reports**, 245 live intel reports feeding trends. ⚠️ **Do NOT re-run `scripts/seed.py` against prod** — it is not idempotent; counts inflate on every run. Local dev (memory store) reseeding is fine.

## Done

- [x] Repo workflow scaffolding (pre-event)
- [x] PS triage across all 106 pages → locked **Fintech PS#7 → Dhaal (ढाल)**

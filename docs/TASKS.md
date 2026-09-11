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
- [WIP-parva] **P0 H1–H3** `/check`: input card with 3 tabs — paste text/URL/UPI · QR image upload (**decode client-side with `jsqr`**, send `qr_text`) · mic (MediaRecorder → `/api/transcribe`) with typed fallback → POST `/api/check` → render verdict card: big verdict state (danger/suspicious/no_known_risk in Hindi+English), signal list with per-signal weight + detail, category chip. Stub API answers already.
- [ ] **P0 H3–H5** Report flow on verdict card ("Report scam" → POST `/api/reports`) + `/intel` console: moderation queue (poll `?status=pending`, verify/reject buttons) + trends board (`/api/intel/trends`: category bars, 7-day line, top indicators, city chips).
- [ ] **P0 H5–H7** `/guardian`: pairing screen (create link → show `pair_code`), guardian inbox (poll 3s, request cards with reason summary, Allow/Block), ward waiting/decision states. Two-browser demo works.
- [ ] **P1 H7–H10** Voice polish: record UX, spoken-verdict playback (`tts_audio_b64`), Hindi-first labels with English subtitles; `/recover` flow (form → render kit: 1930 script, complaint draft, bank letter, checklist, copy buttons).
- [ ] **P1 H10–H12** Golden-path polish mobile-first: loading/error/empty states, contrast beat styling, demo choreography pass with Saud.
- [ ] **H12+** PPT + pitch script (own it); rehearse ×3.

### Engine — Harsh (`backend/`)
- [x] **P0 H1–H4** Deterministic **signal engine** in code (this is the product's spine): UPI URI parser (collect vs pay, amount, payee), lookalike-domain detector (levenshtein vs seeded brand/bank domain list in `backend/data/brands.py`), URL heuristics (shorteners, IP literals, punycode, suspicious TLDs, redirect unwrap via httpx), scam-script keyword patterns (KYC expiry, lottery, digital arrest, electricity, OLX/army, fake customer care), blocklist lookup. Scoring function → verdict. **LLM has zero verdict weight.**
- [WIP-harsh] **P0 H4–H6** Claude layer: scam-category classification + `explanation_hi/en` generated FROM detected signals only (template fallback when API down) · wire `/api/check` fully to CONTRACTS shape · Mongo persistence (in-memory fallback stays). *(Mongo bumped to now per Saud's request — serverless store resets.)*
- [ ] **P0 H6–H8** Reports → verify → indicator upsert → live blocklist in `/api/check` · `/api/intel/trends` aggregations.
- [ ] **P1 H8–H10** Sarvam: `/api/transcribe` (ASR) + TTS on `speak:true` (base64 wav) with auto-fallback.
- [ ] **P1 H10–H12** Guardian endpoints end-to-end · `/api/recovery/kit` (Claude + fixed templates fallback).
- [ ] **H12+** Harden: timeouts, retry-once, per-call latency log (numbers for PPT), kill flaky paths.

### Glue — Saud (root, `scripts/`, deploys, fixtures)
- [x] Kickoff: PS locked · docs rewritten · scaffold + stub API serving all contracts
- [x] **P0 H1–H3** Deploy DONE: frontend **https://dhaal-delta.vercel.app** · backend **https://dhaal-api.vercel.app** (Railway trial expired → backend runs as a Vercel Python service; `backend/vercel.json`). `NEXT_PUBLIC_API_URL` set in Vercel prod env. Deployment protection disabled on both. Redeploy: `vercel --prod --yes` inside `frontend/` or `backend/`. QR card for the live URL still to make (H12–H15 packaging).
- [x] **P0 H3–H5** Fixtures + seeds DONE: `backend/data/brands.py` (brand domains, UPI PSP suffixes, shorteners, TLDs — **Harsh: import, don't recreate**) · `demo/qr_collect_15000.png` + `demo/qr_legit_pay.png` · `demo/RUNSHEET.md` (8 beats, exact paste strings, failure drill) · `scripts/seed.py` tested against live API (43× flywheel + weighted intel reports, all verified; **re-run once after Atlas lands**).
- [ ] **Hourly** Golden-path QA walk; breakages → Blockers; unblocking Parva/Harsh beats own tasks.
- [ ] **P1 H8** Judge-mode dry run on venue network; decide live-vs-mock default per external call; rehearse "judge's own inbox" beat + fixture fallback.
- [ ] **H12–H15** Backup demo video · freeze enforcement · README rewrite.
- [ ] **H15+** Submission package + QR cards · rehearsal timekeeping · submit 30 min early.

## Requests (cross-lane asks — add, push, ping in person)

- [ ] FOR harsh, FROM saud — **bump Mongo/Atlas (H6–H8) in priority**: backend is serverless now, so the in-memory store resets on cold starts/extra instances — reports, guardian links and the blocklist flywheel are only durable once `MONGODB_URI` is wired. Stub fallback stays for local dev.
- [ ] FOR saud, FROM harsh — `backend/data/brands.py` is seeded (~30 official domains, brand tokens, shorteners, scam TLDs); extend it during your fixtures pass (H3–H5). After ANY edit to `backend/engine/` or `backend/data/`, run `backend/tests/run_engine_checks.py` — all golden-path beats are asserted there.

## Blockers (Saud clears these first)

- *(none yet)*

## Done

- [x] Repo workflow scaffolding (pre-event)
- [x] PS triage across all 106 pages → locked **Fintech PS#7 → Dhaal (ढाल)**

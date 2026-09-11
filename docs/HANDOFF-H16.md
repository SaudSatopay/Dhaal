# H16/H17 engineering handoff (post-hardening, pre-judging)

## H17 addendum (judge-review round — read this first)

State: commits through `d951094`, deployed to prod with owner authorization,
all suites green (110 engine / 48 API / 71 channel / 33 guardian = **262**).

**1 · Implemented and why**
- **Detection families for the three externally-reproduced misses** (OTP
  periphrasis "six digits that just arrived", inheritance advance-fee,
  held-parcel customs bond) — as vocabulary families inside existing
  relations, with Hindi/Hinglish/split-sentence paraphrases and 8 benign
  guards as permanent checks. Plus an impersonal-news gate (police-warning
  articles suppress; anything targeting "you/aap" still flags).
- **v5 blind battery cycle**: 120 fresh cases authored by a repo-blind
  session, labels frozen, single run published RAW (84/120), THEN family
  fixes (job-kit fees, reverse-refund play, scan-to-receive QR,
  crypto-doubling, policy-maturity, trial-payment card harvest, baited payee
  display names) + two real bug fixes the battery exposed (completed-register
  matching scammer claims; agent-exemption wrong in both directions), then a
  relabelled regression re-run: 105/120, recall 47/48, FP 1/48. Full framing
  incl. two label disputes: docs/EVAL.md §-1.
- **Warning triage UX**: verdict card leads with DO-THIS-NOW (do / top
  trigger with quoted evidence / verify next); signals show top-2 with a
  native details expander. Progressive disclosure, zero information removed.
- **Intel truthfulness**: 401/403 renders a moderator-lock card (typed
  ApiError; polls stop while locked; key prompt only on explicit actions) —
  an auth failure can no longer masquerade as an outage. Seeded indicators
  carry per-row DEMO tags; header carries the data-mix chip.
- **No-fabrication closed on the last path**: /api/transcribe returns an
  honest 503 on ASR failure (fixture only under explicit MOCK_MODE); client
  routes it into the speak-again/typed coaching flow.

**2 · Verification** — the four suites above (262), the frozen v5 artifact +
regression artifact, prod probes of all three judge cases (30/50/80), prod
browser passes of triage card, expander, intel lock, /learn, /recover.

**3 · Remaining failures / unverified**
- Frozen v5 blind recall is 62.5% — the honest generalization number; the
  105/120 is regression-only. Next blind battery (v6, post-event) is the only
  path to a higher claim.
- Unsupported-vs-context labeling philosophy (7 cases): engine asks a
  clarifying question where labels say "unsupported" — behaviorally safe,
  recorded in EVAL.md, not silently re-labeled.
- Label disputes v4-105, v5-075 recorded, counted against us.
- Live WhatsApp sends still gated on Meta number activation (token+policy);
  live cron firing unobserved (daily window); usability sessions prepared,
  not run (docs/USABILITY.md).

**4 · Criteria reassessment** — see the session summary of 2026-09-12; no
self-assigned scores, evidence links only.

---

# H16 engineering handoff (original)

State at handoff: commits through `8003e65` deployed to prod
(frontend `dhaal-delta.vercel.app`, backend `dhaal-api.vercel.app`), all
local suites green, prod walkthrough done. Read with docs/H16-CHECKLIST.md.

## 1 · What changed and why

- **Exotel truly retired (§2).** All `/api/ivr/*` return **410 before any
  compute/storage** (revivable only via `IVR_ENABLED=1`). The synthetic
  fixture-transcript fallback is **deleted**: a failed transcription is now a
  503 `{"status":"no_transcript"}` — the system can no longer present a
  fabricated transcript as an assessment. Why: a disabled feature must cost
  zero and lie zero.
- **Detection as reusable relations (§3).** Extortion = disclosure-threat +
  money-demand composite (60). OTP self-flow: asking *where to enter* a code
  you requested ≠ someone demanding it. Cross-sentence referents ("the code…
  send it here"). Loan-fee adjacency incl. Devanagari, gift/customs and
  investment-doubling categories, awareness/news registers suppress, reported
  completed fraud still flags. All are pattern relations, not
  exact-wording patches, each with battery cases.
- **Evidence contract (§4A).** Engine emits offset evidence: `start`/`end`
  in **UTF-16 code units** (native JS indices; Python side computes via
  utf-16-le length), stable ids, `signal` links, `factual` flag for
  identifiers (destinations are "recorded", never accusations). Negation
  stripping is length-preserving so offsets survive. Frontend X-Ray renders
  by offsets only (boundary-segment algorithm; overlaps share segments,
  worst tone wins; tap sheet lists every finding; keyboard/a11y pass).
- **Clarification loop (§4B).** `POST /api/check/{cid}/clarify` with
  per-reason option chips incl. "पता नहीं". Answers become **additive**
  `source="user_context"` signals rendered as "आपका जवाब · YOUR ANSWER" —
  stored next to the message (`user_context[]`), never inside it; free text
  is engine-scored then relabelled; a reassuring answer can never subtract
  engine evidence; one round only (409 after); `what_changed` strip states
  before → after honestly. Same loop over WhatsApp via 30-min sender-scoped
  state.
- **Payment reality check (§4C).** For a valid parsed request: what you
  expected vs what the code actually opens (pay/collect + amount + payee),
  promised-IN vs requested-OUT when prose promises money, and the
  unverified-ownership line ("reading a code moves nothing; authorizing
  does; ownership is NOT verified here"). **Late fix from the prod
  walkthrough:** prose refund-promise + executable **pay** URI scored only
  15 (bait VPA) — added `pay_uri_refund_bait` composite (45) with
  offset-linked `refund_promise` evidence and an X-Ray kind; the collect
  lane already had its twin and is explicitly excluded (no double count).
- **WhatsApp reliability (§5).** Inbound: every message across ALL
  entries/changes persisted via atomic `insert_new` on Meta's message id
  BEFORE ack (first-writer-wins dedupe; retries can't double-process).
  Outbound: per-event outbox with attempt history; failures classified
  (429/5xx/transport=transient with backoff 60s→3h max 6 · 401/403=config ·
  other 4xx=permanent); CAS lease so concurrent drains never double-send;
  stale `sending`/`analyzing` recovery (clock-skew-proof). Drains: in-request
  → piggybacked on webhook traffic → `GET|POST /api/wa/outbox/drain` (mod key
  or `Bearer $CRON_SECRET`) → vercel.json **daily** cron. **Delivery is
  AT-LEAST-ONCE and documented as such** (timeout is ambiguous; we retry; a
  rare duplicate beats a silent drop). Hobby cron floor is daily — honest
  limitation, external pinger optional (CHANNELS.md).
- **Community ledger (§6).** Contributions ledgered per (report, indicator)
  with CAS done/reversed transitions → verify/unverify are exactly-once,
  reversal only of own contributions, `/api/reports/reconcile` recounts and
  repairs drift; failure-injection tests crash mid-write and recover.
- **Narration (§7).** Single-flight via CAS `narration_state` (stale>60s
  reclaim, ≤3 attempts); narration NEVER changes verdict/score; frontend
  scopes shimmer per check; needs-context question is speakable.
- **Guardian (§8).** Pair-code claim is an atomic single-use CAS — 8-thread
  race yields exactly one 200; tokens SHA-256 at rest, sent via headers only.
- **Store primitives.** `update_if` / `insert_new` / `set_indicator_count`
  on memory (lock), Mongo (find_one_and_update) and failover stores — the
  concurrency story above is store-level, not app-level hope.

## 2 · Tests and outcomes

All local, deterministic, external services stubbed:

| Suite | Count | Covers |
|---|---|---|
| `tests/run_engine_checks.py` | **95** | golden beats, §3 relations, offset contract (emoji+Hindi slice-back, ids, overlaps, composites, factual destinations), §4C composite |
| `tests/run_api_checks.py` | **48** | API contracts, assessment outcomes, guardian v2 |
| `tests/run_channel_checks.py` | **69** | IVR 410 zero-compute + no-fabrication 503, clarify (10), ledger + injection + reconcile (8), WA outbox (batch/dedupe/backoff/timeout/permanent/recovery/6-thread lease/cron auth), narration single-flight |
| `tests/run_guardian_auth_checks.py` | **33** | token hashing, header-only, 8-thread claim race |

Run: `cd backend && python tests/run_<name>.py` (each exits non-zero on
first failure). Frontend: `npm run build` clean (tsc strict).

## 3 · Eval results and limitations

- **Frozen honest number: v4 = 87/110** (`docs/heldout_v4.json`, developer-
  authored blind, labels frozen pre-run, published RAW before any tuning).
  Full confusion matrix + language/scenario slices + paired cases inside;
  narrative in docs/EVAL.md §0.
- After family-level fixes the SAME set re-runs at **100/110** — that number
  is **regression data, not an eval claim**
  (`docs/heldout_v4_regression.json`, battery field says so). The §4C
  composite re-run changed nothing (same 10 misses, FP still 0/43,
  false-reassurance 0/16).
- Limitations, stated plainly: developer-authored labels (no external
  validation; v4-105 recorded as a label dispute, not edited); single local
  run; the 10 open misses are preserved verbatim in the artifact (subtle
  advance-fee/credential phrasings, one extortion-vs-context call);
  scores are rule weights, **not probabilities** (published commitment).
- **No usability results exist.** docs/USABILITY.md is a prepared protocol;
  zero sessions run, zero participants, nothing claimable (§10).

## 4 · Remaining bugs / known-unsupported

- Rate limiters are per-serverless-instance (labelled in code) — a burst
  across instances multiplies the cap. Acceptable for demo scale.
- WA minute-level retry cadence needs an external pinger on Hobby (daily
  cron otherwise) — documented, not hidden.
- WA test tier: only 5 pre-verified recipients; media messages get an honest
  "not supported yet" reply.
- Photo-QR decoding happens client-side only; a QR *image* sent over
  WhatsApp is not decoded server-side.
- Lint debt: ruff/eslint not fully clean (unused legacy imports etc.);
  no functional impact; sweep post-event.
- `SUSPICIOUS_VPA_WORDS`/promise-word lists are seed lists — coverage grows
  by data, not claimed complete.

## 5 · Env & migrations (owner actions)

- **Set `CRON_SECRET`** in backend Vercel env (any random string) — the
  daily outbox-drain cron authenticates with it.
- **WhatsApp needs a fresh `WA_ACCESS_TOKEN`**: current one is INVALID
  (Meta error 190) after the number's policy hold; register attempts were
  stopped. Plan B if the hold persists: recreate the app under Harsh's
  older FB account and swap `WA_PHONE_NUMBER_ID`, `WA_ACCESS_TOKEN`,
  `META_APP_SECRET` (+ re-verify webhook). Console steps: CHANNELS.md §1.
- `TWILIO_ACCOUNT_SID` / `TWILIO_API_KEY_SID` / `TWILIO_API_KEY_SECRET`
  sit unused in local `.env` (parked H13 path) — safe to remove.
- **Rotate after the event**: every secret that passed through chat
  (`META_APP_SECRET`, the dead WA token, mod key, any Twilio values).
- No DB migrations: new collections (`contribs`, `wa_events`, `wa_outbox`,
  `wa_convo`) create themselves; `/api/reports/reconcile` (mod-gated) is
  available if indicator counts ever drift.

## 6 · Pending external checks (need live services)

- Live Meta send end-to-end (webhook → verdict reply → clarify convo) once
  a valid token exists and the number clears policy hold.
- Vercel cron actually firing at 03:00 UTC (check function logs next day).
- Real-device narration/TTS listen on iPhone Safari (mic test is a morning
  item anyway).

## 7 · Deploy / verify

```bash
cd backend  && vercel --prod --yes
cd frontend && vercel --prod --yes
```

Post-deploy probes (all verified passing at handoff):

- `POST https://dhaal-api.vercel.app/api/check` with the refund+pay-URI
  payload → `danger 60`, `pay_uri_refund_bait`, `refund_promise` evidence.
- `GET /api/ivr/recording|result|jobs/...` → **410** each.
- UI: bare number → chips → tap "पैसे माँगे गए" → सावधान card + "आपका जवाब"
  signal + what-changed strip (crash fixed in `88d7981`).
- UI: fixture 03 (collect) with "पैसे आने हैं" → reality check block.
- Suites: the four `tests/run_*.py` files, then `npm run build`.

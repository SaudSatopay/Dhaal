# H16 hardening checklist (external review round 3 · judging-day sprint)

Living checklist — updated as work lands. Baseline verified at `6c32a0b`:
66 engine / 48 API / 32 guardian / 39 channel green; tsc + build clean.

**FINAL STATE: all sections done except the §10 human round (protocol prepared,
honestly not run). Suites: 95 engine / 48 API / 69 channel / 33 guardian green.
Full handoff: docs/HANDOFF-H16.md.**

- [x] §1 Baseline runs + this checklist
- [x] §2 Exotel retired for real: routes gated OFF pre-compute (410 verified on prod
      for /recording, /result, /jobs), synthetic-transcript fallback DELETED (a failed
      transcription is a 503, never a fabricated assessment), unused creds listed for
      owner in handoff
- [x] §3 Detection: sextortion/extortion composite (weight-60 disclosure-threat+money
      relation) · OTP self-flow question ≠ request · cross-sentence "the code / send it
      here" referents · loan adjacency (Devanagari included) · Devanagari collect-approve
      · news/tutorial awareness registers · reported-demand still flags · _CTX
      "verification" over-trigger removed — all reusable relations, all in the battery
- [x] §4A X-Ray precise: backend offsets (UTF-16 code units, documented in CONTRACTS +
      engine source), stable ids, multi-fragment + repeated + overlapping evidence,
      destinations server-side and marked factual-not-accusatory, frontend renders by
      offsets only (boundary-segment algorithm, no indexOf), a11y (button roles,
      aria-expanded, focus-visible) — verified on prod with emoji+Hindi payload
- [x] §4B Clarification: POST /api/check/{id}/clarify, per-reason option trees incl.
      "I don't know", structured user_context (source-labelled "आपका जवाब" signals,
      never edited into the message), what-changed strip, reassuring answer cannot
      erase direct evidence, one-round cap (409) — prod-verified after fixing the
      user_context SignalRow crash (88d7981)
- [x] §4C Reality check: promised-in vs requested-out block (prod-verified on the
      collect fixture AND the pay-URI lane), unverified-ownership line, no cross-URI
      merging, precise authorize-not-scan wording. Late add: `pay_uri_refund_bait`
      composite — prose promise-in + executable PAY request = 45 (was scoring 15,
      a live gap found in the walkthrough), with offset-linked `refund_promise`
      evidence + X-Ray kind; v4 regression re-run unchanged at 100/110
- [x] §5 WhatsApp reliable: loop ALL entries/changes/messages · atomic claim
      (store-level insert_new) · durable inbound before ack · outbox with attempt
      history/backoff/permanent-vs-transient · drain endpoint (mod key or CRON_SECRET
      bearer) + vercel daily cron + opportunistic drains (Hobby cadence documented
      honestly in CHANNELS.md) · transport timeout = ambiguous ⇒ at-least-once,
      documented · sender-scoped 30-min clarification state · stubbed tests for batch,
      duplicate, send-failure, timeout, retry, concurrency, stale-lease recovery
- [x] §6 Community consistent: per-report contribution ledger, exactly-once via CAS,
      reversal of own contributions only, crash-midway recovery via /api/reports/
      reconcile (drift repair), failure-injection tests, degraded writes visibly
      non-durable
- [x] §7 Narration: single-flight enrichment (CAS narration_state, stale reclaim,
      attempt cap), narratingFor per-check scoping, stale-response guard, context-card
      listen button (speaks the question), verdict never changes post-hoc
- [x] §8 Guardian: atomic single-use claim under 8-thread race (exactly one 200),
      tokens hashed at rest + headers only (no leak in logs), advises-not-blocks intact
- [x] §9 Eval v4: 110 blind-authored developer-labelled cases, labels frozen before
      run, local stubbed run published RAW at 87/110 BEFORE tuning (docs/heldout_v4.json,
      frozen), confusion matrix + language/scenario slices + pairs, failures preserved
      verbatim, v4-105 label dispute recorded; post-tuning re-runs live as relabelled
      regression data (100/110, docs/heldout_v4_regression.json); v3 reclassified
- [~] §10 /learn practice flow live (fictional scenarios, neutral feedback, on-device
      tallies) + docs/USABILITY.md protocol prepared. **Human comprehension round NOT
      run — no participants, no results exist, none claimed.** Running it is the
      first post-event task
- [x] §11 Full suites green + prod browser walkthrough (clarify, X-Ray offsets + tap
      sheets + factual tag, reality check both lanes, IVR 410s) + deploys verified +
      handoff written (docs/HANDOFF-H16.md)

# H16 hardening checklist (external review round 3 · judging-day sprint)

Living checklist — updated as work lands. Baseline verified at `6c32a0b`:
66 engine / 48 API / 32 guardian / 39 channel green; tsc + build clean.

- [x] §1 Baseline runs + this checklist
- [ ] §2 Exotel retired for real: routes gated OFF pre-compute (410), synthetic-transcript
      fallback DELETED (never fabricate an assessment), unused creds listed for owner
- [ ] §3 Detection: sextortion/extortion composite · OTP self-flow question ≠ request ·
      cross-sentence "the code / send it here" referents · loan adjacency · Devanagari
      collect-approve · news/tutorial awareness registers · reported-demand still flags ·
      _CTX "verification" over-trigger removed — all as reusable relations + tests
- [ ] §4A X-Ray precise: backend offsets (UTF-16 code units, documented), stable ids,
      multi-fragment + repeated + overlapping evidence, destinations server-side and
      marked factual-not-accusatory, frontend renders by offsets (no indexOf), a11y pass
- [ ] §4B Clarification: POST /api/check/{id}/clarify, per-reason option trees incl.
      "I don't know", structured user_context (source-labelled signals, never pretend
      in-message), what-changed line, reassuring answer cannot erase direct evidence,
      one-round cap
- [ ] §4C Reality check: promised-in vs requested-out block, unverified-ownership line,
      no cross-URI merging (already), precise wording
- [ ] §5 WhatsApp reliable: loop ALL entries/changes/messages · atomic claim (store-level
      conditional insert) · durable inbound before ack · outbox with attempts/backoff/
      permanent-fail · drain endpoint + vercel cron + opportunistic drains (platform
      honesty: Hobby cron cadence documented) · timeout ambiguity = at-least-once,
      documented · sender-scoped expiring clarification state · stubbed tests for batch,
      duplicate, send-failure, timeout, retry, concurrency
- [ ] §6 Community consistent: per-report contribution ledger, atomic status transition,
      crash-midway recovery via reconcile endpoint, failure-injection tests, degraded
      writes visibly non-durable
- [ ] §7 Narration: single-flight enrichment (no duplicate paid work), narratingFor
      scoping, stale-response guard (verify), context-card listen (speak the question),
      bounded per-instance limits labelled as such
- [ ] §8 Guardian: atomic single-use claim under concurrency (update_if) + threaded test;
      token-leak log scan; consent/copy re-verified
- [ ] §9 Eval v4: 110 blind-authored developer-labelled cases (subagent running),
      labels frozen before run, local stubbed run, confusion matrix + slices + pairs,
      failures preserved; v3 reclassified as regression data
- [ ] §10 /learn comprehension round (requested action + money direction, neutral
      feedback, anonymous local aggregates) + docs/USABILITY.md protocol; human
      validation marked pending
- [ ] §11 Full suites + browser walkthrough + deploy + handoff

# Engine evaluation — honest edition (v2, after external review)

Three kinds of evidence, kept separate on purpose. Development results show responsiveness to failure; the regression suite shows nothing already fixed can silently return; **only the held-out battery measures generalization** — its rules were frozen before the inputs were written, it ran exactly once against production, and its misses are published unedited.

Reproduce everything: `cd backend && python tests/run_engine_checks.py && python tests/run_api_checks.py` (all published payloads are cases).

## 1 · Development batteries (found → fixed → became regression; NOT accuracy claims)

| Battery | First run | After fixes | What it taught |
|---|---|---|---|
| H9 adversarial sweep (17 unseen) | 13/17 | fixed | OTP-delivery FP; job/loan families missing; olx threshold |
| H11 coercion, victim-voiced (7) | 3/7 | fixed | threat *descriptions* need their own family |
| H11 bare-VPA impersonation (5) | 1/5 | fixed | brand-in-VPA only ran on QR payloads |
| H12 external review (5 independent cases) | 0/5 | fixed | ambient single words convicted; "do not share" neutralized requests; `mode=01` misread as collect (NPCI: QR-initiated); refund-advance under threshold; duplicate signal stacking |

These numbers demonstrate iteration speed, not field accuracy — once fixed and folded into regression, the cases stop being independent evidence.

## 2 · Regression suite (runs on every push)

**31 engine checks + 26 API contract checks green.** Includes every demo beat, every battery payload above, moderation-gate 401/200, verification idempotency AND reversal, guardian decision `link_id` auth, and the live Sarvam round trip locally (TTS speaks → own audio back through ASR).

## 3 · Fresh held-out battery (frozen rules · single run vs PROD · unedited)

10 new cases written blind after all H12 fixes. **Result: 5/10 — all 5 benign cases clean (0 false positives), 5 scam misses.** Raw run in `docs/heldout_h12.json`.

| Case | Expected | Got | |
|---|---|---|---|
| Court warrant + "settle ₹20,000 warna jail" | flag | **danger 65** | ok |
| Fake meter-KYC + cut tonight + link | flag | **danger 70** | ok |
| Traffic-challan threat, no money ask | flag | no_known_risk 0 | **miss** |
| `netfl1x-renew.com` payment update | flag | no_known_risk 0 | **miss** |
| "Meeting moved to courthouse cafeteria" | clean | clean 0 | ok |
| Cashback needing ₹10 "pehle bhejein" | flag | no_known_risk 0 | **miss** |
| "Dad's parcel arrived, customs duty paid" | clean | clean 0 | ok |
| "बेटा police case में, छुड़ाने के लिए 30 हज़ार भेजो" | flag | no_known_risk 15 | **miss** |
| Zomato refund initiated notice | clean | clean 0 | ok |
| Prize winner, "pay delivery charge to receive" | flag | no_known_risk 0 | **miss** |

**Post-battery:** 4 of the 5 misses were mechanical gaps (polite verb form *bhejein*, receive-prize bait shape, global-brand lookalikes beyond banks, one coercion form) — fixed, verified, regression-added, deployed. The score above is NOT revised; the next battery will again be fresh. The challan case (threat without a money ask) remains an open design tension: flagging threats with no payment mechanic risks the false positives we just eliminated.

## Corrections to v1 claims (per external review)

- "17/17 after fixes" was a regression result presented too strongly — reclassified under §1.
- "QR variants 7/7, parsing robust" was wrong in the worst way: the tests encoded the same `mode=01` misunderstanding as the code. Both fixed together.
- "Legit traffic scores 0" → precisely: all **15 published benign controls verdict clean**; sub-threshold signal mentions can occur (e.g., "Maine SBI branch jaakar KYC karwa liya" carries one 25-weight token, verdict clean).

## Known limits (say these; don't hide them)

Keyword-family detection — paraphrase coverage grows with the community corpus, not the rulebook · threats without a payment ask stay under threshold by design (precision trade) · lookalike coverage = Indian banks/PSPs/govt + major global consumer brands, not the whole internet · moderation is one shared key tonight (roadmap: per-moderator accounts, auto-verify thresholds) · seeded rows are labelled "synthetic demo" in the UI.

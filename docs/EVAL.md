# Engine evaluation — honest edition (v3, at rules freeze)

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

**35 engine checks + 32 API contract checks green.** Includes every demo beat, every battery payload above, moderation-gate 401/200, verification idempotency AND reversal, guardian decision `link_id` auth, intent-mismatch both ways on the same QR, parsed-`upi://` needs-context exemption, and the live Sarvam round trip locally (TTS speaks → own audio back through ASR).

## 3 · Held-out battery v2 — 60 cases (rules FROZEN at `aa7f715` · single run vs PROD · unedited)

60 new cases authored after the freeze, from scam typology (1930/RBI/news categories) — including deliberately hard negatives. Grading was pre-declared in the runner (`backend/tests/run_heldout_v2.py`); the battery ran exactly once; raw run in `docs/heldout_v2.json`. Same-author caveat as v1: cases are written by the team, post-freeze — independent, not adversarial third-party.

| Slice | Result | Reading |
|---|---|---|
| **Overall** | **51/60** | |
| Scam recall (should flag) | **24/30** | misses below, all sub-threshold, none demo-path |
| Benign precision (must stay clean) | **21/24** | the 3 FPs are exactly the engineered hard negatives |
| Insufficient info (must ask, never clear) | **6/6** | bare numbers/VPAs/fragments all got the context ask |

All 9 misses, unedited:

| Case | Expected | Got | Gap it names |
|---|---|---|---|
| TRAI "SIM deactivated in 2 hrs, pay verification fee" | flag | clean 20 | telecom-regulator family absent |
| Victim-voiced: "police on video call, brother arrested, send 40k" (hi) | flag | clean 15 | third-person family-emergency coercion |
| WhatsApp Gold: forward to 10 groups + enter code (`.vip`) | flag | clean 20 | chain-forward family absent |
| Card points expire today → download `points-redeem.apk` | flag | clean 0 | **`.apk` sideload signal absent entirely** |
| `swiggy-redeliver.xyz` reschedule in 6 hrs | flag | clean 20 | brand-token + TLD didn't combine to lookalike |
| "Son in accident, send 20000, don't call, he is in ICU" | flag | clean 15 | family-emergency money family |
| Student describing a cyber-safety LECTURE about digital arrest | clean | **susp 35** | no reported-speech awareness |
| "Show the delivery boy the OTP from the message" (hi) | clean | **susp 30** | legit share-OTP-with-agent flows |
| "Tell the Ola driver OTP 4412" (hi) | clean | **susp 30** | same — ride/delivery OTPs are MEANT to be shared |

**Read of the misses:** the 6 scam misses are five *missing families* (telecom-regulator, family-emergency ×2, chain-forward, apk-sideload) plus one combination bug — not random noise; each is a nameable rule the community corpus would surface. The 3 false positives are the exact hard negatives we wrote to find the precision boundary: the credential family cannot yet tell "give me your OTP" from "show the rider your OTP", and pattern-matching has no reported-speech awareness. **Per freeze discipline, none of these are fixed tonight** — they are the next battery's development set, and this score stands as published.

## 3a · Held-out battery v1 — 10 cases (historical · description CORRECTED)

10 new cases written blind after all H12 fixes. **Result: 5/10.** Two prior claims about this battery were wrong and are corrected here (caught by external review): the set contained **3 benign and 7 expected-to-flag cases, not 5/5** — so 5/10 = 2 scam hits + 3 benign clean, and "all 5 benign clean, 0 false positives" overstated the benign sample. Additionally its raw file (`docs/heldout_h12.json`) recorded only short case labels, **not the exact inputs** — irreproducible as published. Both defects are fixed from v2 onward (exact payloads in every raw file) and v3 adds full per-case labels + rationale.

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

Keyword-family detection — paraphrase coverage grows with the community corpus, not the rulebook · threats without a payment ask stay under threshold by design (precision trade) · lookalike coverage = Indian banks/PSPs/govt + major global consumer brands, not the whole internet · **no reported-speech awareness** — describing a scam can score like receiving one (v2 FP) · **credential family can't yet separate "give me your OTP" from legit share-OTP-with-agent delivery/ride flows** (v2 FPs) · five scam families named-and-missing per v2 (telecom-regulator, family-emergency, chain-forward, apk-sideload, brand-subdomain combos) · moderation is one shared key tonight (roadmap: per-moderator accounts, auto-verify thresholds) · seeded rows are labelled "synthetic demo" in the UI.

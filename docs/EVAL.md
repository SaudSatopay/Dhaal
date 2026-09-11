# Engine evaluation — honest edition (v4, post-H14 hardening)

Three kinds of evidence, kept separate on purpose. Development results show responsiveness to failure; the regression suite shows nothing already fixed can silently return; **only the held-out battery measures generalization** — its rules were frozen before the inputs were written, it ran exactly once against production, and its misses are published unedited.

Reproduce everything: `cd backend && python tests/run_engine_checks.py && python tests/run_api_checks.py && python tests/run_guardian_auth_checks.py` (all published payloads are cases; suites run keyless against the in-memory store). Held-out raws carry exact inputs, labels, engine commit and dependency state; batteries re-run via `tests/run_heldout_v3.py` (verdicts are deterministic; narration text may vary).

## 1 · Development batteries (found → fixed → became regression; NOT accuracy claims)

| Battery | First run | After fixes | What it taught |
|---|---|---|---|
| H9 adversarial sweep (17 unseen) | 13/17 | fixed | OTP-delivery FP; job/loan families missing; olx threshold |
| H11 coercion, victim-voiced (7) | 3/7 | fixed | threat *descriptions* need their own family |
| H11 bare-VPA impersonation (5) | 1/5 | fixed | brand-in-VPA only ran on QR payloads |
| H12 external review (5 independent cases) | 0/5 | fixed | ambient single words convicted; "do not share" neutralized requests; `mode=01` misread as collect (NPCI: QR-initiated); refund-advance under threshold; duplicate signal stacking |
| H14 external review battery (18 clause-level cases) | mixed | fixed | negation had no sentence scope ("Do not send money" counted as a demand); credential logic fired on mentions and self-help; safety-advice suffixes laundered real asks; reported speech scored as attacks; delivery/ride OTP flows flagged; v2 miss families (telecom, family-emergency, chain-forward, apk, brand-subdomain) |

These numbers demonstrate iteration speed, not field accuracy — once fixed and folded into regression, the cases stop being independent evidence.

## 2 · Regression suite (runs on every push)

**61 engine + 48 API + 32 guardian-authorization checks green** (H14). Includes every demo beat, every battery payload above, clause-level semantics (negation scope, requester attribution, reported speech, agent-flow OTPs), facts consistency (same QR ⇒ same facts under both expectations), assessment outcomes across web/WhatsApp/guardian, moderation-gate 401/200, identifier-extraction flywheel with exact-contribution reversal, WhatsApp signature validation, recovery branching, and every published guardian bypass path (no-credential, ward-credential, cross-pairing, request-id+link_id, legacy pairing, revoked tokens, reused/expired codes).

## 3 · Held-out battery v3 — 64 cases, BLIND-AUTHORED (rules FROZEN at `95b3b5b` · single run vs PROD · unedited)

v3 fixes v2's biggest methodology weakness: the cases were written by a **separate session that never read the engine**, while the engine was rewritten (H14) without reading the cases — labels + rationale per case, sealed until the freeze. Grading pre-declared in `backend/tests/run_heldout_v3.py`; ran exactly once against prod (deployed commit `9254f9e`; engine frozen at `95b3b5b` — the two commits between are frontend-only); raw with exact inputs in `docs/heldout_v3.json`. Community blocklist live, LLM narration on (zero verdict weight).

**Total: 53/64.** Confusion matrix (expected → predicted):

| | → flag | → clean | → context | → unsupported |
|---|---|---|---|---|
| **flag (26)** | **22** | 4 | 0 | 0 |
| **clean (28)** | 3 | **25** | 0 | 0 |
| **context (8)** | 0 | 4 | **4** | 0 |
| **unsupported (2)** | 0 | 0 | 0 | **2** |

| Metric | Value | Target (engineering, not guaranteed) |
|---|---|---|
| Recall on harmful | **22/26 (84.6%)** | >90% — **missed** |
| False warnings on legitimate | **3/28 (10.7%)** | <5% — **missed** |
| Strongest-warning (danger) precision | **9/10 (90%)** | >95% — **missed** (the 1: a hard-negative news report) |
| Any-warning precision | 22/25 (88%) | — |
| Abstention on assessable inputs | 0/54 | (no over-asking) |
| Insufficient-info handling | 4/8 | the weakest slice |
| Unsupported-input handling | 2/2 | |
| Per language | hi 16/20 · en 21/23 · hinglish 16/21 | |

All 11 misses, unedited, each with the gap it names:

| Case | Expected → Got | Gap |
|---|---|---|
| "instant personal loan… GST advance charge" | flag → clean 15 | pattern needs adjacency: "instant loan" ≠ "instant **personal** loan" |
| "jo **code** abhi aapke phone par aaya wo mujhe bata dijiye" | flag → clean 15 | bare "code" was excluded from credential tokens (promo-code FP trade) — delivered-code reference + directive not modeled |
| Sextortion ("recorded you… transfer Rs 20,000") | flag → clean 15 | **sextortion family absent entirely** |
| Paytm care: "रिक्वेस्ट को अपने ऐप में स्वीकार करें" | flag → clean 25 | collect-approve mechanic only matched the English phrase "collect request", not Devanagari "रिक्वेस्ट…स्वीकार" |
| Explainer video: "aaj ke session me samjhte hain ki digital arrest scam kaise chalta hai" | clean → susp 35 | reported-speech markers miss the tutorial-voice register |
| News: "समाचार: साइबर पुलिस ने… गिरोह को गिरफ़्तार किया" | clean → **danger 60** | "समाचार/ख़बर" absent from awareness markers — worst FP of the run |
| "Kal police station gaye the passport verification ke liye… court me property case" | clean → susp 35 | two innocent weak tokens + the mere word "verification" as context co-fired a family |
| Bare threat "अंजाम भुगतना पड़ेगा, सोच लेना।" | context → **clean 0** | 5 words slip the too-short gate: threats without asks need their own context trigger — this produced false reassurance |
| Bank a/c + IFSC alone | context → clean 0 | bare-identifier shapes cover phone/VPA, not account numbers |
| "yeh upi id sahi hai na" | context → clean 0 | referent-less question ("this/it" with nothing attached) not detected |
| "Can you send it now?" | context → clean 0 | same referent-less-question gap |

**Read:** the four insufficient-info misses are the ugliest — each handed a green card to an unjudgeable input, exactly what the assessment outcome exists to prevent; the gate is length/shape-based and needs threat-without-ask and referent-less-question triggers. The three false positives are all reported-speech registers (tutorial, news headline, small talk near trigger words) — the awareness layer works (4 other discussion cases passed) but its marker list is enumerable-and-incomplete by construction. The four scam misses are two pattern-adjacency defects, one Devanagari phrasing hole, and one wholly missing family (sextortion). **Per freeze discipline nothing was fixed before publication; targets missed are reported missed.** These eleven rows are the next battery's development set.

## 3b · Held-out battery v2 — 60 cases (historical · rules frozen at `aa7f715` · published 51/60)

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

Keyword-family detection — paraphrase coverage grows with the community corpus, not the rulebook · reported-speech handling is marker-based and register-incomplete (v3: tutorial voice, news headlines) · the too-short/needs-context gate misses threats-without-asks and referent-less questions (v3's worst rows — green cards on unjudgeable input) · sextortion family absent (v3) · lookalike coverage = Indian banks/PSPs/govt + major consumer brands, not the whole internet · scores are heuristic weights, **not calibrated probabilities** · automated batteries are not user testing · moderation is one shared key tonight (roadmap: per-moderator accounts) · WhatsApp transport auth is test-verified only (Twilio sandbox parked on trial tier) · guardian notifications require the ward's page open (polling) — no background push is claimed · pre-existing frontend `set-state-in-effect` lint debt (runtime-fine) · seeded rows are labelled "synthetic demo" in the UI. *(v2-era limits now fixed and regression-locked: agent-flow OTPs, discussion-context suppression basics, family-emergency/chain-forward/apk/telecom families.)*

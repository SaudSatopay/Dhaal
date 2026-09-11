# Engine evaluation — blind batteries (H9–H12, all reproducible)

Method: every battery was written blind against the engine (inputs the patterns were not tuned on), run against the LIVE deployment, misses fixed, and the payloads folded into `backend/tests/run_engine_checks.py` so they can never regress. Judges can re-run everything: `cd backend && python tests/run_engine_checks.py`.

| Battery | Cases | First pass | After fixes | What the misses taught |
|---|---|---|---|---|
| H9 adversarial sweep (unseen scam + legit + edge) | 17 | 13/17 | **17/17** | OTP-delivery false positive; job-scam & loan-fee families missing; olx threshold |
| H11 coercion (victim-voiced descriptions) | 7 | 3/7 → | **7/7** | descriptions of a threat ("I was told to pay or be arrested") need their own family |
| H11 VPA impersonation (bare pasted VPAs) | 5 | 1/5 → | **5/5** | brand-in-VPA check only ran on QR payloads |
| H12 QR/UPI variant battery (case, mode=01, missing fields) | 7 | **7/7** | 7/7 | collect parsing robust across variants |
| False-positive controls (real bank OTP/debit/late-fee SMS, friend asks, legit VPAs/QRs) | 12 across batteries | — | **12/12 clean** | honest-language promise holds: legit traffic scores 0 |

Regression state: **26 engine checks + 23 API contract checks green** on every push; live smoke includes a Sarvam round trip (TTS speaks a warning → its own audio back through ASR).

Field testing: ~2 hours of unscripted use by the team on real phones (iPhone Safari + Android Chrome) surfaced and fixed: iOS mic container mismatch, hung-permission UI freeze, guardian pairing visibility, fixture-transcript leak on ASR fallback, duplicate signal stacking.

Known limits (say these, don't hide them): script patterns are keyword-based (paraphrase coverage grows with the community corpus) · seeded pilot data is labelled as such in-app · moderation is key-gated single-moderator tonight (auto-verify thresholds on the roadmap).

# H9 adversarial sweep — live prod, 17 unseen inputs (Glue/Saud)

Result: **13/17 correct.** Judges will paste their own messages at the demo (beat 8), so the 4 misses below are pre-freeze tuning targets for Engine. Full repro payloads included — add them to `run_engine_checks.py` when fixed.

## The 4 misses

### 1. FALSE POSITIVE (stage-embarrassing) — legit OTP delivery flags `suspicious 30`
Payload: `123456 is your OTP for SBI net banking login. Do not share it with anyone. -SBI`
Cause: `credential_request` (+30) fires on the word OTP alone.
Suggested fix: negation/context-aware rule — an OTP **delivery** ("… is your OTP", "do not share") is not a credential **request** ("share/enter/batao your OTP"). Suppress or drop to +10 when delivery-shape + negation present. This is the single most likely thing a judge pastes from their own inbox.

### 2. UNDER: job scam → `no_known_risk 15`
Payload: `Work from home! Earn Rs 5000 daily just liking YouTube videos. Register now t.ly/j0bz limited seats`
Only `url_shortener` fired. **No job-scam script pattern exists.** Add `script_job_scam`: work from home · earn daily · ₹/day · liking videos · telegram task · registration fee · limited seats (hi + en). This is one of India's top-3 scam categories right now.

### 3. UNDER: loan-fee scam → `no_known_risk 20`
Payload: `आपके आधार पर ₹50,000 का लोन approve हो गया है। Processing fee ₹550 इस UPI पर भेजें: quickloan.help@okaxis`
Only `fee_demand` fired. Add `script_loan_fee`: loan approve(d) · pre-approved · processing fee · file charge · आधार पर लोन (hi + en). Note the VPA `quickloan.help@…` also contains "help" — `SUSPICIOUS_VPA_WORDS` didn't fire on plain-text VPAs (only in upi:// parsing?) — worth extending the VPA check to VPAs found in free text.

### 4. UNDER: OLX/army advance → `no_known_risk 25`
Payload: `I am army officer posted at Siachen. I want to buy your sofa. I will send advance payment through UPI collect request, please approve when it comes.`
`script_olx_army` fired but +25 alone < 30. Either bump to 30, or add a companion signal: "approve a collect request for money you should RECEIVE" phrasing (`collect_to_receive_bait`) — that's the mechanic of the whole scam.

## Borderline (fine, optional)
- electric-hi and lottery land `suspicious` (40/30) not `danger` — caution is shown, acceptable. Weight bumps optional if time.

## What behaved beautifully
All 7 legit/edge inputs clean (0 signals) except the OTP case · en-KYC lookalike 100 · digital-arrest EN 90 (patterns work cross-language) · collect-QR 100 · junk/empty safe · `llm_pattern_note` carrying zero verdict weight as contracted.

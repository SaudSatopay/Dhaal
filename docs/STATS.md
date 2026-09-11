# Verified impact stats — for the deck + pitch script (checked H9, Sep 11 2026)

Parva: swap any deck placeholders for these. Each has a source; say numbers exactly as written — judges Google.

## The scale (why this matters)

- **23.2 billion UPI transactions in May 2026** (₹29.9 lakh crore that month) — first time past 23B. [NPCI via DD India](https://ddindia.co.in/2026/06/upi-records-23-2-billion-transactions-worth-rs-29-9-trillion-in-may-2026-npci/)
- **~757 million UPI transactions per day** (June 2026). [Entrackr](https://entrackr.com/news/upi-clocks-2272-bn-transactions-worth-rs-2892-lakh-cr-in-june-12122397)

## The wound (the problem slide)

- **₹22,495 crore lost to cyber fraud in India in 2025** — cases up 24% YoY. [ScamWatchHQ summary](https://scamwatchhq.com/india-scams-2026-digital-arrest-upi-fraud-epidemic/) *(cross-check on stage phrasing: "over ₹22,000 crore in 2025")*
- **UPI-specific fraud FY26 (till Nov): ₹805 crore across 10.64 lakh incidents** — government data in Parliament. [The420](https://the420.in/india-upi-fraud-data-fy26-parliament-digital-payments/)
- **₹52,976 crore cumulative cyber-fraud losses over six years** (I4C). [Same source](https://scamwatchhq.com/india-scams-2026-digital-arrest-upi-fraud-epidemic/)
- Core mechanic (say this line): **the victim authorises the payment themselves** — which is why bank-side controls structurally can't stop it, and the shield must live in the user's hand.

## The recovery hour (why /recover exists)

- **1930/I4C system has saved ₹3,431+ crore across 9.94 lakh complaints** — but only when victims report fast. [The420](https://the420.in/india-cyber-fraud-7000-crore-saved-1930-helpline-i4c/)
- Pitch line: *"The golden hour works — ₹3,400 crore recovered proves it. Dhaal puts that hour in everyone's pocket, in their language."*

## Suggested problem-slide narration (2 lines)

> "हर महीने 23 अरब UPI payments — और हर एक को एक इंसान 3 सेकंड में approve करता है, बिना किसी जानकारी के। 2025 में ₹22,000 करोड़ hacking से नहीं गए — मनाने से गए।"
> "Banks can't stop a payment you authorise yourself. So the shield has to live where the decision happens — in your hand."

## Measured performance (prod, H10 battery — quote these in architecture slide)

- **Verdict latency: p50 5.4s** (3.7–5.8s, n=6) — deterministic signals compute in milliseconds; the wait is live Claude narration. Say: *"the verdict itself is instant and rule-based — the seconds are the explanation being written for this exact message."*
- Spoken warning (verdict + Sarvam TTS): ~14s end-to-end — demo driver narrates over it (see runsheet).
- Typed transcribe roundtrip: 0.2s · Sarvam ASR: ~0.6s per clip · webm from browsers accepted natively.
- Reliability: every external call has deterministic fallback; engine 26-check + API 23-check suites green on every push.

## Live product stats (ours, real, from Atlas — update just before submission)

- Community blocklist: pull live from `/api/intel/trends` (`total_reports`, top indicators). Don't hardcode — the number grows.
- Engine: 20 regression + 20 API contract checks green; deterministic verdicts, LLM zero verdict weight; latency numbers land with Harsh's hardening commit.

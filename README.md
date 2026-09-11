# ढाल Dhaal — पैसे भेजने से पहले, एक जाँच।

**A scam shield for every Indian with a phone.** Paste any message, link, UPI ID, QR photo, or just *speak* — Dhaal tells you in your own language exactly why it smells like fraud, **before** you authorise the payment. Every confirmed report strengthens everyone else's shield.

**Live: https://dhaal-delta.vercel.app** · API: https://dhaal-api.vercel.app

Built in one night at **MUJ HackX 4.0** (Manipal University Jaipur, Sep 11–12, 2026) · Fintech PS#7 — *Consumer Protection Against Payment Scams*.

## The problem

India does 23 billion UPI transactions a month — and in the majority of retail fraud, **the victim authorises the payment themselves** (fake collect requests, lookalike KYC links, "digital arrest" calls). Bank-side controls structurally cannot stop a payment you approve. ₹22,000+ crore was lost to cyber fraud in 2025 alone. The shield has to live where the decision happens: in the user's hand, in their language.

## What Dhaal does

| Surface | What happens |
|---|---|
| **जाँच / Check** | Paste text · upload a QR photo (decoded on-device) · or speak. A deterministic signal engine inspects it — UPI collect-vs-pay, lookalike domains, scam-script patterns, community blocklist — and returns खतरा / सावधान / कोई ज्ञात खतरा नहीं with every signal explained, then **speaks the warning aloud in Hindi**. |
| **परिवार की ढाल / Guardian** | An elderly user's risky check pings a family member for a 10-second Allow/Block — protection without surveillance. |
| **धोखों का नक्शा / Intel** | Community reports → human verification → a shared blocklist that instantly protects every user. Live trend board: what's hitting Rajasthan this week. |
| **पहला घंटा / Recover** | Just got scammed? Generates the 1930 call script, the cybercrime.gov.in complaint draft, and the bank dispute letter — in Hindi, in the golden hour that recovers money. |

## Why you can trust the verdict

- **The verdict is code, not vibes.** Deterministic detectors + community intelligence compute the score; the LLM (Claude) only *narrates* what was found — it carries **zero verdict weight** and cannot invent or miss a signal.
- **Voice both ways** — Sarvam AI Saarika ASR understands code-mixed Hindi speech; Bulbul TTS speaks the warning back.
- **Fails safe.** Every external dependency (Claude, Sarvam, Atlas) has a deterministic fallback — the demo never 500s, warnings degrade to templates, never to silence.
- **Honest language.** Dhaal never says "safe" — only "no known risk."

## Architecture

```
Next.js PWA (Vercel)                     FastAPI (Vercel Python service)
 check · guardian · intel · recover  ──►  deterministic SIGNAL ENGINE (verdict)
 QR decoded client-side (jsQR)            ├─ community blocklist (MongoDB Atlas)
                                          ├─ Claude · claude-sonnet-5 (narration only)
                                          └─ Sarvam Saarika ASR + Bulbul TTS (voice)
```

## Run locally

```
# backend (FastAPI, :8000) — runs with ZERO keys: memory store + template fallbacks
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# frontend (Next.js, :3000)
cd frontend && npm install && cp .env.local.example .env.local && npm run dev
```

Optional `.env` at repo root: `ANTHROPIC_API_KEY` (live narration) · `SARVAM_API_KEY` (voice) · `MONGODB_URI` (durable store).

## Tests

```
cd backend && python tests/run_engine_checks.py && python tests/run_api_checks.py
```

26 engine regression checks (every golden-path beat + adversarial sweep cases) · 23 API contract checks · live voice round-trip smoke (`tests/smoke_sarvam_live.py`).

## Team

| | Role |
|---|---|
| **Saud Satopay** ([@SaudSatopay](https://github.com/SaudSatopay)) | Integration, infra & deploys, QA, demo |
| **Parva Panchal** ([@parvapanchal30](https://github.com/parvapanchal30)) | Product, design system, frontend, pitch |
| **Harsh Mishra** ([@harshh-2505](https://github.com/harshh-2505)) | Signal engine, AI pipelines, data layer |

*Demo materials: [demo/RUNSHEET.md](demo/RUNSHEET.md) · pitch deck in [pitch/](pitch/) · verified stats in [docs/STATS.md](docs/STATS.md)*

# Dhaal (ढाल) — Build Plan

> **LOCKED at kickoff.** Fintech PS #7. Golden path outranks everything. Feature freeze at H12 (~midnight).

## Problem statement (chosen)

**Track:** Fintech · **PS #7 — Consumer Protection Against Payment Scams** (PDF p.9)

> Digital payment scams have moved to the consumer. Fake payment requests, malicious QR codes, spoofed customer care numbers, collect requests disguised as refunds and pressure tactics cause more retail loss than technical compromise. **The victim usually authorises the payment themselves, which makes traditional fraud controls ineffective.** Build a consumer-facing protection layer that warns a user BEFORE they authorise a payment they will regret, and turns reported scams into shared intelligence.
> Required: pre-transaction risk check · QR and link inspection · social-engineering script detection · **plain-language warnings in the user's language with the specific reason** · community reporting → shared blocklist + intel feed · recovery guidance for the first hour. Bonus: **guardian mode** for elderly users.

**Why:** the most universal problem in the deck — every judge deleted a scam SMS this morning. Banks structurally cannot stop a payment the victim authorises; the shield must live in the user's hand. Community intel = herd immunity: every report protects everyone else. That's the "solve it for good" mechanism.

## Concept — one sentence

**Dhaal**: before you pay, one check — message, QR, link, number, or a voice recording of the call — and Dhaal tells you in your own language exactly why it smells like a scam; every confirmed report makes every other Indian's shield stronger.

## Golden path — the ONE demo flow that must never break

1. `/check`: paste the demo scam SMS (*"आपका SBI खाता 24 घंटे में बंद… KYC करें: sbi-kyc-update.xyz"*) → **खतरा DANGER** card with signal-by-signal reasons: lookalike domain vs real sbi.co.in · urgency framing · credential request · link target decoded.
2. Upload a QR screenshot → decoded client-side → **"यह ₹15,000 का COLLECT request है — approve करते ही पैसे कटेंगे, आएँगे नहीं"** (the most misunderstood UPI mechanic in India, exposed live).
3. Contrast beat: paste a genuine bank SMS → **कोई ज्ञात खतरा नहीं** — we don't cry wolf (false-positive control, judges notice).
4. Mic: speak the scam call script in Hindi → same verdict, and Dhaal **speaks the warning back in Hindi** (Sarvam ASR + TTS).
5. **Guardian mode** (two screens): grandma's high-risk check pings her son → he sees the reason, taps **Block** → her screen shows a gentle Hindi message. Family protecting family, live.
6. Tap **Report scam** → moderator approves in `/intel` console → second device pastes the *same* scammer number → **instant DANGER from community intelligence**. ← the flywheel moment, shown not told.
7. `/intel` trends board: "इस हफ्ते Rajasthan में" — top scripts, categories, counts over time (seeded + our live reports).
8. Close: **"Sir, open your own inbox — forward us any message you suspect."** Judge's own scam, checked live. (Fixture fallback rehearsed if their inbox is clean.)

## Architecture

```
Next.js (Vercel)                          FastAPI (Railway)
 /check /guardian /intel /recover   ──►    /api/check ─► deterministic SIGNAL ENGINE (code):
 QR decoded client-side (jsQR)                UPI collect-vs-pay · lookalike domains ·
                                              URL heuristics · script patterns · blocklist
                                           Claude: classifies script pattern + writes the
                                              plain-Hindi explanation FROM found signals only
                                           Sarvam: ASR (voice in) + TTS (warning out)
                                           MongoDB Atlas: reports, indicators, guardians
                                           (in-memory fallback · MOCK_MODE everywhere)
```

**The verdict is computed by deterministic scoring over detected signals — the LLM can narrate but can never change the verdict.** Say exactly this to judges: it cannot hallucinate a DANGER or miss one it detected.

## Wow layer (H8–H12, only after MVP works)

Voice loop (in+out) · guardian mode · live intel flywheel demo. Already in the golden path — the wow IS the product.

## Timeline (build ends 6:00 AM · judging 11 AM–4 PM Sep 12)

| Hours | Target |
|---|---|
| H0–H1 | ✅ PS locked · docs · contracts · tasks split |
| H1–H3 | Skeleton runs locally AND **hello-world deployed** (Vercel + Railway, QR to live URL) |
| H3–H8 | Golden-path MVP: paste-text + QR check end-to-end · verdict card with signals · report → blocklist loop |
| H8–H12 | Wow: voice in/out · guardian mode · trends board · rehearse judge moment |
| **H12** | **FEATURE FREEZE** — fixes, polish, demo prep only |
| H12–H15 | Seed data final · error-proofing · **backup demo video recorded** |
| H15–end | PPT · 3× pitch rehearsal · README rewrite · **submit 30 min early** |

Sleep shifts (~2h solo, two always on): Saud H8–H10 · Parva H10–H12 · Harsh H12–H14.

## Demo risk register

| Risk | Mitigation |
|---|---|
| Venue Wi-Fi / API outage | MOCK_MODE auto-fallback per call · fixtures deterministic · hotspot · local run |
| Judge's inbox has no scam | Rehearsed fixture set covers every beat; judge moment is a bonus, not a dependency |
| Noisy hall kills ASR | Push-to-talk close mic · typed path is the primary golden path · voice is beat 4, skippable |
| False positive on a legit message live | Contrast beat uses OUR vetted legit fixture · verdict language is "no KNOWN risk", never "safe" |
| QR decode fails on stage | Decode is client-side (jsQR) on a fixture image we control |

## Pitch skeleton (5 min, one speaker + one demo driver)

2 min problem (**verify numbers before the slide**: UPI does >15B transactions/month; reported digital-payment fraud in India runs to thousands of crores yearly; the victim authorises the payment in the majority of retail scams — cite RBI/NPCI/I4C sources) → 3 min live demo (golden path) → 1 min architecture (deterministic engine + LLM narration + community flywheel) → close: guardian mode + 1930/I4C integration + UPI-app SDK as roadmap; business = B2C free + bank/fintech API licensing. Never lie about what's mocked.

## Submission checklist (re-verify format at check-in)

- [ ] Working prototype, live URL + QR code
- [ ] Backup demo video
- [ ] PPT: Problem → Solution → Live demo → Architecture → Impact → Feasibility → Roadmap
- [ ] Repo: clean README (problem, stack, screenshots, live link, setup)
- [ ] Submitted 30 min before deadline

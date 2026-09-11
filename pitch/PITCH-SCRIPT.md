# Dhaal — 5-minute pitch script

One speaker + one demo driver. Demo driver follows `demo/RUNSHEET.md` beat numbers exactly; speaker never waits for the screen — narration continues over any lag. Rehearse ×3 minimum after feature freeze. Slide notes carry the same beats.

**Timing budget: 0:45 problem · 0:40 solution frame · 3:00 live demo · 0:35 architecture+flywheel · close inside 5:00.**

---

## 0:00 — Hook (slide 1)

> Namaste judges. सुबह-सुबह आप में से हर किसी ने एक scam SMS delete किया होगा।
> We built the thing that should have existed **before** you had to.
> This is **Dhaal — पैसे भेजने से पहले, एक जाँच.**

## 0:10 — Problem (slide 2)

> India runs on UPI — **24 and a half billion** transactions a month.
> And last year **₹22,495 crore** walked out of Indian pockets — mostly **without anyone being hacked**.
> The victim pressed PAY **themselves**. Fake collect requests, KYC-expiry SMS, digital-arrest calls.
> That's why bank fraud controls never fire — there is **no unauthorised transaction to catch**.
> The shield can't live in the bank. It has to live **in the user's hand** — before the PAY button.

## 0:45 — Solution frame (slide 3)

> Dhaal is one check: paste the message, photo the QR, or just **speak the call in Hindi**.
> Dhaal answers the only question that matters — **WHY** it's a scam.
> Not a black-box score: the exact reasons, signal by signal, in the user's own language — **spoken back** to those who can't read fast under pressure.
> And the honest green state is कोई **ज्ञात** खतरा नहीं — we never promise "safe".

*(switch to live app — slide 4 stays up only if the app can't)*

## 1:25 — LIVE DEMO (runsheet beats 1–8, driver leads)

- **B1** paste KYC SMS → खतरा — *"हर signal के साथ: नकली domain, बनावटी जल्दबाज़ी, 43 reports."*
- **B2** QR photo → *"India का सबसे misunderstood scam: यह collect request है — approve करते ही ₹15,000 **कटेंगे**, आएँगे नहीं."*
- **B3** genuine SMS → clean — *"असली message पर Dhaal चुप रहता है। We don't cry wolf."*
- **B4** speak digital-arrest line → danger + **Dhaal speaks the warning back**.
- **B5** guardian: *"दादी की जेब, पोते की एक tap"* — Block lands as a **gentle** family message, not an alarm.
- **B6** flywheel: report → verify in `/intel` → second phone, same number → **44 reports, instant DANGER**. *"एक report ने अभी-अभी हर भारतीय को बचाया — आपने live देखा."*
- **B7** trends: *"इस हफ्ते Rajasthan में 200+ verified reports — KYC scams सबसे ऊपर."* (10 seconds, keep moving)
- **B8** closer: *"Sir — अपना inbox खोलिए. Forward us anything."* (printed Beat-1 card if their inbox is clean)

## 4:25 — Architecture + honesty (slides 5–6, fast)

> Under the hood: a **deterministic signal engine** — parsers, edit-distance, heuristics, community blocklist — computes the verdict.
> **The AI narrates the verdict; it can never change it.** No hallucinated danger, no missed one.
> Every external call degrades to a deterministic fallback — this demo survives dead Wi-Fi.
> What you saw live is live; anything mocked says `mocked: true` on the wire.

## 4:45 — Close (slide 7)

> Roadmap: one-tap hand-off into **1930/I4C**, an **SDK inside UPI apps**, and the intel **API for banks** — they reimburse this fraud today; they'd rather prevent it.
> Free for every Indian, forever.
> **हर report, हर भारतीय की ढाल।** Scan the QR — check your own inbox right now. धन्यवाद।

---

## Q&A prep (30-second answers)

- **New domain / first victim — blocklist empty?** Blocklist is one of five signal families. The KYC SMS scores DANGER on lookalike-distance + TLD + urgency + credential-ask **alone**; community intel just makes it instant for everyone after one report.
- **Why won't the LLM hallucinate?** It has zero verdict weight by construction — it writes prose FROM detected signals; verdict comes from deterministic scoring. Template fallback if the API is down.
- **Privacy?** QR images are decoded on-device (jsQR) — the photo never leaves the phone. Guardian mode shares only the check summary with a chosen family member, by explicit pairing.
- **False positives?** Honest language: "no KNOWN risk", never "safe". Legit-message beat is in the demo because judges should test it.
- **Moderation at scale?** Today: human verify (you saw it — seconds). Next: report-count thresholds auto-verify, moderator handles the tail; I4C feed as trusted source.
- **Business model?** B2C free forever. Revenue: risk API + blocklist licensing to banks/fintechs/UPI apps (they bear reimbursement cost today), plus 1930/I4C integration as public infra.
- **What's mocked right now?** AI narration/TTS fall back to canned templates offline and mark `mocked: true`. Verdict engine, flywheel, guardian, recovery kit are fully live.
- **Hindi only?** Hindi-first, English subtitles everywhere. Sarvam supports 10+ Indic languages — swap `lang`, same pipeline.

## Stat sources (verified 11 Sep 2026 — say "as of" dates out loud if pressed)

- UPI **24.51B txns / ₹29.82 lakh crore, Aug 2026** — NPCI monthly data (Business Standard, 1 Sep 2026)
- **₹22,495 crore lost, 28.1 lakh complaints, 2025** — I4C figures (cited in MHA parliament replies / press)
- **32.4M calls to 1930 in 2025** — I4C
- **₹7,130+ crore saved via CFCFRMS early reporting** — PIB / MHA, Oct 2025

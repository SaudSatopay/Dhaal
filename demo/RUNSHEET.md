# Demo Run-Sheet — exact strings, exact order

Demo driver keeps this open. Every beat has a paste-ready string; never improvise inputs on stage. Rehearse until boring (3× minimum at H12+).

---

## JUDGE FIVE-BEAT (H17) — the 3-minute skeptic's tour

For a judge who says "show me it's real". Five inputs, in this order, zero setup:

**J1 · An UNFAMILIAR scam (no keyword the demo ever used):**
```
Your late uncle left you 8 lakh rupees. Remit a clearance deposit of 2500 rupees to release the inheritance.
```
Expected: **सावधान/suspicious** — advance-fee relation (windfall promised + pay-first), upfront-fee signal. Say: *"यह exact wording हमारे किसी test में नहीं थी — engine रिश्ते पकड़ता है, शब्द नहीं।"* (True: this family was an external reviewer's reproduced miss, fixed at the relation level — the DO-THIS-NOW block leads the card.)

**J2 · A legitimate message (we don't cry wolf):**
```
Dear Customer, Rs.2,500.00 credited to A/c XX4321 on 11-09-26 by UPI ref 625489. Avl Bal Rs.18,240.00 -SBI
```
Expected: **कोई ज्ञात खतरा नहीं**, zero signals — and the card STILL says "verify name & amount yourself", never "safe".

**J3 · An ambiguous input (it asks, doesn't guess):**
```
9822110733
```
Expected: **needs-context question + chips** — no verdict, no green light. Tap "पैसे माँगे गए" → the verdict updates with "आपके जवाब से जाँच बदली" and the answer appears as "आपका जवाब · YOUR ANSWER" — user context never edits the original message.

**J4 · Payment-intent interpretation (the QR that does the opposite):**
Paste (or scan `demo/qr_collect_15000.png`) and tap **"मुझे पैसे आने हैं · RECEIVE"**:
```
upi://collect?pa=refund.helpdesk@okaxis&pn=SBI%20Refunds&am=15000&cu=INR
```
Expected: danger, intent-mismatch lead + **PAYMENT REALITY CHECK** block: expected IN vs opens a ₹15,000 collect OUT, payee shown, "ownership NOT verified here" honesty line.

**J5 · One complete supporting journey (community flywheel):**
Phone A: report the number from J3 ("Scam रिपोर्ट करें") → Laptop `/intel`: moderator desk (key required — auth is not an outage), enter key, VERIFY → Phone A: re-check the same number → **danger with "reported by N users" community signal**. Say: *"एक report, सबकी ढाल — human-verified, ledger-backed, exactly-once."*

If asked "what's your accuracy": open [docs/EVAL.md](../docs/EVAL.md) — frozen blind batteries with published misses, scores are rule-weights not probabilities. Never quote a number without the caveats printed there.

**Devices:** Phone A (patient/user, mobile view) · Laptop (projector: doctor of the demo — `/intel` + guardian inbox) · Phone B or second browser window (flywheel beat 6). All on hotspot, NOT venue Wi-Fi. Backup video on Phone A gallery AND laptop desktop.

**Live URLs:** app `https://dhaal-delta.vercel.app` · API `https://dhaal-api.vercel.app`

---

## Beat 1 — the scam everyone knows (paste → खतरा)

Paste into `/check`:

```
प्रिय ग्राहक, आपका SBI खाता 24 घंटे में बंद हो जाएगा। तुरंत KYC अपडेट करें: http://sbi-kyc-update.xyz/verify
```

Say: *"हर किसी के phone में यह message आया है। Dhaal बताता है — क्यों fake है, हर signal के साथ।"* Point at lookalike-domain signal.

## Beat 2 — the QR trap (upload → collect exposed)

Upload `demo/qr_collect_15000.png` (keep it printed too). When Dhaal asks your intention, tap **"मुझे पैसे आने हैं · RECEIVE"** — the verdict now leads with the intent-mismatch line.
Expected: **"यह ₹15,000 का COLLECT request है — approve करते ही पैसे कटेंगे।"**
Say: *"India का सबसे misunderstood scam — QR से पैसे 'आने' वाले थे, कटने वाले थे।"*
**Beat 2b (the unseen-scam catch):** upload `demo/qr_legit_pay.png` — a PERFECTLY clean pay-QR, zero scam words — and again tap RECEIVE. Dhaal still warns: *"यह वही ठगी है जो keyword-detector कभी नहीं पकड़ सकता — Dhaal ने आपकी नीयत और QR की हरकत का टकराव पकड़ा।"*

## Beat 3 — we don't cry wolf (paste → clean)

```
Dear Customer, Rs.2,500.00 credited to A/c XX4321 on 11-09-26 by UPI ref 625489. Avl Bal Rs.18,240.00 -SBI
```

Expected: **कोई ज्ञात खतरा नहीं**. Say one line: *"असली message पर Dhaal चुप रहता है — वरना कोई warning नहीं सुनता।"*

## Beat 4 — voice, both directions (mic → spoken verdict)

Hold mic, read aloud (or use typed fallback if hall is loud):

```
मैं मुंबई साइबर क्राइम ब्रांच से इंस्पेक्टर बोल रहा हूँ। आपके आधार से एक parcel पकड़ा गया है। गिरफ़्तारी से बचना है तो अभी वेरिफिकेशन फीस भेजिए, किसी को बताइए मत।
```

Expected: danger + **Dhaal speaks the warning back in Hindi**. This is the digital-arrest scam — say the words "digital arrest", judges have read the headlines.

## Beat 5 — guardian mode (two screens)

> **Pre-paired backup (durable in Atlas, survives everything):** code **DHAAL-52E3** · ward link: `https://dhaal-delta.vercel.app/guardian?link=gl_adda9dd0ba&g=Rahul&w=Sunita%20Devi` — if live pairing fumbles on stage, open this link on Phone A and go straight to the risky-check beat.
> **Voice-beat timing note:** verdict + spoken warning ≈ 12–15s end-to-end. Never wait silently — narrate: *"Dhaal समझ रहा है, जवाब बोल कर देगा…"* The pause reads as gravitas if you own it.

Phone A (ward) runs a danger check with guardian linked → Laptop (guardian inbox) gets the request → tap **Block** with note → Phone A shows the gentle Hindi message.
Say: *"दादी के पैसे, पोते की एक tap — बिना दादी की privacy तोड़े।"*

## Beat 6 — the flywheel (report once, protect everyone)

Phone A: check `+919876500001` → danger, **"86 लोगों ने रिपोर्ट किया"** (count is live from Atlas — say whatever the screen says). Report it → laptop `/intel` moderation → verify → Phone B: paste the SAME number → **count +1, instant danger**.
Say: *"हर report, हर भारतीय की ढाल मज़बूत करती है। Jaipur में आज जला, Jodhpur में कल नहीं जलेगा।"*

**Beat 6b (accountability, 15 seconds):** on `/intel`, REJECT the report you just verified → second phone, same number → the warning count drops back. *"गलती हुई तो वापस भी होती है — blocklist जवाबदेह है।"*

## Beat 1b — SCAM X-RAY (new money-shot inside beat 1, +15 seconds)

After the खतरा stamp lands, scroll to **जाल का X-RAY**: the judge's own message with the traps highlighted IN the text. **Tap "वेरिफिकेशन फीस"** → the caption explains the upfront-money trick; **tap the phone number** → "पैसा यहीं जाएगा". Say: *"Dhaal sirf verdict nahi deta — message ke andar ungli rakh kar dikhata hai ki jaal kahan hai. Har highlight engine ka apna matched evidence hai — AI se paint nahi kiya."*

## Beat 7 — the war map

Laptop: `/intel` trends — *"इस हफ्ते Rajasthan में 200+ verified reports: KYC scams सबसे ऊपर।"* 10 seconds, don't linger.

## Beat 7b — WhatsApp bot (where scams actually live)

*"Scam WhatsApp par aata hai — to ढाल bhi WhatsApp par hai."* **Dhaal WhatsApp (Meta Cloud API): +1 (555) 616-2988** — the DRIVER PHONE is allow-listed; the judge dictates or shows any message, driver forwards it, verdict lands back in the same chat in ~6s with signals (needs-context inputs get the QUESTION, never a green card). Say: *"production mein yeh number public hota hai — test tier sirf 5 numbers ki limit hai."*
**If Meta's new-account review hasn't cleared by demo time** (register held): narrate over the webhook evidence instead — console shows handshake green + `messages` subscribed; terminal: unsigned webhook → 403 (signature enforced), then the TwiML curl showing message-in → verdict-out. Sentence: *"built, tested, signature-hardened — number pending Meta's review of our day-old account."*

## Beat 7c — the dumbphone lane (Exotel IVR — RETIRED, tell it straight)

*"Jinke paas smartphone nahi — unke liye humne calling lane BANAYI thi."* Play **`demo/ivr_verdict_sample.wav`** (8 kHz spoken Hindi verdict this backend generated while the lane was live: recording → Saarika ASR → engine → Bulbul TTS). Then the honest close: *"Telco KYC ek business-certificate maangta hai, isliye humne feature RETIRE kiya — routes production me band hain, test-covered hain, aur ek env flag se wapas aa sakta hai jab KYC ho."* Do NOT claim the endpoints answer today — they intentionally return 410. 15 seconds, don't linger.

## Beat 8 — the judge's own pocket (closer)

*"Sir/Ma'am — अपना inbox खोलिए। कोई भी suspicious message forward कीजिए।"* Run it live.
**Fallback** (clean inbox / nerves): hand them a printed card with Beat 1's SMS and let THEM paste it.

---

## If things break

1. API slow/cold → first request may take ~5s (serverless cold start) — warm it up 2 min before demo: open `/check`, run Beat 1 once.
2. API dead → local laptop run: `uvicorn main:app` + frontend `.env.local` → localhost (rehearse this switch once).
3. Everything dead → backup video, zero apology, keep narrating over it.

# Demo Run-Sheet — exact strings, exact order

Demo driver keeps this open. Every beat has a paste-ready string; never improvise inputs on stage. Rehearse until boring (3× minimum at H12+).

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

Upload `demo/qr_collect_15000.png` (keep it printed too — scanning a printed QR looks better on stage).
Expected: **"यह ₹15,000 का COLLECT request है — approve करते ही पैसे कटेंगे।"**
Say: *"India का सबसे misunderstood scam — QR से पैसे 'आने' वाले थे, कटने वाले थे।"*

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

Phone A (ward) runs a danger check with guardian linked → Laptop (guardian inbox) gets the request → tap **Block** with note → Phone A shows the gentle Hindi message.
Say: *"दादी के पैसे, पोते की एक tap — बिना दादी की privacy तोड़े।"*

## Beat 6 — the flywheel (report once, protect everyone)

Phone A: check `+919876500001` → danger, **"43 लोगों ने रिपोर्ट किया"**. Report it → laptop `/intel` moderation → verify → Phone B: paste the SAME number → **44 reports, instant danger**.
Say: *"हर report, हर भारतीय की ढाल मज़बूत करती है। Jaipur में आज जला, Jodhpur में कल नहीं जलेगा।"*

## Beat 7 — the war map

Laptop: `/intel` trends — *"इस हफ्ते Rajasthan में 200+ verified reports: KYC scams सबसे ऊपर।"* 10 seconds, don't linger.

## Beat 8 — the judge's own pocket (closer)

*"Sir/Ma'am — अपना inbox खोलिए। कोई भी suspicious message forward कीजिए।"* Run it live.
**Fallback** (clean inbox / nerves): hand them a printed card with Beat 1's SMS and let THEM paste it.

---

## If things break

1. API slow/cold → first request may take ~5s (serverless cold start) — warm it up 2 min before demo: open `/check`, run Beat 1 once.
2. API dead → local laptop run: `uvicorn main:app` + frontend `.env.local` → localhost (rehearse this switch once).
3. Everything dead → backup video, zero apology, keep narrating over it.

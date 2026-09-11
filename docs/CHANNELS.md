# Channels runbook — WhatsApp (Meta Cloud API) + IVR (Exotel)

Backend endpoints are LIVE and test-covered (`backend/tests/run_channel_checks.py`,
22 checks). What remains is console-side setup + env vars. Saud does the consoles;
values go into the backend Vercel env, then `vercel --prod --yes` in `backend/`.

API base: `https://dhaal-api.vercel.app`

---

## 1 · WhatsApp bot — Meta WhatsApp Cloud API

Why Meta and not Twilio: our Twilio trial blocks custom sandbox webhooks (parked
H13). Meta's Cloud API **test number** allows webhooks on the free tier and can
message up to **5 verified recipient numbers** — enough for the demo + judges.

### Console steps (≈15 min)

1. developers.facebook.com → **Create App** → type **Business** → add product
   **WhatsApp**. (Needs a Meta Business Account, auto-creatable in the flow.)
2. WhatsApp → **API Setup**. Note down:
   - **Phone number ID** (numeric, NOT the +1 number) → `WA_PHONE_NUMBER_ID`
   - **Temporary access token** (24 h) → `WA_ACCESS_TOKEN` — enough for tonight;
     for judging-day durability create a **System User token** (Business
     Settings → System Users → Add → assign the app + WhatsApp permissions →
     Generate token, never-expire) and use that instead.
3. Same page → **To** field → **Manage phone number list** → add + OTP-verify
   the demo phones (yours, Parva's, Harsh's; can add a judge's live in Q&A —
   they get a code on WhatsApp, ~30 s).
4. App Settings → Basic → **App Secret** → `META_APP_SECRET`.
5. Invent any string for `WA_VERIFY_TOKEN` (e.g. `dhaal-wa-7f31`).
6. Set all four in the backend Vercel env → redeploy backend.
7. WhatsApp → **Configuration** → Webhook → **Edit**:
   - Callback URL: `https://dhaal-api.vercel.app/api/wa/webhook`
   - Verify token: the `WA_VERIFY_TOKEN` value → **Verify and save**
     (Meta GETs our endpoint; it echoes `hub.challenge` — instant green if the
     env is deployed).
   - **Manage** → subscribe to the **`messages`** field.
8. Test: from a verified phone, message the test number any scam text → the
   verdict reply lands in the same chat.

### What the endpoint does (already deployed behavior)

- `GET /api/wa/webhook` — Meta's handshake (verify token → echo challenge).
- `POST /api/wa/webhook` — validates `X-Hub-Signature-256` (HMAC-SHA256 with
  the app secret; refused when invalid once the secret is set), ignores
  delivery/read `statuses`, **dedupes by message id** (Meta retries on
  timeouts — no double replies), marks the message read, runs the engine, and
  replies via Graph API. Media → honest "photo/QR/voice not supported yet".
  Same H14 semantics as everywhere: needs-context leads with the question,
  never a green line; the number in the reply is a **rule-weight risk score,
  not a probability** (that's a published EVAL.md commitment — judges have it).

### Notes / limits (say these, don't hide them)

- Test tier: only pre-verified recipients; 24 h temporary token unless a
  system-user token is made. Production would need a real business number +
  display-name review.
- Free-form replies ride Meta's 24-hour customer-service window — always true
  for us because we ONLY reply to an inbound message.

---

## 2 · Dumbphone IVR — Exotel

> **STATUS (H15, Saud's call: "drop Exotel"): PARKED.** Trial KYC cleared PAN
> but then demanded a business certificate (Shop & Establishment / Udyam /
> Trade License) — a real-document gate we won't file for overnight. The lane
> itself is DONE and live: endpoints deployed, 22-check-covered, and prod
> generates real spoken verdicts (ASR→engine→8 kHz Bulbul TTS). Judging story:
> "code-complete, telco number pending DoT-mandated KYC" + the reproducible
> curl demo below + the recorded verdict WAV. Un-parking later = finish KYC,
> grab an ExoPhone, build the 5-applet flow, paste 5 env vars.

Any phone (no internet, no app) calls an ExoPhone, tells the story after the
beep, and hears Dhaal's spoken Hindi verdict — plus an SMS so the guidance
stays in hand. **Prereq: Exotel account with KYC approved** — verify the trial
actually gives you an ExoPhone + App Bazaar access BEFORE the demo slot.

### Env (backend Vercel)

`EXOTEL_SID` · `EXOTEL_API_KEY` · `EXOTEL_API_TOKEN` (my.exotel.com → API
settings) · `EXOTEL_SUBDOMAIN` (`api.exotel.com` or `api.in.exotel.com` — shown
next to the credentials) · `EXOTEL_SMS_FROM` (your ExoPhone/SMS sender).

### Build the call flow (App Bazaar → Create App)

```
[Greeting]  static audio: "ढाल में स्वागत है। बीप के बाद बताइए क्या हुआ —
            कौन सा message या call आया था। बोलने के बाद 1 दबाएँ।"
    ↓
[Record]    max 60s, finish on key 1 / silence
    ↓
[Passthru]  URL: https://dhaal-api.vercel.app/api/ivr/recording
            (async OFF / wait for response — we ACK in <1s)
    ↓
[Greeting → dynamic]  URL: https://dhaal-api.vercel.app/api/ivr/result
            → returns the generated 8 kHz WAV; Exotel plays it.
            On our non-200, Exotel plays this applet's fallback audio —
            set it to: "अभी जाँच नहीं हो पाई। शक हो तो पैसे न भेजें,
            1930 पर call करें। आपको SMS भी भेजा गया है।"
    ↓
[Hangup]
```

Exotel appends `CallSid`, `CallFrom`, `RecordingUrl` etc. to both URLs — the
endpoints accept them as query or form, GET or POST.

Then: ExoPhone settings → attach this app to the number's incoming-call flow.

### What the endpoints do

- `GET|POST /api/ivr/recording` — instant ACK; stores the job keyed by
  `CallSid` (idempotent). No heavy work here (Passthru deadline + serverless).
- `GET /api/ivr/result?CallSid=…` — does the work IN the fetch Exotel plays:
  downloads the recording (basic-auth, **https only**), Saarika ASR → engine →
  short spoken guidance (`_ivr_script`: one verdict sentence + one action;
  needs-context → "call again and tell the whole story; give nobody money/OTP
  till then") → Bulbul TTS at **8 kHz** → returns `audio/wav`. Cached: replays
  serve the same audio, SMS goes once. TTS down → **503** so the flow's static
  fallback speaks; SMS still attempted. Latency budget ≈ recording 1s + ASR
  2s + engine <1s + TTS 3s — inside our existing prod function envelope.
- `GET /api/ivr/jobs/{CallSid}` — moderator-gated debug view (transcript is
  caller PII; audio blob excluded).

### Reproducible test without placing a call

```bash
curl "https://dhaal-api.vercel.app/api/ivr/recording?CallSid=DEMO1&CallFrom=09xxxxxxxxx&RecordingUrl=https://recordings.exotel.com/…/rec.mp3"
curl -o verdict.wav "https://dhaal-api.vercel.app/api/ivr/result?CallSid=DEMO1"
```

No/unreachable recording → the rehearsed digital-arrest fixture transcript is
used and `mocked_transcript: true` is recorded on the job — the lane demos
even if Exotel's recording fetch flakes, and we never claim it was real ASR.

### Honesty notes

- Dhaal cannot verify caller identity; the SMS goes to the caller ID only.
- Recordings are fetched from Exotel, transcribed via Sarvam, and the
  transcript is stored for the check (see docs/PRIVACY.md — update if
  retention changes). Exotel + Sarvam see the audio per their policies.
- SMS sender requires a working ExoPhone SMS route; DND numbers may not
  receive promotional-class SMS — transactional route recommended.

# What Dhaal stores, sends, and shares — plainly

*Honest disclosure, not legal boilerplate. No compliance claims are made beyond
what the code actually does (H14 review). Hackathon prototype.*

## What happens when you check something

- The text / decoded QR string you submit is sent to the Dhaal API over HTTPS
  and **stored** with its verdict, signals and parsed facts (MongoDB Atlas; an
  in-memory stand-in during outages — the response then says
  `community_data: "degraded"` and such writes may not survive).
- **QR photos never leave your phone** — decoding happens in your browser
  (jsQR); only the decoded text is sent.
- Voice: the audio clip is sent to the API and forwarded to **Sarvam AI** for
  transcription; the transcript is then checked like text. Audio is not stored
  by Dhaal.
- For narration, the verdict + signals + your submitted text are sent to
  **Anthropic (Claude)**. The narration cannot change the verdict. When AI is
  off or fails, a rules-composed explanation is used and the response says
  `explanation_source: "rules"`.
- Inputs are capped (4000 chars) and are analysed as data — instructions
  inside a scam message are never followed.

## What a guardian sees (and cannot see)

- Pairing is by consent both ways: the ward redeems a single-use, expiring
  code; either side can revoke at any time (Unpair) and the pairing dies
  server-side immediately.
- After pairing, EVERY check the ward runs sends the guardian: the one-line
  summary, verdict/assessment and score — **not the ward's other activity,
  not their transactions, not their phone contents.**
- The guardian's phone number, entered at pairing, is stored with the pairing
  and shown to the ward as the "call my trusted person" button. It is treated
  as private pairing data: it never appears in QR codes, URLs, or any
  response except to the paired ward.
- The guardian ADVISES ("मत भेजो") — Dhaal cannot and does not block payments
  in any payment app, and never claims to.
- Guardian/ward credentials are random capability tokens stored only as
  SHA-256 hashes; they travel only in request headers.

## Community reports

- Reporting a scam stores the reported message, category and city, pending
  human moderation. On verification, only the **identifiers** inside it
  (phone / UPI ID / domain, canonicalized) join the public blocklist — with
  report counts and freshness timestamps, reversible if a verification is
  withdrawn.
- The radar/trends board shows aggregates and verified indicators only.
  Seeded demo rows are labelled "synthetic demo" in the UI.

## Known limits (prototype honesty)

- One shared moderator key tonight (per-moderator accounts are roadmap).
- Raw submitted messages are stored unredacted for the current check and
  moderation evidence; retention/redaction policy is roadmap, not shipped.
- WhatsApp checks go through Twilio's sandbox when enabled; Twilio sees the
  message per its own policies. Media (photos/voice notes) is not processed.
- Secrets used tonight rotate after the event.

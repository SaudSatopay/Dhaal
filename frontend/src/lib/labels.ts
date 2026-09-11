// Hindi-first UI label maps + every user-facing string as a {hi,en} pair.
// The selected language leads; `pick()` (lib/lang.ts) returns [primary, secondary].
// Verdict copy rule (docs/CONTRACTS.md): never render the word "safe".

import type { ScamCategory, SignalSource, Verdict } from "./types";
import type { LangText } from "./lang";

export const VERDICT_UI: Record<
  Verdict,
  { label: LangText; hint: LangText; tone: "danger" | "caution" | "clear" }
> = {
  danger: {
    label: { hi: "खतरा", en: "DANGER" },
    hint: {
      hi: "रुक जाइए — पैसे मत भेजिए, कुछ मत भरिए",
      en: "Stop — send no money, enter nothing",
    },
    tone: "danger",
  },
  suspicious: {
    label: { hi: "सावधान", en: "SUSPICIOUS" },
    hint: {
      hi: "आगे बढ़ने से पहले खुद पक्का कीजिए",
      en: "Verify on your own before going ahead",
    },
    tone: "caution",
  },
  no_known_risk: {
    label: { hi: "कोई ज्ञात खतरा नहीं", en: "NO KNOWN RISK" },
    hint: {
      hi: "फिर भी नाम और नंबर खुद जाँच लें",
      en: "Still verify the name and number yourself",
    },
    tone: "clear",
  },
};

export const CATEGORY_UI: Record<ScamCategory, LangText> = {
  kyc_expiry: { hi: "KYC धोखा", en: "KYC scam" },
  lottery: { hi: "लॉटरी धोखा", en: "Lottery scam" },
  digital_arrest: { hi: "डिजिटल अरेस्ट", en: "Digital arrest" },
  fake_collect: { hi: "नकली collect request", en: "Fake collect request" },
  electricity: { hi: "बिजली बिल धोखा", en: "Electricity bill scam" },
  olx_army: { hi: "OLX / आर्मी धोखा", en: "OLX / army scam" },
  customer_care: { hi: "नकली कस्टमर केयर", en: "Fake customer care" },
  job_scam: { hi: "नौकरी धोखा", en: "Job scam" },
  investment_doubling: { hi: "पैसा-डबल investment", en: "money-doubling scheme" },
  gift_parcel_customs: { hi: "गिफ्ट-पार्सल customs", en: "gift-parcel customs" },
  loan_fee: { hi: "लोन फ़ीस धोखा", en: "Loan-fee scam" },
  other: { hi: "अन्य धोखा", en: "Other scam" },
};

// community wears the brand saffron — the flywheel IS the brand; engine wears ink;
// llm notes stay visibly weightless.
export const SOURCE_UI: Record<SignalSource, LangText & { cls: string }> = {
  deterministic: { hi: "इंजन जाँच", en: "RULE ENGINE", cls: "border-ink text-ink" },
  community: { hi: "समुदाय", en: "COMMUNITY", cls: "border-saffdeep text-saffdeep" },
  llm_pattern: {
    hi: "AI संकेत",
    en: "0 VERDICT WEIGHT",
    cls: "border-inksoft text-inksoft border-dashed",
  },
  // H16 §4B: signals born from the user's own clarification answer
  user_context: { hi: "आपका जवाब", en: "YOUR ANSWER", cls: "border-saffdeep text-saffdeep" },
};

/* ---------------- shared ---------------- */
export const S_COMMON = {
  check: { hi: "जाँच करो", en: "Check" },
  checking: { hi: "जाँच जारी…", en: "Checking…" },
  listen: { hi: "सुनिए", en: "Listen" },
  stopAudio: { hi: "रोकें", en: "Stop" },
} satisfies Record<string, LangText>;

/* ---------------- /check ---------------- */
export const S_CHECK = {
  title: { hi: "जाँच करो", en: "Check before you pay" },
  wardBanner: {
    hi: "{name} आपकी ढाल हैं — बड़े खतरे पर उनसे पूछा जाएगा",
    en: "{name} is your shield — big risks will ask them first",
  },
  tabPaste: { hi: "पेस्ट करें", en: "Paste" },
  tabQr: { hi: "QR फोटो", en: "QR photo" },
  tabVoice: { hi: "बोलिए", en: "Speak" },
  pasteLabel: {
    hi: "संदेश, link, UPI ID या नंबर यहाँ डालें",
    en: "Paste the message, link, UPI ID or number",
  },
  pastePh: {
    hi: "जैसे: आपका खाता बंद हो जाएगा, KYC करें…",
    en: "e.g. Your account will be closed, update KYC…",
  },
  detected: { hi: "समझा गया", en: "Detected" },
  tryExample: { hi: "आज़मा कर देखिए", en: "Try an example" },
  qrLabel: { hi: "QR का photo या screenshot चुनें", en: "Pick a photo or screenshot of the QR" },
  qrSub: {
    hi: "QR आपके phone पर ही पढ़ा जाता है — photo बाहर नहीं जाती",
    en: "Decoded on your phone — the image never leaves it",
  },
  qrDecoded: { hi: "पढ़ा गया", en: "Decoded" },
  qrError: {
    hi: "QR पढ़ नहीं पाए — साफ़, सीधा screenshot आज़माएँ",
    en: "Could not read the QR — try a clear, straight screenshot",
  },
  voiceLabel: {
    hi: "जो call आया था, वही बोल कर सुनाइए",
    en: "Repeat what the caller said — Dhaal will listen",
  },
  recListening: { hi: "सुन रहे हैं…", en: "Listening…" },
  recStopHint: { hi: "रोकने पर जाँच होगी", en: "stop to check" },
  transcribing: { hi: "समझ रहे हैं…", en: "Transcribing…" },
  tapSpeak: { hi: "दबाइए और बोलिए", en: "Tap and speak" },
  micError: {
    hi: "माइक नहीं मिला या permission नहीं मिली — नीचे टाइप करके जाँचें",
    en: "Mic unavailable or permission denied — type below instead",
  },
  heard: { hi: "यह सुना गया — गलत हो तो सुधारें", en: "Heard this — edit if wrong" },
  checkThis: { hi: "इसकी जाँच करो", en: "Check this" },
  typedLabel: { hi: "या टाइप करें (mic न चले तो)", en: "Or type it (if the mic fails)" },
  typedPh: { hi: "call में जो कहा गया…", en: "what the caller said…" },
  typedBtn: { hi: "जाँचें", en: "Check" },
  errTitle: { hi: "जाँच नहीं हो पाई", en: "Check failed" },
  errHint: { hi: "Internet जाँच कर दोबारा कोशिश करें", en: "Check your connection and retry" },
  scanTitle: { hi: "जाँच हो रही है…", en: "Dhaal is checking…" },
  micShort: {
    hi: "बहुत छोटा — दोबारा दबाकर थोड़ा लंबा बोलिए",
    en: "Too short — tap again and speak a bit longer",
  },
  micErrTitle: { hi: "माइक नहीं मिली", en: "Mic unavailable" },
  micErrPoint: { hi: "↓ नीचे टाइप करके जाँच सकते हैं", en: "↓ type below instead" },
  intentQ: { hi: "आप क्या चाहते थे?", en: "What did you expect?" },
  intentPay: { hi: "मुझे पैसे भेजने हैं", en: "I want to PAY" },
  intentReceive: { hi: "मुझे पैसे आने हैं", en: "I expect to RECEIVE" },
  intentJust: { hi: "बस जाँचना है", en: "Just checking" },
  ctxTitle: { hi: "और जानकारी चाहिए", en: "Need more context" },
  ctxAction: { hi: "पूरा message ऊपर paste करें", en: "Paste the full message above" },
  // H15 verdict-first: narration upgrades the card after the verdict lands
  narrating: { hi: "✦ AI विवरण आ रहा है — verdict final है, बदलेगा नहीं", en: "✦ AI detail incoming — the verdict is already final" },
  // H16 §4B: clarification changed the assessment — say WHY
  answerChanged: { hi: "आपके जवाब से जाँच बदली:", en: "Your answer changed the assessment:" },
  // H14: unreadable/malformed payment code — distinct from "need context"
  unsupTitle: { hi: "पढ़ा नहीं जा सका", en: "Could not read this" },
  unsupAction: { hi: "दुबारा scan करें", en: "Rescan" },
  // ward whose pairing died (revoked/legacy) — say it, don't fail silently
  wardUnlinked: {
    hi: "Guardian से जुड़ाव टूट गया है — /guardian पर जाकर नया code डालें",
    en: "Guardian pairing is no longer active — enter a fresh code on /guardian",
  },
  communityDegraded: {
    hi: "⚠ community blocklist अभी limited है (network) — यह जाँच ताज़ा community reports के बिना हुई",
    en: "⚠ community blocklist temporarily limited (network) — this check ran without the latest community reports",
  },
} satisfies Record<string, LangText>;

/* ---------------- scam x-ray (H15) ---------------- */
// Highlight labels + one-line whys for evidence kinds. Spans are the engine's
// own matches — these strings only NAME what was matched, never invent.
export const S_XRAY = {
  title: { hi: "जाल का X-RAY", en: "Scam X-ray" },
  hint: { hi: "रंगीन हिस्से पर tap करें — वजह वहीं खुलेगी", en: "Tap a highlight to see why it matters" },
  kCred: { hi: "OTP/PIN की माँग", en: "Asks for your code" },
  wCred: {
    hi: "यही असली निशाना है — OTP/PIN देते ही खाता उनके हाथ में। कोई बैंक कभी नहीं माँगता।",
    en: "This is the real target — hand over the code and the account is theirs. No bank ever asks.",
  },
  kRemote: { hi: "Screen का access", en: "Remote access" },
  wRemote: {
    hi: "AnyDesk/screen-share से वे आपका phone लाइव देखते हैं — PIN समेत।",
    en: "With screen access they watch your phone live — PIN included.",
  },
  kFee: { hi: "पहले पैसे माँगे", en: "Upfront money" },
  wFee: {
    hi: "इनाम/refund/नौकरी से पहले 'फीस' — असली में कभी नहीं होता। यही ठगी की कमाई है।",
    en: "A 'fee' before your prize/refund/job — never real. This is where the scam collects.",
  },
  kCollect: { hi: "Approve कराने की चाल", en: "Approve-to-receive trick" },
  wCollect: {
    hi: "Collect request approve करने से पैसे आते नहीं, कटते हैं।",
    en: "Approving a collect request sends money OUT, never in.",
  },
  kThreat: { hi: "धमकी", en: "Threat" },
  wThreat: {
    hi: "डर ही इनका औज़ार है — असली अधिकारी फोन पर धमकाकर पैसे नहीं माँगते।",
    en: "Fear is the tool — real authorities don't threaten you into paying on a call.",
  },
  kFamily: { hi: "अपनों की इमरजेंसी", en: "Family emergency" },
  wFamily: {
    hi: "'अस्पताल/थाने में है, अभी भेजो' — पहले उनके जाने-पहचाने नंबर पर खुद call करें।",
    en: "'In hospital/custody, send now' — first call them yourself on the number you already have.",
  },
  kApk: { hi: "App file (.apk)", en: "App file (.apk)" },
  wApk: {
    hi: "File से भेजी app, Play Store की जाँच से बची हुई — ऐसे ही screen-चोर malware आते हैं।",
    en: "An app sent as a file skips Play Store checks — screen-reading malware ships this way.",
  },
  kUrgency: { hi: "जल्दबाज़ी", en: "Urgency" },
  wUrgency: {
    hi: "सोचने का समय न देना ही चाल है — असली काम 'अभी के अभी' नहीं होते।",
    en: "Denying you thinking time IS the move — real processes are never 'right now or else'.",
  },
  kSecrecy: { hi: "अलग-थलग करना", en: "Isolation" },
  wSecrecy: {
    hi: "'किसी को मत बताना / call मत करना' — ताकि कोई आपको रोक न सके।",
    en: "'Tell no one / don't call' — so nobody can stop you in time.",
  },
  kNewNum: { hi: "नया नंबर", en: "New number" },
  wNewNum: {
    hi: "पहचान बिना जाँचे पैसे माँगना — पुराने नंबर पर call करके ही मानें।",
    en: "Money asked on an unverified identity — believe it only after calling the OLD number.",
  },
  kChain: { hi: "Forward कराना", en: "Chain forwarding" },
  wChain: {
    hi: "'10 groups में भेजो' — असली service कभी forward के बदले कुछ नहीं देती।",
    en: "'Forward to 10 groups' — no real service unlocks anything for forwards.",
  },
  kReported: { hi: "जानकारी/चर्चा", en: "Awareness context" },
  wReported: {
    hi: "यह ठगी के बारे में बताना है, ठगी नहीं — इसीलिए इसे खतरा नहीं गिना गया।",
    en: "This is ABOUT a scam, not a scam at you — which is exactly why it wasn't scored as one.",
  },
  kAgentOk: { hi: "असली delivery flow", en: "Legit agent flow" },
  wAgentOk: {
    hi: "सामने खड़े rider/delivery को OTP दिखाना platform का असली तरीका है — इसे flag नहीं किया गया।",
    en: "Showing an OTP to the rider in front of you is the platform's real flow — not flagged.",
  },
  kDelivery: { hi: "OTP आपको मिला", en: "OTP delivered to you" },
  wDelivery: {
    hi: "यह OTP आपको भेजा गया है, माँगा नहीं गया — यही फ़र्क़ सुरक्षित रखता है।",
    en: "This code was sent TO you, not asked FROM you — that difference is the safety line.",
  },
  kDest: { hi: "पता — कहाँ जाएगा", en: "Destination" },
  wDest: {
    hi: "पैसा/जवाब इसी पते पर जाएगा — यह सिर्फ़ पहचान है, अपने-आप में गलत होने का सबूत नहीं। मालिक कौन है, यह यहाँ verify नहीं होता।",
    en: "Money/replies would flow to THIS address — an identifier, not proof of wrongdoing by itself. Ownership is NOT verified here.",
  },
  kBlackmail: { hi: "ब्लैकमेल", en: "Blackmail" },
  wBlackmail: {
    hi: "बदनामी की धमकी देकर पैसे माँगना जुर्म है — जुर्म UNKA। पैसे न दें, सबूत रखें, 1930 पर रिपोर्ट करें।",
    en: "Demanding money under threat of exposure is extortion — THEIR crime. Don't pay, keep evidence, report on 1930.",
  },
  kSelfQ: { hi: "आपका अपना सवाल", en: "Your own question" },
  wSelfQ: {
    hi: "आप अपने ही app में code डालने की बात पूछ रहे हैं — यह किसी की माँग नहीं है, इसलिए flag नहीं हुआ।",
    en: "You're asking about entering a code in a flow YOU opened — nobody is demanding it, so it isn't flagged.",
  },
  factualTag: { hi: "जानकारी", en: "info" },
  kPromise: { hi: "पैसे आने का वादा", en: "Money promised IN" },
  wPromise: {
    hi: "यह रकम आपको मिलने का वादा है — पर साथ का link PAY request खोलता है। पैसे पाने के लिए कभी pay नहीं करना पड़ता।",
    en: "This amount is promised TO you — yet the attached link opens a PAY request. Receiving money never requires you to pay.",
  },
  kPattern: { hi: "जाना-पहचाना script", en: "Known scam script" },
  wPattern: {
    hi: "यही शब्द भारत भर में चल रहे ठगी-script से मिले — पूरे India का अनुभव आपकी ढाल है।",
    en: "These exact words match scam scripts running across India — the country's experience is your shield.",
  },
} satisfies Record<string, LangText>;

/* ---------------- payment reality check (H16 §4C) ---------------- */
export const S_REALITY = {
  title: { hi: "पैसे की असलियत", en: "Payment reality check" },
  expected: { hi: "आपको उम्मीद थी", en: "You expected" },
  expPay: { hi: "पैसे भेजने की", en: "to pay" },
  expReceive: { hi: "पैसे आने की", en: "to receive money" },
  expUnknown: { hi: "— (बताया नहीं)", en: "— (not stated)" },
  opens: { hi: "यह QR/link खोलता है", en: "This QR/link opens" },
  payReq: { hi: "payment request", en: "a payment request" },
  collectReq: { hi: "collect request", en: "a collect request" },
  toPayee: { hi: "payee", en: "payee" },
  promised: { hi: "वादा (message में)", en: "Promised (in message)" },
  requested: { hi: "माँग (payment code में)", en: "Requested (by the code)" },
  inYou: { hi: "→ आपको", en: "→ to YOU" },
  outYou: { hi: "आपसे बाहर →", en: "OUT of you →" },
  unverified: {
    hi: "यहाँ verify नहीं होता: payee का असली registered नाम सिर्फ़ आपके UPI app में authorize से पहले दिखेगा। Code पढ़ने से पैसा नहीं कटता — authorize करने से कटता है।",
    en: "NOT verified here: the payee's real registered name shows only in your UPI app before you authorize. Parsing a code moves no money — authorizing does.",
  },
} satisfies Record<string, LangText>;

/* ---------------- verdict card ---------------- */
export const S_VERDICT = {
  why: { hi: "ऐसा क्यों", en: "Why this verdict" },
  noSignals: { hi: "कोई खतरे का संकेत नहीं मिला", en: "No risk signals detected" },
  sealReports: { hi: "रिपोर्ट", en: "REPORTS" },
  mismatchPlate: { hi: "उम्मीद के उलट", en: "INTENT MISMATCH" },
  whatTheyWant: { hi: "यह क्या चाहता है", en: "What they want" },
  claims: { hi: "पहचान का दावा", en: "Claims to be" },
  asking: { hi: "माँग रहा है", en: "Asking for" },
  moneyDir: { hi: "पैसा जाएगा", en: "Money moves" },
  moneyOut: { hi: "आपके खाते से बाहर ↗", en: "OUT of your account ↗" },
  pressureL: { hi: "दबाव के तरीके", en: "Pressure tactics" },
  callAsk: { hi: "{name} से पूछें", en: "Call {name} first" },
} satisfies Record<string, LangText>;

/* ---------------- whatsapp strip ---------------- */
export const S_WA = {
  line: {
    hi: "WhatsApp पर भी: +1 (737) 250-8034 · भेजें 'join twilio-trial' · scam forward करो, जाँच पाओ",
    en: "Also on WhatsApp: +1 (737) 250-8034 · send 'join twilio-trial' · forward a scam, get the verdict",
  },
} satisfies Record<string, LangText>;

/* ---------------- report button ---------------- */
export const S_REPORT = {
  open: { hi: "Scam रिपोर्ट करें", en: "Report this scam" },
  doneTitle: { hi: "रिपोर्ट दर्ज हो गई", en: "Report submitted" },
  doneSub: {
    hi: "Verify होते ही यह हर भारतीय की ढाल में जुड़ जाएगी।",
    en: "Once verified, it protects everyone instantly.",
  },
  typeLabel: { hi: "किस तरह का धोखा", en: "Type of scam" },
  cityLabel: { hi: "शहर", en: "City" },
  notePh: { hi: "कुछ और बताना चाहें… (optional)", en: "Anything else… (optional)" },
  submit: { hi: "रिपोर्ट भेजें", en: "Submit report" },
  sending: { hi: "भेज रहे हैं…", en: "Sending…" },
  cancel: { hi: "रहने दें", en: "Cancel" },
} satisfies Record<string, LangText>;

/* ---------------- ward gate ---------------- */
export const S_WARD = {
  pendingTitle: {
    hi: "{name} को बताया गया है — जवाब का इंतज़ार…",
    en: "{name} has been notified — waiting for their reply…",
  },
  pendingSub: {
    hi: "बड़े खतरे पर परिवार की एक नज़र। कुछ भी भेजने से पहले रुके रहिए।",
    en: "A family eye on big risks. Hold on before sending anything.",
  },
  // H14 honesty: Dhaal cannot stop a payment in another app — the guardian
  // ADVISES; sending stays in the ward's hands. Never claim enforcement.
  blockedTitle: { hi: "{name} की सलाह — यह पैसा मत भेजिए", en: "{name} advises — do not send this money" },
  blockedSub: {
    hi: "भेजना आपके हाथ में है — पर आपके अपनों की नज़र आप पर है, यही आपकी ढाल है।",
    en: "Sending stays in your hands — and your family has your back. That is your shield.",
  },
  allowedTitle: { hi: "{name} ने कहा — ठीक है", en: "{name} said — it’s okay" },
  allowedSub: {
    hi: "फिर भी रक़म और नाम एक बार खुद जाँच लीजिए।",
    en: "Still double-check the amount and payee once yourself.",
  },
  noted: {
    hi: "{name} की नज़र में है — कोई ज्ञात खतरा नहीं था",
    en: "Shared with {name} — no known risk found",
  },
} satisfies Record<string, LangText>;

/* ---------------- landing ---------------- */
export const S_HOME = {
  markSub: { hi: "DHAAL — डिजिटल ठगी के खिलाफ", en: "DHAAL — against digital fraud" },
  promise1: { hi: "पैसे भेजने से पहले —", en: "Before you pay —" },
  promise2: { hi: "एक जाँच।", en: "one check." },
  promiseSub: {
    hi: "Message, QR, link, नंबर या call — पैसे भेजने से पहले, एक जाँच।",
    en: "Message, QR, link, number or call — one check before money moves.",
  },
  cta: { hi: "अभी जाँच करो", en: "Check now" },
  counter1: { hi: "इस हफ्ते Rajasthan में", en: "This week in Rajasthan" },
  counter2: { hi: "verified scam reports", en: "verified scam reports" },
  counter3: { hi: "हर report — सबकी ढाल", en: "every report shields everyone" },
  sGuardian: { hi: "परिवार की ढाल", en: "Family shield" },
  sGuardianSub: {
    hi: "Guardian mode — बड़े खतरे पर परिवार से पूछा जाए",
    en: "Guardian mode — family approves risky payments",
  },
  sIntel: { hi: "धोखों का नक्शा", en: "Scam war map" },
  sIntelSub: { hi: "समुदाय की live scam जानकारी", en: "Live scam intel from the community" },
  sRecover: { hi: "पहला घंटा", en: "The first hour" },
  sRecoverSub: { hi: "ठगी हो गई? Recovery kit", en: "Just got scammed? Recovery kit" },
  radarTitle: { hi: "धोखों का LIVE RADAR", en: "Live scam radar" },
  radarSub: { hi: "Rajasthan — हर बिंदु = verified reports", en: "Rajasthan — every dot = verified reports" },
  verifiedNow: { hi: "ज्ञात ठग", en: "Known scams" },
  statLive: { hi: "इस session में", en: "live this session" },
  statLangs: { hi: "भाषाएँ", en: "languages" },
  statFamilies: { hi: "signal families", en: "signal families" },
} satisfies Record<string, LangText>;

/* ---------------- /intel ---------------- */
export const S_INTEL = {
  title: { hi: "धोखों का नक्शा", en: "Scam war map" },
  queue: { hi: "जाँच बाकी", en: "Moderation queue" },
  queueEmpty: {
    hi: "कोई pending report नहीं — सब जाँची जा चुकीं",
    en: "No pending reports — all reviewed",
  },
  warMap: { hi: "धोखों का नक्शा", en: "War map" },
  week: { hi: "इस हफ्ते RAJASTHAN में", en: "THIS WEEK IN RAJASTHAN" },
  perDay: { hi: "रोज़ की रिपोर्टें", en: "Reports per day" },
  byType: { hi: "किस तरह के धोखे", en: "By scam type" },
  mostReported: { hi: "सबसे ज़्यादा रिपोर्ट हुए", en: "Most reported" },
  verify: { hi: "VERIFY — ढाल में जोड़ो", en: "VERIFY — add to the shield" },
  flashOk: {
    hi: "VERIFIED — अब हर जाँच में यह blocklist live है",
    en: "VERIFIED — live in every check now",
  },
  flashFail: { hi: "ACTION FAILED — दोबारा try करें", en: "ACTION FAILED — retry" },
  apiDown: { hi: "API नहीं मिल रही — RETRYING…", en: "API UNREACHABLE — RETRYING…" },
} satisfies Record<string, LangText>;

/* ---------------- /guardian ---------------- */
export const S_GUARDIAN = {
  title: { hi: "परिवार की ढाल", en: "Guardian mode" },
  createTitle: { hi: "अपनों की ढाल बनिए", en: "Be their shield" },
  createSub: {
    hi: "Pair बनाइए — जब वे कुछ खतरनाक जाँचेंगे, आपसे पूछा जाएगा।",
    en: "Create a pair — risky checks on their phone will ask you first.",
  },
  who: { hi: "किसकी रक्षा करनी है", en: "Who are you protecting" },
  whoPh: { hi: "जैसे: सुनीता देवी (दादी)", en: "e.g. Sunita Devi (grandma)" },
  yourName: { hi: "आपका नाम", en: "Your name" },
  yourNamePh: { hi: "जैसे: राहुल", en: "e.g. Rahul" },
  phoneLabel: { hi: "guardian का phone number (optional)", en: "Guardian’s phone (optional)" },
  phoneHint: {
    hi: "खतरे पर ward को 'इनसे पूछें' का call button मिलेगा — सिर्फ यही नंबर",
    en: "On danger, the ward gets a call button — this stored number only",
  },
  createBtn: { hi: "ढाल जोड़ो · Create pair", en: "Create pair" },
  creating: { hi: "बन रही है…", en: "Creating…" },
  youGuard: { hi: "आप {name} की ढाल हैं", en: "You guard {name}" },
  scanHint: {
    hi: "{name} के phone पर यह QR scan करवाएँ (या link भेजें) — बस, जुड़ गया।",
    en: "Scan this QR on {name}’s phone, or send the link — done.",
  },
  copyLink: { hi: "LINK COPY करें", en: "COPY LINK" },
  newPair: { hi: "नया PAIR बनाएँ", en: "NEW PAIR" },
  inboxSub: { hi: "{name} की जाँचें", en: "{name}’s checks" },
  newBadge: { hi: "{n} नई", en: "{n} new" },
  inboxEmpty: {
    hi: "अभी कोई request नहीं। {name} जब कुछ खतरनाक जाँचेंगे, यहाँ 3 सेकंड में दिखेगा।",
    en: "No requests yet. When {name} checks something risky, it lands here within 3 seconds.",
  },
  reqTitle: { hi: "{name} ने कुछ खतरनाक जाँचा", en: "{name} checked something risky" },
  block: { hi: "सलाह भेजो: मत भेजो", en: "Advise: STOP" },
  allow: { hi: "ठीक है · Allow", en: "Looks OK" },
  yourNote: { hi: "आपका note:", en: "Your note:" },
  notePh: {
    hi: "अपनी बात जोड़ें… जैसे: ठग है, मत भेजो (optional)",
    en: "Add a note… e.g. it’s a scam, don’t send (optional)",
  },
  notPaired: {
    hi: "अभी जुड़े नहीं — guardian का QR scan करें या code डालें",
    en: "Not paired yet — scan your guardian’s QR or enter the code",
  },
  activity: { hi: "गतिविधि", en: "Activity" },
  activitySub: { hi: "साफ़ जाँचें भी यहाँ दिखती हैं", en: "clean checks land here too" },
  joinTitle: { hi: "आपके अपनों ने code भेजा है?", en: "Got a pair code from family?" },
  joinBtn: { hi: "जुड़ो", en: "Join" },
  joinErrNotFound: {
    hi: "यह code नहीं मिला — दोबारा देख कर डालें",
    en: "Code not found — check it and retry",
  },
  // H14 pairing lifecycle: codes are single-use and expire in 30 minutes
  joinErrUsed: {
    hi: "यह code इस्तेमाल हो चुका — guardian से नया pairing बनवाएँ",
    en: "This code was already used — ask your guardian to create a fresh pairing",
  },
  joinErrExpired: {
    hi: "code की मियाद खत्म — guardian से नया code लें",
    en: "Code expired — ask your guardian for a fresh one",
  },
  joinErrRate: {
    hi: "बहुत कोशिशें हो गईं — एक मिनट रुक कर फिर डालें",
    en: "Too many attempts — wait a minute and retry",
  },
  codeTtlHint: {
    hi: "code 30 मिनट में expire होगा और एक ही बार चलेगा",
    en: "The code expires in 30 minutes and works exactly once",
  },
  rePairNotice: {
    hi: "सुरक्षा upgrade के बाद पुराना pairing बंद हो गया है — नया pair बनाएँ",
    en: "The old pairing was retired in a security upgrade — create a fresh pair",
  },
  joinErrConn: { hi: "जुड़ नहीं पाए — connection जाँचें", en: "Could not connect — check connection" },
  joinedTitle: { hi: "ढाल जुड़ गई!", en: "Shield connected!" },
  joinedSub: {
    hi: "{ward}अब हर बड़े खतरे पर {g} से पूछा जाएगा — आपकी जेब पर परिवार की नज़र।",
    en: "{ward}every big risk will now ask {g} first — family watching over your money.",
  },
  goCheck: { hi: "जाँच करने चलें →", en: "Start checking →" },
  unpair: { hi: "ढाल हटाएँ · UNPAIR", en: "UNPAIR" },
} satisfies Record<string, LangText>;

/* ---------------- /learn simulator ---------------- */
export const S_LEARN = {
  title: { hi: "ठग को पहचानो", en: "Spot the scam" },
  intro: {
    hi: "5 असली message — बताइए कौन ठग है। ढाल का engine जवाब जाँचेगा।",
    en: "5 real messages — call the scam. Dhaal’s engine checks your answer.",
  },
  start: { hi: "शुरू करो", en: "Start" },
  round: { hi: "message {i}/5", en: "message {i}/5" },
  scamBtn: { hi: "ठग है", en: "SCAM" },
  genuineBtn: { hi: "ठीक है", en: "GENUINE" },
  checking: { hi: "engine जाँच रहा है…", en: "engine checking…" },
  correct: { hi: "सही पकड़ा!", en: "Caught it!" },
  wrong: { hi: "धोखा हो गया", en: "It fooled you" },
  engineSaid: { hi: "ढाल का फ़ैसला", en: "Dhaal’s verdict" },
  next: { hi: "अगला →", en: "Next →" },
  seeScore: { hi: "नतीजा देखो →", en: "See score →" },
  scoreTitle: { hi: "आपने {n}/5 पकड़े", en: "You caught {n}/5" },
  scorePerfect: { hi: "आप खुद एक ढाल हैं!", en: "You are a shield yourself!" },
  scoreGood: { hi: "अच्छी नज़र — पर ठग रोज़ नए तरीके लाते हैं।", en: "Sharp eyes — but scammers bring new tricks daily." },
  scoreLow: {
    hi: "यही तो ठग चाहते हैं — इसीलिए हर message ढाल से जाँचिए।",
    en: "That’s exactly what scammers count on — check every message with Dhaal.",
  },
  ctaInbox: { hi: "अपना inbox जाँचो →", en: "Check your own inbox →" },
  again: { hi: "फिर खेलो", en: "Play again" },
} satisfies Record<string, LangText>;

/* ---------------- /recover ---------------- */
export const S_RECOVER = {
  title: { hi: "पहला घंटा", en: "I got scammed — first hour" },
  introBold: { hi: "घबराइए मत — साँस लीजिए।", en: "Don’t panic — breathe." },
  intro: {
    hi: "पहला घंटा सबसे कीमती है: जल्दी complaint होने पर पैसा freeze होने की उम्मीद कई गुना बढ़ जाती है।",
    en: "The first hour matters most: an early complaint multiplies the chance of freezing the money.",
  },
  call1930: { hi: "1930 पर अभी call करें", en: "Call 1930 now" },
  qTitle: { hi: "2 सवाल — आपका kit तैयार होगा", en: "2 questions — your kit will be ready" },
  optPaid: { hi: "पैसे चले गए", en: "I paid / money left my account" },
  optOtp: { hi: "OTP / PIN बता दिया", en: "I shared an OTP or PIN" },
  optLink: { hi: "Link पर click कर दिया", en: "I clicked a link / installed an app" },
  amount: { hi: "कितने ₹", en: "Amount ₹" },
  how: { hi: "कैसे गए", en: "How" },
  bank: { hi: "बैंक", en: "Bank" },
  // H14: the incident date is the USER's — never assumed to be today
  when: { hi: "कब हुआ", en: "When" },
  buildBtn: { hi: "मेरा kit बनाओ · Build my kit", en: "Build my kit" },
  building: { hi: "बन रहा है…", en: "Building…" },
  say1930: { hi: "1930 पर क्या बोलें", en: "What to say on 1930" },
  complaint: { hi: "Cybercrime.gov.in complaint", en: "Online complaint draft" },
  bankLetter: { hi: "बैंक के लिए चिट्ठी", en: "Letter to your bank" },
  checklistSub: { hi: "एक-एक करके", en: "one by one" },
  allDone: { hi: "सब हो गया — शाबाश", en: "All done — well done" },
} satisfies Record<string, LangText>;

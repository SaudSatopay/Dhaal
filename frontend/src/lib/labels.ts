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
} satisfies Record<string, LangText>;

/* ---------------- verdict card ---------------- */
export const S_VERDICT = {
  why: { hi: "ऐसा क्यों", en: "Why this verdict" },
  noSignals: { hi: "कोई खतरे का संकेत नहीं मिला", en: "No risk signals detected" },
  sealReports: { hi: "रिपोर्ट", en: "REPORTS" },
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
  blockedTitle: { hi: "{name} ने कहा — यह पैसा मत भेजिए", en: "{name} said — do not send this money" },
  blockedSub: {
    hi: "कोई पैसा नहीं गया। आपके अपनों की नज़र आप पर है — यही आपकी ढाल है।",
    en: "Nothing was sent. Your family has your back — that is your shield.",
  },
  allowedTitle: { hi: "{name} ने कहा — ठीक है", en: "{name} said — it’s okay" },
  allowedSub: {
    hi: "फिर भी रक़म और नाम एक बार खुद जाँच लीजिए।",
    en: "Still double-check the amount and payee once yourself.",
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
  block: { hi: "रोक दो · Block", en: "Block" },
  allow: { hi: "ठीक है · Allow", en: "Allow" },
  yourNote: { hi: "आपका note:", en: "Your note:" },
  notePh: {
    hi: "अपनी बात जोड़ें… जैसे: ठग है, मत भेजो (optional)",
    en: "Add a note… e.g. it’s a scam, don’t send (optional)",
  },
  joinTitle: { hi: "आपके अपनों ने code भेजा है?", en: "Got a pair code from family?" },
  joinBtn: { hi: "जुड़ो", en: "Join" },
  joinErrNotFound: {
    hi: "यह code नहीं मिला — दोबारा देख कर डालें",
    en: "Code not found — check it and retry",
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
  buildBtn: { hi: "मेरा kit बनाओ · Build my kit", en: "Build my kit" },
  building: { hi: "बन रहा है…", en: "Building…" },
  say1930: { hi: "1930 पर क्या बोलें", en: "What to say on 1930" },
  complaint: { hi: "Cybercrime.gov.in complaint", en: "Online complaint draft" },
  bankLetter: { hi: "बैंक के लिए चिट्ठी", en: "Letter to your bank" },
  checklistSub: { hi: "एक-एक करके", en: "one by one" },
  allDone: { hi: "सब हो गया — शाबाश", en: "All done — well done" },
} satisfies Record<string, LangText>;

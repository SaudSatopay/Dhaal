"""Social-engineering script detection — bilingual, CLAUSE-LEVEL (H14 rework).

Three upgrades over pure keyword tables (external review P0):
  1. Sentence scope. Text splits into sentences; directive-demand patterns
     (send money / share OTP / pay fee / approve) match per sentence with
     sentence-local NEGATION stripped first — "Do not send money to anyone"
     is not a demand, while "Please send me your OTP. Do not share it with
     anyone else." still is (the negation lives in a different sentence).
  2. Requester attribution for credentials. A credential must be REQUESTED
     (directive verb toward the sender/chat) to fire; mentions, deliveries
     ("887213 is your OTP… do not share") and self-help questions ("How do I
     reset my password?") do not. Telling an OTP to a physically present
     delivery agent / driver is a legitimate platform flow and is exempt
     unless the ask points back to the requester's chat/number.
  3. Reported speech. Educational/awareness/news framing (lecture, workshop,
     advisory, "beware of…") suppresses script-family convictions when the
     text contains no actual directive at the reader — describing a scam is
     not receiving one.

Single latin words are word-boundary regexes ('army' must not fire inside
'harmony'); Devanagari and multi-word phrases match as substrings. The legit
bank-SMS fixture (beat 3) stays the false-positive control.
"""

import re

from engine.common import make_signal


def _rx(words: list[str]) -> list[re.Pattern]:
    out = []
    for w in words:
        if re.fullmatch(r"[a-z0-9]+", w):
            out.append(re.compile(rf"\b{w}\b", re.I))
        else:
            out.append(re.compile(re.escape(w), re.I))
    return out


_SENT_SPLIT = re.compile(r"(?<=[.!?।;])\s+|\n+")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


# ---- sentence-local negation (directive demands only — threat grammar like
# "नहीं भेजा तो जेल" is matched RAW by the coercion patterns, never stripped)
_NEG_STRIP = [
    re.compile(
        r"(?:\bdo\s+not\b|\bdon'?t\b|\bnever\b|\bno\s+need\s+to\b|\bmat\b|मत|"
        r"कभी\s*(?:मत|न(?:हीं)?)|\bkabhi\s+(?:mat|na)\b|\bnahin?\b|नहीं|\bन\b|\bna\b)"
        r"\s+(?:[\w₹.,'-]+\s+){0,3}?"
        r"(?:send|share|give|tell|pay|forward|transfer|enter|type|approve|click|"
        r"bhej\w*|भेज\w*|बता\w*|batao?\w*|daal\w*|डाल\w*|de\b|दे\w*|kar\w*|कर\w*)\w*",
        re.I),
    # "no fee/charge is payable", "koi shulk nahi", "फीस नहीं लगेगी", "free of charge"
    re.compile(r"(?:\bno\b|\bzero\b|कोई|\bkoi\b)\s+(?:[\w-]+\s+){0,2}?"
               r"(?:fee|charge|payment|shulk|शुल्क|फीस|paisa|पैसा)\w*[^.।!?]{0,30}", re.I),
    re.compile(r"(?:fee|charge|shulk|शुल्क|फीस)\w*[^.।!?]{0,25}"
               r"(?:नहीं|nahin?|not\s+payable|no\s+need|waived|माफ़|free)", re.I),
]


def _strip_negated(sentence: str) -> str:
    """LENGTH-PRESERVING (H16): negated demand spans become same-length
    spaces, so every offset found in stripped text is valid in the raw text —
    the evidence-position contract depends on this."""
    for p in _NEG_STRIP:
        sentence = p.sub(lambda m: " " * len(m.group(0)), sentence)
    return sentence


# ---- reported/educational framing (suppresses convictions, never directives)
# H17: impersonal NEWS/ADVISORY frame — a third-party actor described to the
# public, nobody addressed. Suppression logic below lets this override even
# directive-shaped vocabulary, but ONLY when nothing targets "you/aap".
_NEWS_FRAME = re.compile(
    r"police\s+warn|advisory|पुलिस\s+ने\s+(?:चेताया|चेतावनी)|"
    r"fraudsters\s+(?:are|demand|ask)|scammers\s+(?:are|demand|ask)|"
    r"ठग\s+(?:लोग|माँग|मांग)|con\s?men|racket\s+busted|गिरोह",
    re.I)
_SECOND_PERSON = re.compile(
    r"\byour?\b|\baap(?:ka|ke|ki)?\b|आप(?:का|के|की)?|\btum(?:hara|he)?\b|"
    r"तुम्हार|तुम्हें|तेरा|\btera\b", re.I)

_AWARENESS = re.compile(
    r"awareness|workshop|seminar|lecture|classroom|professor|teacher|training|"
    r"advisory|warn(?:ed|ing)\s+(?:us|me|people|about)|beware\s+of|savdhan\s+rahe|"
    r"news|article|akhbar|अख़बार|अखबार|जागरूकता|सिखाया|पढ़ाया|समझाया|\bpadhaya\b|"
    r"\bsikha(?:ya)?\b|cyber\s+safety"
    # tutorial/news registers the v3 battery exposed (v3-044/045)
    r"|समाचार|ख़बर|खबर\s*:|\bkhabar\b|breaking\s*:|\breport\s*:"
    r"|toh\s+doston|दोस्तों|aaj\s+ke\s+session|is\s+video\s+me(?:in)?"
    r"|samjh(?:t|a)e?\s+hain|समझते\s+हैं|सीखेंगे|seekhenge|police\s+ne\s+.{0,30}(?:pakda|गिरफ़्तार|arrest)"
    r"|almost\s+fell\s+for|fell\s+for\s+it|got\s+one\s+of\s+those|mere\s+dost\s+ko\s+aaya|friend\s+got",
    re.I)


# H12 (external review): single ambient words must not convict. Each category
# has STRONG patterns (unambiguous scam grammar — fire alone) and WEAK tokens
# (ambient words like parcel/police/army — fire only when ≥2 co-occur AND the
# text carries money/pressure context).
CATEGORIES: dict[str, tuple[int, list, list]] = {
    "digital_arrest": (35, _rx([
        "digital arrest", "digitally arrest", "digitally arrested", "गिरफ",
        "arrest warrant", "cyber crime", "साइबर क्राइम", "साइबर सेल", "cbi",
        "narcotics", "money laundering", "courier pakda", "ed notice",
        "court warrant",
    ]), _rx([
        "arrest", "arrested", "police", "पुलिस", "parcel", "पार्सल",
        "customs", "कोर्ट", "court", "jail", "जेल", "साइबर", "inspector",
        "इंस्पेक्टर", "verification fee",
    ])),
    "lottery": (30, _rx([
        "lottery", "लॉटरी", "lucky draw", "लकी ड्रा", "jackpot", "kbc",
        "crorepati", "lakh jeet", "jeet gaye", "bumper draw", "बम्पर",
    ]) + [
        # money-scoped "you won ₹X" — cricket scores never carry a currency
        re.compile(r"(?:won|jeet[ae]?|जीत[ae]?)\s?[^.।!?]{0,25}"
                   r"(?:₹|\brs\.?\b|lakh|लाख|crore|करोड़|\d[\d,]{4,})", re.I),
    ], _rx([
        "prize", "इनाम", "winner", "jeeta", "जीते", "claim",
    ])),
    "kyc_expiry": (25, _rx([
        "kyc", "केवाईसी", "खाता बंद", "khata band", "account block",
        "account suspend", "खाता निलंबित", "pan update", "पैन अपडेट",
        "आधार अपडेट", "reactivate",
        # telecom-regulator family (held-out v2 miss): SIM/number kill threats
        "sim deactivat", "sim block", "sim band", "सिम बंद", "number band ho",
        "नंबर बंद हो",
    ]) + [
        re.compile(r"\bsim\b[^.।!?]{0,30}(?:deactivat|block|band|suspend)", re.I),
        re.compile(r"(?:\bnumber\b|नंबर)[^.।!?]{0,25}(?:deactivat|disconnect|band|बंद)", re.I),
        # v5: account frozen/held pending "verification" — any word order
        re.compile(r"(?:खाता|account|a/c)[^.।!?]{0,30}(?:रोक|freeze|frozen|"
                   r"\bhold\b|lock|suspend)", re.I),
    ], _rx([
        "trai",
    ])),
    "electricity": (25, _rx([
        "बिजली", "electricity", "bijli", "power cut", "बत्ती काट",
        "meter update",
    ]), _rx([
        "disconnect", "बिल बकाया", "bill pending",
    ])),
    "olx_army": (30, _rx([
        "advance payment", "एडवांस",
    ]), _rx([
        "army", "आर्मी", "crpf", "bsf", "fauji", "olx", "canteen",
    ])),
    "customer_care": (25, _rx([
        "customer care", "कस्टमर केयर", "helpline number", "toll free",
        "refund process", "complaint number", "care number",
        # v5: support-callback frames ("we saw your complaint… refund")
        "saw your complaint", "regarding your complaint",
    ]) + [
        re.compile(r"process[^.।!?]{0,20}refund|refund[^.।!?]{0,15}process", re.I),
    ], _rx([
        "रिफंड", "refund",
    ])),
    "job_scam": (30, _rx([
        "work from home job", "ghar baithe kamaye", "घर बैठे कमा", "part time job",
        "earn rs", "earn ₹", "earn daily", "daily earning", "roz kamao",
        "रोज़ कमा", "liking videos", "like videos", "telegram task",
        "limited seats", "instagram follow", "task team", "टास्क टीम",
        "prepaid task", "प्रीपेड टास्क", "पहला टास्क", "welcome task",
        # v5 regression families: recruitment-fee frames
        "work-from-home", "data entry job", "per task", "har task",
        "rate hotels", "rate products", "kit fee", "joining fee",
    ]) + [
        re.compile(r"(?:shortlisted|selected)[^.।!?]{0,35}(?:job|role|position|"
                   r"work[- ]?from[- ]?home|wfh|internship|data\s+entry)", re.I),
    ], _rx([
        "youtube video", "registration",
    ])),
    "investment_doubling": (30, _rx([
        "double your money", "money double", "paisa double", "पैसा डबल",
        "guaranteed return", "guaranteed profit", "फिक्स रिटर्न",
        "daily profit", "trading group", "trading tips group",
        # v5 regression family: crypto-doubling events
        "get 2x", "2x back", "double back", "usdt",
    ]) + [
        re.compile(r"send\s+any[^.।!?]{0,25}(?:usdt|crypto|btc|coin)", re.I),
        re.compile(r"\d{1,3}\s?%\s?(?:return|profit|munafa|रिटर्न)", re.I),
        re.compile(r"(?:deposit|invest|जमा)[^.।!?]{0,30}(?:double|profit|return|डबल)", re.I),
    ], []),
    "gift_parcel_customs": (30, _rx([
        "gift parcel", "गिफ्ट पार्सल", "foreign friend", "विदेशी मित्र",
        "videshi dost", "customs par atka", "कस्टम में अटका",
        "customs clearance", "airport par parcel", "parcel me pound",
        "parcel me dollar", "पाउंड रखे",
        # H17: the held-consignment ransom frame, any phrasing
        "customs bond", "customs security", "international package",
    ]) + [
        re.compile(r"(?:holding|held|detained|seized)[^.।!?]{0,35}"
                   r"(?:package|parcel|पार्सल|shipment|consignment)", re.I),
    ], []),
    "loan_fee": (30, _rx([
        "loan approve", "loan approved", "pre-approved loan",
        "pre approved loan", "instant loan", "लोन approve", "लोन मंजूर",
        "आधार पर लोन", "बिना गारंटी लोन", "file charge", "loan sanction",
        "लोन स्वीकृत", "पर्सनल लोन", "ऋण स्वीकृत",
    ]) + [
        re.compile(r"(?:राशि|amount|रक़म)[^.।!?]{0,40}(?:से पहले|se pehle)[^.।!?]{0,40}(?:शुल्क|फीस|fee|charge|जमा)", re.I),
        # gap-tolerant (v3-009: "instant PERSONAL loan", "loan ... approve
        # ho gaya", "GST/charge before disbursal")
        re.compile(r"\b(?:instant|pre.?approved)\b[^.।!?]{0,25}\bloan\b", re.I),
        re.compile(r"(?:\bloan\b|लोन|ऋण)[^.।!?]{0,40}(?:approve|approved|अप्रूव|"
                   r"sanction|मंजूर|स्वीकृत|pass ho)", re.I),
        re.compile(r"(?:इंस्टेंट|तत्काल)[^.।!?]{0,20}(?:लोन|ऋण)", re.I),
        re.compile(r"(?:disbursal|disburse|loan amount)[^.।!?]{0,50}(?:pehle|पहले|before|first)", re.I),
    ], []),
}

# Money/pressure context that lets weak tokens combine into a category hit.
_CTX = _rx([
    "₹", "rs.", "rupees", "rupay", "paise", "fee", "फीस", "फ़ीस", "bhejo",
    "भेजो", "send money", "pay", "payment", "upi", "account", "खाते", "खाता",
    "transfer", "तुरंत", "turant", "immediately", "urgent", "अभी", "warna",
    "वरना", "किसी को मत", "tell no one",
    # H16: bare "verification" removed — it co-fired innocent weak-token pairs
    # (v3-053: passport verification + court date). "verification fee" still
    # counts via fee_demand.
])

_CROSS = [
    ("urgency_framing", 15, "Artificial urgency", "बनावटी जल्दबाज़ी",
     "Scams pressure you to act before you think.",
     "ठग सोचने का समय नहीं देते — जल्दबाज़ी ही चाल है।",
     _rx(["तुरंत", "turant", "immediately", "urgent", "abhi", "अभी",
          "24 घंटे", "24 hours", "24 hour", "2 घंटे", "2 hours", "last warning",
          "अंतिम चेतावनी", "final notice", "जल्दी करें"])),
    ("secrecy_pressure", 20, "Told to keep it secret / cut contact", "छिपाने-अलग करने का दबाव",
     "'Tell no one' and 'don't call' cut you off from the people who would stop this.",
     "'किसी को मत बताओ' और 'call मत करो' कहकर ठग आपको मदद से काटते हैं।",
     _rx(["किसी को मत", "किसी को न बता", "बताइए मत", "बताना मत",
          "tell no one", "don't tell", "do not tell", "confidential",
          "गोपनीय", "किसी से साझा न", "don't call", "do not call",
          "call मत", "फोन मत", "phone mat"])),
    ("fee_demand", 20, "Upfront fee demanded", "पहले फीस माँगी जा रही है",
     "Prizes, refunds and jobs that need a fee first are scams.",
     "जहाँ इनाम/refund से पहले फीस माँगे, वह ठगी है।",
     _rx(["processing fee", "processing charge", "verification fee",
          "वेरिफिकेशन फीस", "फीस भेज", "registration fee", "token amount",
          "security deposit", "शुल्क भेज", "फीस जमा", "file charge",
          "gst charge", "gst jama", "gst जमा", "delivery charge",
          "customs duty", "custom duty", "क्लीयरेंस फीस", "clearance fee",
          "verification amount", "release fee",
          # H17 fee-noun synonyms (judge misses: bond/deposit words)
          "security bond", "customs bond", "clearance deposit",
          "clearance charge", "bond amount", "सिक्योरिटी बॉन्ड",
          # v5 regression: recruitment/insurance fee skins
          "kit fee", "joining fee", "training fee", "joining amount",
          "reactivation fee", "reactivation charge", "unlock fee",
          "टोकन राशि", "token राशि", "trial payment", "ट्रायल भुगतान"])
     + [re.compile(r"(?:charge|fee|shulk|शुल्क|फीस)[^.।!?]{0,25}(?:jama|जमा|bhar|भर|pay\s+kar)", re.I),
        # H17 passive requirement: "a ... bond/deposit of Rs X is required" —
        # runs on negation-stripped text, so "no deposit required" never fires
        re.compile(r"(?:bond|deposit|fee|charge|शुल्क|फीस|राशि)[^.।!?]{0,30}"
                   r"(?:is\s+required|required\s+before|is\s+needed|"
                   r"is\s+payable|payable\s+before|देय\s+है|"
                   r"देना\s+होगा|भरना\s+होगा|अनिवार्य\s+है)", re.I)]),
    # Victim-voiced coercion — judges type DESCRIPTIONS of the threat, not the
    # scammer's script ("I was told to send money or I'd be arrested"). H11.
    ("coercion_extortion", 30, "Money demanded under threat", "धमकी देकर पैसे माँगे जा रहे हैं",
     "Anyone conditioning your safety on a payment is running a scam — real authorities never do.",
     "जो 'पैसे भेजो वरना…' कहे वह ठग है — असली अधिकारी कभी ऐसा नहीं करते।",
     _rx(["if i don't send", "if i dont send", "if i don't pay", "if i dont pay",
          "if i wouldn't send", "if i wouldnt send", "wouldn't send them money",
          "send them money or", "send money or", "pay or else", "or else",
          "told me to send money", "told to send money", "told to pay",
          "asking me to pay", "asking me for money", "demanding money",
          "threaten", "threatened", "धमकी", "वरना", "warna", "नहीं भेजे तो",
          "नहीं भेजा तो", "नहीं दिए तो", "भेजो नहीं तो", "bhejo nahi to",
          "दो नहीं तो", "do nahi to", "पैसे माँग रह", "paise maang",
          "मजबूर कर", "डरा कर पैसे", "डरा रहे", "छुड़ाने के लिए",
          "chhudane ke liye", "bachane ke liye paise", "बचाने के लिए पैसे"])),
    ("threat_framing", 15, "Threat of penalty/action", "डराने-धमकाने की भाषा",
     "Fear of fines, arrest or disconnection is the pressure lever.",
     "जुर्माना, गिरफ़्तारी या कटौती का डर दिखाना ही इनका हथियार है।",
     _rx(["legal action", "कानूनी कार्रवाई", "जुर्माना", "penalty",
          "case दर्ज", "blacklist",
          # bare-menace vocabulary (held-out v3 miss: threat with no ask
          # scored 0 and got a green card)
          "अंजाम भुगत", "anjaam bhugat", "anjam bhugat", "भुगतना पड़ेगा",
          "bhugatna padega", "बुरा होगा", "bura hoga", "देख लेंगे",
          "dekh lenge", "छोड़ूँगा नहीं", "chhodunga nahi",
          "you will regret", "regret this", "i know where you live",
          "जान से", "jaan se", "ghar jaanta", "घर जानता",
          # v5: bare menace-knowledge ("I know what you did… dekhta hu")
          "dekhta hu", "देखता हूँ", "देखता हूं", "sab pata hai",
          "सब पता है"])),
]

# ---- credentials: request vs delivery vs mention (per-sentence) -------------
_CRED_MENTION = _rx(["otp", "pin", "cvv", "password", "पासवर्ड", "mpin",
                     "one time password", "one-time code", "one time code",
                     "verification code", "card number", "expiry date",
                     # periphrasis (H17 judge miss): scammers avoid the word
                     # OTP — "the six digits that just arrived" IS the OTP
                     "digit", "digits", "अंक", "अंकों", "ank", "anko",
                     "छह number", "chhe number",
                     # card-details harvest phrasings
                     "card details", "कार्ड की जानकारी", "कार्ड विवरण",
                     "card ki jankari"])
_CRED_DELIVERY = _rx(["is your otp", "is your one time password", "otp for",
                      "one time password for", "otp is", "code is"])
# directive verb → credential, or credential → directive/direction, in ONE
# sentence (negation already stripped). "code" alone is too broad — only
# qualified code phrases count.
_CRED_TOKEN = (r"(?:otp|ओटीपी|one[\s-]?time\s+(?:password|code)|verification\s+code|"
               r"security\s+code|sms\s+code|\d{1,2}[\s-]?digit\s+code|pin|mpin|"
               r"upi\s+pin|cvv|password|पासवर्ड|पिन"
               # H17 periphrasis family: a counted-digits noun phrase, or
               # "digits that (just) arrived/came" — the OTP without its name
               r"|(?:\d{1,2}|four|five|six|चार|पाँच|छह|chaar|paanch|chhe)"
               r"[\s-]?(?:digits?|अंकों?|अंक|ank(?:o)?\b)(?:\s+ka\s+number)?"
               r"|(?:digits?|अंक(?:ों)?)\s+(?:that|jo|जो)[^.।!?]{0,30}?"
               r"(?:arrived|came|received|mile|aaye?|आया|आए|मिला|मिले)"
               r"|card\s+details|कार्ड\s+(?:की\s+जानकारी|विवरण)|card\s+ki\s+jankari)")
_CRED_REQ_A = re.compile(
    r"(?:send|share|forward|tell|give|type|enter|read\s+out|confirm|"
    r"reply\s+(?:with|karke)|batao?|"
    r"बता(?:ओ|इए|एँ|एं|ये|यें)?|bhej(?:o|iye|ein|en)?|भेज(?:ो|िए|ें|े)?|"
    r"likh(?:o|iye)?|daal(?:o|iye)?|डाल(?:ो|िए|ें)?|dij(?:iye|iy?e)|दीजिए|"
    r"de\s+do|दे\s+दो)\w*\b[^.।!?]{0,50}?" + _CRED_TOKEN,
    re.I)
_CRED_REQ_B = re.compile(
    _CRED_TOKEN + r"[^.।!?]{0,70}?(?:bhej|भेज|bata|बता|share|send|forward|"
    r"dij(?:iye|e)|दीजिए|दे\s+दो|मुझे|mujhe|यहाँ|yahan|"
    r"is\s+(?:number|chat)|इस\s+(?:नंबर|चैट)|हमें|humein|"
    r"darj|दर्ज|enter\s+kar|भर(?:ें|िए|o)?\b)",
    re.I)
# telling/showing an OTP to a physically present platform agent is a real flow
_AGENT_CTX = re.compile(
    r"driver|rider|delivery\s*(?:boy|agent|partner|executive|associate)|courier\s*(?:boy|wala)|"
    r"डिलीवरी|ड्राइवर|राइडर|कूरियर"
    # v5 FP fix: direction-to-agent phrasings without the word "delivery"
    r"|(?:with|to)\s+the\s+agent|agent\s+(?:ko|at\s+(?:the\s+)?door)|एजेंट\s+को", re.I)
# v5 miss fix: the agent exemption is for a PHYSICAL handoff. A caller
# CLAIMING to be the courier ("courier boy bol raha hu... OTP batao") is a
# counterparty request over the phone — the exemption must not apply.
_CALLER_CLAIM = re.compile(
    r"bol\s+rah[ai]\s+h(?:u|un|oon)|बोल\s+रह[ाी]\s+(?:हूँ|हूं)|"
    r"calling\s+from|speaking\s+from|मैं\s+.{0,25}(?:से|department)\s+बोल", re.I)
_CHAT_DIRECTION = re.compile(
    r"मुझे|mujhe|to\s+me|this\s+chat|is\s+(?:number|chat)|इस\s+(?:नंबर|चैट)|"
    r"हमें|humein|whatsapp\s+kar|call\s+par|फोन\s+पर\s+बता", re.I)
# remote-access tooling = credential-grade access request
_REMOTE_ACCESS = _rx(["anydesk", "teamviewer", "quick support", "quicksupport",
                      "screen share", "screen sharing", "remote access"])

# Refund/prize that requires SENDING money first — the advance-fee mechanic.
_BAIT_GET = _rx(["refund", "रिफंड", "cashback", "कैशबैक", "prize", "इनाम",
                 "lottery", "claim your", "claim karne", "वापसी", "winner",
                 "to receive your", "receive karne", "loan", "लोन",
                 "disbursal", "salary milegi", "job milegi",
                 # v4 families: bonus/benefit release, govt-yojana payouts
                 "bonus", "बोनस", "policy", "yojana", "योजना", "मिलेंगे",
                 "milenge", "release hone", "रिलीज़", "on hold", "atka",
                 # H17 windfall families: inheritance/legacy money
                 "inheritance", "विरासत", "वसीयत", "virasat", "wasiyat",
                 "legacy",
                 # v5 regression: selection/maturity windfalls
                 "shortlisted", "selected for", "maturity", "मैच्योरिटी",
                 "आपको मिली है", "जीत लिया"]) + [
    # money someone "left you" — money-scoped so "left you a voicemail" never
    # counts (H17 judge miss: inheritance advance-fee)
    re.compile(r"left\s+you[^.।!?]{0,25}(?:₹|\brs\.?\b|rupees|lakh|लाख|crore|"
               r"करोड़|\d{4,9}|property|estate)", re.I),
    re.compile(r"(?:आपके|aapke)\s+(?:naam|नाम)[^.।!?]{0,25}(?:छोड़|chhod)", re.I),
    # a HELD/DETAINED deliverable ransomed behind a fee (H17 judge miss:
    # customs bond). Requires the hold verb — plain COD/delivery lines with a
    # parcel word never count.
    re.compile(r"(?:holding|held|detained|stuck|seized|rok(?:a|\s+diya)|रोक(?:ा|\s+दिया)|atka|अटका)"
               r"[^.।!?]{0,35}(?:package|parcel|पार्सल|shipment|consignment|courier|कूरियर)", re.I),
    re.compile(r"(?:package|parcel|पार्सल|shipment|consignment)[^.।!?]{0,35}"
               r"(?:\bhold\b|holding|held|detained|stuck|seized|custody|rok(?:a|\s+diya)|रोक(?:ा|\s+दिया)|atka|अटका)", re.I),
]
_BAIT_SEND = _rx(["paise bhejo", "पैसे भेजो", "paise bhej", "पैसे भेज",
                  "send money", "pay first", "pehle pay", "pehle bhejo",
                  "पहले भेजो", "pehle bhejein", "पहले भेजें", "transfer karo",
                  "transfer kare", "pay karo", "send rs", "send ₹",
                  "pay delivery charge", "delivery charge",
                  "shipping charge"]) + [
    # money-scoped sends — "documents bhejo" must never count (H16 precision)
    re.compile(r"(?:₹|\brs\.?\b|paise|पैसे|fee|फीस|charge|शुल्क|\d{2,7})"
               r"[^.।!?]{0,20}?"
               r"(?:bhej(?:o|iye|ein|en|\s+do)?|भेज(?:ो|िए|ें|\s+दो)?)", re.I),
    re.compile(r"(?:bhej(?:o|iye|ein|en)?|भेज(?:ो|िए|ें)?)\s*(?:karne\s+par)?"
               r"[^.।!?]{0,12}(?:₹|\brs\.?\b|\d{3,7})", re.I),
] + [
    # money-scoped deposits only — "documents jama karo" must never count
    re.compile(r"(?:₹|\brs\.?\b|paise|पैसे|fee|फीस|charge|शुल्क|amount|राशि|"
               r"\d{2,7})[^.।!?]{0,26}(?:jama|जमा)", re.I),
    # money-scoped bhugtan/payable forms ("2 रुपये का ट्रायल भुगतान करें",
    # "clearance charge of 6,300 is payable")
    re.compile(r"(?:₹|\brs\.?\b|रुपये|rupees|\d{1,7})[^.।!?]{0,25}"
               r"(?:भुगतान|bhugtan)", re.I),
    re.compile(r"(?:fee|charge|deposit|bond|शुल्क|फीस|राशि)[^.।!?]{0,30}"
               r"(?:payable|is\s+required|देय)", re.I),
    # H17 send-verb synonyms, money-scoped: remit/deposit/wire ₹X — and the
    # Hinglish verb-final order "2500 rupees ... remit karein". Reverse form
    # is remit/wire ONLY: "Rs X was deposited to your account" (a legit
    # credit notice) must never read as a send demand.
    re.compile(r"\b(?:remit|wire)\b[^.।!?]{0,35}(?:₹|\brs\.?\b|rupees|"
               r"\d{3,7})", re.I),
    # imperative deposit: amount must FOLLOW immediately — "was deposited to
    # your account" (a credit notice) must never read as a send demand
    re.compile(r"\bdeposit\s+(?:₹|\brs\.?\s?|rupees\s)?\d{2,7}", re.I),
    re.compile(r"(?:₹|\brs\.?\b|rupees|\d{3,7})[^.।!?]{0,35}"
               r"\b(?:remit|wire)\b", re.I),
    # H17 cross-sentence referent send: "send it to the account below/this
    # UPI" — the money antecedent lives in an earlier sentence; the composite
    # still requires a bait/fee co-signal, so bare logistics never fire
    re.compile(r"send\s+(?:it|this|the\s+(?:amount|fee|bond|deposit))\s+to\s+"
               r"(?:the\s+|this\s+|इस\s+)?(?:account|upi|खाते|number\s+below|below)", re.I),
]

_COLLECT_PHRASE = re.compile(
    r"collect request|collect रिक्वेस्ट|रिक्वेस्ट|request\s+(?:bheji|भेजी|aayi|आई)", re.I)
_APPROVE_WORD = re.compile(r"\bapprove|\baccept\b|स्वीकार|मंज़ूर", re.I)

# ---- extortion via threatened disclosure/harm (H16: v3-016 family) ----------
# Relation, not phrasing: [I hold something over you] + [demand]. The threat
# alone (no demand) routes to the threat_no_ask clarification instead.
_DISCLOSURE_THREAT = _rx([
    "recorded you", "recorded your", "your private video", "private video",
    "private photo", "tumhara video", "तुम्हारा video", "तेरा video",
    "aapka video", "आपकी private", "photos मेरे पास", "photo मेरे पास",
    "video मेरे पास", "video mere paas", "photos mere paas",
    "send it to your family", "send to your contacts",
    "sabko bhej", "सबको भेज", "family ko bhej", "परिवार को भेज",
    "घरवालों को भेज", "रिश्तेदारों को भेज", "viral kar", "वायरल कर",
    "leak kar", "लीक कर", "badnaam kar", "बदनाम कर", "photo edit",
    "nangi photo", "अश्लील", "mms", "screenshot sabko", "expose kar",
    "sabko dikha", "सबको दिखा", "izzat", "इज़्ज़त",
    # v4 (blind battery) family variants: screen-recorded chats, contact-list
    # humiliation (loan-app harassment), "recording is with us" politeness
    "screen-record", "screen record", "recording हमारे पास",
    "रिकॉर्डिंग हमारे पास", "recording mere paas", "every contact",
    "all your contacts", "contact list", "कॉन्टैक्ट लिस्ट",
    "रिश्तेदारों तक", "रिश्तेदारों को भेज", "सबके पास भेज",
    "video chat", "वीडियो कॉल की रिकॉर्ड",
])
# demanded action verbs beyond money (delete/meet/obey) — money demand comes
# from _BAIT_SEND/_SEND_DIRECTIVE post-strip
_DEMAND_VERBS = _rx(["transfer", "bhejo", "भेजो", "bhej do", "भेज दो", "pay",
                     "send", "de do", "दे दो", "jama kar", "जमा कर"])

# ---- self-initiated flow question (H16): "Where do I enter the OTP in the
# official app?" is a user asking about THEIR OWN action — a question, not a
# request from a counterparty. Interrogative + first-person + no redirect to
# the asker's chat/number = mention, never credential_request.
_SELF_QUERY = re.compile(
    r"(?:^|\b)(?:where|how|when|can i|should i|do i|kahan|kaha|kaise|kab|"
    r"कहाँ|कहां|कैसे|कब)\b[^.।!?]{0,60}?(?:\bi\b|\bmy\b|\bme\b|main|mai|apna|"
    r"mera|मैं|मेरा|अपना|करूँ|करूं|karu|karun|daalu|dalu|डालूँ|डालूं|likhu)"
    r"|(?:karu|karun|daalu|dalu|करूँ|करूं|डालूँ|डालूं|likhu|likhun)\s*\?",
    re.I)

# ---- delivered-code referent (H16): once ANY sentence establishes that a
# code/OTP was delivered ("jo code abhi aaya", "the code you received"), a
# later bare directive — "send it here", "wo mujhe bata do", "code bhejo" —
# is a credential request even without the word OTP in that sentence.
_CODE_DELIVERED = re.compile(
    r"(?:otp|code|कोड|ओटीपी|digits?|अंक)[^.।!?]{0,50}(?:aaya|आया|aya|mila|मिला|"
    r"मिले|aaye|आए|received|arrived|"
    r"bheja (?:hai|gaya)|भेजा (?:है|गया)|sent (?:you|to you))"
    r"|(?:just|abhi|अभी)\s+(?:got|received|arrived|aaya|आया)[^.।!?]{0,20}"
    r"(?:otp|code|कोड|digits?|अंक)",
    re.I)
_BARE_REF_REQ = re.compile(
    r"(?:send|share|forward|tell|reply\s+with|batao?|बता(?:ओ|इए|एँ|एं)?|bhej(?:o|iye|ein)?|"
    r"भेज(?:ो|िए|ें)?|likh(?:o|iye)?)\w*\b[^.।!?]{0,30}?"
    r"(?:\bit\b|\bthem\b|\bthat\b|\bhere\b|code|कोड|use|उसे|unhe|उन्हें|wo(?:h)?\b|वो|वह|mujhe|मुझे)"
    r"|(?:\bit\b|\bthem\b|use|उसे|unhe|उन्हें|wo(?:h)?\b|वो|वह|code|कोड)[^.।!?]{0,25}?"
    r"(?:bhej|भेज|bata|बता|send|share|forward|yahan|यहाँ|is\s+(?:number|chat))",
    re.I)

# ---- new families (held-out v2 misses + external review) --------------------
_FAMILY_TROUBLE = _rx(["accident", "एक्सिडेंट", "दुर्घटना", "hospital",
                       "अस्पताल", "icu", "operation", "ऑपरेशन", "police case",
                       "पकड़ा गया", "pakda gaya", "जेल", "थाने", "custody",
                       "hirasat", "गिरफ्तार हो"])
_SEND_DIRECTIVE = _rx(["bhejo", "भेजो", "bhej do", "भेज दो", "bhejein", "भेजें",
                       "bhej", "भेज", "bhejna", "भेजना", "send", "transfer",
                       "gpay par", "phonepe par", "paytm par", "जमा कर"])
_NEW_NUMBER = _rx(["new number", "naya number", "नया नंबर", "number badal",
                   "phone broke", "phone toot", "फोन टूट", "phone kho",
                   "फोन खो", "sim kho", "yeh mera naya"])
_CHAIN_FWD = _rx(["forward this message", "forward karo", "forward karein",
                  "10 groups", "5 groups", "ग्रुप में भेज", "groups me bhejo",
                  "share to groups", "share with 10"])
_APK = re.compile(r"\b[\w-]{2,}\.apk\b|apk\s+(?:file|download|install)|"
                  r"download\s+(?:kar(?:ke|o)|करके)\s+install", re.I)

# ---- v5 families: reverse-refund and scan-to-receive (counterparty baits) ---
_ACCIDENT_SENT = re.compile(
    r"(?:accidentally|galti\s+se|गलती\s+से|by\s+mistake)[^.।!?]{0,45}"
    r"(?:refund|sent|transferr?ed|credited|bhej|भेज|chala\s+gaya|चला\s+गया)"
    r"|(?:refunded|sent|transferr?ed|bhej\s+diya)[^.।!?]{0,25}"
    r"(?:by\s+mistake|galti\s+se|गलती\s+से)", re.I)
_RETURN_ASK = re.compile(
    r"(?:\breturn\b|refund\s+(?:it|back)|wapas\s+(?:bhej|kar)|"
    r"वापस\s+(?:भेज|कर)|send\s+(?:it\s+)?back)", re.I)
_QR_SENT_TO_YOU = re.compile(
    r"(?:qr|क्यूआर)\s*(?:code)?[^.।!?]{0,30}(?:bhej\s+raha|भेज\s+रहा|bheja|भेजा|"
    r"sending|sent)|(?:bhej\s+raha|sending)[^.।!?]{0,15}(?:qr|क्यूआर)", re.I)
_SCAN_DIRECTIVE = re.compile(
    r"scan\s+kar|स्कैन\s+कर|\bscan\b[^.।!?]{0,20}(?:karo|karke|करो|करके)", re.I)
_MONEY_IN_CTX = re.compile(
    r"khareed|खरीद|\bbuy(?:ing)?\b|payment\s+(?:milega|aayega)|"
    r"paise\s+(?:milenge|aayenge)|पैसे\s+(?:मिलेंगे|आएँगे|आएंगे)|"
    r"advance\s+(?:de|deta|दे)", re.I)

_MAX_SPAN = 120


def _ev(evidence: list | None, kind: str, span: str, sentence: int | None = None,
        start: int | None = None, end: int | None = None):
    """Evidence record. start/end are PYTHON character offsets into the raw
    payload (the engine converts to UTF-16 code units at assembly — see
    engine/__init__). span text is capped; offsets are not."""
    if evidence is not None and len(evidence) < 24:
        evidence.append({"kind": kind, "span": span[:_MAX_SPAN],
                         "sentence": sentence, "start": start, "end": end})


def _first_span(patterns, text) -> str | None:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(0)
    return None


def _first_match(patterns, text):
    """First regex Match across a pattern list — offsets come from .start/.end.
    Works identically on negation-stripped text because the strip is
    length-preserving."""
    for p in patterns:
        m = p.search(text)
        if m:
            return m
    return None


def _all_matches(patterns, text, cap: int = 3):
    """Up to `cap` non-overlapping matches across a pattern list — repeated
    phrases each get their own evidence fragment."""
    out, taken = [], []
    for p in patterns:
        for m in p.finditer(text):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            out.append(m)
            taken.append((m.start(), m.end()))
            if len(out) >= cap:
                return out
    return out


def _sentences_with_pos(text: str) -> list[tuple[str, int]]:
    """(sentence, absolute start offset) pairs — the offset backbone."""
    out, pos = [], 0
    for m in _SENT_SPLIT.finditer(text):
        seg = text[pos:m.start()]
        if seg.strip():
            lead = len(seg) - len(seg.lstrip())
            out.append((seg.strip(), pos + lead))
        pos = m.end()
    seg = text[pos:]
    if seg.strip():
        lead = len(seg) - len(seg.lstrip())
        out.append((seg.strip(), pos + lead))
    return out


def detect(text: str, signals: list, evidence: list | None = None) -> list[str]:
    """Adds pattern signals; returns matched categories, strongest first.
    Evidence records carry exact Python-char offsets into `text` (the strip
    being length-preserving makes stripped-text offsets raw-text offsets)."""
    sent_pos = _sentences_with_pos(text)
    sentences = [s for s, _ in sent_pos]
    stripped_all = _strip_negated(text)  # same length as text — offsets shared
    stripped_sents = [stripped_all[p:p + len(s)] for s, p in sent_pos]

    # ---- directive evidence (per sentence, negation-scoped) ----
    cred_request_span = None
    cred_delivery = any(p.search(text) for p in _CRED_DELIVERY)
    delivered_m = _CODE_DELIVERED.search(text)
    code_delivered = bool(delivered_m)
    if delivered_m:  # factual context: where the referent was established
        _ev(evidence, "code_delivery_context", delivered_m.group(0),
            None, delivered_m.start(), delivered_m.end())
    for i, ((raw_s, s_off), st_s) in enumerate(zip(sent_pos, stripped_sents)):
        has_mention = any(p.search(raw_s) for p in _CRED_MENTION)
        # H16 cross-sentence referent: an earlier sentence delivered "the
        # code"; this one may demand it without naming it.
        referent_m = (_BARE_REF_REQ.search(st_s)
                      if code_delivered and not has_mention else None)
        if not has_mention and not referent_m:
            continue
        # H16 self-initiated flow: a first-person QUESTION about where/how *I*
        # enter my code is the user's own action — never a counterparty ask.
        if _SELF_QUERY.search(raw_s) and not _CHAT_DIRECTION.search(raw_s):
            _ev(evidence, "credential_self_query", raw_s, i,
                s_off, s_off + len(raw_s))
            continue
        m = referent_m or _CRED_REQ_A.search(st_s) or _CRED_REQ_B.search(st_s)
        if not m:
            continue
        # in-person platform flow: OTP told/shown to a present agent — exempt
        # unless the ask redirects to the requester's own chat/number, or the
        # "agent" is the CALLER asking for it (identity claim = counterparty).
        if _AGENT_CTX.search(raw_s) and not _CHAT_DIRECTION.search(raw_s) \
                and not _CALLER_CLAIM.search(raw_s):
            _ev(evidence, "credential_agent_flow", raw_s, i,
                s_off, s_off + len(raw_s))
            continue
        cred_request_span = m.group(0)
        _ev(evidence, "credential_request", text[s_off + m.start():s_off + m.end()],
            i, s_off + m.start(), s_off + m.end())
        break

    remote_m = _first_match(_REMOTE_ACCESS, text)
    if remote_m:
        _ev(evidence, "remote_access", remote_m.group(0), None,
            remote_m.start(), remote_m.end())

    bait_send_m = _first_match(_BAIT_SEND, stripped_all)
    bait_send_span = bait_send_m.group(0) if bait_send_m else None
    bait_get_m = _first_match(_BAIT_GET, text)
    bait_get_span = bait_get_m.group(0) if bait_get_m else None
    fee_pats = next(c for c in _CROSS if c[0] == "fee_demand")[6]
    fee_span = _first_span(fee_pats, stripped_all)
    collect_phrase_m = _COLLECT_PHRASE.search(text)
    approve_m = _APPROVE_WORD.search(stripped_all)
    collect_approve = bool(collect_phrase_m and approve_m)
    family_m = _first_match(_FAMILY_TROUBLE, text)
    family_trouble_span = family_m.group(0) if family_m else None
    newnum_m = _first_match(_NEW_NUMBER, text)
    new_number_span = newnum_m.group(0) if newnum_m else None
    chain_m = _first_match(_CHAIN_FWD, text)
    apk_m = _APK.search(text)
    send_dir_m = _first_match(_SEND_DIRECTIVE, stripped_all)

    directive_evidence = any((cred_request_span, bait_send_span, fee_span,
                              remote_m, collect_approve,
                              (family_trouble_span and send_dir_m),
                              (new_number_span and send_dir_m)))

    # ---- reported/educational framing: describing a scam ≠ receiving one ----
    # v5 regression bug: bare "ho gaya" matched SCAMMER claims too ("loan
    # अप्रूव हो गया") and suppressed them as victim self-reports. The
    # register is FIRST-PERSON completion only: an I-actor near the verb.
    _COMPLETED = re.compile(
        r"(?:maine|मैंने|\bi\b)\s?[^.।!?]{0,30}?"
        r"(?:kar\s+diya|कर\s+दिया|bhar\s+diya|भर\s+दिया|de\s+diya|दे\s+दिया|"
        r"bhej\s+diy[ae]|भेज\s+दिय[ेा]|paid|jama\s+kar\s+diya|जमा\s+कर\s+दिया)"
        r"|pay\s+kar\s+diya|paise\s+bhej\s+diye|पैसे\s+भेज\s+दिए", re.I)
    completed_self = bool(_COMPLETED.search(text)) and not directive_evidence
    aware_m = _AWARENESS.search(text)
    # H17: an impersonal news/advisory frame ("Police warn: fraudsters demand
    # a customs bond…") may quote the scam's own vocabulary — that quoted fee
    # is not a demand AT the reader. It suppresses only while nothing in the
    # text targets "you/aap"; the moment a second person appears, directive
    # evidence wins again (victim reports and forwarded scams keep flagging).
    news_m = _NEWS_FRAME.search(text)
    impersonal_news = bool(news_m) and not _SECOND_PERSON.search(text)
    reported = (bool(aware_m) or bool(news_m) or completed_self) and (
        not directive_evidence or impersonal_news)
    if reported:
        frame_m = aware_m or news_m or _COMPLETED.search(text)
        _ev(evidence, "reported_speech", frame_m.group(0), None,
            frame_m.start(), frame_m.end())
        signals.append(make_signal(
            "reported_or_educational", "deterministic", 0,
            "Reads as reporting/teaching about scams",
            "यह ठगी के बारे में बताना/सिखाना लगता है",
            "Scam vocabulary appears in an awareness/reporting frame with no demand aimed at you — not scored as a threat.",
            "ठगी के शब्द जागरूकता/जानकारी के संदर्भ में हैं, आपसे कोई माँग नहीं — इसे खतरा नहीं गिना गया।",
        ))
        return []

    has_ctx = any(p.search(text) for p in _CTX)
    matched: list[tuple[str, int, list]] = []
    for cat, (weight, strong, weak) in CATEGORIES.items():
        strong_ms = [p.search(text) for p in strong if p.search(text)]
        weak_ms = [p.search(text) for p in weak if p.search(text)]
        fires = bool(strong_ms) or (len(weak_ms) >= 2 and has_ctx)
        if fires:
            matched.append((cat, weight, strong_ms + weak_ms))
    matched.sort(key=lambda m: m[1], reverse=True)

    for cat, weight, hit_ms in matched:
        pretty = cat.replace("_", " ")
        # each matched phrase is its own fragment of the same finding
        for hm in hit_ms[:3]:
            _ev(evidence, f"category:{cat}", hm.group(0), None,
                hm.start(), hm.end())
        signals.append(make_signal(
            f"script_{cat}", "deterministic", weight,
            f"Known scam script: {pretty}", "जाना-पहचाना ठगी का तरीका",
            f"Wording matches the '{pretty}' scam script seen across India.",
            f"भाषा भारत भर में चल रहे '{pretty}' ठगी pattern से मिलती है।",
        ))

    for sid, weight, t_en, t_hi, d_en, d_hi, patterns in _CROSS:
        # demand-type cross signals respect negation scope; threat grammar
        # (coercion/secrecy/urgency/threat wording) matches raw text.
        target = stripped_all if sid == "fee_demand" else text
        cross_ms = _all_matches(patterns, target, cap=3)
        if cross_ms:
            for cm in cross_ms:  # repeated phrases each become a fragment
                _ev(evidence, sid, cm.group(0), None, cm.start(), cm.end())
            signals.append(make_signal(sid, "deterministic", weight, t_en, t_hi, d_en, d_hi))

    if cred_request_span or remote_m:
        signals.append(make_signal(
            "credential_request", "deterministic", 30,
            "Asks for OTP/PIN/access", "OTP/PIN/access माँगा जा रहा है",
            "No bank or official ever asks for OTP, PIN, CVV, passwords or screen access.",
            "कोई बैंक या अधिकारी कभी OTP, PIN, CVV, पासवर्ड या screen access नहीं माँगता।",
        ))
    elif cred_delivery:
        dm = _first_match(_CRED_DELIVERY, text)
        if dm:
            _ev(evidence, "credential_delivery", dm.group(0), None,
                dm.start(), dm.end())

    # advance-fee bait: a refund/prize you must SEND money to receive —
    # composite finding, TWO fragments (the bait and the demand)
    if bait_get_span and bait_send_span:
        _ev(evidence, "advance_fee", bait_get_m.group(0), None,
            bait_get_m.start(), bait_get_m.end())
        _ev(evidence, "advance_fee", bait_send_m.group(0), None,
            bait_send_m.start(), bait_send_m.end())
        signals.append(make_signal(
            "advance_fee_refund", "deterministic", 30,
            "Pay-to-receive 'refund/prize'", "'Refund/इनाम' के लिए पहले पैसे",
            "Real refunds and prizes never require you to send money first.",
            "असली refund या इनाम के लिए कभी पहले पैसे नहीं भेजने पड़ते।",
        ))

    # OLX/army mechanic: "approve my collect request to RECEIVE money" —
    # composite finding, two fragments
    if collect_approve:
        _ev(evidence, "collect_approve", collect_phrase_m.group(0), None,
            collect_phrase_m.start(), collect_phrase_m.end())
        _ev(evidence, "collect_approve", approve_m.group(0), None,
            approve_m.start(), approve_m.end())
        signals.append(make_signal(
            "collect_to_receive_bait", "deterministic", 25,
            "Asked to APPROVE to receive money", "पैसे 'पाने' के लिए approve करने को कहा",
            "Approving a collect request always sends money OUT — receiving needs no approval.",
            "Collect request approve करने से पैसे कटते हैं — पैसे पाने के लिए कभी approve नहीं करना पड़ता।",
        ))

    # extortion: threatened disclosure/harm tied to a MONEY demand (H16).
    # High-precision relation (threat-set + demand-verb + money context), so a
    # single hit is danger-grade — blackmail is unambiguous. Without the money
    # context ("recorded your presentation, transfer the file") it never fires.
    disclosure_m = _first_match(_DISCLOSURE_THREAT, text)
    disclosure_span = disclosure_m.group(0) if disclosure_m else None
    money_ctx = re.search(r"₹|\brs\.?\s?\d|rupee|हज़ार|hazaa?r|lakh|लाख|\b\d{3,7}\b",
                          text, re.I)
    if disclosure_span and money_ctx and (
            bait_send_span or _first_span(_DEMAND_VERBS, stripped_all)):
        _ev(evidence, "extortion_disclosure", disclosure_span, None,
            disclosure_m.start(), disclosure_m.end())
        signals.append(make_signal(
            "extortion_disclosure", "deterministic", 60,
            "Blackmail: pay or be exposed", "Blackmail: पैसे दो वरना बदनाम",
            "Threatening to leak/expose something unless you pay is extortion — a crime by THEM, whatever they claim to have. Do not pay; save evidence; report on 1930/cybercrime.gov.in.",
            "कुछ leak/viral करने की धमकी देकर पैसे माँगना ब्लैकमेल है — जुर्म UNKA है, चाहे उनके पास कुछ भी हो। पैसे न दें; सबूत रखें; 1930 पर रिपोर्ट करें।",
        ))
    elif disclosure_span:
        # threat held over the user but no demand stated YET — this must reach
        # the threat_no_ask clarification, never a green card
        _ev(evidence, "threat_framing", disclosure_span, None,
            disclosure_m.start(), disclosure_m.end())
        signals.append(make_signal(
            "threat_framing", "deterministic", 15,
            "Threat of exposure/harm", "बदनामी/नुकसान की धमकी",
            "Something is being held over you — watch for the demand that follows.",
            "आप पर कुछ थोपा जा रहा है — आगे आने वाली माँग ही असली मक़सद है।",
        ))

    # family emergency + send-money (held-out v2 misses s04/s30)
    if family_trouble_span and send_dir_m:
        _ev(evidence, "family_emergency", family_trouble_span, None,
            family_m.start(), family_m.end())
        signals.append(make_signal(
            "family_emergency_pressure", "deterministic", 30,
            "Emergency + send money NOW", "इमरजेंसी बताकर तुरंत पैसे",
            "'Relative in hospital/custody, send money now' is a top phone scam — verify by calling the person on their KNOWN number first.",
            "'अपना अस्पताल/थाने में है, अभी पैसे भेजो' सबसे आम ठगी है — पहले उनके जाने-पहचाने नंबर पर खुद call करके पूछें।",
        ))

    # "new number" identity claim + money ask: never auto-confirm as fraud —
    # this signal asks for verification, not conviction (weight lands in
    # suspicious, and the advice is to call the OLD stored number).
    if new_number_span and send_dir_m:
        _ev(evidence, "new_number_request", new_number_span, None,
            newnum_m.start(), newnum_m.end())
        signals.append(make_signal(
            "unverified_family_request", "deterministic", 30,
            "Unverified 'new number' asking for money", "बिना पहचान पक्की किए पैसे की माँग",
            "A new number claiming to be family and asking for money must be verified — call them on the number you ALREADY have before sending anything.",
            "नया नंबर खुद को अपना बताकर पैसे माँगे तो पहले उनके पुराने नंबर पर call करके पक्का करें — उसके बिना कुछ न भेजें।",
        ))

    # v5 family: "we sent it by MISTAKE — return it" (reverse-refund play:
    # the money usually never arrived, or is stolen money laundered through you)
    acc_m = _ACCIDENT_SENT.search(stripped_all)
    ret_m = _RETURN_ASK.search(stripped_all) if acc_m else None
    if acc_m and ret_m:
        _ev(evidence, "accidental_transfer", acc_m.group(0), None,
            acc_m.start(), acc_m.end())
        _ev(evidence, "accidental_transfer", ret_m.group(0), None,
            ret_m.start(), ret_m.end())
        signals.append(make_signal(
            "accidental_transfer_bait", "deterministic", 35,
            "'Sent by mistake — return it'", "'गलती से भेज दिए — वापस करो'",
            "Check your OWN bank statement first: the 'mistaken transfer' usually never arrived — or is stolen money you'd be laundering back.",
            "पहले अपनी bank statement खुद देखें — 'गलती से आए' पैसे अक्सर आए ही नहीं होते, या चोरी के पैसे होते हैं।",
        ))

    # v5 family: buyer "sending you a QR — scan to GET paid". Receiving money
    # never requires scanning or approving anything.
    qr_m = _QR_SENT_TO_YOU.search(text)
    scan_m = _SCAN_DIRECTIVE.search(stripped_all) if qr_m else None
    if qr_m and scan_m and _MONEY_IN_CTX.search(text):
        _ev(evidence, "scan_to_receive", qr_m.group(0), None,
            qr_m.start(), qr_m.end())
        _ev(evidence, "scan_to_receive", scan_m.group(0), None,
            scan_m.start(), scan_m.end())
        signals.append(make_signal(
            "scan_to_receive_bait", "deterministic", 35,
            "'Scan to RECEIVE money'", "'पैसे पाने के लिए scan करो'",
            "Receiving money never requires scanning a QR or approving anything — a buyer's 'payment QR' moves money OUT of your account.",
            "पैसे PANE के लिए कभी QR scan या approve नहीं करना पड़ता — 'buyer' का भेजा QR आपके खाते से पैसे काटता है।",
        ))

    if chain_m:
        _ev(evidence, "chain_forward", chain_m.group(0), None,
            chain_m.start(), chain_m.end())
        signals.append(make_signal(
            "chain_forward_bait", "deterministic", 25,
            "Forward-to-groups chain bait", "ग्रुप-में-forward वाला चारा",
            "Legitimate services never unlock features for forwarding messages to groups.",
            "कोई असली service 'groups में forward करो' से feature नहीं देती।",
        ))

    if apk_m:
        _ev(evidence, "apk_file", apk_m.group(0), None,
            apk_m.start(), apk_m.end())
        signals.append(make_signal(
            "apk_sideload", "deterministic", 30,
            "Asks to install an app file (.apk)", "सीधे app file (.apk) install कराना",
            "Apps sent as files bypass Play Store checks — screen-reading malware spreads this way. Install only from the official store.",
            "File बनाकर भेजी गई app Play Store की जाँच से बचती है — ऐसे ही screen पढ़ने वाले malware आते हैं। App सिर्फ़ official store से लें।",
        ))

    return [m[0] for m in matched]

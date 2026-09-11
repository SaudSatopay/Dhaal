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
    for p in _NEG_STRIP:
        sentence = p.sub(" ", sentence)
    return sentence


# ---- reported/educational framing (suppresses convictions, never directives)
_AWARENESS = re.compile(
    r"awareness|workshop|seminar|lecture|classroom|professor|teacher|training|"
    r"advisory|warn(?:ed|ing)\s+(?:us|me|people|about)|beware\s+of|savdhan\s+rahe|"
    r"news|article|akhbar|अख़बार|अखबार|जागरूकता|सिखाया|पढ़ाया|समझाया|\bpadhaya\b|"
    r"\bsikha(?:ya)?\b|cyber\s+safety", re.I)


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
        "lottery", "लॉटरी", "lucky draw", "jackpot", "kbc", "crorepati",
        "lakh jeet", "jeet gaye",
    ]), _rx([
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
        re.compile(r"\bnumber\b[^.।!?]{0,25}(?:deactivat|disconnect|band|बंद)", re.I),
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
    ]), _rx([
        "रिफंड", "refund",
    ])),
    "job_scam": (30, _rx([
        "work from home job", "ghar baithe kamaye", "घर बैठे कमा", "part time job",
        "earn rs", "earn ₹", "earn daily", "daily earning", "roz kamao",
        "रोज़ कमा", "liking videos", "like videos", "telegram task",
        "limited seats", "instagram follow",
    ]), _rx([
        "youtube video", "registration",
    ])),
    "loan_fee": (30, _rx([
        "loan approve", "loan approved", "pre-approved loan",
        "pre approved loan", "instant loan", "लोन approve", "लोन मंजूर",
        "आधार पर लोन", "बिना गारंटी लोन", "file charge", "loan sanction",
    ]), []),
}

# Money/pressure context that lets weak tokens combine into a category hit.
_CTX = _rx([
    "₹", "rs.", "rupees", "rupay", "paise", "fee", "फीस", "फ़ीस", "bhejo",
    "भेजो", "send money", "pay", "payment", "upi", "account", "खाते", "खाता",
    "transfer", "तुरंत", "turant", "immediately", "urgent", "अभी", "warna",
    "वरना", "किसी को मत", "tell no one", "verification",
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
     _rx(["processing fee", "verification fee", "वेरिफिकेशन फीस", "फीस भेज",
          "registration fee", "token amount", "security deposit",
          "शुल्क भेज", "फीस जमा", "file charge"])),
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
          "dekh lenge", "छोड़ूँगा नहीं", "chhodunga nahi"])),
]

# ---- credentials: request vs delivery vs mention (per-sentence) -------------
_CRED_MENTION = _rx(["otp", "pin", "cvv", "password", "पासवर्ड", "mpin",
                     "one time password", "one-time code", "one time code",
                     "verification code", "card number", "expiry date"])
_CRED_DELIVERY = _rx(["is your otp", "is your one time password", "otp for",
                      "one time password for", "otp is", "code is"])
# directive verb → credential, or credential → directive/direction, in ONE
# sentence (negation already stripped). "code" alone is too broad — only
# qualified code phrases count.
_CRED_TOKEN = (r"(?:otp|ओटीपी|one[\s-]?time\s+(?:password|code)|verification\s+code|"
               r"security\s+code|sms\s+code|\d{1,2}[\s-]?digit\s+code|pin|mpin|"
               r"upi\s+pin|cvv|password|पासवर्ड|पिन)")
_CRED_REQ_A = re.compile(
    r"(?:send|share|forward|tell|give|type|enter|read\s+out|confirm|batao?|"
    r"बता(?:ओ|इए|एँ|एं|ये|यें)?|bhej(?:o|iye|ein|en)?|भेज(?:ो|िए|ें|े)?|"
    r"likh(?:o|iye)?|daal(?:o|iye)?|डाल(?:ो|िए|ें)?|dij(?:iye|iy?e)|दीजिए|"
    r"de\s+do|दे\s+दो)\w*\b[^.।!?]{0,50}?" + _CRED_TOKEN,
    re.I)
_CRED_REQ_B = re.compile(
    _CRED_TOKEN + r"[^.।!?]{0,40}?(?:bhej|भेज|bata|बता|share|send|forward|"
    r"dij(?:iye|e)|दीजिए|दे\s+दो|मुझे|mujhe|यहाँ|yahan|"
    r"is\s+(?:number|chat)|इस\s+(?:नंबर|चैट)|हमें|humein)",
    re.I)
# telling/showing an OTP to a physically present platform agent is a real flow
_AGENT_CTX = re.compile(
    r"driver|rider|delivery\s*(?:boy|agent|partner|executive|associate)|courier\s*(?:boy|wala)|"
    r"डिलीवरी|ड्राइवर|राइडर|कूरियर", re.I)
_CHAT_DIRECTION = re.compile(
    r"मुझे|mujhe|to\s+me|this\s+chat|is\s+(?:number|chat)|इस\s+(?:नंबर|चैट)|"
    r"हमें|humein|whatsapp\s+kar|call\s+par|फोन\s+पर\s+बता", re.I)
# remote-access tooling = credential-grade access request
_REMOTE_ACCESS = _rx(["anydesk", "teamviewer", "quick support", "quicksupport",
                      "screen share", "screen sharing", "remote access"])

# Refund/prize that requires SENDING money first — the advance-fee mechanic.
_BAIT_GET = _rx(["refund", "रिफंड", "cashback", "कैशबैक", "prize", "इनाम",
                 "lottery", "claim your", "claim karne", "वापसी", "winner",
                 "to receive your", "receive karne"])
_BAIT_SEND = _rx(["paise bhejo", "पैसे भेजो", "paise bhej", "पैसे भेज",
                  "bhejo", "भेजो", "bhejein", "भेजें", "bheje", "send money",
                  "pay first", "pehle pay", "pehle bhejo", "पहले भेजो",
                  "pehle bhejein", "transfer karo", "transfer kare",
                  "pay karo", "send rs", "send ₹", "pay delivery charge",
                  "delivery charge", "shipping charge"])

_COLLECT_PHRASE = re.compile(r"collect request|collect रिक्वेस्ट", re.I)
_APPROVE_WORD = re.compile(r"\bapprove|\baccept\b|स्वीकार|मंज़ूर", re.I)

# ---- new families (held-out v2 misses + external review) --------------------
_FAMILY_TROUBLE = _rx(["accident", "एक्सिडेंट", "दुर्घटना", "hospital",
                       "अस्पताल", "icu", "operation", "ऑपरेशन", "police case",
                       "पकड़ा गया", "pakda gaya", "जेल", "थाने", "custody",
                       "hirasat", "गिरफ्तार हो"])
_SEND_DIRECTIVE = _rx(["bhejo", "भेजो", "bhej do", "भेज दो", "bhejein", "भेजें",
                       "send", "transfer", "gpay par", "phonepe par", "paytm par"])
_NEW_NUMBER = _rx(["new number", "naya number", "नया नंबर", "number badal",
                   "phone broke", "phone toot", "फोन टूट", "phone kho",
                   "फोन खो", "sim kho", "yeh mera naya"])
_CHAIN_FWD = _rx(["forward this message", "forward karo", "forward karein",
                  "10 groups", "5 groups", "ग्रुप में भेज", "groups me bhejo",
                  "share to groups", "share with 10"])
_APK = re.compile(r"\b[\w-]{2,}\.apk\b|apk\s+(?:file|download|install)|"
                  r"download\s+(?:kar(?:ke|o)|करके)\s+install", re.I)

_MAX_SPAN = 120


def _ev(evidence: list | None, kind: str, span: str, sentence: int | None = None):
    if evidence is not None and len(evidence) < 24:
        evidence.append({"kind": kind, "span": span[:_MAX_SPAN], "sentence": sentence})


def _first_span(patterns, text) -> str | None:
    for p in patterns:
        m = p.search(text)
        if m:
            return m.group(0)
    return None


def detect(text: str, signals: list, evidence: list | None = None) -> list[str]:
    """Adds pattern signals; returns matched categories, strongest first.
    Appends evidence spans (kind + exact matched text) to `evidence`."""
    sentences = _sentences(text)
    stripped_sents = [_strip_negated(s) for s in sentences]
    stripped_all = " । ".join(stripped_sents)

    # ---- directive evidence (per sentence, negation-scoped) ----
    cred_request_span = None
    cred_delivery = any(p.search(text) for p in _CRED_DELIVERY)
    for i, (raw_s, st_s) in enumerate(zip(sentences, stripped_sents)):
        has_mention = any(p.search(raw_s) for p in _CRED_MENTION)
        if not has_mention:
            continue
        m = _CRED_REQ_A.search(st_s) or _CRED_REQ_B.search(st_s)
        if not m:
            continue
        # in-person platform flow: OTP told/shown to a present agent — exempt
        # unless the ask redirects to the requester's own chat/number.
        if _AGENT_CTX.search(raw_s) and not _CHAT_DIRECTION.search(raw_s):
            _ev(evidence, "credential_agent_flow", raw_s, i)
            continue
        cred_request_span = m.group(0)
        _ev(evidence, "credential_request", raw_s, i)
        break

    remote_span = _first_span(_REMOTE_ACCESS, text)
    if remote_span:
        _ev(evidence, "remote_access", remote_span)

    bait_send_span = _first_span(_BAIT_SEND, stripped_all)
    bait_get_span = _first_span(_BAIT_GET, text)
    fee_pats = next(c for c in _CROSS if c[0] == "fee_demand")[6]
    fee_span = _first_span(fee_pats, stripped_all)
    collect_approve = bool(_COLLECT_PHRASE.search(text) and _APPROVE_WORD.search(stripped_all))
    family_trouble_span = _first_span(_FAMILY_TROUBLE, text)
    new_number_span = _first_span(_NEW_NUMBER, text)
    chain_span = _first_span(_CHAIN_FWD, text)
    apk_m = _APK.search(text)

    directive_evidence = any((cred_request_span, bait_send_span, fee_span,
                              remote_span, collect_approve,
                              (family_trouble_span and _first_span(_SEND_DIRECTIVE, stripped_all)),
                              (new_number_span and _first_span(_SEND_DIRECTIVE, stripped_all))))

    # ---- reported/educational framing: describing a scam ≠ receiving one ----
    aware_m = _AWARENESS.search(text)
    reported = bool(aware_m) and not directive_evidence
    if reported:
        _ev(evidence, "reported_speech", aware_m.group(0))
        signals.append(make_signal(
            "reported_or_educational", "deterministic", 0,
            "Reads as reporting/teaching about scams",
            "यह ठगी के बारे में बताना/सिखाना लगता है",
            "Scam vocabulary appears in an awareness/reporting frame with no demand aimed at you — not scored as a threat.",
            "ठगी के शब्द जागरूकता/जानकारी के संदर्भ में हैं, आपसे कोई माँग नहीं — इसे खतरा नहीं गिना गया।",
        ))
        return []

    has_ctx = any(p.search(text) for p in _CTX)
    matched: list[tuple[str, int, list[str]]] = []
    for cat, (weight, strong, weak) in CATEGORIES.items():
        strong_hits = [p.search(text).group(0) for p in strong if p.search(text)]
        weak_hits = [p.search(text).group(0) for p in weak if p.search(text)]
        fires = bool(strong_hits) or (len(weak_hits) >= 2 and has_ctx)
        if fires:
            matched.append((cat, weight, strong_hits + weak_hits))
    matched.sort(key=lambda m: m[1], reverse=True)

    for cat, weight, hits in matched:
        pretty = cat.replace("_", " ")
        _ev(evidence, f"category:{cat}", " · ".join(hits[:3]))
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
        span = _first_span(patterns, target)
        if span:
            _ev(evidence, sid, span)
            signals.append(make_signal(sid, "deterministic", weight, t_en, t_hi, d_en, d_hi))

    if cred_request_span or remote_span:
        signals.append(make_signal(
            "credential_request", "deterministic", 30,
            "Asks for OTP/PIN/access", "OTP/PIN/access माँगा जा रहा है",
            "No bank or official ever asks for OTP, PIN, CVV, passwords or screen access.",
            "कोई बैंक या अधिकारी कभी OTP, PIN, CVV, पासवर्ड या screen access नहीं माँगता।",
        ))
    elif cred_delivery:
        _ev(evidence, "credential_delivery", _first_span(_CRED_DELIVERY, text) or "")

    # advance-fee bait: a refund/prize you must SEND money to receive
    if bait_get_span and bait_send_span:
        _ev(evidence, "advance_fee", f"{bait_get_span} + {bait_send_span}")
        signals.append(make_signal(
            "advance_fee_refund", "deterministic", 30,
            "Pay-to-receive 'refund/prize'", "'Refund/इनाम' के लिए पहले पैसे",
            "Real refunds and prizes never require you to send money first.",
            "असली refund या इनाम के लिए कभी पहले पैसे नहीं भेजने पड़ते।",
        ))

    # OLX/army mechanic: "approve my collect request to RECEIVE money"
    if collect_approve:
        _ev(evidence, "collect_approve", "collect request + approve")
        signals.append(make_signal(
            "collect_to_receive_bait", "deterministic", 25,
            "Asked to APPROVE to receive money", "पैसे 'पाने' के लिए approve करने को कहा",
            "Approving a collect request always sends money OUT — receiving needs no approval.",
            "Collect request approve करने से पैसे कटते हैं — पैसे पाने के लिए कभी approve नहीं करना पड़ता।",
        ))

    # family emergency + send-money (held-out v2 misses s04/s30)
    if family_trouble_span and _first_span(_SEND_DIRECTIVE, stripped_all):
        _ev(evidence, "family_emergency", family_trouble_span)
        signals.append(make_signal(
            "family_emergency_pressure", "deterministic", 30,
            "Emergency + send money NOW", "इमरजेंसी बताकर तुरंत पैसे",
            "'Relative in hospital/custody, send money now' is a top phone scam — verify by calling the person on their KNOWN number first.",
            "'अपना अस्पताल/थाने में है, अभी पैसे भेजो' सबसे आम ठगी है — पहले उनके जाने-पहचाने नंबर पर खुद call करके पूछें।",
        ))

    # "new number" identity claim + money ask: never auto-confirm as fraud —
    # this signal asks for verification, not conviction (weight lands in
    # suspicious, and the advice is to call the OLD stored number).
    if new_number_span and _first_span(_SEND_DIRECTIVE, stripped_all):
        _ev(evidence, "new_number_request", new_number_span)
        signals.append(make_signal(
            "unverified_family_request", "deterministic", 30,
            "Unverified 'new number' asking for money", "बिना पहचान पक्की किए पैसे की माँग",
            "A new number claiming to be family and asking for money must be verified — call them on the number you ALREADY have before sending anything.",
            "नया नंबर खुद को अपना बताकर पैसे माँगे तो पहले उनके पुराने नंबर पर call करके पक्का करें — उसके बिना कुछ न भेजें।",
        ))

    if chain_span:
        _ev(evidence, "chain_forward", chain_span)
        signals.append(make_signal(
            "chain_forward_bait", "deterministic", 25,
            "Forward-to-groups chain bait", "ग्रुप-में-forward वाला चारा",
            "Legitimate services never unlock features for forwarding messages to groups.",
            "कोई असली service 'groups में forward करो' से feature नहीं देती।",
        ))

    if apk_m:
        _ev(evidence, "apk_file", apk_m.group(0))
        signals.append(make_signal(
            "apk_sideload", "deterministic", 30,
            "Asks to install an app file (.apk)", "सीधे app file (.apk) install कराना",
            "Apps sent as files bypass Play Store checks — screen-reading malware spreads this way. Install only from the official store.",
            "File बनाकर भेजी गई app Play Store की जाँच से बचती है — ऐसे ही screen पढ़ने वाले malware आते हैं। App सिर्फ़ official store से लें।",
        ))

    return [m[0] for m in matched]

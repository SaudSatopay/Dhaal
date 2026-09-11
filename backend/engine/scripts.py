"""Social-engineering script detection — bilingual (Devanagari + Hinglish + English).

Single latin words are word-boundary regexes ('army' must not fire inside
'harmony'); Devanagari and multi-word phrases match as substrings. The legit
bank-SMS fixture (beat 3) is the false-positive control: nothing here may
match transactional language like 'credited', 'ref', 'A/c', 'Avl Bal'.
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


# H12 (external review): single ambient words must not convict. Each category
# has STRONG patterns (unambiguous scam grammar — fire alone) and WEAK tokens
# (ambient words like parcel/police/army — fire only when ≥2 co-occur AND the
# text carries money/pressure context). "Your parcel will be delivered
# tomorrow" and "the police station is next to the army canteen" stay clean.
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
    ]), []),
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
        "work from home", "ghar baithe", "घर बैठे", "part time job",
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
          "24 घंटे", "24 hours", "24 hour", "2 घंटे", "last warning",
          "अंतिम चेतावनी", "final notice", "जल्दी करें"])),
    # credential_request lives outside this table — it needs delivery-vs-request
    # context (H9 sweep miss #1), handled in detect() below.
    ("secrecy_pressure", 20, "Told to keep it secret", "छिपाने का दबाव",
     "'Tell no one' is how scammers cut you off from help.",
     "'किसी को मत बताओ' कहकर ठग आपको मदद से काटते हैं।",
     _rx(["किसी को मत", "किसी को न बता", "बताइए मत", "बताना मत",
          "tell no one", "don't tell", "do not tell", "confidential",
          "गोपनीय", "किसी से साझा न"])),
    ("fee_demand", 20, "Upfront fee demanded", "पहले फीस माँगी जा रही है",
     "Prizes, refunds and jobs that need a fee first are scams.",
     "जहाँ इनाम/refund से पहले फीस माँगे, वह ठगी है।",
     _rx(["processing fee", "verification fee", "वेरिफिकेशन फीस", "फीस भेज",
          "registration fee", "token amount", "security deposit",
          "शुल्क भेज", "फीस जमा"])),
    # Victim-voiced coercion — judges type DESCRIPTIONS of the threat, not the
    # scammer's script ("I was told to send money or I'd be arrested"). H11 miss.
    ("coercion_extortion", 30, "Money demanded under threat", "धमकी देकर पैसे माँगे जा रहे हैं",
     "Anyone conditioning your safety on a payment is running a scam — real authorities never do.",
     "जो 'पैसे भेजो वरना…' कहे वह ठग है — असली अधिकारी कभी ऐसा नहीं करते।",
     _rx(["if i don't send", "if i dont send", "if i don't pay", "if i dont pay",
          "if i wouldn't send", "if i wouldnt send", "wouldn't send them money",
          "send them money or", "send money or", "pay or else", "or else",
          "told me to send money", "told to send money", "told to pay",
          "asking me to pay", "asking me for money", "demanding money",
          "threaten", "threatened", "धमकी", "वरना", "warna", "नहीं भेजे तो",
          "नहीं भेजा तो", "नहीं दिए तो", "पैसे माँग रह", "paise maang",
          "मजबूर कर", "डरा कर पैसे", "डरा रहे", "छुड़ाने के लिए",
          "chhudane ke liye", "bachane ke liye paise", "बचाने के लिए पैसे"])),
    ("threat_framing", 15, "Threat of penalty/action", "डराने-धमकाने की भाषा",
     "Fear of fines, arrest or disconnection is the pressure lever.",
     "जुर्माना, गिरफ़्तारी या कटौती का डर दिखाना ही इनका हथियार है।",
     _rx(["legal action", "कानूनी कार्रवाई", "जुर्माना", "penalty",
          "case दर्ज", "blacklist"])),
]


# A legit OTP *delivery* ("123456 is your OTP… do not share") must never flag —
# judges paste these (H9 sweep). A *request* ("send me your OTP") always must,
# even when the scammer appends "do not share with anyone ELSE" (H12 bypass:
# request patterns beat delivery patterns; "do not share" alone suppresses
# nothing anymore).
_CRED_WORDS = _rx(["otp", "pin", "cvv", "password", "पासवर्ड", "mpin", "upi pin",
                   "card number", "atm card", "expiry date"])
_CRED_DELIVERY = _rx(["is your otp", "is your one time password", "otp for",
                      "one time password for", "never share", "do not share",
                      "don't share", "na batayen", "मत बताएं", "न बताएं",
                      "साझा न करें", "mat batao", "मत बता"])
# negated "requests" are awareness lines, not requests — strip before matching
_CRED_NEG = [re.compile(p, re.I) for p in (
    r"(never|do not|don'?t)\s+(share|tell|give|enter)[^.।]{0,40}(otp|pin|cvv|password)",
    r"(otp|pin|cvv|password)[^.।]{0,30}(kisi ko na|किसी को न|mat batao|मत बता|na batayen|न बताएं|साझा न करें)",
)]
_CRED_REQUEST = _rx(["send me your otp", "send your otp", "send the otp",
                     "otp bhejo", "otp भेजो", "otp batao", "otp बताओ",
                     "otp बता", "अपना otp", "apna otp", "share your otp",
                     "otp share karo", "enter your otp", "otp send karo",
                     "give me your otp", "tell me your otp", "otp dijiye",
                     "otp दीजिए", "your pin", "pin batao", "pin bhejo",
                     "अपना pin", "cvv batao", "read out the otp",
                     "confirm the otp", "otp confirm"])

# Refund/prize that requires SENDING money first (H12: "refund ke liye paise
# bhejo" scored only 15) — the advance-fee mechanic in one signal.
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


def detect(text: str, signals: list) -> list[str]:
    """Adds pattern signals; returns matched categories, strongest first."""
    has_ctx = any(p.search(text) for p in _CTX)
    matched: list[tuple[str, int, list[str]]] = []
    for cat, (weight, strong, weak) in CATEGORIES.items():
        strong_hits = [p.pattern for p in strong if p.search(text)]
        weak_hits = [p.pattern for p in weak if p.search(text)]
        fires = bool(strong_hits) or (len(weak_hits) >= 2 and has_ctx)
        if fires:
            matched.append((cat, weight, strong_hits + weak_hits))
    matched.sort(key=lambda m: m[1], reverse=True)

    for cat, weight, _hits in matched:
        pretty = cat.replace("_", " ")
        signals.append(make_signal(
            f"script_{cat}", "deterministic", weight,
            f"Known scam script: {pretty}", "जाना-पहचाना ठगी का तरीका",
            f"Wording matches the '{pretty}' scam script seen across India.",
            f"भाषा भारत भर में चल रहे '{pretty}' ठगी pattern से मिलती है।",
        ))

    for sid, weight, t_en, t_hi, d_en, d_hi, patterns in _CROSS:
        if any(p.search(text) for p in patterns):
            signals.append(make_signal(sid, "deterministic", weight, t_en, t_hi, d_en, d_hi))

    if any(p.search(text) for p in _CRED_WORDS):
        stripped = text
        for p in _CRED_NEG:
            stripped = p.sub(" ", stripped)
        is_request = any(p.search(stripped) for p in _CRED_REQUEST)
        is_delivery = any(p.search(text) for p in _CRED_DELIVERY)
        if is_request or not is_delivery:
            signals.append(make_signal(
                "credential_request", "deterministic", 30,
                "Asks for OTP/PIN", "OTP/PIN माँगा जा रहा है",
                "No bank or official ever asks for OTP, PIN, CVV or passwords.",
                "कोई बैंक या अधिकारी कभी OTP, PIN, CVV या पासवर्ड नहीं माँगता।",
            ))

    # advance-fee bait: a refund/prize you must SEND money to receive
    if any(p.search(text) for p in _BAIT_GET) and any(p.search(text) for p in _BAIT_SEND):
        signals.append(make_signal(
            "advance_fee_refund", "deterministic", 30,
            "Pay-to-receive 'refund/prize'", "'Refund/इनाम' के लिए पहले पैसे",
            "Real refunds and prizes never require you to send money first.",
            "असली refund या इनाम के लिए कभी पहले पैसे नहीं भेजने पड़ते।",
        ))

    # OLX/army mechanic: "approve my collect request to RECEIVE money"
    if _COLLECT_PHRASE.search(text) and _APPROVE_WORD.search(text):
        signals.append(make_signal(
            "collect_to_receive_bait", "deterministic", 25,
            "Asked to APPROVE to receive money", "पैसे 'पाने' के लिए approve करने को कहा",
            "Approving a collect request always sends money OUT — receiving needs no approval.",
            "Collect request approve करने से पैसे कटते हैं — पैसे पाने के लिए कभी approve नहीं करना पड़ता।",
        ))

    return [m[0] for m in matched]

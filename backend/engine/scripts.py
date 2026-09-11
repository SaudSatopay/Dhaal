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


CATEGORIES: dict[str, tuple[int, list]] = {
    "digital_arrest": (35, _rx([
        "digital arrest", "digitally arrest", "digitally arrested", "गिरफ",
        "arrest", "arrested", "cyber crime", "साइबर", "cbi", "jail", "जेल",
        "narcotics", "money laundering", "parcel", "पार्सल", "courier pakda",
        "customs", "पुलिस", "police", "कोर्ट", "court warrant", "ed notice",
    ])),
    "lottery": (30, _rx([
        "lottery", "लॉटरी", "lucky draw", "jackpot", "prize", "इनाम", "जीते",
        "jeeta", "jeet gaye", "winner", "kbc", "crorepati", "lakh jeet",
    ])),
    "kyc_expiry": (25, _rx([
        "kyc", "केवाईसी", "खाता बंद", "khata band", "account block",
        "account suspend", "खाता निलंबित", "pan update", "पैन अपडेट",
        "आधार अपडेट", "reactivate",
    ])),
    "electricity": (25, _rx([
        "बिजली", "electricity", "bijli", "power cut", "disconnect",
        "बिल बकाया", "bill pending", "meter update", "बत्ती काट",
    ])),
    "olx_army": (30, _rx([
        "army", "आर्मी", "crpf", "bsf", "fauji", "olx", "canteen",
        "advance payment", "एडवांस",
    ])),
    "customer_care": (25, _rx([
        "customer care", "कस्टमर केयर", "helpline number", "toll free",
        "refund process", "रिफंड", "complaint number", "care number",
    ])),
    "job_scam": (30, _rx([
        "work from home", "ghar baithe", "घर बैठे", "part time job",
        "earn rs", "earn ₹", "earn daily", "daily earning", "roz kamao",
        "रोज़ कमा", "liking videos", "like videos", "youtube video",
        "telegram task", "limited seats", "instagram follow",
    ])),
    "loan_fee": (30, _rx([
        "loan approve", "loan approved", "pre-approved loan",
        "pre approved loan", "instant loan", "लोन approve", "लोन मंजूर",
        "आधार पर लोन", "बिना गारंटी लोन", "file charge", "loan sanction",
    ])),
}

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
          "मजबूर कर", "डरा कर पैसे", "डरा रहे"])),
    ("threat_framing", 15, "Threat of penalty/action", "डराने-धमकाने की भाषा",
     "Fear of fines, arrest or disconnection is the pressure lever.",
     "जुर्माना, गिरफ़्तारी या कटौती का डर दिखाना ही इनका हथियार है।",
     _rx(["legal action", "कानूनी कार्रवाई", "जुर्माना", "penalty",
          "case दर्ज", "blacklist"])),
]


# A legit OTP *delivery* ("123456 is your OTP… do not share") must never flag —
# judges paste these (H9 sweep). A *request* ("apna OTP batao") always must.
_CRED_WORDS = _rx(["otp", "pin", "cvv", "password", "पासवर्ड", "mpin", "upi pin",
                   "card number", "atm card", "expiry date"])
_CRED_DELIVERY = _rx(["is your otp", "is your one time password", "otp for",
                      "one time password for", "do not share", "don't share",
                      "never share", "na batayen", "मत बताएं", "न बताएं",
                      "साझा न करें", "share न करें", "se share na kare"])

_COLLECT_PHRASE = re.compile(r"collect request|collect रिक्वेस्ट", re.I)
_APPROVE_WORD = re.compile(r"\bapprove|\baccept\b|स्वीकार|मंज़ूर", re.I)


def detect(text: str, signals: list) -> list[str]:
    """Adds pattern signals; returns matched categories, strongest first."""
    matched: list[tuple[str, int, list[str]]] = []
    for cat, (weight, patterns) in CATEGORIES.items():
        hits = [p.pattern for p in patterns if p.search(text)]
        if hits:
            matched.append((cat, weight, hits))
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

    if any(p.search(text) for p in _CRED_WORDS) \
            and not any(p.search(text) for p in _CRED_DELIVERY):
        signals.append(make_signal(
            "credential_request", "deterministic", 30,
            "Asks for OTP/PIN", "OTP/PIN माँगा जा रहा है",
            "No bank or official ever asks for OTP, PIN, CVV or passwords.",
            "कोई बैंक या अधिकारी कभी OTP, PIN, CVV या पासवर्ड नहीं माँगता।",
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

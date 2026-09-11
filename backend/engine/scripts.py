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
        "digital arrest", "गिरफ", "arrest", "cyber crime", "साइबर", "cbi",
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
    "olx_army": (25, _rx([
        "army", "आर्मी", "crpf", "bsf", "fauji", "olx", "canteen",
        "advance payment", "एडवांस",
    ])),
    "customer_care": (25, _rx([
        "customer care", "कस्टमर केयर", "helpline number", "toll free",
        "refund process", "रिफंड", "complaint number", "care number",
    ])),
}

_CROSS = [
    ("urgency_framing", 15, "Artificial urgency", "बनावटी जल्दबाज़ी",
     "Scams pressure you to act before you think.",
     "ठग सोचने का समय नहीं देते — जल्दबाज़ी ही चाल है।",
     _rx(["तुरंत", "turant", "immediately", "urgent", "abhi", "अभी",
          "24 घंटे", "24 hours", "24 hour", "2 घंटे", "last warning",
          "अंतिम चेतावनी", "final notice", "जल्दी करें"])),
    ("credential_request", 30, "Asks for OTP/PIN", "OTP/PIN माँगा जा रहा है",
     "No bank or official ever asks for OTP, PIN, CVV or passwords.",
     "कोई बैंक या अधिकारी कभी OTP, PIN, CVV या पासवर्ड नहीं माँगता।",
     _rx(["otp", "pin", "cvv", "password", "पासवर्ड", "mpin", "upi pin",
          "card number", "atm card", "expiry date"])),
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
    ("threat_framing", 15, "Threat of penalty/action", "डराने-धमकाने की भाषा",
     "Fear of fines, arrest or disconnection is the pressure lever.",
     "जुर्माना, गिरफ़्तारी या कटौती का डर दिखाना ही इनका हथियार है।",
     _rx(["legal action", "कानूनी कार्रवाई", "जुर्माना", "penalty",
          "case दर्ज", "blacklist"])),
]


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

    return [m[0] for m in matched]

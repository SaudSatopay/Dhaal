"""Demo fixtures — Glue lane (Saud) owns content; Engine keeps stubs serving them.
Personas per docs/CONTRACTS.md. Deterministic: same input beats always demo the same way.
"""

# Beat 1 — KYC scam SMS (danger)
KYC_SCAM_TEXT = (
    "प्रिय ग्राहक, आपका SBI खाता 24 घंटे में बंद हो जाएगा। तुरंत KYC अपडेट करें: "
    "http://sbi-kyc-update.xyz/verify"
)

# Beat 2 — collect-request QR, decoded client-side to this UPI URI (danger)
QR_COLLECT_URI = "upi://collect?pa=refund.helpdesk@okaxis&pn=SBI%20Refunds&am=15000&cu=INR"

# Beat 3 — genuine bank SMS (no_known_risk; false-positive control)
LEGIT_BANK_TEXT = (
    "Dear Customer, Rs.2,500.00 credited to A/c XX4321 on 11-09-26 by UPI ref 625489. "
    "Avl Bal Rs.18,240.00 -SBI"
)

# Beat 4 — digital-arrest call script (voice path, danger)
DIGITAL_ARREST_TRANSCRIPT = (
    "मैं मुंबई साइबर क्राइम ब्रांच से इंस्पेक्टर बोल रहा हूँ। आपके आधार से एक parcel पकड़ा गया है। "
    "गिरफ़्तारी से बचना है तो अभी वेरिफिकेशन फीस भेजिए, किसी को बताइए मत।"
)

# Beat 6 — pre-seeded community-blocklisted scammer (flywheel moment)
BLOCKLISTED_PHONE = "+919876500001"
BLOCKLISTED_DOMAIN = "sbi-kyc-update.xyz"
BLOCKLISTED_UPI = "refund.helpdesk@okaxis"

SEED_INDICATORS = [
    {"_id": "ind_seed_1", "type": "domain", "value": BLOCKLISTED_DOMAIN,
     "report_count": 43, "first_seen": "2026-09-05T10:00:00Z", "category": "kyc_expiry"},
    {"_id": "ind_seed_2", "type": "phone", "value": BLOCKLISTED_PHONE,
     "report_count": 43, "first_seen": "2026-09-06T09:00:00Z", "category": "digital_arrest"},
    {"_id": "ind_seed_3", "type": "upi", "value": BLOCKLISTED_UPI,
     "report_count": 27, "first_seen": "2026-09-07T14:00:00Z", "category": "fake_collect"},
]

# Trends board seed (~200 verified reports, last 7 days, Rajasthan) — condensed aggregates.
SEED_TRENDS = {
    "total_reports": 212,
    "by_category": [
        {"category": "kyc_expiry", "count": 58},
        {"category": "fake_collect", "count": 41},
        {"category": "digital_arrest", "count": 33},
        {"category": "electricity", "count": 26},
        {"category": "lottery", "count": 22},
        {"category": "olx_army", "count": 18},
        {"category": "customer_care", "count": 14},
    ],
    "by_day": [
        {"day": "2026-09-05", "count": 21}, {"day": "2026-09-06", "count": 26},
        {"day": "2026-09-07", "count": 29}, {"day": "2026-09-08", "count": 33},
        {"day": "2026-09-09", "count": 34}, {"day": "2026-09-10", "count": 35},
        {"day": "2026-09-11", "count": 34},
    ],
    "top_indicators": SEED_INDICATORS,
    "cities": [
        {"city": "Jaipur", "count": 84}, {"city": "Jodhpur", "count": 47},
        {"city": "Udaipur", "count": 38}, {"city": "Kota", "count": 24},
        {"city": "Ajmer", "count": 19},
    ],
}

# Canned explanations used when Claude is unavailable (mocked: true)
CANNED_EXPLANATIONS = {
    "danger_hi": "यह message असली बैंक से नहीं है। असली बैंक कभी link भेजकर KYC नहीं करवाते और न ही 24 घंटे की धमकी देते हैं। इस link पर कुछ भी न भरें, पैसे न भेजें।",
    "danger_en": "This is not from a real bank. Banks never do KYC through links or threaten 24-hour closure. Do not enter anything on this link or send money.",
    "collect_hi": "सावधान! यह PAYMENT REQUEST (collect) है — approve करने से पैसे आएँगे नहीं, आपके खाते से कटेंगे। Refund कभी collect request से नहीं आता।",
    "collect_en": "Careful! This is a COLLECT request — approving it takes money OUT of your account. Refunds never arrive as collect requests.",
    "ok_hi": "इसमें कोई ज्ञात खतरे का संकेत नहीं मिला। फिर भी पैसे भेजने से पहले नाम और नंबर खुद जाँच लें।",
    "ok_en": "No known risk signals found. Still verify the name and number yourself before paying.",
    "arrest_hi": "यह 'digital arrest' ठगी है। पुलिस या साइबर सेल कभी फोन पर पैसे नहीं माँगते और न ही 'किसी को मत बताओ' कहते हैं। फोन काटिए और 1930 पर सूचना दीजिए।",
    "arrest_en": "This is a 'digital arrest' scam. Police never demand money on a call or say 'tell no one'. Hang up and report on 1930.",
}

RECOVERY_KIT_TEMPLATE = {
    "call_script_1930": (
        "1930 पर कॉल करके बोलें: 'मेरे साथ UPI fraud हुआ है। आज दिनांक {date} को ₹{amount} "
        "{bank} खाते से {channel} द्वारा कटे हैं। कृपया मेरी complaint दर्ज करें और transaction "
        "freeze करवाएँ।' अपना ref number लिखना न भूलें।"
    ),
    "complaint_draft": (
        "cybercrime.gov.in → Report → Financial Fraud चुनें। विवरण: दिनांक {date}, राशि ₹{amount}, "
        "माध्यम {channel}, बैंक {bank}। जो message/number/UPI ID मिला वह attach करें। "
        "Complaint number संभाल कर रखें।"
    ),
    "bank_letter": (
        "सेवा में, शाखा प्रबंधक, {bank}। विषय: अनधिकृत UPI लेन-देन ₹{amount} ({date})। "
        "महोदय, मेरे खाते से उक्त राशि धोखे से कटी है। कृपया RBI दिशानिर्देशों अनुसार chargeback/"
        "dispute दर्ज करें व खाता अस्थायी रूप से सुरक्षित करें। — खाताधारक"
    ),
    "checklist": [
        "सबसे पहले 1930 पर कॉल करें (पहला घंटा सबसे कीमती है)",
        "cybercrime.gov.in पर complaint दर्ज करें",
        "बैंक की app/branch से transaction dispute करें और UPI temporarily freeze करवाएँ",
        "Message, number, UPI ID के screenshot सुरक्षित रखें — कुछ delete न करें",
        "उसी scammer से दोबारा बात न करें, 'refund दिलाने वाले' भी ठग होते हैं",
    ],
}

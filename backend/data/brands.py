"""Seed lists for the signal engine. Glue (Saud) extends these during the
fixtures pass (H3-H5) — adding entries is safe, renaming/removing needs Harsh."""

# Domains that are genuinely official — exact host or any subdomain of these
# is never flagged. Keep registrable domains only (no www).
OFFICIAL_DOMAINS = {
    # banks
    "sbi.co.in", "onlinesbi.sbi", "sbicard.com", "yonobusiness.sbi",
    "hdfcbank.com", "icicibank.com", "axisbank.com", "kotak.com",
    "pnbindia.in", "canarabank.com", "unionbankofindia.co.in",
    "bankofbaroda.in", "idfcfirstbank.com", "yesbank.in", "indusind.com",
    # UPI / wallets / payments
    "paytm.com", "phonepe.com", "pay.google.com", "bhimupi.org.in",
    "npci.org.in", "bharatbillpay.com",
    # govt / institutions scammers love to fake
    "rbi.org.in", "uidai.gov.in", "incometax.gov.in", "irctc.co.in",
    "licindia.in", "epfindia.gov.in", "cybercrime.gov.in", "mygov.in",
    # telecom (electricity-bill & KYC scams often fake these)
    "airtel.in", "jio.com", "myvi.in",
}

# Tokens that mean "this claims to be that brand". Matched against
# hyphen/dot-split host tokens: exact for all; prefix + misspelling
# (levenshtein) only for tokens of length >= 4 (see engine/common.py).
BRAND_TOKENS = [
    "sbi", "onlinesbi", "sbicard", "yono",
    "hdfc", "hdfcbank", "icici", "icicibank", "axis", "axisbank",
    "kotak", "pnb", "canara", "unionbank", "baroda", "idfc",
    "yesbank", "indusind",
    "paytm", "phonepe", "gpay", "googlepay", "bhim", "npci",
    "rbi", "uidai", "aadhaar", "aadhar", "irctc", "lic", "epfo",
    "incometax", "airtel", "jio",
]

# URL shorteners — destination hidden; engine unwraps when network allowed.
SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly",
    "rb.gy", "tiny.cc", "rebrand.ly", "shorturl.at", "s.id", "t.ly",
    "surl.li", "v.gd", "soo.gd", "clck.ru",
}

# TLDs disproportionately used in Indian payment scams (endswith match).
SUSPICIOUS_TLDS = (
    ".xyz", ".top", ".online", ".icu", ".buzz", ".club", ".info", ".site",
    ".vip", ".cfd", ".sbs", ".click", ".link", ".work", ".monster",
    ".cyou", ".rest", ".quest", ".support", ".fit", ".loan",
)

# Words inside a UPI VPA local-part that mimic officialdom (refund bait).
SUSPICIOUS_VPA_WORDS = (
    "refund", "support", "help", "helpdesk", "care", "official",
    "verify", "kyc", "cashback", "reward", "claim",
)

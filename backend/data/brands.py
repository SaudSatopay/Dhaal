"""Seed lists for the signal engine. Glue (Saud) extends these during the
fixtures pass (H3-H5) — adding entries is safe, renaming/removing needs Harsh.

Merged at rebase (Saud arbitrated): Harsh's structure/types are canonical;
Saud's fixture-pass entries folded in additively — commerce/courier brands,
AU Bank + JVVNL (Jaipur locals), extra shorteners, `.live` TLD, and the new
additive constant LEGIT_UPI_SUFFIXES (nothing imports it yet — future VPA
plausibility checks + frontend hints)."""

# Domains that are genuinely official — exact host or any subdomain of these
# is never flagged. Keep registrable domains only (no www).
OFFICIAL_DOMAINS = {
    # banks
    "sbi.co.in", "onlinesbi.sbi", "sbicard.com", "yonobusiness.sbi",
    "hdfcbank.com", "icicibank.com", "axisbank.com", "kotak.com",
    "pnbindia.in", "netpnb.com", "canarabank.com", "unionbankofindia.co.in",
    "bankofbaroda.in", "bobibanking.com", "idfcfirstbank.com", "yesbank.in",
    "indusind.com", "federalbank.co.in", "rblbank.com", "aubank.in",
    "idbibank.in",
    # UPI / wallets / payments
    "paytm.com", "phonepe.com", "pay.google.com", "bhimupi.org.in",
    "npci.org.in", "bharatbillpay.com", "cred.club", "mobikwik.com",
    "freecharge.in", "amazonpay.in",
    # govt / institutions scammers love to fake
    "rbi.org.in", "uidai.gov.in", "incometax.gov.in", "irctc.co.in",
    "licindia.in", "epfindia.gov.in", "cybercrime.gov.in", "mygov.in",
    "energy.rajasthan.gov.in",  # JVVNL/discoms — electricity-bill scams
    # telecom (electricity-bill & KYC scams often fake these)
    "airtel.in", "jio.com", "myvi.in",
    # commerce / courier (OLX-army + fake-delivery scams)
    "amazon.in", "flipkart.com", "meesho.com", "olx.in",
    "indiapost.gov.in", "bluedart.com", "delhivery.com",
}

# Tokens that mean "this claims to be that brand". Matched against
# hyphen/dot-split host tokens: exact for all; prefix + misspelling
# (levenshtein) only for tokens of length >= 4 (see engine/common.py).
BRAND_TOKENS = [
    "sbi", "onlinesbi", "sbicard", "yono",
    "hdfc", "hdfcbank", "icici", "icicibank", "axis", "axisbank",
    "kotak", "pnb", "canara", "unionbank", "baroda", "idfc",
    "yesbank", "indusind", "rblbank", "aubank",
    "paytm", "phonepe", "gpay", "googlepay", "bhim", "npci",
    "mobikwik", "freecharge", "amazonpay",
    "rbi", "uidai", "aadhaar", "aadhar", "irctc", "lic", "epfo",
    "incometax", "jvvnl",
    "airtel", "jio", "vodafone",
    "amazon", "flipkart", "meesho", "olx",
    "indiapost", "bluedart",
]
# Deliberately NOT tokens (fuzzy/prefix collisions with everyday payment words —
# domains above stay whitelisted): "federal"≈general · "delhivery"≈delivery ·
# "cred" prefixes credit/credited · "idbi"≈idli · "discom"≈discount.

# URL shorteners — destination hidden; engine unwraps when network allowed.
SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly",
    "rb.gy", "tiny.cc", "rebrand.ly", "shorturl.at", "s.id", "t.ly",
    "surl.li", "v.gd", "soo.gd", "clck.ru", "t2m.io", "goo.su", "u.to",
}

# TLDs disproportionately used in Indian payment scams (endswith match).
SUSPICIOUS_TLDS = (
    ".xyz", ".top", ".online", ".icu", ".buzz", ".club", ".info", ".site",
    ".vip", ".cfd", ".sbs", ".click", ".link", ".work", ".monster",
    ".cyou", ".rest", ".quest", ".support", ".fit", ".loan", ".live",
)

# Words inside a UPI VPA local-part that mimic officialdom (refund bait).
SUSPICIOUS_VPA_WORDS = (
    "refund", "support", "help", "helpdesk", "care", "official",
    "verify", "kyc", "cashback", "reward", "claim",
    "bonus", "prize", "lucky", "winner",
)

# A brand's OWN handle families — a brand token in the local part is plausible
# only on the brand's own suffixes (paytm-order1@paytm = maybe legit merchant;
# support.paytm01@okhdfcbank = impersonation). Consumed by engine/upi.py (H11).
BRAND_OWN_SUFFIXES = {
    "paytm": ("@paytm", "@ptyes", "@ptsbi", "@pthdfc", "@ptaxis"),
    "amazonpay": ("@apl", "@yapl", "@amazonpay"),
    "amazon": ("@apl", "@yapl", "@amazonpay"),
    "phonepe": ("@ybl", "@ibl", "@axl"),
}

# Legit UPI handle suffixes issued by real PSPs — ADDITIVE, not yet consumed
# by the engine. A suffix outside this set is a weak signal, never proof.
LEGIT_UPI_SUFFIXES = {
    "@oksbi", "@okhdfcbank", "@okicici", "@okaxis",       # Google Pay
    "@ybl", "@ibl", "@axl",                               # PhonePe
    "@paytm", "@ptyes", "@ptsbi", "@pthdfc", "@ptaxis",   # Paytm
    "@apl", "@yapl", "@amazonpay",                        # Amazon Pay
    "@upi", "@cnrb", "@pnb", "@boi", "@barodampay",
    "@federal", "@idfcbank", "@indus", "@kotak", "@rbl", "@aubank",
}

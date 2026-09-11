import re
from urllib.parse import parse_qs, urlparse

from data.brands import BRAND_OWN_SUFFIXES, SUSPICIOUS_VPA_WORDS
from engine.common import brand_token_match, extract_vpas, host_tokens, make_signal

UPI_URI_RE = re.compile(r"upi://[^\s\"'<>]+", re.I)
_REFUND_WORDS = ("refund", "रिफंड", "cashback", "कैशबैक", "वापसी", "reward")


def detect(text: str, input_type: str, signals: list) -> dict:
    """Parses upi:// URIs (QR payloads land here as qr_text). Returns
    {'is_collect': bool, 'vpas': set} for the blocklist stage."""
    info = {"is_collect": False, "vpas": extract_vpas(text)}
    low = text.lower()

    for uri in UPI_URI_RE.findall(text):
        parsed = urlparse(uri)
        qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        pa = qs.get("pa", "").lower()
        pn = qs.get("pn", "")
        amount = qs.get("am", "")
        if pa:
            info["vpas"].add(pa)

        # UPI deep-link mechanics: collect = approving PULLS money out.
        is_collect = (
            "collect" in parsed.netloc.lower()
            or "collect" in parsed.path.lower()
            or qs.get("mode") == "01"
        )
        if is_collect:
            info["is_collect"] = True
            amt = f"₹{amount} " if amount else ""
            signals.append(make_signal(
                "upi_collect_request", "deterministic", 45,
                "This is a COLLECT request", "यह COLLECT request है",
                f"Approving sends {amt}OUT of your account — money will not come in.",
                f"Approve करते ही {amt}आपके खाते से कटेंगे — पैसे आएँगे नहीं।",
            ))
            if any(w in (pa + " " + pn.lower() + " " + low) for w in _REFUND_WORDS):
                signals.append(make_signal(
                    "collect_refund_bait", "deterministic", 25,
                    "'Refund' that takes money", "'Refund' जो पैसे लेता है",
                    "Real refunds are credited directly — never via a collect request you approve.",
                    "असली refund सीधे खाते में आता है — कभी भी collect request approve करके नहीं।",
                ))

        # payee claiming to be a brand (name or VPA) — real brands use
        # verified merchant handles, not lookalike names on personal VPAs
        brand = brand_token_match(host_tokens(pn.lower())) or (
            pa and brand_token_match(host_tokens(pa.split("@")[0]))
        )
        if brand:
            signals.append(make_signal(
                "payee_impersonation", "deterministic", 30,
                f"Payee poses as {str(brand).upper()}",
                f"Payee खुद को {str(brand).upper()} बता रहा है",
                f"Payee name/ID imitates {str(brand).upper()} but is not a verified merchant handle.",
                f"Payee का नाम/ID {str(brand).upper()} जैसा है पर verified merchant नहीं है।",
            ))

    # Brand token in ANY VPA's local part (free text included — H11 field miss:
    # support.paytm01@okhdfcbank pasted bare scored only +15). A brand on a
    # foreign PSP suffix is impersonation; the brand's own suffixes are exempt.
    for vpa in sorted(info["vpas"]):
        # skip URL-userinfo lookalikes (…//sbi.co.in@evil.xyz) — that text is a
        # URL trick, not a VPA; engine/urls.py owns it (userinfo_url_trick).
        if re.search(r"/" + re.escape(vpa), text):
            continue
        local, _, suffix = vpa.partition("@")
        brand = brand_token_match(host_tokens(local))
        if brand:
            own = BRAND_OWN_SUFFIXES.get(str(brand), ())
            if ("@" + suffix) not in own:
                signals.append(make_signal(
                    "payee_impersonation", "deterministic", 30,
                    f"UPI ID poses as {str(brand).upper()}",
                    f"UPI ID खुद को {str(brand).upper()} बता रही है",
                    f"'{vpa}' carries the {str(brand).upper()} name on a handle {str(brand).upper()} does not issue.",
                    f"'{vpa}' में {str(brand).upper()} का नाम है पर handle {str(brand).upper()} का नहीं है।",
                ))
                break

    # Bait words in ANY VPA in the input — upi:// payee or free text alike
    # (H9 sweep: quickloan.help@okaxis pasted in an SMS body must fire too).
    for vpa in sorted(info["vpas"]):
        if any(w in vpa.split("@")[0] for w in SUSPICIOUS_VPA_WORDS):
            signals.append(make_signal(
                "suspicious_vpa", "deterministic", 15,
                "Bait words in UPI ID", "UPI ID में चारा-शब्द",
                f"'{vpa}' uses words like refund/support/verify to look official.",
                f"'{vpa}' में refund/support/verify जैसे शब्द official दिखने के लिए हैं।",
            ))
            break
    return info

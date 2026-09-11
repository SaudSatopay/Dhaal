from data.brands import OFFICIAL_DOMAINS, SUSPICIOUS_TLDS
from engine.common import brand_token_match, host_tokens, levenshtein, make_signal


def is_official(host: str) -> bool:
    host = host.lower()
    return any(host == off or host.endswith("." + off) for off in OFFICIAL_DOMAINS)


def _lookalike(host: str) -> tuple[str, str] | None:
    """Why does this host imitate something official? -> (what, how) or None."""
    for off in OFFICIAL_DOMAINS:
        if off in host and host != off and not host.endswith("." + off):
            return off, "embeds the real address inside a fake one"
        cap = 1 if len(off) <= 10 else 2
        if levenshtein(host, off, cap) <= cap:
            return off, "is a near-identical misspelling"
    brand = brand_token_match(host_tokens(host))
    if brand:
        return brand.upper(), "uses the brand's name but is not the official site"
    return None


def detect(hosts, signals: list) -> None:
    seen = set()
    for host in hosts:
        host = host.lower().removeprefix("www.")
        if not host or host in seen or is_official(host):
            continue
        seen.add(host)

        hit = _lookalike(host)
        if hit:
            what, how = hit
            signals.append(make_signal(
                "lookalike_domain", "deterministic", 40,
                "Lookalike domain", "नकली मिलती-जुलती वेबसाइट",
                f"{host} {how} ({what}).",
                f"{host} असली {what} जैसा दिखता है पर official नहीं है।",
            ))

        if host.startswith("xn--") or ".xn--" in host:
            signals.append(make_signal(
                "punycode_domain", "deterministic", 25,
                "Disguised characters in address", "पते में छिपे हुए अक्षर",
                f"{host} uses punycode — letters that only look like a real name.",
                f"{host} में ऐसे अक्षर हैं जो असली नाम जैसे सिर्फ़ दिखते हैं।",
            ))

        if host.endswith(SUSPICIOUS_TLDS):
            tld = host[host.rfind("."):]
            signals.append(make_signal(
                "suspicious_tld", "deterministic", 20,
                "Suspicious web address", "संदिग्ध वेबसाइट पता",
                f"Addresses ending {tld} are heavily used in scams; banks never use them.",
                f"{tld} पर खत्म होने वाले पते scam में बहुत चलते हैं; बैंक कभी नहीं।",
            ))

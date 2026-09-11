import ipaddress
import re
from urllib.parse import urlparse

import httpx

from data.brands import SHORTENER_DOMAINS
from engine.common import make_signal

FULL_URL_RE = re.compile(r"https?://[^\s\"'<>）)\]]+", re.I)
# bare domains in SMS text ("sbi-kyc.xyz/verify", "paytm-care.in") — not
# preceded by @ (that's a VPA/email) or another dot/word char
BARE_DOMAIN_RE = re.compile(
    r"(?<![\w@.])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,12})(/[^\s\"'<>]*)?(?![\w@])",
    re.I,
)

_UNWRAP_TIMEOUT = 3.0


def _host_of(url: str) -> str:
    netloc = urlparse(url).netloc
    host = netloc.rsplit("@", 1)[-1]  # strip userinfo trick
    return host.split(":")[0].lower().removeprefix("www.")


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def _unwrap(url: str) -> str | None:
    """Follow a shortener to its destination. Network is optional by design —
    any failure returns None and the shortener signal stands on its own."""
    try:
        with httpx.Client(follow_redirects=True, timeout=_UNWRAP_TIMEOUT) as c:
            r = c.head(url)
            if r.status_code >= 400:
                r = c.get(url)
            return str(r.url)
    except Exception:
        return None


def extract_urls(text: str) -> list[str]:
    urls = FULL_URL_RE.findall(text)
    stripped = FULL_URL_RE.sub(" ", text)
    for m in BARE_DOMAIN_RE.finditer(stripped):
        host, path = m.group(1), m.group(2) or ""
        if not any(ch.isalpha() for ch in host.split(".")[-1]):
            continue
        urls.append(f"http://{host}{path}")
    return urls


def first_host(text: str) -> str | None:
    """Used by report verification to turn a pasted URL into a blocklist value."""
    for u in extract_urls(text):
        h = _host_of(u)
        if h:
            return h
    return None


def detect(text: str, signals: list, allow_network: bool = False) -> dict:
    """URL-structure heuristics; collects every involved host (including
    unwrapped shortener destinations) for the domain + blocklist stages."""
    hosts: list[str] = []
    for url in extract_urls(text):
        netloc = urlparse(url).netloc
        host = _host_of(url)
        if not host:
            continue
        hosts.append(host)

        if "@" in netloc:
            decoy = netloc.rsplit("@", 1)[0]
            signals.append(make_signal(
                "userinfo_url_trick", "deterministic", 35,
                "Address hides the real site", "पता असली साइट छिपा रहा है",
                f"The link shows '{decoy}' but actually opens {host}.",
                f"Link में '{decoy}' दिखता है पर असल में {host} खुलता है।",
            ))

        if _is_ip(host):
            signals.append(make_signal(
                "ip_literal_url", "deterministic", 30,
                "Link is a raw IP address", "Link सीधा IP address है",
                "Legitimate services never send bare-IP links; scam kits do.",
                "असली संस्थाएँ कभी IP-address वाला link नहीं भेजतीं।",
            ))
            continue

        if host in SHORTENER_DOMAINS:
            final = _unwrap(url) if allow_network else None
            if final:
                fhost = _host_of(final)
                if fhost and fhost != host:
                    hosts.append(fhost)
                signals.append(make_signal(
                    "url_shortener", "deterministic", 15,
                    "Short link — destination checked", "Short link — असली पता जाँचा",
                    f"{host} actually leads to {fhost or 'the same place'}.",
                    f"{host} असल में {fhost or 'वहीं'} पर ले जाता है।",
                ))
            else:
                signals.append(make_signal(
                    "url_shortener", "deterministic", 30,
                    "Short link hides destination", "Short link असली पता छिपाता है",
                    f"{host} hides where you will really land — a favourite scam wrapper.",
                    f"{host} छिपाता है कि आप असल में कहाँ पहुँचेंगे — scam का पसंदीदा तरीका।",
                ))
    return {"hosts": hosts}

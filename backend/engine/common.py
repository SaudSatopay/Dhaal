import re

from data.brands import BRAND_TOKENS


def make_signal(sid, source, weight, t_en, t_hi, d_en, d_hi) -> dict:
    return {
        "id": sid, "source": source, "weight": weight,
        "title_en": t_en, "title_hi": t_hi, "detail_en": d_en, "detail_hi": d_hi,
    }


def levenshtein(a: str, b: str, cap: int = 3) -> int:
    """Edit distance, early-exiting at cap+1 (we only care about near-misses)."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > cap:
            return cap + 1
        prev = cur
    return prev[-1]


def brand_token_match(tokens) -> str | None:
    """Which brand does this host/VPA claim to be? Exact token for all brands;
    prefix ('sbikyc'-style only for len>=4) and misspellings for longer ones —
    short tokens like 'sbi'/'lic' stay exact-only so 'asbestos'/'republic'
    never false-positive."""
    for t in tokens:
        if not t:
            continue
        for b in BRAND_TOKENS:
            if t == b:
                return b
            if len(b) >= 4:
                if t.startswith(b) and len(t) > len(b):
                    return b
                d = levenshtein(t, b, 2)
                if (5 <= len(b) <= 6 and d <= 1) or (len(b) >= 7 and d <= 2):
                    return b
    return None


def host_tokens(host: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", host.lower()) if t]


_PHONE_RUN = re.compile(r"\+?\d(?:[\d\s-]{8,16})\d")
_VPA = re.compile(r"\b[a-zA-Z0-9._-]{2,256}@[a-zA-Z][a-zA-Z0-9]{1,64}\b")


def norm_phone(raw: str) -> str | None:
    """Digits only, last 10 — '+91 98765-00001', '9876500001' compare equal."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) >= 10:
        return digits[-10:]
    return None


def extract_phones(text: str) -> set[str]:
    out = set()
    for m in _PHONE_RUN.findall(text):
        p = norm_phone(m)
        if p:
            out.add(p)
    return out


def extract_vpas(text: str) -> set[str]:
    return {m.lower() for m in _VPA.findall(text)}

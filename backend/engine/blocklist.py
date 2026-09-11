"""Community blocklist lookup — the flywheel. A moderator-verified indicator
is high-confidence by definition, so ONE verified report is enough to turn
the verdict: weight 65 clears the danger threshold on its own."""

import re

from engine.common import extract_phones, make_signal, norm_phone

WEIGHT = 65


def _bounded(value: str, low: str) -> bool:
    """Identifier match with boundaries — 'olx.in' must not hit 'prolx.info',
    'a@ok' must not hit 'ba@okx' (H14: precise canonical matching)."""
    return re.search(r"(?<![\w.-])" + re.escape(value) + r"(?![\w-])", low) is not None


def detect(text: str, hosts, vpas, indicators: dict, signals: list) -> str | None:
    low = text.lower()
    host_set = {h.lower() for h in hosts}
    phone_set = extract_phones(text)
    first_category = None

    for value, ind in indicators.items():
        v = str(value).lower()
        itype = ind.get("type", "script")
        if itype == "phone":
            hit = (norm_phone(v) or v) in phone_set
        elif itype == "domain":
            # exact host, or any subdomain of the listed domain, or bounded in prose
            hit = (v in host_set
                   or any(h.endswith("." + v) for h in host_set)
                   or _bounded(v, low))
        elif itype == "upi":
            hit = v in vpas or _bounded(v, low)
        else:  # script snippets
            hit = v in low
        if not hit:
            continue

        first_category = first_category or ind.get("category")
        count = ind.get("report_count", 1)
        signals.append(make_signal(
            "community_blocklist", "community", WEIGHT,
            f"Reported by {count} user{'s' if count != 1 else ''}",
            f"{count} लोगों ने रिपोर्ट किया है",
            f"'{value}' is on the verified community blocklist ({itype}).",
            f"'{value}' verified community blocklist में है ({itype})।",
        ))
    return first_category

"""Dhaal deterministic signal engine.

Verdict = scored sum of deterministic + community signals ONLY. The LLM layer
(added H4-H6) narrates from these signals and can never change the verdict —
`llm_pattern` signals, when they arrive, carry zero weight here.
"""

from engine import blocklist, domains, scripts, upi, urls

DANGER_AT = 60
SUSPICIOUS_AT = 30


def run_signal_engine(
    payload: str,
    input_type: str = "text",
    indicators: dict | None = None,
    allow_network: bool = False,
):
    """Returns (verdict, score, signals, category) per docs/CONTRACTS.md."""
    text = (payload or "").strip()
    signals: list[dict] = []

    upi_info = upi.detect(text, input_type, signals)
    url_info = urls.detect(text, signals, allow_network=allow_network)
    domains.detect(url_info["hosts"], signals)
    script_cats = scripts.detect(text, signals)
    community_cat = blocklist.detect(
        text, url_info["hosts"], upi_info["vpas"], indicators or {}, signals
    )

    score = min(100, sum(s["weight"] for s in signals))
    verdict = (
        "danger" if score >= DANGER_AT
        else "suspicious" if score >= SUSPICIOUS_AT
        else "no_known_risk"
    )

    # category precedence: collect mechanics > community intel > script pattern
    category = None
    if upi_info["is_collect"]:
        category = "fake_collect"
    elif community_cat:
        category = community_cat
    elif script_cats:
        category = script_cats[0]

    signals.sort(key=lambda s: s["weight"], reverse=True)
    return verdict, score, signals, category

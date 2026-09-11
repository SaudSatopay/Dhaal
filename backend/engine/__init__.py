"""Dhaal deterministic signal engine.

Verdict = scored sum of deterministic + community signals ONLY. The LLM layer
narrates from these signals and can never change the verdict — `llm_pattern`
signals, when they arrive, carry zero weight here.

H14 refactor (external review): the engine now ALSO returns a `facts` block —
what the input *is*, parsed independently of whether it is suspicious. The
same QR yields the same payment facts whatever the user expected; expectation
only feeds mismatch detection. Missing evidence stays unknown, never guessed.
"""

from engine import blocklist, domains, scripts, upi, urls

DANGER_AT = 60
SUSPICIOUS_AT = 30

_FACT_ENUMS = {
    "money_direction": {"out_of_your_account", "none_detected", "unknown"},
    "expectation": {"pay", "receive", "verify", "unknown"},
    "parse_status": {"valid", "incomplete", "unsupported", "malformed", "multiple", None},
}

_EV_TO_ACTION = {
    "credential_request": "disclose_credential",
    "remote_access": "grant_remote_access",
    "advance_fee": "send_money",
    "fee_demand": "pay_fee",
    "collect_approve": "approve_payment",
    "family_emergency": "send_money",
    "new_number_request": "send_money",
    "apk_file": "install_app_file",
    "chain_forward": "forward_message",
}


def _build_facts(input_type, expected_intent, upi_info, url_info, evidence,
                 signals) -> dict:
    parse = upi_info.get("parse")
    executable = parse is not None and parse.get("status") == "valid" \
        and parse.get("action") in ("pay", "collect")

    requested: list[str] = []
    for ev in evidence:
        act = _EV_TO_ACTION.get(ev["kind"])
        if act and act not in requested:
            requested.append(act)
    if executable and "approve_payment" not in requested:
        requested.insert(0, "approve_payment")
    if url_info.get("hosts") and "open_link" not in requested:
        requested.append("open_link")

    # money direction is a PARSED fact: any executable payment request moves
    # money out of the approver's account — true for pay and collect alike,
    # and true regardless of what the user expected (the H13 inconsistency).
    if executable or any(ev["kind"] in ("advance_fee", "collect_approve",
                                        "family_emergency", "new_number_request")
                         for ev in evidence):
        money_direction = "out_of_your_account"
    elif parse is not None and parse.get("status") in ("incomplete", "malformed",
                                                       "unsupported", "multiple"):
        money_direction = "unknown"
    else:
        money_direction = "none_detected"

    claimed = upi_info.get("claimed_brand")
    if not claimed:
        for s in signals:
            if s["id"] == "lookalike_domain":
                claimed = s.get("claimed_brand")
                break

    missing: list[str] = []
    if parse is not None:
        if parse.get("status") == "incomplete":
            missing.append("payee")
        if parse.get("status") == "valid" and not parse.get("amount"):
            missing.append("amount")
    if (expected_intent or "unknown") == "unknown" and executable:
        missing.append("your_intent")

    pressure = [ev["kind"] for ev in evidence
                if ev["kind"] in ("urgency_framing", "secrecy_pressure",
                                  "threat_framing", "coercion_extortion")]

    facts = {
        "input_kind": input_type,
        "parse": parse,
        "expectation": expected_intent if expected_intent in ("pay", "receive", "verify")
        else "unknown",
        "money_direction": money_direction,
        "claimed_identity": claimed,
        "requested_actions": requested[:8],
        "evidence": evidence[:24],
        "pressure": pressure,
        "missing": missing,
    }
    assert facts["money_direction"] in _FACT_ENUMS["money_direction"]
    assert facts["expectation"] in _FACT_ENUMS["expectation"]
    assert parse is None or parse.get("status") in _FACT_ENUMS["parse_status"]
    return facts


def run_signal_engine(
    payload: str,
    input_type: str = "text",
    indicators: dict | None = None,
    allow_network: bool = False,
    expected_intent: str | None = None,
):
    """Returns (verdict, score, signals, category, facts) per docs/CONTRACTS.md."""
    text = (payload or "").strip()
    signals: list[dict] = []
    evidence: list[dict] = []

    upi_info = upi.detect(text, input_type, signals, expected_intent=expected_intent)
    url_info = urls.detect(text, signals, allow_network=allow_network)
    domains.detect(url_info["hosts"], signals)
    script_cats = scripts.detect(text, signals, evidence)
    community_cat = blocklist.detect(
        text, url_info["hosts"], upi_info["vpas"], indicators or {}, signals
    )

    # Dedup by signal id (H12): identical signals never stack; distinct
    # evidence spans are preserved in facts.evidence even when scoring dedups.
    seen: dict[str, dict] = {}
    for s in signals:
        if s["id"] in seen:
            seen[s["id"]]["occurrences"] = seen[s["id"]].get("occurrences", 1) + 1
        else:
            seen[s["id"]] = s
    signals = list(seen.values())
    for s in signals:
        n = s.get("occurrences", 1)
        if n > 1:
            s["detail_en"] = s["detail_en"].rstrip() + f" (×{n} in this input)"
            s["detail_hi"] = s["detail_hi"].rstrip() + f" (×{n})"

    score = min(100, sum(s["weight"] for s in signals))
    verdict = (
        "danger" if score >= DANGER_AT
        else "suspicious" if score >= SUSPICIOUS_AT
        else "no_known_risk"
    )

    # category precedence: collect mechanics > community intel > script pattern.
    # A PAY QR with an intent mismatch is NOT labelled fake_collect — the
    # transaction-type label comes from validated parsing only.
    category = None
    if upi_info["is_collect"]:
        category = "fake_collect"
    elif community_cat:
        category = community_cat
    elif script_cats:
        category = script_cats[0]

    facts = _build_facts(input_type, expected_intent, upi_info, url_info,
                         evidence, signals)

    signals.sort(key=lambda s: s["weight"], reverse=True)
    return verdict, score, signals, category, facts

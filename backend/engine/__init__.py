"""Dhaal deterministic signal engine.

Verdict = scored sum of deterministic + community signals ONLY. The LLM layer
narrates from these signals and can never change the verdict — `llm_pattern`
signals, when they arrive, carry zero weight here.

H14 refactor (external review): the engine now ALSO returns a `facts` block —
what the input *is*, parsed independently of whether it is suspicious. The
same QR yields the same payment facts whatever the user expected; expectation
only feeds mismatch detection. Missing evidence stays unknown, never guessed.
"""

import re

from engine import blocklist, domains, scripts, upi, urls
from engine.common import make_signal

DANGER_AT = 60
SUSPICIOUS_AT = 30

_FACT_ENUMS = {
    "money_direction": {"out_of_your_account", "none_detected", "unknown"},
    "expectation": {"pay", "receive", "verify", "unknown"},
    "parse_status": {"valid", "incomplete", "unsupported", "malformed", "multiple", None},
}

# Offset convention (H16, documented contract): evidence `start`/`end` are
# UTF-16 CODE UNITS into the raw payload — i.e. plain JavaScript string
# indices (`payload.slice(start, end)` is exact), because every consumer is a
# JS surface. Python computes them from char offsets via the utf-16-le length
# trick below; astral-plane emoji count as 2 units on both sides, so Hindi,
# emoji and mixed text stay aligned.


def _u16(s: str, char_idx: int) -> int:
    return len(s[:char_idx].encode("utf-16-le")) // 2


# H16 §4C: an amount PROMISED to the user in PROSE (refund/cashback/prize
# "you'll get ₹X"). upi:// URIs are blanked LENGTH-PRESERVINGLY first, so a
# request's own am= never reads as a promise and match offsets stay raw-text
# offsets (same trick as scripts._strip_negated).
_PROMISE_WORDS = re.compile(
    r"refund|रिफंड|cashback|कैशबैक|prize|इनाम|jeet|जीत|milega|मिलेगा|"
    r"milenge|मिलेंगे|wapas|वापस|credited|aayega|आएगा", re.I)
_AMOUNT_IN_PROSE = re.compile(r"(?:₹|rs\.?\s?)\s?([\d,]{2,9})", re.I)
_URI_BLANK = re.compile(r"upi://[^\s\"'<>]*")


def _promised_incoming(text: str):
    """(amount_str, start, end) of the first promised-in amount, else None."""
    prose = _URI_BLANK.sub(lambda m: " " * len(m.group(0)), text)
    for pm in _AMOUNT_IN_PROSE.finditer(prose):
        window = prose[max(0, pm.start() - 45):pm.end() + 45]
        if _PROMISE_WORDS.search(window):
            return pm.group(1).replace(",", ""), pm.start(), pm.end()
    return None


# evidence kind -> (linked signal id, factual). factual=True marks records
# that are identifiers/context — NOT accusations of wrongdoing by themselves.
_EV_META: dict[str, tuple[str | None, bool]] = {
    "credential_request": ("credential_request", False),
    "credential_self_query": (None, True),
    "credential_agent_flow": (None, True),
    "credential_delivery": (None, True),
    "code_delivery_context": (None, True),
    "remote_access": ("credential_request", False),
    "advance_fee": ("advance_fee_refund", False),
    "fee_demand": ("fee_demand", False),
    "collect_approve": ("collect_to_receive_bait", False),
    "extortion_disclosure": ("extortion_disclosure", False),
    "threat_framing": ("threat_framing", False),
    "coercion_extortion": ("coercion_extortion", False),
    "urgency_framing": ("urgency_framing", False),
    "secrecy_pressure": ("secrecy_pressure", False),
    "family_emergency": ("family_emergency_pressure", False),
    "new_number_request": ("unverified_family_request", False),
    "chain_forward": ("chain_forward_bait", False),
    "apk_file": ("apk_sideload", False),
    "reported_speech": ("reported_or_educational", True),
    "destination": (None, True),
    "refund_promise": ("pay_uri_refund_bait", False),
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


def _build_facts(text, input_type, expected_intent, upi_info, url_info,
                 evidence, signals) -> dict:
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

    # H16 §4C: an amount PROMISED to the user (refund/cashback/prize "you'll
    # get ₹X") — extracted from prose only, never from inside a upi:// URI, so
    # the reality check can contrast promised-IN with requested-OUT.
    pr = _promised_incoming(text)
    promised = pr[0] if pr else None

    facts = {
        "input_kind": input_type,
        "parse": parse,
        "promised_incoming": promised,
        "expectation": expected_intent if expected_intent in ("pay", "receive", "verify")
        else "unknown",
        "money_direction": money_direction,
        "claimed_identity": claimed,
        "requested_actions": requested[:8],
        "evidence": evidence[:24],  # finalized (ids/offsets) by the caller
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

    # H16 §4C composite: prose PROMISES money IN while the same message
    # carries an EXECUTABLE PAY request — "pay to receive your refund".
    # Receiving money never requires authorizing a payment. The collect twin
    # (collect_refund_bait) lives in engine/upi.py; this is the pay-URI lane.
    _parse = upi_info.get("parse")
    _promise = _promised_incoming(text)
    if _promise and _parse and _parse.get("status") == "valid" \
            and _parse.get("action") == "pay":
        p_amt, p_s, p_e = _promise
        req_amt = _parse.get("amount")
        signals.append(make_signal(
            "pay_uri_refund_bait", "deterministic", 45,
            "'Refund' that OPENS a payment", "'Refund' जो payment खुलवाता है",
            (f"₹{p_amt} promised IN — but the link opens a "
             + (f"₹{req_amt} " if req_amt else "")
             + "PAY request: authorizing it sends money OUT of your account. "
               "Receiving money never requires you to pay."),
            (f"₹{p_amt} आने का वादा — पर link "
             + (f"₹{req_amt} की " if req_amt else "")
             + "PAY request खोलता है: authorize करते ही पैसे आपके खाते से "
               "जाएँगे। पैसे पाने के लिए कभी pay नहीं करना पड़ता।"),
        ))
        evidence.append({"kind": "refund_promise", "span": text[p_s:p_e][:120],
                         "sentence": None, "start": p_s, "end": p_e})

    # destinations — visible identifiers the money/replies would flow to.
    # FACTUAL records: extraction is not an accusation and never implies the
    # identifier is malicious or verified. (upi:// URIs are skipped — the
    # parse block already carries their payee precisely.)
    if not text.lower().startswith("upi://"):
        from engine.common import _PHONE_RUN, _VPA
        from engine.urls import FULL_URL_RE
        n_dest = 0
        for rx in (FULL_URL_RE, _VPA, _PHONE_RUN):
            for m in rx.finditer(text):
                if n_dest >= 6:
                    break
                if len(m.group(0)) < 6:
                    continue
                evidence.append({"kind": "destination", "span": m.group(0)[:120],
                                 "sentence": None, "start": m.start(),
                                 "end": m.end()})
                n_dest += 1

    # finalize evidence: stable ids, UTF-16 offsets, signal links, factual flag
    for n, ev in enumerate(evidence, 1):
        ev["id"] = f"ev{n}"
        sig_link, factual = _EV_META.get(
            ev["kind"],
            (f"script_{ev['kind'][9:]}", False) if ev["kind"].startswith("category:")
            else (None, False))
        ev["signal"] = sig_link
        ev["factual"] = factual
        if ev.get("start") is not None:
            ev["quote"] = text[ev["start"]:ev["end"]][:160]
            ev["start"] = _u16(text, ev["start"])
            ev["end"] = _u16(text, ev["end"])

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

    facts = _build_facts(text, input_type, expected_intent, upi_info, url_info,
                         evidence, signals)

    signals.sort(key=lambda s: s["weight"], reverse=True)
    return verdict, score, signals, category, facts

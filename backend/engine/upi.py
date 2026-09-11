"""upi:// URI semantics — parse FACTS first, judge risk second (H14 refactor).

parse_uris() is suspicion-free: it reports what each URI *is* (action, payee,
amount, validity) per the NPCI deep-linking spec, identically regardless of
what the user expected. detect() then derives risk signals FROM those facts
plus the user's stated expectation. mode=01 stays what H12 established: QR-
initiated, NOT collect.

Parse statuses (mutually exclusive per URI):
  valid       — supported action (pay|collect) with a payee VPA
  incomplete  — supported action but no payee (pa=): not an executable request
  unsupported — a upi scheme action we don't model (mandate etc.): no claims
  malformed   — unparseable / conflicting duplicate params / no action at all
"""

import re
from urllib.parse import parse_qs, unquote_plus, urlparse

from data.brands import BRAND_OWN_SUFFIXES, LEGIT_UPI_SUFFIXES, SUSPICIOUS_VPA_WORDS
from engine.common import brand_token_match, extract_vpas, host_tokens, make_signal


def _plausible_merchant(local: str, suffix: str, brand: str) -> bool:
    """H15 (VPA plausibility): `zomato@paytm` — the EXACT brand name as the
    whole local part on a known PSP handle — is how aggregator-issued merchant
    VPAs actually look, so it is plausible, not impersonation. Anything with
    extra words (`support.zomato`, `airtel-recharge`) keeps flagging: real
    merchant handles don't carry bait prefixes. Fixes published v2-comparison
    regression b04 generically, no per-brand suffix lists needed."""
    return local == brand and ("@" + suffix) in LEGIT_UPI_SUFFIXES

UPI_URI_RE = re.compile(r"upi://[^\s\"'<>]*", re.I)
_REFUND_WORDS = ("refund", "रिफंड", "cashback", "कैशबैक", "वापसी", "reward")
_SUPPORTED_ACTIONS = ("pay", "collect")
_AMOUNT_RE = re.compile(r"\d{1,7}(\.\d{1,2})?")
_VPA_SHAPE = re.compile(r"^[a-z0-9._-]{2,256}@[a-z][a-z0-9]{1,64}$", re.I)


def parse_uris(text: str) -> list[dict]:
    """Every upi:// URI in the text as a fact record — no risk judgement."""
    out = []
    for uri in UPI_URI_RE.findall(text):
        rec = {"uri": uri[:300], "status": "malformed", "action": "unknown",
               "payee_vpa": None, "payee_name": None, "amount": None,
               "currency": None, "amount_invalid": False}
        try:
            parsed = urlparse(uri)
        except ValueError:
            out.append(rec)
            continue
        action = (parsed.netloc or parsed.path.strip("/")).strip().lower()
        rec["action"] = action or "unknown"
        try:
            qs_lists = parse_qs(parsed.query, keep_blank_values=True)
        except ValueError:
            qs_lists = {}
        # duplicate params that disagree = tampering/ambiguity — never guess
        conflicting = any(len(set(v)) > 1 for v in qs_lists.values())
        qs = {k.lower(): v[0].strip() for k, v in qs_lists.items()}

        pa = unquote_plus(qs.get("pa", "")).strip().lower()
        if pa and not _VPA_SHAPE.fullmatch(pa):
            pa = ""  # a payee that isn't a VPA shape is no payee
        pn = unquote_plus(qs.get("pn", "")).strip()[:100]
        am_raw = unquote_plus(qs.get("am", "")).strip()
        amount = None
        if am_raw:
            if _AMOUNT_RE.fullmatch(am_raw) and float(am_raw) > 0:
                amount = am_raw
            else:
                rec["amount_invalid"] = True
        cu = qs.get("cu", "").upper() or None

        rec.update({"payee_vpa": pa or None, "payee_name": pn or None,
                    "amount": amount, "currency": cu if amount else None})
        if conflicting or not action:
            rec["status"] = "malformed"
        elif action not in _SUPPORTED_ACTIONS:
            rec["status"] = "unsupported"
        elif not pa:
            rec["status"] = "incomplete"
        else:
            rec["status"] = "valid"
        out.append(rec)
    return out


def summarize_parse(uris: list[dict]) -> dict | None:
    """One facts block for the whole input. Multiple differing payment URIs are
    reported as 'multiple' — amounts/payees are never merged across requests."""
    if not uris:
        return None
    base = {"uri_count": len(uris), "uris": uris}
    if len(uris) == 1:
        u = uris[0]
        base.update({"status": u["status"], "action": u["action"],
                     "payee_vpa": u["payee_vpa"], "payee_name": u["payee_name"],
                     "amount": u["amount"], "currency": u["currency"]})
        return base
    firsts = {(u["payee_vpa"], u["amount"], u["action"]) for u in uris}
    if len(firsts) == 1:  # true duplicates of one request
        u = uris[0]
        base.update({"status": u["status"], "action": u["action"],
                     "payee_vpa": u["payee_vpa"], "payee_name": u["payee_name"],
                     "amount": u["amount"], "currency": u["currency"]})
    else:
        base.update({"status": "multiple", "action": "unknown", "payee_vpa": None,
                     "payee_name": None, "amount": None, "currency": None})
    return base


def detect(text: str, input_type: str, signals: list,
           expected_intent: str | None = None) -> dict:
    """Risk signals derived from parsed facts + expectation. Returns
    {'is_collect', 'vpas', 'has_uri', 'amount', 'uris', 'parse', 'claimed_brand'}."""
    uris = parse_uris(text)
    parse = summarize_parse(uris)
    info = {"is_collect": False, "vpas": extract_vpas(text), "has_uri": bool(uris),
            "amount": parse["amount"] if parse else "", "uris": uris,
            "parse": parse, "claimed_brand": None}
    low = text.lower()

    executable = [u for u in uris if u["status"] == "valid"]
    for u in uris:
        if u["payee_vpa"]:
            info["vpas"].add(u["payee_vpa"])

        # UPI deep-link mechanics: collect = approving PULLS money out.
        # (mode=01 means QR-initiated, NOT collect — H12/NPCI.)
        if u["action"] == "collect" and u["status"] in ("valid", "incomplete"):
            info["is_collect"] = True
            amt = f"₹{u['amount']} " if u["amount"] else ""
            signals.append(make_signal(
                "upi_collect_request", "deterministic", 45,
                "This is a COLLECT request", "यह COLLECT request है",
                f"Approving sends {amt}OUT of your account — money will not come in.",
                f"Approve करते ही {amt}आपके खाते से कटेंगे — पैसे आएँगे नहीं।",
            ))
            pa, pn = u["payee_vpa"] or "", (u["payee_name"] or "").lower()
            if any(w in (pa + " " + pn + " " + low) for w in _REFUND_WORDS):
                signals.append(make_signal(
                    "collect_refund_bait", "deterministic", 25,
                    "'Refund' that takes money", "'Refund' जो पैसे लेता है",
                    "Real refunds are credited directly — never via a collect request you approve.",
                    "असली refund सीधे खाते में आता है — कभी भी collect request approve करके नहीं।",
                ))

        # payee claiming to be a brand (name or VPA local part)
        pn_l = (u["payee_name"] or "").lower()
        pa_l = u["payee_vpa"] or ""
        pa_local, _, pa_suffix = pa_l.partition("@")
        brand = brand_token_match(host_tokens(pn_l)) or (
            pa_l and brand_token_match(host_tokens(pa_local))
        )
        if brand:
            own = BRAND_OWN_SUFFIXES.get(str(brand), ())
            suffix = "@" + pa_suffix if pa_l else ""
            if not (suffix and suffix in own) \
                    and not (pa_l and _plausible_merchant(pa_local, pa_suffix, str(brand))):
                info["claimed_brand"] = str(brand)
                signals.append(make_signal(
                    "payee_impersonation", "deterministic", 30,
                    f"Payee poses as {str(brand).upper()}",
                    f"Payee खुद को {str(brand).upper()} बता रहा है",
                    f"Payee name/ID imitates {str(brand).upper()} but is not a verified merchant handle.",
                    f"Payee का नाम/ID {str(brand).upper()} जैसा है पर verified merchant नहीं है।",
                ))

        # VPA plausibility (H15): a payee handle no known PSP issues is a weak
        # caution — never proof (the PSP list is a seed, not the registry).
        if pa_l and pa_suffix and ("@" + pa_suffix) not in LEGIT_UPI_SUFFIXES:
            signals.append(make_signal(
                "vpa_unknown_handle", "deterministic", 12,
                "Unrecognized UPI handle", "अनजाना UPI handle",
                f"'@{pa_suffix}' is not a handle from the known PSP list — verify the payee name extra carefully.",
                f"'@{pa_suffix}' जाने-पहचाने PSP handles में नहीं है — नाम-पता और भी ध्यान से जाँचें।",
            ))

    # INTENT MISMATCH — only against an EXECUTABLE payment request (valid
    # parse). Every valid upi:// request, pay or collect, moves money OUT of
    # the approver's account; if the user expected money IN, that conflict is
    # itself the evidence — no scam keywords needed. Wording is precise: the
    # QR *opens* a payment request; authorizing it sends money. Scanning alone
    # does not transfer anything.
    if expected_intent == "receive" and executable:
        u = executable[0]
        amt = f"₹{u['amount']} का " if u["amount"] else ""
        amt_en = f"a ₹{u['amount']} " if u["amount"] else "a "
        if u["action"] == "collect":
            d_en = f"You expected money IN — this is {amt_en}collect request: approving it sends money OUT of your account."
            d_hi = f"आपको पैसे आने थे — यह {amt}collect request है: approve करते ही पैसे आपके खाते से कटेंगे।"
        else:
            d_en = (f"You expected money IN — but this QR opens {amt_en}payment request. "
                    "Authorizing that payment sends money FROM your account. "
                    "Receiving money never requires you to authorize a payment.")
            d_hi = (f"आपको पैसे आने थे — पर यह QR {amt}payment request खोलता है। "
                    "उसे authorize करते ही पैसे आपके खाते से जाएँगे। "
                    "पैसे पाने के लिए कभी payment authorize नहीं करना पड़ता।")
        signals.append(make_signal(
            "intent_mismatch", "deterministic", 40,
            "Does the OPPOSITE of what you expect", "जो आप चाहते हैं, उससे उल्टा",
            d_en, d_hi,
        ))

    # Brand token in ANY VPA's local part (free text included — H11):
    # brand on a foreign PSP suffix is impersonation; own suffixes exempt.
    for vpa in sorted(info["vpas"]):
        # skip URL-userinfo lookalikes (…//sbi.co.in@evil.xyz) — that text is a
        # URL trick, not a VPA; engine/urls.py owns it (userinfo_url_trick).
        if re.search(r"/" + re.escape(vpa), text):
            continue
        local, _, suffix = vpa.partition("@")
        brand = brand_token_match(host_tokens(local))
        if brand:
            own = BRAND_OWN_SUFFIXES.get(str(brand), ())
            if ("@" + suffix) not in own \
                    and not _plausible_merchant(local, suffix, str(brand)):
                info["claimed_brand"] = info["claimed_brand"] or str(brand)
                signals.append(make_signal(
                    "payee_impersonation", "deterministic", 30,
                    f"UPI ID poses as {str(brand).upper()}",
                    f"UPI ID खुद को {str(brand).upper()} बता रही है",
                    f"'{vpa}' carries the {str(brand).upper()} name on a handle {str(brand).upper()} does not issue.",
                    f"'{vpa}' में {str(brand).upper()} का नाम है पर handle {str(brand).upper()} का नहीं है।",
                ))
                break

    # Bait words in ANY VPA in the input — upi:// payee or free text alike.
    for vpa in sorted(info["vpas"]):
        if any(w in vpa.split("@")[0] for w in SUSPICIOUS_VPA_WORDS):
            signals.append(make_signal(
                "suspicious_vpa", "deterministic", 15,
                "Bait words in UPI ID", "UPI ID में चारा-शब्द",
                f"'{vpa}' uses words like refund/support/verify to look official.",
                f"'{vpa}' में refund/support/verify जैसे शब्द official दिखने के लिए हैं।",
            ))
            break

    # v5 family: bait words in the payee DISPLAY NAME of an EXECUTABLE
    # request ("pn=Bank Refund") — the name a UPI app shows at authorize time
    # was chosen to look like money coming in. Weight lands at suspicious on
    # its own: an executable request wearing a refund costume is the trick.
    # (Skipped when payee_impersonation already fired — one deceptive payee
    # identity is ONE finding, not two stacking weights.)
    for u in executable if not info["claimed_brand"] else []:
        pn_low = (u["payee_name"] or "").lower()
        if pn_low and any(w in pn_low for w in SUSPICIOUS_VPA_WORDS):
            signals.append(make_signal(
                "baited_payee_name", "deterministic", 30,
                "Payee NAME dressed as refund/reward",
                "Payee का नाम refund/reward जैसा",
                f"This payment request's display name '{u['payee_name']}' uses refund/support wording — a request never GIVES money, whatever it is named.",
                f"इस payment request का नाम '{u['payee_name']}' refund/support जैसा रखा गया है — request कभी पैसे देती नहीं, नाम कुछ भी हो।",
            ))
            break
    return info

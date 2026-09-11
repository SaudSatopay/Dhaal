"""Golden-path regression checks for the signal engine — zero deps, run:
    cd backend && .venv/Scripts/python.exe tests/run_engine_checks.py
Every demo beat from docs/PLAN.md is asserted here; run before every push
that touches engine/ or data/.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fixtures as FX  # noqa: E402
from engine import run_signal_engine  # noqa: E402

INDICATORS = {i["value"]: dict(i) for i in FX.SEED_INDICATORS}
PASS = 0


def check(name, payload, want_verdict, *, itype="text", indicators=None,
          want_signal=None, want_category=None, forbid_signal=None,
          expected_intent=None, want_fact=None):
    """want_fact: dotted path into the facts block -> expected value,
    e.g. {"parse.status": "valid", "money_direction": "out_of_your_account"}."""
    global PASS
    verdict, score, signals, category, facts = run_signal_engine(
        payload, itype, indicators if indicators is not None else INDICATORS,
        allow_network=False, expected_intent=expected_intent,
    )
    ids = [s["id"] for s in signals]
    ok = verdict == want_verdict
    if want_signal:
        ok = ok and want_signal in ids
    if forbid_signal:
        ok = ok and forbid_signal not in ids
    if want_category:
        ok = ok and category == want_category
    for path, want in (want_fact or {}).items():
        node = facts
        for part in path.split("."):
            node = (node or {}).get(part)
        ok = ok and node == want
    status = "ok " if ok else "FAIL"
    print(f"{status} {name}: verdict={verdict} score={score} cat={category} signals={ids}")
    if not ok:
        sys.exit(f"FAILED: {name} (wanted {want_verdict}"
                 f"{', signal ' + want_signal if want_signal else ''}"
                 f"{', category ' + want_category if want_category else ''})")
    PASS += 1


# --- the five golden-path beats ---
check("beat1 KYC scam SMS", FX.KYC_SCAM_TEXT, "danger",
      want_signal="lookalike_domain", want_category="kyc_expiry")
check("beat2 collect QR", FX.QR_COLLECT_URI, "danger", itype="qr_text",
      want_signal="upi_collect_request", want_category="fake_collect")
check("beat3 legit bank SMS", FX.LEGIT_BANK_TEXT, "no_known_risk")
check("beat4 digital-arrest voice", FX.DIGITAL_ARREST_TRANSCRIPT, "danger",
      itype="voice_transcript", want_signal="script_digital_arrest",
      want_category="digital_arrest")
check("beat6 blocklisted number", FX.BLOCKLISTED_PHONE, "danger",
      want_signal="community_blocklist")

# --- flywheel: ONE fresh verified report must be enough for danger ---
check("fresh single report", "call from 9812345670 about parcel",
      "danger", indicators={"+919812345670": {
          "type": "phone", "value": "+919812345670",
          "report_count": 1, "category": "digital_arrest"}})

# --- phone normalisation variants all hit the same indicator ---
for variant in ("98765 00001", "+91-98765-00001", "09876500001 par call karo"):
    check(f"phone variant '{variant}'", variant, "danger",
          want_signal="community_blocklist")

# --- false-positive controls ---
check("legit pay QR", "upi://pay?pa=sharma.store@ybl&pn=Sharma%20General%20Store&am=120&cu=INR",
      "no_known_risk", itype="qr_text", forbid_signal="upi_collect_request")
check("casual chat", "Bhai kal movie chalein? 7 baje uber le lena",
      "no_known_risk")
check("brand mention in plain text ok", "Maine SBI branch jaakar KYC karwa liya",
      "no_known_risk", indicators={})

# --- URL heuristics ---
check("misspelt domain", "login at sbl.co.in/verify update now",
      "suspicious", indicators={}, want_signal="lookalike_domain")
check("userinfo trick", "https://sbi.co.in@evil-site.xyz/login",
      "suspicious", indicators={}, want_signal="userinfo_url_trick")
check("ip literal", "pay here http://185.63.90.11/upi",
      "suspicious", indicators={}, want_signal="ip_literal_url")
check("shortener unresolved", "aapka refund yahan hai bit.ly/3xk9",
      "suspicious", indicators={}, want_signal="url_shortener")
check("brand token domain", "offer: hdfc-rewards.top/claim",
      "danger", indicators={}, want_signal="lookalike_domain")

# --- script patterns ---
# H12: advance_fee_refund now stacks on lottery+fee — danger is the truer verdict
check("lottery + fee", "Congratulations! KBC lottery winner. Processing fee Rs 5000 bhejein",
      "danger", indicators={}, want_signal="script_lottery")
check("electricity scam", "बिजली बिल बकाया है, आज रात disconnect हो जाएगा। तुरंत भुगतान करें 9812340000",
      "suspicious", indicators={}, want_signal="script_electricity")

# --- H9 sweep payloads (docs/SWEEP-H9.md) — the four fixed misses ---
check("H9.1 legit OTP delivery stays clean",
      "123456 is your OTP for SBI net banking login. Do not share it with anyone. -SBI",
      "no_known_risk", indicators={}, forbid_signal="credential_request")
check("H9.1b real OTP request still fires",
      "SBI account band ho jayega, apna OTP turant batao",
      "suspicious", indicators={}, want_signal="credential_request")
check("H9.2 job scam",
      "Work from home! Earn Rs 5000 daily just liking YouTube videos. Register now t.ly/j0bz limited seats",
      "danger", indicators={}, want_signal="script_job_scam")
check("H9.3 loan-fee scam",
      "आपके आधार पर ₹50,000 का लोन approve हो गया है। Processing fee ₹550 इस UPI पर भेजें: quickloan.help@okaxis",
      "danger", indicators={}, want_signal="script_loan_fee")
# H12 (external review): this used to stay under threshold "by design" — the
# pay-to-receive-refund mechanic now has its own signal and correctly flags.
check("H9.3b/H12 refund-advance bait flags",
      "Refund ke liye paise bhejo refund.super@okhdfcbank par",
      "suspicious", indicators={}, want_signal="advance_fee_refund")
check("H9.4 olx army collect bait",
      "I am army officer posted at Siachen. I want to buy your sofa. I will send "
      "advance payment through UPI collect request, please approve when it comes.",
      "suspicious", indicators={}, want_signal="collect_to_receive_bait")

# --- junk never crashes ---
for junk in ("", "   ", "🙏🙏🙏", "a" * 5000, "upi://", "http://",
             "upi://pay", "upi://pay?", "upi://mandate?pa=x@ybl",
             "upi://pay?pa=%%%&am=abc", "upi://pay?pa=a@ybl&am=1&pa=b@ybl"):
    v, s, sg, c, f = run_signal_engine(junk, "text", INDICATORS)
    assert v in ("danger", "suspicious", "no_known_risk"), junk

# --- H12 external-review battery (all five reproduced, then fixed) ---
check("H12.1 benign parcel notice clean",
      "Your parcel will be delivered tomorrow.", "no_known_risk",
      indicators={}, forbid_signal="script_digital_arrest")
check("H12.2 benign police/army sentence clean",
      "The police station is next to the army canteen.", "no_known_risk",
      indicators={})
check("H12.3 OTP request bypass flags",
      "Please send me your OTP. Do not share it with anyone else.",
      "suspicious", indicators={}, want_signal="credential_request")
check("H12.3b OTP awareness SMS stays clean",
      "Never share your OTP with anyone. Bank kabhi OTP nahi maangta. -SBI",
      "no_known_risk", indicators={}, forbid_signal="credential_request")
check("H12.4 ordinary mode=01 pay QR clean (NPCI: mode=01 = QR-initiated, not collect)",
      "upi://pay?pa=merchant123@ybl&pn=Kirana%20Store&am=250&mode=01",
      "no_known_risk", itype="qr_text", indicators={},
      forbid_signal="upi_collect_request")


# --- H12+ intent mismatch (the differentiator): expectation vs payload action ---
def check_intent(name, payload, intent, want_verdict, want_signal=None, forbid_signal=None):
    global PASS
    v, s, sigs, _, _f = run_signal_engine(payload, "qr_text", {}, expected_intent=intent)
    ids = [x["id"] for x in sigs]
    ok = v == want_verdict and (not want_signal or want_signal in ids)         and (not forbid_signal or forbid_signal not in ids)
    print(("ok " if ok else "FAIL"), f"{name}: verdict={v} signals={ids}")
    if not ok:
        sys.exit(f"FAILED: {name}")
    PASS += 1

check_intent("intent: clean pay-QR but user expected to RECEIVE",
             "upi://pay?pa=merchant123@ybl&pn=Store&am=15000&cu=INR&mode=01",
             "receive", "suspicious", want_signal="intent_mismatch")
check_intent("intent: collect + expected receive escalates",
             "upi://collect?pa=refund.helpdesk@okaxis&am=15000",
             "receive", "danger", want_signal="intent_mismatch")
check_intent("intent: normal shopping (pay+pay) stays clean",
             "upi://pay?pa=merchant123@ybl&am=250", "pay",
             "no_known_risk", forbid_signal="intent_mismatch")
check_intent("intent: no intent given = unchanged behavior",
             "upi://pay?pa=merchant123@ybl&am=250", None,
             "no_known_risk", forbid_signal="intent_mismatch")

print("ok  junk inputs survive")
PASS += 1

# --- H14 external-review battery: clause-level semantics -------------------
# benign — negation, reported speech, self-help, legit agent flows
check("H14 benign: WFH routine sentence",
      "I work from home every Friday.", "no_known_risk", indicators={},
      forbid_signal="script_job_scam")
check("H14 benign: awareness workshop (reported speech)",
      "Our school is holding a cyber crime awareness workshop.",
      "no_known_risk", indicators={}, forbid_signal="script_digital_arrest")
check("H14 benign: negated demand ('do not send money')",
      "Your refund is approved. Do not send money to anyone.",
      "no_known_risk", indicators={}, forbid_signal="advance_fee_refund")
check("H14 benign: negated charge ('no delivery charge')",
      "Your prize has shipped. No delivery charge is payable.",
      "no_known_risk", indicators={}, forbid_signal="advance_fee_refund")
check("H14 benign: password self-help question",
      "How do I reset my password?", "no_known_risk", indicators={},
      forbid_signal="credential_request")
check("H14 benign: OTP to delivery agent (legit platform flow)",
      "आपका पार्सल आज शाम 6 बजे तक पहुँचेगा। delivery boy को message वाला OTP दिखा दें।",
      "no_known_risk", indicators={}, forbid_signal="credential_request")
check("H14 benign: OTP to Ola driver (legit platform flow)",
      "Ola driver 2 min में पहुँच रहा है। OTP 4412 driver को बताएँ।",
      "no_known_risk", indicators={}, forbid_signal="credential_request")
check("H14 benign: lecture DESCRIBING digital arrest",
      "Aaj college me cyber safety lecture tha, professor ne bataya ki digital arrest "
      "wale CBI bolke darate hain aur paise mangte hain.",
      "no_known_risk", indicators={}, forbid_signal="script_digital_arrest")
# harmful — the safety-advice suffix must not launder the ask
check("H14 harmful: polite forward-the-code + advice suffix",
      "Kindly forward the one-time code you just received to this chat. "
      "Do not share it with anyone else.",
      "suspicious", indicators={}, want_signal="credential_request")
check("H14 harmful: negated OTP but password requested next sentence",
      "Never share your OTP. Send me your password to restore access.",
      "suspicious", indicators={}, want_signal="credential_request")
check("H14 harmful: remote-access request",
      "Anydesk download karke 9-digit code bata dijiye, hum aapka KYC ghar baithe kar denge.",
      "suspicious", indicators={}, want_signal="credential_request")
# held-out v2 miss families, generalized (not exact-string patches)
check("H14 v2-miss: TRAI SIM deactivation + fee",
      "This is TRAI. Your SIM will be deactivated in 2 hours due to illegal activity. "
      "Press 1 and pay the verification fee to keep your number active.",
      "danger", indicators={}, want_signal="script_kyc_expiry")
check("H14 v2-miss: chain-forward code bait",
      "To activate WhatsApp Gold forward this message to 10 groups and enter the "
      "verification code we sent you here: wa-gold.vip",
      "danger", indicators={}, want_signal="chain_forward_bait")
check("H14 v2-miss: .apk sideload lure",
      "क्रेडिट कार्ड के points आज expire हो रहे हैं! points को cash में बदलने के लिए "
      "app download करें: points-redeem.apk",
      "suspicious", indicators={}, want_signal="apk_sideload")
check("H14 v2-miss: brand-subdomain lookalike (swiggy)",
      "Your Swiggy order #8812 could not be delivered. Reschedule at "
      "swiggy-redeliver.xyz within 6 hours or order stands cancelled.",
      "danger", indicators={}, want_signal="lookalike_domain")
check("H14 v2-miss: family emergency + isolation",
      "URGENT: Your son met with an accident, admitted in hospital. Send 20000 "
      "immediately for operation on this GPay number. Don't call, he is in ICU.",
      "danger", indicators={}, want_signal="family_emergency_pressure")
check("H14 v2-miss: victim-voiced police video call",
      "पापा को video call पर पुलिस वर्दी वाले ने कहा कि भाई पकड़ा गया है, "
      "अभी 40 हज़ार भेजो नहीं तो FIR होगी। पैसे भेज दें क्या?",
      "danger", indicators={}, want_signal="family_emergency_pressure")
check("H14 ambiguous: 'new number' family ask -> verify, not convict",
      "Hi Dad, this is my new number. My phone broke. Please transfer 8000 to my "
      "friend. I will explain tonight.",
      "suspicious", indicators={}, want_signal="unverified_family_request",
      forbid_signal="script_digital_arrest")

# --- H14 facts pipeline: same QR ⇒ same facts, expectation only gates mismatch
_PAY_QR = "upi://pay?pa=ramlal@okaxis&pn=Ramlal%20Kirana&am=120"
check("H14 facts: pay QR + expect pay — facts parsed, no mismatch",
      _PAY_QR, "no_known_risk", itype="qr_text", indicators={},
      expected_intent="pay", forbid_signal="intent_mismatch",
      want_fact={"parse.status": "valid", "parse.action": "pay",
                 "parse.amount": "120", "parse.payee_vpa": "ramlal@okaxis",
                 "money_direction": "out_of_your_account"})
check("H14 facts: SAME QR + expect receive — same facts, mismatch fires",
      _PAY_QR, "suspicious", itype="qr_text", indicators={},
      expected_intent="receive", want_signal="intent_mismatch",
      want_fact={"parse.status": "valid", "parse.action": "pay",
                 "parse.amount": "120", "parse.payee_vpa": "ramlal@okaxis",
                 "money_direction": "out_of_your_account"})
check("H14 facts: incomplete URI (no payee) is not a valid pay claim",
      "upi://pay?pn=Store&am=500", "no_known_risk", itype="qr_text",
      indicators={}, forbid_signal="intent_mismatch",
      want_fact={"parse.status": "incomplete", "money_direction": "unknown"})
check("H14 facts: incomplete URI + expect receive — no mismatch without a parsed request",
      "upi://pay?pn=Store&am=500", "no_known_risk", itype="qr_text",
      indicators={}, expected_intent="receive", forbid_signal="intent_mismatch")
check("H14 facts: unsupported action stays unknown",
      "upi://mandate?pa=x@ybl&am=99", "no_known_risk", itype="qr_text",
      indicators={}, want_fact={"parse.status": "unsupported"})
check("H14 facts: invalid amount never guessed",
      "upi://pay?pa=xy@ybl&am=12,000", "no_known_risk", itype="qr_text",
      indicators={}, want_fact={"parse.status": "valid", "parse.amount": None})
check("H14 facts: two differing URIs never merge amounts",
      "upi://pay?pa=a@ybl&am=100 upi://pay?pa=b@ybl&am=900",
      "no_known_risk", itype="qr_text", indicators={},
      want_fact={"parse.status": "multiple", "parse.amount": None})
check("H14 facts: conflicting duplicate params = malformed",
      "upi://pay?pa=a@ybl&am=1&pa=b@ybl", "no_known_risk", itype="qr_text",
      indicators={}, want_fact={"parse.status": "malformed"})

print(f"\nALL {PASS} CHECKS PASSED")

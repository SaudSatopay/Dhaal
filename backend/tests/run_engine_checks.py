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
          want_signal=None, want_category=None, forbid_signal=None):
    global PASS
    verdict, score, signals, category = run_signal_engine(
        payload, itype, indicators if indicators is not None else INDICATORS,
        allow_network=False,
    )
    ids = [s["id"] for s in signals]
    ok = verdict == want_verdict
    if want_signal:
        ok = ok and want_signal in ids
    if forbid_signal:
        ok = ok and forbid_signal not in ids
    if want_category:
        ok = ok and category == want_category
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
for junk in ("", "   ", "🙏🙏🙏", "a" * 5000, "upi://", "http://"):
    v, s, sg, c = run_signal_engine(junk, "text", INDICATORS)
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

print("ok  junk inputs survive")
PASS += 1

print(f"\nALL {PASS} CHECKS PASSED")

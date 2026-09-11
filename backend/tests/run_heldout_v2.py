# Held-out battery v2 — 60 cases written AFTER the rules froze (post aa7f715).
# Discipline: authored from scam typology (1930/RBI/news categories), not from
# the pattern tables; runs ONCE against PROD; misses are published unedited in
# docs/EVAL.md and the raw run lands in docs/heldout_v2.json. Fixing a miss
# never edits this file's grade — fixes go to the NEXT fresh battery.
#
# Grading (pre-declared):
#   flag    -> pass if verdict in {danger, suspicious}
#   clean   -> pass if verdict == no_known_risk AND needs_context is null
#   context -> pass if needs_context is non-null
import json, sys, time, urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Devanagari on Windows consoles

API = "https://dhaal-api.vercel.app/api/check"
OUT = Path(__file__).resolve().parents[2] / "docs" / "heldout_v2.json"

# (id, expect, type, expected_intent, payload)
CASES = [
    # ---- SCAM: digital arrest / coercion (5)
    ("s01", "flag", "text", None, "मैं CBI officer बोल रहा हूँ। आपके आधार से money laundering हुई है। गिरफ़्तारी से बचना है तो 50,000 RTGS करें, वरना आज शाम टीम आएगी।"),
    ("s02", "flag", "text", None, "FedEx parcel me drugs mile hain aapke naam par. Mumbai police cyber cell ko call transfer kar raha hoon. Case band karne ke liye security deposit 25000 bhejna hoga, skype par aao."),
    ("s03", "flag", "text", None, "This is TRAI. Your SIM will be deactivated in 2 hours due to illegal activity. Press 1 and pay the verification fee to keep your number active."),
    ("s04", "flag", "text", None, "पापा को video call पर पुलिस वर्दी वाले ने कहा कि भाई पकड़ा गया है, अभी 40 हज़ार भेजो नहीं तो FIR होगी। पैसे भेज दें क्या?"),
    ("s05", "flag", "text", None, "Aapka bijli connection aaj raat 9:30 baje disconnect ho jayega. Turant electricity officer ko is number par call karke recharge karein."),
    # ---- SCAM: KYC / phishing links (6)
    ("s06", "flag", "text", None, "Dear customer your PNB account has been suspended. Update PAN card immediately click http://pnb-kyc-verify.in-login.top"),
    ("s07", "flag", "text", None, "प्रिय ग्राहक, आपका Paytm wallet 24 घंटे में बंद हो जाएगा। KYC के लिए इस नंबर पर तुरंत संपर्क करें।"),
    ("s08", "flag", "text", None, "Your electricity bill is overdue. Pay now to avoid disconnection tonight: bit.ly/3xEleBill"),
    ("s09", "flag", "text", None, "SBI YONO account temporary block hua hai. Reactivate karne ke liye apna netbanking password aur ATM pin verify karein is link par: sbi-yono.online"),
    ("s10", "flag", "text", None, "Income Tax refund of Rs 15,490 approved. Verify your bank account at incometax-refund.co.in to receive credit today."),
    ("s24", "flag", "text", None, "Dear user your Netflix subscription failed. Update payment at netflix-billing-update.com to avoid losing your account."),
    # ---- SCAM: collect / QR / intent tricks (4)
    ("s11", "flag", "qr", "receive", "upi://pay?pa=refund.olx7@okicici&pn=OLX%20Refund&am=9500"),
    ("s12", "flag", "text", None, "Paytm ne aapko ₹5,000 bheja hai. Amount receive karne ke liye yeh QR scan karein aur apna UPI PIN daalein."),
    ("s13", "flag", "qr", None, "upi://pay?pa=kbcwinner2026@oksbi&pn=KBC%20Lucky%20Draw&am=4999"),
    ("s14", "flag", "text", None, "Sir main aapki gaadi advance booking karna chahta hoon, main aapko abhi 15000 ki collect request bhejta hoon, aap approve kar dena, paisa aapke account me aa jayega."),
    # ---- SCAM: OTP / credential / remote access (4)
    ("s15", "flag", "text", None, "Your SBI OTP is 445211. Share this code with our executive to complete your cashback claim."),
    ("s16", "flag", "text", None, "बैंक से बोल रहे हैं, आपका debit card block हुआ है। unblock के लिए card number और CVV बताइए।"),
    ("s17", "flag", "text", None, "Anydesk download karke 9-digit code bata dijiye, hum aapka KYC ghar baithe kar denge."),
    ("s18", "flag", "text", None, "To activate WhatsApp Gold forward this message to 10 groups and enter the verification code we sent you here: wa-gold.vip"),
    # ---- SCAM: advance fee / prize / job / loan / refund (5)
    ("s19", "flag", "text", None, "Congratulations! Your number won ₹25,00,000 in Jio Lucky Draw. To claim deposit processing fee ₹6,999 on gpay number 9811223344."),
    ("s20", "flag", "text", None, "Amazon पर part time job — रोज़ 2000-5000 कमाएँ। पहले 3 task free, फिर registration ₹500। अभी telegram पर join करें।"),
    ("s21", "flag", "text", None, "Aapka loan 2 lakh approve ho gaya hai bina document ke. File charge sirf 1999 pehle jama karein, uske baad amount transfer hoga."),
    ("s22", "flag", "text", None, "Flipkart order cancelled, refund initiated. To receive ₹3,499 refund scan the QR and enter UPI PIN when prompted."),
    ("s23", "flag", "text", None, "क्रेडिट कार्ड के points आज expire हो रहे हैं! points को cash में बदलने के लिए app download करें: points-redeem.apk"),
    # ---- SCAM: impersonation / lookalike / emergency (6)
    ("s25", "flag", "text", None, "hdfc.support.care@ybl ko 1 rupya bhejke account verify karo, phir pura refund milega."),
    ("s26", "flag", "text", None, "Your Swiggy order #8812 could not be delivered. Reschedule at swiggy-redeliver.xyz within 6 hours or order stands cancelled."),
    ("s27", "flag", "text", None, "आपकी बेटी का admission form incomplete है। fine ₹1,150 आज ही भरें वरना seat cancel हो जाएगी: muj-admissions.site"),
    ("s28", "flag", "qr", None, "upi://pay?pa=airtel-recharge@okaxis&pn=Airtel%20Official"),
    ("s29", "flag", "voice_transcript", None, "haan sir main customer care se bol raha hoon aapke refund ke liye google pay kholiye aur jo request aayi hai usme pin daal dijiye bas refund credit ho jayega"),
    ("s30", "flag", "text", None, "URGENT: Your son met with an accident, admitted in hospital. Send 20000 immediately for operation on this GPay number. Don't call, he is in ICU."),
    # ---- BENIGN: must stay clean (24)
    ("b01", "clean", "text", None, "Dear Customer, OTP for txn of INR 2,500.00 at Amazon Pay is 887213. Valid for 10 mins. DO NOT share with anyone. -HDFC Bank"),
    ("b02", "clean", "text", None, "माँ ने कहा है शाम को 2000 भेज देना दूध वाले के लिए, PhonePe पर ही भेजना।"),
    ("b03", "clean", "text", None, "Your a/c XX4432 credited INR 15,000 on 11-Sep-26 by a/c linked to mobile 98XXXXXX10 (IMPS Ref 551209). -SBI"),
    ("b04", "clean", "qr", "pay", "upi://pay?pa=zomato@paytm&pn=Zomato&am=349"),
    ("b05", "clean", "text", None, "Aaj college me cyber safety lecture tha, professor ne bataya ki digital arrest wale CBI bolke darate hain aur paise mangte hain. Crazy stuff yaar."),
    ("b06", "clean", "text", None, "बिजली का बिल आ गया है 1,240 का, due date 20 सितम्बर है। BBPS से भर दूँगा weekend पर।"),
    ("b07", "clean", "text", None, "Your Swiggy order is out for delivery. Rider Ramesh will reach in 12 mins. Enjoy your meal!"),
    ("b08", "clean", "text", None, "Rent reminder: please transfer ₹18,000 to landlord@okhdfcbank by the 5th. Same as every month."),
    ("b09", "clean", "text", None, "Bhai kal match ke tickets book kar liye, tera hissa 850 hua, jab time mile bhej dena. No rush."),
    ("b10", "clean", "text", None, "Dear customer, your Jio recharge of Rs 299 is successful. Validity 28 days. Thank you."),
    ("b11", "clean", "text", None, "आपका पार्सल आज शाम 6 बजे तक पहुँचेगा। delivery boy को message वाला OTP दिखा दें।"),
    ("b12", "clean", "text", None, "Team dinner split: everyone pays 460 to Rahul, UPI rahul.sharma22@oksbi. I'll collect cash from the interns."),
    ("b13", "clean", "text", None, "SBI: आपके खाते से 550 debit हुआ ATM WD। यदि यह आपने नहीं किया तो तुरंत 1930 पर कॉल करें।"),
    ("b14", "clean", "text", None, "Netflix: Your plan payment of ₹199 was successful. Next billing date 11 Oct 2026."),
    ("b15", "clean", "text", None, "Yaar mera KYC pending tha isliye main khud branch gaya tha, ho gaya ab. Tension nahi."),
    ("b16", "clean", "text", None, "Reminder: Society maintenance ₹2,100 due by 15th. Pay at the office or the society QR near the lift. — Secretary"),
    ("b17", "clean", "text", None, "Ola driver 2 min में पहुँच रहा है। OTP 4412 driver को बताएँ।"),
    ("b18", "clean", "text", None, "Credited: INR 899.00 refund from Flipkart for order OD1123 to your original payment method. No action needed."),
    ("b19", "clean", "text", None, "Police verification passport ke liye kal aayegi ghar pe, documents ready rakhna."),
    ("b20", "clean", "qr", "pay", "upi://pay?pa=9812345678@ybl&pn=Sunita%20Devi"),
    ("b21", "clean", "text", None, "Big Billion Days: Up to 80% off on electronics. Sale ends tonight. Shop now on the Flipkart app!"),
    ("b22", "clean", "text", None, "नानी की दवाई के 1,500 भेज दिए हैं तेरे PhonePe पर, मिल गए?"),
    ("b23", "clean", "text", None, "Your DTH recharge will expire tomorrow. Recharge with the Rs 350 plan to continue services. -TataPlay"),
    ("b24", "clean", "text", None, "Interview scheduled Friday 11 AM at our Andheri office. Carry resume and ID proof. — HR, Infosys"),
    # ---- INSUFFICIENT: must ask, never clear (6)
    ("c01", "context", "text", None, "9812345678"),
    ("c02", "context", "text", None, "sunita.devi55@ybl"),
    ("c03", "context", "text", None, "kal bhej dena"),
    ("c04", "context", "text", None, "is this safe?"),
    ("c05", "context", "text", None, "+91 99887 76655"),
    ("c06", "context", "text", None, "scan karu?"),
]

def call(case):
    cid, expect, typ, intent, payload = case
    body = json.dumps({"type": typ, "payload": payload, "lang": "hi",
                       "expected_intent": intent}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json"})
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                return {"error": str(e)}
            time.sleep(3)

def grade(expect, d):
    if "error" in d:
        return False
    v, nc = d.get("verdict"), d.get("needs_context")
    if expect == "flag":
        return v in ("danger", "suspicious")
    if expect == "clean":
        return v == "no_known_risk" and not nc
    return bool(nc)  # context

rows, t0 = [], time.time()
for i, case in enumerate(CASES, 1):
    cid, expect, typ, intent, payload = case
    d = call(case)
    p = grade(expect, d)
    rows.append({
        "id": cid, "expect": expect, "type": typ, "expected_intent": intent,
        "payload": payload, "verdict": d.get("verdict"), "score": d.get("score"),
        "signals": [s["id"] for s in d.get("signals", [])],
        "needs_context": (d.get("needs_context") or {}).get("reason"),
        "error": d.get("error"), "pass": p,
    })
    print(f"[{i:2}/60] {cid} {expect:7} -> {d.get('verdict') or d.get('error'):>13} "
          f"{d.get('score', ''):>3} {'ok' if p else 'MISS'}")

n = lambda e: [r for r in rows if r["expect"] == e]
hit = lambda rs: sum(r["pass"] for r in rs)
summary = {
    "battery": "heldout_v2", "run_at_ist": "2026-09-11", "target": API,
    "frozen_at_commit": "aa7f715", "runs": 1,
    "total": f"{hit(rows)}/60",
    "scam": f"{hit(n('flag'))}/{len(n('flag'))}",
    "benign_clean": f"{hit(n('clean'))}/{len(n('clean'))}",
    "insufficient": f"{hit(n('context'))}/{len(n('context'))}",
    "seconds": round(time.time() - t0),
}
OUT.write_text(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n== HELD-OUT v2 (single run, unedited) ==")
for k, v in summary.items():
    print(f"  {k}: {v}")
print(f"\nraw -> {OUT}")
misses = [r for r in rows if not r["pass"]]
if misses:
    print(f"\nmisses ({len(misses)}):")
    for r in misses:
        print(f"  {r['id']} [{r['expect']}] got {r['verdict']} {r['score']} {r['signals']} :: {r['payload'][:70]}")

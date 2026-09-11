// Demo example chips — strings MUST stay byte-identical to backend/fixtures.py
// (Saud owns fixture content; update here if his H3–H5 fixtures pass changes them).

import type { LangText } from "./lang";

export const EXAMPLES: { label: LangText; text: string }[] = [
  {
    label: { hi: "KYC धोखा SMS", en: "KYC scam SMS" },
    text:
      "प्रिय ग्राहक, आपका SBI खाता 24 घंटे में बंद हो जाएगा। तुरंत KYC अपडेट करें: " +
      "http://sbi-kyc-update.xyz/verify",
  },
  {
    label: { hi: "असली bank SMS", en: "genuine bank SMS" },
    text:
      "Dear Customer, Rs.2,500.00 credited to A/c XX4321 on 11-09-26 by UPI ref 625489. " +
      "Avl Bal Rs.18,240.00 -SBI",
  },
  {
    label: { hi: "₹15,000 collect request", en: "collect QR (decoded)" },
    text: "upi://collect?pa=refund.helpdesk@okaxis&pn=SBI%20Refunds&am=15000&cu=INR",
  },
  {
    label: { hi: "रिपोर्ट किया नंबर", en: "reported number" },
    text: "+919876500001",
  },
];

// /learn simulator pool — REAL corpus only: demo fixtures (backend/fixtures.py)
// plus the OTP-delivery legit shape the engine explicitly handles (H11 sweep).
// The engine's verdict is the ground truth for scoring — nothing invented.
export const LEARN_POOL: string[] = [
  EXAMPLES[0].text, // KYC scam SMS
  EXAMPLES[1].text, // genuine credit SMS
  EXAMPLES[2].text, // ₹15,000 collect URI
  // digital-arrest call script (backend/fixtures.py beat 4, verbatim)
  "मैं मुंबई साइबर क्राइम ब्रांच से इंस्पेक्टर बोल रहा हूँ। आपके आधार से एक parcel पकड़ा गया है। गिरफ़्तारी से बचना है तो अभी वेरिफिकेशन फीस भेजिए, किसी को बताइए मत।",
  // legit OTP delivery — the engine suppresses credential_request on this shape
  "Dear Customer, 482913 is your OTP for txn of Rs.1,499.00 at Amazon. DO NOT share this OTP with anyone. -SBI",
];

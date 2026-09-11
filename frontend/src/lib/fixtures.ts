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

// Demo example chips — strings MUST stay byte-identical to backend/fixtures.py
// (Saud owns fixture content; update here if his H3–H5 fixtures pass changes them).

export const EXAMPLES: { label_hi: string; label_en: string; text: string }[] = [
  {
    label_hi: "KYC धोखा SMS",
    label_en: "KYC scam SMS",
    text:
      "प्रिय ग्राहक, आपका SBI खाता 24 घंटे में बंद हो जाएगा। तुरंत KYC अपडेट करें: " +
      "http://sbi-kyc-update.xyz/verify",
  },
  {
    label_hi: "असली bank SMS",
    label_en: "genuine bank SMS",
    text:
      "Dear Customer, Rs.2,500.00 credited to A/c XX4321 on 11-09-26 by UPI ref 625489. " +
      "Avl Bal Rs.18,240.00 -SBI",
  },
  {
    label_hi: "₹15,000 collect request",
    label_en: "collect QR (decoded)",
    text: "upi://collect?pa=refund.helpdesk@okaxis&pn=SBI%20Refunds&am=15000&cu=INR",
  },
  {
    label_hi: "रिपोर्ट किया नंबर",
    label_en: "reported number",
    text: "+919876500001",
  },
];

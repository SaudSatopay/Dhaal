// Hindi-first UI label maps for contract enums. Verdict copy rule (docs/CONTRACTS.md):
// never render the word "safe" — the green state is "no KNOWN risk".
// `tone` keys the visual identity: danger/caution = hazard notice, clear = quiet chit.

import type { ScamCategory, SignalSource, Verdict } from "./types";

export const VERDICT_UI: Record<
  Verdict,
  { hi: string; en: string; hint_hi: string; tone: "danger" | "caution" | "clear" }
> = {
  danger: {
    hi: "खतरा",
    en: "DANGER",
    hint_hi: "रुक जाइए — पैसे मत भेजिए, कुछ मत भरिए",
    tone: "danger",
  },
  suspicious: {
    hi: "सावधान",
    en: "SUSPICIOUS",
    hint_hi: "आगे बढ़ने से पहले खुद पक्का कीजिए",
    tone: "caution",
  },
  no_known_risk: {
    hi: "कोई ज्ञात खतरा नहीं",
    en: "NO KNOWN RISK",
    hint_hi: "फिर भी नाम और नंबर खुद जाँच लें",
    tone: "clear",
  },
};

export const CATEGORY_UI: Record<ScamCategory, { hi: string; en: string }> = {
  kyc_expiry: { hi: "KYC धोखा", en: "KYC scam" },
  lottery: { hi: "लॉटरी धोखा", en: "Lottery scam" },
  digital_arrest: { hi: "डिजिटल अरेस्ट", en: "Digital arrest" },
  fake_collect: { hi: "नकली collect request", en: "Fake collect request" },
  electricity: { hi: "बिजली बिल धोखा", en: "Electricity bill scam" },
  olx_army: { hi: "OLX / आर्मी धोखा", en: "OLX / army scam" },
  customer_care: { hi: "नकली कस्टमर केयर", en: "Fake customer care" },
  other: { hi: "अन्य धोखा", en: "Other scam" },
};

// community wears the brand saffron — the flywheel IS the brand; engine wears ink;
// llm notes stay visibly weightless.
export const SOURCE_UI: Record<SignalSource, { hi: string; en: string; cls: string }> = {
  deterministic: {
    hi: "इंजन जाँच",
    en: "RULE ENGINE",
    cls: "border-ink text-ink",
  },
  community: {
    hi: "समुदाय",
    en: "COMMUNITY",
    cls: "border-saffdeep text-saffdeep",
  },
  llm_pattern: {
    hi: "AI संकेत",
    en: "0 VERDICT WEIGHT",
    cls: "border-inksoft text-inksoft border-dashed",
  },
};

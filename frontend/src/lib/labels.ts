// Hindi-first UI label maps for contract enums. Verdict copy rule (docs/CONTRACTS.md):
// never render the word "safe" — the green state is "no KNOWN risk".

import type { ScamCategory, SignalSource, Verdict } from "./types";

export const VERDICT_UI: Record<
  Verdict,
  { hi: string; en: string; hint_hi: string; icon: string; banner: string; ring: string }
> = {
  danger: {
    hi: "खतरा",
    en: "DANGER",
    hint_hi: "रुक जाइए — पैसे मत भेजिए, कुछ मत भरिए",
    icon: "🛑",
    banner: "bg-red-600 text-white",
    ring: "border-red-600",
  },
  suspicious: {
    hi: "सावधान",
    en: "SUSPICIOUS",
    hint_hi: "आगे बढ़ने से पहले खुद पक्का कीजिए",
    icon: "⚠️",
    banner: "bg-amber-500 text-black",
    ring: "border-amber-500",
  },
  no_known_risk: {
    hi: "कोई ज्ञात खतरा नहीं",
    en: "NO KNOWN RISK",
    hint_hi: "फिर भी नाम और नंबर खुद जाँच लें",
    icon: "🛡️",
    banner: "bg-emerald-600 text-white",
    ring: "border-emerald-600",
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

export const SOURCE_UI: Record<SignalSource, { hi: string; en: string; cls: string }> = {
  deterministic: {
    hi: "इंजन जाँच",
    en: "rule engine",
    cls: "bg-sky-100 text-sky-800 dark:bg-sky-900/60 dark:text-sky-200",
  },
  community: {
    hi: "समुदाय रिपोर्ट",
    en: "community",
    cls: "bg-purple-100 text-purple-800 dark:bg-purple-900/60 dark:text-purple-200",
  },
  llm_pattern: {
    hi: "AI संकेत",
    en: "AI note · 0 verdict weight",
    cls: "bg-neutral-200 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400",
  },
};

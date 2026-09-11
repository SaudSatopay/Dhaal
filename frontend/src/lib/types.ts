// Contract types — mirror docs/CONTRACTS.md exactly. Do not drift.

export type Verdict = "danger" | "suspicious" | "no_known_risk";

export type InputType = "text" | "url" | "upi" | "qr_text" | "voice_transcript";

export type SignalSource = "deterministic" | "community" | "llm_pattern";

export type ScamCategory =
  | "kyc_expiry"
  | "lottery"
  | "digital_arrest"
  | "fake_collect"
  | "electricity"
  | "olx_army"
  | "customer_care"
  | "job_scam"
  | "loan_fee"
  | "other";

export type Signal = {
  id: string;
  source: SignalSource;
  weight: number;
  title_en: string;
  title_hi: string;
  detail_en: string;
  detail_hi: string;
};

// H12+ structured "what they want" — derived deterministically from signals
export type Analysis = {
  claimed_identity?: string | null;
  asking_for?: { what: string; hi: string; amount?: string | number | null }[];
  money_direction?: "out_of_your_account" | "none_detected" | string;
  pressure?: { tag: string; hi: string }[];
};

export type ExpectedIntent = "pay" | "receive" | "verify" | null;

export type Check = {
  _id: string;
  input: { type: InputType; payload: string; lang: string };
  verdict: Verdict;
  score: number;
  signals: Signal[];
  explanation_hi: string;
  explanation_en: string;
  scam_category: ScamCategory | null;
  // H12+ additions (additive, backward-compatible)
  analysis?: Analysis | null;
  expected_intent?: ExpectedIntent;
  needs_context?: { reason: string; question_hi: string; question_en: string } | null;
  tts_audio_b64: string | null;
  mocked: boolean;
  created_at: string;
  guardian_request_id?: string;
};

export type TranscribeResult = {
  transcript: string;
  lang: string;
  mocked: boolean;
};

export type IndicatorType = "phone" | "upi" | "domain" | "script";

export type Report = {
  _id: string;
  payload: string;
  category: ScamCategory;
  note: string;
  city: string;
  status: "pending" | "verified" | "rejected";
  indicator_type: IndicatorType;
  created_at: string;
};

export type Indicator = {
  _id: string;
  type: IndicatorType;
  value: string;
  report_count: number;
  first_seen: string;
  category: ScamCategory;
};

export type GuardianLink = {
  _id: string;
  ward_name: string;
  guardian_name: string;
  guardian_phone?: string; // H12+: the STORED trusted number for "call my person"
  pair_code: string;
  created_at: string;
};

export type GuardianRequest = {
  _id: string;
  link_id: string;
  check_id: string;
  summary_hi: string;
  // guardian contract v2 (H11): EVERY ward check creates a request — risky ⇒
  // "pending" (needs Allow/Block), clean ⇒ "noted" (informational only).
  // verdict/score optional-guarded: pre-v2 rows in Atlas lack them.
  verdict?: Verdict;
  score?: number;
  status: "pending" | "allowed" | "blocked" | "noted";
  guardian_note: string;
  created_at: string;
};

export type Trends = {
  total_reports: number;
  by_category: { category: ScamCategory; count: number }[];
  by_day: { day: string; count: number }[];
  top_indicators: Indicator[];
  cities: { city: string; count: number }[];
  live_reports?: number;
};

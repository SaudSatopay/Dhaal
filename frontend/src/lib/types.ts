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

export type Check = {
  _id: string;
  input: { type: InputType; payload: string; lang: string };
  verdict: Verdict;
  score: number;
  signals: Signal[];
  explanation_hi: string;
  explanation_en: string;
  scam_category: ScamCategory | null;
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

export type Trends = {
  total_reports: number;
  by_category: { category: ScamCategory; count: number }[];
  by_day: { day: string; count: number }[];
  top_indicators: Indicator[];
  cities: { city: string; count: number }[];
  live_reports?: number;
};

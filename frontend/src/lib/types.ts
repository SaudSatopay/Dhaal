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

// H14 structured "what they want" — read straight off the parsed FACTS
export type Analysis = {
  claimed_identity?: string | null;
  asking_for?: { what: string; hi: string; amount?: string | number | null }[];
  money_direction?: "out_of_your_account" | "none_detected" | "unknown" | string;
  pressure?: { tag: string; hi: string }[];
  expectation?: string;
  missing?: string[];
};

export type ExpectedIntent = "pay" | "receive" | "verify" | null;

// H14 first-class assessment outcome: a risk verdict exists ONLY when the
// input was actually assessable. needs_context/unsupported ⇒ verdict null.
export type Assessment = "assessed" | "needs_context" | "unsupported_input";

export type ParseFacts = {
  status: "valid" | "incomplete" | "unsupported" | "malformed" | "multiple";
  action: string;
  payee_vpa: string | null;
  payee_name: string | null;
  amount: string | null;
  currency: string | null;
  uri_count: number;
} | null;

export type Facts = {
  input_kind: string;
  parse: ParseFacts;
  expectation: "pay" | "receive" | "verify" | "unknown";
  money_direction: "out_of_your_account" | "none_detected" | "unknown";
  claimed_identity: string | null;
  requested_actions: string[];
  evidence: { kind: string; span: string; sentence: number | null }[];
  pressure: string[];
  missing: string[];
};

export type Check = {
  _id: string;
  input: { type: InputType; payload: string; lang: string };
  assessment: Assessment;
  verdict: Verdict | null; // null whenever assessment !== "assessed"
  score: number;
  signals: Signal[];
  explanation_hi: string;
  explanation_en: string;
  explanation_source?: "llm" | "rules";
  scam_category: ScamCategory | null;
  // H12+/H14 additions (additive, backward-compatible)
  facts?: Facts;
  analysis?: Analysis | null;
  expected_intent?: ExpectedIntent;
  needs_context?: { reason: string; question_hi: string; question_en: string } | null;
  tts_audio_b64: string | null;
  mocked: boolean;
  community_data?: "live" | "degraded";
  timings?: { engine_ms: number; narration_ms: number; tts_ms: number; total_ms: number };
  created_at: string;
  guardian_request_id?: string;
  guardian_delivery?: "sent" | "sent_not_durable" | "unlinked";
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

// H14 create response: the guardian capability token appears ONCE here and is
// then stored only as a hash server-side. Codes are single-use + expiring.
export type GuardianLinkCreated = {
  link_id: string;
  ward_name: string;
  guardian_name: string;
  guardian_phone?: string; // H12+: the STORED trusted number for "call my person"
  pair_code: string;
  pair_code_expires_at: string;
  guardian_token: string;
  created_at: string;
};

// H14 claim response — the minimum the ward role needs, plus its own token.
export type GuardianLinkClaimed = {
  link_id: string;
  ward_token: string;
  ward_name: string;
  guardian_name: string;
  guardian_phone?: string;
};

export type GuardianRequest = {
  _id: string;
  check_id: string;
  summary_hi: string;
  assessment?: Assessment;
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

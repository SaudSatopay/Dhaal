// localStorage pairing state for guardian mode. Two roles, two keys, two
// CAPABILITY TOKENS (H14): the ward's token authorizes submitting checks to
// the guardian and polling its own requests; the guardian's token authorizes
// the inbox and decisions. Tokens live only here and in request HEADERS —
// never in URLs, QR codes, or server responses after minting.

// guardian_phone is the STORED trusted number (H12+) — the tel: button on a
// danger verdict dials THIS, never a number found inside a checked message.
export type WardPair = {
  link_id: string;
  ward_token: string; // absent on legacy pairings -> they must re-pair
  guardian_name: string;
  ward_name: string;
  guardian_phone?: string;
};
export type GuardianPair = {
  link_id: string;
  guardian_token: string;
  guardian_name: string;
  ward_name: string;
  pair_code: string;
  pair_code_expires_at?: string;
  guardian_phone?: string;
};

const WARD_KEY = "dhaal_ward_link";
const GUARDIAN_KEY = "dhaal_guardian_link";

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: unknown) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage unavailable (private mode etc.) — guardian mode just stays off
  }
}

// H14: a stored pairing without its capability token is a pre-token legacy
// pairing — the server will never honor it, so treat it as absent (the UI
// then shows the loud "not paired" state and the person re-pairs).
export const getWardPair = () => {
  const p = read<WardPair>(WARD_KEY);
  return p && p.ward_token ? p : null;
};
export const setWardPair = (p: WardPair | null) => write(WARD_KEY, p);
export const getGuardianPair = () => {
  const p = read<GuardianPair>(GUARDIAN_KEY);
  return p && p.guardian_token ? p : null;
};
export const setGuardianPair = (p: GuardianPair | null) => write(GUARDIAN_KEY, p);

// localStorage pairing state for guardian mode. Two roles, two keys:
// ward = the protected person (their /check sends ward_link_id),
// guardian = the family member whose inbox polls the link.

// guardian_phone is the STORED trusted number (H12+) — the tel: button on a
// danger verdict dials THIS, never a number found inside a checked message.
export type WardPair = {
  link_id: string;
  guardian_name: string;
  ward_name: string;
  guardian_phone?: string;
};
export type GuardianPair = {
  link_id: string;
  guardian_name: string;
  ward_name: string;
  pair_code: string;
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

export const getWardPair = () => read<WardPair>(WARD_KEY);
export const setWardPair = (p: WardPair | null) => write(WARD_KEY, p);
export const getGuardianPair = () => read<GuardianPair>(GUARDIAN_KEY);
export const setGuardianPair = (p: GuardianPair | null) => write(GUARDIAN_KEY, p);

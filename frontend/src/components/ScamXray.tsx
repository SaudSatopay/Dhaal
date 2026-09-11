"use client";

// SCAM X-RAY (H15) — the message itself becomes the exhibit. Every evidence
// span the engine matched is highlighted IN PLACE in the original text; tap a
// highlight and Dhaal explains why that exact phrase matters. Nothing here is
// generated: spans come verbatim from facts.evidence (the deterministic
// engine's matches), destinations from visible identifiers in the text. A
// message about scams (reported speech) highlights as INFO, not as a threat —
// honesty is part of the show.

import { useMemo, useState } from "react";
import type { Facts } from "@/lib/types";
import { S_XRAY } from "@/lib/labels";
import { pick, type Lang, type LangText } from "@/lib/lang";

type Tone = "danger" | "caution" | "info";

type KindUI = { label: LangText; why: LangText; tone: Tone };

const KIND_UI: Record<string, KindUI> = {
  credential_request: { label: S_XRAY.kCred, why: S_XRAY.wCred, tone: "danger" },
  remote_access: { label: S_XRAY.kRemote, why: S_XRAY.wRemote, tone: "danger" },
  fee_demand: { label: S_XRAY.kFee, why: S_XRAY.wFee, tone: "danger" },
  advance_fee: { label: S_XRAY.kFee, why: S_XRAY.wFee, tone: "danger" },
  collect_approve: { label: S_XRAY.kCollect, why: S_XRAY.wCollect, tone: "danger" },
  coercion_extortion: { label: S_XRAY.kThreat, why: S_XRAY.wThreat, tone: "danger" },
  threat_framing: { label: S_XRAY.kThreat, why: S_XRAY.wThreat, tone: "danger" },
  family_emergency: { label: S_XRAY.kFamily, why: S_XRAY.wFamily, tone: "danger" },
  apk_file: { label: S_XRAY.kApk, why: S_XRAY.wApk, tone: "danger" },
  urgency_framing: { label: S_XRAY.kUrgency, why: S_XRAY.wUrgency, tone: "caution" },
  secrecy_pressure: { label: S_XRAY.kSecrecy, why: S_XRAY.wSecrecy, tone: "caution" },
  new_number_request: { label: S_XRAY.kNewNum, why: S_XRAY.wNewNum, tone: "caution" },
  chain_forward: { label: S_XRAY.kChain, why: S_XRAY.wChain, tone: "caution" },
  reported_speech: { label: S_XRAY.kReported, why: S_XRAY.wReported, tone: "info" },
  credential_agent_flow: { label: S_XRAY.kAgentOk, why: S_XRAY.wAgentOk, tone: "info" },
  credential_delivery: { label: S_XRAY.kDelivery, why: S_XRAY.wDelivery, tone: "info" },
  destination: { label: S_XRAY.kDest, why: S_XRAY.wDest, tone: "caution" },
  category: { label: S_XRAY.kPattern, why: S_XRAY.wPattern, tone: "danger" },
};

const TONE_MARK: Record<Tone, string> = {
  danger: "bg-dangertint border-b-2 border-danger text-dangerdeep",
  caution: "bg-cautiontint border-b-2 border-caution text-cautiondeep",
  info: "bg-cleartint border-b-2 border-clear text-cleardeep",
};
const TONE_CHIP: Record<Tone, string> = {
  danger: "border-danger text-dangerdeep",
  caution: "border-caution text-cautiondeep",
  info: "border-clear text-cleardeep",
};

function kindUI(kind: string): KindUI | null {
  if (KIND_UI[kind]) return KIND_UI[kind];
  if (kind.startsWith("category:")) return KIND_UI.category;
  return null; // unknown evidence kinds simply don't highlight — never guess
}

type Seg = { text: string; kind?: string };
type Match = { start: number; end: number; kind: string };

// visible identifiers the money/answer would flow to — factual, not accusatory
const DEST_RE =
  /https?:\/\/[^\s"'<>]+|\b[a-z0-9][a-z0-9.\-_]{1,60}@[a-z][a-z0-9]{1,64}\b|(?<!\d)\+?\d[\d\s-]{8,14}\d(?!\d)/gi;

function buildSegments(payload: string, evidence: Facts["evidence"]): Seg[] {
  const matches: Match[] = [];
  const low = payload.toLowerCase();
  for (const ev of evidence) {
    if (!ev.span || !kindUI(ev.kind)) continue;
    // spans may be composites like "a + b" from the engine — try parts too
    for (const piece of [ev.span, ...ev.span.split(" + ")]) {
      const needle = piece.trim().toLowerCase();
      if (needle.length < 2) continue;
      const idx = low.indexOf(needle);
      if (idx >= 0) {
        matches.push({ start: idx, end: idx + needle.length, kind: ev.kind });
        break;
      }
    }
  }
  for (const m of payload.matchAll(DEST_RE)) {
    if (m.index !== undefined && m[0].length >= 6) {
      matches.push({ start: m.index, end: m.index + m[0].length, kind: "destination" });
    }
  }
  // earlier + longer wins; overlaps dropped so the text renders exactly once
  matches.sort((a, b) => a.start - b.start || b.end - a.end);
  const flat: Match[] = [];
  for (const m of matches) {
    if (!flat.length || m.start >= flat[flat.length - 1].end) flat.push(m);
  }
  const segs: Seg[] = [];
  let pos = 0;
  for (const m of flat) {
    if (m.start > pos) segs.push({ text: payload.slice(pos, m.start) });
    segs.push({ text: payload.slice(m.start, m.end), kind: m.kind });
    pos = m.end;
  }
  if (pos < payload.length) segs.push({ text: payload.slice(pos) });
  return segs;
}

export default function ScamXray({
  payload,
  evidence,
  lang,
}: {
  payload: string;
  evidence: Facts["evidence"];
  lang: Lang;
}) {
  const [active, setActive] = useState<string | null>(null);
  const segs = useMemo(
    () => buildSegments(payload, evidence ?? []),
    [payload, evidence]
  );
  const marked = segs.filter((s) => s.kind);
  // a QR/URI-only payload has no prose to x-ray; skip rather than decorate
  if (marked.length === 0 || /^upi:\/\//i.test(payload.trim())) return null;

  const activeUI = active ? kindUI(active) : null;

  return (
    <div className="border-b-2 border-line p-4">
      <h3 className="plate text-inksoft">
        {pick(lang, S_XRAY.title)[0]} · {pick(lang, S_XRAY.title)[1]}
      </h3>
      <div className="mt-2 border-2 border-ink bg-paper2 p-3">
        <p className="max-h-52 overflow-y-auto whitespace-pre-wrap break-words text-[15px] leading-relaxed">
          {segs.map((s, i) =>
            s.kind ? (
              <mark
                key={i}
                role="button"
                tabIndex={0}
                onClick={() => setActive(active === s.kind ? null : s.kind!)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setActive(active === s.kind ? null : s.kind!);
                  }
                }}
                className={`cursor-pointer rounded-none px-0.5 font-semibold ${TONE_MARK[kindUI(s.kind)!.tone]} ${
                  active === s.kind ? "outline outline-2 outline-ink" : ""
                }`}
              >
                {s.text}
              </mark>
            ) : (
              <span key={i}>{s.text}</span>
            )
          )}
        </p>
      </div>
      {/* tap-to-explain caption — the evidence speaks */}
      {activeUI ? (
        <div
          className={`mt-2 border-2 bg-paper p-2.5 ${TONE_CHIP[activeUI.tone]}`}
          aria-live="polite"
        >
          <p className="plate">{pick(lang, activeUI.label)[0]} · {pick(lang, activeUI.label)[1]}</p>
          <p className="mt-1 text-sm font-semibold leading-snug">
            {pick(lang, activeUI.why)[0]}
          </p>
          <p className="mt-0.5 text-xs leading-snug text-inksoft">
            {pick(lang, activeUI.why)[1]}
          </p>
        </div>
      ) : (
        <p className="plate mt-1.5 text-inksoft">{pick(lang, S_XRAY.hint)[0]}</p>
      )}
    </div>
  );
}

"use client";

// SCAM X-RAY (H16, precision rework) — the message itself becomes the
// exhibit. Every finding highlights at its EXACT backend-reported position:
// evidence start/end are UTF-16 code units, i.e. native JS string indices, so
// payload.slice(start, end) is the ground truth — no client-side searching,
// no first-occurrence guessing, Hindi and emoji included. Overlapping
// findings are preserved: a segment can carry several findings and the tap
// sheet lists every one. `factual` records (destinations, delivery context,
// legit flows) render as neutral information — extraction is never an
// accusation, and a destination is never claimed verified or malicious.

import { useMemo, useState } from "react";
import type { Evidence } from "@/lib/types";
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
  extortion_disclosure: { label: S_XRAY.kBlackmail, why: S_XRAY.wBlackmail, tone: "danger" },
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
  credential_self_query: { label: S_XRAY.kSelfQ, why: S_XRAY.wSelfQ, tone: "info" },
  code_delivery_context: { label: S_XRAY.kDelivery, why: S_XRAY.wDelivery, tone: "info" },
  destination: { label: S_XRAY.kDest, why: S_XRAY.wDest, tone: "caution" },
  refund_promise: { label: S_XRAY.kPromise, why: S_XRAY.wPromise, tone: "danger" },
  category: { label: S_XRAY.kPattern, why: S_XRAY.wPattern, tone: "danger" },
};

const TONE_RANK: Record<Tone, number> = { danger: 3, caution: 2, info: 1 };
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
  return null; // unknown kinds simply don't highlight — never guess
}

type Seg = { text: string; evs: Evidence[] };

// Boundary segmentation: overlapping findings SHARE segments instead of one
// silently swallowing the other — every finding stays reachable via tap.
function buildSegments(payload: string, evidence: Evidence[]): Seg[] {
  const usable = evidence.filter(
    (e) =>
      e.start !== null &&
      e.end !== null &&
      e.start >= 0 &&
      e.end <= payload.length &&
      e.end > e.start &&
      kindUI(e.kind)
  );
  if (usable.length === 0) return [{ text: payload, evs: [] }];
  const points = new Set<number>([0, payload.length]);
  for (const e of usable) {
    points.add(e.start!);
    points.add(e.end!);
  }
  const sorted = [...points].sort((a, b) => a - b);
  const segs: Seg[] = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    const [a, b] = [sorted[i], sorted[i + 1]];
    if (a === b) continue;
    const evs = usable.filter((e) => e.start! <= a && e.end! >= b);
    segs.push({ text: payload.slice(a, b), evs });
  }
  return segs;
}

function segTone(evs: Evidence[]): Tone {
  let best: Tone = "info";
  for (const e of evs) {
    const t = kindUI(e.kind)!.tone;
    if (TONE_RANK[t] > TONE_RANK[best]) best = t;
  }
  return best;
}

export default function ScamXray({
  payload,
  evidence,
  lang,
}: {
  payload: string;
  evidence: Evidence[];
  lang: Lang;
}) {
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const segs = useMemo(() => buildSegments(payload, evidence ?? []), [payload, evidence]);
  const marked = segs.filter((s) => s.evs.length > 0);
  if (marked.length === 0 || /^upi:\/\//i.test(payload.trim())) return null;

  // active segment's findings, deduped by kind for the tap sheet
  const active = activeKey
    ? segs.find((_, i) => `seg${i}` === activeKey)?.evs ?? []
    : [];
  const activeKinds = [...new Map(active.map((e) => [e.kind, e])).values()];

  return (
    <div className="border-b-2 border-line p-4">
      <h3 className="plate text-inksoft">
        {pick(lang, S_XRAY.title)[0]} · {pick(lang, S_XRAY.title)[1]}
      </h3>
      <div className="mt-2 border-2 border-ink bg-paper2 p-3">
        <p className="max-h-52 overflow-y-auto whitespace-pre-wrap break-words text-[15px] leading-loose">
          {segs.map((s, i) =>
            s.evs.length > 0 ? (
              <mark
                key={i}
                role="button"
                tabIndex={0}
                aria-expanded={activeKey === `seg${i}`}
                aria-label={s.evs
                  .map((e) => pick(lang, kindUI(e.kind)!.label)[0])
                  .join(", ")}
                onClick={() => setActiveKey(activeKey === `seg${i}` ? null : `seg${i}`)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setActiveKey(activeKey === `seg${i}` ? null : `seg${i}`);
                  }
                }}
                className={`-my-0.5 cursor-pointer rounded-none px-0.5 py-0.5 font-semibold ${TONE_MARK[segTone(s.evs)]} ${
                  activeKey === `seg${i}` ? "outline outline-2 outline-ink" : ""
                } focus-visible:outline focus-visible:outline-2 focus-visible:outline-ink`}
              >
                {s.text}
              </mark>
            ) : (
              <span key={i}>{s.text}</span>
            )
          )}
        </p>
      </div>
      {/* tap-to-explain sheet — EVERY finding under the tapped segment */}
      {activeKinds.length > 0 ? (
        <div className="mt-2 space-y-2" aria-live="polite">
          {activeKinds.map((e) => {
            const ui = kindUI(e.kind)!;
            return (
              <div key={e.id} className={`border-2 bg-paper p-2.5 ${TONE_CHIP[ui.tone]}`}>
                <p className="plate">
                  {pick(lang, ui.label)[0]} · {pick(lang, ui.label)[1]}
                  {e.factual && (
                    <span className="ml-2 border border-line px-1 text-inksoft">
                      {pick(lang, S_XRAY.factualTag)[0]}
                    </span>
                  )}
                </p>
                <p className="mt-1 text-sm font-semibold leading-snug">
                  {pick(lang, ui.why)[0]}
                </p>
                <p className="mt-0.5 text-xs leading-snug text-inksoft">
                  {pick(lang, ui.why)[1]}
                </p>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="plate mt-1.5 text-inksoft">{pick(lang, S_XRAY.hint)[0]}</p>
      )}
    </div>
  );
}

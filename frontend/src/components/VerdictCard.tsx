"use client";

// The product's money shot, as a suraksha poster: DANGER/SUSPICIOUS render as a
// hazard notice (stripe band, enormous खतरा, rubber-stamp community seal, stamp-slam
// reveal); NO_KNOWN_RISK is a quiet clearance chit. Danger screams, safety whispers.
// Visual layer only — data flow and audio behavior unchanged.

import { useEffect, useRef, useState } from "react";
import type { Check, Signal } from "@/lib/types";
import { CATEGORY_UI, SOURCE_UI, VERDICT_UI } from "@/lib/labels";
import { ISpeaker, IStop } from "@/components/icons";

const TONE = {
  danger: {
    stripe: "hazard-danger",
    headline: "text-danger",
    sub: "text-dangerdeep",
    border: "border-ink",
  },
  caution: {
    stripe: "hazard-caution",
    headline: "text-caution",
    sub: "text-cautiondeep",
    border: "border-ink",
  },
} as const;

function WeightTrack({ weight }: { weight: number }) {
  const w = Math.max(4, Math.min(weight, 100));
  return (
    <div className="h-1.5 w-full border border-line bg-paper2">
      <div className="h-full bg-ink" style={{ width: `${w}%` }} />
    </div>
  );
}

function SignalRow({ s }: { s: Signal }) {
  const src = SOURCE_UI[s.source];
  return (
    <li className="py-3">
      <div className="flex items-start justify-between gap-3">
        <span className="font-semibold leading-snug">{s.title_hi}</span>
        <span className="shrink-0 border-2 border-ink px-1.5 font-mono text-sm font-semibold tabular-nums">
          +{s.weight}
        </span>
      </div>
      <div className="plate mt-0.5 text-inksoft">{s.title_en}</div>
      <div className="mt-2">
        <WeightTrack weight={s.weight} />
      </div>
      <p className="mt-2 text-sm leading-snug">{s.detail_hi}</p>
      <p className="mt-0.5 text-xs leading-snug text-inksoft">{s.detail_en}</p>
      <span className={`plate mt-2 inline-block border px-1.5 py-0.5 ${src.cls}`}>
        {src.hi} · {src.en}
      </span>
    </li>
  );
}

export default function VerdictCard({
  check,
  actions,
  autoSpeak = false,
}: {
  check: Check;
  actions?: React.ReactNode; // e.g. the Report button (wired in the intel task)
  autoSpeak?: boolean; // voice-path beat 4: Dhaal speaks the warning back unprompted
}) {
  const v = VERDICT_UI[check.verdict];
  const cat = check.scam_category ? CATEGORY_UI[check.scam_category] : null;
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [speaking, setSpeaking] = useState(false);

  function speak() {
    if (!check.tts_audio_b64) return;
    if (!audioRef.current) {
      audioRef.current = new Audio(`data:audio/wav;base64,${check.tts_audio_b64}`);
      audioRef.current.onended = () => setSpeaking(false);
    }
    if (speaking) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setSpeaking(false);
    } else {
      setSpeaking(true);
      audioRef.current.play().catch(() => setSpeaking(false));
    }
  }

  // Auto-play the spoken warning once when a voice-path result mounts. The tap
  // that ran the check counts as the user gesture, so autoplay is allowed.
  const audio = check.tts_audio_b64;
  useEffect(() => {
    if (!autoSpeak || !audio) return;
    const el = new Audio(`data:audio/wav;base64,${audio}`);
    audioRef.current = el;
    el.onended = () => setSpeaking(false);
    setSpeaking(true);
    el.play().catch(() => setSpeaking(false));
    return () => {
      el.pause();
      setSpeaking(false);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoSpeak, audio]);

  const listenButton = check.tts_audio_b64 ? (
    <button
      onClick={speak}
      className="mt-3 inline-flex items-center gap-2 border-2 border-ink bg-paper px-4 py-1.5 text-sm font-semibold hover:bg-paper2"
    >
      {speaking ? <IStop className="h-4 w-4" /> : <ISpeaker className="h-4 w-4" />}
      {speaking ? "रोकें" : "सुनिए · LISTEN"}
    </button>
  ) : null;

  /* ---------------- quiet clearance chit ---------------- */
  if (check.verdict === "no_known_risk") {
    return (
      <section
        aria-live="polite"
        className="chit-in mx-auto max-w-md border-2 border-clear bg-paper"
      >
        <div className="flex items-start gap-3 p-4">
          <svg viewBox="0 0 24 24" className="mt-1 h-7 w-7 shrink-0 text-clear" aria-hidden="true">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" />
            <path d="m7.5 12.5 3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="square" />
          </svg>
          <div className="min-w-0">
            <h2 className="font-display text-2xl font-bold leading-tight text-clear">{v.hi}</h2>
            <p className="plate mt-0.5 text-cleardeep">{v.en}</p>
            <p className="mt-2 leading-relaxed">{check.explanation_hi}</p>
            <p className="mt-1 text-sm leading-relaxed text-inksoft">{check.explanation_en}</p>
            <p className="mt-2 text-sm italic text-inksoft">{v.hint_hi}</p>
            {listenButton}
          </div>
        </div>
        {check.signals.length > 0 && (
          <div className="border-t border-line px-4 pb-3">
            <ul className="divide-y divide-line">
              {check.signals.map((s) => (
                <SignalRow key={s.id} s={s} />
              ))}
            </ul>
          </div>
        )}
        {actions && <div className="border-t border-line p-4">{actions}</div>}
      </section>
    );
  }

  /* ---------------- hazard notice (danger / suspicious) ---------------- */
  const t = TONE[v.tone as "danger" | "caution"];
  const community = check.signals.find((s) => s.source === "community");
  const sealCount = community?.title_en.match(/\d+/)?.[0] ?? null;

  return (
    <section aria-live="polite" className="stamp-in border-[3px] border-ink bg-paper shadow-poster">
      {/* hazard stripe band */}
      <div className={`h-8 border-b-[3px] border-ink ${t.stripe}`} aria-hidden="true" />

      {/* headline block */}
      <div className="relative border-b-[3px] border-ink p-4 pb-3.5">
        <p className="plate text-inksoft">ढाल सुरक्षा जाँच · DHAAL NOTICE</p>
        <h2 className={`type-verdict mt-1 font-display font-extrabold ${t.headline}`}>{v.hi}</h2>
        <p className={`plate mt-1 ${t.sub}`}>{v.en}</p>
        <p className="mt-2.5 max-w-[26rem] font-semibold leading-snug">{v.hint_hi}</p>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          {cat && (
            <span className="border-2 border-ink bg-paper2 px-2 py-0.5 text-sm font-semibold">
              {cat.hi} · {cat.en}
            </span>
          )}
          <span className="font-mono text-sm tabular-nums text-inksoft">
            <span className="text-lg font-semibold text-ink">{check.score}</span>/100 RISK
          </span>
        </div>

        {/* community rubber-stamp seal */}
        {community && (
          <div
            aria-hidden="true"
            className={`absolute -top-7 right-3 flex h-[92px] w-[92px] -rotate-6 flex-col items-center justify-center rounded-full border-[3px] bg-paper/80 outline outline-2 outline-offset-[3px] ${
              v.tone === "danger"
                ? "border-danger text-dangerdeep outline-danger"
                : "border-caution text-cautiondeep outline-caution"
            }`}
            style={{
              backgroundImage:
                "radial-gradient(circle at 32% 28%, rgba(20,24,31,0.07), transparent 55%)",
            }}
          >
            <span className="font-mono text-3xl font-semibold leading-none tabular-nums">
              {sealCount ?? "—"}
            </span>
            <span className="mt-0.5 text-xs font-bold leading-none">रिपोर्ट</span>
          </div>
        )}
      </div>

      {/* plain-language explanation */}
      <div className="border-b-2 border-line p-4">
        <p className="text-lg leading-relaxed">{check.explanation_hi}</p>
        <p className="mt-1.5 text-sm leading-relaxed text-inksoft">{check.explanation_en}</p>
        {listenButton}
      </div>

      {/* signal-by-signal reasons */}
      <div className="p-4 pt-3">
        <h3 className="plate text-inksoft">ऐसा क्यों · WHY THIS VERDICT</h3>
        {check.signals.length === 0 ? (
          <p className="mt-2 text-sm text-inksoft">
            कोई खतरे का संकेत नहीं मिला · no risk signals detected
          </p>
        ) : (
          <ul className="mt-1 divide-y-2 divide-line">
            {check.signals.map((s) => (
              <SignalRow key={s.id} s={s} />
            ))}
          </ul>
        )}
      </div>

      {actions && <div className="border-t-[3px] border-ink p-4">{actions}</div>}
    </section>
  );
}

"use client";

// The product's money shot: verdict + the exact reasons, Hindi-first.
// Reused by /check now and the guardian screens later — keep it payload-driven.

import { useRef, useState } from "react";
import type { Check } from "@/lib/types";
import { CATEGORY_UI, SOURCE_UI, VERDICT_UI } from "@/lib/labels";

function WeightBar({ weight }: { weight: number }) {
  const w = Math.max(4, Math.min(weight, 100));
  const color =
    weight >= 40 ? "bg-red-500" : weight >= 20 ? "bg-amber-500" : "bg-neutral-400";
  return (
    <div className="h-1.5 w-full rounded-full bg-neutral-200 dark:bg-neutral-800">
      <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${w}%` }} />
    </div>
  );
}

export default function VerdictCard({
  check,
  actions,
}: {
  check: Check;
  actions?: React.ReactNode; // e.g. the Report button (wired in the intel task)
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

  return (
    <section
      className={`overflow-hidden rounded-2xl border-2 ${v.ring} bg-white shadow-sm dark:bg-neutral-900`}
      aria-live="polite"
    >
      {/* Big verdict banner */}
      <div className={`p-4 ${v.banner}`}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-3xl font-extrabold leading-tight">
              {v.icon} {v.hi}
            </div>
            <div className="mt-0.5 text-sm font-semibold uppercase tracking-wide opacity-90">
              {v.en}
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold tabular-nums">{check.score}</div>
            <div className="text-xs opacity-90">risk / 100</div>
          </div>
        </div>
        <div className="mt-2 text-sm font-medium opacity-95">{v.hint_hi}</div>
        {cat && (
          <span className="mt-3 inline-block rounded-full bg-black/20 px-3 py-1 text-xs font-semibold">
            {cat.hi} · {cat.en}
          </span>
        )}
      </div>

      {/* Plain-language explanation */}
      <div className="border-b border-neutral-200 p-4 dark:border-neutral-800">
        <p className="text-base leading-relaxed">{check.explanation_hi}</p>
        <p className="mt-1.5 text-sm leading-relaxed text-neutral-500">
          {check.explanation_en}
        </p>
        {check.tts_audio_b64 && (
          <button
            onClick={speak}
            className="mt-3 rounded-full border border-neutral-300 px-4 py-1.5 text-sm font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
          >
            {speaking ? "⏹ रोकें" : "🔊 सुनिए · Listen"}
          </button>
        )}
      </div>

      {/* Signal-by-signal reasons */}
      <div className="p-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
          ऐसा क्यों? · Why this verdict
        </h3>
        {check.signals.length === 0 ? (
          <p className="mt-2 text-sm text-neutral-500">
            कोई खतरे का संकेत नहीं मिला · no risk signals detected
          </p>
        ) : (
          <ul className="mt-3 space-y-3">
            {check.signals.map((s) => {
              const src = SOURCE_UI[s.source];
              return (
                <li key={s.id} className="rounded-xl border border-neutral-200 p-3 dark:border-neutral-800">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold leading-snug">{s.title_hi}</span>
                    <span className="shrink-0 text-sm font-bold tabular-nums text-neutral-600 dark:text-neutral-300">
                      +{s.weight}
                    </span>
                  </div>
                  <div className="mt-0.5 text-xs text-neutral-500">{s.title_en}</div>
                  <div className="mt-2">
                    <WeightBar weight={s.weight} />
                  </div>
                  <p className="mt-2 text-sm leading-snug">{s.detail_hi}</p>
                  <p className="mt-0.5 text-xs leading-snug text-neutral-500">{s.detail_en}</p>
                  <span
                    className={`mt-2 inline-block rounded-full px-2 py-0.5 text-[11px] font-medium ${src.cls}`}
                  >
                    {src.hi} · {src.en}
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {actions && <div className="border-t border-neutral-200 p-4 dark:border-neutral-800">{actions}</div>}
    </section>
  );
}

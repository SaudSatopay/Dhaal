"use client";

// "ठग को पहचानो" — 5 real fixture messages, the user calls scam/genuine, the
// REAL engine (/api/check) is the referee. Pure frontend + existing API; the
// reveal shows the engine's verdict + its top signals. Herd immunity, gamified.

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Check } from "@/lib/types";
import { LEARN_POOL } from "@/lib/fixtures";
import { S_LEARN, VERDICT_UI } from "@/lib/labels";
import { apiLang, fmt, pick, useLang } from "@/lib/lang";
import TopBar from "@/components/TopBar";
import { IArrowR, ICheck, ICross, IShieldCheck } from "@/components/icons";

type Round = {
  text: string;
  guessScam?: boolean;
  check?: Check;
};

function shuffled<T>(arr: T[]): T[] {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

const isScamVerdict = (c: Check) => c.verdict !== "no_known_risk";

export default function LearnPage() {
  const lang = useLang();
  const [rounds, setRounds] = useState<Round[] | null>(null);
  const [idx, setIdx] = useState(-1); // -1 = intro screen
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    setRounds(shuffled(LEARN_POOL).map((text) => ({ text })));
  }, []);

  function restart() {
    setRounds(shuffled(LEARN_POOL).map((text) => ({ text })));
    setIdx(-1);
    setError(false);
  }

  async function guess(guessScam: boolean) {
    if (!rounds || busy) return;
    setBusy(true);
    setError(false);
    try {
      const res = await api<Check>("/api/check", {
        method: "POST",
        body: JSON.stringify({
          type: "text",
          payload: rounds[idx].text,
          lang: apiLang(lang),
        }),
      });
      setRounds((rs) =>
        rs ? rs.map((r, i) => (i === idx ? { ...r, guessScam, check: res } : r)) : rs
      );
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  if (!rounds) return null;

  const current = idx >= 0 && idx < rounds.length ? rounds[idx] : null;
  const finished = idx >= rounds.length;
  const score = rounds.filter(
    (r) => r.check && r.guessScam === isScamVerdict(r.check)
  ).length;

  return (
    <div className="min-h-screen bg-paper">
      <TopBar title_hi={S_LEARN.title.hi} title_en={S_LEARN.title.en} />

      <main className="mx-auto max-w-xl p-4 pb-16">
        {/* ---------------- intro ---------------- */}
        {idx === -1 && (
          <section className="border-[3px] border-ink bg-paper p-5 text-center shadow-poster">
            <IShieldCheck className="mx-auto h-12 w-12 text-saffdeep" />
            <h2 className="mt-3 font-display text-3xl font-extrabold leading-tight">
              {pick(lang, S_LEARN.title)[0]}
            </h2>
            <p className="plate mt-1 text-inksoft">{pick(lang, S_LEARN.title)[1]}</p>
            <p className="mx-auto mt-3 max-w-sm">{pick(lang, S_LEARN.intro)[0]}</p>
            <button
              onClick={() => setIdx(0)}
              className="mt-5 border-[3px] border-ink bg-saffron px-10 py-3 font-display text-xl font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
            >
              {pick(lang, S_LEARN.start)[0]}
            </button>
          </section>
        )}

        {/* ---------------- round ---------------- */}
        {current && (
          <section className="border-[3px] border-ink bg-paper shadow-poster-sm">
            <div className="flex items-center justify-between border-b-[3px] border-ink px-3 py-2">
              <span className="plate text-inksoft">
                {fmt(pick(lang, S_LEARN.round)[0], { i: idx + 1 })}
              </span>
              <span className="flex gap-1" aria-hidden="true">
                {rounds.map((r, i) => (
                  <span
                    key={i}
                    className={`inline-block h-2 w-2 border border-ink ${
                      i < idx ? "bg-ink" : i === idx ? "bg-saffron" : "bg-paper"
                    }`}
                  />
                ))}
              </span>
            </div>

            <p className="whitespace-pre-wrap break-words border-b-2 border-line bg-paper2 p-4 text-base leading-relaxed">
              {current.text}
            </p>

            {!current.check ? (
              <div className="p-4">
                <div className="flex gap-2">
                  <button
                    onClick={() => guess(true)}
                    disabled={busy}
                    className="flex flex-1 items-center justify-center gap-2 border-[3px] border-danger bg-paper px-4 py-3 font-display text-lg font-bold text-dangerdeep hover:bg-dangertint disabled:opacity-40"
                  >
                    <ICross className="h-5 w-5" /> {pick(lang, S_LEARN.scamBtn)[0]}
                  </button>
                  <button
                    onClick={() => guess(false)}
                    disabled={busy}
                    className="flex flex-1 items-center justify-center gap-2 border-[3px] border-clear bg-paper px-4 py-3 font-display text-lg font-bold text-cleardeep hover:bg-cleartint disabled:opacity-40"
                  >
                    <ICheck className="h-5 w-5" /> {pick(lang, S_LEARN.genuineBtn)[0]}
                  </button>
                </div>
                {busy && (
                  <p className="plate blink mt-3 text-center text-saffdeep">
                    {pick(lang, S_LEARN.checking)[0]}
                  </p>
                )}
                {error && (
                  <p className="mt-3 text-center text-sm font-bold text-saffdeep">
                    API? — दोबारा tap करें · tap again
                  </p>
                )}
              </div>
            ) : (
              <RoundReveal
                round={current}
                onNext={() => setIdx((i) => i + 1)}
                last={idx === rounds.length - 1}
              />
            )}
          </section>
        )}

        {/* ---------------- score ---------------- */}
        {finished && (
          <section className="stamp-in border-[3px] border-ink bg-paper p-5 text-center shadow-poster">
            <h2 className="font-display text-4xl font-extrabold">
              {fmt(pick(lang, S_LEARN.scoreTitle)[0], { n: score })}
            </h2>
            <p className="mt-2 text-inksoft">
              {pick(
                lang,
                score === 5 ? S_LEARN.scorePerfect : score >= 3 ? S_LEARN.scoreGood : S_LEARN.scoreLow
              )[0]}
            </p>
            <Link
              href="/check"
              className="mt-5 inline-flex items-center gap-2 border-[3px] border-ink bg-saffron px-8 py-3 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
            >
              {pick(lang, S_LEARN.ctaInbox)[0]} <IArrowR className="h-5 w-5" />
            </Link>
            <div className="mt-4">
              <button
                onClick={restart}
                className="plate text-inksoft underline underline-offset-2 hover:text-ink"
              >
                {pick(lang, S_LEARN.again)[0]}
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

function RoundReveal({
  round,
  onNext,
  last,
}: {
  round: Round;
  onNext: () => void;
  last: boolean;
}) {
  const lang = useLang();
  const check = round.check!;
  const scam = isScamVerdict(check);
  const correct = round.guessScam === scam;
  // simulator rounds are full fixture texts — always assessed; fall back safe
  const v = VERDICT_UI[check.verdict ?? "no_known_risk"];
  const vCls =
    v.tone === "danger"
      ? "border-danger text-dangerdeep"
      : v.tone === "caution"
        ? "border-caution text-cautiondeep"
        : "border-clear text-cleardeep";

  return (
    <div className="chit-in p-4">
      <p
        className={`flex items-center gap-2 font-display text-2xl font-extrabold ${
          correct ? "text-cleardeep" : "text-dangerdeep"
        }`}
      >
        {correct ? <ICheck className="h-6 w-6" /> : <ICross className="h-6 w-6" />}
        {pick(lang, correct ? S_LEARN.correct : S_LEARN.wrong)[0]}
      </p>

      <div className="mt-3 border-2 border-line bg-paper2 p-3">
        <p className="plate text-inksoft">
          {pick(lang, S_LEARN.engineSaid)[0]} · {pick(lang, S_LEARN.engineSaid)[1]}
        </p>
        <p className="mt-1.5 flex flex-wrap items-center gap-2">
          <span className={`plate border-2 px-2 py-0.5 ${vCls}`}>
            {pick(lang, v.label)[0]} · {check.score}/100
          </span>
        </p>
        {check.signals.slice(0, 2).map((s) => (
          <p key={s.id} className="mt-2 text-sm font-semibold leading-snug">
            ▸ {lang === "en" ? s.title_en : s.title_hi}
          </p>
        ))}
        <p className="mt-2 text-sm leading-snug text-inksoft">
          {(lang === "en" ? check.explanation_en : check.explanation_hi).slice(0, 160)}
        </p>
      </div>

      <button
        onClick={onNext}
        className="mt-4 w-full border-[3px] border-ink bg-saffron px-6 py-2.5 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
      >
        {pick(lang, last ? S_LEARN.seeScore : S_LEARN.next)[0]}
      </button>
    </div>
  );
}

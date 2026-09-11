"use client";

// The product's money shot, as a suraksha poster: DANGER/SUSPICIOUS render as a
// hazard notice (stripe band, enormous headline, rubber-stamp community seal,
// stamp-slam reveal); NO_KNOWN_RISK is a quiet clearance chit. Danger screams,
// safety whispers. Bilingual: the selected language leads everywhere.

import { useEffect, useRef, useState } from "react";
import type { Check, Signal } from "@/lib/types";
import { CATEGORY_UI, S_COMMON, S_REALITY, S_VERDICT, SOURCE_UI, VERDICT_UI } from "@/lib/labels";
import { pick, useLang, type Lang } from "@/lib/lang";
import ScamXray from "@/components/ScamXray";
import { ISpeaker, IStop } from "@/components/icons";

const TONE = {
  danger: {
    stripe: "hazard-danger",
    headline: "text-danger",
    sub: "text-dangerdeep",
  },
  caution: {
    stripe: "hazard-caution",
    headline: "text-caution",
    sub: "text-cautiondeep",
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

function SignalRow({ s, lang }: { s: Signal; lang: Lang }) {
  const src = SOURCE_UI[s.source] ?? SOURCE_UI.deterministic; // unknown sources never crash the card
  const [srcP, srcS] = pick(lang, src);
  const title = lang === "en" ? [s.title_en, s.title_hi] : [s.title_hi, s.title_en];
  const detail = lang === "en" ? [s.detail_en, s.detail_hi] : [s.detail_hi, s.detail_en];
  return (
    <div className="py-3">
      <div className="flex items-start justify-between gap-3">
        <span className="font-semibold leading-snug">{title[0]}</span>
        <span className="shrink-0 border-2 border-ink px-1.5 font-mono text-sm font-semibold tabular-nums">
          +{s.weight}
        </span>
      </div>
      <div className="plate mt-0.5 text-inksoft">{title[1]}</div>
      <div className="mt-2">
        <WeightTrack weight={s.weight} />
      </div>
      <p className="mt-2 text-sm leading-snug">{detail[0]}</p>
      <p className="mt-0.5 text-xs leading-snug text-inksoft">{detail[1]}</p>
      <span className={`plate mt-2 inline-block border px-1.5 py-0.5 ${src.cls}`}>
        {srcP} · {srcS}
      </span>
    </div>
  );
}

export default function VerdictCard({
  check,
  actions,
  autoSpeak = false,
  theater = false,
}: {
  check: Check;
  actions?: React.ReactNode; // e.g. the Report button (wired in the intel task)
  autoSpeak?: boolean; // voice-path beat 4: Dhaal speaks the warning back unprompted
  /** choreographed reveal of the REAL response: signals stagger in, score counts
      up, then the verdict stamp-slams. Zero invention — pure presentation order. */
  theater?: boolean;
}) {
  const lang = useLang();

  // ---- verdict theater staging (hazard notices only; the clear chit stays quiet)
  const isHazard = check.verdict !== null && check.verdict !== "no_known_risk";
  const staged = theater && isHazard;
  const [revealed, setRevealed] = useState(staged ? 0 : Number.MAX_SAFE_INTEGER);
  const [slammed, setSlammed] = useState(!staged);
  const [shownScore, setShownScore] = useState(staged ? 0 : check.score);

  useEffect(() => {
    if (!staged) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setRevealed(Number.MAX_SAFE_INTEGER);
      setSlammed(true);
      setShownScore(check.score);
      return;
    }
    setRevealed(0);
    setSlammed(false);
    setShownScore(0);
    const n = check.signals.length;
    const timers: ReturnType<typeof setTimeout>[] = [];
    for (let i = 1; i <= n; i++) {
      timers.push(setTimeout(() => setRevealed(i), 200 + i * 150));
    }
    const total = 200 + n * 150 + 300;
    timers.push(
      setTimeout(() => {
        setSlammed(true);
        setShownScore(check.score); // throttled tabs must never slam with a stale count
      }, total)
    );
    let s = 0;
    const step = Math.max(1, check.score / Math.max(1, total / 40));
    const si = setInterval(() => {
      s += step;
      if (s >= check.score) {
        setShownScore(check.score);
        clearInterval(si);
      } else {
        setShownScore(Math.round(s));
      }
    }, 40);
    return () => {
      timers.forEach(clearTimeout);
      clearInterval(si);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [staged, check._id]);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [speaking, setSpeaking] = useState(false);
  // H14: verdict is nullable in the contract; unassessed checks never reach
  // this card (the check page renders the context/unsupported panel), so
  // lookups below use a narrowed alias — after every hook, per hook rules.
  const verdict = check.verdict ?? "no_known_risk";
  const v = VERDICT_UI[verdict];
  const [vLabel, vLabelSub] = pick(lang, v.label);
  const [vHint] = pick(lang, v.hint);
  const cat = check.scam_category ? CATEGORY_UI[check.scam_category] : null;
  const explanation =
    lang === "en"
      ? [check.explanation_en, check.explanation_hi]
      : [check.explanation_hi, check.explanation_en];

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
      {speaking
        ? pick(lang, S_COMMON.stopAudio)[0]
        : `${pick(lang, S_COMMON.listen)[0]} · ${pick(lang, S_COMMON.listen)[1]}`}
    </button>
  ) : null;

  /* ---------------- quiet clearance chit ---------------- */
  if (verdict === "no_known_risk") {
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
            <h2 className="font-display text-2xl font-bold leading-tight text-clear">{vLabel}</h2>
            <p className="plate mt-0.5 text-cleardeep">{vLabelSub}</p>
            <p className="mt-2 leading-relaxed">{explanation[0]}</p>
            <p className="mt-1 text-sm leading-relaxed text-inksoft">{explanation[1]}</p>
            <p className="mt-2 text-sm italic text-inksoft">{vHint}</p>
            {listenButton}
          </div>
        </div>
        {/* clean-but-noteworthy: awareness context, agent flows, destinations
            still show their x-ray — honesty about what was and wasn't scored */}
        {check.facts?.evidence && check.facts.evidence.length > 0 && (
          <div className="border-t border-line">
            <ScamXray
              payload={check.input.payload}
              evidence={check.facts.evidence}
              lang={lang}
            />
          </div>
        )}
        {check.signals.length > 0 && (
          <div className="border-t border-line px-4 pb-3">
            <ul className="divide-y divide-line">
              {check.signals.map((s) => (
                <li key={s.id}>
                  <SignalRow s={s} lang={lang} />
                </li>
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
  const [why, whySub] = pick(lang, S_VERDICT.why);
  const [sealWord] = pick(lang, S_VERDICT.sealReports);

  // H12+ intent-mismatch hero — the expectation-vs-payload catch renders as the
  // TOP element, larger than any other signal (runsheet beat 2b money-shot).
  const mismatch = check.signals.find((s) => s.id === "intent_mismatch");
  const rest = mismatch ? check.signals.filter((s) => s.id !== "intent_mismatch") : check.signals;
  const heroShown = !staged || revealed >= 1;
  const shownRest = rest.slice(0, Math.max(0, revealed - (mismatch ? 1 : 0)));

  // H12+ structured analysis — "what they want", straight from the response
  const an = check.analysis;
  const anAsking = an?.asking_for ?? [];
  const anPressure = an?.pressure ?? [];
  const anMoneyOut = an?.money_direction === "out_of_your_account";
  const anHasContent = !!an && (!!an.claimed_identity || anAsking.length > 0 || anMoneyOut || anPressure.length > 0);
  const inr = (a: string | number) => {
    const n = Number(a);
    return Number.isFinite(n) ? `₹${n.toLocaleString("en-IN")}` : String(a);
  };

  return (
    <section
      aria-live="polite"
      className={`border-[3px] border-ink bg-paper shadow-poster ${staged ? "chit-in" : "stamp-in"}`}
    >
      {/* hazard stripe band */}
      <div className={`h-8 border-b-[3px] border-ink ${t.stripe}`} aria-hidden="true" />

      {/* headline block */}
      <div className="relative border-b-[3px] border-ink p-4 pb-3.5">
        <p className="plate text-inksoft">ढाल सुरक्षा जाँच · DHAAL NOTICE</p>
        <div className={slammed ? "stamp-in" : "invisible"}>
          <h2 className={`type-verdict mt-1 font-display font-extrabold ${t.headline}`}>{vLabel}</h2>
          <p className={`plate mt-1 ${t.sub}`}>{vLabelSub}</p>
          <p className="mt-2.5 max-w-[26rem] font-semibold leading-snug">{vHint}</p>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          {cat && (
            <span
              className={`border-2 border-ink bg-paper2 px-2 py-0.5 text-sm font-semibold ${
                slammed ? "" : "invisible"
              }`}
            >
              {pick(lang, cat)[0]} · {pick(lang, cat)[1]}
            </span>
          )}
          <span className="font-mono text-sm tabular-nums text-inksoft">
            <span className="text-lg font-semibold text-ink">{shownScore}</span>/100 RISK
          </span>
        </div>

        {/* community rubber-stamp seal */}
        {community && slammed && (
          <div
            aria-hidden="true"
            className={`stamp-in absolute -top-7 right-3 flex h-[92px] w-[92px] -rotate-6 flex-col items-center justify-center rounded-full border-[3px] bg-paper/80 outline outline-2 outline-offset-[3px] ${
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
            <span className={`mt-0.5 font-bold leading-none ${lang === "en" ? "text-[10px]" : "text-xs"}`}>
              {sealWord}
            </span>
          </div>
        )}
      </div>

      {/* H12+ mismatch hero — full danger treatment, above everything else */}
      {mismatch && (
        <div className={`border-b-[3px] border-ink bg-dangertint p-4 ${heroShown ? (staged ? "row-reveal" : "") : "invisible"}`}>
          <p className="plate text-dangerdeep">
            {pick(lang, S_VERDICT.mismatchPlate)[0]} · {pick(lang, S_VERDICT.mismatchPlate)[1]} · +{mismatch.weight}
          </p>
          <p className="mt-1.5 font-display text-2xl font-bold leading-snug text-dangerdeep">
            {lang === "en" ? mismatch.detail_en : mismatch.detail_hi}
          </p>
          <p className="mt-1 text-sm leading-snug text-inksoft">
            {lang === "en" ? mismatch.detail_hi : mismatch.detail_en}
          </p>
        </div>
      )}

      {/* plain-language explanation */}
      <div className="border-b-2 border-line p-4">
        <p className="text-lg leading-relaxed">{explanation[0]}</p>
        <p className="mt-1.5 text-sm leading-relaxed text-inksoft">{explanation[1]}</p>
        {listenButton}
      </div>

      {/* H15 SCAM X-RAY — the engine's evidence spans, highlighted in the
          original message; tap to see why each phrase matters */}
      {slammed && check.facts?.evidence && (
        <ScamXray
          payload={check.input.payload}
          evidence={check.facts.evidence}
          lang={lang}
        />
      )}

      {/* H16 §4C payment reality check — a VALID parsed request only; precise
          mechanics wording; promised-in vs requested-out when both exist */}
      {slammed && check.facts?.parse?.status === "valid" && (
        <div className="border-b-2 border-line p-4">
          <h3 className="plate text-inksoft">
            {pick(lang, S_REALITY.title)[0]} · {pick(lang, S_REALITY.title)[1]}
          </h3>
          <div className="mt-2 divide-y-2 divide-line border-2 border-ink">
            <div className="flex items-baseline justify-between gap-3 p-2.5">
              <span className="plate shrink-0 text-inksoft">{pick(lang, S_REALITY.expected)[0]}</span>
              <span className="text-sm font-bold">
                {check.facts.expectation === "pay"
                  ? pick(lang, S_REALITY.expPay)[0]
                  : check.facts.expectation === "receive"
                    ? pick(lang, S_REALITY.expReceive)[0]
                    : pick(lang, S_REALITY.expUnknown)[0]}
              </span>
            </div>
            <div className="flex items-baseline justify-between gap-3 p-2.5">
              <span className="plate shrink-0 text-inksoft">{pick(lang, S_REALITY.opens)[0]}</span>
              <span className="text-right font-mono text-sm font-bold">
                {check.facts.parse.action === "collect"
                  ? pick(lang, S_REALITY.collectReq)[0]
                  : pick(lang, S_REALITY.payReq)[0]}
                {check.facts.parse.amount && (
                  <span className="ml-1.5 text-dangerdeep">₹{check.facts.parse.amount}</span>
                )}
                {check.facts.parse.payee_vpa && (
                  <span className="block text-xs font-normal text-inksoft">
                    {pick(lang, S_REALITY.toPayee)[0]}: {check.facts.parse.payee_vpa}
                  </span>
                )}
              </span>
            </div>
            {check.facts.promised_incoming && (
              <div className="p-2.5">
                <div className="flex items-baseline justify-between gap-3">
                  <span className="plate text-inksoft">{pick(lang, S_REALITY.promised)[0]}</span>
                  <span className="font-mono text-sm font-bold text-cleardeep">
                    ₹{check.facts.promised_incoming} {pick(lang, S_REALITY.inYou)[0]}
                  </span>
                </div>
                <div className="mt-1 flex items-baseline justify-between gap-3">
                  <span className="plate text-inksoft">{pick(lang, S_REALITY.requested)[0]}</span>
                  <span className="font-mono text-sm font-bold text-dangerdeep">
                    {pick(lang, S_REALITY.outYou)[0]} ₹{check.facts.parse.amount ?? "?"}
                  </span>
                </div>
              </div>
            )}
          </div>
          <p className="mt-2 text-xs leading-snug text-inksoft">
            {pick(lang, S_REALITY.unverified)[0]}
          </p>
        </div>
      )}

      {/* H12+ analysis — "what they want" ink-frame table */}
      {anHasContent && (
        <div className="border-b-2 border-line p-4">
          <h3 className="plate text-inksoft">
            {pick(lang, S_VERDICT.whatTheyWant)[0]} · {pick(lang, S_VERDICT.whatTheyWant)[1]}
          </h3>
          <div className="mt-2 divide-y-2 divide-line border-2 border-ink">
            {an?.claimed_identity && (
              <div className="flex items-baseline justify-between gap-3 p-2.5">
                <span className="plate shrink-0 text-inksoft">{pick(lang, S_VERDICT.claims)[0]}</span>
                <span className="font-mono text-sm font-bold">{an.claimed_identity}</span>
              </div>
            )}
            {anAsking.map((a, i) => (
              <div key={i} className="flex items-baseline justify-between gap-3 p-2.5">
                <span className="plate shrink-0 text-inksoft">
                  {i === 0 ? pick(lang, S_VERDICT.asking)[0] : ""}
                </span>
                <span className="text-right text-sm font-semibold">
                  {lang === "en" ? a.what : a.hi}
                  {a.amount != null && (
                    <span className="ml-2 font-mono font-bold text-dangerdeep">{inr(a.amount)}</span>
                  )}
                </span>
              </div>
            ))}
            {anMoneyOut && (
              <div className="flex items-baseline justify-between gap-3 p-2.5">
                <span className="plate shrink-0 text-inksoft">{pick(lang, S_VERDICT.moneyDir)[0]}</span>
                <span className="text-sm font-bold text-dangerdeep">
                  {pick(lang, S_VERDICT.moneyOut)[0]}
                </span>
              </div>
            )}
            {anPressure.length > 0 && (
              <div className="flex items-center justify-between gap-3 p-2.5">
                <span className="plate shrink-0 text-inksoft">{pick(lang, S_VERDICT.pressureL)[0]}</span>
                <span className="flex flex-wrap justify-end gap-1.5">
                  {anPressure.map((p) => (
                    <span key={p.tag} className="plate border border-cautiondeep px-1.5 py-0.5 text-cautiondeep">
                      {lang === "en" ? p.tag : p.hi}
                    </span>
                  ))}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* signal-by-signal reasons */}
      <div className="p-4 pt-3">
        <h3 className="plate text-inksoft">
          {why} · {whySub}
        </h3>
        {check.signals.length === 0 ? (
          <p className="mt-2 text-sm text-inksoft">
            {pick(lang, S_VERDICT.noSignals)[0]}
          </p>
        ) : (
          <ul className="mt-1 divide-y-2 divide-line">
            {shownRest.map((s) => (
              <li key={s.id} className={staged ? "row-reveal row-sweep relative overflow-hidden" : ""}>
                <SignalRow s={s} lang={lang} />
              </li>
            ))}
          </ul>
        )}
      </div>

      {actions && slammed && (
        <div className={`border-t-[3px] border-ink p-4 ${staged ? "chit-in" : ""}`}>{actions}</div>
      )}
    </section>
  );
}

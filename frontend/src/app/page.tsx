"use client";

// The landing — a live war-room poster. Giant inked wordmark, then the SCAM
// RADAR: a survey-style Rajasthan plate with a rotating sweep and pings sized
// by REAL verified-report counts from /api/intel/trends, odometer stats, and
// a ticker of the latest verified indicators. All data live — nothing invented.

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ScamCategory, Trends } from "@/lib/types";
import { CATEGORY_UI, S_HOME, S_WA } from "@/lib/labels";
import { pick, useLang, type Lang, type LangText } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";
import { DhaalMark, IArrowR, IGlobe, IShieldCheck, ISiren, IUsers } from "@/components/icons";
import { S_LEARN } from "@/lib/labels";

const SURFACES: { href: string; Icon: typeof IUsers; label: LangText; sub: LangText }[] = [
  { href: "/guardian", Icon: IUsers, label: S_HOME.sGuardian, sub: S_HOME.sGuardianSub },
  { href: "/intel", Icon: IGlobe, label: S_HOME.sIntel, sub: S_HOME.sIntelSub },
  { href: "/learn", Icon: IShieldCheck, label: S_LEARN.title, sub: S_LEARN.intro },
  { href: "/recover", Icon: ISiren, label: S_HOME.sRecover, sub: S_HOME.sRecoverSub },
];

// Survey-plate frame: viewBox 0 0 320 300. Rajasthan drawn from geography —
// north tip at Sri Ganganagar, the eastern Dholpur notch, the Kota–Jhalawar
// hang, the Banswara tail south, the Jaisalmer point west. Inked, not GIS.
const RAJASTHAN_PATH =
  "M112 18 L140 30 L158 48 L186 56 L218 62 L252 78 L272 96 L250 106 " +
  "L258 132 L262 166 L252 196 L224 190 L218 210 L196 252 L172 264 L150 248 " +
  "L128 232 L106 222 L74 208 L52 194 L24 150 L36 112 L58 74 L86 40 Z";

// Ping anchor per city + hand-placed label offset (dx, dy) so plates never
// collide with dots or each other. Unknown cities are skipped, never guessed.
const CITY_XY: Record<string, { xy: [number, number]; label: [number, number] }> = {
  jaipur: { xy: [196, 96], label: [12, -14] },
  jodhpur: { xy: [98, 148], label: [-2, 20] },
  udaipur: { xy: [152, 222], label: [-46, 14] },
  kota: { xy: [226, 162], label: [12, 12] },
  ajmer: { xy: [160, 130], label: [10, 12] },
  bikaner: { xy: [76, 78], label: [10, -10] },
  jaisalmer: { xy: [52, 140], label: [8, -14] },
  alwar: { xy: [222, 78], label: [12, -8] },
};

function Radar({ trends, lang }: { trends: Trends; lang: Lang }) {
  const cities = trends.cities.filter((c) => CITY_XY[c.city.toLowerCase()]);
  const max = Math.max(...cities.map((c) => c.count), 1);
  return (
    <svg viewBox="0 0 320 300" className="w-full" role="img" aria-label={pick(lang, S_HOME.radarSub)[0]}>
      <defs>
        {/* survey hatch for the drop-shadow plate */}
        <pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke="var(--color-ink)" strokeWidth="1.6" />
        </pattern>
        {/* faint chart grid */}
        <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
          <path d="M28 0H0V28" fill="none" stroke="var(--color-line)" strokeWidth="0.7" />
        </pattern>
        {/* the sweep beam — bright leading edge, long fade */}
        <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="var(--color-saffron)" stopOpacity="0" />
          <stop offset="0.82" stopColor="var(--color-saffron)" stopOpacity="0.28" />
          <stop offset="1" stopColor="var(--color-saffron)" stopOpacity="0.55" />
        </linearGradient>
        <clipPath id="stateClip">
          <path d={RAJASTHAN_PATH} />
        </clipPath>
      </defs>

      {/* chart-paper ground */}
      <rect x="6" y="6" width="308" height="288" fill="url(#grid)" />
      {/* registration crosses */}
      {[[36, 34], [284, 34], [36, 268], [284, 268]].map(([x, y], i) => (
        <g key={i} stroke="var(--color-line)" strokeWidth="1.4">
          <line x1={x - 6} y1={y} x2={x + 6} y2={y} />
          <line x1={x} y1={y - 6} x2={x} y2={y + 6} />
        </g>
      ))}
      {/* survey margin notes */}
      <text x="10" y="152" className="font-mono" fontSize="8" fill="var(--color-inksoft)" transform="rotate(-90 10 152)" textAnchor="middle" letterSpacing="2">
        27°N
      </text>
      <text x="160" y="296" className="font-mono" fontSize="8" fill="var(--color-inksoft)" textAnchor="middle" letterSpacing="2">
        73°E — RAJASTHAN — SURVEY OF SCAMS · 2026
      </text>
      {/* compass */}
      <g transform="translate(292 24)">
        <line x1="0" y1="10" x2="0" y2="-8" stroke="var(--color-ink)" strokeWidth="1.6" />
        <path d="M0 -12 L4 -4 L-4 -4 Z" fill="var(--color-ink)" />
        <text x="0" y="22" className="font-mono" fontSize="8" fill="var(--color-inksoft)" textAnchor="middle">N</text>
      </g>

      {/* the state — hatched shadow, misregistered saffron pass, ink pass */}
      <path d={RAJASTHAN_PATH} transform="translate(7 7)" fill="url(#hatch)" opacity="0.16" />
      <path d={RAJASTHAN_PATH} transform="translate(3.5 3.5)" fill="var(--color-saffron)" opacity="0.85" />
      <path
        d={RAJASTHAN_PATH}
        fill="var(--color-paper2)"
        stroke="var(--color-ink)"
        strokeWidth="3"
        strokeLinejoin="miter"
      />

      {/* survey grid inside the state + rotating sweep, both clipped */}
      <g clipPath="url(#stateClip)">
        <rect x="0" y="0" width="320" height="300" fill="url(#grid)" opacity="0.55" />
        <g className="radar-sweep" style={{ transformOrigin: "160px 150px" }}>
          <path d="M160 150 L340 40 L340 150 Z" fill="url(#beam)" />
        </g>
      </g>

      {/* city pings + label plates with leader lines */}
      {cities.map((c, i) => {
        const spot = CITY_XY[c.city.toLowerCase()];
        const [x, y] = spot.xy;
        const [dx, dy] = spot.label;
        const r = 5 + (c.count / max) * 7;
        const name = c.city.charAt(0).toUpperCase() + c.city.slice(1);
        const lx = x + dx + (dx >= 0 ? r : -r);
        const ly = y + dy + (dy > 6 ? r : dy < -6 ? -r : 0);
        return (
          <g key={c.city}>
            <circle
              className="radar-ping"
              cx={x}
              cy={y}
              r={r}
              fill="none"
              stroke="var(--color-danger)"
              strokeWidth="2"
              style={{ animationDelay: `${i * 0.45}s` }}
            />
            <circle cx={x} cy={y} r={r} fill="var(--color-saffron)" stroke="var(--color-ink)" strokeWidth="2" />
            <circle cx={x} cy={y} r="1.6" fill="var(--color-ink)" />
            <text
              x={lx}
              y={ly}
              textAnchor={dx >= 0 ? "start" : "end"}
              className="font-mono"
              fontSize="10"
              fontWeight="600"
              fill="var(--color-ink)"
              stroke="var(--color-paper2)"
              strokeWidth="3.5"
              paintOrder="stroke"
              strokeLinejoin="round"
            >
              {name} · {c.count}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function Odometer({ value }: { value: number }) {
  const [shown, setShown] = useState<number | null>(null);

  useEffect(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setShown(value);
      return;
    }
    let v = Math.max(0, value - 18);
    setShown(v);
    const t = setInterval(() => {
      v += 1;
      setShown(v);
      if (v >= value) clearInterval(t);
    }, 55);
    return () => clearInterval(t);
  }, [value]);

  if (shown === null) return null;
  return (
    <div className="flex gap-1" aria-label={`${value} verified reports`}>
      {String(shown).padStart(3, "0").split("").map((d, i) => (
        <span
          key={i}
          className="inline-block w-7 border-2 border-ink bg-ink py-0.5 text-center font-mono text-xl font-semibold leading-none text-paper"
        >
          {d}
        </span>
      ))}
    </div>
  );
}

function Ticker({ trends, lang }: { trends: Trends; lang: Lang }) {
  const items = trends.top_indicators.slice(0, 6).map((ind) => {
    const cat = CATEGORY_UI[ind.category as ScamCategory];
    return `${ind.value} · ${ind.report_count}×${cat ? ` · ${pick(lang, cat)[0]}` : ""}`;
  });
  if (items.length === 0) return null;
  const row = items.join("  ▸  ");
  return (
    <div className="mt-3 flex items-stretch border-2 border-ink bg-paper2">
      <span className="plate shrink-0 self-center border-r-2 border-ink bg-saffron px-2 py-1.5">
        {pick(lang, S_HOME.verifiedNow)[0]}
      </span>
      <div className="relative flex-1 overflow-hidden">
        <div className="ticker-track flex w-max items-center whitespace-nowrap py-1.5 font-mono text-xs text-ink">
          <span className="px-3">{row}</span>
          <span className="px-3" aria-hidden="true">{row}</span>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const lang = useLang();
  const [health, setHealth] = useState<"checking" | "up" | "down">("checking");
  const [trends, setTrends] = useState<Trends | null>(null);

  useEffect(() => {
    api<{ ok: boolean }>("/api/health")
      .then((h) => setHealth(h.ok ? "up" : "down"))
      .catch(() => setHealth("down"));
    api<Trends>("/api/intel/trends")
      .then(setTrends)
      .catch(() => {});
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-paper">
      {/* poster edge tape */}
      <div className="hazard-saffron h-2.5 border-b-2 border-ink" aria-hidden="true" />

      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-5 pb-4">
        <div className="flex-1 pt-5">
          {/* ===================== THE MASTHEAD ===================== */}
          <div className="chit-in d1 relative">
            <div className="flex items-start justify-between">
              <span className="plate text-inksoft">{pick(lang, S_HOME.markSub)[0]}</span>
              <LangToggle />
            </div>

            {/* seal + giant wordmark, optically locked at the type's x-height */}
            <div className="mt-1 flex items-center gap-4">
              <DhaalMark className="seal-pop d2 h-[4.6rem] w-auto shrink-0 sm:h-[5.6rem]" />
              <h1 className="type-wordmark font-display font-extrabold tracking-tight">
                ढाल
              </h1>
            </div>
            <div className="rule-grow mt-2 h-1.5 bg-saffron" aria-hidden="true" />

            {/* the promise — poster type, the check boxed like a stamped field */}
            <p className="type-hero mt-3 font-display font-bold">
              {pick(lang, S_HOME.promise1)[0]}{" "}
              <span className="inline-block -rotate-1 border-[3px] border-ink bg-saffron px-2 leading-tight shadow-poster-sm">
                {pick(lang, S_HOME.promise2)[0]}
              </span>
            </p>
            <p className="mt-2.5 max-w-md text-[15px] leading-snug text-inksoft">
              {pick(lang, S_HOME.promiseSub)[0]}
            </p>
          </div>

          {/* ===================== THE ACTION ===================== */}
          <Link
            href="/check"
            className="chit-in d3 sheet mt-5 block border-[3px] border-ink bg-saffron p-4 shadow-poster"
          >
            <span className="flex items-center justify-between gap-3">
              <span className="font-display text-3xl font-extrabold leading-none sm:text-4xl">
                {pick(lang, S_HOME.cta)[0]}
              </span>
              <IArrowR className="cta-arrow h-9 w-9 shrink-0" />
            </span>
            <span className="plate mt-2 block opacity-70">PASTE · QR PHOTO · VOICE · WHATSAPP</span>
          </Link>

          {/* ===================== THE RADAR ===================== */}
          <section className="chit-in d4 mt-6 border-[3px] border-ink bg-paper shadow-poster">
            <div className="flex items-center justify-between border-b-[3px] border-ink px-3 py-2">
              <h2 className="font-display text-lg font-bold leading-none">
                {pick(lang, S_HOME.radarTitle)[0]}
              </h2>
              {health === "up" && (
                <span className="plate border border-saffdeep px-1.5 py-0.5 text-saffdeep">
                  <span className="blink">●</span> LIVE
                </span>
              )}
            </div>
            {trends ? (
              <>
                <p className="plate px-3 pt-2 text-inksoft">{pick(lang, S_HOME.radarSub)[0]}</p>
                <div className="px-3 pb-1 pt-1">
                  <Radar trends={trends} lang={lang} />
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-t-2 border-line px-3 py-2.5">
                  <Odometer value={trends.total_reports} />
                  <div className="plate flex flex-wrap gap-x-3 gap-y-1 text-inksoft">
                    <span>
                      <span className="font-semibold text-saffdeep">
                        +{trends.live_reports ?? 0}
                      </span>{" "}
                      {pick(lang, S_HOME.statLive)[0]}
                    </span>
                    <span>
                      <span className="font-semibold text-ink">2</span>{" "}
                      {pick(lang, S_HOME.statLangs)[0]}
                    </span>
                    <span>
                      <span className="font-semibold text-ink">5</span>{" "}
                      {pick(lang, S_HOME.statFamilies)[0]}
                    </span>
                  </div>
                </div>
                <p className="border-t-2 border-line px-3 py-1.5 font-mono text-[11px] font-semibold tracking-wide text-inksoft">
                  {lang === "hi"
                    ? "डेटा: synthetic demo + आज शाम की live रिपोर्टें"
                    : "data: synthetic demo + this evening's live reports"}
                </p>
              </>
            ) : (
              <div className="m-3 h-56 animate-pulse bg-paper2" />
            )}
          </section>

          {/* just-verified ticker */}
          {trends && <Ticker trends={trends} lang={lang} />}

          {/* ===================== THE INDEX ===================== */}
          <nav className="chit-in d5 mt-7 border-t-[3px] border-ink">
            {SURFACES.map((s, i) => (
              <Link
                key={s.href}
                href={s.href}
                className="group flex items-center gap-3.5 border-b-2 border-line py-3 pl-1 pr-1 transition-colors hover:bg-paper2"
              >
                <span className="plate w-7 shrink-0 text-inksoft" aria-hidden="true">
                  0{i + 1}
                </span>
                <span className="flex h-11 w-11 shrink-0 items-center justify-center border-2 border-ink bg-paper text-saffdeep shadow-poster-sm transition-transform group-hover:-translate-y-0.5">
                  <s.Icon className="h-6 w-6" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-lg font-bold leading-tight">
                    {pick(lang, s.label)[0]}
                  </span>
                  <span className="block truncate text-sm text-inksoft">
                    {pick(lang, s.sub)[0]}
                  </span>
                </span>
                <IArrowR className="h-5 w-5 shrink-0 text-inksoft transition-transform group-hover:translate-x-1 group-hover:text-ink" />
              </Link>
            ))}
          </nav>
        </div>

        {/* WhatsApp bot strip — check without even opening the app */}
        <p className="plate mt-6 border-2 border-line bg-paper2 px-3 py-2 text-center text-inksoft">
          {pick(lang, S_WA.line)[0]}
        </p>

        <footer className="flex items-center justify-between pb-2 pt-6">
          <span className="plate text-inksoft">
            MUJ HACKX 4.0 · FINTECH PS#7 · {process.env.NEXT_PUBLIC_BUILD}
          </span>
          {health === "up" ? (
            <span className="plate -rotate-2 border-2 border-ink px-2 py-0.5">
              SHIELD ONLINE
            </span>
          ) : health === "down" ? (
            <span className="plate blink -rotate-2 border-2 border-saffdeep px-2 py-0.5 text-saffdeep">
              API OFFLINE
            </span>
          ) : (
            <span className="plate text-inksoft">…</span>
          )}
        </footer>
      </main>
    </div>
  );
}

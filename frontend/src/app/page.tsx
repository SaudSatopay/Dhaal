"use client";

// The QR-scan landing — a live war-room poster. The hero is the SCAM RADAR:
// a hand-drawn Rajasthan outline with pings sized by REAL verified-report
// counts from /api/intel/trends, odometer stats, and a ticker of the latest
// verified indicators. All data live from the API — nothing invented.

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ScamCategory, Trends } from "@/lib/types";
import { CATEGORY_UI, S_HOME } from "@/lib/labels";
import { pick, useLang, type Lang, type LangText } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";
import { IArrowR, IGlobe, IShield, IShieldCheck, ISiren, IUsers } from "@/components/icons";
import { S_LEARN } from "@/lib/labels";

const SURFACES: { href: string; Icon: typeof IUsers; label: LangText; sub: LangText }[] = [
  { href: "/guardian", Icon: IUsers, label: S_HOME.sGuardian, sub: S_HOME.sGuardianSub },
  { href: "/intel", Icon: IGlobe, label: S_HOME.sIntel, sub: S_HOME.sIntelSub },
  { href: "/learn", Icon: IShieldCheck, label: S_LEARN.title, sub: S_LEARN.intro },
  { href: "/recover", Icon: ISiren, label: S_HOME.sRecover, sub: S_HOME.sRecoverSub },
];

// Hand-placed coordinates on the hand-drawn outline below (viewBox 0 0 200 190).
// Only cities we can place render a ping; unknown cities are skipped, never guessed.
const CITY_XY: Record<string, [number, number]> = {
  jaipur: [118, 62],
  jodhpur: [58, 92],
  udaipur: [88, 140],
  kota: [138, 118],
  ajmer: [96, 84],
  bikaner: [52, 48],
  jaisalmer: [28, 80],
  alwar: [132, 50],
};

// Simplified Rajasthan outline — deliberately hand-drawn (ink on paper), not GIS.
const RAJASTHAN_PATH =
  "M58 12 L78 18 L98 38 L128 46 L152 58 L168 74 L150 92 L152 122 L142 140 L112 168 L98 164 L84 146 L66 140 L44 122 L22 104 L14 78 L30 44 Z";

function Radar({ trends, lang }: { trends: Trends; lang: Lang }) {
  const cities = trends.cities.filter((c) => CITY_XY[c.city.toLowerCase()]);
  const max = Math.max(...cities.map((c) => c.count), 1);
  return (
    <svg viewBox="0 0 200 190" className="w-full" role="img" aria-label={pick(lang, S_HOME.radarSub)[0]}>
      {/* faint registration crosses — war-desk paper texture */}
      {[
        [40, 40], [160, 40], [40, 150], [160, 150], [100, 95],
      ].map(([x, y], i) => (
        <g key={i} stroke="var(--color-line)" strokeWidth="1">
          <line x1={x - 4} y1={y} x2={x + 4} y2={y} />
          <line x1={x} y1={y - 4} x2={x} y2={y + 4} />
        </g>
      ))}
      <path
        d={RAJASTHAN_PATH}
        fill="var(--color-paper2)"
        stroke="var(--color-ink)"
        strokeWidth="2.5"
        strokeLinejoin="miter"
      />
      {cities.map((c, i) => {
        const [x, y] = CITY_XY[c.city.toLowerCase()];
        const r = 3.5 + (c.count / max) * 5;
        return (
          <g key={c.city}>
            <circle
              className="radar-ping"
              cx={x}
              cy={y}
              r={r}
              fill="none"
              stroke="var(--color-danger)"
              strokeWidth="1.5"
              style={{ animationDelay: `${i * 0.45}s` }}
            />
            <circle cx={x} cy={y} r={r} fill="var(--color-saffron)" stroke="var(--color-ink)" strokeWidth="1.5" />
            <text
              x={x}
              y={y + r + 8}
              textAnchor="middle"
              className="font-mono"
              fontSize="7"
              fill="var(--color-inksoft)"
            >
              {c.city} · {c.count}
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
        <div className="flex-1 pt-6">
          {/* compact wordmark row + language pill */}
          <div className="flex items-end justify-between gap-3">
            <div className="flex items-end gap-2.5">
              <IShield className="h-9 w-9 text-ink" />
              <h1 className="font-display text-5xl font-extrabold leading-none tracking-tight">
                ढाल
              </h1>
            </div>
            <LangToggle />
          </div>
          <p className="mt-2.5 font-display text-xl font-bold leading-snug">
            {pick(lang, S_HOME.promise1)[0]} {pick(lang, S_HOME.promise2)[0]}
          </p>

          {/* THE HERO — live scam radar */}
          <section className="mt-4 border-[3px] border-ink bg-paper shadow-poster">
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
                <div className="px-6 pb-1 pt-1">
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
              </>
            ) : (
              <div className="m-3 h-48 animate-pulse bg-paper2" />
            )}
          </section>

          {/* just-verified ticker */}
          {trends && <Ticker trends={trends} lang={lang} />}

          {/* THE action */}
          <Link
            href="/check"
            className="mt-5 block border-[3px] border-ink bg-saffron p-4 shadow-poster transition-transform active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
          >
            <span className="flex items-center justify-between gap-3">
              <span className="font-display text-3xl font-extrabold leading-none">
                {pick(lang, S_HOME.cta)[0]}
              </span>
              <IArrowR className="h-8 w-8 shrink-0" />
            </span>
            <span className="plate mt-1.5 block opacity-70">PASTE · QR PHOTO · VOICE</span>
          </Link>

          {/* secondary surfaces — a typographic index, not a card grid */}
          <nav className="mt-6 border-t-[3px] border-ink">
            {SURFACES.map((s) => (
              <Link
                key={s.href}
                href={s.href}
                className="group flex items-center gap-3.5 border-b-2 border-line py-3 hover:bg-paper2"
              >
                <s.Icon className="h-6 w-6 shrink-0 text-saffdeep" />
                <span className="min-w-0 flex-1">
                  <span className="block text-lg font-bold leading-tight">
                    {pick(lang, s.label)[0]}
                  </span>
                  <span className="block truncate text-sm text-inksoft">
                    {pick(lang, s.sub)[0]}
                  </span>
                </span>
                <IArrowR className="h-5 w-5 shrink-0 text-inksoft group-hover:text-ink" />
              </Link>
            ))}
          </nav>
        </div>

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

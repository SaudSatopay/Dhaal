"use client";

// Community intel console (golden-path beats 6+7) — the WAR DESK of the poster
// world: paper ground, ink borders, hazard bands, stamp motifs. The one dark
// element is the weekly hero plate (ink + paper text + saffron), same system as
// the deck's LIVE DEMO slide. Left = trends war map, right = moderation queue.
// Verify here → indicator goes live for every /api/check within seconds.

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { CATEGORY_UI, S_INTEL } from "@/lib/labels";
import { pick, useLang } from "@/lib/lang";
import type { Report, ScamCategory, Trends } from "@/lib/types";
import LangToggle from "@/components/LangToggle";
import { ICheck, ICross, TypeMark } from "@/components/icons";

function catLabel(c: string): { hi: string; en: string } {
  return CATEGORY_UI[c as ScamCategory] ?? { hi: c, en: c };
}

function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "now";
  if (s < 3600) return `${Math.floor(s / 60)} min`;
  if (s < 86400) return `${Math.floor(s / 3600)} hr`;
  return `${Math.floor(s / 86400)} d`;
}

/* ---------------- poster furniture ---------------- */

function SectionCard({
  title,
  sub,
  children,
}: {
  title: string;
  sub: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-2 border-ink bg-paper">
      <div className="hazard-saffron h-2 border-b-2 border-ink" aria-hidden="true" />
      <div className="p-4">
        <h3 className="font-display text-lg font-bold leading-tight">
          {title} <span className="plate ml-1 font-sans font-normal text-inksoft">{sub}</span>
        </h3>
        <div className="mt-3">{children}</div>
      </div>
    </div>
  );
}

/* ---------------- trends board ---------------- */

function DayLine({ days }: { days: { day: string; count: number }[] }) {
  if (days.length < 2) return null;
  const W = 320;
  const H = 96;
  const PAD = 8;
  const max = Math.max(...days.map((d) => d.count)) * 1.15 || 1;
  const x = (i: number) => PAD + (i * (W - 2 * PAD)) / (days.length - 1);
  const y = (c: number) => H - PAD - (c / max) * (H - 2 * PAD);
  const pts = days.map((d, i) => `${x(i)},${y(d.count)}`).join(" ");
  const area = `${PAD},${H - PAD} ${pts} ${W - PAD},${H - PAD}`;
  const last = days[days.length - 1];
  const fmt = (iso: string) => {
    const d = new Date(`${iso}T00:00:00`);
    return `${d.getDate()} ${d.toLocaleString("en", { month: "short" })}`;
  };
  return (
    <svg viewBox={`0 0 ${W} ${H + 16}`} className="w-full" role="img" aria-label="verified reports per day">
      <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="var(--color-ink)" strokeWidth="2" />
      <polygon points={area} fill="var(--color-saffron)" opacity="0.18" />
      <polyline
        points={pts}
        fill="none"
        stroke="var(--color-saffron)"
        strokeWidth="2.5"
        strokeLinecap="square"
        strokeLinejoin="miter"
      />
      {days.map((d, i) => (
        <g key={d.day}>
          <circle cx={x(i)} cy={y(d.count)} r="7" fill="transparent">
            <title>{`${fmt(d.day)}: ${d.count} reports`}</title>
          </circle>
          <rect
            x={x(i) - 2.5}
            y={y(d.count) - 2.5}
            width="5"
            height="5"
            fill="var(--color-saffron)"
            stroke="var(--color-ink)"
            strokeWidth="1"
            className="pointer-events-none"
          />
        </g>
      ))}
      <text
        x={x(days.length - 1) - 5}
        y={y(last.count) - 8}
        textAnchor="end"
        fill="var(--color-ink)"
        className="font-mono text-[11px] font-semibold tabular-nums"
      >
        {last.count}
      </text>
      <text x={PAD} y={H + 12} fill="var(--color-inksoft)" className="font-mono text-[10px]">
        {fmt(days[0].day)}
      </text>
      <text x={W - PAD} y={H + 12} textAnchor="end" fill="var(--color-inksoft)" className="font-mono text-[10px]">
        {fmt(last.day)}
      </text>
    </svg>
  );
}

function CategoryBars({ cats }: { cats: { category: ScamCategory; count: number }[] }) {
  const lang = useLang();
  const max = Math.max(...cats.map((c) => c.count)) || 1;
  return (
    <ul className="space-y-2.5">
      {cats.map((c) => {
        const [p, s] = pick(lang, catLabel(c.category));
        return (
          <li key={c.category} className="grid grid-cols-[9rem_1fr_2.5rem] items-center gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-tight">{p}</div>
              <div className="plate truncate text-inksoft">{s}</div>
            </div>
            <div className="h-3 border border-ink bg-paper2">
              <div
                className="h-full border-r border-ink bg-saffron"
                style={{ width: `${Math.max(6, (c.count / max) * 100)}%` }}
              />
            </div>
            <div className="text-right font-mono text-sm font-semibold tabular-nums">
              {c.count}
            </div>
          </li>
        );
      })}
    </ul>
  );
}

function TrendsBoard({ trends }: { trends: Trends }) {
  const lang = useLang();
  return (
    <div className="space-y-4">
      {/* hero stat — the one earned dark plate (ink + paper + saffron) */}
      <div className="relative border-[3px] border-ink bg-ink p-4 text-paper shadow-poster">
        <div className="plate text-saffron">{pick(lang, S_INTEL.week)[0]}</div>
        <div className="mt-1 flex items-baseline gap-3">
          <span className="font-mono text-6xl font-semibold tabular-nums leading-none">
            {trends.total_reports}
          </span>
          <span className="text-sm text-paper/70">
            verified
            <br />
            scam reports
          </span>
        </div>
        {typeof trends.live_reports === "number" && trends.live_reports > 0 && (
          <div className="plate mt-2 text-saffron">
            +{trends.live_reports} STORED VERIFIED REPORTS
          </div>
        )}
        <div className="mt-1 font-mono text-[11px] font-semibold tracking-wide text-paper/70">
          DATA: SYNTHETIC DEMO + THIS EVENING&apos;S LIVE REPORTS
        </div>
        {/* stamp ring, war-desk seal */}
        <div
          aria-hidden="true"
          className="plate absolute right-3 top-3 -rotate-6 rounded-full border-2 border-saffron px-2 py-3 text-saffron"
        >
          ढाल · LIVE
        </div>
      </div>

      <SectionCard title={pick(lang, S_INTEL.perDay)[0]} sub={pick(lang, S_INTEL.perDay)[1]}>
        <DayLine days={trends.by_day} />
      </SectionCard>

      <SectionCard title={pick(lang, S_INTEL.byType)[0]} sub={pick(lang, S_INTEL.byType)[1]}>
        <CategoryBars cats={trends.by_category} />
      </SectionCard>

      <SectionCard
        title={pick(lang, S_INTEL.mostReported)[0]}
        sub={pick(lang, S_INTEL.mostReported)[1]}
      >
        <ul className="divide-y-2 divide-line">
          {trends.top_indicators.slice(0, 6).map((ind, i) => (
            <li key={ind._id ?? ind.value} className="flex items-center gap-3 py-2">
              <span className="w-6 shrink-0 text-right font-mono text-xs font-semibold text-saffdeep">
                {String(i + 1).padStart(2, "0")}
              </span>
              <TypeMark type={ind.type} className="h-4 w-4 shrink-0 text-ink" />
              <span className="min-w-0 flex-1 truncate font-mono text-sm">{ind.value}</span>
              <span className="shrink-0 border-2 border-saffdeep px-1.5 font-mono text-xs font-semibold tabular-nums text-saffdeep">
                {ind.report_count}×
              </span>
            </li>
          ))}
        </ul>
      </SectionCard>

      <div className="flex flex-wrap gap-2">
        {trends.cities.map((c) => (
          <span key={c.city} className="border-2 border-ink bg-paper px-2.5 py-1 text-sm">
            {c.city}{" "}
            <span className="font-mono font-semibold tabular-nums text-saffdeep">{c.count}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/* ---------------- moderation queue ---------------- */

function QueueCard({
  report,
  onDecide,
  busy,
}: {
  report: Report;
  onDecide: (id: string, action: "verify" | "reject") => void;
  busy: boolean;
}) {
  const lang = useLang();
  const [lp, ls] = pick(lang, catLabel(report.category));
  const pending = report.status === "pending";
  return (
    <li className={`border-ink bg-paper ${pending ? "border-[3px] shadow-poster-sm" : "border-2"}`}>
      {pending && <div className="hazard-danger h-2.5 border-b-2 border-ink" aria-hidden="true" />}
      <div className="p-3">
        <div className="flex items-start justify-between gap-2">
          <span className="flex min-w-0 items-start gap-2 break-all font-mono text-sm leading-snug">
            <TypeMark type={report.indicator_type} className="mt-0.5 h-4 w-4 shrink-0 text-inksoft" />
            <span>
              {report.payload.length > 90 ? `${report.payload.slice(0, 90)}…` : report.payload}
            </span>
          </span>
          <span className="plate shrink-0 text-inksoft">{timeAgo(report.created_at)}</span>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <span className="plate border border-ink px-1.5 py-0.5">
            {lp} · {ls}
          </span>
          <span className="plate border border-line px-1.5 py-0.5 text-inksoft">{report.city}</span>
          <span className="plate border border-line px-1.5 py-0.5 text-inksoft">
            {report.indicator_type}
          </span>
        </div>
        {report.note && <p className="mt-2 text-sm italic text-inksoft">“{report.note}”</p>}
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => onDecide(report._id, "verify")}
            disabled={busy}
            className="flex flex-1 items-center justify-center gap-2 border-[3px] border-ink bg-saffron px-3 py-2 font-display text-sm font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:opacity-40"
          >
            <ICheck className="h-4 w-4" /> {pick(lang, S_INTEL.verify)[0]}
          </button>
          <button
            onClick={() => onDecide(report._id, "reject")}
            disabled={busy}
            className="flex items-center gap-1.5 border-2 border-ink px-3 py-2 text-sm font-semibold hover:bg-paper2 disabled:opacity-40"
          >
            <ICross className="h-3.5 w-3.5" /> Reject
          </button>
        </div>
      </div>
    </li>
  );
}

/* ---------------- page ---------------- */

export default function IntelPage() {
  const lang = useLang();
  const [trends, setTrends] = useState<Trends | null>(null);
  const [queue, setQueue] = useState<Report[] | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [actingOn, setActingOn] = useState<string | null>(null);
  const [flash, setFlash] = useState<"" | "ok" | "fail">("");
  const flashTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const loadTrends = useCallback(async () => {
    try {
      setTrends(await api<Trends>("/api/intel/trends"));
      setApiDown(false);
    } catch {
      setApiDown(true);
    }
  }, []);

  const loadQueue = useCallback(async () => {
    try {
      const res = await api<{ reports: Report[] }>("/api/reports?status=pending");
      setQueue(res.reports);
      setApiDown(false);
    } catch {
      setApiDown(true);
    }
  }, []);

  useEffect(() => {
    loadTrends();
    loadQueue();
    // no hidden-guard: projector setups can misreport visibility (see WardGate)
    const qt = setInterval(loadQueue, 3000);
    const tt = setInterval(loadTrends, 15000);
    return () => {
      clearInterval(qt);
      clearInterval(tt);
    };
  }, [loadQueue, loadTrends]);

  async function decide(id: string, action: "verify" | "reject") {
    setActingOn(id);
    try {
      await api(`/api/reports/${id}/verify`, {
        method: "POST",
        body: JSON.stringify({ action }),
      });
      setQueue((q) => (q ? q.filter((r) => r._id !== id) : q));
      if (action === "verify") {
        setFlash("ok");
        if (flashTimer.current) clearTimeout(flashTimer.current);
        flashTimer.current = setTimeout(() => setFlash(""), 5000);
        loadTrends();
      }
    } catch {
      setFlash("fail");
      if (flashTimer.current) clearTimeout(flashTimer.current);
      flashTimer.current = setTimeout(() => setFlash(""), 5000);
      loadQueue();
    } finally {
      setActingOn(null);
    }
  }

  const [titleP, titleS] = pick(lang, S_INTEL.title);
  const [queueP, queueS] = pick(lang, S_INTEL.queue);

  return (
    <div className="min-h-screen bg-paper">
      {/* war-desk masthead — same poster system as every other page */}
      <header className="sticky top-0 z-10 border-b-[3px] border-ink bg-paper">
        <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-2.5">
          <Link href="/" aria-label="Dhaal home" className="flex items-baseline gap-1.5 hover:opacity-80">
            <span aria-hidden="true" className="text-lg leading-none">←</span>
            <span className="font-display text-2xl font-extrabold leading-none">ढाल</span>
          </Link>
          <div className="min-w-0 flex-1 border-l-2 border-ink pl-3">
            <div className="truncate font-bold leading-tight">{titleP}</div>
            <div className="plate truncate text-inksoft">{titleS} · WAR DESK</div>
          </div>
          <LangToggle />
          <span className="plate shrink-0 border border-saffdeep px-2 py-0.5 text-saffdeep">
            <span className="blink">●</span> LIVE
          </span>
        </div>
        <div className="hazard-saffron h-2 border-t-2 border-ink" aria-hidden="true" />
      </header>

      <main className="mx-auto max-w-5xl p-4 pb-16">
        {apiDown && (
          <div className="plate mb-4 border-2 border-saffdeep bg-paper2 p-3 text-saffdeep">
            {pick(lang, S_INTEL.apiDown)[0]}
          </div>
        )}
        {flash && (
          <div
            className={`mb-4 border-[3px] border-ink p-3 font-bold shadow-poster-sm ${
              flash === "ok" ? "bg-saffron" : "bg-paper2 text-saffdeep"
            }`}
          >
            {pick(lang, flash === "ok" ? S_INTEL.flashOk : S_INTEL.flashFail)[0]}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_minmax(20rem,24rem)]">
          {/* moderation queue — first on mobile, right column on laptop */}
          <section className="lg:order-2">
            <h2 className="flex items-center justify-between font-display text-xl font-bold">
              <span>
                {queueP} <span className="plate ml-1 font-sans font-normal text-inksoft">{queueS}</span>
              </span>
              {queue && (
                <span
                  className={`px-2 font-mono text-sm font-semibold tabular-nums ${
                    queue.length > 0
                      ? "blink border-2 border-ink bg-saffron"
                      : "border border-line text-inksoft"
                  }`}
                >
                  {queue.length}
                </span>
              )}
            </h2>
            {queue === null ? (
              <div className="mt-3 h-24 animate-pulse border-2 border-line bg-paper2" />
            ) : queue.length === 0 ? (
              <p className="mt-3 border-2 border-dashed border-ink p-4 text-center text-sm text-inksoft">
                {pick(lang, S_INTEL.queueEmpty)[0]}
                <span className="plate mt-1 block">NEW REPORTS LAND HERE WITHIN 3S</span>
              </p>
            ) : (
              <ul className="mt-3 space-y-3">
                {queue.map((r) => (
                  <QueueCard key={r._id} report={r} onDecide={decide} busy={actingOn === r._id} />
                ))}
              </ul>
            )}
          </section>

          {/* trends war map */}
          <section className="lg:order-1">
            <h2 className="font-display text-xl font-bold">
              {pick(lang, S_INTEL.warMap)[0]}{" "}
              <span className="plate ml-1 font-sans font-normal text-inksoft">
                {pick(lang, S_INTEL.warMap)[1]}
              </span>
            </h2>
            {trends ? (
              <div className="mt-3">
                <TrendsBoard trends={trends} />
              </div>
            ) : (
              <div className="mt-3 space-y-4">
                <div className="h-28 animate-pulse border-2 border-line bg-paper2" />
                <div className="h-40 animate-pulse border-2 border-line bg-paper2" />
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

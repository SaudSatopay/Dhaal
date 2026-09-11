"use client";

// Community intel console (golden-path beats 6+7). Runs on the LAPTOP/projector:
// the ONE deliberate dark surface — ink war room, saffron accents, mono numerals —
// against the paper-light phone surfaces. Left = trends war map, right = moderation
// queue. Verify here → indicator goes live for every /api/check within seconds.

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { CATEGORY_UI } from "@/lib/labels";
import type { Report, ScamCategory, Trends } from "@/lib/types";
import { ICheck, ICross, TypeMark } from "@/components/icons";

function catLabel(c: string): { hi: string; en: string } {
  return CATEGORY_UI[c as ScamCategory] ?? { hi: c, en: c };
}

function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "अभी · now";
  if (s < 3600) return `${Math.floor(s / 60)} min`;
  if (s < 86400) return `${Math.floor(s / 3600)} hr`;
  return `${Math.floor(s / 86400)} d`;
}

// ---------------------------------------------------------------- trends board

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
    <div>
      <svg viewBox={`0 0 ${W} ${H + 16}`} className="w-full" role="img" aria-label="verified reports per day">
        <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="var(--color-inkline)" strokeWidth="1.5" />
        <polygon points={area} fill="var(--color-saffron)" opacity="0.12" />
        <polyline
          points={pts}
          fill="none"
          stroke="var(--color-saffron)"
          strokeWidth="2.5"
          strokeLinecap="square"
          strokeLinejoin="miter"
        />
        {days.map((d, i) => (
          <circle key={d.day} cx={x(i)} cy={y(d.count)} r="7" className="fill-transparent">
            <title>{`${fmt(d.day)}: ${d.count} reports`}</title>
          </circle>
        ))}
        {days.map((d, i) => (
          <rect
            key={`v-${d.day}`}
            x={x(i) - 2.5}
            y={y(d.count) - 2.5}
            width="5"
            height="5"
            className="pointer-events-none"
            fill="var(--color-saffron)"
          />
        ))}
        <text
          x={x(days.length - 1) - 5}
          y={y(last.count) - 8}
          textAnchor="end"
          fill="var(--color-paper)"
          className="font-mono text-[11px] font-semibold tabular-nums"
        >
          {last.count}
        </text>
        <text x={PAD} y={H + 12} fill="var(--color-fog)" className="font-mono text-[10px]">
          {fmt(days[0].day)}
        </text>
        <text x={W - PAD} y={H + 12} textAnchor="end" fill="var(--color-fog)" className="font-mono text-[10px]">
          {fmt(last.day)}
        </text>
      </svg>
    </div>
  );
}

function CategoryBars({ cats }: { cats: { category: ScamCategory; count: number }[] }) {
  const max = Math.max(...cats.map((c) => c.count)) || 1;
  return (
    <ul className="space-y-2.5">
      {cats.map((c) => {
        const l = catLabel(c.category);
        return (
          <li key={c.category} className="grid grid-cols-[9rem_1fr_2.5rem] items-center gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold leading-tight">{l.hi}</div>
              <div className="plate truncate text-fog">{l.en}</div>
            </div>
            <div className="h-2.5 border border-inkline bg-inkpanel">
              <div
                className="h-full bg-saffron"
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
  return (
    <div className="space-y-4">
      {/* hero stat */}
      <div className="border-2 border-inkline bg-inkpanel p-4">
        <div className="plate text-saffron">इस हफ्ते RAJASTHAN में · THIS WEEK</div>
        <div className="mt-1 flex items-baseline gap-3">
          <span className="font-mono text-6xl font-semibold tabular-nums leading-none">
            {trends.total_reports}
          </span>
          <span className="text-sm text-fog">
            verified
            <br />
            scam reports
          </span>
        </div>
        {typeof trends.live_reports === "number" && trends.live_reports > 0 && (
          <div className="plate mt-2 text-saffron">
            +{trends.live_reports} VERIFIED LIVE THIS SESSION
          </div>
        )}
      </div>

      {/* 7-day line */}
      <div className="border-2 border-inkline bg-inkpanel p-4">
        <h3 className="text-sm font-bold">
          रोज़ की रिपोर्टें <span className="plate ml-1 font-normal text-fog">PER DAY</span>
        </h3>
        <div className="mt-2">
          <DayLine days={trends.by_day} />
        </div>
      </div>

      {/* category bars */}
      <div className="border-2 border-inkline bg-inkpanel p-4">
        <h3 className="text-sm font-bold">
          किस तरह के धोखे <span className="plate ml-1 font-normal text-fog">BY SCAM TYPE</span>
        </h3>
        <div className="mt-3">
          <CategoryBars cats={trends.by_category} />
        </div>
      </div>

      {/* top indicators */}
      <div className="border-2 border-inkline bg-inkpanel p-4">
        <h3 className="text-sm font-bold">
          सबसे ज़्यादा रिपोर्ट हुए <span className="plate ml-1 font-normal text-fog">MOST REPORTED</span>
        </h3>
        <ul className="mt-2 divide-y divide-inkline">
          {trends.top_indicators.slice(0, 6).map((ind, i) => (
            <li key={ind._id ?? ind.value} className="flex items-center gap-3 py-2">
              <span className="w-5 shrink-0 text-right font-mono text-xs text-fog">
                {String(i + 1).padStart(2, "0")}
              </span>
              <TypeMark type={ind.type} className="h-4 w-4 shrink-0 text-fog" />
              <span className="min-w-0 flex-1 truncate font-mono text-sm">{ind.value}</span>
              <span className="shrink-0 border border-saffron px-1.5 font-mono text-xs font-semibold tabular-nums text-saffron">
                {ind.report_count}×
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* cities */}
      <div className="flex flex-wrap gap-2">
        {trends.cities.map((c) => (
          <span key={c.city} className="border border-inkline px-2.5 py-1 text-sm text-fog">
            {c.city} <span className="font-mono font-semibold tabular-nums text-paper">{c.count}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- moderation queue

function QueueCard({
  report,
  onDecide,
  busy,
}: {
  report: Report;
  onDecide: (id: string, action: "verify" | "reject") => void;
  busy: boolean;
}) {
  const l = catLabel(report.category);
  const pending = report.status === "pending";
  return (
    <li className={`border-2 bg-inkpanel p-3 ${pending ? "border-saffron" : "border-inkline"}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="flex min-w-0 items-start gap-2 break-all font-mono text-sm leading-snug">
          <TypeMark type={report.indicator_type} className="mt-0.5 h-4 w-4 shrink-0 text-fog" />
          <span>
            {report.payload.length > 90 ? `${report.payload.slice(0, 90)}…` : report.payload}
          </span>
        </span>
        <span className="plate shrink-0 text-fog">{timeAgo(report.created_at)}</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="plate border border-inkline px-1.5 py-0.5 text-fog">
          {l.hi} · {l.en}
        </span>
        <span className="plate border border-inkline px-1.5 py-0.5 text-fog">{report.city}</span>
        <span className="plate border border-inkline px-1.5 py-0.5 text-fog">
          {report.indicator_type}
        </span>
      </div>
      {report.note && <p className="mt-2 text-sm italic text-fog">“{report.note}”</p>}
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => onDecide(report._id, "verify")}
          disabled={busy}
          className="flex flex-1 items-center justify-center gap-2 border-2 border-saffron bg-saffron px-3 py-2 text-sm font-bold text-ink hover:bg-saffron/85 disabled:opacity-40"
        >
          <ICheck className="h-4 w-4" /> VERIFY — ढाल में जोड़ो
        </button>
        <button
          onClick={() => onDecide(report._id, "reject")}
          disabled={busy}
          className="flex items-center gap-1.5 border-2 border-inkline px-3 py-2 text-sm font-semibold text-fog hover:border-fog hover:text-paper disabled:opacity-40"
        >
          <ICross className="h-3.5 w-3.5" /> Reject
        </button>
      </div>
    </li>
  );
}

// ---------------------------------------------------------------- page

export default function IntelPage() {
  const [trends, setTrends] = useState<Trends | null>(null);
  const [queue, setQueue] = useState<Report[] | null>(null);
  const [apiDown, setApiDown] = useState(false);
  const [actingOn, setActingOn] = useState<string | null>(null);
  const [flash, setFlash] = useState("");
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
        setFlash("VERIFIED — अब हर जाँच में यह blocklist live है");
        if (flashTimer.current) clearTimeout(flashTimer.current);
        flashTimer.current = setTimeout(() => setFlash(""), 5000);
        loadTrends();
      }
    } catch {
      setFlash("ACTION FAILED — दोबारा try करें");
      if (flashTimer.current) clearTimeout(flashTimer.current);
      flashTimer.current = setTimeout(() => setFlash(""), 5000);
      loadQueue();
    } finally {
      setActingOn(null);
    }
  }

  return (
    <div className="min-h-screen bg-ink text-paper">
      {/* war-room masthead */}
      <header className="sticky top-0 z-10 border-b-2 border-inkline bg-ink">
        <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 py-2.5">
          <Link href="/" aria-label="Dhaal home" className="flex items-baseline gap-1.5 hover:opacity-80">
            <span aria-hidden="true" className="text-lg leading-none">←</span>
            <span className="font-display text-2xl font-extrabold leading-none">ढाल</span>
          </Link>
          <div className="min-w-0 border-l-2 border-inkline pl-3">
            <div className="truncate font-bold leading-tight">धोखों का नक्शा</div>
            <div className="plate truncate text-fog">COMMUNITY INTEL · WAR ROOM</div>
          </div>
          <span className="plate ml-auto shrink-0 border border-saffron px-2 py-0.5 text-saffron">
            <span className="blink">●</span> LIVE
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl p-4 pb-16">
        {apiDown && (
          <div className="plate mb-4 border-2 border-saffron p-3 text-saffron">
            API नहीं मिल रही — RETRYING…
          </div>
        )}
        {flash && (
          <div className="mb-4 border-2 border-saffron bg-inkpanel p-3 font-semibold text-saffron">
            {flash}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_minmax(20rem,24rem)]">
          {/* moderation queue — first on mobile, right column on laptop */}
          <section className="lg:order-2">
            <h2 className="flex items-center justify-between font-bold">
              <span>
                Moderation queue <span className="plate ml-1 font-normal text-fog">जाँच बाकी</span>
              </span>
              {queue && (
                <span
                  className={`px-2 font-mono text-sm font-semibold tabular-nums ${
                    queue.length > 0 ? "bg-saffron text-ink" : "border border-inkline text-fog"
                  }`}
                >
                  {queue.length}
                </span>
              )}
            </h2>
            {queue === null ? (
              <div className="mt-3 h-24 animate-pulse border-2 border-inkline bg-inkpanel" />
            ) : queue.length === 0 ? (
              <p className="mt-3 border-2 border-dashed border-inkline p-4 text-center text-sm text-fog">
                कोई pending report नहीं — सब जाँची जा चुकीं
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
            <h2 className="font-bold">
              War map <span className="plate ml-1 font-normal text-fog">धोखों का नक्शा</span>
            </h2>
            {trends ? (
              <div className="mt-3">
                <TrendsBoard trends={trends} />
              </div>
            ) : (
              <div className="mt-3 space-y-4">
                <div className="h-28 animate-pulse border-2 border-inkline bg-inkpanel" />
                <div className="h-40 animate-pulse border-2 border-inkline bg-inkpanel" />
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

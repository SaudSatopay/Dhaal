"use client";

// Community intel console (golden-path beats 6+7). Runs on the LAPTOP/projector:
// left = trends war map, right = moderation queue. Verify here → indicator goes
// live for every /api/check within seconds — the flywheel moment.

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { CATEGORY_UI } from "@/lib/labels";
import type { IndicatorType, Report, ScamCategory, Trends } from "@/lib/types";
import TopBar from "@/components/TopBar";

const TYPE_ICON: Record<IndicatorType, string> = {
  phone: "📞",
  upi: "₹",
  domain: "🌐",
  script: "💬",
};

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
        <polygon points={area} className="fill-blue-500/10" />
        <polyline
          points={pts}
          className="fill-none stroke-blue-600 dark:stroke-blue-400"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {days.map((d, i) => (
          <circle key={d.day} cx={x(i)} cy={y(d.count)} r="7" className="fill-transparent">
            <title>{`${fmt(d.day)}: ${d.count} reports`}</title>
          </circle>
        ))}
        {days.map((d, i) => (
          <circle
            key={`v-${d.day}`}
            cx={x(i)}
            cy={y(d.count)}
            r="2.5"
            className="pointer-events-none fill-blue-600 dark:fill-blue-400"
          />
        ))}
        <text
          x={x(days.length - 1) - 4}
          y={y(last.count) - 8}
          textAnchor="end"
          className="fill-neutral-600 text-[11px] font-semibold tabular-nums dark:fill-neutral-300"
        >
          {last.count}
        </text>
        <text x={PAD} y={H + 12} className="fill-neutral-400 text-[10px]">
          {fmt(days[0].day)}
        </text>
        <text x={W - PAD} y={H + 12} textAnchor="end" className="fill-neutral-400 text-[10px]">
          {fmt(last.day)}
        </text>
      </svg>
    </div>
  );
}

function CategoryBars({ cats }: { cats: { category: ScamCategory; count: number }[] }) {
  const max = Math.max(...cats.map((c) => c.count)) || 1;
  return (
    <ul className="space-y-2">
      {cats.map((c) => {
        const l = catLabel(c.category);
        return (
          <li key={c.category} className="grid grid-cols-[9rem,1fr,2.5rem] items-center gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-medium leading-tight">{l.hi}</div>
              <div className="truncate text-[11px] text-neutral-500">{l.en}</div>
            </div>
            <div className="h-2.5 rounded-full bg-neutral-200 dark:bg-neutral-800">
              <div
                className="h-2.5 rounded-full bg-blue-600 dark:bg-blue-500"
                style={{ width: `${Math.max(6, (c.count / max) * 100)}%` }}
              />
            </div>
            <div className="text-right text-sm font-semibold tabular-nums text-neutral-700 dark:text-neutral-200">
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
    <div className="space-y-5">
      {/* hero stat */}
      <div className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="text-xs font-semibold uppercase tracking-wide text-neutral-500">
          इस हफ्ते Rajasthan में · this week in Rajasthan
        </div>
        <div className="mt-1 flex items-baseline gap-2">
          <span className="text-5xl font-extrabold tabular-nums">{trends.total_reports}</span>
          <span className="text-sm text-neutral-500">verified scam reports</span>
        </div>
        {typeof trends.live_reports === "number" && trends.live_reports > 0 && (
          <div className="mt-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
            +{trends.live_reports} अभी live verify हुईं · verified live in this session
          </div>
        )}
      </div>

      {/* 7-day line */}
      <div className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <h3 className="text-sm font-semibold">
          रोज़ की रिपोर्टें <span className="font-normal text-neutral-500">· reports per day</span>
        </h3>
        <div className="mt-2">
          <DayLine days={trends.by_day} />
        </div>
      </div>

      {/* category bars */}
      <div className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <h3 className="text-sm font-semibold">
          किस तरह के धोखे <span className="font-normal text-neutral-500">· by scam type</span>
        </h3>
        <div className="mt-3">
          <CategoryBars cats={trends.by_category} />
        </div>
      </div>

      {/* top indicators */}
      <div className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <h3 className="text-sm font-semibold">
          सबसे ज़्यादा रिपोर्ट हुए <span className="font-normal text-neutral-500">· most reported</span>
        </h3>
        <ul className="mt-2 divide-y divide-neutral-100 dark:divide-neutral-800">
          {trends.top_indicators.slice(0, 6).map((ind, i) => (
            <li key={ind._id ?? ind.value} className="flex items-center gap-3 py-2">
              <span className="w-5 text-right text-xs font-bold text-neutral-400">{i + 1}</span>
              <span aria-hidden>{TYPE_ICON[ind.type] ?? "❓"}</span>
              <span className="min-w-0 flex-1 truncate font-mono text-sm">{ind.value}</span>
              <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-bold tabular-nums text-red-700 dark:bg-red-950/60 dark:text-red-300">
                {ind.report_count}×
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* cities */}
      <div className="flex flex-wrap gap-2">
        {trends.cities.map((c) => (
          <span
            key={c.city}
            className="rounded-full border border-neutral-300 bg-white px-3 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-900"
          >
            {c.city} <span className="font-semibold tabular-nums">· {c.count}</span>
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
  return (
    <li className="rounded-2xl border border-neutral-200 bg-white p-3 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex items-start justify-between gap-2">
        <span className="break-all font-mono text-sm leading-snug">
          {TYPE_ICON[report.indicator_type] ?? "❓"}{" "}
          {report.payload.length > 90 ? `${report.payload.slice(0, 90)}…` : report.payload}
        </span>
        <span className="shrink-0 text-[11px] text-neutral-400">{timeAgo(report.created_at)}</span>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[11px]">
        <span className="rounded-full bg-neutral-100 px-2 py-0.5 font-medium dark:bg-neutral-800">
          {l.hi} · {l.en}
        </span>
        <span className="rounded-full bg-neutral-100 px-2 py-0.5 dark:bg-neutral-800">
          📍 {report.city}
        </span>
        <span className="rounded-full bg-neutral-100 px-2 py-0.5 uppercase dark:bg-neutral-800">
          {report.indicator_type}
        </span>
      </div>
      {report.note && <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">“{report.note}”</p>}
      <div className="mt-3 flex gap-2">
        <button
          onClick={() => onDecide(report._id, "verify")}
          disabled={busy}
          className="flex-1 rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-40"
        >
          ✓ Verify — ढाल में जोड़ो
        </button>
        <button
          onClick={() => onDecide(report._id, "reject")}
          disabled={busy}
          className="rounded-xl border border-neutral-300 px-3 py-2 text-sm font-medium text-neutral-600 hover:bg-neutral-100 disabled:opacity-40 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
        >
          ✗ Reject
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
    const qt = setInterval(() => {
      if (!document.hidden) loadQueue();
    }, 3000);
    const tt = setInterval(() => {
      if (!document.hidden) loadTrends();
    }, 15000);
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
        setFlash("✓ Verified — अब हर जाँच में यह blocklist live है · live for every check now");
        if (flashTimer.current) clearTimeout(flashTimer.current);
        flashTimer.current = setTimeout(() => setFlash(""), 5000);
        loadTrends();
      }
    } catch {
      setFlash("action fail हुई — दोबारा try करें · action failed, retry");
      if (flashTimer.current) clearTimeout(flashTimer.current);
      flashTimer.current = setTimeout(() => setFlash(""), 5000);
      loadQueue();
    } finally {
      setActingOn(null);
    }
  }

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <TopBar title_hi="सबकी रिपोर्ट, सबकी सुरक्षा" title_en="Community intel console" />

      <main className="mx-auto max-w-5xl p-4 pb-16">
        {apiDown && (
          <div className="mb-4 rounded-xl border-2 border-red-300 bg-red-50 p-3 text-sm font-medium text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
            API नहीं मिल रही — connection जाँचें · can’t reach the API, retrying…
          </div>
        )}
        {flash && (
          <div className="mb-4 rounded-xl border-2 border-emerald-300 bg-emerald-50 p-3 text-sm font-semibold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
            {flash}
          </div>
        )}

        <div className="grid gap-6 lg:grid-cols-[1fr_minmax(20rem,24rem)]">
          {/* moderation queue — first on mobile, right column on laptop */}
          <section className="lg:order-2">
            <h2 className="flex items-center justify-between font-bold">
              <span>
                Moderation queue{" "}
                <span className="text-sm font-normal text-neutral-500">· जाँच बाकी</span>
              </span>
              {queue && (
                <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-sm font-bold tabular-nums text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                  {queue.length}
                </span>
              )}
            </h2>
            {queue === null ? (
              <div className="mt-3 h-24 animate-pulse rounded-2xl bg-neutral-200 dark:bg-neutral-900" />
            ) : queue.length === 0 ? (
              <p className="mt-3 rounded-2xl border border-dashed border-neutral-300 p-4 text-center text-sm text-neutral-500 dark:border-neutral-700">
                कोई pending report नहीं — सब जाँची जा चुकीं ✓<br />
                <span className="text-xs">new reports land here within 3 seconds</span>
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
              War map <span className="text-sm font-normal text-neutral-500">· धोखों का नक्शा</span>
            </h2>
            {trends ? (
              <div className="mt-3">
                <TrendsBoard trends={trends} />
              </div>
            ) : (
              <div className="mt-3 space-y-4">
                <div className="h-28 animate-pulse rounded-2xl bg-neutral-200 dark:bg-neutral-900" />
                <div className="h-40 animate-pulse rounded-2xl bg-neutral-200 dark:bg-neutral-900" />
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

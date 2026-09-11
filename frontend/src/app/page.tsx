"use client";

// The QR-scan landing — a judge's first 5 seconds. One promise, one button,
// live proof the community shield is real.

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Trends } from "@/lib/types";

const SURFACES = [
  {
    href: "/guardian",
    icon: "👨‍👩‍👧",
    hi: "परिवार की ढाल",
    en: "Guardian mode — family approves risky payments",
  },
  {
    href: "/intel",
    icon: "🗺️",
    hi: "धोखों का नक्शा",
    en: "Live scam intel from the community",
  },
  {
    href: "/recover",
    icon: "🚑",
    hi: "पहला घंटा",
    en: "Just got scammed? Recovery kit",
  },
];

export default function Home() {
  const [health, setHealth] = useState<"checking" | "up" | "down">("checking");
  const [reports, setReports] = useState<number | null>(null);

  useEffect(() => {
    api<{ ok: boolean }>("/api/health")
      .then((h) => setHealth(h.ok ? "up" : "down"))
      .catch(() => setHealth("down"));
    api<Trends>("/api/intel/trends")
      .then((t) => setReports(t.total_reports))
      .catch(() => {});
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col p-6">
      <div className="flex flex-1 flex-col justify-center py-8">
        {/* hero */}
        <div className="text-center">
          <div className="text-6xl" aria-hidden>
            🛡️
          </div>
          <h1 className="mt-3 text-6xl font-extrabold tracking-tight">ढाल</h1>
          <p className="mt-1 text-lg font-medium text-neutral-500">Dhaal</p>
          <p className="mx-auto mt-5 max-w-sm text-2xl font-bold leading-snug">
            पैसे भेजने से पहले —<br />
            एक जाँच।
          </p>
          <p className="mt-2 text-neutral-500">
            Message, QR, link, number या call — before you pay, one check.
          </p>
        </div>

        <Link
          href="/check"
          className="mt-8 block rounded-2xl bg-blue-600 p-5 text-center text-white shadow-lg transition hover:bg-blue-700"
        >
          <span className="block text-2xl font-extrabold">🔍 अभी जाँचो · Check now</span>
          <span className="mt-1 block text-sm opacity-90">paste · QR photo · बोल कर</span>
        </Link>

        {/* live community proof */}
        {reports !== null && (
          <p className="mt-4 text-center text-sm text-neutral-500">
            इस हफ्ते Rajasthan में{" "}
            <span className="font-bold text-neutral-800 dark:text-neutral-100">
              {reports} scams
            </span>{" "}
            community ने verify किए — हर report सबकी ढाल
          </p>
        )}

        {/* secondary surfaces */}
        <nav className="mt-8 grid gap-3">
          {SURFACES.map((s) => (
            <Link
              key={s.href}
              href={s.href}
              className="flex items-center gap-4 rounded-2xl border border-neutral-200 bg-white p-4 transition hover:border-blue-400 hover:shadow dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-blue-600"
            >
              <span className="text-3xl" aria-hidden>
                {s.icon}
              </span>
              <span className="min-w-0">
                <span className="block font-bold">{s.hi}</span>
                <span className="block truncate text-sm text-neutral-500">{s.en}</span>
              </span>
              <span className="ml-auto text-neutral-400" aria-hidden>
                →
              </span>
            </Link>
          ))}
        </nav>
      </div>

      <footer className="flex items-center justify-between pb-2 text-xs text-neutral-400">
        <span>MUJ HackX 4.0 · Fintech PS#7</span>
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              health === "up"
                ? "bg-emerald-500"
                : health === "down"
                  ? "bg-red-500"
                  : "bg-neutral-300 dark:bg-neutral-700"
            }`}
            aria-hidden
          />
          {health === "up" ? "shield online" : health === "down" ? "API unreachable" : "…"}
        </span>
      </footer>
    </main>
  );
}

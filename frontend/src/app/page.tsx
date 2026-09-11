"use client";

// The QR-scan landing — a suraksha poster, not a SaaS hero. One promise, one
// giant CTA, live proof the community shield is real (odometer counter).

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Trends } from "@/lib/types";
import { IArrowR, IGlobe, IShield, ISiren, IUsers } from "@/components/icons";

const SURFACES = [
  {
    href: "/guardian",
    Icon: IUsers,
    hi: "परिवार की ढाल",
    en: "Guardian mode — family approves risky payments",
  },
  {
    href: "/intel",
    Icon: IGlobe,
    hi: "धोखों का नक्शा",
    en: "Live scam intel from the community",
  },
  {
    href: "/recover",
    Icon: ISiren,
    hi: "पहला घंटा",
    en: "Just got scammed? Recovery kit",
  },
] as const;

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
          className="inline-block w-8 border-2 border-ink bg-ink py-1 text-center font-mono text-2xl font-semibold leading-none text-paper"
        >
          {d}
        </span>
      ))}
    </div>
  );
}

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
    <div className="flex min-h-screen flex-col bg-paper">
      {/* poster edge tape */}
      <div className="hazard-saffron h-2.5 border-b-2 border-ink" aria-hidden="true" />

      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-5 pb-4">
        <div className="flex-1 pt-8">
          {/* wordmark lockup */}
          <IShield className="h-11 w-11 text-ink" />
          <h1 className="type-wordmark mt-1 font-display font-extrabold tracking-tight">
            ढाल
          </h1>
          <p className="plate -mt-2 text-inksoft">DHAAL — डिजिटल ठगी के खिलाफ</p>

          <p className="type-hero mt-6 font-display font-bold">
            पैसे भेजने से पहले —
            <br />
            एक जाँच।
          </p>
          <p className="mt-2 max-w-sm text-inksoft">
            Message, QR, link, number या call — before you pay, one check.
          </p>

          {/* THE action */}
          <Link
            href="/check"
            className="mt-7 block border-[3px] border-ink bg-saffron p-4 shadow-poster transition-transform active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
          >
            <span className="flex items-center justify-between gap-3">
              <span className="font-display text-3xl font-extrabold leading-none">
                अभी जाँच करो
              </span>
              <IArrowR className="h-8 w-8 shrink-0" />
            </span>
            <span className="plate mt-1.5 block opacity-70">
              PASTE · QR PHOTO · VOICE — CHECK NOW
            </span>
          </Link>

          {/* live community proof */}
          {reports !== null && (
            <div className="mt-7 flex items-center gap-3.5">
              <Odometer value={reports} />
              <p className="text-sm leading-snug text-inksoft">
                इस हफ्ते Rajasthan में
                <span className="block font-bold text-ink">verified scam reports</span>
                हर report — सबकी ढाल
              </p>
            </div>
          )}

          {/* secondary surfaces — a typographic index, not a card grid */}
          <nav className="mt-8 border-t-[3px] border-ink">
            {SURFACES.map((s) => (
              <Link
                key={s.href}
                href={s.href}
                className="group flex items-center gap-3.5 border-b-2 border-line py-3.5 hover:bg-paper2"
              >
                <s.Icon className="h-6 w-6 shrink-0 text-saffdeep" />
                <span className="min-w-0 flex-1">
                  <span className="block text-lg font-bold leading-tight">{s.hi}</span>
                  <span className="block truncate text-sm text-inksoft">{s.en}</span>
                </span>
                <IArrowR className="h-5 w-5 shrink-0 text-inksoft group-hover:text-ink" />
              </Link>
            ))}
          </nav>
        </div>

        <footer className="flex items-center justify-between pb-2 pt-8">
          <span className="plate text-inksoft">MUJ HACKX 4.0 · FINTECH PS#7</span>
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

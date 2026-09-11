"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";

const surfaces = [
  { href: "/check", label: "Check — message / QR / voice", hi: "जाँच करो" },
  { href: "/guardian", label: "Guardian mode", hi: "परिवार की ढाल" },
  { href: "/intel", label: "Community intel", hi: "सबकी रिपोर्ट, सबकी सुरक्षा" },
  { href: "/recover", label: "I got scammed — first hour kit", hi: "पहला घंटा" },
];

export default function Home() {
  const [health, setHealth] = useState<"checking" | "up" | "down">("checking");

  useEffect(() => {
    api<{ ok: boolean }>("/api/health")
      .then((h) => setHealth(h.ok ? "up" : "down"))
      .catch(() => setHealth("down"));
  }, []);

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center gap-8 p-6">
      <div>
        <h1 className="text-5xl font-bold">
          ढाल <span className="text-2xl font-normal text-neutral-500">Dhaal</span>
        </h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400">
          पैसे भेजने से पहले — एक जाँच। Before you pay, one check.
        </p>
        <p className="mt-1 text-xs text-neutral-500">
          API:{" "}
          <span
            className={
              health === "up"
                ? "text-green-600"
                : health === "down"
                  ? "text-red-600"
                  : ""
            }
          >
            {health === "checking" ? "checking…" : health === "up" ? "connected" : "unreachable — start backend (uvicorn main:app) or set NEXT_PUBLIC_API_URL"}
          </span>
        </p>
      </div>
      <nav className="flex flex-col gap-3">
        {surfaces.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="rounded-lg border border-neutral-300 p-4 hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-900"
          >
            <div className="font-medium">{s.label}</div>
            <div className="text-sm text-neutral-500">{s.hi}</div>
          </Link>
        ))}
      </nav>
      <p className="text-xs text-neutral-400">
        MUJ HackX 4.0 · golden path lives in docs/PLAN.md
      </p>
    </main>
  );
}

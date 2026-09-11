"use client";

// SCAFFOLD ONLY — proves the end-to-end plumbing. Parva (Product lane) replaces this
// with the real /check UI per docs/TASKS.md: tabs (paste / QR via jsqr / mic), verdict
// card, signal breakdown, report button. Contract: docs/CONTRACTS.md POST /api/check.

import { useState } from "react";
import { api } from "@/lib/api";

type Signal = {
  id: string;
  source: string;
  weight: number;
  title_hi: string;
  detail_hi: string;
};
type Check = {
  verdict: "danger" | "suspicious" | "no_known_risk";
  score: number;
  signals: Signal[];
  explanation_hi: string;
  scam_category: string | null;
};

const VERDICT_UI = {
  danger: { label: "खतरा — DANGER", cls: "bg-red-600 text-white" },
  suspicious: { label: "सावधान — SUSPICIOUS", cls: "bg-amber-500 text-black" },
  no_known_risk: {
    label: "कोई ज्ञात खतरा नहीं — NO KNOWN RISK",
    cls: "bg-green-600 text-white",
  },
};

export default function CheckPage() {
  const [payload, setPayload] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Check | null>(null);
  const [error, setError] = useState("");

  async function run() {
    setBusy(true);
    setError("");
    try {
      const type = payload.trim().toLowerCase().startsWith("upi://")
        ? "qr_text"
        : "text";
      setResult(await api<Check>("/api/check", {
        method: "POST",
        body: JSON.stringify({ type, payload }),
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl p-6">
      <h1 className="text-2xl font-bold">जाँच करो</h1>
      <textarea
        className="mt-4 w-full rounded-lg border border-neutral-300 p-3 dark:border-neutral-700 dark:bg-neutral-900"
        rows={5}
        placeholder="Message, link, UPI ID या upi:// (QR से decoded) यहाँ paste करें…"
        value={payload}
        onChange={(e) => setPayload(e.target.value)}
      />
      <button
        onClick={run}
        disabled={busy || !payload.trim()}
        className="mt-3 rounded-lg bg-blue-600 px-5 py-2 font-medium text-white disabled:opacity-50"
      >
        {busy ? "जाँच रही है…" : "Check karo"}
      </button>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {result && (
        <section className="mt-6 rounded-lg border border-neutral-300 dark:border-neutral-700">
          <div className={`rounded-t-lg p-3 font-bold ${VERDICT_UI[result.verdict].cls}`}>
            {VERDICT_UI[result.verdict].label} · score {result.score}
          </div>
          <p className="p-3">{result.explanation_hi}</p>
          <ul className="space-y-2 p-3 pt-0">
            {result.signals.map((s) => (
              <li key={s.id} className="rounded border border-neutral-200 p-2 text-sm dark:border-neutral-800">
                <span className="font-medium">{s.title_hi}</span>{" "}
                <span className="text-neutral-500">(+{s.weight} · {s.source})</span>
                <div className="text-neutral-600 dark:text-neutral-400">{s.detail_hi}</div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}

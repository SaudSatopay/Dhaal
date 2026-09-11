"use client";

// Flywheel entry point (golden-path beat 6): one report here → /intel moderation →
// verified indicator → every future /api/check hits it. Keep it one-tap cheap.

import { useState } from "react";
import { api } from "@/lib/api";
import { CATEGORY_UI } from "@/lib/labels";
import type { Report, ScamCategory } from "@/lib/types";

const CITIES = ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "अन्य · other"];

export default function ReportButton({
  payload,
  defaultCategory,
}: {
  payload: string;
  defaultCategory: ScamCategory | null;
}) {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<ScamCategory>(defaultCategory ?? "other");
  const [city, setCity] = useState(CITIES[0]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState<Report | null>(null);

  async function submit() {
    setBusy(true);
    setError("");
    try {
      const rep = await api<Report>("/api/reports", {
        method: "POST",
        body: JSON.stringify({ payload, category, note, city }),
      });
      setDone(rep);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <div className="rounded-xl bg-emerald-50 p-3 text-sm dark:bg-emerald-950/40">
        <p className="font-semibold text-emerald-700 dark:text-emerald-300">
          ✓ रिपोर्ट दर्ज हो गई · report submitted
        </p>
        <p className="mt-1 text-emerald-800/80 dark:text-emerald-200/70">
          Verify होते ही यह हर भारतीय की ढाल में जुड़ जाएगी। · Once verified, it protects
          everyone instantly.
        </p>
      </div>
    );
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full rounded-xl border-2 border-red-200 bg-red-50 px-4 py-2.5 font-semibold text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300 dark:hover:bg-red-950/70"
      >
        🚩 Scam रिपोर्ट करें · Report this scam
      </button>
    );
  }

  return (
    <div className="space-y-2.5">
      <p className="break-all rounded-lg bg-neutral-100 p-2 font-mono text-xs dark:bg-neutral-800">
        {payload.length > 120 ? `${payload.slice(0, 120)}…` : payload}
      </p>
      <div className="grid grid-cols-2 gap-2">
        <label className="block text-xs font-medium text-neutral-500">
          किस तरह का धोखा? · type
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as ScamCategory)}
            className="mt-1 w-full rounded-lg border border-neutral-300 bg-white p-2 text-sm dark:border-neutral-700 dark:bg-neutral-950"
          >
            {(Object.keys(CATEGORY_UI) as ScamCategory[]).map((c) => (
              <option key={c} value={c}>
                {CATEGORY_UI[c].hi} · {CATEGORY_UI[c].en}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-xs font-medium text-neutral-500">
          शहर · city
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="mt-1 w-full rounded-lg border border-neutral-300 bg-white p-2 text-sm dark:border-neutral-700 dark:bg-neutral-950"
          >
            {CITIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
      </div>
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="कुछ और बताना चाहें… (optional)"
        className="w-full rounded-lg border border-neutral-300 bg-white p-2 text-sm dark:border-neutral-700 dark:bg-neutral-950"
      />
      {error && <p className="text-sm font-medium text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={busy}
          className="flex-1 rounded-xl bg-red-600 px-4 py-2.5 font-semibold text-white hover:bg-red-700 disabled:opacity-40"
        >
          {busy ? "भेज रहे हैं…" : "रिपोर्ट भेजें · Submit report"}
        </button>
        <button
          onClick={() => setOpen(false)}
          disabled={busy}
          className="rounded-xl border border-neutral-300 px-4 py-2.5 text-sm dark:border-neutral-700"
        >
          रहने दें
        </button>
      </div>
    </div>
  );
}

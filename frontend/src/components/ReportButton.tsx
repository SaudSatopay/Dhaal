"use client";

// Flywheel entry point (golden-path beat 6): one report here → /intel moderation →
// verified indicator → every future /api/check hits it. Keep it one-tap cheap.
// Danger red here is semantic (reporting danger), not decoration.

import { useState } from "react";
import { api } from "@/lib/api";
import { CATEGORY_UI, S_REPORT } from "@/lib/labels";
import { pick, useLang } from "@/lib/lang";
import type { Report, ScamCategory } from "@/lib/types";
import { ICheck, IFlag } from "@/components/icons";

const CITIES = ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "अन्य · other"];

export default function ReportButton({
  payload,
  defaultCategory,
}: {
  payload: string;
  defaultCategory: ScamCategory | null;
}) {
  const lang = useLang();
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
    const [dT] = pick(lang, S_REPORT.doneTitle);
    const [dS, dS2] = pick(lang, S_REPORT.doneSub);
    return (
      <div className="border-2 border-ink bg-paper2 p-3 text-sm">
        <p className="flex items-center gap-2 font-bold text-saffdeep">
          <ICheck className="h-4 w-4" /> {dT}
        </p>
        <p className="mt-1 text-inksoft">
          {dS} <span className="text-inksoft/70">· {dS2}</span>
        </p>
      </div>
    );
  }

  if (!open) {
    const [oP, oS] = pick(lang, S_REPORT.open);
    return (
      <button
        onClick={() => setOpen(true)}
        className="flex w-full items-center justify-center gap-2.5 border-[3px] border-danger bg-paper px-4 py-2.5 font-bold text-dangerdeep hover:bg-dangertint"
      >
        <IFlag className="h-5 w-5" />
        {oP} · {oS}
      </button>
    );
  }

  return (
    <div className="space-y-2.5">
      <p className="break-all border border-line bg-paper2 p-2 font-mono text-xs">
        {payload.length > 120 ? `${payload.slice(0, 120)}…` : payload}
      </p>
      <div className="grid grid-cols-2 gap-2">
        <label className="plate block text-inksoft">
          {pick(lang, S_REPORT.typeLabel)[0]}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as ScamCategory)}
            className="mt-1 w-full border-2 border-ink bg-paper p-2 font-sans text-sm normal-case tracking-normal"
          >
            {(Object.keys(CATEGORY_UI) as ScamCategory[]).map((c) => (
              <option key={c} value={c}>
                {pick(lang, CATEGORY_UI[c])[0]} · {pick(lang, CATEGORY_UI[c])[1]}
              </option>
            ))}
          </select>
        </label>
        <label className="plate block text-inksoft">
          {pick(lang, S_REPORT.cityLabel)[0]}
          <select
            value={city}
            onChange={(e) => setCity(e.target.value)}
            className="mt-1 w-full border-2 border-ink bg-paper p-2 font-sans text-sm normal-case tracking-normal"
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
        placeholder={pick(lang, S_REPORT.notePh)[0]}
        className="w-full border-2 border-ink bg-paper p-2 text-sm placeholder:text-inksoft/70"
      />
      {error && <p className="text-sm font-semibold text-dangerdeep">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={busy}
          className="flex-1 border-[3px] border-ink bg-danger px-4 py-2.5 font-bold text-paper shadow-poster-sm hover:bg-dangerdeep disabled:opacity-40"
        >
          {busy ? pick(lang, S_REPORT.sending)[0] : pick(lang, S_REPORT.submit)[0]}
        </button>
        <button
          onClick={() => setOpen(false)}
          disabled={busy}
          className="border-2 border-ink px-4 py-2.5 text-sm font-semibold hover:bg-paper2"
        >
          {pick(lang, S_REPORT.cancel)[0]}
        </button>
      </div>
    </div>
  );
}

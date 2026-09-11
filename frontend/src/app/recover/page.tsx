"use client";

// First-hour recovery kit. The reader just got scammed and is panicking —
// calm tone, ONE giant action (call 1930 — the golden hour), then ready-made
// scripts they can copy instead of composing while shaking.
// The 1930 button wears danger red deliberately: the user IS in a danger state.

import { useState } from "react";
import { api } from "@/lib/api";
import { S_RECOVER } from "@/lib/labels";
import { apiLang, pick, useLang, type LangText } from "@/lib/lang";
import TopBar from "@/components/TopBar";
import { ICheck, IPhone } from "@/components/icons";

type Kit = {
  call_script_1930: string;
  complaint_draft: string;
  bank_letter: string;
  checklist: string[];
  mocked: boolean;
};

const WHAT_OPTIONS: { id: string; label: LangText }[] = [
  { id: "paid", label: S_RECOVER.optPaid },
  { id: "shared_otp", label: S_RECOVER.optOtp },
  { id: "clicked_link", label: S_RECOVER.optLink },
];

const CHANNELS = [
  { id: "upi", label: "UPI" },
  { id: "card", label: "Card" },
  { id: "netbanking", label: "Net banking" },
  { id: "wallet", label: "Wallet" },
];

function CopyBlock({ title, text }: { title: LangText; text: string }) {
  const lang = useLang();
  const [copied, setCopied] = useState(false);
  const [tp, ts] = pick(lang, title);
  return (
    <section className="border-2 border-ink bg-paper p-4">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-bold">
          {tp} <span className="plate ml-1 font-normal text-inksoft">{ts}</span>
        </h3>
        <button
          onClick={() => {
            navigator.clipboard?.writeText(text).then(
              () => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              },
              () => {}
            );
          }}
          className="plate shrink-0 border-2 border-ink px-2.5 py-1 hover:bg-paper2"
        >
          {copied ? "✓ COPIED" : "COPY"}
        </button>
      </div>
      <p className="mt-2 whitespace-pre-wrap border border-line bg-paper2 p-3 text-sm leading-relaxed">
        {text}
      </p>
    </section>
  );
}

export default function RecoverPage() {
  const lang = useLang();
  const [what, setWhat] = useState("paid");
  const [amount, setAmount] = useState("");
  const [channel, setChannel] = useState("upi");
  const [bank, setBank] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [kit, setKit] = useState<Kit | null>(null);
  const [ticked, setTicked] = useState<Record<number, boolean>>({});

  async function getKit() {
    setBusy(true);
    setError("");
    try {
      const res = await api<Kit>("/api/recovery/kit", {
        method: "POST",
        body: JSON.stringify({
          what,
          amount: Number(amount) || 0,
          channel,
          bank: bank.trim(),
          lang: apiLang(lang),
        }),
      });
      setKit(res);
      setTicked({});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <TopBar title_hi={S_RECOVER.title.hi} title_en={S_RECOVER.title.en} />

      <main className="mx-auto max-w-xl space-y-4 p-4 pb-16">
        <p className="border-2 border-ink bg-paper2 p-4 text-sm leading-relaxed">
          <span className="font-bold">{pick(lang, S_RECOVER.introBold)[0]}</span>{" "}
          {pick(lang, S_RECOVER.intro)[0]}
        </p>

        {/* the ONE action — emergency red, earned */}
        <a
          href="tel:1930"
          className="block border-[3px] border-ink bg-danger p-5 text-paper shadow-poster transition-transform active:translate-x-[3px] active:translate-y-[3px] active:shadow-none"
        >
          <span className="flex items-center gap-4">
            <IPhone className="h-10 w-10 shrink-0" />
            <span>
              <span className="block font-display text-3xl font-extrabold leading-none">
                {pick(lang, S_RECOVER.call1930)[0]}
              </span>
              <span className="plate mt-1.5 block opacity-85">
                NATIONAL CYBER CRIME HELPLINE · सरकारी · मुफ़्त · 24×7
              </span>
            </span>
          </span>
        </a>

        {/* details form */}
        <section className="border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
          <h2 className="font-bold">
            {pick(lang, S_RECOVER.qTitle)[0]}
            <span className="plate mt-0.5 block font-normal text-inksoft">
              {pick(lang, S_RECOVER.qTitle)[1]}
            </span>
          </h2>

          <div className="mt-3 space-y-2">
            {WHAT_OPTIONS.map((o) => (
              <label
                key={o.id}
                className={`flex cursor-pointer items-center gap-3 border-2 p-3 ${
                  what === o.id ? "border-ink bg-paper2" : "border-line hover:border-ink"
                }`}
              >
                <input
                  type="radio"
                  name="what"
                  checked={what === o.id}
                  onChange={() => setWhat(o.id)}
                  className="accent-ink"
                />
                <span>
                  <span className="block font-semibold">{pick(lang, o.label)[0]}</span>
                  <span className="block text-xs text-inksoft">{pick(lang, o.label)[1]}</span>
                </span>
              </label>
            ))}
          </div>

          <div className="mt-3 grid grid-cols-3 gap-2">
            <label className="plate col-span-1 block text-inksoft">
              {pick(lang, S_RECOVER.amount)[0]}
              <input
                inputMode="numeric"
                value={amount}
                onChange={(e) => setAmount(e.target.value.replace(/[^\d]/g, ""))}
                placeholder="15000"
                className="mt-1 w-full border-2 border-ink bg-paper p-2.5 font-mono text-base tracking-normal placeholder:text-inksoft/50"
              />
            </label>
            <label className="plate col-span-1 block text-inksoft">
              {pick(lang, S_RECOVER.how)[0]}
              <select
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="mt-1 w-full border-2 border-ink bg-paper p-2.5 font-sans text-base normal-case tracking-normal"
              >
                {CHANNELS.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="plate col-span-1 block text-inksoft">
              {pick(lang, S_RECOVER.bank)[0]}
              <input
                value={bank}
                onChange={(e) => setBank(e.target.value)}
                placeholder="SBI"
                className="mt-1 w-full border-2 border-ink bg-paper p-2.5 font-sans text-base normal-case tracking-normal placeholder:text-inksoft/50"
              />
            </label>
          </div>

          {error && <p className="mt-3 text-sm font-bold text-saffdeep">{error}</p>}
          <button
            onClick={getKit}
            disabled={busy}
            className="mt-4 w-full border-[3px] border-ink bg-saffron px-6 py-3 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:opacity-40"
          >
            {busy ? pick(lang, S_RECOVER.building)[0] : pick(lang, S_RECOVER.buildBtn)[0]}
          </button>
        </section>

        {kit && (
          <div className="space-y-4">
            <CopyBlock title={S_RECOVER.say1930} text={kit.call_script_1930} />
            <CopyBlock title={S_RECOVER.complaint} text={kit.complaint_draft} />
            <CopyBlock title={S_RECOVER.bankLetter} text={kit.bank_letter} />

            <section className="border-2 border-ink bg-paper p-4">
              <h3 className="font-bold">
                Checklist{" "}
                <span className="plate ml-1 font-normal text-inksoft">
                  {pick(lang, S_RECOVER.checklistSub)[0]}
                </span>
              </h3>
              <ul className="mt-2 divide-y divide-line">
                {kit.checklist.map((item, i) => (
                  <li key={i}>
                    <label className="flex cursor-pointer items-start gap-3 py-2.5 hover:bg-paper2">
                      <input
                        type="checkbox"
                        checked={!!ticked[i]}
                        onChange={() => setTicked((t) => ({ ...t, [i]: !t[i] }))}
                        className="mt-1 h-4 w-4 accent-ink"
                      />
                      <span
                        className={`text-sm leading-relaxed ${
                          ticked[i] ? "text-inksoft line-through" : ""
                        }`}
                      >
                        {item}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
              {Object.values(ticked).filter(Boolean).length === kit.checklist.length && (
                <p className="plate mt-2 flex items-center gap-1.5 text-cleardeep">
                  <ICheck className="h-3.5 w-3.5" /> {pick(lang, S_RECOVER.allDone)[0]}
                </p>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

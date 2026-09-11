"use client";

// First-hour recovery kit. The reader just got scammed and is panicking —
// calm tone, ONE giant action (call 1930 — the golden hour), then ready-made
// scripts they can copy instead of composing while shaking.

import { useState } from "react";
import { api } from "@/lib/api";
import TopBar from "@/components/TopBar";

type Kit = {
  call_script_1930: string;
  complaint_draft: string;
  bank_letter: string;
  checklist: string[];
  mocked: boolean;
};

const WHAT_OPTIONS = [
  { id: "paid", hi: "पैसे चले गए", en: "I paid / money left my account" },
  { id: "shared_otp", hi: "OTP / PIN बता दिया", en: "I shared an OTP or PIN" },
  { id: "clicked_link", hi: "Link पर click कर दिया", en: "I clicked a link / installed an app" },
];

const CHANNELS = [
  { id: "upi", label: "UPI" },
  { id: "card", label: "Card" },
  { id: "netbanking", label: "Net banking" },
  { id: "wallet", label: "Wallet" },
];

function CopyBlock({ title_hi, title_en, text }: { title_hi: string; title_en: string; text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <section className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
      <div className="flex items-center justify-between gap-2">
        <h3 className="font-bold">
          {title_hi} <span className="text-xs font-normal text-neutral-500">· {title_en}</span>
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
          className="shrink-0 rounded-full border border-neutral-300 px-3 py-1 text-xs font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
        >
          {copied ? "✓ copied" : "📋 copy"}
        </button>
      </div>
      <p className="mt-2 whitespace-pre-wrap rounded-xl bg-neutral-50 p-3 text-sm leading-relaxed dark:bg-neutral-950/60">
        {text}
      </p>
    </section>
  );
}

export default function RecoverPage() {
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
          lang: "hi-IN",
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
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <TopBar title_hi="पहला घंटा" title_en="I got scammed — first hour" />

      <main className="mx-auto max-w-xl space-y-4 p-4 pb-16">
        <p className="rounded-2xl bg-blue-50 p-4 text-sm leading-relaxed text-blue-900 dark:bg-blue-950/40 dark:text-blue-200">
          <span className="font-bold">घबराइए मत — साँस लीजिए।</span> पहला घंटा सबसे कीमती
          है: जल्दी complaint होने पर पैसा freeze होने की उम्मीद कई गुना बढ़ जाती है। ·
          Breathe. Acting within the first hour multiplies the chance of freezing the money.
        </p>

        {/* the ONE action */}
        <a
          href="tel:1930"
          className="block rounded-2xl bg-red-600 p-5 text-center text-white shadow-lg hover:bg-red-700"
        >
          <span className="block text-3xl font-extrabold">📞 1930 पर अभी call करें</span>
          <span className="mt-1 block text-sm opacity-90">
            National Cyber Crime Helpline · सरकारी, मुफ़्त, 24×7
          </span>
        </a>

        {/* details form */}
        <section className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
          <h2 className="font-bold">
            2 सवाल — आपका kit तैयार होगा{" "}
            <span className="text-xs font-normal text-neutral-500">· get your ready-made kit</span>
          </h2>

          <div className="mt-3 space-y-2">
            {WHAT_OPTIONS.map((o) => (
              <label
                key={o.id}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border-2 p-3 ${
                  what === o.id
                    ? "border-blue-600 bg-blue-50 dark:bg-blue-950/40"
                    : "border-neutral-200 dark:border-neutral-800"
                }`}
              >
                <input
                  type="radio"
                  name="what"
                  checked={what === o.id}
                  onChange={() => setWhat(o.id)}
                  className="accent-blue-600"
                />
                <span>
                  <span className="block font-medium">{o.hi}</span>
                  <span className="block text-xs text-neutral-500">{o.en}</span>
                </span>
              </label>
            ))}
          </div>

          <div className="mt-3 grid grid-cols-3 gap-2">
            <label className="col-span-1 block text-xs font-medium text-neutral-500">
              कितने ₹?
              <input
                inputMode="numeric"
                value={amount}
                onChange={(e) => setAmount(e.target.value.replace(/[^\d]/g, ""))}
                placeholder="15000"
                className="mt-1 w-full rounded-xl border border-neutral-300 bg-white p-2.5 dark:border-neutral-700 dark:bg-neutral-950"
              />
            </label>
            <label className="col-span-1 block text-xs font-medium text-neutral-500">
              कैसे गए?
              <select
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="mt-1 w-full rounded-xl border border-neutral-300 bg-white p-2.5 dark:border-neutral-700 dark:bg-neutral-950"
              >
                {CHANNELS.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="col-span-1 block text-xs font-medium text-neutral-500">
              बैंक
              <input
                value={bank}
                onChange={(e) => setBank(e.target.value)}
                placeholder="SBI"
                className="mt-1 w-full rounded-xl border border-neutral-300 bg-white p-2.5 dark:border-neutral-700 dark:bg-neutral-950"
              />
            </label>
          </div>

          {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
          <button
            onClick={getKit}
            disabled={busy}
            className="mt-4 w-full rounded-xl bg-blue-600 px-6 py-3 font-bold text-white hover:bg-blue-700 disabled:opacity-40"
          >
            {busy ? "बन रहा है…" : "🧰 मेरा kit बनाओ · Build my kit"}
          </button>
        </section>

        {kit && (
          <div className="space-y-4">
            <CopyBlock
              title_hi="1930 पर क्या बोलें"
              title_en="what to say on 1930"
              text={kit.call_script_1930}
            />
            <CopyBlock
              title_hi="Cybercrime.gov.in complaint"
              title_en="online complaint draft"
              text={kit.complaint_draft}
            />
            <CopyBlock
              title_hi="बैंक के लिए चिट्ठी"
              title_en="letter to your bank"
              text={kit.bank_letter}
            />

            <section className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
              <h3 className="font-bold">
                Checklist <span className="text-xs font-normal text-neutral-500">· एक-एक करके</span>
              </h3>
              <ul className="mt-2 space-y-2">
                {kit.checklist.map((item, i) => (
                  <li key={i}>
                    <label className="flex cursor-pointer items-start gap-3 rounded-xl p-2 hover:bg-neutral-50 dark:hover:bg-neutral-800/60">
                      <input
                        type="checkbox"
                        checked={!!ticked[i]}
                        onChange={() => setTicked((t) => ({ ...t, [i]: !t[i] }))}
                        className="mt-1 h-4 w-4 accent-emerald-600"
                      />
                      <span
                        className={`text-sm leading-relaxed ${
                          ticked[i] ? "text-neutral-400 line-through" : ""
                        }`}
                      >
                        {item}
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}

"use client";

// Guardian mode (golden-path beat 5, PS bonus): family protecting family.
// Same route, three faces:
//   • guardian (laptop): create pair → BIG pair code + ward QR/link → live inbox (3s poll)
//   • ward join (phone): opens ?link=… → stores pairing locally → every /check now pings guardian
//   • ward paired: status + unpair
// Pairing hand-off carries link_id in the URL because the API has no resolve-by-code
// endpoint yet (asked in docs/TASKS.md Requests); pair_code stays the human-readable label.

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import QRCode from "qrcode";
import { api } from "@/lib/api";
import type { GuardianLink, GuardianRequest } from "@/lib/types";
import {
  getGuardianPair,
  getWardPair,
  setGuardianPair,
  setWardPair,
  type GuardianPair,
} from "@/lib/guardian";
import TopBar from "@/components/TopBar";

function QrCanvas({ text }: { text: string }) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    if (ref.current) {
      QRCode.toCanvas(ref.current, text, { width: 168, margin: 1 }).catch(() => {});
    }
  }, [text]);
  return <canvas ref={ref} className="rounded-xl border border-neutral-200 bg-white p-1 dark:border-neutral-700" />;
}

function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "अभी · now";
  if (s < 3600) return `${Math.floor(s / 60)} min`;
  return `${Math.floor(s / 3600)} hr`;
}

// ---------------------------------------------------------------- guardian inbox

function RequestCard({
  req,
  wardName,
  onDecide,
  busy,
}: {
  req: GuardianRequest;
  wardName: string;
  onDecide: (id: string, decision: "allowed" | "blocked", note: string) => void;
  busy: boolean;
}) {
  const [note, setNote] = useState("");
  const pending = req.status === "pending";
  return (
    <li
      className={`rounded-2xl border-2 p-4 ${
        pending
          ? "border-amber-400 bg-amber-50 dark:border-amber-600 dark:bg-amber-950/40"
          : "border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-semibold leading-snug">
          {pending ? "⚠️ " : ""}
          {wardName} ने कुछ खतरनाक जाँचा
          <span className="block text-xs font-normal text-neutral-500">
            {wardName} checked something risky · {timeAgo(req.created_at)}
          </span>
        </p>
        {!pending && (
          <span
            className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold ${
              req.status === "blocked"
                ? "bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
                : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
            }`}
          >
            {req.status === "blocked" ? "रोका · blocked" : "ठीक कहा · allowed"}
          </span>
        )}
      </div>
      <p className="mt-2 rounded-xl bg-white p-3 text-sm leading-relaxed dark:bg-neutral-950/60">
        {req.summary_hi}
      </p>
      {pending && (
        <>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="अपनी बात जोड़ें… जैसे: ठग है, मत भेजो (optional)"
            className="mt-3 w-full rounded-xl border border-neutral-300 bg-white p-2.5 text-sm dark:border-neutral-700 dark:bg-neutral-950"
          />
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => onDecide(req._id, "blocked", note)}
              disabled={busy}
              className="flex-1 rounded-xl bg-rose-600 px-4 py-2.5 font-bold text-white hover:bg-rose-700 disabled:opacity-40"
            >
              🛑 रोक दो · Block
            </button>
            <button
              onClick={() => onDecide(req._id, "allowed", note)}
              disabled={busy}
              className="flex-1 rounded-xl border-2 border-emerald-600 px-4 py-2.5 font-bold text-emerald-700 hover:bg-emerald-50 disabled:opacity-40 dark:text-emerald-400 dark:hover:bg-emerald-950/40"
            >
              ✓ ठीक है · Allow
            </button>
          </div>
        </>
      )}
      {!pending && req.guardian_note && (
        <p className="mt-2 text-sm text-neutral-500">आपका note: “{req.guardian_note}”</p>
      )}
    </li>
  );
}

function GuardianInbox({ pair, onUnpair }: { pair: GuardianPair; onUnpair: () => void }) {
  const [requests, setRequests] = useState<GuardianRequest[] | null>(null);
  const [actingOn, setActingOn] = useState<string | null>(null);
  const [wardUrl, setWardUrl] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setWardUrl(
      `${window.location.origin}/guardian?link=${pair.link_id}&g=${encodeURIComponent(
        pair.guardian_name
      )}&w=${encodeURIComponent(pair.ward_name)}`
    );
  }, [pair]);

  const load = useCallback(async () => {
    try {
      const res = await api<{ requests: GuardianRequest[] }>(
        `/api/guardian/requests?link_id=${pair.link_id}`
      );
      setRequests(res.requests);
    } catch {
      // keep last state; next poll retries
    }
  }, [pair.link_id]);

  useEffect(() => {
    load();
    const t = setInterval(load, 3000); // no hidden-guard: see WardGate note
    return () => clearInterval(t);
  }, [load]);

  async function decide(id: string, decision: "allowed" | "blocked", note: string) {
    setActingOn(id);
    try {
      await api(`/api/guardian/requests/${id}/decision`, {
        method: "POST",
        body: JSON.stringify({ decision, note }),
      });
      await load();
    } finally {
      setActingOn(null);
    }
  }

  const pending = requests?.filter((r) => r.status === "pending") ?? [];
  const decided = requests?.filter((r) => r.status !== "pending") ?? [];

  return (
    <div className="space-y-5">
      <section className="rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-neutral-500">
              आप {pair.ward_name} की ढाल हैं · you are guarding {pair.ward_name}
            </p>
            <p className="mt-1 text-3xl font-extrabold tracking-widest">{pair.pair_code}</p>
          </div>
          {wardUrl && <QrCanvas text={wardUrl} />}
        </div>
        <p className="mt-2 text-xs text-neutral-500">
          {pair.ward_name} के phone पर यह QR scan करवाएँ (या link भेजें) — बस, जुड़ गया। ·
          Scan this QR on {pair.ward_name}&rsquo;s phone, or send the link.
        </p>
        <div className="mt-2 flex gap-2">
          <button
            onClick={() => {
              navigator.clipboard?.writeText(wardUrl).then(
                () => {
                  setCopied(true);
                  setTimeout(() => setCopied(false), 2000);
                },
                () => {}
              );
            }}
            className="rounded-full border border-neutral-300 px-3 py-1 text-xs font-medium hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
          >
            {copied ? "✓ copied" : "📋 link copy करें"}
          </button>
          <button
            onClick={onUnpair}
            className="rounded-full border border-neutral-300 px-3 py-1 text-xs text-neutral-500 hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
          >
            नया pair बनाएँ
          </button>
        </div>
      </section>

      <section>
        <h2 className="flex items-center justify-between font-bold">
          <span>
            Inbox <span className="text-sm font-normal text-neutral-500">· {pair.ward_name} की जाँचें</span>
          </span>
          {pending.length > 0 && (
            <span className="animate-pulse rounded-full bg-amber-500 px-2.5 py-0.5 text-sm font-bold text-black">
              {pending.length} नई
            </span>
          )}
        </h2>
        {requests === null ? (
          <div className="mt-3 h-24 animate-pulse rounded-2xl bg-neutral-200 dark:bg-neutral-900" />
        ) : requests.length === 0 ? (
          <p className="mt-3 rounded-2xl border border-dashed border-neutral-300 p-6 text-center text-sm text-neutral-500 dark:border-neutral-700">
            अभी कोई request नहीं। {pair.ward_name} जब कुछ खतरनाक जाँचेंगे, यहाँ 3 सेकंड में
            दिखेगा।
            <br />
            <span className="text-xs">requests appear here within 3 seconds</span>
          </p>
        ) : (
          <ul className="mt-3 space-y-3">
            {[...pending, ...decided].map((r) => (
              <RequestCard
                key={r._id}
                req={r}
                wardName={pair.ward_name}
                onDecide={decide}
                busy={actingOn === r._id}
              />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- create pair

function CreatePair({ onCreated }: { onCreated: (p: GuardianPair) => void }) {
  const [wardName, setWardName] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function create() {
    setBusy(true);
    setError("");
    try {
      const link = await api<GuardianLink>("/api/guardian/links", {
        method: "POST",
        body: JSON.stringify({ ward_name: wardName.trim(), guardian_name: guardianName.trim() }),
      });
      onCreated({
        link_id: link._id,
        pair_code: link.pair_code,
        ward_name: link.ward_name,
        guardian_name: link.guardian_name,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-2xl border border-neutral-200 bg-white p-5 dark:border-neutral-800 dark:bg-neutral-900">
      <h2 className="text-lg font-bold">अपनों की ढाल बनिए</h2>
      <p className="mt-1 text-sm text-neutral-500">
        Pair बनाइए — जब वे कुछ खतरनाक जाँचेंगे, आपसे पूछा जाएगा। Be the shield for someone
        you love: risky checks on their phone ask you first.
      </p>
      <label className="mt-4 block text-sm font-medium">
        किसकी रक्षा करनी है? · who are you protecting?
        <input
          value={wardName}
          onChange={(e) => setWardName(e.target.value)}
          placeholder="जैसे: सुनीता देवी (दादी)"
          className="mt-1 w-full rounded-xl border border-neutral-300 bg-white p-3 dark:border-neutral-700 dark:bg-neutral-950"
        />
      </label>
      <label className="mt-3 block text-sm font-medium">
        आपका नाम · your name
        <input
          value={guardianName}
          onChange={(e) => setGuardianName(e.target.value)}
          placeholder="जैसे: राहुल"
          className="mt-1 w-full rounded-xl border border-neutral-300 bg-white p-3 dark:border-neutral-700 dark:bg-neutral-950"
        />
      </label>
      {error && <p className="mt-3 text-sm font-medium text-red-600">{error}</p>}
      <button
        onClick={create}
        disabled={busy || !wardName.trim() || !guardianName.trim()}
        className="mt-4 w-full rounded-xl bg-blue-600 px-6 py-3 font-bold text-white hover:bg-blue-700 disabled:opacity-40"
      >
        {busy ? "बन रही है…" : "🛡️ ढाल जोड़ो · Create pair"}
      </button>
    </section>
  );
}

// ---------------------------------------------------------------- ward faces

function WardJoined({ guardianName, wardName }: { guardianName: string; wardName: string }) {
  return (
    <section className="rounded-2xl border-2 border-emerald-300 bg-emerald-50 p-6 text-center dark:border-emerald-800 dark:bg-emerald-950/40">
      <div className="text-5xl" aria-hidden>
        🛡️
      </div>
      <h2 className="mt-3 text-2xl font-extrabold text-emerald-900 dark:text-emerald-100">
        ढाल जुड़ गई!
      </h2>
      <p className="mt-2 text-emerald-900/90 dark:text-emerald-200/90">
        {wardName ? `${wardName} जी, ` : ""}अब हर बड़े खतरे पर {guardianName} से पूछा जाएगा —
        आपकी जेब पर परिवार की नज़र।
      </p>
      <p className="mt-1 text-sm text-emerald-800/70 dark:text-emerald-300/70">
        Paired with {guardianName}. Risky checks will ask them first.
      </p>
      <Link
        href="/check"
        className="mt-5 inline-block rounded-xl bg-emerald-600 px-8 py-3 font-bold text-white hover:bg-emerald-700"
      >
        जाँच करने चलें · Start checking →
      </Link>
      <div className="mt-4">
        <button
          onClick={() => {
            setWardPair(null);
            window.location.href = "/guardian";
          }}
          className="text-xs text-emerald-800/60 underline dark:text-emerald-300/60"
        >
          ढाल हटाएँ · unpair
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- page shell

function GuardianInner() {
  const params = useSearchParams();
  const [mode, setMode] = useState<"loading" | "ward" | "guardian-create" | "guardian-inbox">(
    "loading"
  );
  const [gPair, setGPair] = useState<GuardianPair | null>(null);
  const [ward, setWard] = useState<{ guardian_name: string; ward_name: string } | null>(null);

  useEffect(() => {
    const linkParam = params.get("link");
    if (linkParam) {
      const p = {
        link_id: linkParam,
        guardian_name: params.get("g") || "आपका guardian",
        ward_name: params.get("w") || "",
      };
      setWardPair(p);
      setWard(p);
      setMode("ward");
      return;
    }
    // stored-role priority: guardian inbox wins (the laptop must never lose its
    // console to a stray ward pairing on the same browser); explicit ?link= above
    // already forces ward mode.
    const existingGuardian = getGuardianPair();
    if (existingGuardian) {
      setGPair(existingGuardian);
      setMode("guardian-inbox");
      return;
    }
    const existingWard = getWardPair();
    if (existingWard) {
      setWard(existingWard);
      setMode("ward");
      return;
    }
    setMode("guardian-create");
  }, [params]);

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <TopBar title_hi="परिवार की ढाल" title_en="Guardian mode" />
      <main className="mx-auto max-w-xl p-4 pb-16">
        {mode === "loading" && (
          <div className="h-40 animate-pulse rounded-2xl bg-neutral-200 dark:bg-neutral-900" />
        )}
        {mode === "ward" && ward && (
          <WardJoined guardianName={ward.guardian_name} wardName={ward.ward_name} />
        )}
        {mode === "guardian-create" && (
          <CreatePair
            onCreated={(p) => {
              setGuardianPair(p);
              setGPair(p);
              setMode("guardian-inbox");
            }}
          />
        )}
        {mode === "guardian-inbox" && gPair && (
          <GuardianInbox
            pair={gPair}
            onUnpair={() => {
              setGuardianPair(null);
              setGPair(null);
              setMode("guardian-create");
            }}
          />
        )}
      </main>
    </div>
  );
}

export default function GuardianPage() {
  return (
    <Suspense fallback={null}>
      <GuardianInner />
    </Suspense>
  );
}

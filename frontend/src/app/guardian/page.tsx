"use client";

// Guardian mode (golden-path beat 5, PS bonus): family protecting family.
// Same route, three faces:
//   • guardian (laptop): create pair → BIG pair code + ward QR/link → live inbox (3s poll)
//   • ward join (phone): opens ?link=… or types the pair code → stores pairing locally
//   • ward paired: status + unpair
// Block/Allow buttons wear verdict colors deliberately — a guardian decision IS a verdict.

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
  type WardPair,
} from "@/lib/guardian";
import { S_GUARDIAN, VERDICT_UI } from "@/lib/labels";
import { fmt, pick, useLang, type Lang } from "@/lib/lang";
import TopBar from "@/components/TopBar";
import { ICheck, ICross, IShield, IShieldCheck } from "@/components/icons";

// guardian contract v2: every request carries verdict+score (pre-v2 rows may not)
function VerdictChip({
  verdict,
  score,
  lang,
}: {
  verdict?: GuardianRequest["verdict"];
  score?: number;
  lang: Lang;
}) {
  if (!verdict || !VERDICT_UI[verdict]) return null;
  const v = VERDICT_UI[verdict];
  const cls =
    v.tone === "danger"
      ? "border-danger text-dangerdeep"
      : v.tone === "caution"
        ? "border-caution text-cautiondeep"
        : "border-clear text-cleardeep";
  return (
    <span className={`plate shrink-0 border px-1.5 py-0.5 ${cls}`}>
      {pick(lang, v.label)[0]}
      {typeof score === "number" ? ` · ${score}` : ""}
    </span>
  );
}

function QrCanvas({ text }: { text: string }) {
  const ref = useRef<HTMLCanvasElement | null>(null);
  useEffect(() => {
    if (ref.current) {
      QRCode.toCanvas(ref.current, text, { width: 168, margin: 1 }).catch(() => {});
    }
  }, [text]);
  return <canvas ref={ref} className="border-2 border-ink bg-white p-1" />;
}

function timeAgo(iso: string): string {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "now";
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
  const lang = useLang();
  const [note, setNote] = useState("");
  const pending = req.status === "pending";
  return (
    <li className={`border-ink bg-paper p-4 ${pending ? "border-[3px] shadow-poster-sm" : "border-2"}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="font-bold leading-snug">
          {fmt(pick(lang, S_GUARDIAN.reqTitle)[0], { name: wardName })}
          <span className="plate mt-0.5 flex flex-wrap items-center gap-1.5 font-normal text-inksoft">
            <VerdictChip verdict={req.verdict} score={req.score} lang={lang} />
            {timeAgo(req.created_at)}
          </span>
        </p>
        {pending ? (
          <span className="plate blink shrink-0 border border-saffdeep px-1.5 py-0.5 text-saffdeep">
            {lang === "en" ? "NEW" : "नई"}
          </span>
        ) : (
          <span
            className={`plate shrink-0 border px-1.5 py-0.5 ${
              req.status === "blocked"
                ? "border-danger text-dangerdeep"
                : "border-clear text-cleardeep"
            }`}
          >
            {req.status === "blocked" ? "रोका · BLOCKED" : "ठीक कहा · ALLOWED"}
          </span>
        )}
      </div>
      <p className="mt-2 border border-line bg-paper2 p-3 text-sm leading-relaxed">
        {req.summary_hi}
      </p>
      {pending && (
        <>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={pick(lang, S_GUARDIAN.notePh)[0]}
            className="mt-3 w-full border-2 border-ink bg-paper p-2.5 text-sm placeholder:text-inksoft/60"
          />
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => onDecide(req._id, "blocked", note)}
              disabled={busy}
              className="flex flex-1 items-center justify-center gap-2 border-[3px] border-ink bg-danger px-4 py-2.5 font-bold text-paper shadow-poster-sm hover:bg-dangerdeep disabled:opacity-40"
            >
              <ICross className="h-4 w-4" /> {pick(lang, S_GUARDIAN.block)[0]}
            </button>
            <button
              onClick={() => onDecide(req._id, "allowed", note)}
              disabled={busy}
              className="flex flex-1 items-center justify-center gap-2 border-2 border-clear px-4 py-2.5 font-bold text-cleardeep hover:bg-cleartint disabled:opacity-40"
            >
              <ICheck className="h-4 w-4" /> {pick(lang, S_GUARDIAN.allow)[0]}
            </button>
          </div>
        </>
      )}
      {!pending && req.guardian_note && (
        <p className="mt-2 text-sm text-inksoft">
          {pick(lang, S_GUARDIAN.yourNote)[0]} “{req.guardian_note}”
        </p>
      )}
    </li>
  );
}

function GuardianInbox({ pair, onUnpair }: { pair: GuardianPair; onUnpair: () => void }) {
  const lang = useLang();
  const [requests, setRequests] = useState<GuardianRequest[] | null>(null);
  const [actingOn, setActingOn] = useState<string | null>(null);
  const [wardUrl, setWardUrl] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setWardUrl(
      `${window.location.origin}/guardian?link=${pair.link_id}&g=${encodeURIComponent(
        pair.guardian_name
      )}&w=${encodeURIComponent(pair.ward_name)}${
        pair.guardian_phone ? `&p=${encodeURIComponent(pair.guardian_phone)}` : ""
      }`
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
        body: JSON.stringify({ decision, note, link_id: pair.link_id }),
      });
      await load();
    } finally {
      setActingOn(null);
    }
  }

  const pending = requests?.filter((r) => r.status === "pending") ?? [];
  const decided =
    requests?.filter((r) => r.status === "allowed" || r.status === "blocked") ?? [];
  const noted = requests?.filter((r) => r.status === "noted") ?? [];

  return (
    <div className="space-y-5">
      <section className="border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="plate text-inksoft">
              {fmt(pick(lang, S_GUARDIAN.youGuard)[0], { name: pair.ward_name })} · PAIR CODE
            </p>
            <p className="mt-1 font-mono text-3xl font-semibold tracking-[0.2em]">
              {pair.pair_code}
            </p>
          </div>
          {wardUrl && <QrCanvas text={wardUrl} />}
        </div>
        <p className="mt-2 text-sm text-inksoft">
          {fmt(pick(lang, S_GUARDIAN.scanHint)[0], { name: pair.ward_name })}
        </p>
        <div className="mt-2.5 flex gap-2">
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
            className="plate border-2 border-ink px-2.5 py-1 hover:bg-paper2"
          >
            {copied ? "✓ COPIED" : pick(lang, S_GUARDIAN.copyLink)[0]}
          </button>
          <button
            onClick={onUnpair}
            className="plate border border-line px-2.5 py-1 text-inksoft hover:bg-paper2"
          >
            {pick(lang, S_GUARDIAN.newPair)[0]}
          </button>
        </div>
      </section>

      <section>
        <h2 className="flex items-center justify-between font-bold">
          <span>
            Inbox{" "}
            <span className="plate ml-1 font-normal text-inksoft">
              {fmt(pick(lang, S_GUARDIAN.inboxSub)[0], { name: pair.ward_name })}
            </span>
          </span>
          {pending.length > 0 && (
            <span className="blink bg-saffron px-2 font-mono text-sm font-semibold tabular-nums">
              {fmt(pick(lang, S_GUARDIAN.newBadge)[0], { n: pending.length })}
            </span>
          )}
        </h2>
        {requests === null ? (
          <div className="mt-3 h-24 animate-pulse border-2 border-line bg-paper2" />
        ) : requests.length === 0 ? (
          <p className="mt-3 border-2 border-dashed border-ink p-6 text-center text-sm text-inksoft">
            {fmt(pick(lang, S_GUARDIAN.inboxEmpty)[0], { name: pair.ward_name })}
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

      {/* v2 activity feed — every clean ward check lands here, quiet, no buttons */}
      {noted.length > 0 && (
        <section>
          <h2 className="font-bold">
            {pick(lang, S_GUARDIAN.activity)[0]}{" "}
            <span className="plate ml-1 font-normal text-inksoft">
              {pick(lang, S_GUARDIAN.activitySub)[0]}
            </span>
          </h2>
          <ul className="mt-2 divide-y divide-line border-y border-line">
            {noted.slice(0, 12).map((r) => (
              <li key={r._id} className="flex items-start gap-2.5 py-2.5">
                <VerdictChip verdict={r.verdict} score={r.score} lang={lang} />
                <span className="min-w-0 flex-1 truncate text-sm text-inksoft">
                  {r.summary_hi}
                </span>
                <span className="plate shrink-0 text-inksoft">{timeAgo(r.created_at)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- create pair

function CreatePair({ onCreated }: { onCreated: (p: GuardianPair) => void }) {
  const lang = useLang();
  const [wardName, setWardName] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function create() {
    setBusy(true);
    setError("");
    try {
      const link = await api<GuardianLink>("/api/guardian/links", {
        method: "POST",
        body: JSON.stringify({
          ward_name: wardName.trim(),
          guardian_name: guardianName.trim(),
          guardian_phone: guardianPhone.trim(),
        }),
      });
      onCreated({
        link_id: link._id,
        pair_code: link.pair_code,
        ward_name: link.ward_name,
        guardian_name: link.guardian_name,
        guardian_phone: link.guardian_phone || undefined,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="border-[3px] border-ink bg-paper p-5 shadow-poster-sm">
      <IShield className="h-9 w-9 text-saffdeep" />
      <h2 className="mt-2 font-display text-2xl font-bold leading-tight">
        {pick(lang, S_GUARDIAN.createTitle)[0]}
      </h2>
      <p className="mt-1 text-sm text-inksoft">{pick(lang, S_GUARDIAN.createSub)[0]}</p>
      <label className="mt-4 block">
        <span className="plate text-inksoft">{pick(lang, S_GUARDIAN.who)[0]}</span>
        <input
          value={wardName}
          onChange={(e) => setWardName(e.target.value)}
          placeholder={pick(lang, S_GUARDIAN.whoPh)[0]}
          className="mt-1 w-full border-2 border-ink bg-paper p-3 placeholder:text-inksoft/60"
        />
      </label>
      <label className="mt-3 block">
        <span className="plate text-inksoft">{pick(lang, S_GUARDIAN.yourName)[0]}</span>
        <input
          value={guardianName}
          onChange={(e) => setGuardianName(e.target.value)}
          placeholder={pick(lang, S_GUARDIAN.yourNamePh)[0]}
          className="mt-1 w-full border-2 border-ink bg-paper p-3 placeholder:text-inksoft/60"
        />
      </label>
      <label className="mt-3 block">
        <span className="plate text-inksoft">{pick(lang, S_GUARDIAN.phoneLabel)[0]}</span>
        <input
          type="tel"
          inputMode="tel"
          value={guardianPhone}
          onChange={(e) => setGuardianPhone(e.target.value)}
          placeholder="+91 98xxx xxxxx"
          className="mt-1 w-full border-2 border-ink bg-paper p-3 font-mono placeholder:text-inksoft/50"
        />
        <span className="mt-1 block text-xs text-inksoft">{pick(lang, S_GUARDIAN.phoneHint)[0]}</span>
      </label>
      {error && <p className="mt-3 text-sm font-bold text-saffdeep">{error}</p>}
      <button
        onClick={create}
        disabled={busy || !wardName.trim() || !guardianName.trim()}
        className="mt-4 w-full border-[3px] border-ink bg-saffron px-6 py-3 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:opacity-40"
      >
        {busy ? pick(lang, S_GUARDIAN.creating)[0] : pick(lang, S_GUARDIAN.createBtn)[0]}
      </button>
    </section>
  );
}

// ---------------------------------------------------------------- join by code
// Ward-side "type the code" flow — GET /api/guardian/links/resolve?pair_code=
// (docs/CONTRACTS.md; case-insensitive, bare code accepted).

function JoinByCode({ onJoined }: { onJoined: (p: WardPair) => void }) {
  const lang = useLang();
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<"" | "notfound" | "conn">("");

  async function join() {
    setBusy(true);
    setError("");
    try {
      const link = await api<GuardianLink & { error?: string }>(
        `/api/guardian/links/resolve?pair_code=${encodeURIComponent(code.trim())}`
      );
      if (link.error || !link._id) {
        setError("notfound");
        return;
      }
      onJoined({
        link_id: link._id,
        guardian_name: link.guardian_name,
        ward_name: link.ward_name,
        guardian_phone: link.guardian_phone || undefined,
      });
    } catch {
      setError("conn");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mt-5 border-2 border-ink bg-paper p-4">
      {/* unpaired state must never be silent (Saud's field test) */}
      <p className="mb-3 flex items-center gap-2 border-2 border-saffdeep bg-paper2 px-3 py-2 text-sm font-bold text-saffdeep">
        <IShield className="h-4 w-4 shrink-0" />
        {pick(lang, S_GUARDIAN.notPaired)[0]}
      </p>
      <p className="font-bold">
        {pick(lang, S_GUARDIAN.joinTitle)[0]}
        <span className="plate mt-0.5 block font-normal text-inksoft">
          {pick(lang, S_GUARDIAN.joinTitle)[1]}
        </span>
      </p>
      <div className="mt-2.5 flex gap-2">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.toUpperCase())}
          onKeyDown={(e) => {
            if (e.key === "Enter" && code.trim() && !busy) join();
          }}
          placeholder="DHAAL-4821"
          maxLength={12}
          className="w-full border-2 border-ink bg-paper p-2.5 font-mono text-lg tracking-[0.15em] placeholder:text-inksoft/40"
        />
        <button
          onClick={join}
          disabled={busy || !code.trim()}
          className="shrink-0 border-[3px] border-ink bg-paper px-4 font-display font-bold hover:bg-paper2 disabled:opacity-40"
        >
          {busy ? "…" : pick(lang, S_GUARDIAN.joinBtn)[0]}
        </button>
      </div>
      {error && (
        <p className="mt-2 text-sm font-bold text-saffdeep">
          {pick(lang, error === "notfound" ? S_GUARDIAN.joinErrNotFound : S_GUARDIAN.joinErrConn)[0]}
        </p>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- ward faces

function WardJoined({ guardianName, wardName }: { guardianName: string; wardName: string }) {
  const lang = useLang();
  const wardPrefix = wardName ? (lang === "en" ? `${wardName}, ` : `${wardName} जी, `) : "";
  return (
    <section className="border-[3px] border-ink bg-paper p-6 text-center shadow-poster">
      <IShieldCheck className="mx-auto h-14 w-14 text-saffdeep" />
      <h2 className="mt-3 font-display text-3xl font-extrabold">
        {pick(lang, S_GUARDIAN.joinedTitle)[0]}
      </h2>
      <p className="mt-2">
        {fmt(pick(lang, S_GUARDIAN.joinedSub)[0], { ward: wardPrefix, g: guardianName })}
      </p>
      <Link
        href="/check"
        className="mt-5 inline-block border-[3px] border-ink bg-saffron px-8 py-3 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
      >
        {pick(lang, S_GUARDIAN.goCheck)[0]}
      </Link>
      <div className="mt-4">
        <button
          onClick={() => {
            setWardPair(null);
            window.location.href = "/guardian";
          }}
          className="plate text-inksoft underline underline-offset-2 hover:text-ink"
        >
          {pick(lang, S_GUARDIAN.unpair)[0]}
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
        guardian_phone: params.get("p") || undefined,
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
    <div className="min-h-screen bg-paper">
      <TopBar title_hi={S_GUARDIAN.title.hi} title_en={S_GUARDIAN.title.en} />
      <main className="mx-auto max-w-xl p-4 pb-16">
        {mode === "loading" && (
          <div className="h-40 animate-pulse border-2 border-line bg-paper2" />
        )}
        {mode === "ward" && ward && (
          <WardJoined guardianName={ward.guardian_name} wardName={ward.ward_name} />
        )}
        {mode === "guardian-create" && (
          <>
            <CreatePair
              onCreated={(p) => {
                setGuardianPair(p);
                setGPair(p);
                setMode("guardian-inbox");
              }}
            />
            <JoinByCode
              onJoined={(p) => {
                setWardPair(p);
                setWard(p);
                setMode("ward");
              }}
            />
          </>
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

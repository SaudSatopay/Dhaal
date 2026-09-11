"use client";

// Golden-path beat 1–4 surface (docs/PLAN.md): paste / QR / voice → POST /api/check
// → VerdictCard. QR decoding is CLIENT-side (jsQR) — backend only ever sees qr_text.
// Visual identity: suraksha poster. Bilingual: selected language leads; the API
// `lang` field follows the toggle and drives explanation + TTS language.

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import jsQR from "jsqr";
import { api, apiForm } from "@/lib/api";
import type { Check, ExpectedIntent, InputType, TranscribeResult } from "@/lib/types";
import { EXAMPLES } from "@/lib/fixtures";
import { S_CHECK, S_COMMON, S_VERDICT } from "@/lib/labels";
import { apiLang, fmt, pick, useLang, type Lang, type LangText } from "@/lib/lang";
import TopBar from "@/components/TopBar";
import VerdictCard from "@/components/VerdictCard";
import ReportButton from "@/components/ReportButton";
import WardGate from "@/components/WardGate";
import { getWardPair, type WardPair } from "@/lib/guardian";
import { IArrowR, IMic, IPaste, IPhone, IQr, IShield, IStop } from "@/components/icons";

type Tab = "paste" | "qr" | "voice";

const TABS: { id: Tab; label: LangText; Icon: typeof IPaste }[] = [
  { id: "paste", label: S_CHECK.tabPaste, Icon: IPaste },
  { id: "qr", label: S_CHECK.tabQr, Icon: IQr },
  { id: "voice", label: S_CHECK.tabVoice, Icon: IMic },
];

// Cosmetic hint — the engine runs every detector regardless, but an honest type
// label helps the demo narration ("Dhaal saw this is a UPI collect URI").
function detectType(raw: string): InputType {
  const t = raw.trim();
  if (/^upi:\/\//i.test(t)) return "upi";
  if (/^[a-z0-9.\-_]{2,}@[a-z]{2,}$/i.test(t)) return "upi"; // VPA e.g. name@oksbi
  if (/^https?:\/\/\S+$/i.test(t) && !/\s/.test(t)) return "url";
  if (/^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}(\/\S*)?$/i.test(t)) return "url"; // bare domain
  return "text";
}

const TYPE_HINT: Record<InputType, string> = {
  text: "MESSAGE",
  url: "LINK",
  upi: "UPI",
  qr_text: "QR",
  voice_transcript: "VOICE",
};

async function decodeQrImage(file: File): Promise<string | null> {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const el = new Image();
      el.onload = () => resolve(el);
      el.onerror = () => reject(new Error("image load failed"));
      el.src = url;
    });
    // Try near-native first, then a downscale pass (helps huge screenshots).
    for (const maxSide of [1600, 800]) {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const w = Math.max(1, Math.round(img.width * scale));
      const h = Math.max(1, Math.round(img.height * scale));
      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) return null;
      ctx.drawImage(img, 0, 0, w, h);
      const data = ctx.getImageData(0, 0, w, h);
      const code = jsQR(data.data, w, h);
      if (code?.data) return code.data;
      if (scale === 1) break; // second pass only useful if first was downscaled
    }
    return null;
  } finally {
    URL.revokeObjectURL(url);
  }
}

// The engine's REAL detector families (backend/engine/*) — cycled while waiting,
// so the ~5s Claude-narration wait reads as work, not lag.
const DETECTORS = [
  "UPI COLLECT PARSER",
  "LOOKALIKE DOMAINS",
  "URL HEURISTICS",
  "SCAM-SCRIPT PATTERNS",
  "COMMUNITY BLOCKLIST",
  "CLAUDE NARRATION",
];

function ScanShield({ lang }: { lang: Lang }) {
  const [p, s] = pick(lang, S_CHECK.scanTitle);
  const [di, setDi] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = setInterval(() => setDi((i) => (i + 1) % DETECTORS.length), 480);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="flex flex-col items-center border-[3px] border-ink bg-paper p-6 shadow-poster-sm">
      <div className="h-16 w-14 text-ink">
        <svg viewBox="0 0 48 56" className="h-full w-full" aria-hidden="true">
          <path
            d="M24 3 6 9.5v13C6 33.8 13.4 41.6 24 46c10.6-4.4 18-12.2 18-23.5v-13Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinejoin="miter"
          />
          <g className="scan-line">
            <line x1="11" y1="25" x2="37" y2="25" stroke="var(--color-saffron)" strokeWidth="3" />
          </g>
        </svg>
      </div>
      <p className="mt-3 font-display text-xl font-bold">{p}</p>
      <p className="plate mt-1 text-inksoft">{s}</p>
      <p className="plate mt-3 border-t-2 border-line pt-2 text-saffdeep" aria-hidden="true">
        ▸ {DETECTORS[di]}
      </p>
    </div>
  );
}

export default function CheckPage() {
  const lang = useLang();
  const [tab, setTab] = useState<Tab>("paste");

  // shared check state
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Check | null>(null);
  const [resultFromVoice, setResultFromVoice] = useState(false);
  const resultRef = useRef<HTMLDivElement | null>(null);

  // guardian pairing (ward side) — read once on mount, localStorage is client-only
  const [wardPair, setWardPairState] = useState<WardPair | null>(null);
  useEffect(() => {
    setWardPairState(getWardPair());
  }, []);

  // paste tab
  const [payload, setPayload] = useState("");

  // H12+ intent question — QR / UPI payloads ask what the USER expected before
  // checking; "receive" meeting any upi:// fires the intent_mismatch signal.
  const [askIntent, setAskIntent] = useState<{ type: InputType; text: string } | null>(null);

  // qr tab
  const [qrPreview, setQrPreview] = useState<string | null>(null);
  const [qrDecoded, setQrDecoded] = useState<string | null>(null);
  const [qrError, setQrError] = useState(false);

  // voice tab
  const [recording, setRecording] = useState(false);
  const [recSeconds, setRecSeconds] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [micError, setMicError] = useState(false);
  const [micShort, setMicShort] = useState(false);
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const recStartRef = useRef(0); // min-1s recording guard (Saud's field test)
  const streamRef = useRef<MediaStream | null>(null); // track cleanup even if onstop never fires
  const watchdogRef = useRef<ReturnType<typeof setTimeout> | null>(null); // 20s auto-stop
  const [micRetry, setMicRetry] = useState(false); // ASR fell back — don't show fixture text
  const [micRequesting, setMicRequesting] = useState(false); // permission prompt in flight

  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  async function runCheck(
    type: InputType,
    text: string,
    speak = false,
    expectedIntent: ExpectedIntent = null
  ) {
    if (!text.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    setAskIntent(null);
    try {
      const res = await api<Check>("/api/check", {
        method: "POST",
        body: JSON.stringify({
          type,
          payload: text,
          lang: apiLang(lang),
          speak,
          expected_intent: expectedIntent,
          ward_token: wardPair?.ward_token ?? null,
        }),
      });
      setResult(res);
      setResultFromVoice(type === "voice_transcript");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  // ---------------- QR flow ----------------
  async function onQrFile(file: File | undefined | null) {
    if (!file) return;
    setQrError(false);
    setQrDecoded(null);
    setResult(null);
    setQrPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(file);
    });
    const text = await decodeQrImage(file).catch(() => null);
    if (!text) {
      setQrError(true);
      return;
    }
    setQrDecoded(text);
    // QR = money about to move — ask the intent question before checking
    setAskIntent({ type: "qr_text", text });
  }

  // ---------------- voice flow ----------------
  // iOS Safari records audio/mp4, Chrome records webm — pick what THIS browser
  // supports and name the upload accordingly (a .webm name on mp4 bytes made
  // Sarvam reject and the user saw the fixture transcript — H11 field bug).
  const MIME_CANDIDATES = ["audio/mp4", "audio/webm;codecs=opus", "audio/webm"];
  function extFor(mime: string): string {
    if (mime.includes("mp4")) return "m4a";
    if (mime.includes("ogg")) return "ogg";
    return "webm";
  }

  async function startRecording() {
    if (recording) return; // double-tap on a slow phone must not double-start
    setMicError(false);
    setMicShort(false);
    setMicRetry(false);
    setTranscript("");
    setResult(null);
    // In-app browsers (WhatsApp/Instagram webviews) hang getUserMedia forever
    // with no prompt — the H11 "button does literally nothing" symptom. Show a
    // requesting state IMMEDIATELY and race an 8s timeout so the UI always moves.
    if (!navigator.mediaDevices?.getUserMedia) {
      setMicError(true);
      return;
    }
    setMicRequesting(true);
    try {
      const stream = (await Promise.race([
        navigator.mediaDevices.getUserMedia({ audio: true }),
        new Promise<never>((_, rej) =>
          setTimeout(() => rej(new Error("mic-timeout")), 8000)
        ),
      ])) as MediaStream;
      setMicRequesting(false);
      streamRef.current = stream;
      const mime = typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported
        ? MIME_CANDIDATES.find((m) => MediaRecorder.isTypeSupported(m))
        : undefined;
      const mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        // min-1s guard: an accidental double-tap produces useless audio — discard
        // and coach, don't send it to ASR
        if (Date.now() - recStartRef.current < 1000) {
          setMicShort(true);
          return;
        }
        const type = mr.mimeType || mime || "audio/webm";
        const blob = new Blob(chunksRef.current, { type });
        await transcribeAudio(blob, extFor(type));
      };
      recRef.current = mr;
      mr.start(500);
      recStartRef.current = Date.now();
      setRecording(true);
      setRecSeconds(0);
      timerRef.current = setInterval(() => setRecSeconds((s) => s + 1), 1000);
      // watchdog: never leave the button stuck "recording" (hung permission,
      // detached handler) — auto-stop at 20s, plenty for any scam script
      watchdogRef.current = setTimeout(() => stopRecording(), 20000);
    } catch {
      setMicRequesting(false);
      setMicError(true);
      setRecording(false);
    }
  }

  function stopRecording() {
    if (watchdogRef.current) {
      clearTimeout(watchdogRef.current);
      watchdogRef.current = null;
    }
    const mr = recRef.current;
    recRef.current = null;
    try {
      if (mr && mr.state !== "inactive") mr.stop();
    } catch {
      /* already stopped */
    }
    // belt & braces: if onstop never fires, don't leak the mic
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  async function transcribeAudio(blob: Blob, ext: string = "webm") {
    setTranscribing(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("audio", blob, `clip.${ext}`);
      fd.append("lang_hint", apiLang(lang));
      const res = await apiForm<TranscribeResult>("/api/transcribe", fd);
      if (res.mocked) {
        // ASR fell back to the demo fixture — showing someone else's words as
        // "your voice" is worse than asking again (H11 field bug).
        setTranscript("");
        setMicRetry(true);
        return;
      }
      setTranscript(res.transcript);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTranscribing(false);
    }
  }

  async function checkTypedAsVoice(text: string) {
    // contract flow: typed fallback still goes through /api/transcribe
    setTranscribing(true);
    setError("");
    try {
      const res = await api<TranscribeResult>("/api/transcribe", {
        method: "POST",
        body: JSON.stringify({ typed_text: text, lang_hint: apiLang(lang) }),
      });
      setTranscript(res.transcript);
      await runCheck("voice_transcript", res.transcript, true);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTranscribing(false);
    }
  }

  const detected = detectType(payload);

  return (
    <div className="min-h-screen bg-paper">
      <TopBar title_hi={S_CHECK.title.hi} title_en={S_CHECK.title.en} />

      <main className="mx-auto max-w-xl p-4 pb-16">
        {wardPair && (
          <Link
            href="/guardian"
            className="mb-3 flex items-center justify-center gap-2 border-2 border-ink bg-paper2 px-3 py-2 text-center text-sm font-semibold hover:bg-paper"
          >
            <IShield className="h-4 w-4 shrink-0 text-saffdeep" />
            {fmt(pick(lang, S_CHECK.wardBanner)[0], { name: wardPair.guardian_name })}
            <span aria-hidden="true" className="text-inksoft">→</span>
          </Link>
        )}

        {/* Tabs — joined signage segments */}
        <div role="tablist" aria-label="input method" className="flex border-[3px] border-ink bg-paper">
          {TABS.map((t, i) => {
            const [tp, ts] = pick(lang, t.label);
            return (
              <button
                key={t.id}
                role="tab"
                aria-selected={tab === t.id}
                onClick={() => setTab(t.id)}
                className={`flex-1 px-2 py-2.5 transition-colors ${
                  i < TABS.length - 1 ? "border-r-2 border-ink" : ""
                } ${tab === t.id ? "bg-ink text-paper" : "hover:bg-paper2"}`}
              >
                <t.Icon className="mx-auto h-5 w-5" />
                <span className="mt-1 block text-sm font-bold leading-tight">{tp}</span>
                <span className={`plate block ${tab === t.id ? "text-paper/70" : "text-inksoft"}`}>
                  {ts}
                </span>
              </button>
            );
          })}
        </div>

        {/* ---------------- Paste tab ---------------- */}
        {tab === "paste" && (
          <section className="mt-4 border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
            <label htmlFor="paste-box" className="block font-bold">
              {pick(lang, S_CHECK.pasteLabel)[0]}
              <span className="plate mt-0.5 block font-normal text-inksoft">
                {pick(lang, S_CHECK.pasteLabel)[1]}
              </span>
            </label>
            <textarea
              id="paste-box"
              rows={5}
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              placeholder={pick(lang, S_CHECK.pastePh)[0]}
              className="mt-2 w-full border-2 border-ink bg-paper p-3 text-base outline-none placeholder:text-inksoft/60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-saffron"
            />
            <div className="mt-2.5 flex items-end justify-between gap-3">
              <span className="plate text-inksoft">
                {payload.trim()
                  ? `${pick(lang, S_CHECK.detected)[0]} · ${TYPE_HINT[detected]}`
                  : ""}
              </span>
              <button
                onClick={() =>
                  detected === "upi"
                    ? setAskIntent({ type: "upi", text: payload })
                    : runCheck(detected, payload)
                }
                disabled={busy || !payload.trim()}
                className="shrink-0 border-[3px] border-ink bg-saffron px-6 py-2.5 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:opacity-40"
              >
                {busy ? pick(lang, S_COMMON.checking)[0] : pick(lang, S_COMMON.check)[0]}
              </button>
            </div>

            <div className="mt-4 border-t-2 border-line pt-3">
              <div className="plate text-inksoft">
                {pick(lang, S_CHECK.tryExample)[0]} · {pick(lang, S_CHECK.tryExample)[1]}
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={ex.label.en}
                    onClick={() => {
                      setPayload(ex.text);
                      setResult(null);
                    }}
                    className="border-2 border-ink bg-paper px-2.5 py-1 text-xs font-semibold hover:bg-paper2"
                  >
                    <span className="mr-1.5 font-mono text-saffdeep">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {pick(lang, ex.label)[0]}
                  </button>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ---------------- QR tab ---------------- */}
        {tab === "qr" && (
          <section className="mt-4 border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
            <label htmlFor="qr-file" className="block cursor-pointer">
              <span className="font-bold">{pick(lang, S_CHECK.qrLabel)[0]}</span>
              <span className="plate mt-0.5 block text-inksoft">
                {pick(lang, S_CHECK.qrSub)[0]}
              </span>
              <div className="mt-3 flex min-h-36 items-center justify-center border-2 border-dashed border-ink bg-paper2 p-4 text-center">
                {qrPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={qrPreview} alt="uploaded QR" className="max-h-48 border-2 border-ink" />
                ) : (
                  <IQr className="h-12 w-12 text-inksoft" />
                )}
              </div>
            </label>
            <input
              id="qr-file"
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => onQrFile(e.target.files?.[0])}
            />
            {qrDecoded && (
              <p className="mt-3 break-all border border-line bg-paper2 p-2 font-mono text-xs">
                <span className="plate mr-1 text-inksoft">{pick(lang, S_CHECK.qrDecoded)[0]} →</span>
                {qrDecoded}
              </p>
            )}
            {qrError && (
              <p className="mt-3 text-sm font-bold text-saffdeep">
                {pick(lang, S_CHECK.qrError)[0]}
              </p>
            )}
          </section>
        )}

        {/* ---------------- Voice tab ---------------- */}
        {tab === "voice" && (
          <section className="mt-4 border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
            <div className="text-center">
              <p className="font-bold">
                {pick(lang, S_CHECK.voiceLabel)[0]}
                <span className="plate mt-0.5 block font-normal text-inksoft">
                  {pick(lang, S_CHECK.voiceLabel)[1]}
                </span>
              </p>
              <span className="relative mt-4 inline-block">
                {recording && (
                  <span className="pulse-ring absolute inset-0 rounded-full border-2 border-danger" aria-hidden="true" />
                )}
                <button
                  onClick={recording ? stopRecording : startRecording}
                  disabled={transcribing || micRequesting}
                  className={`flex h-24 w-24 items-center justify-center rounded-full border-[3px] border-ink transition-colors ${
                    recording ? "bg-danger text-paper" : "bg-saffron text-ink shadow-poster-sm"
                  } disabled:opacity-40`}
                  aria-label={recording ? "stop recording" : "start recording"}
                >
                  {recording ? <IStop className="h-9 w-9" /> : <IMic className="h-9 w-9" />}
                </button>
              </span>
              <div className="mt-2.5 min-h-5 text-sm text-inksoft">
                {micRequesting ? (
                  <span className="blink font-semibold text-ink">
                    {lang === "hi"
                      ? "माइक की permission माँग रहे हैं… (popup देखें)"
                      : "Requesting mic permission… (watch for the popup)"}
                  </span>
                ) : recording ? (
                  <span className="font-semibold text-dangerdeep">
                    {pick(lang, S_CHECK.recListening)[0]}{" "}
                    <span className="font-mono font-semibold">{recSeconds}s</span> —{" "}
                    {pick(lang, S_CHECK.recStopHint)[0]}
                  </span>
                ) : transcribing ? (
                  <span className="blink font-semibold text-ink">
                    {pick(lang, S_CHECK.transcribing)[0]}
                  </span>
                ) : (
                  `${pick(lang, S_CHECK.tapSpeak)[0]} · ${pick(lang, S_CHECK.tapSpeak)[1]}`
                )}
              </div>
              {micShort && !recording && (
                <p className="mt-2 text-sm font-bold text-saffdeep">
                  {pick(lang, S_CHECK.micShort)[0]}
                </p>
              )}
              {micRetry && !recording && !transcribing && (
                <p className="mt-2 text-sm font-bold text-saffdeep">
                  {lang === "hi"
                    ? "आवाज़ साफ़ समझ नहीं आई — फिर से बोलें, या नीचे टाइप करें।"
                    : "Couldn't hear that clearly — speak again, or type below."}
                </p>
              )}
              {micError && (
                <div className="mt-3 border-2 border-ink bg-paper2 p-3 text-left">
                  <p className="font-bold">{pick(lang, S_CHECK.micErrTitle)[0]}</p>
                  <p className="mt-0.5 text-sm text-inksoft">{pick(lang, S_CHECK.micError)[0]}</p>
                  <p className="mt-1.5 text-sm font-bold text-saffdeep">
                    {pick(lang, S_CHECK.micErrPoint)[0]}
                  </p>
                </div>
              )}
            </div>

            {transcript && (
              <div className="mt-4">
                <label htmlFor="transcript-box" className="plate text-inksoft">
                  {pick(lang, S_CHECK.heard)[0]}
                </label>
                <textarea
                  id="transcript-box"
                  rows={3}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="mt-1 w-full border-2 border-ink bg-paper p-3 text-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-saffron"
                />
                <button
                  onClick={() => runCheck("voice_transcript", transcript, true)}
                  disabled={busy || !transcript.trim()}
                  className="mt-2 w-full border-[3px] border-ink bg-saffron px-6 py-2.5 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:opacity-40"
                >
                  {busy ? pick(lang, S_COMMON.checking)[0] : pick(lang, S_CHECK.checkThis)[0]}
                </button>
              </div>
            )}

            <div className="mt-5 border-t-2 border-line pt-4">
              <label htmlFor="typed-voice" className="plate text-inksoft">
                {pick(lang, S_CHECK.typedLabel)[0]}
              </label>
              <TypedVoiceBox
                lang={lang}
                disabled={busy || transcribing || recording}
                onSubmit={checkTypedAsVoice}
              />
            </div>
          </section>
        )}

        {/* ---------------- Shared result area ---------------- */}
        <div ref={resultRef} className="mt-5 scroll-mt-20">
          {/* H12+ intent question — three poster chips before a QR/UPI check */}
          {askIntent && !busy && (
            <section className="chit-in border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
              <p className="font-display text-xl font-bold leading-tight">
                {pick(lang, S_CHECK.intentQ)[0]}
              </p>
              <p className="plate mt-0.5 text-inksoft">{pick(lang, S_CHECK.intentQ)[1]}</p>
              <div className="mt-3 grid gap-2">
                {(
                  [
                    { t: S_CHECK.intentPay, v: "pay" as ExpectedIntent, plate: "PAY" },
                    { t: S_CHECK.intentReceive, v: "receive" as ExpectedIntent, plate: "RECEIVE" },
                    { t: S_CHECK.intentJust, v: null as ExpectedIntent, plate: "CHECK" },
                  ] as const
                ).map((c) => (
                  <button
                    key={c.plate}
                    onClick={() => runCheck(askIntent.type, askIntent.text, false, c.v)}
                    className="flex items-center justify-between border-[3px] border-ink bg-paper px-4 py-2.5 text-left font-bold hover:bg-saffron"
                  >
                    <span>
                      {pick(lang, c.t)[0]}
                      <span className="plate ml-2 font-normal text-inksoft">· {c.plate}</span>
                    </span>
                    <IArrowR className="h-4 w-4 shrink-0" />
                  </button>
                ))}
              </div>
            </section>
          )}

          {busy && <ScanShield lang={lang} />}
          {error && (
            <div className="border-[3px] border-ink bg-paper">
              <div className="hazard-saffron h-3 border-b-2 border-ink" aria-hidden="true" />
              <div className="p-4">
                <p className="font-bold">
                  {pick(lang, S_CHECK.errTitle)[0]} · {pick(lang, S_CHECK.errTitle)[1]}
                </p>
                <p className="mt-1 break-all font-mono text-xs text-inksoft">{error}</p>
                <p className="mt-2 text-sm text-inksoft">{pick(lang, S_CHECK.errHint)[0]}</p>
              </div>
            </div>
          )}
          {/* H14 first-class assessment: needs_context / unsupported_input
              carry NO verdict — render the question or the parse failure, and
              never a green card. (The old client-side upi:// exemption is gone:
              the backend now parses URIs into facts and assesses correctly.) */}
          {result && !busy && result.assessment !== "assessed" ? (
            <section
              className={`chit-in border-[3px] bg-paper p-4 ${
                result.assessment === "unsupported_input" ? "border-ink" : "border-caution"
              }`}
            >
              <p className="plate text-cautiondeep">
                {result.assessment === "unsupported_input"
                  ? `${pick(lang, S_CHECK.unsupTitle)[0]} · ${pick(lang, S_CHECK.unsupTitle)[1]}`
                  : `${pick(lang, S_CHECK.ctxTitle)[0]} · ${pick(lang, S_CHECK.ctxTitle)[1]}`}
              </p>
              <p className="mt-2 text-lg font-semibold leading-snug">
                {lang === "en" ? result.explanation_en : result.explanation_hi}
              </p>
              <p className="mt-1.5 text-sm text-inksoft">
                {lang === "en" ? result.explanation_hi : result.explanation_en}
              </p>
              {/* sub-threshold findings still shown — thin input, honest output */}
              {result.signals.filter((s) => s.weight > 0).length > 0 && (
                <ul className="mt-2 space-y-1">
                  {result.signals
                    .filter((s) => s.weight > 0)
                    .slice(0, 2)
                    .map((s) => (
                      <li key={s.id} className="plate text-inksoft">
                        ▸ {lang === "en" ? s.title_en : s.title_hi} (+{s.weight})
                      </li>
                    ))}
                </ul>
              )}
              <button
                onClick={() => {
                  setResult(null);
                  setTab("paste");
                  setTimeout(() => document.getElementById("paste-box")?.focus(), 50);
                }}
                className="mt-3 border-[3px] border-ink bg-saffron px-5 py-2 font-display font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
              >
                {result.assessment === "unsupported_input"
                  ? pick(lang, S_CHECK.unsupAction)[0]
                  : pick(lang, S_CHECK.ctxAction)[0]}
              </button>
            </section>
          ) : (
            <>
              {/* H14 honesty strips: dead pairing + degraded community intel */}
              {result && !busy && result.guardian_delivery === "unlinked" && wardPair && (
                <p className="mb-3 border-2 border-saffdeep bg-paper2 px-3 py-2 text-sm font-bold text-saffdeep">
                  {pick(lang, S_CHECK.wardUnlinked)[0]}
                </p>
              )}
              {result && !busy && result.community_data === "degraded" && (
                <p className="mb-3 border border-line bg-paper2 px-3 py-2 text-xs text-inksoft">
                  {pick(lang, S_CHECK.communityDegraded)[0]}
                </p>
              )}
              {result && !busy && result.guardian_request_id && wardPair && (
                <div className="mb-4">
                  <WardGate
                    key={result.guardian_request_id}
                    requestId={result.guardian_request_id}
                    guardianName={wardPair.guardian_name}
                    checkVerdict={result.verdict}
                  />
                </div>
              )}
              {result && !busy && (
                <VerdictCard
                  check={result}
                  theater
                  autoSpeak={resultFromVoice}
                  actions={
                    <div className="space-y-2.5">
                      {/* trusted call — the STORED guardian number only, never one
                          from the checked message */}
                      {result.verdict === "danger" && wardPair?.guardian_phone && (
                        <a
                          href={`tel:${wardPair.guardian_phone}`}
                          className="flex w-full items-center justify-center gap-2.5 border-[3px] border-ink bg-saffron px-4 py-2.5 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                        >
                          <IPhone className="h-5 w-5" />
                          {fmt(pick(lang, S_VERDICT.callAsk)[0], { name: wardPair.guardian_name })}
                        </a>
                      )}
                      <ReportButton
                        key={result._id}
                        payload={result.input.payload}
                        defaultCategory={result.scam_category}
                      />
                    </div>
                  }
                />
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}

function TypedVoiceBox({
  lang,
  disabled,
  onSubmit,
}: {
  lang: Lang;
  disabled: boolean;
  onSubmit: (text: string) => void;
}) {
  const [text, setText] = useState("");
  return (
    <div className="mt-1.5 flex gap-2">
      <input
        id="typed-voice"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && text.trim() && !disabled) onSubmit(text);
        }}
        placeholder={pick(lang, S_CHECK.typedPh)[0]}
        className="w-full border-2 border-ink bg-paper p-3 text-base placeholder:text-inksoft/60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-saffron"
      />
      <button
        onClick={() => onSubmit(text)}
        disabled={disabled || !text.trim()}
        className="shrink-0 border-[3px] border-ink bg-paper px-4 font-display font-bold hover:bg-paper2 disabled:opacity-40"
      >
        {pick(lang, S_CHECK.typedBtn)[0]}
      </button>
    </div>
  );
}

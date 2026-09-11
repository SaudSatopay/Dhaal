"use client";

// Golden-path beat 1–4 surface (docs/PLAN.md): paste / QR / voice → POST /api/check
// → VerdictCard. QR decoding is CLIENT-side (jsQR) — backend only ever sees qr_text.
// Visual identity: suraksha poster — paper ground, ink borders, saffron action.

import { useEffect, useRef, useState } from "react";
import jsQR from "jsqr";
import { api, apiForm } from "@/lib/api";
import type { Check, InputType, TranscribeResult } from "@/lib/types";
import { EXAMPLES } from "@/lib/fixtures";
import TopBar from "@/components/TopBar";
import VerdictCard from "@/components/VerdictCard";
import ReportButton from "@/components/ReportButton";
import WardGate from "@/components/WardGate";
import { getWardPair, type WardPair } from "@/lib/guardian";
import { IMic, IPaste, IQr, IShield, IStop } from "@/components/icons";

type Tab = "paste" | "qr" | "voice";

const TABS: { id: Tab; hi: string; en: string; Icon: typeof IPaste }[] = [
  { id: "paste", hi: "पेस्ट करें", en: "PASTE", Icon: IPaste },
  { id: "qr", hi: "QR फोटो", en: "QR IMAGE", Icon: IQr },
  { id: "voice", hi: "बोलिए", en: "VOICE", Icon: IMic },
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

function ScanShield() {
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
      <p className="mt-3 font-display text-xl font-bold">जाँच हो रही है…</p>
      <p className="plate mt-1 text-inksoft">DHAAL IS CHECKING</p>
    </div>
  );
}

export default function CheckPage() {
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

  // qr tab
  const [qrPreview, setQrPreview] = useState<string | null>(null);
  const [qrDecoded, setQrDecoded] = useState<string | null>(null);
  const [qrError, setQrError] = useState("");

  // voice tab
  const [recording, setRecording] = useState(false);
  const [recSeconds, setRecSeconds] = useState(0);
  const [transcribing, setTranscribing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [micError, setMicError] = useState("");
  const recRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (result && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [result]);

  async function runCheck(type: InputType, text: string, speak = false) {
    if (!text.trim()) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const res = await api<Check>("/api/check", {
        method: "POST",
        body: JSON.stringify({
          type,
          payload: text,
          lang: "hi-IN",
          speak,
          ward_link_id: wardPair?.link_id ?? null,
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
    setQrError("");
    setQrDecoded(null);
    setResult(null);
    setQrPreview((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(file);
    });
    const text = await decodeQrImage(file).catch(() => null);
    if (!text) {
      setQrError("QR पढ़ नहीं पाए — साफ़, सीधा screenshot आज़माएँ · could not read the QR");
      return;
    }
    setQrDecoded(text);
    await runCheck("qr_text", text);
  }

  // ---------------- voice flow ----------------
  async function startRecording() {
    setMicError("");
    setTranscript("");
    setResult(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mr.mimeType || "audio/webm" });
        await transcribeAudio(blob);
      };
      recRef.current = mr;
      mr.start();
      setRecording(true);
      setRecSeconds(0);
      timerRef.current = setInterval(() => setRecSeconds((s) => s + 1), 1000);
    } catch {
      setMicError(
        "माइक नहीं मिला या permission नहीं मिली — नीचे टाइप करके जाँचें · mic unavailable, use the typed box below"
      );
    }
  }

  function stopRecording() {
    recRef.current?.stop();
    recRef.current = null;
    setRecording(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }

  async function transcribeAudio(blob: Blob) {
    setTranscribing(true);
    setError("");
    try {
      const fd = new FormData();
      fd.append("audio", blob, "clip.webm");
      fd.append("lang_hint", "hi-IN");
      const res = await apiForm<TranscribeResult>("/api/transcribe", fd);
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
        body: JSON.stringify({ typed_text: text, lang_hint: "hi-IN" }),
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
      <TopBar title_hi="जाँच करो" title_en="CHECK BEFORE YOU PAY" />

      <main className="mx-auto max-w-xl p-4 pb-16">
        {wardPair && (
          <p className="mb-3 flex items-center justify-center gap-2 border-2 border-ink bg-paper2 px-3 py-2 text-center text-sm font-semibold">
            <IShield className="h-4 w-4 shrink-0 text-saffdeep" />
            {wardPair.guardian_name} आपकी ढाल हैं — बड़े खतरे पर उनसे पूछा जाएगा
          </p>
        )}

        {/* Tabs — joined signage segments */}
        <div role="tablist" aria-label="input method" className="flex border-[3px] border-ink bg-paper">
          {TABS.map((t, i) => (
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
              <span className="mt-1 block text-sm font-bold leading-tight">{t.hi}</span>
              <span className={`plate block ${tab === t.id ? "text-paper/70" : "text-inksoft"}`}>
                {t.en}
              </span>
            </button>
          ))}
        </div>

        {/* ---------------- Paste tab ---------------- */}
        {tab === "paste" && (
          <section className="mt-4 border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
            <label htmlFor="paste-box" className="block font-bold">
              संदेश, link, UPI ID या नंबर यहाँ डालें
              <span className="plate mt-0.5 block font-normal text-inksoft">
                PASTE THE MESSAGE, LINK, UPI ID OR NUMBER
              </span>
            </label>
            <textarea
              id="paste-box"
              rows={5}
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              placeholder="जैसे: आपका खाता बंद हो जाएगा, KYC करें…"
              className="mt-2 w-full border-2 border-ink bg-paper p-3 text-base outline-none placeholder:text-inksoft/60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-saffron"
            />
            <div className="mt-2.5 flex items-end justify-between gap-3">
              <span className="plate text-inksoft">
                {payload.trim() ? `समझा गया · ${TYPE_HINT[detected]}` : ""}
              </span>
              <button
                onClick={() => runCheck(detected, payload)}
                disabled={busy || !payload.trim()}
                className="shrink-0 border-[3px] border-ink bg-saffron px-6 py-2.5 font-display text-lg font-bold shadow-poster-sm transition-transform active:translate-x-[2px] active:translate-y-[2px] active:shadow-none disabled:opacity-40"
              >
                {busy ? "जाँच जारी…" : "जाँच करो"}
              </button>
            </div>

            <div className="mt-4 border-t-2 border-line pt-3">
              <div className="plate text-inksoft">आज़मा कर देखिए · TRY AN EXAMPLE</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={ex.label_en}
                    onClick={() => {
                      setPayload(ex.text);
                      setResult(null);
                    }}
                    className="border-2 border-ink bg-paper px-2.5 py-1 text-xs font-semibold hover:bg-paper2"
                  >
                    <span className="mr-1.5 font-mono text-saffdeep">{String(i + 1).padStart(2, "0")}</span>
                    {ex.label_hi}
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
              <span className="font-bold">QR का photo या screenshot चुनें</span>
              <span className="plate mt-0.5 block text-inksoft">
                DECODED ON YOUR PHONE — THE IMAGE NEVER LEAVES IT
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
                <span className="plate mr-1 text-inksoft">DECODED →</span>
                {qrDecoded}
              </p>
            )}
            {qrError && <p className="mt-3 text-sm font-bold text-saffdeep">{qrError}</p>}
          </section>
        )}

        {/* ---------------- Voice tab ---------------- */}
        {tab === "voice" && (
          <section className="mt-4 border-[3px] border-ink bg-paper p-4 shadow-poster-sm">
            <div className="text-center">
              <p className="font-bold">
                जो call आया था, वही बोल कर सुनाइए
                <span className="plate mt-0.5 block font-normal text-inksoft">
                  REPEAT WHAT THE CALLER SAID — DHAAL WILL LISTEN
                </span>
              </p>
              <span className="relative mt-4 inline-block">
                {recording && (
                  <span className="pulse-ring absolute inset-0 rounded-full border-2 border-danger" aria-hidden="true" />
                )}
                <button
                  onClick={recording ? stopRecording : startRecording}
                  disabled={transcribing}
                  className={`flex h-24 w-24 items-center justify-center rounded-full border-[3px] border-ink transition-colors ${
                    recording ? "bg-danger text-paper" : "bg-saffron text-ink shadow-poster-sm"
                  } disabled:opacity-40`}
                  aria-label={recording ? "stop recording" : "start recording"}
                >
                  {recording ? <IStop className="h-9 w-9" /> : <IMic className="h-9 w-9" />}
                </button>
              </span>
              <div className="mt-2.5 h-5 text-sm text-inksoft">
                {recording ? (
                  <>
                    सुन रहे हैं… <span className="font-mono font-semibold text-ink">{recSeconds}s</span> — रोकने पर जाँच होगी
                  </>
                ) : transcribing ? (
                  "समझ रहे हैं… · transcribing"
                ) : (
                  "दबाइए और बोलिए · tap and speak"
                )}
              </div>
              {micError && <p className="mt-2 text-sm font-bold text-saffdeep">{micError}</p>}
            </div>

            {transcript && (
              <div className="mt-4">
                <label htmlFor="transcript-box" className="plate text-inksoft">
                  यह सुना गया — गलत हो तो सुधारें · HEARD THIS, EDIT IF WRONG
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
                  {busy ? "जाँच जारी…" : "इसकी जाँच करो"}
                </button>
              </div>
            )}

            <div className="mt-5 border-t-2 border-line pt-4">
              <label htmlFor="typed-voice" className="plate text-inksoft">
                या टाइप करें (MIC न चले तो) · OR TYPE IT INSTEAD
              </label>
              <TypedVoiceBox
                disabled={busy || transcribing || recording}
                onSubmit={checkTypedAsVoice}
              />
            </div>
          </section>
        )}

        {/* ---------------- Shared result area ---------------- */}
        <div ref={resultRef} className="mt-5 scroll-mt-20">
          {busy && <ScanShield />}
          {error && (
            <div className="border-[3px] border-ink bg-paper">
              <div className="hazard-saffron h-3 border-b-2 border-ink" aria-hidden="true" />
              <div className="p-4">
                <p className="font-bold">जाँच नहीं हो पाई · CHECK FAILED</p>
                <p className="mt-1 break-all font-mono text-xs text-inksoft">{error}</p>
                <p className="mt-2 text-sm text-inksoft">
                  Internet जाँच कर दोबारा कोशिश करें · check connection and retry
                </p>
              </div>
            </div>
          )}
          {result && !busy && result.guardian_request_id && wardPair && (
            <div className="mb-4">
              <WardGate
                key={result.guardian_request_id}
                requestId={result.guardian_request_id}
                guardianName={wardPair.guardian_name}
              />
            </div>
          )}
          {result && !busy && (
            <VerdictCard
              check={result}
              autoSpeak={resultFromVoice}
              actions={
                <ReportButton
                  key={result._id}
                  payload={result.input.payload}
                  defaultCategory={result.scam_category}
                />
              }
            />
          )}
        </div>
      </main>
    </div>
  );
}

function TypedVoiceBox({
  disabled,
  onSubmit,
}: {
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
        placeholder="call में जो कहा गया…"
        className="w-full border-2 border-ink bg-paper p-3 text-base placeholder:text-inksoft/60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-saffron"
      />
      <button
        onClick={() => onSubmit(text)}
        disabled={disabled || !text.trim()}
        className="shrink-0 border-[3px] border-ink bg-paper px-4 font-display font-bold hover:bg-paper2 disabled:opacity-40"
      >
        जाँचें
      </button>
    </div>
  );
}

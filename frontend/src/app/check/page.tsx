"use client";

// Golden-path beat 1–4 surface (docs/PLAN.md): paste / QR / voice → POST /api/check
// → VerdictCard. QR decoding is CLIENT-side (jsQR) — backend only ever sees qr_text.

import { useEffect, useRef, useState } from "react";
import jsQR from "jsqr";
import { api, apiForm } from "@/lib/api";
import type { Check, InputType, TranscribeResult } from "@/lib/types";
import { EXAMPLES } from "@/lib/fixtures";
import TopBar from "@/components/TopBar";
import VerdictCard from "@/components/VerdictCard";

type Tab = "paste" | "qr" | "voice";

const TABS: { id: Tab; hi: string; en: string; icon: string }[] = [
  { id: "paste", hi: "पेस्ट करें", en: "Paste", icon: "📋" },
  { id: "qr", hi: "QR फोटो", en: "QR image", icon: "📷" },
  { id: "voice", hi: "बोलिए", en: "Voice", icon: "🎤" },
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
  text: "message · टेक्स्ट",
  url: "link · लिंक",
  upi: "UPI",
  qr_text: "QR",
  voice_transcript: "आवाज़ · voice",
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

export default function CheckPage() {
  const [tab, setTab] = useState<Tab>("paste");

  // shared check state
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Check | null>(null);
  const resultRef = useRef<HTMLDivElement | null>(null);

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
        body: JSON.stringify({ type, payload: text, lang: "hi-IN", speak }),
      });
      setResult(res);
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
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950">
      <TopBar title_hi="जाँच करो" title_en="Check before you pay" />

      <main className="mx-auto max-w-xl p-4 pb-16">
        {/* Tabs */}
        <div
          role="tablist"
          aria-label="input method"
          className="grid grid-cols-3 gap-1 rounded-xl bg-neutral-200 p-1 dark:bg-neutral-900"
        >
          {TABS.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              className={`rounded-lg px-2 py-2 text-sm font-medium transition ${
                tab === t.id
                  ? "bg-white shadow dark:bg-neutral-700"
                  : "text-neutral-600 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:bg-neutral-800"
              }`}
            >
              <span className="block text-base">{t.icon}</span>
              <span className="block leading-tight">{t.hi}</span>
              <span className="block text-[11px] text-neutral-500">{t.en}</span>
            </button>
          ))}
        </div>

        {/* ---------------- Paste tab ---------------- */}
        {tab === "paste" && (
          <section className="mt-4 rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
            <label htmlFor="paste-box" className="block font-semibold">
              संदेश, link, UPI ID या नंबर यहाँ डालें
              <span className="block text-xs font-normal text-neutral-500">
                paste the message, link, UPI ID or phone number
              </span>
            </label>
            <textarea
              id="paste-box"
              rows={5}
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              placeholder="जैसे: आपका खाता बंद हो जाएगा, KYC करें…"
              className="mt-2 w-full rounded-xl border border-neutral-300 bg-white p-3 text-base outline-none focus:border-blue-500 dark:border-neutral-700 dark:bg-neutral-950"
            />
            <div className="mt-2 flex items-center justify-between gap-2">
              <span className="text-xs text-neutral-500">
                {payload.trim() ? `समझा गया · detected: ${TYPE_HINT[detected]}` : ""}
              </span>
              <button
                onClick={() => runCheck(detected, payload)}
                disabled={busy || !payload.trim()}
                className="rounded-xl bg-blue-600 px-6 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:opacity-40"
              >
                {busy ? "जाँच जारी…" : "जाँच करो · Check"}
              </button>
            </div>

            <div className="mt-4 border-t border-neutral-200 pt-3 dark:border-neutral-800">
              <div className="text-xs font-medium text-neutral-500">
                आज़मा कर देखिए · try an example
              </div>
              <div className="mt-2 flex flex-wrap gap-2">
                {EXAMPLES.map((ex) => (
                  <button
                    key={ex.label_en}
                    onClick={() => {
                      setPayload(ex.text);
                      setResult(null);
                    }}
                    className="rounded-full border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
                  >
                    {ex.label_hi} <span className="text-neutral-500">· {ex.label_en}</span>
                  </button>
                ))}
              </div>
            </div>
          </section>
        )}

        {/* ---------------- QR tab ---------------- */}
        {tab === "qr" && (
          <section className="mt-4 rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
            <label htmlFor="qr-file" className="block cursor-pointer">
              <span className="font-semibold">QR का photo या screenshot चुनें</span>
              <span className="block text-xs text-neutral-500">
                upload a photo / screenshot of the QR — decoded on YOUR phone, image never leaves it
              </span>
              <div className="mt-3 flex min-h-36 items-center justify-center rounded-xl border-2 border-dashed border-neutral-300 p-4 text-center hover:border-blue-500 dark:border-neutral-700">
                {qrPreview ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={qrPreview} alt="uploaded QR" className="max-h-48 rounded-lg" />
                ) : (
                  <span className="text-4xl">📷</span>
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
              <p className="mt-3 break-all rounded-lg bg-neutral-100 p-2 font-mono text-xs dark:bg-neutral-800">
                <span className="font-sans font-medium text-neutral-500">decoded → </span>
                {qrDecoded}
              </p>
            )}
            {qrError && <p className="mt-3 text-sm font-medium text-red-600">{qrError}</p>}
          </section>
        )}

        {/* ---------------- Voice tab ---------------- */}
        {tab === "voice" && (
          <section className="mt-4 rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
            <div className="text-center">
              <p className="font-semibold">
                जो call आया था, वही बोल कर सुनाइए
                <span className="block text-xs font-normal text-neutral-500">
                  repeat what the caller said — Dhaal will listen
                </span>
              </p>
              <button
                onClick={recording ? stopRecording : startRecording}
                disabled={transcribing}
                className={`mt-4 h-24 w-24 rounded-full text-4xl shadow-lg transition ${
                  recording
                    ? "animate-pulse bg-red-600 text-white"
                    : "bg-blue-600 text-white hover:bg-blue-700"
                } disabled:opacity-40`}
                aria-label={recording ? "stop recording" : "start recording"}
              >
                {recording ? "⏹" : "🎤"}
              </button>
              <div className="mt-2 h-5 text-sm text-neutral-500">
                {recording
                  ? `सुन रहे हैं… ${recSeconds}s — बोलना बंद करने पर ⏹ दबाएँ`
                  : transcribing
                    ? "समझ रहे हैं… · transcribing"
                    : "दबाइए और बोलिए · tap and speak"}
              </div>
              {micError && <p className="mt-2 text-sm font-medium text-amber-600">{micError}</p>}
            </div>

            {transcript && (
              <div className="mt-4">
                <label htmlFor="transcript-box" className="text-xs font-medium text-neutral-500">
                  यह सुना गया — गलत हो तो सुधारें · heard this, edit if wrong
                </label>
                <textarea
                  id="transcript-box"
                  rows={3}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-neutral-300 bg-white p-3 text-base dark:border-neutral-700 dark:bg-neutral-950"
                />
                <button
                  onClick={() => runCheck("voice_transcript", transcript, true)}
                  disabled={busy || !transcript.trim()}
                  className="mt-2 w-full rounded-xl bg-blue-600 px-6 py-2.5 font-semibold text-white hover:bg-blue-700 disabled:opacity-40"
                >
                  {busy ? "जाँच जारी…" : "इसकी जाँच करो · Check this"}
                </button>
              </div>
            )}

            <div className="mt-5 border-t border-neutral-200 pt-4 dark:border-neutral-800">
              <label htmlFor="typed-voice" className="text-xs font-medium text-neutral-500">
                या टाइप करें (mic न चले तो) · or type it instead
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
          {busy && (
            <div className="animate-pulse rounded-2xl border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
              <div className="h-16 rounded-xl bg-neutral-200 dark:bg-neutral-800" />
              <div className="mt-3 h-4 w-3/4 rounded bg-neutral-200 dark:bg-neutral-800" />
              <div className="mt-2 h-4 w-1/2 rounded bg-neutral-200 dark:bg-neutral-800" />
              <p className="mt-3 text-center text-sm text-neutral-500">
                ढाल जाँच रही है… · Dhaal is checking
              </p>
            </div>
          )}
          {error && (
            <div className="rounded-2xl border-2 border-red-300 bg-red-50 p-4 text-sm dark:border-red-900 dark:bg-red-950/40">
              <p className="font-semibold text-red-700 dark:text-red-300">
                जाँच नहीं हो पाई · check failed
              </p>
              <p className="mt-1 break-all text-red-600 dark:text-red-400">{error}</p>
              <p className="mt-2 text-neutral-600 dark:text-neutral-400">
                Internet जाँच कर दोबारा कोशिश करें · check connection and retry
              </p>
            </div>
          )}
          {result && !busy && <VerdictCard check={result} />}
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
    <div className="mt-1 flex gap-2">
      <input
        id="typed-voice"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && text.trim() && !disabled) onSubmit(text);
        }}
        placeholder="call में जो कहा गया…"
        className="w-full rounded-xl border border-neutral-300 bg-white p-3 text-base dark:border-neutral-700 dark:bg-neutral-950"
      />
      <button
        onClick={() => onSubmit(text)}
        disabled={disabled || !text.trim()}
        className="shrink-0 rounded-xl bg-blue-600 px-4 font-semibold text-white hover:bg-blue-700 disabled:opacity-40"
      >
        जाँचें
      </button>
    </div>
  );
}

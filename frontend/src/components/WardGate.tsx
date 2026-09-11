"use client";

// Ward-side panel after a risky check pinged the guardian (beat 5).
// Polls the request every 3s until decided. Blocked = GENTLE, warm, family tone —
// never scary red; the scam already scared them.

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { GuardianRequest } from "@/lib/types";

export default function WardGate({
  requestId,
  guardianName,
}: {
  requestId: string;
  guardianName: string;
}) {
  const [req, setReq] = useState<GuardianRequest | null>(null);

  useEffect(() => {
    let stop = false;
    async function tick() {
      try {
        const r = await api<GuardianRequest & { error?: string }>(
          `/api/guardian/requests/${requestId}`
        );
        if (!stop && !r.error) setReq(r);
        return r;
      } catch {
        return null;
      }
    }
    tick();
    // no document.hidden guard: projector/mirroring setups can misreport visibility,
    // and a silently-paused poll on stage costs more than tiny 3s GETs ever will
    const t = setInterval(async () => {
      const r = await tick();
      if (r && !("error" in r && r.error) && r.status !== "pending") clearInterval(t);
    }, 3000);
    const onWake = () => void tick(); // instant refresh when the phone screen wakes
    document.addEventListener("visibilitychange", onWake);
    return () => {
      stop = true;
      clearInterval(t);
      document.removeEventListener("visibilitychange", onWake);
    };
  }, [requestId]);

  const status = req?.status ?? "pending";

  if (status === "pending") {
    return (
      <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-950/40">
        <div className="flex items-center gap-3">
          <span className="animate-pulse text-3xl" aria-hidden>
            🛡️
          </span>
          <div>
            <p className="font-bold text-amber-900 dark:text-amber-200">
              {guardianName} को बताया गया है — जवाब का इंतज़ार…
            </p>
            <p className="mt-0.5 text-sm text-amber-800/80 dark:text-amber-300/80">
              बड़े खतरे पर परिवार की एक नज़र। कुछ भी भेजने से पहले रुके रहिए। · Your guardian
              has been notified, waiting for their reply.
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (status === "blocked") {
    return (
      <div className="rounded-2xl border-2 border-rose-200 bg-rose-50 p-5 text-center dark:border-rose-800 dark:bg-rose-950/40">
        <div className="text-4xl" aria-hidden>
          ❤️
        </div>
        <p className="mt-2 text-xl font-bold text-rose-900 dark:text-rose-100">
          {guardianName} ने कहा — यह पैसा मत भेजिए
        </p>
        {req?.guardian_note && (
          <p className="mt-2 rounded-xl bg-white/70 p-3 text-base text-rose-900 dark:bg-rose-900/40 dark:text-rose-100">
            “{req.guardian_note}”
          </p>
        )}
        <p className="mt-3 text-sm text-rose-800/80 dark:text-rose-200/80">
          कोई पैसा नहीं गया। आपके अपनों की नज़र आप पर है — यही आपकी ढाल है। · Nothing was
          sent. Your family has your back.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border-2 border-emerald-300 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950/40">
      <p className="font-bold text-emerald-900 dark:text-emerald-200">
        ✓ {guardianName} ने कहा — ठीक है
      </p>
      {req?.guardian_note && (
        <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-300">“{req.guardian_note}”</p>
      )}
      <p className="mt-1 text-sm text-emerald-800/80 dark:text-emerald-300/80">
        फिर भी रक़म और नाम एक बार खुद जाँच लीजिए। · Still double-check the amount and payee.
      </p>
    </div>
  );
}

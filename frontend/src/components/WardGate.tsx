"use client";

// Ward-side panel after a risky check pinged the guardian (beat 5).
// Polls the request every 3s until decided. Blocked = GENTLE, warm, family tone —
// saffron heart and ink, never alarm-red; the scam already scared them.

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { GuardianRequest } from "@/lib/types";
import { ICheck, IHeart, IShield } from "@/components/icons";

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
      <div className="border-2 border-ink bg-paper2 p-4">
        <div className="flex items-center gap-3">
          <IShield className="blink h-8 w-8 shrink-0 text-saffdeep" />
          <div>
            <p className="font-bold">{guardianName} को बताया गया है — जवाब का इंतज़ार…</p>
            <p className="mt-0.5 text-sm text-inksoft">
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
      <div className="border-[3px] border-ink bg-paper p-5 text-center shadow-poster-sm">
        <IHeart className="mx-auto h-9 w-9 text-saffdeep" />
        <p className="mt-2 font-display text-2xl font-bold leading-tight">
          {guardianName} ने कहा — यह पैसा मत भेजिए
        </p>
        {req?.guardian_note && (
          <p className="mt-3 border border-line bg-paper2 p-3 text-base">
            “{req.guardian_note}”
          </p>
        )}
        <p className="mt-3 text-sm text-inksoft">
          कोई पैसा नहीं गया। आपके अपनों की नज़र आप पर है — यही आपकी ढाल है। · Nothing was
          sent. Your family has your back.
        </p>
      </div>
    );
  }

  return (
    <div className="border-2 border-clear bg-paper p-4">
      <p className="flex items-center gap-2 font-bold text-cleardeep">
        <ICheck className="h-4 w-4" /> {guardianName} ने कहा — ठीक है
      </p>
      {req?.guardian_note && (
        <p className="mt-1 text-sm">“{req.guardian_note}”</p>
      )}
      <p className="mt-1 text-sm text-inksoft">
        फिर भी रक़म और नाम एक बार खुद जाँच लीजिए। · Still double-check the amount and payee.
      </p>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ScamCategory, Trends } from "@/lib/types";
import { CATEGORY_UI } from "@/lib/labels";
import { pick, useLang } from "@/lib/lang";
import LangToggle from "@/components/LangToggle";
import { DhaalMark } from "@/components/icons";

export default function TopBar({ title_hi, title_en }: { title_hi: string; title_en: string }) {
  const lang = useLang();
  const [primary, secondary] = pick(lang, { hi: title_hi, en: title_en });

  // live threat ticker — REAL top indicators from /api/intel/trends, rotating
  const [items, setItems] = useState<string[]>([]);
  const [i, setI] = useState(0);
  useEffect(() => {
    api<Trends>("/api/intel/trends")
      .then((t) =>
        setItems(
          t.top_indicators.slice(0, 5).map((ind) => {
            const cat = CATEGORY_UI[ind.category as ScamCategory];
            return `${ind.value} · ${ind.report_count} reports${cat ? ` · ${pick(lang, cat)[0]}` : ""}`;
          })
        )
      )
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);
  useEffect(() => {
    if (items.length < 2) return;
    const t = setInterval(() => setI((x) => (x + 1) % items.length), 4000);
    return () => clearInterval(t);
  }, [items.length]);

  return (
    <header className="sticky top-0 z-10 border-b-[3px] border-ink bg-paper">
      <div className="mx-auto flex max-w-xl items-center gap-3 px-4 py-2.5">
        <Link href="/" aria-label="Dhaal home" className="flex items-center gap-1.5 hover:opacity-80">
          <span aria-hidden="true" className="text-lg leading-none">←</span>
          <DhaalMark className="seal-live h-7 w-auto" />
          <span className="font-display text-2xl font-extrabold leading-none">ढाल</span>
        </Link>
        <div className="min-w-0 flex-1 border-l-2 border-ink pl-3">
          <div className="truncate font-bold leading-tight">{primary}</div>
          <div className="plate truncate text-inksoft">{secondary}</div>
        </div>
        <LangToggle />
      </div>
      {items.length > 0 && (
        <div className="overflow-hidden border-t-2 border-line bg-paper2">
          <p key={i} className="row-reveal plate mx-auto max-w-xl truncate px-4 py-1 text-inksoft">
            <span aria-hidden="true" className="mr-1 text-dangerdeep">⚠</span>
            {items[i]}
          </p>
        </div>
      )}
    </header>
  );
}

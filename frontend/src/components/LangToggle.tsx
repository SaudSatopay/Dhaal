"use client";

// The global हिं/EN pill — on every masthead. Saffron marks the active language;
// `ink` variant sits on the /intel war-room dark surface.

import { setLang, useLang, type Lang } from "@/lib/lang";

const OPTIONS: { id: Lang; label: string }[] = [
  { id: "hi", label: "हिं" },
  { id: "en", label: "EN" },
];

export default function LangToggle({ variant = "paper" }: { variant?: "paper" | "ink" }) {
  const lang = useLang();
  const border = variant === "paper" ? "border-ink" : "border-fog";
  const idle =
    variant === "paper" ? "text-ink hover:bg-paper2" : "text-fog hover:text-paper";
  return (
    <div
      role="group"
      aria-label="भाषा · language"
      className={`flex shrink-0 overflow-hidden rounded-full border-2 ${border}`}
    >
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          onClick={() => setLang(o.id)}
          aria-pressed={lang === o.id}
          className={`px-2.5 py-0.5 font-mono text-xs font-semibold leading-5 ${
            lang === o.id ? "bg-saffron text-ink" : idle
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

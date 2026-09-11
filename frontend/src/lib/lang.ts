"use client";

// Global language state — "dhaal-lang" in localStorage, default Hindi.
// useSyncExternalStore: server snapshot is "hi", the stored value applies in the
// hydration render pass (no mismatch warnings, no visible flash), and every
// subscribed component re-renders together when the pill is toggled.

import { useSyncExternalStore } from "react";

export type Lang = "hi" | "en";
export type LangText = { hi: string; en: string };

const KEY = "dhaal-lang";
const listeners = new Set<() => void>();
let cached: Lang | null = null;

function read(): Lang {
  try {
    return localStorage.getItem(KEY) === "en" ? "en" : "hi";
  } catch {
    return "hi";
  }
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  const onStorage = (e: StorageEvent) => {
    if (e.key === KEY) {
      cached = read();
      cb();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

function getSnapshot(): Lang {
  if (cached === null) cached = read();
  return cached;
}

export function setLang(l: Lang) {
  cached = l;
  try {
    localStorage.setItem(KEY, l);
  } catch {
    // storage unavailable — toggle still works for this page-load
  }
  listeners.forEach((f) => f());
}

export function useLang(): Lang {
  return useSyncExternalStore(subscribe, getSnapshot, () => "hi");
}

/** contract lang codes — drives Claude explanation + Sarvam TTS language */
export const apiLang = (l: Lang) => (l === "en" ? "en-IN" : "hi-IN");

/** [primary, secondary] in the selected language order */
export const pick = (l: Lang, t: LangText): [string, string] =>
  l === "en" ? [t.en, t.hi] : [t.hi, t.en];

/** tiny {name}-style template fill for strings that carry values */
export function fmt(s: string, vars: Record<string, string | number>): string {
  return s.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ""));
}

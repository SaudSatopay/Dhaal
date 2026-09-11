import Link from "next/link";

export default function TopBar({ title_hi, title_en }: { title_hi: string; title_en: string }) {
  return (
    <header className="sticky top-0 z-10 border-b border-neutral-200 bg-white/90 backdrop-blur dark:border-neutral-800 dark:bg-neutral-950/90">
      <div className="mx-auto flex max-w-xl items-center gap-3 px-4 py-3">
        <Link href="/" className="text-lg font-bold" aria-label="Dhaal home">
          ← ढाल
        </Link>
        <div className="min-w-0">
          <div className="truncate font-semibold leading-tight">{title_hi}</div>
          <div className="truncate text-xs text-neutral-500">{title_en}</div>
        </div>
      </div>
    </header>
  );
}

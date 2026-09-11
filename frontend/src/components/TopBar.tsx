import Link from "next/link";

export default function TopBar({ title_hi, title_en }: { title_hi: string; title_en: string }) {
  return (
    <header className="sticky top-0 z-10 border-b-[3px] border-ink bg-paper">
      <div className="mx-auto flex max-w-xl items-center gap-3 px-4 py-2.5">
        <Link href="/" aria-label="Dhaal home" className="flex items-baseline gap-1.5 hover:opacity-80">
          <span aria-hidden="true" className="text-lg leading-none">←</span>
          <span className="font-display text-2xl font-extrabold leading-none">ढाल</span>
        </Link>
        <div className="min-w-0 border-l-2 border-ink pl-3">
          <div className="truncate font-bold leading-tight">{title_hi}</div>
          <div className="plate truncate text-inksoft">{title_en}</div>
        </div>
      </div>
    </header>
  );
}

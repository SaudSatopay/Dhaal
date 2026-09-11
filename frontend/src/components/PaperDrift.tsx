// Notice-board ephemera — PRINTED watermarks drifting behind content.
// Purely decorative: aria-hidden, pointer-events-none, z-0 (content sits at
// z-10), hidden under prefers-reduced-motion (globals.css). Glyphs live in
// the gutters and the breathing room BETWEEN sections; cards with paper
// backgrounds pass over them like sheets pinned above the board.

const INK = "var(--color-ink)";
const SAFF = "var(--color-saffdeep)";

function MiniShield({ style, className }: { style: React.CSSProperties; className: string }) {
  return (
    <svg viewBox="0 0 56 62" className={className} style={style}>
      <path
        d="M28 4.5 48 11v15.5c0 12.6-8.2 21-20 26.5C16.2 47.5 8 39.1 8 26.5V11Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
      />
      <path d="M19 25.5l6.5 6.5L38.5 18.5" fill="none" stroke="currentColor" strokeWidth="4.5" strokeLinecap="square" />
    </svg>
  );
}

function Cross({ style, className }: { style: React.CSSProperties; className: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} style={style}>
      <path d="M12 3v18M3 12h18" stroke="currentColor" strokeWidth="2.4" />
    </svg>
  );
}

function QrBracket({ style, className }: { style: React.CSSProperties; className: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} style={style}>
      <path d="M4 12V4h8M20 4h8v8M28 20v8h-8M12 28H4v-8" fill="none" stroke="currentColor" strokeWidth="3" />
    </svg>
  );
}

// variant "hero": fuller field for the landing. variant "quiet": sparse — the
// working pages, never near the task.
export default function PaperDrift({ variant = "hero" }: { variant?: "hero" | "quiet" }) {
  const hero = variant === "hero";
  return (
    <div aria-hidden="true" className="drift-layer">
      {/* left gutter, top to bottom */}
      <MiniShield
        className="drift-a h-20 w-20"
        style={{ top: "3.5%", left: "-0.4rem", color: INK, opacity: 0.13 }}
      />
      <span
        className="drift-b font-mono font-semibold"
        style={{ top: "27%", left: "0.15rem", fontSize: "3rem", color: SAFF, opacity: 0.17, lineHeight: 1 }}
      >
        ₹
      </span>
      <Cross
        className="drift-c h-7 w-7"
        style={{ top: "48%", left: "0.5rem", color: INK, opacity: 0.16 }}
      />
      <span
        className="drift-a plate"
        style={{ top: "66%", left: "-1.4rem", fontSize: "0.68rem", color: INK, opacity: 0.15, rotate: "-90deg" }}
      >
        जाँच · CHECK
      </span>
      {hero && (
        <MiniShield
          className="drift-c h-12 w-12"
          style={{ top: "88%", left: "0", color: SAFF, opacity: 0.14 }}
        />
      )}

      {/* right gutter */}
      <QrBracket
        className="drift-b h-14 w-14"
        style={{ top: "8%", right: "-0.2rem", color: INK, opacity: 0.14 }}
      />
      <span
        className="drift-c font-display font-extrabold"
        style={{ top: "34%", right: "0.1rem", fontSize: "2.6rem", color: INK, opacity: 0.11, lineHeight: 1 }}
      >
        ✓
      </span>
      <span
        className="drift-a font-mono font-semibold"
        style={{ top: "57%", right: "0.4rem", fontSize: "2.2rem", color: SAFF, opacity: 0.16, lineHeight: 1 }}
      >
        ₹
      </span>
      {hero && (
        <>
          <Cross
            className="drift-b h-6 w-6"
            style={{ top: "18.5%", right: "3rem", color: INK, opacity: 0.15 }}
          />
          <MiniShield
            className="drift-b h-14 w-14"
            style={{ top: "78%", right: "-0.5rem", color: SAFF, opacity: 0.15 }}
          />
          <span
            className="drift-c plate"
            style={{ top: "95%", right: "0.2rem", fontSize: "0.68rem", color: INK, opacity: 0.16 }}
          >
            सुरक्षा
          </span>
        </>
      )}
    </div>
  );
}

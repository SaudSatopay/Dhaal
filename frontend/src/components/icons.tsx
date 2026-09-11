// Signage-style inline SVG marks — square terminals, 2.2 stroke, currentColor.
// The anti-slop rule: no emoji as icons, anywhere.

type P = { className?: string };

const S = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2.2,
  strokeLinecap: "square" as const,
  strokeLinejoin: "miter" as const,
};

function Svg({ className, children }: P & { children: React.ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" focusable="false">
      {children}
    </svg>
  );
}

export function IShield({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M12 2.8 4.8 5.6v5.5c0 4.6 3 7.7 7.2 9.7 4.2-2 7.2-5.1 7.2-9.7V5.6Z" />
    </Svg>
  );
}

export function IShieldCheck({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M12 2.8 4.8 5.6v5.5c0 4.6 3 7.7 7.2 9.7 4.2-2 7.2-5.1 7.2-9.7V5.6Z" />
      <path {...S} d="m8.6 11.8 2.4 2.4 4.4-4.6" />
    </Svg>
  );
}

export function IPaste({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M8 4.5H6v17h12v-17h-2" />
      <path {...S} d="M9 2.8h6v3.4H9zM9 10h6M9 13.5h6M9 17h4" />
    </Svg>
  );
}

export function IQr({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M3.5 3.5h6v6h-6zM14.5 3.5h6v6h-6zM3.5 14.5h6v6h-6z" />
      <path {...S} d="M14.5 14.5h2.5v2.5h-2.5zM18 18h2.5v2.5H18zM18 14.5h2.5M14.5 18v2.5" />
    </Svg>
  );
}

export function IMic({ className }: P) {
  return (
    <Svg className={className}>
      <rect {...S} x="9" y="2.8" width="6" height="11" />
      <path {...S} d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3.2M8.5 21.2h7" />
    </Svg>
  );
}

export function IStop({ className }: P) {
  return (
    <Svg className={className}>
      <rect {...S} x="6" y="6" width="12" height="12" />
    </Svg>
  );
}

export function ISpeaker({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M4 9.5h3.5L13 5v14l-5.5-4.5H4zM16.5 9a4.5 4.5 0 0 1 0 6M19 6.5a8 8 0 0 1 0 11" />
    </Svg>
  );
}

export function IFlag({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M5.5 21.5v-18M5.5 4h13l-2.6 4 2.6 4h-13" />
    </Svg>
  );
}

export function IPhone({ className }: P) {
  return (
    <Svg className={className}>
      <path
        {...S}
        d="M4.5 4.5h4l1.8 4.4-2.2 2.2a13 13 0 0 0 4.8 4.8l2.2-2.2 4.4 1.8v4a1.8 1.8 0 0 1-1.9 1.8C9.7 20.7 3.3 14.3 2.7 6.4A1.8 1.8 0 0 1 4.5 4.5Z"
      />
    </Svg>
  );
}

export function IGlobe({ className }: P) {
  return (
    <Svg className={className}>
      <circle {...S} cx="12" cy="12" r="8.8" />
      <path {...S} d="M3.2 12h17.6M12 3.2c-4.8 4.8-4.8 12.8 0 17.6 4.8-4.8 4.8-12.8 0-17.6Z" />
    </Svg>
  );
}

export function IScript({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M4 4.5h16v11H9l-5 4.5zM8 8.5h8M8 11.5h5" />
    </Svg>
  );
}

export function IUsers({ className }: P) {
  return (
    <Svg className={className}>
      <circle {...S} cx="9" cy="8" r="3.2" />
      <path {...S} d="M3.5 20a5.5 5.5 0 0 1 11 0M15.5 5.2a3.2 3.2 0 0 1 0 5.9M17 14.6a5.5 5.5 0 0 1 3.5 5.4" />
    </Svg>
  );
}

export function IHeart({ className }: P) {
  return (
    <Svg className={className}>
      <path
        {...S}
        d="M12 20.5 4.8 13a4.6 4.6 0 0 1 6.5-6.5l.7.7.7-.7A4.6 4.6 0 0 1 19.2 13Z"
      />
    </Svg>
  );
}

export function ICheck({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="m4.5 12.5 5 5 10-11" />
    </Svg>
  );
}

export function ICross({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="m5.5 5.5 13 13M18.5 5.5l-13 13" />
    </Svg>
  );
}

export function IArrowR({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M3.5 12h16M14 5.5l6.5 6.5L14 18.5" />
    </Svg>
  );
}

export function ISiren({ className }: P) {
  return (
    <Svg className={className}>
      <path {...S} d="M7 19v-5a5 5 0 0 1 10 0v5M4 19h16v2.2H4zM12 3v2.4M4.8 6.2l1.7 1.7M19.2 6.2l-1.7 1.7" />
    </Svg>
  );
}

// Indicator-type marks for intel surfaces (upi uses the typographic ₹)
export function TypeMark({ type, className }: { type: string; className?: string }) {
  if (type === "phone") return <IPhone className={className} />;
  if (type === "domain") return <IGlobe className={className} />;
  if (type === "script") return <IScript className={className} />;
  if (type === "upi")
    return (
      <span className={`inline-flex items-center justify-center font-mono font-semibold ${className ?? ""}`} aria-hidden="true">
        ₹
      </span>
    );
  return <IScript className={className} />;
}

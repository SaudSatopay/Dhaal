import type { Metadata } from "next";
import { Anek_Devanagari, IBM_Plex_Mono, Mukta } from "next/font/google";
import "./globals.css";

// Type IS the design: Anek Devanagari for display lockups, Mukta for body,
// IBM Plex Mono for numbers/indicators. Hindi first, English subtitles.
const anek = Anek_Devanagari({
  variable: "--font-anek",
  subsets: ["devanagari", "latin"],
  weight: ["500", "600", "700", "800"],
});

const mukta = Mukta({
  variable: "--font-mukta",
  subsets: ["devanagari", "latin"],
  weight: ["400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Dhaal (ढाल)",
  description:
    "पैसे भेजने से पहले — एक जाँच। Check any message, QR, link or call before you pay.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${anek.variable} ${mukta.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

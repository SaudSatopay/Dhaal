import type { Metadata } from "next";
import { Geist, Geist_Mono, Noto_Sans_Devanagari } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Hindi-first product — Devanagari deserves a real face, not the system fallback.
// Latin glyphs come from Geist; Devanagari falls through to Noto.
const notoDevanagari = Noto_Sans_Devanagari({
  variable: "--font-noto-dev",
  subsets: ["devanagari"],
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
      className={`${geistSans.variable} ${geistMono.variable} ${notoDevanagari.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

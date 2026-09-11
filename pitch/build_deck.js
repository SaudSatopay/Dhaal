// Dhaal — HackX judging deck generator. Rebuild: node build_deck.js  → Dhaal-HackX-pitch.pptx
// Numbers verified 11 Sep 2026: NPCI Aug-2026 UPI volume; I4C 2025 fraud + 1930 stats.
const pptxgen = require("pptxgenjs");
const path = require("path");
const QR = require(path.join(__dirname, "..", "frontend", "node_modules", "qrcode"));

const NAVY = "1B2A4A";
const PANEL = "223458"; // card on dark
const LIGHT = "F6F8FC";
const WHITE = "FFFFFF";
const INK = "1B2A4A";
const MUTED = "5A6B8C";
const ICE = "C9D7F2";
const RED = "DC2626";
const RED_DARK = "B91C1C";
const RED_TINT = "FDECEC";
const EMERALD = "059669";
const EMERALD_TINT = "E7F6F0";
const BLUE = "2563EB";
const BLUE_TINT = "EAF1FE";
const AMBER_TINT = "FDF3E3";
const BORDER = "D9E2F1";

const F = "Arial";
const W = 13.33;

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = "Team Dhaal";
  pres.title = "Dhaal (ढाल) — before you pay, one check";

  const qrDataUrl = await QR.toDataURL("https://dhaal-delta.vercel.app", {
    width: 480,
    margin: 1,
    color: { dark: "1B2A4A", light: "FFFFFF" },
  });

  // ---------------------------------------------------------------- helpers
  function title(slide, text, opts = {}) {
    slide.addText(text, {
      x: 0.6, y: 0.42, w: W - 1.2, h: 0.75,
      fontFace: F, fontSize: 33, bold: true, color: INK, align: "left",
      isTextBox: true, margin: 0, ...opts,
    });
  }
  function card(slide, x, y, w, h, fill, line) {
    slide.addShape("ROUNDED_RECTANGLE", {
      x, y, w, h, fill: { color: fill }, rectRadius: 0.09,
      line: line ? { color: line, width: 1 } : { color: fill, width: 0 },
    });
  }
  function iconCircle(slide, x, y, d, bg, glyph, glyphSize) {
    slide.addShape("OVAL", { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg, width: 0 } });
    slide.addText(glyph, {
      x: x - 0.1, y: y - 0.06, w: d + 0.2, h: d + 0.12, fontFace: F,
      fontSize: glyphSize, align: "center", valign: "middle", isTextBox: true, margin: 0, color: INK,
    });
  }

  // ================================================================ S1 · title
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    s.addText("🛡️", { x: 0, y: 0.72, w: W, h: 1.3, fontFace: F, fontSize: 76, align: "center", isTextBox: true, margin: 0, color: WHITE });
    s.addText("ढाल", { x: 0, y: 2.02, w: W, h: 1.55, fontFace: F, fontSize: 84, bold: true, color: WHITE, align: "center", isTextBox: true, margin: 0 });
    s.addText("D H A A L", { x: 0, y: 3.62, w: W, h: 0.4, fontFace: F, fontSize: 15, color: ICE, align: "center", charSpacing: 6, isTextBox: true, margin: 0 });
    s.addText("पैसे भेजने से पहले — एक जाँच", { x: 0, y: 4.18, w: W, h: 0.72, fontFace: F, fontSize: 27, bold: true, color: WHITE, align: "center", isTextBox: true, margin: 0 });
    s.addText("Before you pay, one check.", { x: 0, y: 4.92, w: W, h: 0.45, fontFace: F, fontSize: 16, color: ICE, align: "center", isTextBox: true, margin: 0 });
    s.addText("Saud Satopay  ·  Parva Panchal  ·  Harsh Mishra", { x: 0, y: 6.02, w: W, h: 0.4, fontFace: F, fontSize: 13, color: ICE, align: "center", isTextBox: true, margin: 0 });
    s.addText("MUJ HackX 4.0 · Fintech PS #7 — Consumer Protection Against Payment Scams", {
      x: 0.6, y: 6.92, w: 8.6, h: 0.4, fontFace: F, fontSize: 11, color: ICE, align: "left", isTextBox: true, margin: 0,
    });
    s.addText("dhaal-delta.vercel.app", { x: 9.4, y: 6.92, w: 3.33, h: 0.4, fontFace: F, fontSize: 12, bold: true, color: WHITE, align: "right", isTextBox: true, margin: 0 });
    s.addNotes("Namaste judges. Everyone in this hall deleted a scam SMS this morning. We built the thing that should have existed before you had to. This is Dhaal — before you pay, one check. [10 sec, move fast]");
  }

  // ================================================================ S2 · problem
  {
    const s = pres.addSlide();
    s.background = { color: LIGHT };
    title(s, "The scam arrives faster than any fraud team");
    const stats = [
      { big: "24.51 B", label: "UPI transactions every month", src: "NPCI · Aug 2026" },
      { big: "₹22,495 Cr", label: "lost to cyber fraud in 2025", src: "I4C · 28.1 lakh cases" },
      { big: "32.4 M", label: "calls to the 1930 helpline in 2025", src: "≈ one victim every second" },
    ];
    stats.forEach((st, i) => {
      const x = 0.6 + i * 4.11;
      card(s, x, 1.45, 3.91, 2.0, WHITE, BORDER);
      s.addText(st.big, { x: x + 0.25, y: 1.62, w: 3.41, h: 0.85, fontFace: F, fontSize: 38, bold: true, color: BLUE, isTextBox: true, margin: 0 });
      s.addText(st.label, { x: x + 0.25, y: 2.5, w: 3.41, h: 0.55, fontFace: F, fontSize: 13.5, color: INK, isTextBox: true, margin: 0 });
      s.addText(st.src, { x: x + 0.25, y: 3.06, w: 3.41, h: 0.32, fontFace: F, fontSize: 10, color: MUTED, isTextBox: true, margin: 0 });
    });
    card(s, 0.6, 3.85, 12.13, 1.75, RED_TINT, "F5C6C6");
    s.addText("The victim presses PAY themselves — so bank-side fraud controls never fire.", {
      x: 1.0, y: 4.05, w: 11.4, h: 0.6, fontFace: F, fontSize: 20, bold: true, color: RED_DARK, isTextBox: true, margin: 0,
    });
    s.addText("Fake collect requests · malicious QRs · KYC-expiry SMS · digital-arrest calls — pressure moves the money before doubt arrives.", {
      x: 1.0, y: 4.72, w: 11.4, h: 0.6, fontFace: F, fontSize: 14, color: INK, isTextBox: true, margin: 0,
    });
    s.addText("Banks structurally cannot stop an authorised payment. The shield has to live in the user's hand — before the PAY button.", {
      x: 0.6, y: 5.95, w: 12.13, h: 0.5, fontFace: F, fontSize: 14.5, italic: true, color: MUTED, isTextBox: true, margin: 0,
    });
    s.addNotes("India runs on UPI — 24.5 billion transactions a month. And ₹22,495 crore walked out of Indian pockets last year, mostly NOT through hacking: the victim authorises the payment themselves. That's why bank fraud controls never fire — there is no unauthorised transaction to catch. The protection has to move to the user's hand. [45 sec]");
  }

  // ================================================================ S3 · solution
  {
    const s = pres.addSlide();
    s.background = { color: LIGHT };
    title(s, "Dhaal: one check before money moves");

    // left — verdict mini-card
    card(s, 0.6, 1.42, 5.7, 5.35, WHITE, BORDER);
    s.addShape("ROUNDED_RECTANGLE", { x: 0.85, y: 1.67, w: 5.2, h: 1.05, fill: { color: RED }, rectRadius: 0.07, line: { color: RED, width: 0 } });
    s.addText("🛑 खतरा · DANGER", { x: 1.05, y: 1.74, w: 4.8, h: 0.55, fontFace: F, fontSize: 21, bold: true, color: WHITE, isTextBox: true, margin: 0 });
    s.addText("रुक जाइए — पैसे मत भेजिए · risk 100/100", { x: 1.05, y: 2.3, w: 4.8, h: 0.36, fontFace: F, fontSize: 12, color: WHITE, isTextBox: true, margin: 0 });
    const sig = [
      { t: "Reported by 43 users — community blocklist", w2: "+65" },
      { t: "Lookalike domain — sbi-kyc-update.xyz imitates sbi.co.in", w2: "+40" },
      { t: "Known scam script — “KYC expiry” pattern", w2: "+25" },
    ];
    sig.forEach((g, i) => {
      const y = 2.98 + i * 0.92;
      card(s, 0.85, y, 5.2, 0.78, LIGHT, BORDER);
      s.addText(g.t, { x: 1.05, y: y + 0.09, w: 4.05, h: 0.6, fontFace: F, fontSize: 11.5, color: INK, isTextBox: true, margin: 0, valign: "middle" });
      s.addText(g.w2, { x: 5.1, y: y + 0.09, w: 0.8, h: 0.6, fontFace: F, fontSize: 15, bold: true, color: RED, align: "right", isTextBox: true, margin: 0, valign: "middle" });
    });
    s.addText("“यह message असली बैंक से नहीं है — इस link पर कुछ भी न भरें।”  + spoken aloud in Hindi", {
      x: 0.85, y: 5.85, w: 5.2, h: 0.75, fontFace: F, fontSize: 12, italic: true, color: MUTED, isTextBox: true, margin: 0,
    });

    // right — inputs
    const inputs = [
      { g: "📋", bg: BLUE_TINT, t: "Paste anything", d: "SMS, WhatsApp forward, link, UPI ID, phone number" },
      { g: "📷", bg: AMBER_TINT, t: "QR photo", d: "decoded on the phone itself — the image never leaves the device" },
      { g: "🎤", bg: EMERALD_TINT, t: "Speak the call", d: "Hindi in, Hindi out — Dhaal speaks the warning back" },
    ];
    inputs.forEach((inp, i) => {
      const y = 1.42 + i * 1.18;
      iconCircle(s, 6.75, y + 0.14, 0.72, inp.bg, inp.g, 26);
      s.addText(inp.t, { x: 7.7, y: y + 0.02, w: 5.0, h: 0.42, fontFace: F, fontSize: 17, bold: true, color: INK, isTextBox: true, margin: 0 });
      s.addText(inp.d, { x: 7.7, y: y + 0.46, w: 5.0, h: 0.55, fontFace: F, fontSize: 12.5, color: MUTED, isTextBox: true, margin: 0 });
    });
    card(s, 6.75, 5.12, 5.98, 1.65, WHITE, BORDER);
    s.addText("Verdict with the exact reasons — हिंदी + English, signal by signal.", {
      x: 7.0, y: 5.3, w: 5.5, h: 0.6, fontFace: F, fontSize: 14.5, bold: true, color: INK, isTextBox: true, margin: 0,
    });
    s.addText("Never the word “safe” — the honest green state is कोई ज्ञात खतरा नहीं (no KNOWN risk).", {
      x: 7.0, y: 5.95, w: 5.5, h: 0.6, fontFace: F, fontSize: 12, color: MUTED, isTextBox: true, margin: 0,
    });
    s.addNotes("One box, three doors: paste anything, upload a QR photo — decoded on-device — or just speak the call in Hindi. And Dhaal answers the only question that matters: WHY. Not a black-box score — the exact reasons, in the user's own language, spoken back if they can't read fast under pressure. [40 sec → hand to demo driver]");
  }

  // ================================================================ S4 · demo map
  {
    const s = pres.addSlide();
    s.background = { color: LIGHT };
    title(s, "Live demo — the golden path");
    const beats = [
      { g: "📩", t: "The SMS everyone got", d: "paste the KYC-expiry scam → खतरा, lookalike domain exposed" },
      { g: "📷", t: "The QR trap", d: "₹15,000 COLLECT request — “approve करते ही पैसे कटेंगे”" },
      { g: "✅", t: "We don't cry wolf", d: "genuine bank SMS → कोई ज्ञात खतरा नहीं" },
      { g: "🎤", t: "Voice, both directions", d: "digital-arrest script spoken in Hindi → danger, warning spoken back" },
      { g: "👨‍👩‍👧", t: "Guardian mode", d: "grandma's risky check → son taps Block → gentle Hindi message" },
      { g: "🔁", t: "The flywheel", d: "report → verify in /intel → same number instantly DANGER for everyone" },
    ];
    beats.forEach((b, i) => {
      const x = 0.6 + (i % 3) * 4.11;
      const y = 1.42 + Math.floor(i / 3) * 2.28;
      card(s, x, y, 3.91, 2.08, WHITE, BORDER);
      s.addText(`${i + 1}`, { x: x + 0.22, y: y + 0.2, w: 0.5, h: 0.5, fontFace: F, fontSize: 22, bold: true, color: BLUE, isTextBox: true, margin: 0 });
      s.addText(b.g, { x: x + 0.68, y: y + 0.2, w: 0.6, h: 0.5, fontFace: F, fontSize: 20, isTextBox: true, margin: 0, color: INK });
      s.addText(b.t, { x: x + 0.22, y: y + 0.72, w: 3.5, h: 0.42, fontFace: F, fontSize: 15, bold: true, color: INK, isTextBox: true, margin: 0 });
      s.addText(b.d, { x: x + 0.22, y: y + 1.14, w: 3.5, h: 0.85, fontFace: F, fontSize: 11.5, color: MUTED, isTextBox: true, margin: 0 });
    });
    card(s, 0.6, 6.0, 12.13, 0.85, NAVY, NAVY);
    s.addText("Closer — the judge's own pocket: “Sir, open your inbox. Forward us any message you suspect.” (fixture fallback rehearsed)", {
      x: 1.0, y: 6.13, w: 11.4, h: 0.6, fontFace: F, fontSize: 14, bold: true, color: WHITE, isTextBox: true, margin: 0, valign: "middle",
    });
    s.addNotes("DEMO DRIVER: follow demo/RUNSHEET.md exactly — never improvise inputs. This slide stays up only if the live app cannot (backup video second, narration never stops). Total demo time budget: 3 minutes.");
  }

  // ================================================================ S5 · architecture
  {
    const s = pres.addSlide();
    s.background = { color: LIGHT };
    title(s, "Deterministic core · AI narration · community memory");

    const flow = [
      { t: "📱 Next.js", d: "Vercel · QR decoded client-side", w: 2.5 },
      { t: "⚙️ FastAPI", d: "serverless API", w: 2.2 },
      { t: "SIGNAL ENGINE — code, not AI", d: "UPI collect-vs-pay · lookalike domains · URL heuristics · scam-script patterns · community blocklist", w: 4.7, hero: true },
      { t: "🧮 Verdict", d: "scored sum → खतरा / सावधान / no known risk", w: 2.3 },
    ];
    let x = 0.6;
    flow.forEach((f, i) => {
      const h = 1.75, y = 1.5;
      card(s, x, y, f.w, h, f.hero ? NAVY : WHITE, f.hero ? NAVY : BORDER);
      s.addText(f.t, { x: x + 0.18, y: y + 0.14, w: f.w - 0.36, h: f.hero ? 0.62 : 0.5, fontFace: F, fontSize: f.hero ? 14.5 : 14, bold: true, color: f.hero ? WHITE : INK, isTextBox: true, margin: 0 });
      s.addText(f.d, { x: x + 0.18, y: y + (f.hero ? 0.74 : 0.66), w: f.w - 0.36, h: 0.95, fontFace: F, fontSize: f.hero ? 10.5 : 10.5, color: f.hero ? ICE : MUTED, isTextBox: true, margin: 0 });
      x += f.w;
      if (i < flow.length - 1) {
        s.addText("→", { x: x - 0.09, y: 2.12, w: 0.5, h: 0.5, fontFace: F, fontSize: 20, bold: true, color: MUTED, align: "center", isTextBox: true, margin: 0 });
        x += 0.31;
      }
    });

    const side = [
      { g: "🤖", t: "Claude", d: "writes the plain-Hindi explanation FROM detected signals only — zero verdict weight", tint: BLUE_TINT },
      { g: "🗣️", t: "Sarvam AI", d: "Indic ASR (voice in) + TTS (warning spoken back)", tint: EMERALD_TINT },
      { g: "🗄️", t: "MongoDB Atlas", d: "reports · blocklist indicators · guardian links (in-memory fallback)", tint: AMBER_TINT },
    ];
    side.forEach((c, i) => {
      const cx = 0.6 + i * 4.11;
      card(s, cx, 3.6, 3.91, 1.5, WHITE, BORDER);
      iconCircle(s, cx + 0.2, 3.78, 0.6, c.tint, c.g, 20);
      s.addText(c.t, { x: cx + 0.95, y: 3.75, w: 2.8, h: 0.4, fontFace: F, fontSize: 14, bold: true, color: INK, isTextBox: true, margin: 0 });
      s.addText(c.d, { x: cx + 0.95, y: 4.14, w: 2.8, h: 0.85, fontFace: F, fontSize: 10.5, color: MUTED, isTextBox: true, margin: 0 });
    });

    card(s, 0.6, 5.5, 12.13, 1.3, EMERALD_TINT, "BFE5D6");
    s.addText("The LLM can narrate the verdict — it can never change it. No hallucinated DANGER, no silently missed one.", {
      x: 1.0, y: 5.66, w: 11.4, h: 0.5, fontFace: F, fontSize: 16, bold: true, color: "046A50", isTextBox: true, margin: 0,
    });
    s.addText("Every external call (Claude · Sarvam · Atlas) degrades to a deterministic fallback — the demo survives dead venue Wi-Fi.", {
      x: 1.0, y: 6.2, w: 11.4, h: 0.45, fontFace: F, fontSize: 12.5, color: INK, isTextBox: true, margin: 0,
    });
    s.addNotes("The verdict is computed by deterministic scoring over detected signals — parsers, edit-distance, heuristics, a community blocklist. The LLM writes the explanation FROM those signals and carries zero verdict weight: it cannot hallucinate a danger or miss one it detected. Say exactly this sentence. [30 sec]");
  }

  // ================================================================ S6 · flywheel + honesty
  {
    const s = pres.addSlide();
    s.background = { color: LIGHT };
    title(s, "Every report makes every Indian's shield stronger");

    const steps = [
      { g: "🚩", t: "One victim reports", d: "one tap on the verdict card" },
      { g: "✅", t: "Moderator verifies", d: "/intel console — seconds" },
      { g: "⚡", t: "Indicator goes live", d: "phone · UPI ID · domain · script" },
      { g: "🛡️", t: "Everyone is covered", d: "next check anywhere hits it instantly" },
    ];
    steps.forEach((st, i) => {
      const y = 1.45 + i * 1.32;
      iconCircle(s, 0.75, y, 0.78, BLUE_TINT, st.g, 26);
      s.addText(st.t, { x: 1.78, y: y + 0.02, w: 4.4, h: 0.42, fontFace: F, fontSize: 16.5, bold: true, color: INK, isTextBox: true, margin: 0 });
      s.addText(st.d, { x: 1.78, y: y + 0.46, w: 4.4, h: 0.4, fontFace: F, fontSize: 12, color: MUTED, isTextBox: true, margin: 0 });
      if (i < steps.length - 1)
        s.addText("↓", { x: 0.88, y: y + 0.82, w: 0.5, h: 0.45, fontFace: F, fontSize: 18, bold: true, color: BLUE, isTextBox: true, margin: 0 });
    });
    s.addText("Live in tonight's demo: 43 reports → your report → 44 — the same scammer instantly flagged on a second phone.", {
      x: 0.75, y: 6.62, w: 5.9, h: 0.7, fontFace: F, fontSize: 12, italic: true, color: MUTED, isTextBox: true, margin: 0,
    });

    card(s, 7.0, 1.45, 5.73, 2.35, WHITE, BORDER);
    s.addText("The first hour decides recovery", { x: 7.25, y: 1.62, w: 5.2, h: 0.45, fontFace: F, fontSize: 16.5, bold: true, color: INK, isTextBox: true, margin: 0 });
    s.addText("₹7,130 Cr already saved where victims reported fast (I4C reporting system). Dhaal's recovery kit scripts that hour: the 1930 call, the cybercrime.gov.in complaint, the bank letter — copy-ready, in Hindi.", {
      x: 7.25, y: 2.1, w: 5.2, h: 1.55, fontFace: F, fontSize: 12.5, color: INK, isTextBox: true, margin: 0,
    });

    card(s, 7.0, 4.05, 5.73, 2.6, EMERALD_TINT, "BFE5D6");
    s.addText("What is real tonight", { x: 7.25, y: 4.22, w: 5.2, h: 0.45, fontFace: F, fontSize: 16.5, bold: true, color: "046A50", isTextBox: true, margin: 0 });
    s.addText(
      [
        { text: "Live: signal engine · community flywheel · guardian mode · recovery kit · deployed at dhaal-delta.vercel.app", options: { bullet: true, breakLine: true } },
        { text: "Degrades honestly: AI narration & voice fall back to templates offline — responses carry mocked: true", options: { bullet: true, breakLine: true } },
        { text: "We never present a mocked path as live.", options: { bullet: true, bold: true } },
      ],
      { x: 7.35, y: 4.72, w: 5.15, h: 1.8, fontFace: F, fontSize: 12, color: INK, isTextBox: true, margin: 0, paraSpaceAfter: 8 }
    );
    s.addNotes("Community intel is herd immunity: one grandmother's report in Jaipur protects a student in Jodhpur the same minute — you watched it happen live. And when someone is already a victim, the first hour decides everything: ₹7,130 crore has been saved where people reported fast. Dhaal scripts that hour. Everything on the left half you just saw live; what's mocked says so on the wire. [40 sec]");
  }

  // ================================================================ S7 · close
  {
    const s = pres.addSlide();
    s.background = { color: NAVY };
    title(s, "ढाल हर जेब में — a shield in every pocket", { color: WHITE });
    const road = [
      { g: "🚨", t: "1930 / I4C hand-off", d: "one-tap complaint with evidence attached" },
      { g: "🧩", t: "SDK inside UPI apps", d: "the check runs before the PAY sheet" },
      { g: "🏦", t: "Bank & fintech API", d: "licensing the blocklist + risk engine" },
    ];
    road.forEach((r, i) => {
      const x = 0.6 + i * 4.11;
      card(s, x, 1.55, 3.91, 1.95, PANEL, PANEL);
      s.addText(r.g, { x: x + 0.25, y: 1.75, w: 0.7, h: 0.55, fontFace: F, fontSize: 24, isTextBox: true, margin: 0, color: WHITE });
      s.addText(r.t, { x: x + 0.25, y: 2.32, w: 3.4, h: 0.45, fontFace: F, fontSize: 16, bold: true, color: WHITE, isTextBox: true, margin: 0 });
      s.addText(r.d, { x: x + 0.25, y: 2.78, w: 3.4, h: 0.6, fontFace: F, fontSize: 11.5, color: ICE, isTextBox: true, margin: 0 });
    });
    s.addText("Free for every Indian. B2B API for the banks and fintechs who reimburse this fraud anyway.", {
      x: 0.6, y: 3.85, w: 12.13, h: 0.5, fontFace: F, fontSize: 15, color: ICE, align: "center", isTextBox: true, margin: 0,
    });
    s.addText("हर report, हर भारतीय की ढाल।", {
      x: 0.6, y: 4.75, w: 12.13, h: 0.8, fontFace: F, fontSize: 30, bold: true, color: WHITE, align: "center", isTextBox: true, margin: 0,
    });
    s.addImage({ data: qrDataUrl, x: 5.92, y: 5.75, w: 1.5, h: 1.5 });
    s.addText("dhaal-delta.vercel.app — scan and check your own inbox", {
      x: 0.6, y: 7.02, w: 12.13, h: 0.35, fontFace: F, fontSize: 11, color: ICE, align: "center", isTextBox: true, margin: 0,
    });
    s.addNotes("Roadmap: hand complaints straight into 1930/I4C, put the check inside UPI apps as an SDK, license the intel to banks — they reimburse this fraud today, they'd rather prevent it. Free for citizens, forever. Every report, every Indian's shield. Scan the QR — check your own inbox right now. Dhanyavaad. [25 sec]");
  }

  await pres.writeFile({ fileName: path.join(__dirname, "Dhaal-HackX-pitch.pptx") });
  console.log("WROTE Dhaal-HackX-pitch.pptx");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

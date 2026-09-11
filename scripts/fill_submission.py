"""Fill the organizers' PPT template with Dhaal content -> pitch/Dhaal-HackX-submission.pptx

Re-run after editing TEAM_NAME / TEAM_ID below:
    python scripts/fill_submission.py
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

TEAM_NAME = "[Your Team Name]"   # <-- FILL from registration
TEAM_ID = "[Registration ID]"    # <-- FILL from registration

INK = RGBColor(0x0E, 0x28, 0x41)
ACC = RGBColor(0x15, 0x60, 0x82)
RED = RGBColor(0xC6, 0x28, 0x28)

p = Presentation("pitch/template/PPT Template - MUJ HACKX 4.0.pptx")
slides = list(p.slides)

# ---- Slide 1: cover fields
sub = [sh for sh in slides[0].shapes if sh.has_text_frame and "Team Name" in sh.text_frame.text][0]
tf = sub.text_frame
lines = [
    ("Dhaal (ढाल) — the pre-payment scam shield for every Indian", True),
    (f"Team Name: {TEAM_NAME}", False),
    (f"Team ID: {TEAM_ID}", False),
    ("Problem Statement Selected: Consumer Protection Against Payment Scams (Fintech PS #7)", False),
    ("Theme: Fintech", False),
]
while len(tf.paragraphs) < len(lines):
    tf.add_paragraph()
for para, (txt, bold) in zip(tf.paragraphs, lines):
    for r in list(para.runs)[1:]:
        r._r.getparent().remove(r._r)
    run = para.runs[0] if para.runs else para.add_run()
    run.text = txt
    run.font.bold = bold
    if bold:
        run.font.color.rgb = ACC


def fill(slide, blocks):
    box = slide.shapes.add_textbox(Inches(0.9), Inches(2.05), Inches(11.5), Inches(5.1))
    tf = box.text_frame
    tf.word_wrap = True
    first = True
    for kind, text in blocks:
        para = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        run = para.add_run()
        run.text = text
        f = run.font
        f.name = "Calibri"
        if kind == "h":
            f.size = Pt(17); f.bold = True; f.color.rgb = ACC
            para.space_before = Pt(10); para.space_after = Pt(2)
        elif kind == "big":
            f.size = Pt(20); f.bold = True; f.color.rgb = INK
            para.space_after = Pt(6)
        elif kind == "red":
            f.size = Pt(16); f.bold = True; f.color.rgb = RED
            para.space_before = Pt(8)
        else:
            f.size = Pt(14.5); f.color.rgb = INK
            para.space_after = Pt(3)


fill(slides[1], [  # IDEA / SOLUTION TITLE
    ("big", "ढाल Dhaal — पैसे भेजने से पहले, एक जाँच। One check before you pay."),
    ("t", "Paste any message, link, UPI ID or number — photograph a QR — or just SPEAK the call in Hindi. Dhaal returns a verdict with every reason, in the user's language, and speaks the warning back."),
    ("h", "Four surfaces, one shield"),
    ("t", "जाँच Check — verdict + weighted signals, spoken aloud (Hindi/English toggle) · परिवार की ढाल Guardian — an elderly user's risky payment pings family for a 10-second Allow/Block · धोखों का नक्शा Intel — community reports become everyone's live blocklist · पहला घंटा Recover — 1930 script + cybercrime.gov.in complaint + bank letter, auto-drafted in Hindi."),
    ("h", "Why it's different"),
    ("t", "The verdict is computed by a deterministic rule engine — the AI only explains it and can never change it. Dhaal never says \"safe\", only \"no known risk\". Every confirmed report instantly strengthens every other user's shield."),
    ("red", "Live now: dhaal-delta.vercel.app — judges can check their own inbox during Q&A."),
])
fill(slides[2], [  # TECHNICAL APPROACH
    ("h", "Stack"),
    ("t", "Next.js PWA (Vercel) · FastAPI on Vercel Python · MongoDB Atlas (durable community intel) · Claude claude-sonnet-5 (narration only) · Sarvam AI — Saarika ASR + Bulbul TTS (voice in/out) · QR decoded on-device with jsQR."),
    ("h", "Deterministic signal engine — the AI has zero verdict weight"),
    ("t", "UPI collect-vs-pay parser · lookalike-domain detection (token + edit-distance vs official bank/PSP seed list) · 10 scam-script families incl. coercion/extortion, job & loan-fee scams (Hindi + Hinglish + English) · bait-word VPA analysis · community blocklist (human-verified) · urgency/secrecy/fee-demand psychology signals. Score ≥60 → खतरा, ≥30 → सावधान."),
    ("h", "Reliability engineering"),
    ("t", "Every external call (Claude, Sarvam, Atlas) has retry-once + a deterministic fallback — dead venue Wi-Fi degrades prose, never protection. Anything mocked is labelled mocked:true on the wire."),
    ("t", "49 automated checks green (26 engine regression incl. adversarial sweep + 23 API contract) · measured live: verdict in ms, p50 5.4s with AI explanation, Hindi ASR 0.6s/clip."),
])
fill(slides[3], [  # USER EXPERIENCE & DESIGN
    ("h", "Designed like a public-safety poster, not a SaaS dashboard"),
    ("t", "Hand-crafted \"suraksha poster\" identity: ink + saffron hazard language, Anek Devanagari display type, rubber-stamp community count on the verdict card. Danger screams; safety whispers."),
    ("h", "Built for the next billion users"),
    ("t", "Hindi-first with a global हिं/EN toggle (persists across every page and every output, including the spoken warning) · voice in AND voice out for low-literacy users · QR photos decoded on-device — the image never leaves the phone · works on entry-level phones over weak networks."),
    ("h", "Dignity by design"),
    ("t", "Guardian mode shares only the risk summary with a chosen family member — never transactions. Every ward check appears on the guardian's page (risky = decision, clean = quiet note). Honest language everywhere: \"no KNOWN risk\", never \"safe\"."),
])
fill(slides[4], [  # FEASIBILITY AND VIABILITY
    ("big", "Not a concept — deployed, tested and durable tonight."),
    ("t", "Live: dhaal-delta.vercel.app (app) + dhaal-api.vercel.app (API) · MongoDB Atlas holds 450+ verified community reports · guardian pairing, flywheel and the voice loop all work end-to-end on stage hardware."),
    ("h", "Engineering feasibility"),
    ("t", "Entire stack runs on free tiers (Vercel + Atlas M0) — marginal cost per check is a fraction of a paisa (one short Claude narration; the verdict itself is free rule computation). 49 automated checks; an adversarial sweep of unseen scams was fixed pre-demo and folded into regression."),
    ("h", "Risks & mitigations"),
    ("t", "API outage → deterministic fallbacks (the demo survives) · false positives → delivery-vs-request context rules, tested on real bank OTP/debit SMS (score 0) · blocklist poisoning → human moderator verification before any indicator goes live · scale → stateless serverless + Atlas; TTS caching."),
])
fill(slides[5], [  # IMPACT AND BENEFITS
    ("big", "₹22,495 crore lost to cyber fraud in 2025 — and the victim pressed PAY themselves."),
    ("t", "24.51 billion UPI transactions/month (NPCI, Aug 2026) · 28.1 lakh complaints in 2025 (I4C) · ₹805 crore UPI fraud in FY26 (Parliament) — bank-side controls structurally cannot stop payments the victim authorises."),
    ("h", "Dhaal's compounding shield"),
    ("t", "One report → human verification → instant protection for every user: herd immunity for fraud — a scam burned in Jaipur today cannot work in Jodhpur tomorrow · Guardian mode protects the most-targeted group, the elderly · The recovery kit puts the golden hour in every pocket: fast 1930 reporting has already saved ₹7,130+ crore nationally."),
    ("h", "Who benefits"),
    ("t", "Every Indian with a phone (free forever) · families of elderly users · banks & UPI apps (fewer reimbursements) · police cyber cells (structured, early reports)."),
])
fill(slides[6], [  # BUSINESS MODEL & SUSTAINABILITY
    ("h", "Citizens: free forever"),
    ("t", "The consumer shield stays free — protection this fundamental must not be paywalled. Cost per user is negligible by construction (deterministic engine, free-tier infra)."),
    ("h", "Revenue: the institutions that bear today's fraud cost"),
    ("t", "Risk-API + verified-blocklist licensing to banks, fintechs and UPI apps (they reimburse this fraud today; prevention is cheaper) · a pre-payment check SDK inside UPI apps — the check runs before the PAY button renders · deployment partnerships: state cyber cells & the CSC network (assisted mode)."),
    ("h", "Sustainability & moat"),
    ("t", "The community blocklist compounds with every user — a network effect no new entrant starts with · Roadmap: one-tap 1930/I4C hand-off, 10+ Indic languages via the same Sarvam pipeline (single parameter), auto-verify thresholds for moderation at scale."),
])
fill(slides[7], [  # RESEARCH AND REFERENCES
    ("h", "Data sources (verified 11 Sep 2026)"),
    ("t", "NPCI monthly UPI statistics — 24.51B transactions / ₹29.82 lakh crore, Aug 2026 · I4C (MHA): ₹22,495 crore lost, 28.1 lakh complaints, 2025; 32.4M calls to 1930 · Ministry of Finance, Rajya Sabha reply: ₹805 crore UPI fraud, 10.64 lakh incidents, FY26 (to Nov) · PIB/MHA: ₹7,130+ crore saved via CFCFRMS (1930) early reporting · RBI guidelines on unauthorised-transaction liability."),
    ("h", "Domain research"),
    ("t", "Scam-script corpus built from I4C advisories & documented fraud patterns: digital arrest, KYC-expiry, collect-request refund bait, OLX/army advance, job-task & loan-fee scams, electricity disconnection · UPI deep-link (upi://) collect-vs-pay semantics · NPCI PSP handle registry for VPA verification."),
    ("h", "Build"),
    ("t", "Live app: dhaal-delta.vercel.app · API: dhaal-api.vercel.app · Repository: github.com/SaudSatopay/MUJ-HACKX (49 automated checks, full docs & contracts) · Sponsor tech used in production: Sarvam AI (Saarika ASR + Bulbul TTS), MongoDB Atlas."),
])

p.save("pitch/Dhaal-HackX-submission.pptx")
print("saved pitch/Dhaal-HackX-submission.pptx")

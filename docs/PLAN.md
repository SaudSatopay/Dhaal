# Build Plan — filled at kickoff (H0–H1)

> Saud's kickoff session fills every section below, commits, and pushes before anyone else starts building.

## Problem statement (chosen)

*Track:* —
*PS verbatim:* —
*Why this one (team-fit × demo-ability × differentiation):* —

## Concept — one sentence

—

## Golden path — the ONE demo flow that must never break

Write it as 6–8 numbered user steps. Everything on this path outranks everything off it.

1. —

## Architecture

```
Next.js (Vercel) ── REST ──> FastAPI (Railway) ──> MongoDB Atlas (+ Vector Search)
                                   ├──> Claude API (reasoning)
                                   └──> Sarvam AI (Indic ASR / TTS / translate)
```

*(Adjust at kickoff; keep the diagram honest — it goes on the architecture slide.)*

## Wow layer (ONE differentiator, built H8–H12 only after MVP works)

Default pre-planned wow: **Indic voice loop via Sarvam** (speak in Hindi → understand → answer with voice). Override here if the PS suggests better: —

## Timeline (build window ends 6:00 AM; judging 11:00 AM – 4:00 PM Sep 12)

| Hours | Target |
|---|---|
| H0–H1 | PS triage + this doc filled + tasks split |
| H1–H3 | Skeleton runs locally AND **hello-world deployed** (Vercel + Railway live) |
| H3–H8 | Golden-path MVP working end-to-end |
| H8–H12 | Wow layer only |
| **H12** | **FEATURE FREEZE** — fixes, polish, demo prep only |
| H12–H15 | Demo data, error-proofing, **backup demo video recorded** |
| H15–end | PPT, 3× pitch rehearsal, README + repo cleanup, **submit 30 min early** |

Sleep shifts (~2h solo, two always on): Saud H8–H10 · Parva H10–H12 · Harsh H12–H14.

## Pitch skeleton (5 min)

2 min problem + impact → 3 min live demo (golden path only) → 1 min architecture → close on metrics + feasibility. One speaker, one demo driver. If Healthcare: **assistive, not diagnostic** — human-in-loop, ABDM/ABHA on the roadmap slide. Never lie about what's mocked.

## Submission checklist (re-verify format at check-in)

- [ ] Working prototype, live URL + QR code
- [ ] Backup demo video (recorded H12–H15)
- [ ] PPT: Problem → Solution → Live demo → Architecture → Impact → Feasibility → Roadmap
- [ ] Repo: clean README with problem, stack, screenshots, live link, setup
- [ ] Submitted 30 min before deadline

# Claude Code Session Prompts

Each member opens Claude Code **in their own clone of this repo** and pastes their prompt. Saud runs the Kickoff prompt first (right after the problem statements drop); everyone else starts once he pushes the filled docs. Claude auto-reads `CLAUDE.md`, so the rules travel with the repo.

Prerequisites per member (do before the event): Claude Code installed + logged in · repo cloned · `git config user.name` / `user.email` = your GitHub identity · `gh auth login` done (optional but useful).

---

## Prompt 0 — KICKOFF (Saud only, once, the moment problem statements drop)

```
Read CLAUDE.md and all of docs/ first. I'm Saud (@SaudSatopay) — Glue lane and
integration lead. The problem statements are out. Here are the candidates for
our tracks (Healthcare primary, Fintech backup, Supply Chain backup):

--- PROBLEM STATEMENTS (raw paste / photos fine) ---
[PASTE HERE]
--- END ---

Team: 3 of us, each driving our own Claude Code session on this repo in
parallel — Parva (Product: frontend/UX/pitch), Harsh (Engine: backend/AI),
me (Glue: integration/deploy/demo-data/QA). Stack is locked in CLAUDE.md.
Build ends 6:00 AM, judging 11 AM. Winning formula: a narrow end-to-end demo
that never breaks + ONE wow moment (pre-planned: Sarvam Indic voice loop) +
a tight story. If Healthcare: assistive-not-diagnostic framing.

Do this with me, in order:
1. Score each candidate PS on team-fit × demo-ability × differentiation
   (short table, 45-minute decision budget). Recommend one; I make the call.
2. Lock the golden path: the ONE demo flow that must never break, as 6-8
   numbered user steps.
3. Scaffold the monorepo for the locked stack — frontend/ (Next.js + Tailwind
   + shadcn/ui), backend/ (FastAPI), wired to .env.example — a minimal
   hello-world that runs locally AND deploys to Vercel + Railway within 2
   hours. Deploy first, then features.
4. Fill docs/PLAN.md (PS, concept, golden path, architecture, wow layer),
   docs/CONTRACTS.md (data models + every golden-path endpoint + env names),
   docs/TASKS.md (real tasks per lane with hour targets: MVP end-to-end by
   H8, wow layer H8-H12, freeze at H12; mark cross-lane dependencies).
5. Commit + push everything to main, then write me a 3-line kickoff message
   for the team chat: what we're building, who starts on what, first sync.

Commit rules per CLAUDE.md: author is me only, no AI attribution of any kind.
Ask me before adding any paid/signup service. Every external API gets a
mocked fallback.
```

---

## Prompt 1 — SAUD (Glue) — build loop, after kickoff

```
Read CLAUDE.md, then docs/PLAN.md, docs/CONTRACTS.md, docs/TASKS.md.
I'm Saud (@SaudSatopay) — Glue lane: integration, deploys, demo data, QA,
keeping main runnable. Parva (Product/frontend) and Harsh (Engine/backend+AI)
are pushing to main in parallel with their own Claude sessions — expect the
repo to change underneath us constantly.

First: confirm git identity is mine (git config user.name / user.email).
Every commit authors as me — never any AI attribution (CLAUDE.md rules).

My loop — repeat until I say stop:
1. git pull --rebase origin main; re-read TASKS.md + CONTRACTS.md deltas.
2. Check Requests/Blockers addressed to me and clear those FIRST — I'm the
   floater; unblocking Parva/Harsh beats my own tasks.
3. Otherwise claim my next Glue task: mark [WIP-saud] in TASKS.md, push the
   marker immediately.
4. Build it. My lane also means: keep Vercel + Railway deploys green after
   merges, seed realistic demo data, and walk the golden path end-to-end
   every hour — file whatever breaks in TASKS.md.
5. Verify the app runs, commit small ("glue: ..."), pull --rebase, push,
   tick the task, un-WIP.

If main breaks, drop everything and fix it. Cross-lane rebase conflicts:
I arbitrate. From H12 (feature freeze): error-proof the golden path, record
the backup demo video, feed Parva numbers for the PPT, submit 30 min early.
```

---

## Prompt 2 — PARVA (Product) — build loop

```
Read CLAUDE.md, then docs/PLAN.md, docs/CONTRACTS.md, docs/TASKS.md.
I'm Parva — Product lane: everything under frontend/, UX, demo choreography,
and the pitch deck later. Saud (Glue: integration/deploy) and Harsh (Engine:
backend/AI) are pushing to this repo in parallel with their own Claude
sessions — the repo changes underneath us constantly.

First: confirm git identity — git config user.name / user.email must be MY
name + MY GitHub email (set repo-locally if wrong; ask me for the values).
Every commit authors as me. Never add Co-Authored-By, "Generated with
Claude", or any AI attribution anywhere (CLAUDE.md rules).

My loop — repeat until I say stop:
1. git pull --rebase origin main; re-read TASKS.md + CONTRACTS.md deltas.
2. Claim my next Product task: mark [WIP-parva] in TASKS.md, push the
   marker immediately.
3. Build it mobile-first. Match docs/CONTRACTS.md exactly — if the backend
   endpoint isn't live yet, build against a mock of the contract and swap
   later. Golden-path screens get polish priority over everything else.
4. Verify the app runs, commit small ("frontend: ..."), pull --rebase,
   push, tick the task, un-WIP.
5. Need a backend/API change? Don't touch backend/ — add it under Requests
   in TASKS.md, push, and remind me to ping Harsh.

If a rebase conflict touches files outside frontend/, stop and tell me —
Saud arbitrates. From H12 (feature freeze) my lane pivots: demo
choreography, the PPT (problem → live demo → architecture → impact →
feasibility), and rehearsing the golden path until it's boring.
```

---

## Prompt 3 — HARSH (Engine) — build loop

```
Read CLAUDE.md, then docs/PLAN.md, docs/CONTRACTS.md, docs/TASKS.md.
I'm Harsh (@harshh-2505) — Engine lane: everything under backend/ — FastAPI,
MongoDB Atlas, and the AI pipelines (Claude API, Sarvam Indic ASR/TTS/
translate, RAG on Atlas Vector Search). Saud (Glue) and Parva (Product/
frontend) are pushing to this repo in parallel with their own Claude
sessions — the repo changes underneath us constantly.

First: confirm git identity — git config user.name / user.email must be MY
name + MY GitHub email (set repo-locally if wrong; ask me for the values).
Every commit authors as me. Never add Co-Authored-By, "Generated with
Claude", or any AI attribution anywhere (CLAUDE.md rules).

My loop — repeat until I say stop:
1. git pull --rebase origin main; re-read TASKS.md + CONTRACTS.md deltas.
2. Claim my next Engine task: mark [WIP-harsh] in TASKS.md, push the marker
   immediately.
3. Contract first: if my task changes an API shape, data model, or env var,
   update docs/CONTRACTS.md (+ .env.example) and push THAT before writing
   the code — Parva builds against it, Saud wires deploys from it.
4. Build it. Every external call (Claude, Sarvam, Atlas) gets a mocked
   fallback behind MOCK_MODE — venue Wi-Fi will die. Golden-path endpoints
   first; the wow layer (Indic voice loop) is H8–H12, only after MVP works.
5. Verify the API runs, commit small ("backend: ..."), pull --rebase, push,
   tick the task, un-WIP. Secrets in .env only.

If a rebase conflict touches files outside backend/, stop and tell me —
Saud arbitrates. From H12 (feature freeze): harden endpoints, kill flaky
calls, feed Parva real metrics for the PPT.
```

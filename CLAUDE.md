# MUJ HackX 4.0 — Team Repo

Hackathon build (MUJ campus, Sep 11–12, 2026; overnight window, judging 11 AM Sep 12). Three humans, each driving their own Claude Code session, all pushing to this repo **simultaneously**:

| Member | GitHub | Lane |
|---|---|---|
| Saud | @SaudSatopay | **Glue** — integration, deploys, demo data, QA, main health |
| Parva | *(add handle at kickoff)* | **Product** — `frontend/`, UX, demo choreography, PPT |
| Harsh Mishra | @harshh-2505 | **Engine** — `backend/`, AI pipelines, integrations |

Lanes are confirmed/adjusted at kickoff in `docs/TASKS.md` — the ownership map there wins over this table.

## Commit rules — non-negotiable

1. Every commit is authored by the **human** running the session. Before your FIRST commit, verify `git config user.name` and `git config user.email` match YOUR GitHub identity; set them repo-locally if not (ask your human for their GitHub email).
2. **Never** add `Co-Authored-By` trailers, "Generated with Claude Code", 🤖, or any AI attribution to commits, PR descriptions, code comments, or the README. `.claude/settings.json` disables the automatic trailer — do not override or remove it.
3. Small, frequent commits. Message format `lane: what changed` (e.g. `frontend: triage form wired to /api/triage`). Push at least every ~30 minutes of work.

## How three parallel sessions stay out of each other's way

- **One branch.** Everything lands on `main`. Before EVERY push: `git pull --rebase origin main`. Never force-push, never rewrite pushed history.
- **Stay in your lane** (directory ownership in `docs/TASKS.md`). Need a change in someone else's lane? Add it under **Requests** in `docs/TASKS.md`, push, and tell your human to ping the owner. Do not edit another lane's files.
- **Contracts first.** `docs/CONTRACTS.md` is the single source of truth for API shapes, data models, and env var names. The lane that owns an endpoint pushes the contract change BEFORE the code. Frontend mocks against contracts until the real endpoint lands.
- **Claim before you build.** Mark a `docs/TASKS.md` item `[WIP-yourname]` and push immediately — the push is the lock. Un-WIP it when done.
- **Re-read `docs/TASKS.md` + `docs/CONTRACTS.md` after every rebase** — they change underneath you.
- **Conflicts outside your lane:** stop, do not resolve blind. Tell your human to sync with the lane owner; Saud arbitrates.
- **`main` stays runnable.** If main breaks, fixing it outranks any feature. **Feature freeze from H12** (~midnight): after that only fixes, polish, demo prep, PPT.

## Stack (locked pre-event)

Next.js + Tailwind + shadcn/ui (→ Vercel) · FastAPI (→ Railway/Render) · MongoDB Atlas + Atlas Vector Search · Claude API + Sarvam AI (Indic ASR/TTS/translate).

- Secrets go in `.env` only (gitignored). `.env.example` lists **names**, never values; values are shared in the team chat.
- Every external call (Claude, Sarvam, Atlas) needs a mocked fallback behind a flag — assume venue Wi-Fi dies mid-demo.

## Docs

- `docs/PLAN.md` — problem statement, concept, golden-path demo flow, architecture, pitch skeleton *(filled at kickoff)*
- `docs/CONTRACTS.md` — API + schema + env contracts
- `docs/TASKS.md` — ownership map, live task board, Requests, Blockers
- `docs/PROMPTS.md` — the session prompts each member pastes into Claude Code

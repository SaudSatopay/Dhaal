# Task Board — the live coordination file

Claim a task: change `[ ]` to `[WIP-saud]` / `[WIP-parva]` / `[WIP-harsh]`, **push immediately** (the push is the lock). Done: `[x]`, un-WIP, push. Re-read this file after every `git pull --rebase`.

## Ownership map (who may edit what)

| Lane | Owner | Owns |
|---|---|---|
| **Product** | Parva | `frontend/**` · PPT · demo choreography |
| **Engine** | Harsh (@harshh-2505) | `backend/**` · AI pipelines · Data models + API sections of `docs/CONTRACTS.md` |
| **Glue** | Saud (@SaudSatopay) | root configs · deploy configs · `scripts/` · `demo/` (seed data) · `README.md` · rest of `docs/` |

Rule: you edit only what your lane owns. Anything else goes through **Requests** below.

## Board

*(Kickoff session replaces these placeholders with real tasks per lane, tagged with hour targets — MVP by H8, wow by H12, freeze at H12.)*

### Product — Parva
- [ ] (kickoff fills)

### Engine — Harsh
- [ ] (kickoff fills)

### Glue — Saud
- [ ] (kickoff fills)

## Requests (cross-lane asks — add, push, then ping them in person/chat)

Format: `- [ ] FOR harsh, FROM parva — need /api/triage to also return confidence score`

- *(none yet)*

## Blockers (things stopping a lane right now — Saud clears these first)

- *(none yet)*

## Done

- *(move finished items here if the board gets noisy)*

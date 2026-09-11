# Dhaal (ढाल)

**पैसे भेजने से पहले — एक जाँच।** A consumer scam-protection layer: check any message, QR, link, number, or call recording *before* you pay — get the verdict with reasons in your own language. Every confirmed report strengthens everyone's shield.

Built at MUJ HackX 4.0 (Sep 11–12, 2026) · Fintech PS #7.

*Live demo link, screenshots and pitch land here before submission.*

## Run locally

Backend (FastAPI, port 8000):

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Frontend (Next.js, port 3000):

```
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000 — the home page shows API connection status. Stub API serves the full contract with demo fixtures out of the box (no keys, no DB needed).

## Team docs

- [docs/PLAN.md](docs/PLAN.md) — locked PS, golden path, architecture, timeline
- [docs/CONTRACTS.md](docs/CONTRACTS.md) — API + data contracts (source of truth)
- [docs/TASKS.md](docs/TASKS.md) — live task board + ownership map

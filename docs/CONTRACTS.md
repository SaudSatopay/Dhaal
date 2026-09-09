# Contracts — single source of truth

API shapes, data models, and env var names. **The owning lane pushes a contract change BEFORE the code that implements it.** Frontend builds against these (mocked if needed) — never against guesses.

Change protocol: edit here → commit `contracts: ...` → push → then implement. Everyone re-reads this file after every rebase.

## Env vars

Mirror of `.env.example` — names + who consumes them:

| Name | Used by | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | backend | reasoning LLM |
| `SARVAM_API_KEY` | backend | Indic ASR/TTS/translate |
| `MONGODB_URI` | backend | Atlas cluster |
| `NEXT_PUBLIC_API_URL` | frontend | FastAPI base URL |
| `MOCK_MODE` | backend | `true` = all external calls return canned fixtures (demo fallback) |

## Data models (MongoDB collections)

*Filled at kickoff. Format:*

### `collection_name` — owner: Engine
```json
{ "_id": "ObjectId", "field": "type — meaning" }
```

## API endpoints

*Filled at kickoff. Golden-path endpoints first. Format:*

### `POST /api/example` — owner: Engine — status: contract-only | mocked | live
Request:
```json
{ "field": "string" }
```
Response `200`:
```json
{ "field": "string" }
```
Errors: `4xx/5xx` shape: `{ "error": "message" }`

# AI Scientist — Frontend

A Next.js 15 + Tailwind dashboard for the AI Scientist backend.

## Pages

* **Dashboard** (`/`) — Run the full pipeline on a topic, watch results stream in.
* **Papers** (`/papers`) — Multi-source search + browse the indexed corpus.
* **Ideas** (`/ideas`) — Generate novel research directions, scored by an LLM peer reviewer.
* **Experiments** (`/experiments`) — Inspect generated code, captured stdout/stderr, and parsed metrics.
* **Drafts** (`/drafts`) — Read drafted papers rendered as Markdown.

## Setup

```bash
cd frontend
cp .env.example .env.local            # if your backend isn't on http://127.0.0.1:8000
npm install
npm run dev                           # http://localhost:3000
```

The backend must be running:

```bash
cd backend
ai-scientist serve --port 8000
```

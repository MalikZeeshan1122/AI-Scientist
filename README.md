# AI Scientist

An autonomous research assistant that can read scientific papers, propose new research ideas,
run computational experiments in a sandbox, draft full academic papers, and iteratively
critique and improve its own work.

> Inspired by recent work like Sakana AI's *AI Scientist*, AutoGPT-Sci, and Aviary —
> built from scratch as a transparent, hackable, locally-runnable reference implementation.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          AI Scientist Pipeline                           │
│                                                                          │
│   Topic                                                                  │
│     │                                                                    │
│     ▼                                                                    │
│  ┌──────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │  Search  ├──►│   Ingest +  ├──►│   Ideate    ├──►│   Score &   │     │
│  │  4 srcs  │   │  Summarise  │   │ (RAG over   │   │   rank      │     │
│  └──────────┘   │  + chunk +  │   │  ChromaDB)  │   └──────┬──────┘     │
│                 │  embed      │   └─────────────┘          │            │
│                 └─────────────┘                            ▼            │
│                                                  ┌────────────────┐     │
│                                                  │  Design + run  │     │
│                                                  │  Python expt.  │     │
│                                                  │  in sandbox    │     │
│                                                  └────────┬───────┘     │
│                                                           ▼             │
│                                                  ┌────────────────┐     │
│                                                  │  Draft paper   │     │
│                                                  │  (MD / LaTeX)  │     │
│                                                  └────────┬───────┘     │
│                                                           ▼             │
│                                                  ┌────────────────┐     │
│                                                  │ Critique loop  │     │
│                                                  │ self-improve   │     │
│                                                  └────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

## Features

| Capability | Implementation |
|---|---|
| **Read papers** | Unified search across **arXiv**, **Semantic Scholar**, **OpenAlex**, and a **local PDF folder**, with PDF text extraction |
| **Summarise findings** | Section-aware chunking + structured LLM summarisation (`PaperSummary` Pydantic schema) |
| **Semantic search** | Persistent **ChromaDB** vector store with Google `text-embedding-004` |
| **Propose ideas** | LLM ideator grounded in retrieved chunks + seed papers; auto-scored on novelty / feasibility / impact |
| **Run simulations** | LLM-generated Python script executed in a subprocess sandbox with timeout, output cap, and metric extraction |
| **Draft papers** | Full Markdown and LaTeX output, with abstract + standard sections + references |
| **Self-improve** | Reviewer-critic loop that scores drafts (soundness/clarity/novelty/significance) and rewrites until quality plateaus |
| **LLM backends** | Pluggable: **Anthropic Claude** + **Google Gemini** (add more in `ai_scientist/llm/`) |
| **Persistence** | SQLite (`projects`, `papers`, `ideas`, `experiments`, `drafts`) |
| **CLI** | `ai-scientist search/ideate/run/projects/serve` (Typer + Rich) |
| **HTTP API** | FastAPI with OpenAPI docs at `/docs` |
| **Web UI** | Next.js 15 + Tailwind dashboard for runs, papers, ideas, experiments, drafts |
| **Tests** | 20-test pytest suite using mocked LLMs / HTTP — no API keys required |

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env               # set ANTHROPIC_API_KEY and/or GOOGLE_API_KEY
pytest                             # 20 tests, no network needed
ai-scientist serve                 # FastAPI on :8000
```

### 2. Frontend

```bash
cd frontend
cp .env.example .env.local         # only if backend isn't on http://127.0.0.1:8000
npm install
npm run dev                        # http://localhost:3000
```

### 3. Or with Docker

```bash
docker compose up --build
# backend  -> http://localhost:8000  (Swagger at /docs)
# frontend -> http://localhost:3000
```

## CLI tour

```bash
ai-scientist search "diffusion models for protein design"
ai-scientist ideate "energy-efficient transformer inference" --n 5
ai-scientist run    "sparse mixture-of-experts inference" \
                    --papers 6 --ideas 5 --refine 2 --format markdown
ai-scientist projects
ai-scientist serve  --port 8000
```

The `run` command performs the full pipeline end-to-end:

1. Searches all configured paper sources
2. Downloads PDFs + extracts + chunks + embeds them in ChromaDB
3. Generates structured summaries
4. Generates `--ideas` novel research directions, peer-reviews each
5. Picks the highest-scoring idea, designs a self-contained Python experiment
6. Executes the experiment inside a sandboxed subprocess (default 120s wall-clock cap)
7. Drafts a workshop-style paper (Markdown or LaTeX)
8. Runs the critique-and-revise self-improvement loop for `--refine` iterations

## Project layout

```
AI-Scientist-1/
├── backend/                            Python package (Pydantic + FastAPI + Typer)
│   ├── ai_scientist/
│   │   ├── llm/                        Pluggable Anthropic + Google providers
│   │   ├── sources/                    arxiv / semantic_scholar / openalex / local_pdf / unified
│   │   ├── ingestion/                  PDF parsing, chunking, structured summarisation
│   │   ├── vectorstore/                ChromaDB persistent vector store
│   │   ├── ideation/                   Idea generation + peer-review scoring
│   │   ├── experiments/                LLM code-gen + subprocess sandbox
│   │   ├── writing/                    Markdown + LaTeX paper drafting
│   │   ├── selfimprove/                Critique → revise loop
│   │   ├── api/                        FastAPI app
│   │   ├── pipeline.py                 End-to-end orchestration
│   │   ├── storage.py                  SQLite persistence
│   │   ├── cli.py                      Typer CLI
│   │   └── config.py                   Pydantic settings
│   ├── examples/                       6 runnable example scripts
│   ├── tests/                          20-test pytest suite (no API keys needed)
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── README.md
├── frontend/                           Next.js 15 + Tailwind dashboard
│   ├── app/
│   │   ├── page.tsx                    Dashboard (run pipeline)
│   │   ├── papers/page.tsx             Multi-source search + indexed corpus
│   │   ├── ideas/page.tsx              Generate + browse ideas
│   │   ├── experiments/page.tsx        Code, output, metrics
│   │   └── drafts/page.tsx             Rendered Markdown viewer
│   ├── components/
│   ├── lib/api.ts
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Examples

```bash
cd backend
python examples/01_search_arxiv.py "graph neural networks"
python examples/02_summarize_paper.py "attention is all you need"
python examples/03_generate_ideas.py "test-time compute scaling"
python examples/04_run_experiment.py
python examples/05_draft_paper.py
python examples/06_full_pipeline.py "sparse mixture-of-experts"
```

## Design notes

* **Pluggable LLM** — every component takes an optional `llm: LLMProvider`; `get_llm()` is the
  default factory keyed off `AI_SCIENTIST_DEFAULT_PROVIDER`.
* **Pluggable sources** — implement `PaperSource` to add new corpora (PubMed, NASA ADS, etc.).
* **Structured outputs** — the LLM is always asked for JSON validated against a Pydantic schema
  (`PaperSummary`, `IdeaScore`, `_Design`, `CritiqueReport`, …); no fragile regex parsing.
* **Deterministic experiments** — the experiment-design prompt requires a metrics block delimited
  by `===METRICS_START===` / `===METRICS_END===`, so results are machine-readable.
* **Sandbox safety** — `experiments/sandbox.py` is a *development* sandbox: subprocess + wall-clock
  timeout + output cap + per-run workspace dir. For untrusted code in production, run inside a
  Docker / gVisor / firecracker container.

## Honest limitations

This is a working reference implementation, not a magic auto-discovery system:

* "Novelty" is judged by an LLM, not a real literature-coverage check.
* Experiments are limited to <2 minutes of CPU on a single machine.
* The system has no concept of statistical significance across multiple runs.
* Produced drafts need a human's careful read before being treated as research output.

The point is to make the **pipeline** transparent and hackable, so you can swap in better
components for any stage you care about.

## Contributors

Credits are listed in [**CONTRIBUTORS.md**](CONTRIBUTORS.md). GitHub also builds a [contributor graph](https://github.com/MalikZeeshan1122/AI-Scientist/graphs/contributors) from merged commits.

## License

MIT.

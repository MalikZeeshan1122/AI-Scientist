# AI Scientist — Backend

An autonomous research assistant that:

1. **Reads** scientific papers (arXiv, Semantic Scholar, OpenAlex, local PDFs)
2. **Indexes** them in a vector store (ChromaDB)
3. **Proposes** new research ideas grounded in that corpus
4. **Designs and runs** Python experiments in a sandboxed subprocess
5. **Drafts** a workshop-style paper (Markdown or LaTeX)
6. **Critiques and revises** its own draft in a self-improvement loop

Pluggable LLM backends: **Anthropic Claude** and **Google Gemini**.

## Install

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env  # then fill in ANTHROPIC_API_KEY / GOOGLE_API_KEY
```

## CLI

```bash
ai-scientist search "diffusion models for protein design"
ai-scientist ideate "energy-efficient transformer inference" --n 5
ai-scientist run    "sparse mixture-of-experts inference" --papers 6 --ideas 5 --refine 2
ai-scientist projects
ai-scientist serve  # starts the FastAPI backend on :8000
```

## Examples

```bash
python examples/01_search_arxiv.py "graph neural networks"
python examples/02_summarize_paper.py "attention is all you need"
python examples/03_generate_ideas.py "test-time compute scaling"
python examples/04_run_experiment.py
python examples/05_draft_paper.py
python examples/06_full_pipeline.py "sparse mixture-of-experts"
```

## Tests

```bash
pytest
```

The test suite uses a `FakeLLM` and mocked HTTP — it does not require API keys or network access.

## Architecture

```
ai_scientist/
├── config.py              Pydantic settings (env vars)
├── llm/                   Pluggable Anthropic + Google providers
├── sources/               Paper sources: arxiv, semantic_scholar, openalex, local_pdf, unified
├── ingestion/             PDF parsing, section-aware chunking, structured summarisation
├── vectorstore/           ChromaDB-backed semantic search
├── ideation/              Novelty-aware idea generation + peer-review scoring
├── experiments/           LLM code-gen + sandboxed Python execution
├── writing/               Markdown + LaTeX paper drafting
├── selfimprove/           Critique → revise loop
├── pipeline.py            End-to-end orchestration
├── storage.py             SQLite persistence (projects, papers, ideas, experiments, drafts)
├── cli.py                 Typer CLI
└── api/                   FastAPI HTTP API consumed by the Next.js frontend
```

## Sandbox safety

`experiments/sandbox.py` runs LLM-generated Python in a subprocess with:

* a wall-clock timeout (default 120 s)
* an output-size cap
* writes confined to a per-run workspace directory

This is **a development sandbox, not a security boundary**. For untrusted code in
production, run inside Docker or a microVM.

## API

```bash
ai-scientist serve --port 8000
# then open http://127.0.0.1:8000/docs for interactive Swagger UI
```

Key endpoints: `POST /search`, `POST /ideate`, `POST /experiment`, `POST /draft`,
`POST /run`, `GET /projects`, `GET /projects/{id}`.

## Configuration

All knobs live in `.env` (see `.env.example`). Highlights:

| Variable | Default | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required if `default_provider=anthropic` |
| `GOOGLE_API_KEY` | — | Required for Gemini and for embeddings |
| `AI_SCIENTIST_DEFAULT_PROVIDER` | `anthropic` | `anthropic` or `google` |
| `AI_SCIENTIST_SANDBOX_TIMEOUT_S` | `120` | Per-experiment wall-clock cap |
| `AI_SCIENTIST_CHROMA_DIR` | `./data/chroma` | Vector store persistence |

# VentureValuator

**AI-powered startup pitch deck analyser for investors and founders.**

[![CI](https://github.com/riddhi2106/VentureValuator/actions/workflows/ci.yml/badge.svg)](https://github.com/riddhi2106/VentureValuator/actions/workflows/ci.yml)

Upload a pitch deck PDF and VentureValuator runs a full due-diligence pipeline in minutes — extracting structured data, conducting web-grounded market research, modelling unit economics, stress-testing assumptions with a sceptical VC persona, and generating a professional investor memo and PowerPoint pitch deck.

---

## 🔍 The Problem

Early-stage founders often want to explore the true potential of their ideas — to understand whether the problem is real, whether a market exists, and whether the business is financially viable. At the same time, investors need fast, structured insights to decide whether a startup is worth pursuing.

Yet evaluating a startup typically requires:
- Extensive research into markets and competitors
- Manual extraction of information from messy pitch decks
- Careful analysis of traction and unit economics
- The creation of consistent memos or decks

This process is **slow, subjective, and error-prone**.

## 💡 The Solution

VentureValuator streamlines the entire startup-evaluation workflow for both founders and investors. Instead of manually extracting information from pitch decks, researching markets, and building financial models, the tool automates each step — from structured data extraction to financial projections, market analysis, scoring, and memo/deck generation.

This reduces hours of work into minutes, enabling founders to quickly test the viability of their ideas and helping investors make faster, more consistent, data-driven decisions.

---

## ✨ Features

| Capability | Details |
|---|---|
| **PDF extraction** | Parses any pitch deck and extracts problem, solution, target customer, business model, GTM strategy, competition, pricing, and key numeric metrics |
| **Market research** | Web-grounded analysis via DuckDuckGo / Tavily with live public-company comparable multiples via a local MCP server (Yahoo Finance P/S ratios) |
| **Financial modelling** | Builds a 24-month revenue projection with base / conservative / optimistic scenarios, gross margin, CAC, LTV, LTV/CAC ratio, and breakeven month |
| **Sceptical VC review** | A dedicated agent challenges claims, surfaces red flags, flags missing data, and proposes partner-meeting questions |
| **Investor memo** | Generates a structured memo with a weighted 6-dimension rubric score, overall verdict (Invest / Pass / Neutral / Avoid), and confidence percentage |
| **Pitch deck export** | Auto-generates a `.pptx` slide deck from the analysis output |
| **Sensitivity sandbox** | Interactive sliders to re-score each dimension and adjust LTV/CAC assumptions — live recalculation in the UI |
| **Memory** | All runs are persisted locally; overview dashboard shows total analyses, latest score, and connection status |
| **Cancellable pipeline** | Each stage shows real-time progress; the user can cancel mid-run |

---

## 🏗️ Architecture

```
VentureValuator/
├── app/                    # Streamlit UI layer
│   ├── ui.py               # Entry point (page router)
│   ├── components.py       # Shared UI components & pipeline threading
│   ├── pipeline_store.py   # Thread-safe pipeline state store
│   ├── styles.py           # Global CSS theme injection
│   └── pages/              # Multi-page Streamlit pages
│
├── core/
│   ├── orchestrator.py     # Sequential 6-step pipeline runner
│   └── memory_manager.py   # Local run persistence
│
├── agents/                 # One agent per pipeline stage
│   ├── extractor_agent.py  # PDF → structured JSON (LLM)
│   ├── market_agent.py     # Market research (web + MCP comps)
│   ├── financial_agent.py  # Financial model & projections
│   ├── skeptic_agent.py    # Sceptical VC challenge review
│   ├── memo_agent.py       # Investor memo + weighted scoring
│   └── deck_agent.py       # PowerPoint deck generation
│
├── tools/
│   ├── llm_client.py       # Unified ChatGPT client and auth fallbacks
│   ├── pdf_reader.py       # PDF text extraction (pdfplumber)
│   ├── web_search.py       # DuckDuckGo / Tavily search wrapper
│   ├── mcp_client.py       # Client for local MCP finance server
│   ├── finance_utils.py    # Financial helper utilities
│   └── auth_status.py      # ChatGPT OAuth connection checker
│
├── mcp_server.py           # Local MCP server (yfinance P/S ratios)
├── tests/                  # Pytest unit/integration + Playwright E2E tests
├── .github/workflows/      # Automated lint, test, coverage, and image build
├── Dockerfile              # Non-root production container
├── pyproject.toml          # Project metadata and dependency/tool configuration
├── uv.lock                 # Reproducible dependency lock
├── requirements.txt        # Streamlit Cloud compatibility export
└── .env.example
```

### Pipeline stages

```
PDF Upload
    │
    ▼
[1] ExtractionAgent   →  structured JSON from pitch text
    │
    ▼
[2] MarketAgent       →  TAM/SAM/SOM, trends, competitors, web citations
    │
    ▼
[3] FinancialAgent    →  revenue model, CAC, LTV, breakeven
    │
    ▼
[4] SkepticAgent      →  red flags, partner questions, diligence steps
    │
    ▼
[5] MemoAgent         →  weighted rubric score + investor memo text
    │
    ▼
[6] PitchDeckAgent    →  .pptx export
```

---

## 🎯 Scoring Rubric

The `MemoAgent` uses a weighted 6-dimension framework:

| Dimension | Weight |
|---|---|
| Market Timing | 20% |
| Traction Metrics | 20% |
| Unit Economics | 20% |
| Problem Clarity | 15% |
| Competitive Moat | 15% |
| GTM & Team | 10% |

Scores reflect the quality, magnitude, and provenance of the available evidence—not
merely whether a field is populated. Deck-sourced financials receive more weight than
model assumptions, market claims are rewarded for independent citations, and the
sceptical VC review applies targeted penalties to the dimensions affected by each red
flag or missing diligence item. Confidence is calculated separately from evidence
completeness.

**Verdicts:**

| Score | Verdict |
|---|---|
| ≥ 7.5 | Invest |
| ≥ 6.0 | Pass |
| ≥ 5.0 | Neutral |
| < 5.0 | Avoid |

---

## 🚀 Quick start

### 1. Clone and install

```bash
git clone https://github.com/your-org/VentureValuator.git
cd VentureValuator
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install uv
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM provider — "chatgpt_oauth" uses the local ChatGPT OAuth proxy
LLM_PROVIDER=chatgpt_oauth
CHATGPT_MODEL=gpt-4o

# If using the ChatGPT OAuth proxy (login-with-chatgpt)
OPENAI_OAUTH_PROXY_URL=http://127.0.0.1:10531/v1
```

### 3. Start the MCP finance server (optional but recommended)

The MCP server provides live Price/Sales ratio comparables via Yahoo Finance.

```bash
python mcp_server.py
```

> The server runs on stdio and is consumed automatically by the `MarketAgent`. You can leave it running in the background.

### 4. Launch the app

```bash
streamlit run app/ui.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Testing and code quality

Install the development toolchain from the locked environment:

```bash
uv sync --frozen --extra dev
```

Run the same checks enforced by CI:

```bash
uv run ruff check .
TEST_MODE=true DISABLE_WEB_SEARCH=true uv run pytest -q --cov
uv run python -m compileall -q agents app core tools
```

The Python suite covers deterministic financial calculations, evidence provenance,
rubric-v2 scoring, targeted skeptic penalties, startup naming, pipeline state, and
end-to-end orchestration with external agents mocked. Browser journeys remain under
`tests/*.spec.ts`.

GitHub Actions runs linting, compilation, tests, and coverage on Python 3.12, 3.13,
and 3.14, then verifies that the production Docker image builds.

---

## 🐳 Docker

Build and run the non-root production image:

```bash
docker build -t venturevaluator .
docker run --rm -p 8501:8501 --env-file .env venturevaluator
```

The container exposes port `8501`, persists runtime data under `/app/memory` and
`/app/outputs`, and includes a health check against Streamlit's `/_stcore/health`
endpoint. Mount those directories as volumes when persistence outside the container
is required.

---

## 🔑 LLM Configuration

VentureValuator supports two LLM backends, configurable via `LLM_PROVIDER` in `.env`:

| Provider | Description |
|---|---|
| `chatgpt_oauth` | Uses the [login-with-chatgpt](https://pypi.org/project/login-with-chatgpt/) OAuth proxy — no API key required, uses your ChatGPT account |
| `openai` | Standard OpenAI API key (`OPENAI_API_KEY`) |

### Test / demo mode

Set `TEST_MODE=true` in `.env` to run the UI without any live LLM calls. Agents return mock responses so you can explore the interface.

---

## 🌐 Web search

Market research is web-grounded by default.

**DuckDuckGo** (`ddgs`) — zero-config fallback, no API key needed.

To disable web search entirely (e.g. offline / air-gapped):

```env
DISABLE_WEB_SEARCH=true
```

---

## 📂 Outputs

After each analysis the following artefacts are available for download directly from the UI:

| Output | Format | Description |
|---|---|---|
| Investor memo | `.txt` | Full structured memo with scores, strengths, risks, and sceptic review |
| Analysis data | `.json` | Complete raw pipeline output (extracted fields, market data, financials, etc.) |
| Pitch deck | `.pptx` | Auto-generated PowerPoint presentation |

All runs are also persisted in the `memory/` directory for the history dashboard.

---

## 📦 Dependencies

`pyproject.toml` is the dependency and tooling source of truth. `uv.lock` pins the
complete reproducible environment; `requirements.txt` is retained for Streamlit
Community Cloud compatibility.

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `pdfplumber` | PDF text extraction |
| `openai ≥ 2.45` | LLM API client |
| `login-with-chatgpt` | ChatGPT OAuth proxy |
| `ddgs ≥ 9.0` | DuckDuckGo search |
| `plotly ≥ 5.18` | Interactive charts (radar, revenue projection) |
| `python-pptx` | PowerPoint deck generation |
| `yfinance ≥ 0.2` | Live public company financial data |
| `mcp ≥ 1.0` | Model Context Protocol server/client |
| `httpx` | Async HTTP client |
| `python-dotenv` | `.env` file loading |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m "feat: add my feature"`)
4. Push and open a pull request

Before opening a pull request, run `uv run ruff check .` and
`TEST_MODE=true DISABLE_WEB_SEARCH=true uv run pytest -q --cov`. Please keep each
agent in its own file under `agents/` and use `tools/llm_client.py` as the single LLM
dispatch point.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

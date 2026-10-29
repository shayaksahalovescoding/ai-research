# 🔬 Autonomous AI Research Scientist Platform

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PySide6 / Qt](https://img.shields.io/badge/PySide6-Qt_6.8+-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://wiki.qt.io/Qt_for_Python)
[![Docker Sandbox](https://img.shields.io/badge/Docker-Zero--Trust_Sandbox-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-1.14+-4A5568?style=for-the-badge)](https://alembic.sqlalchemy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

An auditable, safety-conscious, end-to-end **Autonomous AI Research Scientist** platform. The system conducts continuous, evidence-grounded scientific research: querying open-access scientific literature repositories, generating competing hypothesis tournaments, selecting optimal experiments using **Expected Information Gain (EIG)**, running isolated simulation experiments via **Domain Experiment Adapters** in zero-trust Docker sandboxes, performing non-parametric statistical inference, submitting results to a **Deep Epistemic Scientific Critic**, updating Bayesian posterior beliefs, and compiling publication-grade academic manuscripts in PDF, LaTeX (`.tex`), and Markdown formats.

> **Epistemic Core Principle:** Generated text, synthesized hypotheses, and computational sandbox results are **never** treated as authoritative facts without their cryptographically linked provenance chains and multi-seed replication verification.

---

## 🏛️ Architectural Overview: Domain-Agnostic Core + Domain Adapters

```
                     ┌────────────────────────────────────────────────────────┐
                     │         Domain-Agnostic Scientific Reasoning Core      │
                     ├────────────────────────────────────────────────────────┤
                     │ • Literature Mining & Full-Text PDF Reader (arXiv/PMC) │
                     │ • Hybrid Information Retrieval (Dense + BM25 + RRF)   │
                     │ • Sentence-Level Evidence Extraction & Provenance      │
                     │ • Research Gap Discovery & Unverified Assumptions      │
                     │ • Competing Hypotheses Tournament {H_main, H_null, ...}│
                     │ • Expected Information Gain (EIG / Cost) Engine        │
                     │ • Deep Epistemic Referee (Power, Strawman, Leakage)    │
                     │ • Bayesian Posterior Belief Updater P(H_i | Data)      │
                     │ • Academic Manuscript & LaTeX/PDF Exporter             │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │          Domain Experiment Adapter Interface           │
                     ├───────────────────────────┬────────────────────────────┤
                     │   MLExperimentAdapter     │ BiomedicalExperimentAdapter│
                     │ (Curvature Momentum,      │ (Nanocarrier Diffusion,    │
                     │  RL Q-Ensembles,          │  Pharmacokinetics &        │
                     │  Generalization Sparsity) │  Cellular Uptake Kinetics) │
                     └───────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                     ┌────────────────────────────────────────────────────────┐
                     │        Zero-Trust Isolated Docker Sandbox              │
                     │ (Read-only root, no network, drop ALL caps, UID 10001) │
                     └────────────────────────────────────────────────────────┘
```

```
                      ┌────────────────────────────────────────────────────────┐
                      │              User Research Inquiry / GUI               │
                      └───────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
                      ┌────────────────────────────────────────────────────────┐
                      │         Multi-Source Scientific Literature             │
                      │  [PubMed (NIH)] [OpenAlex (250M+)] [arXiv] [Live Web]  │
                      └───────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
                      ┌────────────────────────────────────────────────────────┐
                      │            PDF Full-Text & Section Parser              │
                      │  (Abstract, Methodology, Empirical Tables, Discussion) │
                      └───────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
                      ┌────────────────────────────────────────────────────────┐
                      │   Dense Semantic Vector Store & Subword Embeddings     │
                      │   (Multi-filter: Year, Citations, Journal, Section)    │
                      └───────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
                      ┌────────────────────────────────────────────────────────┐
                      │       Immutable Sentence-Level Evidence Locators       │
                      └───────────────────────────┬────────────────────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────┴────────────────────────────────────────────────┐
│                           AUTONOMOUS MULTI-ITERATION DISCOVERY LOOP                              │
│                                                                                                  │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 1. Hypothesis Generator (Local Ollama Llama-3 / Conservative Evidence Synthesizer)       │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                                 ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 2. Dynamic Simulation Generator & AST Static Security Guardrails Filter                  │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                                 ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 3. Isolated Docker Sandbox Execution (Read-only root, no network, drop ALL caps, UID 10001)│   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                                 ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 4. Paired Statistical Analysis (Bootstrap 95% CI B=2000, Permutation Test N=10000, Cohen d│   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                                 ▼                                                │
│   ┌──────────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 5. Scientific Critic & Automated Peer Referee (Rejects non-positive Δ, low sample count) │   │
│   └─────────────────────────────────────────────┬────────────────────────────────────────────┘   │
│                                                 │                                                │
│                   Refinement Feedback           │ Verdict: ACCEPT or Max Iterations Reached      │
│                   ◄─────────────────────────────┴────────────────────────────┐                   │
└──────────────────────────────────────────────────────────────────────────────┼───────────────────┘
                                                                               │
                                                                               ▼
                                           ┌───────────────────────────────────────────────────────┐
                                           │       Academic Manuscript & Report Generator          │
                                           │  • Formatted HTML / PDF Document                     │
                                           │  • arXiv / Overleaf LaTeX (.tex)                     │
                                           │  • Markdown (.md) with Citation Index                │
                                           └───────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Pipeline

The state machine coordinates each task through an explicit, bounded sequence of states (`app/orchestration/state.py`):

| Step | State | Description | Subsystem Involved |
| :--- | :--- | :--- | :--- |
| **01** | `CREATED` | Research project and initial question initialized | `app/api/routes.py`, `app/storage/models.py` |
| **02** | `RETRIEVING` | Concurrent multi-database literature search executed | `app/literature/providers.py` |
| **03** | `EXTRACTING` | Multi-section parsing and sentence-level evidence extraction | `app/evidence/extractor.py`, `app/literature/pdf_reader.py` |
| **04** | `HYPOTHESIZING` | Evidence-grounded hypothesis formulation & LLM synthesis | `app/hypotheses/generator.py` |
| **05** | `PLANNING_EXPERIMENT` | Hypothesis-tailored simulation planning and AST validation | `app/experiments/catalog.py`, `app/execution/ast_security.py` |
| **06** | `EXECUTING` | Isolated container execution inside zero-trust Docker sandbox | `app/execution/sandbox.py` |
| **07** | `ANALYZING` | Paired non-parametric statistical inference & effect size estimation | `app/statistics/service.py` |
| **08** | `CRITIQUING` | Epistemic referee evaluation and limitation auditing | `app/critique/service.py` |
| **09** | `COMPLETED` | Lineage persistence and multi-format academic manuscript synthesis | `app/reporting/manuscript_generator.py` |

---

## 🔬 Core Subsystems Deep-Dive

### 1. Multi-Source Autonomous Literature Mining
*File:* [`app/literature/providers.py`](file:///d:/Ai_research/app/literature/providers.py)

Queries scientific repositories concurrently using thread-pool workers, extracts clean keywords, handles API pagination, and deduplicates titles:
- **PubMed / NCBI E-Utilities:** Directly queries NIH PubMed for biomedical, clinical, pharmacokinetic, and nanomedicine research.
- **OpenAlex Catalog:** Queries 250M+ open scientific works with DOI resolution, reconstructing inverted abstract indexes into full continuous text.
- **arXiv Preprint Server:** Queries physics, computer science, optimization, and machine learning research via the Atom feed API.
- **Live Scientific Web & Wikipedia:** Retrieves encyclopedic overviews and summaries for broader interdisciplinary context.

```python
from app.literature.providers import MultiSourceResearchProvider
from app.core.config import Settings

provider = MultiSourceResearchProvider(Settings())
result = provider.search("nanoparticle targeted drug delivery oncology")
for paper in result.papers:
    print(f"[{paper.source_provider}] {paper.title} ({paper.external_id})")
```

### 2. Open-Access Full-Text PDF & Section Extraction
*File:* [`app/literature/pdf_reader.py`](file:///d:/Ai_research/app/literature/pdf_reader.py)

Parses open-access scientific articles and structures content into typed sections:
- **`ABSTRACT`**: Executive summary and background.
- **`METHODOLOGY`**: Experimental design, assay protocols, microfluidic ratios, and hyperparameters.
- **`RESULTS_TABLE`**: Tabular empirical benchmarks and baseline vs. treatment deltas.
- **`FIGURE_CAPTION`**: Empirical trajectories, error bars, and kinetic profiles.
- **`DISCUSSION`**: Boundary constraints, failure modes, and scientific limitations.

### 3. Semantic Vector Store & Dense Subword Indexing
*File:* [`app/literature/vector_store.py`](file:///d:/Ai_research/app/literature/vector_store.py)

An in-memory dense semantic vector index with cosine similarity search and multi-attribute metadata filtering:
- **Dual Embedding Mode:** Uses local Ollama embeddings (`/api/embeddings`) when available, with a deterministic 64-dimensional multi-gram subword hashing algorithm as an offline fallback.
- **Multi-Attribute Metadata Filtering:**
  - Publication Year range (`year_min`, `year_max`)
  - Minimum citation count (`min_citations`)
  - Journal / Repository provider (`arXiv`, `PubMed`, `OpenAlex`, `Web`)
  - Specific section type (`METHODOLOGY`, `RESULTS_TABLE`, `FIGURE_CAPTION`, `ABSTRACT`, `DISCUSSION`)

### 4. Sentence-Level Evidence Extraction Engine
*File:* [`app/evidence/extractor.py`](file:///d:/Ai_research/app/evidence/extractor.py)

Extracts verbatim sentence snippets from retrieved papers with verifiable locators (e.g., `abstract:sentence:1`, `pdf:section:methodology`, `pdf:table:1`). These immutable records form the factual basis for all downstream hypotheses, preventing hallucinations.

### 5. Evidence-Grounded Hypothesis Synthesis & Multi-Iteration Refinement
*File:* [`app/hypotheses/generator.py`](file:///d:/Ai_research/app/hypotheses/generator.py)

Proposes structured hypothesis candidates with complete causal mechanisms:
- **Structured Fields:** Statement, theoretical causal mechanism, scientific assumptions, testable empirical predictions, confidence score ($0.0 - 1.0$), novelty rating, testability score, and estimated compute/experimental cost.
- **Local Ollama Integration:** Communicates with Ollama (`llama3:latest`) via JSON schema enforcement.
- **Autonomous Multi-Iteration Refinement:** In iteration $N \ge 2$, the refiner consumes the measured difference $\Delta$, statistical power, $p$-value, confidence intervals, and referee audit points from iteration $N-1$ to calibrate assumptions, narrow parameter boundaries, and resolve referee objections.

### 6. AST Security Guardrails & Static Code Analyzer
*File:* [`app/execution/ast_security.py`](file:///d:/Ai_research/app/execution/ast_security.py)

Parses Python code into an Abstract Syntax Tree (`ast.parse`) before sandbox execution to enforce safety invariants:
- **Banned Modules:** `socket`, `requests`, `urllib`, `urllib3`, `http`, `httpx`, `aiohttp`, `websocket`, `subprocess`, `pty`, `multiprocessing`, `threading`, `ctypes`, `shutil`, `pickle`, `importlib`.
- **Banned Built-in Functions:** `eval()`, `exec()`, `compile()`, `__import__()`, `globals()`, `locals()`, `getattr()`, `setattr()`, `delattr()`.
- **Banned OS Operations:** `os.system()`, `os.popen()`, `os.remove()`, `os.unlink()`, `os.kill()`, `os.chmod()`, `os.execve()`, `os.spawn()`.
- **Banned Introspection:** `__subclasses__()`, `__builtins__`, `__globals__`.

### 7. Hypothesis-Tailored Simulation Script Generator
*File:* [`app/execution/code_generator.py`](file:///d:/Ai_research/app/execution/code_generator.py)

Dynamically generates self-contained Python simulation scripts matching the hypothesis's domain (nanomedicine diffusion kinetics, stochastic policy optimization, or empirical machine learning). The script reads Base64 JSON configurations via `RESEARCH_EXPERIMENT_CONFIG_B64`, runs paired baseline vs. treatment trials across configured random seeds, and outputs structured JSON metrics to stdout.

### 8. Isolated Docker Sandbox Execution Engine
*File:* [`app/execution/sandbox.py`](file:///d:/Ai_research/app/execution/sandbox.py)

Executes experiments inside unprivileged, ephemeral Docker containers:
```bash
docker run --rm \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --pids-limit 64 \
  --memory 512m \
  --cpus 1.0 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  --tmpfs /work:rw,noexec,nosuid,nodev,size=64m \
  --user 10001:10001 \
  --env RESEARCH_EXPERIMENT_CONFIG_B64=<payload> \
  ai-research-experiment:dev
```
- **Fallback Execution:** When Docker daemon is unavailable, falls back to a subprocess runner enforcing AST security.
- **Cryptographic Artifact Hashing:** Hashes all outputs with SHA-256 and records them in the database.

### 9. Non-Parametric Paired Statistical Inference
*File:* [`app/statistics/service.py`](file:///d:/Ai_research/app/statistics/service.py)

Computes statistical significance across paired trial scores without assuming normal distributions:
- **Standardized Effect Size ($d$):** Cohen's $d = \frac{\bar{\Delta}}{\sigma_{\Delta}}$
- **Non-Parametric Bootstrap Confidence Intervals:** $B = 2,000$ resamples to construct empirical 95% confidence intervals $[CI_{\text{lower}}, CI_{\text{upper}}]$.
- **Exact Paired Permutation Test:** $R = 10,000$ random sign flips under null hypothesis $H_0: \Delta = 0$ to compute exact empirical $p$-values.

### 10. Rule-Based Scientific Critic & Peer Referee
*File:* [`app/critique/service.py`](file:///d:/Ai_research/app/critique/service.py)

Acts as an automated scientific peer referee:
- **`REJECT`**: Triggered if mean effect size $\le 0$ or bootstrap 95% CI includes zero / negative improvement.
- **`NEEDS_REVISION`**: Triggered if sample count $N < 10$ or paired permutation $p \ge 0.05$.
- **`ACCEPT_WITH_LIMITATIONS`**: Granted only when all statistical criteria are met with positive effect bounds.
- Explicitly flags exploratory scopes so synthetic/toy simulations are never mischaracterized as general human discoveries.

### 11. Academic Manuscript & Publication Generator
*File:* [`app/reporting/manuscript_generator.py`](file:///d:/Ai_research/app/reporting/manuscript_generator.py)

Compiles project entities, literature citations, hypotheses, statistical metrics, referee findings, and provenance links into complete academic papers in three formats:
1. **Interactive HTML & Formatted Document:** Rendered article with typography, metric tables, callout blocks, and bibliography.
2. **LaTeX Manuscript (`.tex`):** Standard article format with mathematical equations, Booktabs tables, and BibTeX citations ready for arXiv or Overleaf submission.
3. **Markdown Report (`.md`):** Complete structured report with citation references.

### 12. Bidirectional Provenance DAG & Cryptographic Audit Trails
*Files:* [`app/storage/models.py`](file:///d:/Ai_research/app/storage/models.py), [`app/storage/database.py`](file:///d:/Ai_research/app/storage/database.py)

Every entity inherits from `AuditedEntity` (UUID, UTC timestamps, `schema_version`, JSON provenance). Relationships are recorded in `ProvenanceLink` (`MOTIVATED_BY`, `EXTRACTED_FROM`, `TESTS`, `MEASURED_BY`, `EVALUATES`, `REFINED_FROM`). Cascading project deletions cleanly remove all downstream DAG links, metrics, and artifacts.

---

## 🖥️ PySide6 Desktop Application

The platform includes a desktop GUI built with **PySide6 / Qt 6.8** featuring a dark theme (`gui/theme.py`) and non-blocking asynchronous worker threads.

To run the GUI:
```powershell
python run_gui.py
```

### Desktop UI Capabilities:
1. **Project Management:** Create new research questions, browse past projects, and perform cascading deletions with confirmation dialogs.
2. **8-Stage Workflow Pipeline Stepper (`StageTrackerWidget`):** Real-time status indicators across the 8 research stages.
3. **Semantic Vector Search & PDF Reader Tab (`LiteratureTab`):** Live vector queries across all indexed full-text sections with instant filters for Year, Citations, Journal, and Section Type.
4. **Hypothesis Evolution Tab (`HypothesisTab`):** Displays statements, mechanisms, assumptions, and predictions alongside the **Interactive Hypothesis Evolution Tree** (`EvolutionTreeWidget`).
5. **Sandboxed Experiments & Statistical Analysis Tab (`ExperimentTab`):**
   - Scientific Critic Evaluation banner and audit findings.
   - 4-Column KPI grid (Baseline, Treatment, Mean $\Delta$, Cohen's $d$).
   - **Bootstrap 95% CI Forest Plot Canvas** (`ForestCIChartCanvas`).
   - **Permutation Test Null Distribution Plot Canvas** (`PermutationChartCanvas`).
   - AST-Verified Python code inspector.
6. **Audit Lineage & Interactive DAG Tab (`ProvenanceTab`):**
   - **Directed Acyclic Graph Canvas** (`ProvenanceDAGCanvas`) rendered via NetworkX and Matplotlib.
   - Interactive Lineage Table and live JSON Provenance Inspector.
7. **Publication-Ready Academic Manuscript Modal (`ManuscriptModal`):** View rendered articles, edit LaTeX / Markdown sources, and export directly to `.pdf`, `.tex`, or `.md` files.

---

## 🌐 REST API Reference

The FastAPI backend exposes endpoints under the `/api/v1` prefix:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/healthz` | System health check |
| `POST` | `/api/v1/projects` | Create a new research project with a research question |
| `GET` | `/api/v1/projects` | List all research projects ordered by creation date |
| `GET` | `/api/v1/projects/{project_id}` | Get project details and status |
| `DELETE` | `/api/v1/projects/{project_id}` | Cascading deletion of project and all associated records |
| `POST` | `/api/v1/projects/{project_id}/research` | Start autonomous discovery loop (`wait=true` or background task, `iterations=1..5`) |
| `GET` | `/api/v1/projects/{project_id}/status` | Get current execution stage, error codes, and trace ID |
| `GET` | `/api/v1/projects/{project_id}/hypotheses` | List all hypotheses formulated for this project |
| `GET` | `/api/v1/projects/{project_id}/evolution` | Get multi-iteration hypothesis evolution tree with critique resolutions |
| `GET` | `/api/v1/projects/{project_id}/manuscript` | Generate academic manuscript (`format=markdown\|latex\|html\|all`) |
| `GET` | `/api/v1/papers?project_id={id}` | List papers retrieved for a project |
| `GET` | `/api/v1/papers/{paper_id}` | Get paper metadata, abstract, and extracted evidence |
| `GET` | `/api/v1/papers/{paper_id}/sections` | Get full-text structured sections (Methodology, Tables, Captions) |
| `GET` | `/api/v1/literature/search/semantic` | Semantic vector search with filters (`year_min`, `min_citations`, `journal`, `section_type`) |
| `POST` | `/api/v1/experiments` | Register a new experiment specification for a hypothesis |
| `GET` | `/api/v1/experiments/{experiment_id}` | Retrieve experiment specification |
| `POST` | `/api/v1/experiments/{experiment_id}/run` | Execute experiment inside the sandbox runner |
| `GET` | `/api/v1/experiments/{experiment_id}/results` | Retrieve metrics, statistical analysis, and critique verdict |
| `GET` | `/api/v1/knowledge?project_id={id}` | Get provenance DAG nodes and edges for graph visualization |
| `GET` | `/api/v1/provenance/{record_id}` | Retrieve cryptographic provenance payload and parent relationships |

---

## 🗄️ Database Schema & Data Model

Every persisted entity extends `AuditedEntity` (`id`, `created_at`, `updated_at`, `schema_version`, `provenance`):

```
┌──────────────────┐       1:N       ┌──────────────────┐       1:N       ┌──────────────────┐
│ ResearchProject  ├────────────────►│   ResearchTask   │                 │      Source      │
└────────┬─────────┘                 └──────────────────┘                 └────────┬─────────┘
         │ 1:1                                                                     │ 1:N
         ▼                                                                         ▼
┌──────────────────┐                                                      ┌──────────────────┐
│ ResearchQuestion │                                                      │      Paper       │
└──────────────────┘                                                      └────────┬─────────┘
         │                                                                         │ 1:N
         │                                                                         ▼
         │                 1:N       ┌──────────────────┐       1:N       ┌──────────────────┐
         ├──────────────────────────►│    Hypothesis    │◄────────────────┤     Evidence     │
         │                           └────────┬─────────┘                 └──────────────────┘
         │                                    │ 1:N
         ▼                                    ▼
┌──────────────────┐       1:N       ┌──────────────────┐
│  ProvenanceLink  │                 │    Experiment    │
└──────────────────┘                 └────────┬─────────┘
                                              │ 1:N
                                              ▼
┌──────────────────┐       1:N       ┌──────────────────┐       1:1       ┌──────────────────┐
│     Artifact     │◄────────────────┤  ExperimentRun   ├────────────────►│      Result      │
└──────────────────┘                 └────────┬─────────┘                 └────────┬─────────┘
                                              │ 1:N                                │ 1:1
                                              ▼                                    ▼
                                     ┌──────────────────┐                 ┌──────────────────┐
                                     │      Metric      │                 │     Critique     │
                                     └──────────────────┘                 └──────────────────┘
```

---

## 🛡️ Security Model & Sandbox Invariants

The platform implements defense-in-depth for AI-generated code execution:

1. **AST Pre-Execution Verification:** Scripts are parsed and checked against a strict denylist of modules, builtins, and OS calls before touching disk.
2. **Container Security Flags:**
   - `--network none`: Complete physical network isolation.
   - `--read-only`: Immutable root filesystem.
   - `--cap-drop ALL`: All Linux capabilities dropped.
   - `--security-opt no-new-privileges:true`: Prevents privilege escalation.
   - `--user 10001:10001`: Runs as unprivileged non-root user.
   - `--tmpfs /tmp:size=64m,noexec,nosuid,nodev`: Non-executable in-memory scratch space.
3. **Resource Quotas:** Memory capped at `512MB`, CPU capped at `1.0`, execution hard timeout at `45s`.
4. **Cryptographic Checksums:** Generated scripts and execution outputs are fingerprinted with SHA-256.

---

## 📦 Installation & Getting Started

### Prerequisites
- **Python 3.12+**
- **Docker Engine & Docker Compose** (for sandboxed execution)
- *(Optional)* **Ollama** with `llama3:latest` for local LLM generation

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/autonomous-ai-research-scientist.git
   cd autonomous-ai-research-scientist
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

4. **Initialize environment configuration:**
   ```powershell
   copy .env.example .env
   ```

5. **Run database migrations:**
   ```powershell
   alembic upgrade head
   ```

---

## 🚀 Running the Platform

### Option A: Desktop GUI Mode (Recommended)
Run the standalone PySide6 desktop GUI with local SQLite storage:
```powershell
python run_gui.py
```

### Option B: FastAPI Backend Server
Launch the REST API server with Uvicorn:
```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Option C: Docker Compose Full Stack
Build and launch PostgreSQL, the API server, and the experiment sandbox image:
```bash
# Build the experiment sandbox image
docker compose build experiment-sandbox

# Start Database and API Server
docker compose up -d
```

### Option D: Local Ollama LLM Acceleration (Optional)
To enable local LLM-powered hypothesis formulation:
```bash
ollama run llama3:latest
```
The platform automatically detects Ollama at `http://127.0.0.1:11434` and falls back to deterministic synthesis if unreachable.

---

## 🧪 Testing Suite

The repository includes a comprehensive test suite across unit, integration, security, and evaluation tests.

Run the entire test suite:
```powershell
python -m pytest -v
```

### Test Suite Breakdown:

```powershell
# Run Unit Tests only
python -m pytest tests/unit -v

# Run AST Security and Policy Tests
python -m pytest tests/security -v

# Run Workflow Integration Tests
python -m pytest tests/integration -v

# Run with Real Docker Sandbox (requires Docker daemon)
python -m pytest -m docker -v
```

---

## ⚙️ Configuration Reference

All settings can be customized via `.env` or environment variables:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | `str` | `sqlite:///./research.db` | Database connection string (PostgreSQL or SQLite) |
| `ARXIV_BASE_URL` | `HttpUrl` | `https://export.arxiv.org/api/query` | arXiv API endpoint |
| `ARXIV_MAX_RESULTS` | `int` | `8` | Maximum papers retrieved per arXiv search |
| `SANDBOX_IMAGE` | `str` | `ai-research-experiment:dev` | Docker image for experiment sandbox |
| `SANDBOX_VOLUME` | `str` | `research_artifacts` | Docker volume for artifact storage |
| `SANDBOX_TIMEOUT_SECONDS` | `int` | `45` | Hard timeout for sandbox execution |
| `SANDBOX_MEMORY_LIMIT` | `str` | `512m` | Docker container memory quota |
| `SANDBOX_CPU_LIMIT` | `float` | `1.0` | Docker container CPU quota |
| `RESEARCH_MAX_ITERATIONS`| `int` | `1` | Default multi-iteration discovery loop depth |
| `OLLAMA_BASE_URL` | `str` | `http://127.0.0.1:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `str` | `llama3:latest` | Ollama model identifier |
| `LOG_LEVEL` | `str` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## 📂 Project Directory Structure

```
Ai_research/
├── app/                                 # Core Application Backend
│   ├── api/                             # FastAPI Routes & Dependencies
│   │   ├── dependencies.py              # Dependency Injection Container
│   │   └── routes.py                    # RESTful Endpoints
│   ├── core/                            # Configuration & Exceptions
│   │   ├── config.py                    # Pydantic Settings
│   │   └── errors.py                    # ResearchWorkflowError & Codes
│   ├── critique/                        # Scientific Critic & Referee
│   │   └── service.py                   # Rule-Based Critic Engine
│   ├── evidence/                        # Evidence Grounding Engine
│   │   └── extractor.py                 # Sentence-Level Evidence Extractor
│   ├── execution/                       # Sandboxed Execution & Security
│   │   ├── ast_security.py              # AST Static Analysis Validator
│   │   ├── code_generator.py            # Dynamic Simulation Generator
│   │   └── sandbox.py                   # Docker Sandbox Runner
│   ├── experiments/                     # Experiment Template Catalog
│   │   └── catalog.py                   # Registered Experiment Templates
│   ├── hypotheses/                      # Hypothesis Generation Subsystem
│   │   └── generator.py                 # Ollama & Evidence Generator / Refiner
│   ├── literature/                      # Multi-Source Literature Mining
│   │   ├── pdf_reader.py                # Open-Access PDF & Section Parser
│   │   ├── providers.py                 # PubMed, OpenAlex, arXiv, Web Adapters
│   │   └── vector_store.py              # Dense Semantic Vector Index
│   ├── orchestration/                   # Autonomous Workflow Coordinator
│   │   ├── research_orchestrator.py     # End-to-End Orchestrator Loop
│   │   └── state.py                     # 8-Stage Finite State Machine
│   ├── reporting/                       # Manuscript Synthesis Subsystem
│   │   └── manuscript_generator.py      # PDF, LaTeX (.tex), Markdown (.md)
│   ├── schemas/                         # API & Domain Data Models
│   │   ├── api.py                       # Strict Request/Response Pydantic Models
│   │   └── domain.py                    # Domain Record Envelopes
│   ├── statistics/                      # Paired Statistical Inference
│   │   └── service.py                   # Bootstrap CIs & Permutation Tests
│   ├── storage/                         # Database Persistence Layer
│   │   ├── database.py                  # Engine, Session & Cascading Helpers
│   │   └── models.py                    # SQLAlchemy Audited Entities
│   └── main.py                          # FastAPI Application Factory
├── docker/                              # Container Definitions
│   ├── api/Dockerfile                   # API Server Production Image
│   └── experiment/Dockerfile            # Unprivileged Sandbox Image
├── docs/                                # Documentation & Specifications
├── experiments/                         # Simulation Source Templates
│   └── toy_ml/experiment.py             # Baseline / Treatment Simulation
├── gui/                                 # PySide6 Desktop GUI Application
│   ├── api_client.py                    # Async API Client & QThread Workers
│   ├── main_window.py                   # Main Window & Project Dialogs
│   ├── theme.py                         # Dark Theme Stylesheet & Status Tokens
│   └── widgets/                         # Reusable GUI Tabs & Charts
│       ├── charts/                      # Interactive Visualizations
│       │   ├── evolution_tree.py        # Hypothesis Evolution Tree
│       │   ├── forest_chart.py          # Bootstrap 95% CI Forest Plot
│       │   ├── permutation_chart.py     # Permutation Null Distribution Plot
│       │   └── provenance_graph.py      # Lineage DAG Network Graph
│       ├── experiment_tab.py            # Experiments & Statistics View
│       ├── hypothesis_tab.py            # Hypotheses & Evolution Inspector
│       ├── literature_tab.py            # Semantic Search & PDF Reader
│       ├── manuscript_modal.py          # Academic Manuscript Exporter
│       ├── provenance_tab.py            # Provenance DAG Explorer
│       └── stage_tracker.py             # Horizontal Pipeline Stepper
├── migrations/                          # Alembic Database Migrations
│   ├── env.py                           # Migration Environment
│   └── versions/                        # Migration Revisions
├── tests/                               # Comprehensive Test Suite
│   ├── conftest.py                      # Fixtures & Deterministic Doubles
│   ├── evaluation/                      # Grounding Evaluation Tests
│   ├── integration/                     # Workflow & Docker Integration Tests
│   ├── security/                        # AST & Sandbox Policy Tests
│   └── unit/                            # Unit Tests for Subsystems
├── alembic.ini                          # Alembic Configuration
├── docker-compose.yml                   # Multi-Container Deployment Spec
├── pyproject.toml                       # Python Packaging & Dependencies
├── README.md                            # Complete System Documentation
└── run_gui.py                           # PySide6 Desktop App Launcher
```

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

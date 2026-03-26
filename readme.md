<div align="center">

# Olympia Academia

Privacy-first RAG system for building a personal/organizational knowledge base from WhatsApp and web content.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00ADD8?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-AI_Enrichment-FF6B6B?style=for-the-badge)](https://deepseek.com)

</div>

---

## Overview

Olympia Academia is an end‑to‑end Retrieval‑Augmented Generation (RAG) system that turns WhatsApp‑shared links into a local, searchable knowledge base with an AI assistant on top.

It:

- Extracts links from WhatsApp chat exports
- Validates and scrapes YouTube and web content
- Enriches content using DeepSeek (via Ollama)
- Builds hybrid FAISS + BM25 indices
- Serves an interactive Streamlit chat UI with source‑grounded answers

All data and indices are stored locally to preserve privacy.

### Core Components

| Component   | Path              | Purpose                                |
|------------|-------------------|----------------------------------------|
| `app.py`   | root              | Streamlit chat interface (entrypoint) |
| Ingestion  | `src/ingestion/`  | WhatsApp link extraction & scraping   |
| Processing | `src/processing/` | AI enrichment & classification        |
| Database   | `src/database/`   | Index building (FAISS, BM25)          |
| Engine     | `src/engine/`     | Hybrid retrieval & ranking            |
| Utils      | `src/utils/`      | Config, evaluation, rate limiting     |

---

## Features

- WhatsApp link ingestion (TXT exports)
- URL validation and deduplication
- YouTube transcript and web article scraping
- AI enrichment (titles, topics, categories, summaries, keywords)
- Hybrid search (semantic + keyword, FAISS + BM25)
- Streamlit chat app with:
  - Multi‑turn conversations
  - Smart query routing
  - Source cards and relevance scores
  - Fact‑checking against retrieved context
  - Follow‑up suggestions
  - Database statistics and controls (clear cache, clear memory)
- Per‑user rate limiting and usage tracking

---

## Architecture

High‑level data and query flow:

```text
WhatsApp Export
   └─> Ingestion: link_extractor.py, cleaner.py
         └─> universal_ingestor.py (YouTube + Web scraping)
              └─> processing.batch_processor (AI enrichment via DeepSeek/Ollama)
                   └─> database.build_db (FAISS + BM25 indices)
                        └─> engine.rag_engine (Hybrid search)
                             └─> app.py (Streamlit chat interface)
```

Hybrid search:

- Semantic search on FAISS embeddings (Sentence Transformers)
- Keyword search on BM25
- Weighted fusion (configurable; default 40% semantic / 60% keyword)

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- Ability to run/use Ollama with a DeepSeek model (or compatible API)
- WhatsApp chat export(s) in `.txt` format (optional but recommended)

### 2. Install

```bash
git clone https://github.com/<your-username>/olympia-academia.git
cd olympia-academia

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required
OLLAMA_API_KEY=your_api_key_here

# Optional (with defaults)
OLLAMA_HOST=https://ollama.com
OLLAMA_MODEL=deepseek-v3.1:671b-cloud

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
BATCH_SIZE=10
MAX_WORKERS=5
TOP_K_RESULTS=5
DAILY_USER_QUOTA=100
```

### 4. Build the Knowledge Base

If you have WhatsApp data and want to build your own KB end‑to‑end:

```bash
# 1) Extract links from WhatsApp exports (in data/raw/)
python -m src.ingestion.link_extractor

# 2) Validate and clean URLs
python -m src.ingestion.cleaner

# 3) Scrape content (YouTube + web)
python -m src.ingestion.universal_ingestor batch

# 4) AI enrichment (titles, categories, summaries, topics)
python -m src.processing.batch_processor

# 5) Build FAISS + BM25 indices
python -m src.database.build_db
```

### 5. Run the App

```bash
streamlit run app.py
# Optional:
# streamlit run app.py --server.port 8080
```

Open the displayed URL (default `http://localhost:8501`) in your browser.

---

## Usage

### Streamlit Chat Interface (`app.py`)

The main entry point is:

```bash
streamlit run app.py
```

You get:

- A sidebar with:
  - Database stats (documents, cache hit rate)
  - Guardrail/strictness options
  - Buttons to clear conversation memory and cache
- A main chat area with:
  - Hero section and KB selection (if you manage multiple datasets)
  - User/assistant messages
  - Verification indicators (grounded vs. ungrounded claims)
  - Expandable source cards (top‑K retrieved documents)
  - Suggested follow‑up questions

Internally, `app.py`:

- Routes queries (decides when to hit the DB vs. reuse context)
- Expands user queries into multiple search candidates
- Calls `HybridSearchEngine` to retrieve top‑K results
- Builds a structured prompt with retrieved context
- Generates an answer and a critique pass for fact‑checking
- Streams the answer and displays supporting sources

---

## Data Pipeline

Each stage can be run independently or end‑to‑end.

1. Extraction (WhatsApp → link list)

   ```bash
   python -m src.ingestion.link_extractor
   # Output: data/processed/whatsapp_links_unique.xlsx
   ```

2. Validation (filter dead/bad URLs)

   ```bash
   python -m src.ingestion.cleaner
   # Output: data/processed/oa_cleaned.xlsx
   ```

3. Ingestion (scraping)

   ```bash
   python -m src.ingestion.universal_ingestor batch
   # Output: data/processed/scraped_content.xlsx (naming may vary)
   ```

4. Enrichment (AI metadata and summaries)

   ```bash
   python -m src.processing.batch_processor
   # Output: data/processed/oa_enriched.xlsx
   ```

5. Indexing (search indices)

   ```bash
   python -m src.database.build_db
   # Output: data/db/olympia_vectors.index, olympia_bm25.pkl, olympia_docs.pkl
   ```

6. Serving (search + chat)

   ```bash
   streamlit run app.py
   ```

For a programmatic “all‑in‑one” run:

```python
from src.ingestion import run_full_pipeline
from src.database.build_db import DatabaseBuilder

results = run_full_pipeline(max_workers=10)
print(f"Ingested {results['total_ingested']} items")

DatabaseBuilder().build_all()
```

---

## Programmatic API (Core Pieces)

### Hybrid Search Engine

```python
from src.engine.rag_engine import HybridSearchEngine

engine = HybridSearchEngine()

# Basic search
results = engine.search("quantum mechanics", top_k=5)

# Filter by resource type
results = engine.search(
    query="python tutorial",
    top_k=3,
    type_filter="Video Resource",
)

# Stats
stats = engine.get_stats()
print(stats["total_documents"], stats["cache_hit_rate"])
```

Each result is a dict (or `SearchResult` dataclass in code) containing:

```python
{
    "id": int,
    "score": float,
    "title": str,
    "link": str,
    "type": str,
    "category": str,
    "topic": str,
    "summary": str,
    "insights": str,
    "context": str,
}
```

### Universal Ingestor

```python
from src.ingestion import UniversalIngestor

ingestor = UniversalIngestor(enrich=True)

# Single URL
content = ingestor.ingest("https://youtube.com/watch?v=...")

# Batch
urls = ["https://...", "https://..."]
for item in ingestor.ingest_batch(urls, max_workers=5):
    print(item.title, item.success)
```

---

## Project Structure

```text
olympia-academia/
├── app.py                      # Streamlit chat interface
├── requirements.txt
├── .env.example
├── README.md

├── data/
│   ├── raw/                    # WhatsApp exports, etc.
│   ├── processed/              # Cleaned, enriched spreadsheets
│   ├── db/                     # Indices and user limits
│   │   ├── olympia_vectors.index
│   │   ├── olympia_bm25.pkl
│   │   ├── olympia_docs.pkl
│   │   └── user_limits.db
│   └── backups/

└── src/
    ├── ingestion/
    │   ├── link_extractor.py
    │   ├── cleaner.py
    │   └── universal_ingestor.py
    │
    ├── processing/
    │   └── batch_processor.py
    │
    ├── database/
    │   └── build_db.py
    │
    ├── engine/
    │   └── rag_engine.py
    │
    └── utils/
        ├── config.py
        ├── evaluate_system.py
        └── limit_checker.py
```

---

## Configuration Reference

Key environment variables (in `.env`):

| Variable                 | Required | Default                                   | Description                          |
|--------------------------|----------|-------------------------------------------|--------------------------------------|
| `OLLAMA_API_KEY`        | Yes      | –                                         | Ollama API key                       |
| `OLLAMA_HOST`           | No       | `https://ollama.com`                      | Ollama API host                      |
| `OLLAMA_MODEL`          | No       | `deepseek-v3.1:671b-cloud`                | LLM for enrichment and responses     |
| `EMBEDDING_MODEL`       | No       | `sentence-transformers/all-MiniLM-L6-v2`  | Embedding model                      |
| `BATCH_SIZE`            | No       | `10`                                      | Records per enrichment batch         |
| `MAX_WORKERS`           | No       | `5`                                       | Concurrent scraping/enrichment jobs  |
| `TOP_K_RESULTS`         | No       | `5`                                       | Default number of search results     |
| `HYBRID_ALPHA`          | No       | `0.7`                                     | Semantic weighting factor            |
| `DAILY_USER_QUOTA`      | No       | `100`                                     | Max queries per user per day         |
| `MAX_REQUESTS_PER_MINUTE` | No     | `30`                                      | Global request throttling            |

---

## Troubleshooting (Common Issues)

- **FAISS index not found**

  Build the database:

  ```bash
  python -m src.database.build_db
  ```

- **API key missing**

  Ensure `.env` exists and `OLLAMA_API_KEY` is set:

  ```bash
  cp .env.example .env
  # then edit .env
  ```

- **Ollama connection failed**

  - Start Ollama: `ollama serve`
  - Check `OLLAMA_HOST` in `.env`
  - Confirm model is available: `ollama list`

- **No links extracted from WhatsApp**

  - Export chat as `.txt` (text only) from WhatsApp
  - Ensure file is UTF‑8 encoded
  - Place exports under `data/raw/` or adjust paths in `link_extractor.py`

- **Rate limit reached**

  - Wait until the next day (quota reset)
  - Or increase `DAILY_USER_QUOTA` in `.env`
  - Or delete `data/db/user_limits.db` to reset counts

For more detailed evaluation, run:

```bash
python -m src.utils.evaluate_system
```

---

## Contributing

Contributions are welcome. Typical workflow:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes with tests and doc updates
4. Run linting/tests where available
5. Open a Pull Request with a clear description

---

<div align="center">

Made by the Olympia Academia team.

</div>
```

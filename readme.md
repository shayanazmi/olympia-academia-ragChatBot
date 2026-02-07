Here's the updated `src/README.md` that now includes the `app.py` documentation:

## Updated `src/README.md`

```markdown
<div align="center">

# 🏛️ Olympia Academia

### Source Code Documentation

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00ADD8?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-AI_Enrichment-FF6B6B?style=for-the-badge)](https://deepseek.com)

**Privacy-First RAG System for WhatsApp Knowledge Bases**

[Architecture](#-architecture) •
[App Interface](#-app-interface) •
[Modules](#-modules) •
[Pipeline](#-data-pipeline) •
[Quick Start](#-quick-start) •
[API Reference](#-api-reference)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [App Interface (app.py)](#-app-interface-apppy)
- [Modules](#-modules)
  - [Ingestion](#1-ingestion-srcingestion)
  - [Processing](#2-processing-srcprocessing)
  - [Database](#3-database-srcdatabase)
  - [Engine](#4-engine-srcengine)
  - [Utils](#5-utils-srcutils)
- [Data Pipeline](#-data-pipeline)
- [Quick Start](#-quick-start)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [File Structure](#-file-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

Olympia Academia is a complete RAG (Retrieval-Augmented Generation) system with the following components:

| Component | Location | Purpose |
|-----------|----------|---------|
| **app.py** | Root | Streamlit chat interface (main entry point) |
| **ingestion** | `src/ingestion/` | Data collection & scraping |
| **processing** | `src/processing/` | AI enrichment & classification |
| **database** | `src/database/` | Index building |
| **engine** | `src/engine/` | Hybrid search & retrieval |
| **utils** | `src/utils/` | Configuration & helpers |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OLYMPIA ACADEMIA                                   │
│                         Complete Architecture                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        INGESTION LAYER                               │   │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐  │   │
│  │  │   WhatsApp  │───▶│    Link     │───▶│      Link Cleaner       │  │   │
│  │  │   Export    │    │  Extractor  │    │   (URL Validation)      │  │   │
│  │  └─────────────┘    └─────────────┘    └───────────┬─────────────┘  │   │
│  │                                                     │                │   │
│  │                                        ┌────────────▼────────────┐  │   │
│  │                                        │   Universal Ingestor   │  │   │
│  │                                        │  ┌─────┐    ┌───────┐  │  │   │
│  │                                        │  │ YT  │    │  Web  │  │  │   │
│  │                                        │  └─────┘    └───────┘  │  │   │
│  │                                        └────────────┬────────────┘  │   │
│  └─────────────────────────────────────────────────────┼───────────────┘   │
│                                                        │                    │
│  ┌─────────────────────────────────────────────────────▼───────────────┐   │
│  │                       PROCESSING LAYER                               │   │
│  │  ┌───────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Batch Processor                             │  │   │
│  │  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │  │   │
│  │  │  │   Scraped   │───▶│  DeepSeek   │───▶│    Enriched     │   │  │   │
│  │  │  │   Content   │    │  via Ollama │    │    Metadata     │   │  │   │
│  │  │  └─────────────┘    └─────────────┘    └─────────────────┘   │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┬───────────────┘   │
│                                                        │                    │
│  ┌─────────────────────────────────────────────────────▼───────────────┐   │
│  │                       DATABASE LAYER                                 │   │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐  │   │
│  │  │  Sentence       │    │                 │    │                 │  │   │
│  │  │  Transformer    │───▶│   FAISS Index   │    │   BM25 Index    │  │   │
│  │  │  (Embeddings)   │    │   (Semantic)    │    │   (Keyword)     │  │   │
│  │  └─────────────────┘    └────────┬────────┘    └────────┬────────┘  │   │
│  └──────────────────────────────────┼──────────────────────┼───────────┘   │
│                                     │                      │                │
│  ┌──────────────────────────────────┼──────────────────────┼───────────┐   │
│  │                       ENGINE LAYER                      │           │   │
│  │                      ┌──────────┴──────────────────────┴─────┐     │   │
│  │                      │         Hybrid Search Engine          │     │   │
│  │                      │  ┌─────────────┐   ┌──────────────┐  │     │   │
│  │                      │  │  Semantic   │ + │   Keyword    │  │     │   │
│  │                      │  │   Search    │   │   Search     │  │     │   │
│  │                      │  │   (40%)     │   │    (60%)     │  │     │   │
│  │                      │  └─────────────┘   └──────────────┘  │     │   │
│  │                      └──────────────────────────────────────┘     │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│                                          │                                  │
│  ┌───────────────────────────────────────▼──────────────────────────────┐  │
│  │                       PRESENTATION LAYER                              │  │
│  │  ┌────────────────────────────────────────────────────────────────┐  │  │
│  │  │                        app.py                                   │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │  │
│  │  │  │   Streamlit  │  │    Chat      │  │   Source Display     │ │  │  │
│  │  │  │   Interface  │  │   History    │  │   & Verification     │ │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │  │
│  │  │                                                                 │  │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │  │  │
│  │  │  │    Query     │  │   Response   │  │    Follow-up         │ │  │  │
│  │  │  │   Routing    │  │  Streaming   │  │   Suggestions        │ │  │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────────┘ │  │  │
│  │  └────────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ App Interface (`app.py`)

The main entry point for users - a Streamlit-based chat interface.

### Location

```
olympia-academia/
├── 📄 app.py              # ← Main Streamlit Application
└── 📁 src/
    └── ...
```

### Features

| Feature | Description |
|---------|-------------|
| 🎨 **Dark Academic Theme** | Custom CSS for professional look |
| 💬 **Multi-turn Chat** | Context-aware conversations |
| 🔍 **Smart Query Routing** | Determines when to search vs. use memory |
| 📚 **Source Cards** | Displays retrieved documents with metadata |
| ✅ **Fact Verification** | AI-powered response grounding check |
| 💡 **Follow-up Suggestions** | Auto-generated relevant questions |
| 📊 **Database Stats** | Real-time index statistics in sidebar |
| 🔄 **Regenerate Answers** | Re-run generation without new search |
| ⚡ **Rate Limiting** | User quota management |

### User Interface Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ┌─────────────┐  ┌──────────────────────────────────────────────────┐ │
│  │             │  │                                                  │ │
│  │   SIDEBAR   │  │              MAIN CHAT AREA                      │ │
│  │             │  │                                                  │ │
│  │  🏛️ Olympia │  │  ┌────────────────────────────────────────────┐ │ │
│  │  v2.5       │  │  │              HERO SECTION                   │ │ │
│  │             │  │  │     🏛️ Olympia Academia                     │ │ │
│  │  ───────    │  │  │     Your Research Assistant                 │ │ │
│  │             │  │  │                                             │ │ │
│  │  Database:  │  │  │   [Bird Nav] [Grothendieck] [Lean]         │ │ │
│  │  ● Active   │  │  └────────────────────────────────────────────┘ │ │
│  │             │  │                                                  │ │
│  │  Guardrails:│  │  ┌────────────────────────────────────────────┐ │ │
│  │  ● Strict   │  │  │ 👤 User: How do birds navigate?            │ │ │
│  │             │  │  └────────────────────────────────────────────┘ │ │
│  │  ───────    │  │                                                  │ │
│  │             │  │  ┌────────────────────────────────────────────┐ │ │
│  │  📊 Stats:  │  │  │ 🏛️ Olympia: Birds use quantum mechanics... │ │ │
│  │  • Docs: 500│  │  │                                             │ │ │
│  │  • Cache: 85%│ │  │ ✅ Verified: Grounded in Database          │ │ │
│  │             │  │  └────────────────────────────────────────────┘ │ │
│  │  ───────    │  │                                                  │ │
│  │             │  │  📚 View 5 Retrieved Sources ▼                  │ │
│  │  [Clear     │  │                                                  │ │
│  │   Memory]   │  │  💡 Follow-up questions:                        │ │
│  │             │  │  [Question 1] [Question 2] [Question 3]         │ │
│  │  [Clear     │  │                                                  │ │
│  │   Cache]    │  │  ────────────────────────────────────────────── │ │
│  │             │  │                                                  │ │
│  └─────────────┘  │  [Ask a research question...               🔍] │ │
│                   └──────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. Query Routing

```python
def refine_query(client, user_input, history):
    """
    Smart routing to determine if new search is needed.
    
    Returns:
        needs_search (bool): Whether to query the database
        queries (list): Expanded search queries for better coverage
    """
```

- Analyzes conversation history
- Determines if follow-up or new topic
- Generates 3 varied search queries for better retrieval

#### 2. Source Card Display

```python
def format_source_card(result):
    """Format search result as styled HTML card."""
```

Displays:
- 📄 Title with link
- 📊 Relevance score
- 🏷️ Resource type
- 📝 Summary excerpt

#### 3. Response Generation

```python
def get_system_instruction(context_str, prompt):
    """Generate structured prompt for AI response."""
```

Output format:
- **Direct Answer** - Synthesized response
- **Primary Resource** - Best matching source
- **Related Papers/Articles** - Non-video resources
- **Related Videos** - Video resources
- **Related Channels** - YouTube channels
- **Related Topics** - Prerequisite concepts

#### 4. Fact Verification

```python
# Post-generation critique loop
if "RETRIEVED RESOURCES" in context_str:
    critique_prompt = "Does answer contain claims NOT in context?"
    # Shows ✅ Verified or ⚠️ Warning
```

### Running the App

```bash
# Standard launch
streamlit run app.py

# With custom port
streamlit run app.py --server.port 8080

# With auto-reload disabled
streamlit run app.py --server.runOnSave false
```

### Environment Requirements

```env
# Required in .env file
OLLAMA_API_KEY=your_api_key_here
OLLAMA_HOST=https://ollama.com
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
```

### Session State

| Key | Type | Purpose |
|-----|------|---------|
| `messages` | `list` | Chat history |
| `last_context` | `str` | Last retrieved context for follow-ups |
| `user_id` | `str` | Unique user identifier for rate limiting |

### Customization

#### Changing the Theme

Edit the CSS in `app.py`:

```python
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;  /* Change background */
    }
    .source-card {
        border-left: 4px solid #4CAF50;  /* Change accent color */
    }
</style>
""", unsafe_allow_html=True)
```

#### Adding Quick Query Buttons

```python
if st.button("🧬 DNA Structure", use_container_width=True):
    st.session_state.messages.append({
        "role": "user", 
        "content": "Explain DNA double helix structure"
    })
    st.rerun()
```

#### Modifying Response Format

Edit `get_system_instruction()` to change the AI output structure.

---

## 📦 Modules

### 1. Ingestion (`src/ingestion/`)

The data collection layer responsible for extracting and preparing raw content.

#### Files

| File | Class/Function | Description |
|------|----------------|-------------|
| `link_extractor.py` | `WhatsAppLinkExtractor` | Parses WhatsApp chat exports to extract URLs |
| `cleaner.py` | `LinkCleaner` | Validates URLs and removes dead links |
| `universal_ingestor.py` | `UniversalIngestor` | Scrapes content from YouTube and web sources |
| `__init__.py` | `IngestionPipeline` | High-level pipeline orchestration |

#### Usage

```python
from src.ingestion import LinkExtractor, LinkCleaner, UniversalIngestor

# Step 1: Extract links from WhatsApp
extractor = LinkExtractor()
extractor.process_all()
extractor.deduplicate()
extractor.save()

# Step 2: Validate links
cleaner = LinkCleaner()
cleaner.run()

# Step 3: Ingest content
ingestor = UniversalIngestor(enrich=True)
result = ingestor.ingest("https://youtube.com/watch?v=...")
```

#### Pipeline Shortcut

```python
from src.ingestion import run_full_pipeline

# Run everything in one command
results = run_full_pipeline(max_workers=10)
print(f"Ingested {results['total_ingested']} items")
```

---

### 2. Processing (`src/processing/`)

AI-powered enrichment using DeepSeek via Ollama.

#### Files

| File | Class/Function | Description |
|------|----------------|-------------|
| `batch_processor.py` | `run_batch_enrichment()` | Batch AI analysis of scraped content |
| `__init__.py` | - | Module exports |

#### Features

- **Batch Processing**: Processes multiple records in single API calls
- **Smart Classification**: Categorizes resources by type and topic
- **Title Generation**: Creates clear academic titles
- **Resume Support**: Continues from last processed record

#### Usage

```python
from src.processing.batch_processor import run_batch_enrichment

# Process all pending records
run_batch_enrichment()
```

#### Output Fields

| Field | Description | Example |
|-------|-------------|---------|
| `Final_Title` | Generated academic title | "Introduction to Quantum Computing" |
| `Resource_Type` | Content classification | "Video Resource", "Research Paper" |
| `Enriched_Topic` | Standardized topic | "Quantum Mechanics" |
| `Enriched_Category` | Domain hierarchy | "Physics > Quantum Computing" |

---

### 3. Database (`src/database/`)

Index building for fast hybrid search.

#### Files

| File | Class/Function | Description |
|------|----------------|-------------|
| `build_db.py` | `DatabaseBuilder` | Creates FAISS and BM25 indices |
| `__init__.py` | - | Module exports |

#### Generated Files

```
data/db/
├── olympia_vectors.index   # FAISS vector index (semantic search)
├── olympia_bm25.pkl        # BM25 index (keyword search)
└── olympia_docs.pkl        # Document metadata
```

#### Usage

```python
from src.database.build_db import DatabaseBuilder

# Build all indices
builder = DatabaseBuilder()
builder.build_all()

# Or verify existing database
from src.database.build_db import verify_database
verify_database()
```

#### Command Line

```bash
# Build database
python -m src.database.build_db

# Verify integrity
python -m src.database.build_db --verify

# Custom input file
python -m src.database.build_db --input "path/to/data.xlsx"
```

---

### 4. Engine (`src/engine/`)

The hybrid search and retrieval engine.

#### Files

| File | Class/Function | Description |
|------|----------------|-------------|
| `rag_engine.py` | `HybridSearchEngine` | Main search interface |
| `rag_engine.py` | `Librarian` | Legacy alias for backward compatibility |
| `__init__.py` | - | Module exports |

#### Search Algorithm

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID SEARCH FLOW                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Query: "quantum mechanics bird navigation"                 │
│                    │                                        │
│         ┌─────────┴─────────┐                              │
│         ▼                   ▼                              │
│  ┌─────────────┐    ┌─────────────┐                        │
│  │  SEMANTIC   │    │   KEYWORD   │                        │
│  │   SEARCH    │    │   SEARCH    │                        │
│  │  (FAISS)    │    │   (BM25)    │                        │
│  │             │    │             │                        │
│  │  Weight:    │    │  Weight:    │                        │
│  │   40%       │    │   60%       │                        │
│  └──────┬──────┘    └──────┬──────┘                        │
│         │                  │                                │
│         └────────┬─────────┘                                │
│                  ▼                                          │
│         ┌─────────────┐                                    │
│         │   FUSION    │                                    │
│         │  & RANKING  │                                    │
│         └──────┬──────┘                                    │
│                ▼                                            │
│         ┌─────────────┐                                    │
│         │  TOP-K      │                                    │
│         │  RESULTS    │                                    │
│         └─────────────┘                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Usage

```python
from src.engine.rag_engine import HybridSearchEngine

# Initialize
engine = HybridSearchEngine()

# Basic search
results = engine.search("quantum mechanics", top_k=5)

# Filtered search
results = engine.search(
    query="python tutorial",
    top_k=3,
    type_filter="Video Resource"
)

# Get statistics
stats = engine.get_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
```

#### Result Structure

```python
{
    "id": 42,
    "score": 0.8532,
    "title": "Introduction to Quantum Computing",
    "link": "https://youtube.com/watch?v=...",
    "type": "Video Resource",
    "category": "Physics > Quantum Computing",
    "topic": "Quantum Mechanics",
    "summary": "A beginner-friendly introduction...",
    "insights": "Key concepts: superposition, entanglement...",
    "context": "This video explains the fundamental principles..."
}
```

#### Command Line

```bash
# Interactive search
python -m src.engine.rag_engine --interactive

# Single query
python -m src.engine.rag_engine "machine learning basics"

# Show statistics
python -m src.engine.rag_engine --stats
```

---

### 5. Utils (`src/utils/`)

Configuration, evaluation, and helper utilities.

#### Files

| File | Description |
|------|-------------|
| `config.py` | Centralized configuration settings |
| `evaluate_system.py` | RAG evaluation framework |
| `limit_checker.py` | User quota management |
| `__init__.py` | Module exports |

#### Configuration (`config.py`)

```python
from src.utils.config import (
    # Paths
    PROJECT_ROOT,
    DATA_DIR,
    DB_DIR,
    
    # Model settings
    OLLAMA_MODEL,
    EMBEDDING_MODEL,
    
    # Search settings
    TOP_K_RESULTS,
    HYBRID_ALPHA,
    
    # UI settings
    APP_TITLE,
    WELCOME_MESSAGE,
)
```

#### Evaluation (`evaluate_system.py`)

```python
from src.utils.evaluate_system import run_evaluation_suite

# Run full evaluation
run_evaluation_suite()

# Generates:
# - data/processed/evaluation_report.csv
# - data/processed/evaluation_summary.md
```

**Metrics Evaluated:**

| Metric | Description | Target |
|--------|-------------|--------|
| Hit Rate | Retrieval accuracy | >80% |
| Faithfulness | Answer grounding | >4.0/5 |
| Relevance | Answer quality | >4.0/5 |
| Latency | Response time | <10s |

#### Rate Limiting (`limit_checker.py`)

```python
from src.utils.limit_checker import check_and_update_limit

# Check user quota
allowed, count = check_and_update_limit(
    user_id="user123",
    max_limit=100  # Daily limit
)

if allowed:
    # Process request
    pass
else:
    print(f"Daily limit reached: {count}/{100}")
```

---

## 🔄 Data Pipeline

### Complete Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          DATA PIPELINE                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STAGE 1: EXTRACTION                                                     │
│  ┌─────────────────┐                                                     │
│  │  WhatsApp Chat  │──▶ link_extractor.py ──▶ whatsapp_links_unique.xlsx│
│  │    Exports      │                                                     │
│  └─────────────────┘                                                     │
│           │                                                              │
│           ▼                                                              │
│  STAGE 2: VALIDATION                                                     │
│  ┌─────────────────┐                                                     │
│  │  Raw Links      │──▶ cleaner.py ──▶ oa_cleaned.xlsx                  │
│  │  (with dead)    │         │                                          │
│  └─────────────────┘         └──▶ Removes 404s, validates URLs          │
│           │                                                              │
│           ▼                                                              │
│  STAGE 3: INGESTION                                                      │
│  ┌─────────────────┐                                                     │
│  │  Valid URLs     │──▶ universal_ingestor.py ──▶ Scraped Content       │
│  │                 │         │                                          │
│  └─────────────────┘         ├──▶ YouTube: Transcripts                  │
│           │                  └──▶ Web: Article text                     │
│           ▼                                                              │
│  STAGE 4: ENRICHMENT                                                     │
│  ┌─────────────────┐                                                     │
│  │  Raw Content    │──▶ batch_processor.py ──▶ oa_enriched.xlsx         │
│  │                 │         │                                          │
│  └─────────────────┘         └──▶ DeepSeek: Title, Category, Keywords  │
│           │                                                              │
│           ▼                                                              │
│  STAGE 5: INDEXING                                                       │
│  ┌─────────────────┐                                                     │
│  │  Enriched Data  │──▶ build_db.py ──▶ olympia_vectors.index           │
│  │                 │         │          olympia_bm25.pkl                │
│  └─────────────────┘         │          olympia_docs.pkl                │
│           │                  │                                          │
│           ▼                  └──▶ Sentence Transformers + BM25          │
│  STAGE 6: SERVING                                                        │
│  ┌─────────────────┐                                                     │
│  │  Search Indices │──▶ rag_engine.py ──▶ Hybrid Search Results         │
│  │                 │         │                                          │
│  └─────────────────┘         └──▶ 40% Semantic + 60% Keyword            │
│           │                                                              │
│           ▼                                                              │
│  STAGE 7: INTERFACE                                                      │
│  ┌─────────────────┐                                                     │
│  │  Hybrid Search  │──▶ app.py ──▶ Streamlit Chat Interface             │
│  │    Results      │         │                                          │
│  └─────────────────┘         ├──▶ Source cards                          │
│                              ├──▶ AI response generation                │
│                              ├──▶ Fact verification                     │
│                              └──▶ Follow-up suggestions                 │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Commands

```bash
# Stage 1: Extract
python -m src.ingestion.link_extractor

# Stage 2: Validate
python -m src.ingestion.cleaner

# Stage 3: Ingest
python -m src.ingestion.universal_ingestor batch

# Stage 4: Enrich
python -m src.processing.batch_processor

# Stage 5: Index
python -m src.database.build_db

# Stage 6 & 7: Serve
streamlit run app.py
```

---

## 🚀 Quick Start

### Option 1: Step-by-Step

```bash
# 1. Setup environment
cd olympia-academia
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API key

# 3. Run pipeline (if you have data)
python -m src.ingestion.link_extractor
python -m src.ingestion.cleaner
python -m src.processing.batch_processor
python -m src.database.build_db

# 4. Launch app
streamlit run app.py
```

### Option 2: Full Pipeline (Programmatic)

```python
from src.ingestion import run_full_pipeline
from src.database.build_db import DatabaseBuilder

# Run ingestion pipeline
run_full_pipeline(max_workers=10)

# Build database
builder = DatabaseBuilder()
builder.build_all()

print("✅ Setup complete! Run: streamlit run app.py")
```

### Option 3: Just Run the Chat (with existing database)

```bash
# Ensure database files exist in data/db/
streamlit run app.py
```

### Option 4: Verify Installation

```python
from src import verify_installation, quick_setup

# Check if everything is set up correctly
verify_installation()

# Print setup guide
quick_setup()
```

---

## 📖 API Reference

### Core Classes

#### `HybridSearchEngine`

```python
class HybridSearchEngine:
    """Main search interface for Olympia Academia."""
    
    def __init__(self, lazy_load: bool = False):
        """
        Initialize the search engine.
        
        Args:
            lazy_load: If True, defer loading until first search
        """
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        type_filter: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            type_filter: Filter by resource type
            use_cache: Whether to use result caching
            
        Returns:
            List of search results with scores and metadata
        """
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
    
    def clear_cache(self):
        """Clear the search result cache."""
```

#### `UniversalIngestor`

```python
class UniversalIngestor:
    """Content scraper supporting YouTube and web sources."""
    
    def __init__(self, enrich: bool = True):
        """
        Initialize the ingestor.
        
        Args:
            enrich: Whether to enrich content with AI analysis
        """
    
    def ingest(self, url: str) -> IngestedContent:
        """
        Ingest content from a single URL.
        
        Args:
            url: URL to process
            
        Returns:
            IngestedContent with scraped and enriched data
        """
    
    def ingest_batch(
        self,
        urls: List[str],
        max_workers: int = 5
    ) -> Generator[IngestedContent, None, None]:
        """
        Process multiple URLs concurrently.
        
        Args:
            urls: List of URLs to process
            max_workers: Number of concurrent threads
            
        Yields:
            IngestedContent for each URL
        """
```

#### `DatabaseBuilder`

```python
class DatabaseBuilder:
    """Builds FAISS and BM25 search indices."""
    
    def load_data(self):
        """Load enriched data from Excel file."""
    
    def filter_and_enrich(self):
        """Filter active links and create search contexts."""
    
    def build_vector_index(self):
        """Build FAISS vector index for semantic search."""
    
    def build_bm25_index(self):
        """Build BM25 index for keyword search."""
    
    def build_all(self):
        """Run the complete database building pipeline."""
```

### Data Classes

#### `IngestedContent`

```python
@dataclass
class IngestedContent:
    url: str                    # Source URL
    source_type: str            # 'youtube' | 'web'
    title: str                  # Extracted title
    content: str                # Main text/transcript
    author: Optional[str]       # Content author
    published_date: Optional[str]
    description: Optional[str]
    language: Optional[str]
    word_count: int
    ai_summary: Optional[str]   # AI-generated summary
    keywords: Optional[List[str]]
    category: Optional[str]
    topics: Optional[List[str]]
    success: bool
    error_message: Optional[str]
```

#### `SearchResult`

```python
@dataclass
class SearchResult:
    id: int                     # Document ID
    score: float                # Relevance score (0-1)
    title: str                  # Resource title
    link: str                   # Source URL
    type: str                   # Resource type
    category: str               # Domain category
    topic: str                  # Main topic
    summary: str                # AI summary
    insights: str               # Key insights
    context: str                # Relevant context
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required
OLLAMA_API_KEY=your_api_key_here

# Optional (with defaults)
OLLAMA_HOST=https://ollama.com
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
OLLAMA_TIMEOUT=120

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Processing
BATCH_SIZE=10
MAX_WORKERS=5

# Rate Limiting
MAX_REQUESTS_PER_MINUTE=30
DAILY_USER_QUOTA=100
```

### Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_API_KEY` | *required* | API key for Ollama |
| `OLLAMA_HOST` | `https://ollama.com` | Ollama server URL |
| `OLLAMA_MODEL` | `deepseek-v3.1:671b-cloud` | Model for AI enrichment |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `BATCH_SIZE` | `10` | Records per API batch |
| `MAX_WORKERS` | `5` | Concurrent processing threads |
| `TOP_K_RESULTS` | `5` | Default search results |
| `HYBRID_ALPHA` | `0.7` | Semantic search weight |
| `DAILY_USER_QUOTA` | `100` | Max queries per user per day |

---

## 📁 File Structure

```
olympia-academia/
│
├── 📄 app.py                    # 🖥️ STREAMLIT CHAT INTERFACE
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env.example              # Environment template
├── 📄 .gitignore                # Git ignore rules
├── 📄 README.md                 # Project README
│
├── 📁 data/
│   ├── 📁 raw/                  # Raw data (WhatsApp exports, etc.)
│   │   └── .gitkeep
│   ├── 📁 processed/            # Processed Excel files
│   │   └── .gitkeep
│   ├── 📁 db/                   # Search indices
│   │   ├── olympia_vectors.index
│   │   ├── olympia_bm25.pkl
│   │   ├── olympia_docs.pkl
│   │   └── user_limits.db
│   └── 📁 backups/              # Automatic backups
│
├── 📁 legacy/                   # Deprecated scripts
│
└── 📁 src/                      # SOURCE CODE
    ├── 📄 __init__.py           # Package initialization
    ├── 📄 README.md             # This documentation
    ├── 📄 requirements.txt      # Source-specific requirements
    │
    ├── 📁 ingestion/            # Data Collection Layer
    │   ├── 📄 __init__.py
    │   ├── 📄 link_extractor.py
    │   ├── 📄 cleaner.py
    │   └── 📄 universal_ingestor.py
    │
    ├── 📁 processing/           # AI Enrichment Layer
    │   ├── 📄 __init__.py
    │   └── 📄 batch_processor.py
    │
    ├── 📁 database/             # Index Building Layer
    │   ├── 📄 __init__.py
    │   └── 📄 build_db.py
    │
    ├── 📁 engine/               # Search & Retrieval Layer
    │   ├── 📄 __init__.py
    │   └── 📄 rag_engine.py
    │
    └── 📁 utils/                # Utilities Layer
        ├── 📄 __init__.py
        ├── 📄 config.py
        ├── 📄 evaluate_system.py
        └── 📄 limit_checker.py
```

---

## 🔧 Troubleshooting

### Common Issues

<details>
<summary><b>❌ "FAISS index not found"</b></summary>

**Cause:** Database hasn't been built yet.

**Solution:**
```bash
python -m src.database.build_db
```
</details>

<details>
<summary><b>❌ "API Key Missing"</b></summary>

**Cause:** `.env` file not configured.

**Solution:**
```bash
cp .env.example .env
# Edit .env and add your OLLAMA_API_KEY
```
</details>

<details>
<summary><b>❌ "Ollama connection failed"</b></summary>

**Cause:** Ollama server not running or wrong host.

**Solution:**
1. Start Ollama: `ollama serve`
2. Check `.env` for correct `OLLAMA_HOST`
3. Verify model: `ollama list`
</details>

<details>
<summary><b>❌ "No links extracted from WhatsApp"</b></summary>

**Cause:** Chat file format not recognized.

**Solution:**
1. Export chat as `.txt` from WhatsApp
2. Check file encoding (should be UTF-8)
3. Verify file paths in `link_extractor.py`
</details>

<details>
<summary><b>❌ "Permission denied when saving Excel"</b></summary>

**Cause:** File is open in another program.

**Solution:**
1. Close Excel/spreadsheet application
2. Check file permissions
3. The script will auto-retry 3 times
</details>

<details>
<summary><b>❌ "YouTube transcript not available"</b></summary>

**Cause:** Video doesn't have captions or is private.

**Solution:**
1. Falls back to video description automatically
2. Install `youtube-transcript-api` for better support
3. Some videos genuinely have no transcripts
</details>

<details>
<summary><b>❌ "Rate limit reached"</b></summary>

**Cause:** Daily query quota exceeded.

**Solution:**
1. Wait until next day (quota resets at midnight)
2. Increase `DAILY_USER_QUOTA` in `.env`
3. Delete `data/db/user_limits.db` to reset
</details>

<details>
<summary><b>❌ "Streamlit won't start"</b></summary>

**Cause:** Various possible issues.

**Solution:**
```bash
# Check Streamlit installation
pip install --upgrade streamlit

# Run with debug mode
streamlit run app.py --logger.level=debug

# Check port availability
streamlit run app.py --server.port 8502
```
</details>

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verify Installation

```python
from src import verify_installation
verify_installation()
```

### Get System Info

```python
from src import print_system_info
print_system_info()
```

---

## 📊 Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Link Extraction | ~1s/1000 links | Depends on file size |
| URL Validation | ~2s/URL | Network-bound |
| Web Scraping | ~3s/page | Includes parsing |
| YouTube Transcript | ~1s/video | Using API |
| AI Enrichment | ~5s/batch of 10 | DeepSeek API |
| Index Building | ~30s/1000 docs | FAISS + BM25 |
| Hybrid Search | ~50ms/query | With caching |
| **Chat Response** | ~3-5s | Including streaming |

---

## 🤝 Contributing

1. Follow the existing code structure
2. Add docstrings to all functions
3. Update this README for new features
4. Test with `python -m src.utils.evaluate_system`

---


---

<div align="center">

**Made with ❤️ by the Olympia Academia Team**

[Back to Top](#-olympia-academia)

</div>
```

---


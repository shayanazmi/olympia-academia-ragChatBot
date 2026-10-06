<div align="center">

# 🏛️ Olympia Academia

**Intelligent Academic Research Assistant with Grounded Hybrid Retrieval & NVIDIA NIM**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-00ADD8?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA-NIM_API-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

</div>

---

## 📌 Overview

**Olympia Academia** is an end-to-end Retrieval-Augmented Generation (RAG) system engineered to transform academic chat exports (e.g. WhatsApp, community channels) and curated web resources into an intelligent, searchable research knowledge base with an interactive AI research assistant.

It bridges messy, unstructured links shared across research channels into structured, semantically indexed resources powered by:
- **Hybrid Retrieval**: Dense vector search via **FAISS** (`all-MiniLM-L6-v2`) + sparse lexical ranking via **BM25**.
- **NVIDIA NIM Microservices**: High-performance reasoning with Nemotron & Llama 3 models for query routing, multi-candidate query expansion, and grounded response synthesis.
- **Automated Data Ingestion**: End-to-end extraction from WhatsApp exports, YouTube transcript fetching, and web article extraction.
- **Interactive UI**: A Streamlit interface equipped with verification indicators, source citation cards, and one-click database building.

---

## ✨ Features

- 📱 **WhatsApp Link Ingestion**: Extracts and parses raw links directly from WhatsApp chat exports (`.txt`).
- 🌐 **Universal Content Ingestion**: Automatically scrapes web articles and retrieves YouTube video transcripts.
- 🏷️ **AI Enrichment Pipeline**: Synthesizes titles, topics, research categories, concise summaries, and key insights.
- ⚡ **Hybrid Search (`Librarian`)**: Combines semantic embeddings (Sentence Transformers) with keyword search (BM25) with reciprocal-rank / score fusion.
- 🎯 **Smart Query Routing & Expansion**: Analyzes conversational context with fast LLMs to route queries and formulate targeted multi-query expansions.
- 🛡️ **Source-Grounded Answers**: Responses are verified against retrieved context and rendered with clickable citation cards and relevance metrics.
- 📊 **In-App Database Management**: Check vector counts, cache hit rates, clear session states, or build/seed the database directly inside Streamlit.

---

## 🏗️ Architecture

```text
┌────────────────────────┐
│  WhatsApp Export / Web │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Ingestion & Cleaner    │  --> link_extractor.py, cleaner.py, universal_ingestor.py
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ AI Enrichment          │  --> batch_processor.py (Summaries, Topics, Metadata)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Database Builder       │  --> build_db.py (FAISS Index + BM25 Lexical Model)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Hybrid RAG Engine      │  --> rag_engine.py (Librarian: FAISS + BM25 Fusion)
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│ Streamlit UI & NIM LLM │  --> app.py (NVIDIA NIM Reasoning & Grounded Citations)
└────────────────────────┘
```

---

## 📂 Project Structure

```text
olympia-academia-ragChatBot/
├── app.py                      # Main Streamlit web application & chat UI
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variable configuration
├── .gitignore                  # Git ignore rules for data, models & caches
├── README.md                   # Project documentation
│
├── data/                       # Local data directories (gitignored)
│   ├── raw/                    # Raw WhatsApp exports (.txt) & link spreadsheets
│   ├── processed/              # Cleaned & enriched spreadsheets (.xlsx)
│   ├── db/                     # FAISS index, BM25 model, doc storage
│   │   ├── olympia_vectors.index
│   │   ├── olympia_bm25.pkl
│   │   └── olympia_docs.pkl
│   └── backups/                # Database backups
│
└── src/
    ├── ingestion/              # Data collection & URL processing
    │   ├── link_extractor.py   # Regex-based link extraction from chat exports
    │   ├── cleaner.py          # URL validation and deduplication
    │   └── universal_ingestor.py # Scrapes YouTube transcripts & web pages
    │
    ├── processing/             # Enrichment & batch processing
    │   └── batch_processor.py  # AI categorization and summary generation
    │
    ├── database/               # Index creation and persistence
    │   ├── build_db.py         # Builds FAISS and BM25 index artifacts
    │   └── seed_data.py        # Curated academic research seed dataset
    │
    ├── engine/                 # Search & retrieval mechanics
    │   └── rag_engine.py       # Hybrid retrieval engine (`Librarian`)
    │
    └── utils/                  # Shared configuration & helper modules
        ├── config.py           # Centralized configuration & environment loader
        └── nim_client.py       # NVIDIA NIM API client wrapper
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+**
- An **NVIDIA NIM API key** (free trial available at [build.nvidia.com](https://build.nvidia.com))
- Git installed on your machine

### 2. Clone the Repository

```bash
git clone https://github.com/shayanazmi/olympia-academia-ragChatBot.git
cd olympia-academia-ragChatBot
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example configuration:

```bash
cp .env.example .env
```

Open `.env` in your text editor and add your NVIDIA NIM credentials:

```env
# NVIDIA NIM API Credentials (https://build.nvidia.com)
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1

# Optimal Models
NVIDIA_PRIMARY_MODEL=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
NVIDIA_FAST_MODEL=meta/llama-3.2-11b-vision-instruct
NVIDIA_TIMEOUT=60

# Local Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2
DAILY_USER_QUOTA=100
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

---

## 💻 Running the Application

Launch the Streamlit web interface:

```bash
streamlit run app.py
```

Once loaded in your browser (usually `http://localhost:8501`):
1. If you haven't built the database yet, click **"🌱 Build Seed Academic Database"** in the sidebar. This instantly creates the FAISS and BM25 indices from curated academic resources.
2. Type any academic or scientific research query in the chat input.
3. Review the AI's synthesized explanation alongside expandable source cards and relevance scores.

---

## 🛠️ Data Pipeline Workflows

If you want to ingest your own custom WhatsApp chat export or web sources:

### 1. Extract Links from WhatsApp
Place your WhatsApp chat export `.txt` files into `data/raw/` and run:
```bash
python -m src.ingestion.link_extractor
```

### 2. Clean & Deduplicate URLs
```bash
python -m src.ingestion.cleaner
```

### 3. Ingest Content (YouTube transcripts & Web scraping)
```bash
python -m src.ingestion.universal_ingestor batch
```

### 4. AI Metadata Enrichment
```bash
python -m src.processing.batch_processor
```

### 5. Build Local Search Indices
```bash
python -m src.database.build_db
```

---

## ⚙️ Configuration Reference

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `NVIDIA_API_KEY` | **Yes** | — | NVIDIA NIM API key from [build.nvidia.com](https://build.nvidia.com) |
| `NVIDIA_BASE_URL` | No | `https://integrate.api.nvidia.com/v1` | NVIDIA NIM endpoint |
| `NVIDIA_PRIMARY_MODEL`| No | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Main reasoning model for RAG response generation |
| `NVIDIA_FAST_MODEL` | No | `meta/llama-3.2-11b-vision-instruct` | Fast model for query routing and sub-query expansion |
| `NVIDIA_TIMEOUT` | No | `60` | Request timeout in seconds |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | SentenceTransformer model used for dense FAISS vectors |
| `DAILY_USER_QUOTA` | No | `100` | Daily request cap per user |

---

## ❓ Troubleshooting

- **Database indices not found**:
  Click **"Build Seed Academic Database"** in the sidebar or run `python -m src.database.build_db` in the terminal.
- **NVIDIA_API_KEY Missing**:
  Verify that `.env` is created in the project root and contains `NVIDIA_API_KEY=nvapi-...`.
- **PyTorch / SentenceTransformers Issues**:
  Ensure PyTorch compatible with your OS/hardware is installed (`pip install torch torchvision`).

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

"""
Olympia Academia - Main Source Package
=======================================

A privacy-first RAG system that turns WhatsApp group links into a 
searchable local knowledge base.

Modules:
--------
- ingestion: Extract, clean, and ingest content from various sources
- processing: AI enrichment using Ollama/DeepSeek
- database: Build FAISS and BM25 search indices
- engine: Hybrid search and RAG query engine
- utils: Configuration, evaluation, and helper utilities

Workflow:
---------
1. Extract links from WhatsApp chats (ingestion.link_extractor)
2. Validate and clean links (ingestion.cleaner)
3. Scrape content from URLs (ingestion.universal_ingestor)
4. Enrich with AI analysis (processing.batch_processor)
5. Build search indices (database.build_db)
6. Query via RAG engine (engine.rag_engine)

Example:
--------
>>> from src.ingestion import run_full_pipeline
>>> from src.database.build_db import DatabaseBuilder
>>> from src.engine.rag_engine import HybridSearchEngine
>>> 
>>> # Run complete ingestion pipeline
>>> run_full_pipeline()
>>> 
>>> # Build search database
>>> builder = DatabaseBuilder()
>>> builder.build_all()
>>> 
>>> # Query the system
>>> engine = HybridSearchEngine()
>>> results = engine.search("quantum mechanics")

Author: Olympia Academia Team
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Olympia Academia Team"
__license__ = "MIT"

# Core project metadata
PROJECT_NAME = "Olympia Academia"
PROJECT_DESCRIPTION = "Privacy-first RAG system for WhatsApp knowledge bases"

# Import version info from submodules
from . import ingestion
from . import processing
from . import database
from . import engine
from . import utils

# Make commonly used classes easily accessible
from .ingestion import (
    LinkExtractor,
    LinkCleaner,
    UniversalIngestor,
    IngestionPipeline,
)

from .engine.rag_engine import (
    HybridSearchEngine,
    Librarian,  # Legacy alias
)

from .database.build_db import DatabaseBuilder

from .utils.config import (
    PROJECT_ROOT,
    DATA_DIR,
    DB_DIR,
    OLLAMA_MODEL,
    EMBEDDING_MODEL,
)

from .utils.limit_checker import (
    check_and_update_limit,
    init_limits_db,
)

# Quick access to common workflows
def quick_setup():
    """
    Quick setup guide for new users.
    Prints step-by-step instructions.
    """
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🏛️  OLYMPIA ACADEMIA SETUP GUIDE" + " " * 14 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    print("📋 Step-by-step workflow:")
    print()
    print("1️⃣  Extract links from WhatsApp chats:")
    print("    python -m src.ingestion.link_extractor")
    print()
    print("2️⃣  Validate and clean links:")
    print("    python -m src.ingestion.cleaner")
    print()
    print("3️⃣  Scrape and enrich content:")
    print("    python -m src.ingestion.universal_ingestor batch")
    print("    OR")
    print("    python -m src.processing.batch_processor")
    print()
    print("4️⃣  Build search indices:")
    print("    python -m src.database.build_db")
    print()
    print("5️⃣  Launch the chatbot:")
    print("    streamlit run app.py")
    print()
    print("📚 For more details, see README.md")
    print()
    print("💡 Quick test:")
    print("    python -m src.engine.rag_engine --interactive")
    print()


def verify_installation():
    """
    Verify that all required components are properly installed.
    Returns a status report.
    """
    print("🔍 Verifying Olympia Academia installation...")
    print()
    
    issues = []
    warnings = []
    
    # Check directories
    from pathlib import Path
    
    dirs_to_check = {
        "Project Root": PROJECT_ROOT,
        "Data Directory": DATA_DIR,
        "Database Directory": DB_DIR,
    }
    
    print("📁 Directory Structure:")
    for name, path in dirs_to_check.items():
        exists = "✓" if Path(path).exists() else "✗"
        status = "OK" if Path(path).exists() else "MISSING"
        print(f"  {exists} {name}: {status}")
        if not Path(path).exists():
            issues.append(f"{name} not found at {path}")
    print()
    
    # Check required packages
    print("📦 Required Packages:")
    packages = {
        'pandas': 'Data processing',
        'faiss': 'Vector search (faiss-cpu or faiss-gpu)',
        'sentence_transformers': 'Embeddings',
        'streamlit': 'Web interface',
        'ollama': 'AI enrichment',
        'requests': 'Web scraping',
        'beautifulsoup4': 'HTML parsing',
    }
    
    for package, description in packages.items():
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✓ {package}: Installed")
        except ImportError:
            print(f"  ✗ {package}: MISSING ({description})")
            issues.append(f"Missing package: {package}")
    print()
    
    # Check optional packages
    print("🔧 Optional Packages:")
    optional = {
        'trafilatura': 'Enhanced web scraping',
        'yt_dlp': 'YouTube downloads',
        'youtube_transcript_api': 'YouTube transcripts',
    }
    
    for package, description in optional.items():
        try:
            __import__(package)
            print(f"  ✓ {package}: Installed")
        except ImportError:
            print(f"  ⚠ {package}: Not installed ({description})")
            warnings.append(f"Optional: {package} - {description}")
    print()
    
    # Check database files
    from pathlib import Path
    
    print("🗄️  Database Files:")
    db_files = {
        "FAISS Index": DB_DIR / "olympia_vectors.index",
        "BM25 Index": DB_DIR / "olympia_bm25.pkl",
        "Documents": DB_DIR / "olympia_docs.pkl",
    }
    
    db_built = True
    for name, path in db_files.items():
        exists = "✓" if Path(path).exists() else "✗"
        status = "Found" if Path(path).exists() else "Not built yet"
        print(f"  {exists} {name}: {status}")
        if not Path(path).exists():
            db_built = False
    
    if not db_built:
        warnings.append("Database not built. Run: python -m src.database.build_db")
    print()
    
    # Summary
    print("═" * 60)
    if issues:
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        print()
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
        print()
    
    if not issues and not warnings:
        print("✅ All systems operational!")
    elif not issues:
        print("✅ Core system ready (some optional features unavailable)")
    else:
        print("❌ Please fix issues before proceeding")
    
    print("═" * 60)
    print()
    
    return len(issues) == 0


def get_system_info():
    """Get detailed system information."""
    import platform
    import sys
    from pathlib import Path
    
    info = {
        "Project": PROJECT_NAME,
        "Version": __version__,
        "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "Platform": platform.platform(),
        "Project Root": str(PROJECT_ROOT),
        "Data Directory": str(DATA_DIR),
        "Database Directory": str(DB_DIR),
        "Ollama Model": OLLAMA_MODEL,
        "Embedding Model": EMBEDDING_MODEL,
    }
    
    # Check database status
    db_files = [
        DB_DIR / "olympia_vectors.index",
        DB_DIR / "olympia_bm25.pkl",
        DB_DIR / "olympia_docs.pkl",
    ]
    
    db_exists = all(Path(f).exists() for f in db_files)
    info["Database Status"] = "Built" if db_exists else "Not built"
    
    if db_exists:
        # Get database stats
        try:
            import pickle
            with open(DB_DIR / "olympia_docs.pkl", 'rb') as f:
                docs = pickle.load(f)
                info["Total Documents"] = len(docs)
        except:
            pass
    
    return info


def print_system_info():
    """Print formatted system information."""
    info = get_system_info()
    
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 12 + "🏛️  OLYMPIA ACADEMIA" + " " * 23 + "║")
    print("╠" + "═" * 58 + "╣")
    
    for key, value in info.items():
        padding = 20 - len(key)
        print(f"║  {key}:{' ' * padding}{value[:35]:<35} ║")
    
    print("╚" + "═" * 58 + "╝")


# Module exports
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__license__',
    'PROJECT_NAME',
    'PROJECT_DESCRIPTION',
    
    # Submodules
    'ingestion',
    'processing',
    'database',
    'engine',
    'utils',
    
    # Main classes
    'LinkExtractor',
    'LinkCleaner',
    'UniversalIngestor',
    'IngestionPipeline',
    'HybridSearchEngine',
    'Librarian',
    'DatabaseBuilder',
    
    # Utility functions
    'check_and_update_limit',
    'init_limits_db',
    'quick_setup',
    'verify_installation',
    'get_system_info',
    'print_system_info',
    
    # Configuration
    'PROJECT_ROOT',
    'DATA_DIR',
    'DB_DIR',
    'OLLAMA_MODEL',
    'EMBEDDING_MODEL',
]


# Auto-verify on import (can be disabled with environment variable)
import os
if os.getenv("OLYMPIA_AUTO_VERIFY", "0") == "1":
    verify_installation()
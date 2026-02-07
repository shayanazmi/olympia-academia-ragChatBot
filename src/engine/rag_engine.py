"""
RAG Engine for Olympia Academia
================================
Hybrid search engine combining semantic (FAISS) and keyword (BM25) search.

Author: Olympia Academia Team
"""

import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import re
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import time

# ==========================================
# CONFIGURATION
# ==========================================

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)-8s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Path Configuration - Updated to match new structure
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DB_DIR = PROJECT_ROOT / "data" / "db"

# Database paths - using your naming convention
VECTOR_DB_PATH = DB_DIR / "olympia_vectors.index"
METADATA_PATH = DB_DIR / "olympia_docs.pkl"  # Updated from olympia_metadata.pkl
BM25_PATH = DB_DIR / "olympia_bm25.pkl"

# Model Configuration
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# Search Configuration
DEFAULT_TOP_K = 5
MAX_CANDIDATES = 15  # 3x top_k for candidate generation
VECTOR_WEIGHT = 0.4  # Semantic search weight
BM25_WEIGHT = 0.6    # Keyword search weight
BM25_NORMALIZATION_FACTOR = 8.0

# ==========================================
# DATA CLASSES
# ==========================================

@dataclass
class SearchResult:
    """Structured search result."""
    id: int
    score: float
    title: str
    link: str
    type: str
    category: str
    topic: str
    summary: str
    insights: str
    context: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "score": round(self.score, 4),
            "title": self.title,
            "link": self.link,
            "type": self.type,
            "category": self.category,
            "topic": self.topic,
            "summary": self.summary,
            "insights": self.insights,
            "context": self.context
        }

# ==========================================
# HYBRID SEARCH ENGINE
# ==========================================

class HybridSearchEngine:
    """
    Advanced hybrid search combining semantic and keyword matching.
    
    Features:
    - FAISS for semantic similarity
    - BM25 for keyword relevance
    - Weighted fusion with normalization
    - Result caching for performance
    - Detailed logging and metrics
    """
    
    def __init__(self, lazy_load: bool = False):
        """
        Initialize the search engine.
        
        Args:
            lazy_load: If True, defer loading resources until first search
        """
        self.model = None
        self.index = None
        self.df = None
        self.bm25 = None
        self.tokenized_corpus = None
        
        # Performance tracking
        self._search_cache = {}
        self._cache_hits = 0
        self._total_searches = 0
        
        if not lazy_load:
            self._load_resources()
    
    def _load_resources(self):
        """Load all required resources: models, indices, and metadata."""
        start_time = time.time()
        logger.info("🔄 Loading Olympia Academia search resources...")
        
        try:
            # 1. Load Embedding Model
            logger.info(f"   Loading embedding model: {EMBEDDING_MODEL}")
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            
            # 2. Load FAISS Index
            if not VECTOR_DB_PATH.exists():
                raise FileNotFoundError(
                    f"❌ Vector index not found at {VECTOR_DB_PATH}\n"
                    f"   Run 'python -m src.database.build_db' first."
                )
            
            self.index = faiss.read_index(str(VECTOR_DB_PATH))
            logger.info(f"   ✓ FAISS index loaded: {self.index.ntotal} vectors")
            
            # 3. Load Metadata
            if not METADATA_PATH.exists():
                raise FileNotFoundError(
                    f"❌ Metadata not found at {METADATA_PATH}\n"
                    f"   Run 'python -m src.database.build_db' first."
                )
            
            with open(METADATA_PATH, 'rb') as f:
                self.df = pickle.load(f)
            logger.info(f"   ✓ Metadata loaded: {len(self.df)} documents")
            
            # 4. Load BM25 Index
            if not BM25_PATH.exists():
                raise FileNotFoundError(
                    f"❌ BM25 index not found at {BM25_PATH}\n"
                    f"   Run 'python -m src.database.build_db' first."
                )
            
            with open(BM25_PATH, 'rb') as f:
                bm25_data = pickle.load(f)
            
            # Handle both old and new BM25 format
            if isinstance(bm25_data, dict):
                self.bm25 = bm25_data['bm25']
                self.tokenized_corpus = bm25_data.get('tokenized_corpus', None)
            else:
                self.bm25 = bm25_data
                self.tokenized_corpus = None
            
            logger.info(f"   ✓ BM25 index loaded")
            
            # Log total load time
            load_time = time.time() - start_time
            logger.info(f"✅ All resources loaded in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")
            raise
    
    def clean_query(self, query: str) -> List[str]:
        """
        Clean and tokenize query for BM25 search.
        
        Args:
            query: Raw query string
            
        Returns:
            List of cleaned tokens
        """
        # Convert to lowercase and remove special characters
        cleaned = re.sub(r'[^\w\s\-]', '', str(query).lower())
        # Normalize whitespace and split
        tokens = cleaned.split()
        # Remove empty tokens
        return [t for t in tokens if t]
    
    def _normalize_scores(self, scores: Dict[int, float], method: str = "minmax") -> Dict[int, float]:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            scores: Dictionary of index -> score
            method: Normalization method ('minmax' or 'zscore')
            
        Returns:
            Normalized scores
        """
        if not scores:
            return {}
        
        values = list(scores.values())
        
        if method == "minmax":
            min_val = min(values)
            max_val = max(values)
            if max_val == min_val:
                return {k: 0.5 for k in scores}
            return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}
        
        elif method == "zscore":
            mean = np.mean(values)
            std = np.std(values)
            if std == 0:
                return {k: 0.5 for k in scores}
            return {k: 0.5 + 0.5 * np.tanh((v - mean) / std) for k, v in scores.items()}
        
        return scores
    
    def _semantic_search(self, query: str, k: int) -> Dict[int, float]:
        """
        Perform semantic search using FAISS.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            Dictionary of index -> similarity score
        """
        # Encode query
        query_vector = self.model.encode([query], normalize_embeddings=True).astype('float32')
        
        # Search (using inner product since embeddings are normalized)
        distances, indices = self.index.search(query_vector, k)
        
        results = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:  # Valid index
                # For normalized vectors, inner product = cosine similarity
                # Convert to [0, 1] range
                similarity = (dist + 1) / 2  # From [-1, 1] to [0, 1]
                results[idx] = max(0, min(1, similarity))
        
        return results
    
    def _keyword_search(self, query: str, k: int) -> Dict[int, float]:
        """
        Perform keyword search using BM25.
        
        Args:
            query: Search query
            k: Number of results
            
        Returns:
            Dictionary of index -> BM25 score
        """
        # Tokenize query
        query_tokens = self.clean_query(query)
        
        if not query_tokens:
            return {}
        
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k indices
        top_indices = np.argsort(bm25_scores)[::-1][:k]
        
        results = {}
        for idx in top_indices:
            score = bm25_scores[idx]
            if score > 0:
                results[idx] = score
        
        return results
    
    def _extract_document_fields(self, row: pd.Series) -> Dict[str, str]:
        """
        Safely extract and format document fields.
        
        Args:
            row: DataFrame row
            
        Returns:
            Dictionary with formatted fields
        """
        # Helper function to safely get field
        def safe_get(field_name: str, default: str = "") -> str:
            value = row.get(field_name, default)
            if pd.isna(value) or str(value).strip() in ["", "nan", "None"]:
                return default
            return str(value).strip()
        
        # Extract title with fallbacks
        title = safe_get('Final_Title')
        if not title:
            title = safe_get('Scraped_Title', 'Untitled Resource')
        
        # Extract summary with fallbacks
        summary = safe_get('AI_Summary')
        if not summary:
            summary = safe_get('Scraped_Context', 'No summary available.')
        
        # Extract insights
        insights = safe_get('Key_Insights', 'See summary for details.')
        
        # Extract other fields
        fields = {
            'title': title[:200],  # Limit length
            'link': safe_get('URL', '#'),
            'type': safe_get('Resource_Type', 'Resource'),
            'category': safe_get('Enriched_Category', 'General'),
            'topic': safe_get('Enriched_Topic', ''),
            'summary': summary[:800],
            'insights': insights[:400],
            'context': safe_get('Scraped_Context', '')[:600]
        }
        
        return fields
    
    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        type_filter: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining semantic and keyword matching.
        
        Args:
            query: Search query
            top_k: Number of results to return
            type_filter: Optional filter by resource type
            use_cache: Whether to use result caching
            
        Returns:
            List of search results as dictionaries
        """
        # Ensure resources are loaded
        if self.model is None:
            self._load_resources()
        
        self._total_searches += 1
        
        # Check cache
        cache_key = f"{query}_{top_k}_{type_filter}"
        if use_cache and cache_key in self._search_cache:
            self._cache_hits += 1
            logger.debug(f"Cache hit for query: {query[:50]}")
            return self._search_cache[cache_key]
        
        start_time = time.time()
        logger.info(f"🔍 Searching for: {query[:100]}...")
        
        # Generate candidates (3x for better coverage)
        num_candidates = min(MAX_CANDIDATES, top_k * 3)
        
        # 1. Semantic Search
        semantic_scores = self._semantic_search(query, num_candidates)
        logger.debug(f"   Semantic search found {len(semantic_scores)} candidates")
        
        # 2. Keyword Search
        keyword_scores = self._keyword_search(query, num_candidates)
        logger.debug(f"   Keyword search found {len(keyword_scores)} candidates")
        
        # 3. Normalize scores
        semantic_norm = self._normalize_scores(semantic_scores, "minmax")
        keyword_norm = self._normalize_scores(keyword_scores, "minmax")
        
        # 4. Hybrid Fusion
        final_scores = {}
        all_indices = set(semantic_norm.keys()) | set(keyword_norm.keys())
        
        for idx in all_indices:
            sem_score = semantic_norm.get(idx, 0.0)
            key_score = keyword_norm.get(idx, 0.0)
            
            # Weighted combination
            final_score = (sem_score * VECTOR_WEIGHT) + (key_score * BM25_WEIGHT)
            final_scores[idx] = final_score
        
        # 5. Sort and filter
        sorted_indices = sorted(final_scores, key=final_scores.get, reverse=True)
        
        results = []
        for idx in sorted_indices:
            if len(results) >= top_k:
                break
            
            # Get document
            try:
                row = self.df.iloc[idx]
            except IndexError:
                logger.warning(f"Index {idx} out of bounds")
                continue
            
            # Apply type filter if specified
            if type_filter:
                doc_type = str(row.get('Resource_Type', '')).lower()
                if type_filter.lower() not in doc_type:
                    continue
            
            # Extract fields
            fields = self._extract_document_fields(row)
            
            # Create result
            result = SearchResult(
                id=int(idx),
                score=float(final_scores[idx]),
                **fields
            )
            
            results.append(result.to_dict())
        
        # Log search metrics
        search_time = time.time() - start_time
        logger.info(
            f"   ✓ Found {len(results)} results in {search_time:.3f}s "
            f"(Cache rate: {self._cache_hits/self._total_searches:.1%})"
        )
        
        # Cache results
        if use_cache:
            self._search_cache[cache_key] = results
            # Limit cache size
            if len(self._search_cache) > 100:
                # Remove oldest entries
                for key in list(self._search_cache.keys())[:20]:
                    del self._search_cache[key]
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        return {
            "total_documents": len(self.df) if self.df is not None else 0,
            "index_size": self.index.ntotal if self.index else 0,
            "total_searches": self._total_searches,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": self._cache_hits / max(1, self._total_searches),
            "cache_size": len(self._search_cache)
        }
    
    def clear_cache(self):
        """Clear the search cache."""
        self._search_cache.clear()
        logger.info("Search cache cleared")

# ==========================================
# LEGACY COMPATIBILITY
# ==========================================

# Alias for backward compatibility
Librarian = HybridSearchEngine

# ==========================================
# TESTING & CLI
# ==========================================

def main():
    """Command-line interface for testing the search engine."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Test Olympia Academia Search Engine")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("-t", "--type", help="Filter by resource type")
    parser.add_argument("--stats", action="store_true", help="Show engine statistics")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    # Initialize engine
    print("Initializing search engine...")
    engine = HybridSearchEngine()
    
    if args.stats:
        stats = engine.get_stats()
        print("\n📊 Search Engine Statistics:")
        print("─" * 40)
        for key, value in stats.items():
            print(f"{key:20s}: {value}")
        return
    
    if args.interactive:
        print("\n🔍 Interactive Search Mode (type 'quit' to exit)")
        print("─" * 60)
        
        while True:
            query = input("\nEnter query: ").strip()
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            results = engine.search(query, top_k=args.top_k)
            
            print(f"\nFound {len(results)} results:")
            print("─" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['title'][:80]}")
                print(f"   Score: {result['score']:.3f} | Type: {result['type']}")
                print(f"   Link: {result['link'][:60]}...")
                print(f"   Summary: {result['summary'][:150]}...")
        
        print("\nGoodbye!")
    
    elif args.query:
        # Single query mode
        results = engine.search(args.query, top_k=args.top_k, type_filter=args.type)
        
        print(f"\nSearch Results for: '{args.query}'")
        print("─" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Type: {result['type']}")
            print(f"   Link: {result['link']}")
            print(f"   Summary: {result['summary'][:200]}...")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
"""
Hybrid RAG Engine for Olympia Academia
Combines Dense Semantic Search (FAISS) with Sparse Keyword Matching (BM25Okapi).
"""

import os
import re
import time
import pickle
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.utils.config import (
    FAISS_INDEX_PATH,
    BM25_INDEX_PATH,
    DOCUMENTS_PATH,
    EMBEDDING_MODEL,
    DEFAULT_TOP_K,
    MAX_CANDIDATES,
    VECTOR_WEIGHT,
    BM25_WEIGHT,
)

logger = logging.getLogger(__name__)

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

class HybridSearchEngine:
    """
    Hybrid search engine combining FAISS semantic vector search and BM25 keyword matching.
    """
    
    def __init__(self, lazy_load: bool = False):
        self.model = None
        self.index = None
        self.df = None
        self.bm25 = None
        self.tokenized_corpus = None
        
        self._search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_hits = 0
        self._total_searches = 0
        
        if not lazy_load:
            self._load_resources()
            
    def _load_resources(self):
        """Load FAISS index, BM25 model, document store, and embedding model."""
        start_time = time.time()
        logger.info("🔄 Loading Olympia Academia search indices...")
        
        if not FAISS_INDEX_PATH.exists() or not DOCUMENTS_PATH.exists() or not BM25_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"Search indices not found in {FAISS_INDEX_PATH.parent}.\n"
                f"Please run 'python -m src.database.build_db --sample' first to generate indices."
            )
            
        # 1. Load Sentence Transformer
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        # 2. Load FAISS Index
        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        
        # 3. Load Document Metadata
        with open(DOCUMENTS_PATH, 'rb') as f:
            self.df = pickle.load(f)
            
        # 4. Load BM25 Index
        with open(BM25_INDEX_PATH, 'rb') as f:
            bm25_data = pickle.load(f)
            if isinstance(bm25_data, dict):
                self.bm25 = bm25_data['bm25']
                self.tokenized_corpus = bm25_data.get('tokenized_corpus')
            else:
                self.bm25 = bm25_data
                self.tokenized_corpus = None
                
        elapsed = time.time() - start_time
        logger.info(f"✅ Indices loaded in {elapsed:.2f}s ({self.index.ntotal} vectors, {len(self.df)} documents)")

    def clean_query(self, query: str) -> List[str]:
        """Clean and tokenize query string for BM25 matching."""
        cleaned = re.sub(r'[^\w\s\-]', '', str(query).lower())
        return [t for t in cleaned.split() if t]

    def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        """
        Robust MinMax score normalization.
        Guards against zero-denominator when all scores are equal or only 1 item exists.
        """
        if not scores:
            return {}
        values = list(scores.values())
        min_val = min(values)
        max_val = max(values)
        
        # Guard against zero-division / tie scores
        if max_val == min_val:
            return {k: 1.0 if max_val > 0 else 0.0 for k in scores}
            
        return {k: (v - min_val) / (max_val - min_val) for k, v in scores.items()}

    def _semantic_search(self, query: str, k: int) -> Dict[int, float]:
        """Execute semantic search against FAISS."""
        query_vector = self.model.encode([query], normalize_embeddings=True).astype('float32')
        distances, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        
        results = {}
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                # Inner product with L2 normalized vectors = Cosine similarity in [-1, 1]
                similarity = (dist + 1.0) / 2.0
                results[int(idx)] = max(0.0, min(1.0, float(similarity)))
        return results

    def _keyword_search(self, query: str, k: int) -> Dict[int, float]:
        """Execute BM25 keyword matching."""
        tokens = self.clean_query(query)
        if not tokens or self.bm25 is None:
            return {}
            
        bm25_scores = self.bm25.get_scores(tokens)
        top_indices = np.argsort(bm25_scores)[::-1][:k]
        
        results = {}
        for idx in top_indices:
            score = float(bm25_scores[idx])
            if score > 0:
                results[int(idx)] = score
        return results

    def _extract_document_fields(self, row: pd.Series) -> Dict[str, str]:
        """Safely extract document attributes."""
        def safe_get(field: str, default: str = "") -> str:
            val = row.get(field, default)
            if pd.isna(val) or str(val).strip() in ["", "nan", "None"]:
                return default
            return str(val).strip()
            
        title = safe_get('Final_Title') or safe_get('Scraped_Title', 'Untitled Resource')
        summary = safe_get('AI_Summary') or safe_get('Scraped_Context', 'No summary available.')
        insights = safe_get('Key_Insights') or summary
        
        return {
            'title': title[:200],
            'link': safe_get('URL', '#'),
            'type': safe_get('Resource_Type', 'Academic Resource'),
            'category': safe_get('Enriched_Category', 'General'),
            'topic': safe_get('Enriched_Topic', 'General Topic'),
            'summary': summary[:1000],
            'insights': insights[:500],
            'context': safe_get('Scraped_Context', '')[:1000],
        }

    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        type_filter: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic vectors and BM25 keywords.
        """
        if self.model is None or self.index is None:
            self._load_resources()
            
        self._total_searches += 1
        cache_key = f"{query}_{top_k}_{type_filter}"
        if use_cache and cache_key in self._search_cache:
            self._cache_hits += 1
            return self._search_cache[cache_key]
            
        num_candidates = min(MAX_CANDIDATES, max(top_k * 3, 10))
        
        # 1. Candidate Generation
        semantic_scores = self._semantic_search(query, num_candidates)
        keyword_scores = self._keyword_search(query, num_candidates)
        
        # 2. Score Normalization
        sem_norm = self._normalize_scores(semantic_scores)
        key_norm = self._normalize_scores(keyword_scores)
        
        # 3. Hybrid Fusion
        all_indices = set(sem_norm.keys()) | set(key_norm.keys())
        final_scores = {}
        for idx in all_indices:
            s_score = sem_norm.get(idx, 0.0)
            k_score = key_norm.get(idx, 0.0)
            final_scores[idx] = (s_score * VECTOR_WEIGHT) + (k_score * BM25_WEIGHT)
            
        sorted_indices = sorted(final_scores, key=final_scores.get, reverse=True)
        
        # 4. Result Formatting & Filtering
        results = []
        for idx in sorted_indices:
            if len(results) >= top_k:
                break
            try:
                row = self.df.iloc[idx]
            except IndexError:
                continue
                
            if type_filter:
                row_type = str(row.get('Resource_Type', '')).lower()
                if type_filter.lower() not in row_type:
                    continue
                    
            fields = self._extract_document_fields(row)
            result = SearchResult(
                id=int(idx),
                score=float(final_scores[idx]),
                **fields
            )
            results.append(result.to_dict())
            
        if use_cache:
            if len(self._search_cache) > 200:
                self._search_cache.clear()
            self._search_cache[cache_key] = results
            
        return results

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.df) if self.df is not None else 0,
            "vector_count": self.index.ntotal if self.index else 0,
            "total_searches": self._total_searches,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": f"{(self._cache_hits / max(1, self._total_searches)):.1%}",
        }

# Backward compatibility alias
Librarian = HybridSearchEngine

def main():
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else "Grothendieck"
    engine = HybridSearchEngine()
    print(f"\n🔍 Searching for: '{query}'")
    results = engine.search(query, top_k=5)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['title']} (Score: {r['score']})")
        print(f"    Type: {r['type']} | Topic: {r['topic']}")
        print(f"    Link: {r['link']}")
        print(f"    Summary: {r['summary'][:160]}...")

if __name__ == "__main__":
    main()
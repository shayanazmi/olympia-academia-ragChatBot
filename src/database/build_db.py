"""
Database Builder for Olympia Academia
Builds FAISS vector index and BM25 keyword index from processed data or seed dataset.
"""

import os
import re
import pickle
import logging
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from src.utils.config import (
    PROJECT_ROOT,
    DATA_DIR,
    PROCESSED_DATA_DIR,
    DB_DIR,
    FAISS_INDEX_PATH,
    BM25_INDEX_PATH,
    DOCUMENTS_PATH,
    ENRICHED_DATA_PATH,
    CLEANED_DATA_PATH,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
)
from src.database.seed_data import get_seed_dataframe

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ %(levelname)-8s │ %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 32

def clean_text(text):
    """Clean text for better keyword matching."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\-\.]', '', text)
    return text.strip()

def create_search_context(row):
    """
    Create rich search context combining multiple fields.
    Weights different fields differently for better retrieval.
    """
    components = []
    
    # Title gets highest weight (repeat 3x)
    title = str(row.get('Final_Title', '')).strip()
    if not title or title == 'nan':
        title = str(row.get('Scraped_Title', '')).strip()
    if title and title != 'nan':
        components.extend([title] * 3)
    
    # Topic gets medium weight (repeat 2x)
    topic = str(row.get('Enriched_Topic', '')).strip()
    if topic and topic != 'nan':
        components.extend([topic] * 2)
    
    # Keywords get medium weight (repeat 2x)
    keywords = str(row.get('Keywords', '')).strip()
    if keywords and keywords != 'nan':
        components.extend([keywords] * 2)
    
    # Context / Summary gets normal weight
    context = str(row.get('Scraped_Context', '')).strip()
    if not context or context == 'nan':
        context = str(row.get('AI_Summary', '')).strip()
    if context and context != 'nan':
        components.append(context[:2000])
    
    # Resource type for categorical matching
    resource_type = str(row.get('Resource_Type', '')).strip()
    if resource_type and resource_type != 'nan':
        components.append(f"Type: {resource_type}")
    
    return ' '.join(components)

class DatabaseBuilder:
    """Handles the construction of search indices."""
    
    def __init__(self, input_file: Optional[Path] = None, use_sample: bool = False):
        self.input_file = input_file
        self.use_sample = use_sample
        self.model = None
        self.master_df = None
        self.embeddings = None
        
    def load_data(self):
        """Load and prepare data from file or seed generator."""
        if self.use_sample:
            logger.info("🌱 Generating database from curated sample seed data...")
            self.master_df = get_seed_dataframe()
            logger.info(f"   Loaded {len(self.master_df)} curated academic records")
            return

        target_file = self.input_file or ENRICHED_DATA_PATH
        
        # If default enriched file doesn't exist, try cleaned or fallback to sample
        if not target_file.exists():
            if CLEANED_DATA_PATH.exists():
                logger.info(f"⚠️ Enriched data not found; falling back to cleaned data: {CLEANED_DATA_PATH}")
                target_file = CLEANED_DATA_PATH
            else:
                logger.warning(f"⚠️ No processed data file found at {target_file}. Falling back to sample seed dataset!")
                self.master_df = get_seed_dataframe()
                logger.info(f"   Loaded {len(self.master_df)} curated academic records")
                return

        logger.info(f"📂 Loading enriched data from: {target_file}")
        try:
            xls = pd.read_excel(target_file, sheet_name=None)
            if len(xls) == 1:
                self.master_df = list(xls.values())[0]
            else:
                df_list = [df for df in xls.values()]
                self.master_df = pd.concat(df_list, ignore_index=True)
            logger.info(f"   Loaded {len(self.master_df)} rows from Excel")
        except Exception as e:
            logger.error(f"❌ Error reading Excel: {e}. Using seed sample dataset instead.")
            self.master_df = get_seed_dataframe()

    def filter_and_enrich(self):
        """Filter active links and create search contexts."""
        logger.info("🔍 Filtering and formatting search contexts...")
        
        # Filter active links if status column exists
        if 'Link_Status' in self.master_df.columns:
            active_df = self.master_df[self.master_df['Link_Status'] == 'Active']
            if len(active_df) > 0:
                self.master_df = active_df
        
        # Deduplicate on URL
        if 'URL' in self.master_df.columns:
            self.master_df = self.master_df.drop_duplicates(subset=['URL'], keep='first')
        
        # Ensure standard columns exist with fallbacks
        for col in ['Final_Title', 'Scraped_Title', 'Resource_Type', 'Keywords', 'Enriched_Topic', 'Enriched_Category', 'Scraped_Context', 'AI_Summary', 'Key_Insights']:
            if col not in self.master_df.columns:
                self.master_df[col] = ""

        # Fill missing titles
        self.master_df['Final_Title'] = self.master_df['Final_Title'].replace('', np.nan).fillna(
            self.master_df['Scraped_Title'].replace('', np.nan)
        ).fillna('Untitled Academic Resource')

        # Create rich search context
        self.master_df['Search_Context'] = self.master_df.apply(create_search_context, axis=1)
        self.master_df['Search_Context_Clean'] = self.master_df['Search_Context'].apply(clean_text)
        
        # Filter empty contexts
        self.master_df = self.master_df[self.master_df['Search_Context_Clean'].str.len() > 5].copy()
        self.master_df.reset_index(drop=True, inplace=True)
        logger.info(f"✅ Final dataset: {len(self.master_df)} documents ready for indexing")

    def build_vector_index(self):
        """Build FAISS vector index for semantic search."""
        logger.info(f"🧠 Building FAISS vector index with {EMBEDDING_MODEL}...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        texts = self.master_df['Search_Context'].tolist()
        logger.info(f"   Encoding {len(texts)} documents...")
        
        self.embeddings = self.model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization so Inner Product = Cosine Similarity
        ).astype('float32')
        
        dimension = self.embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(self.embeddings)
        
        DB_DIR.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(FAISS_INDEX_PATH))
        logger.info(f"   ✅ FAISS index saved to {FAISS_INDEX_PATH} ({index.ntotal} vectors)")

    def build_bm25_index(self):
        """Build BM25 index for keyword search."""
        logger.info("📚 Building BM25 keyword index...")
        
        tokenized_corpus = [
            doc.split() for doc in self.master_df['Search_Context_Clean']
        ]
        
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_data = {
            'bm25': bm25,
            'tokenized_corpus': tokenized_corpus
        }
        
        with open(BM25_INDEX_PATH, 'wb') as f:
            pickle.dump(bm25_data, f)
        
        logger.info(f"   ✅ BM25 index saved to {BM25_INDEX_PATH}")

    def save_metadata(self):
        """Save document metadata for retrieval."""
        logger.info("💾 Saving document metadata store...")
        
        metadata_columns = [
            'URL', 'Final_Title', 'Scraped_Title', 'Resource_Type', 'Enriched_Topic',
            'Enriched_Category', 'Keywords', 'Scraped_Context', 'AI_Summary',
            'Key_Insights', 'Search_Context'
        ]
        columns_to_save = [c for c in metadata_columns if c in self.master_df.columns]
        metadata_df = self.master_df[columns_to_save].copy()
        
        with open(DOCUMENTS_PATH, 'wb') as f:
            pickle.dump(metadata_df, f)
            
        logger.info(f"   ✅ Metadata saved to {DOCUMENTS_PATH} ({len(metadata_df)} documents)")

    def build_all(self):
        """Run complete database construction pipeline."""
        logger.info("=" * 60)
        logger.info("🚀 OLYMPIA ACADEMIA DATABASE BUILDER")
        logger.info("=" * 60)
        
        self.load_data()
        self.filter_and_enrich()
        self.build_vector_index()
        self.build_bm25_index()
        self.save_metadata()
        
        logger.info("=" * 60)
        logger.info("🎉 DATABASE BUILD COMPLETE!")
        logger.info("=" * 60)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Olympia Academia search database")
    parser.add_argument('--sample', action='store_true', help="Build index using curated academic seed data")
    parser.add_argument('--input', type=str, help="Custom input Excel file path")
    args = parser.parse_args()
    
    input_path = Path(args.input) if args.input else None
    builder = DatabaseBuilder(input_file=input_path, use_sample=args.sample)
    builder.build_all()

if __name__ == "__main__":
    main()
"""
Database Builder for Olympia Academia
=====================================
Builds FAISS vector index and BM25 keyword index from processed data.

Author: Olympia Academia Team
"""

import pandas as pd
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import os
import re
from pathlib import Path
import logging
from tqdm import tqdm

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

# Path Configuration - Using absolute paths based on your structure
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"

# Ensure DB directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)

# File paths - matching your naming convention
INPUT_FILE = PROCESSED_DIR / "oa_final.xlsx"
VECTOR_DB_PATH = DB_DIR / "olympia_vectors.index"
BM25_PATH = DB_DIR / "olympia_bm25.pkl"
METADATA_PATH = DB_DIR / "olympia_docs.pkl"  # Changed from olympia_metadata.pkl for consistency

# Model Configuration
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Fast & Good
EMBEDDING_DIMENSION = 384
BATCH_SIZE = 32  # For embedding generation

# ==========================================
# TEXT PROCESSING
# ==========================================

def clean_text(text):
    """Clean text for better keyword matching."""
    if pd.isna(text):
        return ""
    # Keep alphanumeric, spaces, and some punctuation for context
    text = str(text).lower()
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    text = re.sub(r'[^\w\s\-\.]', '', text)  # Keep words, spaces, hyphens, periods
    return text.strip()

def create_search_context(row):
    """
    Create rich search context combining multiple fields.
    Weights different fields differently for better retrieval.
    """
    components = []
    
    # Title gets highest weight (repeat 3x)
    title = str(row.get('Final_Title', '')).strip()
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
    
    # Context/Summary gets normal weight
    context = str(row.get('Scraped_Context', '')).strip()
    if context and context != 'nan':
        components.append(context[:1000])  # Limit context length
    
    # Resource type for categorical matching
    resource_type = str(row.get('Resource_Type', '')).strip()
    if resource_type and resource_type != 'nan':
        components.append(f"Type: {resource_type}")
    
    return ' '.join(components)

# ==========================================
# DATABASE BUILDER
# ==========================================

class DatabaseBuilder:
    """Handles the construction of search indices."""
    
    def __init__(self):
        self.model = None
        self.master_df = None
        self.embeddings = None
        
    def load_data(self):
        """Load and prepare the enriched data."""
        logger.info(f"📂 Loading enriched data from: {INPUT_FILE}")
        
        if not INPUT_FILE.exists():
            raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
        
        try:
            # Load all sheets if multiple exist
            xls = pd.read_excel(INPUT_FILE, sheet_name=None)
            
            if len(xls) == 1:
                # Single sheet
                self.master_df = list(xls.values())[0]
                logger.info(f"   Loaded single sheet with {len(self.master_df)} rows")
            else:
                # Multiple sheets - concatenate
                df_list = []
                for sheet_name, df in xls.items():
                    logger.info(f"   Loading sheet '{sheet_name}': {len(df)} rows")
                    df_list.append(df)
                self.master_df = pd.concat(df_list, ignore_index=True)
                logger.info(f"   Combined total: {len(self.master_df)} rows")
                
        except Exception as e:
            logger.error(f"❌ Error reading Excel: {e}")
            raise
    
    def filter_and_enrich(self):
        """Filter active links and create search contexts."""
        logger.info("🔍 Filtering and enriching data...")
        
        initial_count = len(self.master_df)
        
        # Filter active links only
        if 'Link_Status' in self.master_df.columns:
            self.master_df = self.master_df[self.master_df['Link_Status'] == 'Active']
            logger.info(f"   Filtered to {len(self.master_df)} active links")
        
        # Remove duplicates based on URL
        if 'URL' in self.master_df.columns:
            before_dedup = len(self.master_df)
            self.master_df = self.master_df.drop_duplicates(subset=['URL'], keep='first')
            if before_dedup != len(self.master_df):
                logger.info(f"   Removed {before_dedup - len(self.master_df)} duplicate URLs")
        
        # Fill missing values intelligently
        self.master_df['Final_Title'] = self.master_df['Final_Title'].fillna(
            self.master_df.get('Scraped_Title', pd.Series())
        )
        self.master_df['Resource_Type'] = self.master_df['Resource_Type'].fillna('Web Resource')
        self.master_df['Keywords'] = self.master_df['Keywords'].fillna('')
        self.master_df['Enriched_Topic'] = self.master_df['Enriched_Topic'].fillna('')
        
        # Create rich search context
        logger.info("   Creating search contexts...")
        self.master_df['Search_Context'] = self.master_df.apply(create_search_context, axis=1)
        
        # Create clean version for BM25
        self.master_df['Search_Context_Clean'] = self.master_df['Search_Context'].apply(clean_text)
        
        # Remove empty contexts
        before_filter = len(self.master_df)
        self.master_df = self.master_df[self.master_df['Search_Context_Clean'].str.len() > 10]
        if before_filter != len(self.master_df):
            logger.info(f"   Removed {before_filter - len(self.master_df)} empty entries")
        
        logger.info(f"✅ Final dataset: {len(self.master_df)} documents ready for indexing")
    
    def build_vector_index(self):
        """Build FAISS vector index for semantic search."""
        logger.info(f"🧠 Building vector index with {EMBEDDING_MODEL}...")
        
        # Initialize model
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Generate embeddings in batches
        texts = self.master_df['Search_Context'].tolist()
        logger.info(f"   Encoding {len(texts)} documents...")
        
        self.embeddings = self.model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        
        # Convert to float32 for FAISS
        self.embeddings = np.array(self.embeddings).astype('float32')
        
        # Create FAISS index
        dimension = self.embeddings.shape[1]
        
        # Using IndexFlatIP for inner product (equivalent to cosine similarity when normalized)
        index = faiss.IndexFlatIP(dimension)
        
        # Add vectors to index
        index.add(self.embeddings)
        
        # Save index
        faiss.write_index(index, str(VECTOR_DB_PATH))
        logger.info(f"   ✅ FAISS index saved to {VECTOR_DB_PATH}")
        logger.info(f"   Index contains {index.ntotal} vectors of dimension {dimension}")
    
    def build_bm25_index(self):
        """Build BM25 index for keyword search."""
        logger.info("📚 Building BM25 keyword index...")
        
        # Tokenize documents
        tokenized_corpus = [
            doc.split() for doc in self.master_df['Search_Context_Clean']
        ]
        
        # Build BM25 index
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Save BM25 index
        with open(BM25_PATH, 'wb') as f:
            pickle.dump(bm25, f)
        
        # Also save the tokenized corpus for query processing
        bm25_data = {
            'bm25': bm25,
            'tokenized_corpus': tokenized_corpus
        }
        
        with open(BM25_PATH, 'wb') as f:
            pickle.dump(bm25_data, f)
        
        logger.info(f"   ✅ BM25 index saved to {BM25_PATH}")
        
        # Calculate and log statistics
        avg_doc_length = np.mean([len(doc) for doc in tokenized_corpus])
        logger.info(f"   Average document length: {avg_doc_length:.1f} tokens")
    
    def save_metadata(self):
        """Save document metadata for retrieval."""
        logger.info("💾 Saving document metadata...")
        
        # Select relevant columns for storage
        metadata_columns = [
            'URL', 'Final_Title', 'Resource_Type', 'Enriched_Topic',
            'Keywords', 'Scraped_Context', 'Search_Context'
        ]
        
        # Keep only existing columns
        columns_to_save = [col for col in metadata_columns if col in self.master_df.columns]
        metadata_df = self.master_df[columns_to_save].copy()
        
        # Add index for reference
        metadata_df.reset_index(drop=True, inplace=True)
        
        # Save as pickle
        with open(METADATA_PATH, 'wb') as f:
            pickle.dump(metadata_df, f)
        
        logger.info(f"   ✅ Metadata saved to {METADATA_PATH}")
        logger.info(f"   Saved {len(metadata_df)} documents with {len(columns_to_save)} fields each")
    
    def build_all(self):
        """Run the complete database building pipeline."""
        logger.info("="*60)
        logger.info("🚀 OLYMPIA ACADEMIA DATABASE BUILDER")
        logger.info("="*60)
        
        try:
            # Step 1: Load data
            self.load_data()
            
            # Step 2: Filter and enrich
            self.filter_and_enrich()
            
            # Step 3: Build vector index
            self.build_vector_index()
            
            # Step 4: Build BM25 index
            self.build_bm25_index()
            
            # Step 5: Save metadata
            self.save_metadata()
            
            # Summary
            logger.info("="*60)
            logger.info("🎉 DATABASE BUILD COMPLETE!")
            logger.info("="*60)
            logger.info("Generated files:")
            logger.info(f"  📁 {VECTOR_DB_PATH.name} ({VECTOR_DB_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
            logger.info(f"  📁 {BM25_PATH.name} ({BM25_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
            logger.info(f"  📁 {METADATA_PATH.name} ({METADATA_PATH.stat().st_size / 1024 / 1024:.1f} MB)")
            logger.info("")
            logger.info("Next step: Run 'streamlit run app.py' to start the chatbot")
            
        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            raise

# ==========================================
# UTILITY FUNCTIONS
# ==========================================

def verify_database():
    """Verify that all database files exist and are valid."""
    logger.info("🔍 Verifying database integrity...")
    
    issues = []
    
    # Check FAISS index
    if not VECTOR_DB_PATH.exists():
        issues.append(f"Missing FAISS index: {VECTOR_DB_PATH}")
    else:
        try:
            index = faiss.read_index(str(VECTOR_DB_PATH))
            logger.info(f"   ✓ FAISS index: {index.ntotal} vectors")
        except Exception as e:
            issues.append(f"Invalid FAISS index: {e}")
    
    # Check BM25 index
    if not BM25_PATH.exists():
        issues.append(f"Missing BM25 index: {BM25_PATH}")
    else:
        try:
            with open(BM25_PATH, 'rb') as f:
                bm25_data = pickle.load(f)
            logger.info(f"   ✓ BM25 index loaded successfully")
        except Exception as e:
            issues.append(f"Invalid BM25 index: {e}")
    
    # Check metadata
    if not METADATA_PATH.exists():
        issues.append(f"Missing metadata: {METADATA_PATH}")
    else:
        try:
            with open(METADATA_PATH, 'rb') as f:
                metadata = pickle.load(f)
            logger.info(f"   ✓ Metadata: {len(metadata)} documents")
        except Exception as e:
            issues.append(f"Invalid metadata: {e}")
    
    if issues:
        logger.error("❌ Database verification failed:")
        for issue in issues:
            logger.error(f"   - {issue}")
        return False
    else:
        logger.info("✅ All database files verified successfully")
        return True

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build Olympia Academia search database")
    parser.add_argument('--verify', action='store_true', help="Verify existing database")
    parser.add_argument('--input', type=str, help="Custom input file path")
    
    args = parser.parse_args()
    
    if args.verify:
        verify_database()
    else:
        if args.input:
            global INPUT_FILE
            INPUT_FILE = Path(args.input)
        
        builder = DatabaseBuilder()
        builder.build_all()

if __name__ == "__main__":
    main()
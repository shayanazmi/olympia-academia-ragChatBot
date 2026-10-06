"""
Olympia Academia - Data Ingestion Module
=========================================

This module provides tools for extracting, cleaning, and ingesting content
from various sources including WhatsApp chats, YouTube videos, and web pages.

Components:
-----------
- LinkExtractor: Extract links from WhatsApp chat exports
- LinkCleaner: Validate and clean extracted links
- UniversalIngestor: Scrape content from YouTube and web sources

Typical workflow:
----------------
1. Extract links from WhatsApp chats using LinkExtractor
2. Clean and validate links using LinkCleaner
3. Ingest content from links using UniversalIngestor

Example:
--------
>>> from src.ingestion import LinkExtractor, LinkCleaner, UniversalIngestor
>>> 
>>> # Extract links
>>> extractor = LinkExtractor()
>>> extractor.process_all()
>>> extractor.save()
>>> 
>>> # Clean links
>>> cleaner = LinkCleaner()
>>> cleaner.run()
>>> 
>>> # Ingest content
>>> ingestor = UniversalIngestor()
>>> results = ingestor.ingest_batch(urls)

Author: Olympia Academia Team
License: MIT
"""

# Version info
__version__ = "1.0.0"
__author__ = "Olympia Academia Team"

# ==========================================
# IMPORTS
# ==========================================

# From link_extractor.py
from .link_extractor import (
    WhatsAppLinkExtractor,
    WhatsAppLinkExtractor as LinkExtractor,  # Alias for backward compatibility
    ExtractedLink,
    CHAT_FILES,
    OUTPUT_EXCEL,
    OUTPUT_CSV,
    OUTPUT_JSON,
)

# From cleaner.py
from .cleaner import (
    LinkCleaner,
    URLValidator,
    ValidationResult,
    BackupManager,
    SafeExcelWriter,
    INPUT_FILE as CLEANER_INPUT,
    WORK_FILE,
    OUTPUT_FILE as CLEANER_OUTPUT,
)

# From universal_ingestor.py
from .universal_ingestor import (
    get_youtube_transcript,
    get_website_content,
    process_links_batch,
)

# ==========================================
# MODULE CONFIGURATION
# ==========================================

import logging
from pathlib import Path

# Setup module logger
logger = logging.getLogger(__name__)

# Define module paths
MODULE_DIR = Path(__file__).parent
PROJECT_ROOT = MODULE_DIR.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================

def extract_whatsapp_links(
    chat_files=None,
    output_dir=None,
    deduplicate=True,
    formats=None
):
    """
    Convenience function to extract links from WhatsApp chats.
    
    Args:
        chat_files: List of chat file paths (default: configured files)
        output_dir: Output directory path (default: data/raw/)
        deduplicate: Whether to remove duplicate links (default: True)
        formats: Output formats ['excel', 'csv', 'json'] (default: ['excel', 'csv'])
    
    Returns:
        DataFrame of extracted links
    
    Example:
        >>> df = extract_whatsapp_links()
        >>> print(f"Extracted {len(df)} unique links")
    """
    extractor = WhatsAppLinkExtractor(chat_files)
    extractor.process_all()
    
    if deduplicate:
        extractor.deduplicate()
    
    if output_dir:
        output_path = Path(output_dir)
        extractor.save(
            excel_path=output_path / "whatsapp_links.xlsx",
            csv_path=output_path / "whatsapp_links.csv",
            json_path=output_path / "whatsapp_links.json",
            formats=formats or ['excel', 'csv']
        )
    else:
        extractor.save(formats=formats or ['excel', 'csv'])
    
    extractor.print_summary()
    return extractor.to_dataframe()


def validate_links(
    input_file=None,
    output_file=None,
    max_workers=5
):
    """
    Convenience function to validate and clean links.
    
    Args:
        input_file: Path to input Excel file (default: data/raw/whatsapp_links_unique.xlsx)
        output_file: Path to output file (default: data/processed/oa_cleaned.xlsx)
        max_workers: Number of concurrent workers (default: 5)
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> success = validate_links()
        >>> if success:
        ...     print("Links validated successfully")
    """
    from pathlib import Path
    
    cleaner = LinkCleaner(
        input_file=Path(input_file) if input_file else CLEANER_INPUT,
        output_file=Path(output_file) if output_file else CLEANER_OUTPUT
    )
    
    return cleaner.run()


def ingest_urls(
    urls,
    output_file=None,
    max_workers=5,
    show_progress=True
):
    """
    Convenience function to ingest content from URLs.
    
    Args:
        urls: List of URLs or path to file containing URLs
        output_file: Optional JSON output file path
        max_workers: Number of concurrent workers (default: 5)
        show_progress: Whether to show progress bar (default: True)
    
    Returns:
        List of IngestedContent objects
    
    Example:
        >>> results = ingest_urls(['https://youtube.com/watch?v=...'])
        >>> for r in results:
        ...     if r.success:
        ...         print(f"{r.title}: {r.word_count} words")
    """
    import json
    from pathlib import Path
    
    # Handle file input
    if isinstance(urls, (str, Path)):
        urls_path = Path(urls)
        if urls_path.exists():
            with open(urls_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
    
    # Initialize ingestor
    ingestor = UniversalIngestor()
    
    # Process URLs
    results = list(ingestor.ingest_batch(
        urls, 
        max_workers=max_workers,
        progress_callback=(lambda c, t: print(f"Progress: {c}/{t}")) if show_progress else None
    ))
    
    # Save if output specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                [r.to_dict() for r in results],
                f,
                indent=2,
                ensure_ascii=False
            )
        logger.info(f"Results saved to {output_file}")
    
    # Print summary
    stats = ingestor.get_stats()
    logger.info(
        f"Ingestion complete: {stats['success']} success, "
        f"{stats['failed']} failed, {stats['skipped']} skipped"
    )
    
    return results


def run_full_pipeline(
    chat_files=None,
    skip_extraction=False,
    skip_cleaning=False,
    skip_ingestion=False,
    max_workers=5
):
    """
    Run the complete ingestion pipeline.
    
    Args:
        chat_files: List of WhatsApp chat files (default: configured files)
        skip_extraction: Skip link extraction step (default: False)
        skip_cleaning: Skip link cleaning step (default: False)
        skip_ingestion: Skip content ingestion step (default: False)
        max_workers: Number of concurrent workers (default: 5)
    
    Returns:
        Dictionary with pipeline results
    
    Example:
        >>> results = run_full_pipeline()
        >>> print(f"Pipeline completed: {results['total_ingested']} items processed")
    """
    results = {
        'extraction': None,
        'cleaning': None,
        'ingestion': None,
        'total_links': 0,
        'valid_links': 0,
        'total_ingested': 0
    }
    
    try:
        # Step 1: Extract links
        if not skip_extraction:
            logger.info("="*60)
            logger.info("STEP 1: EXTRACTING LINKS FROM WHATSAPP")
            logger.info("="*60)
            df = extract_whatsapp_links(chat_files)
            results['extraction'] = len(df)
            results['total_links'] = len(df)
        
        # Step 2: Clean and validate links
        if not skip_cleaning:
            logger.info("\n" + "="*60)
            logger.info("STEP 2: VALIDATING AND CLEANING LINKS")
            logger.info("="*60)
            success = validate_links(max_workers=max_workers)
            results['cleaning'] = success
            
            # Count valid links
            if success and CLEANER_OUTPUT.exists():
                import pandas as pd
                df_clean = pd.read_excel(CLEANER_OUTPUT)
                results['valid_links'] = len(df_clean)
        
        # Step 3: Ingest content
        if not skip_ingestion:
            logger.info("\n" + "="*60)
            logger.info("STEP 3: INGESTING CONTENT FROM URLS")
            logger.info("="*60)
            
            # Load cleaned URLs
            if CLEANER_OUTPUT.exists():
                import pandas as pd
                df_clean = pd.read_excel(CLEANER_OUTPUT)
                urls = df_clean['Link'].tolist() if 'Link' in df_clean.columns else []
                
                if urls:
                    ingested = ingest_urls(
                        urls,
                        output_file=PROCESSED_DIR / "ingested_content.json",
                        max_workers=max_workers
                    )
                    results['ingestion'] = ingested
                    results['total_ingested'] = len([r for r in ingested if r.success])
                else:
                    logger.warning("No URLs found to ingest")
            else:
                logger.warning(f"Cleaned file not found: {CLEANER_OUTPUT}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*60)
        logger.info(f"Links Extracted:  {results['total_links']}")
        logger.info(f"Valid Links:      {results['valid_links']}")
        logger.info(f"Content Ingested: {results['total_ingested']}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    
    return results

# ==========================================
# PIPELINE CLASS (ALTERNATIVE INTERFACE)
# ==========================================

class IngestionPipeline:
    """
    High-level interface for the complete ingestion pipeline.
    
    This class provides a convenient way to run the entire ingestion
    process with configuration and state management.
    
    Example:
        >>> pipeline = IngestionPipeline()
        >>> pipeline.configure(max_workers=10)
        >>> pipeline.run()
    """
    
    def __init__(self):
        self.extractor = None
        self.cleaner = None
        self.ingestor = None
        self.config = {
            'max_workers': 5,
            'deduplicate': True,
            'output_formats': ['excel', 'csv'],
            'chat_files': None
        }
        self.results = {}
    
    def configure(self, **kwargs):
        """
        Configure pipeline settings.
        
        Args:
            max_workers: Number of concurrent workers
            deduplicate: Whether to remove duplicate links
            output_formats: List of output formats
            chat_files: List of chat files to process
        """
        self.config.update(kwargs)
        return self
    
    def extract_links(self):
        """Run link extraction step."""
        logger.info("Running link extraction...")
        self.extractor = WhatsAppLinkExtractor(self.config.get('chat_files'))
        self.extractor.process_all()
        
        if self.config.get('deduplicate'):
            self.extractor.deduplicate()
        
        self.extractor.save(formats=self.config.get('output_formats'))
        self.results['extraction'] = self.extractor.to_dataframe()
        return self
    
    def clean_links(self):
        """Run link cleaning step."""
        logger.info("Running link validation...")
        self.cleaner = LinkCleaner()
        success = self.cleaner.run()
        self.results['cleaning'] = success
        return self
    
    def ingest_content(self):
        """Run content ingestion step."""
        logger.info("Running content ingestion...")
        
        # Load cleaned URLs
        if CLEANER_OUTPUT.exists():
            import pandas as pd
            df = pd.read_excel(CLEANER_OUTPUT)
            urls = df['Link'].tolist() if 'Link' in df.columns else []
            
            self.ingestor = UniversalIngestor()
            results = list(self.ingestor.ingest_batch(
                urls,
                max_workers=self.config.get('max_workers')
            ))
            self.results['ingestion'] = results
        
        return self
    
    def run(self, steps=None):
        """
        Run specified pipeline steps.
        
        Args:
            steps: List of steps to run ['extract', 'clean', 'ingest']
                   If None, runs all steps.
        
        Returns:
            Pipeline results dictionary
        """
        steps = steps or ['extract', 'clean', 'ingest']
        
        if 'extract' in steps:
            self.extract_links()
        
        if 'clean' in steps:
            self.clean_links()
        
        if 'ingest' in steps:
            self.ingest_content()
        
        return self.results
    
    def get_statistics(self):
        """Get pipeline execution statistics."""
        stats = {
            'links_extracted': 0,
            'links_validated': 0,
            'content_ingested': 0,
            'success_rate': 0
        }
        
        if 'extraction' in self.results:
            stats['links_extracted'] = len(self.results['extraction'])
        
        if 'cleaning' in self.results:
            stats['links_validated'] = self.cleaner.stats['active'] if self.cleaner else 0
        
        if 'ingestion' in self.results:
            stats['content_ingested'] = len([
                r for r in self.results['ingestion'] 
                if r.success
            ])
            
            total = len(self.results['ingestion'])
            if total > 0:
                stats['success_rate'] = stats['content_ingested'] / total
        
        return stats

# ==========================================
# MODULE EXPORTS
# ==========================================

__all__ = [
    # Main classes
    'WhatsAppLinkExtractor',
    'LinkExtractor',
    'LinkCleaner',
    'UniversalIngestor',
    'IngestionPipeline',
    
    # Data classes
    'ExtractedLink',
    'IngestedContent',
    'ValidationResult',
    
    # Scrapers
    'BaseScraper',
    'YouTubeScraper',
    'WebScraper',
    
    # Utilities
    'URLValidator',
    'BackupManager',
    'SafeExcelWriter',
    
    # Convenience functions
    'extract_whatsapp_links',
    'validate_links',
    'ingest_urls',
    'run_full_pipeline',
    
    # Constants
    'CHAT_FILES',
    'OUTPUT_EXCEL',
    'OUTPUT_CSV',
    'OUTPUT_JSON',
    'WORK_FILE',
    'DEFAULT_HEADERS',
    'REQUEST_TIMEOUT',
    'MAX_WORKERS',
]

# ==========================================
# MODULE INITIALIZATION
# ==========================================

def _initialize_module():
    """Initialize module on import."""
    # Ensure required directories exist
    for directory in [RAW_DIR, PROCESSED_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"Ingestion module initialized: v{__version__}")

# Run initialization
_initialize_module()
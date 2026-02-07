"""
Link Cleaner & Validator for Olympia Academia
==============================================
Validates links, detects dead URLs, and scrapes basic metadata.

Features:
- Concurrent URL validation
- Dead link detection (404, removed videos)
- Basic metadata scraping (title, description)
- Automatic backup system
- Progress resumption

Author: Olympia Academia Team
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import shutil
import concurrent.futures
from datetime import datetime
from pathlib import Path
import logging
from typing import Tuple, Dict, Optional, List
from dataclasses import dataclass

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

# Path Configuration - Updated for new project structure
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BACKUP_DIR = DATA_DIR / "backups"

# Ensure directories exist
for dir_path in [RAW_DIR, PROCESSED_DIR, BACKUP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# File paths
INPUT_FILE = RAW_DIR / "whatsapp_links_unique.xlsx"  # From link_extractor.py
WORK_FILE = PROCESSED_DIR / "oa_cleaning_progress.xlsx"
OUTPUT_FILE = PROCESSED_DIR / "oa_cleaned.xlsx"

# Processing Configuration
MAX_WORKERS = 5
REQUEST_TIMEOUT = 15
BATCH_SAVE_SIZE = 20
MAX_RETRIES = 3
RETRY_DELAY = 5

# User-Agent Rotation (To avoid 403 blocks)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# Dead link indicators
YOUTUBE_DEAD_INDICATORS = [
    "Video unavailable",
    "This video has been removed",
    "This video is private",
    "This video is no longer available",
    "Sign in to confirm your age",
    "This video may be inappropriate"
]

# ==========================================
# DATA CLASSES
# ==========================================

@dataclass
class ValidationResult:
    """Result of URL validation."""
    status: str
    title: str
    context: str
    error: Optional[str] = None
    
    def is_active(self) -> bool:
        return self.status == "Active"

# ==========================================
# SAFETY SYSTEMS
# ==========================================

class BackupManager:
    """Handles file backups and recovery."""
    
    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, filepath: Path) -> Optional[Path]:
        """Creates a timestamped backup of the file."""
        if not filepath.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{timestamp}_{filepath.name}"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(filepath, backup_path)
            logger.info(f"🛡️ Backup created: {backup_path.name}")
            return backup_path
        except Exception as e:
            logger.error(f"⚠️ Backup failed: {e}")
            return None
    
    def cleanup_old_backups(self, keep_latest: int = 5):
        """Remove old backups, keeping only the latest N."""
        backups = sorted(self.backup_dir.glob("*.xlsx"), reverse=True)
        for backup in backups[keep_latest:]:
            try:
                backup.unlink()
                logger.debug(f"Removed old backup: {backup.name}")
            except Exception:
                pass

class SafeExcelWriter:
    """Safely writes Excel files with retry logic."""
    
    @staticmethod
    def save(sheets_dict: Dict[str, pd.DataFrame], filepath: Path) -> bool:
        """
        Save Excel file with retries for permission errors.
        
        Args:
            sheets_dict: Dictionary of sheet_name -> DataFrame
            filepath: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(MAX_RETRIES):
            try:
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    for name, data in sheets_dict.items():
                        # Truncate sheet name if too long
                        safe_name = name[:31] if len(name) > 31 else name
                        data.to_excel(writer, sheet_name=safe_name, index=False)
                logger.info("💾 Progress saved")
                return True
            except PermissionError:
                logger.warning(
                    f"⚠️ File is open in another program. "
                    f"Retry {attempt + 1}/{MAX_RETRIES} in {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)
            except Exception as e:
                logger.error(f"⚠️ Save error: {e}")
                return False
        
        logger.error("❌ Failed to save after all retries")
        return False

# ==========================================
# URL VALIDATION
# ==========================================

class URLValidator:
    """Validates URLs and extracts metadata."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def _get_random_ua(self) -> str:
        """Get a random User-Agent."""
        return random.choice(USER_AGENTS)
    
    def _is_youtube_url(self, url: str) -> bool:
        """Check if URL is a YouTube link."""
        return any(domain in url.lower() for domain in ['youtube.com', 'youtu.be'])
    
    def _check_youtube_dead(self, html: str) -> bool:
        """Check if YouTube video is dead/unavailable."""
        return any(indicator in html for indicator in YOUTUBE_DEAD_INDICATORS)
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Tuple[str, str]:
        """Extract title and description from HTML."""
        # Title extraction
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        
        # Try Open Graph title as fallback
        if not title:
            og_title = soup.find('meta', attrs={'property': 'og:title'})
            if og_title:
                title = og_title.get('content', '').strip()
        
        # Description extraction
        description = ""
        
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        
        # Try Open Graph description as fallback
        if not description:
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                description = og_desc.get('content', '').strip()
        
        # Limit description length
        description = description[:500] if description else ""
        
        return title, description
    
    def validate(self, url: str) -> ValidationResult:
        """
        Validate a URL and extract metadata.
        
        Args:
            url: URL to validate
            
        Returns:
            ValidationResult with status, title, and context
        """
        # Check for invalid/empty URLs
        if pd.isna(url) or not str(url).strip():
            return ValidationResult("Invalid_URL", "", "", "Empty or null URL")
        
        url = str(url).strip()
        
        if not url.startswith(('http://', 'https://')):
            return ValidationResult("Invalid_URL", "", "", "Missing protocol")
        
        try:
            headers = {'User-Agent': self._get_random_ua()}
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            
            # Check for YouTube-specific dead videos
            if self._is_youtube_url(url):
                if self._check_youtube_dead(response.text):
                    return ValidationResult(
                        "Inactive", 
                        "YouTube Video Unavailable", 
                        "",
                        "Video removed or unavailable"
                    )
            
            # Check HTTP status
            if response.status_code == 404:
                return ValidationResult("Inactive", "404 Not Found", "", "Page not found")
            
            if response.status_code >= 400:
                return ValidationResult(
                    f"Review_HTTP_{response.status_code}", 
                    "", 
                    "",
                    f"HTTP {response.status_code}"
                )
            
            if response.status_code != 200:
                return ValidationResult(
                    f"Review_HTTP_{response.status_code}",
                    "",
                    "",
                    f"Non-200 status: {response.status_code}"
                )
            
            # Parse and extract metadata
            soup = BeautifulSoup(response.text, 'html.parser')
            title, description = self._extract_metadata(soup)
            
            return ValidationResult("Active", title, description)
            
        except requests.exceptions.Timeout:
            return ValidationResult("Timeout", "", "", "Request timed out")
        
        except requests.exceptions.ConnectionError:
            return ValidationResult("Connection_Error", "", "", "Failed to connect")
        
        except requests.exceptions.TooManyRedirects:
            return ValidationResult("Too_Many_Redirects", "", "", "Redirect loop")
        
        except Exception as e:
            return ValidationResult("Error", "", "", str(e)[:100])

# ==========================================
# MAIN CLEANER CLASS
# ==========================================

class LinkCleaner:
    """
    Main class for cleaning and validating links.
    
    Workflow:
    1. Load input file (or resume from work file)
    2. Validate each unprocessed link
    3. Save progress periodically
    4. Generate final cleaned output
    """
    
    def __init__(
        self,
        input_file: Path = INPUT_FILE,
        work_file: Path = WORK_FILE,
        output_file: Path = OUTPUT_FILE
    ):
        self.input_file = input_file
        self.work_file = work_file
        self.output_file = output_file
        
        self.backup_manager = BackupManager(BACKUP_DIR)
        self.validator = URLValidator()
        self.sheets: Dict[str, pd.DataFrame] = {}
        
        # Statistics
        self.stats = {
            'total': 0,
            'active': 0,
            'inactive': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def initialize(self) -> bool:
        """Initialize the working environment."""
        # Check for existing work file (resume mode)
        if self.work_file.exists():
            logger.info(f"📄 Resuming from work file: {self.work_file.name}")
            self.backup_manager.create_backup(self.work_file)
            file_to_load = self.work_file
        
        # Start fresh from input file
        elif self.input_file.exists():
            logger.info(f"🆕 Starting fresh from: {self.input_file.name}")
            shutil.copy2(self.input_file, self.work_file)
            file_to_load = self.work_file
        
        else:
            logger.error(f"❌ Input file not found: {self.input_file}")
            return False
        
        # Load the Excel file
        try:
            xls = pd.read_excel(file_to_load, sheet_name=None)
            self.sheets = {name: df.copy() for name, df in xls.items()}
            logger.info(f"   Loaded {len(self.sheets)} sheet(s)")
            return True
        except Exception as e:
            logger.error(f"❌ Error loading Excel: {e}")
            return False
    
    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure required columns exist in DataFrame."""
        required_columns = ['Link_Status', 'Scraped_Title', 'Scraped_Context']
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""
        
        return df
    
    def _get_link_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the link column in DataFrame."""
        possible_names = ['Link', 'URL', 'link', 'url', 'Links', 'URLs']
        
        for name in possible_names:
            if name in df.columns:
                return name
        
        return None
    
    def process_sheet(self, sheet_name: str, df: pd.DataFrame) -> pd.DataFrame:
        """Process a single sheet."""
        logger.info(f"\n{'='*50}")
        logger.info(f"Processing Sheet: {sheet_name}")
        logger.info(f"{'='*50}")
        
        # Find link column
        link_col = self._get_link_column(df)
        if not link_col:
            logger.warning(f"⚠️ Skipping {sheet_name}: No 'Link' or 'URL' column found")
            self.stats['skipped'] += len(df)
            return df
        
        # Normalize column name
        if link_col != 'Link':
            df = df.rename(columns={link_col: 'Link'})
        
        # Ensure status columns exist
        df = self._ensure_columns(df)
        
        # Find rows needing validation
        pending_mask = df['Link_Status'].isna() | (df['Link_Status'] == "")
        pending_indices = df[pending_mask].index.tolist()
        total_pending = len(pending_indices)
        
        if total_pending == 0:
            logger.info("✅ All links already validated")
            return df
        
        logger.info(f"🚀 Validating {total_pending} pending links...")
        
        # Process with concurrent execution
        unsaved_changes = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all tasks
            future_to_idx = {
                executor.submit(self.validator.validate, df.at[idx, 'Link']): idx
                for idx in pending_indices
            }
            
            # Process results as they complete
            for i, future in enumerate(concurrent.futures.as_completed(future_to_idx)):
                idx = future_to_idx[future]
                
                try:
                    result = future.result()
                    
                    # Update DataFrame
                    df.at[idx, 'Link_Status'] = result.status
                    df.at[idx, 'Scraped_Title'] = result.title
                    df.at[idx, 'Scraped_Context'] = result.context
                    
                    # Update statistics
                    self.stats['total'] += 1
                    if result.is_active():
                        self.stats['active'] += 1
                        logger.info(f"[{i+1}/{total_pending}] ✅ Active: {result.title[:40]}...")
                    elif result.status == "Inactive":
                        self.stats['inactive'] += 1
                        logger.info(f"[{i+1}/{total_pending}] ❌ Dead: {df.at[idx, 'Link'][:50]}...")
                    else:
                        self.stats['errors'] += 1
                        logger.info(f"[{i+1}/{total_pending}] ⚠️ {result.status}")
                    
                    unsaved_changes += 1
                    
                except Exception as e:
                    logger.error(f"Error processing index {idx}: {e}")
                    df.at[idx, 'Link_Status'] = "Processing_Error"
                    self.stats['errors'] += 1
                
                # Periodic save
                if unsaved_changes >= BATCH_SAVE_SIZE:
                    self.sheets[sheet_name] = df
                    SafeExcelWriter.save(self.sheets, self.work_file)
                    unsaved_changes = 0
        
        return df
    
    def run(self):
        """Run the complete cleaning process."""
        logger.info("🧹 OLYMPIA ACADEMIA LINK CLEANER")
        logger.info("="*60)
        
        # Initialize
        if not self.initialize():
            return False
        
        # Process each sheet
        for sheet_name, df in self.sheets.items():
            processed_df = self.process_sheet(sheet_name, df)
            self.sheets[sheet_name] = processed_df
            
            # Save after each sheet
            SafeExcelWriter.save(self.sheets, self.work_file)
        
        # Generate final output
        self._generate_output()
        
        # Print summary
        self._print_summary()
        
        # Cleanup old backups
        self.backup_manager.cleanup_old_backups(keep_latest=5)
        
        return True
    
    def _generate_output(self):
        """Generate the final cleaned output file."""
        logger.info(f"\n📝 Generating final output: {self.output_file.name}")
        
        # Create output with only active links
        active_sheets = {}
        
        for sheet_name, df in self.sheets.items():
            if 'Link_Status' in df.columns:
                active_df = df[df['Link_Status'] == 'Active'].copy()
                if len(active_df) > 0:
                    active_sheets[sheet_name] = active_df
                    logger.info(f"   {sheet_name}: {len(active_df)} active links")
            else:
                active_sheets[sheet_name] = df
        
        if active_sheets:
            SafeExcelWriter.save(active_sheets, self.output_file)
            logger.info(f"✅ Clean output saved to: {self.output_file.name}")
    
    def _print_summary(self):
        """Print cleaning summary."""
        logger.info("\n" + "="*60)
        logger.info("📊 CLEANING SUMMARY")
        logger.info("="*60)
        logger.info(f"   Total Processed:  {self.stats['total']}")
        logger.info(f"   ✅ Active:        {self.stats['active']}")
        logger.info(f"   ❌ Inactive:      {self.stats['inactive']}")
        logger.info(f"   ⚠️ Errors:        {self.stats['errors']}")
        logger.info(f"   ⏭️ Skipped:       {self.stats['skipped']}")
        logger.info("="*60)
        
        if self.stats['active'] > 0:
            logger.info(f"\n🎉 Next step: Run batch_processor.py to enrich the data")

# ==========================================
# CLI INTERFACE
# ==========================================

def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean and validate links for Olympia Academia")
    parser.add_argument('--input', '-i', type=str, help="Custom input file path")
    parser.add_argument('--output', '-o', type=str, help="Custom output file path")
    parser.add_argument('--workers', '-w', type=int, default=MAX_WORKERS, help="Number of concurrent workers")
    
    args = parser.parse_args()
    
    # Override defaults if provided
    input_file = Path(args.input) if args.input else INPUT_FILE
    output_file = Path(args.output) if args.output else OUTPUT_FILE
    
    if args.workers:
        global MAX_WORKERS
        MAX_WORKERS = args.workers
    
    # Run cleaner
    cleaner = LinkCleaner(
        input_file=input_file,
        output_file=output_file
    )
    
    success = cleaner.run()
    
    if not success:
        exit(1)

if __name__ == "__main__":
    main()
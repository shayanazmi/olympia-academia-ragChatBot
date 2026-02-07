"""
Link Extractor for Olympia Academia
====================================
Extracts and deduplicates links from WhatsApp chat exports.

Features:
- Multi-file processing
- URL deduplication
- Metadata extraction (date, time, sender)
- Multiple export formats (Excel, CSV, JSON)

Author: Olympia Academia Team
"""

import re
import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

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
CHAT_DIR = Path("D:/college/Olympia Academia/oa_chatbot/OlympiaAcademia_chat")

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Output files
OUTPUT_EXCEL = RAW_DIR / "whatsapp_links_unique.xlsx"
OUTPUT_CSV = RAW_DIR / "whatsapp_links_unique.csv"
OUTPUT_JSON = RAW_DIR / "whatsapp_links_unique.json"

# Chat files to process (update with your actual paths)
CHAT_FILES = [
    CHAT_DIR / "WhatsApp_Chat_with_OlympiaAcademia" / "WhatsApp_Chat_with_OlympiaAcademia.txt",
    CHAT_DIR / "WhatsApp_Chat_with_OlympiaAcademia_AMU" / "WhatsApp_Chat_with_OlympiaAcademia_AMU.txt",
    CHAT_DIR / "WhatsApp_Chat_with_Olympia_academia_JMI" / "WhatsApp_Chat_with_Olympia_academia_JMI.txt"
]

# ==========================================
# REGEX PATTERNS
# ==========================================

# WhatsApp message patterns (handles multiple formats)
MESSAGE_PATTERNS = [
    # Format: DD/MM/YY, HH:MM am/pm - Sender: Message
    re.compile(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}\s*[apAP][mM])\s*-\s*([^:]+):\s*(.*)$'
    ),
    # Format: DD/MM/YY, HH:MM - Sender: Message (24-hour)
    re.compile(
        r'^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2})\s*-\s*([^:]+):\s*(.*)$'
    ),
    # Format: [DD/MM/YY, HH:MM:SS] Sender: Message (alternative format)
    re.compile(
        r'^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}:\d{2})\]\s*([^:]+):\s*(.*)$'
    ),
]

# URL extraction pattern (more comprehensive)
URL_PATTERN = re.compile(
    r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s\]\)\"\'<>]*'
)

# Known link categories
LINK_CATEGORIES = {
    'youtube': ['youtube.com', 'youtu.be'],
    'github': ['github.com', 'gitlab.com'],
    'medium': ['medium.com', 'towardsdatascience.com'],
    'docs': ['docs.google.com', 'drive.google.com'],
    'social': ['twitter.com', 'x.com', 'linkedin.com', 'facebook.com'],
    'academic': ['arxiv.org', 'researchgate.net', 'scholar.google'],
    'news': ['bbc.com', 'cnn.com', 'reuters.com'],
}

# ==========================================
# DATA CLASSES
# ==========================================

@dataclass
class ExtractedLink:
    """Represents an extracted link with metadata."""
    date: str
    time: str
    sender: str
    link: str
    source_file: str
    category: str = "other"
    
    def to_dict(self) -> Dict:
        return asdict(self)

# ==========================================
# LINK EXTRACTOR CLASS
# ==========================================

class WhatsAppLinkExtractor:
    """
    Extracts links from WhatsApp chat exports.
    
    Handles:
    - Multiple chat file formats
    - URL deduplication
    - Category detection
    - Multiple output formats
    """
    
    def __init__(self, chat_files: List[Path] = None):
        self.chat_files = chat_files or CHAT_FILES
        self.links: List[ExtractedLink] = []
        self.stats = {
            'files_processed': 0,
            'messages_parsed': 0,
            'links_found': 0,
            'links_unique': 0,
            'links_per_category': {}
        }
    
    def _detect_category(self, url: str) -> str:
        """Detect the category of a URL."""
        url_lower = url.lower()
        
        for category, domains in LINK_CATEGORIES.items():
            if any(domain in url_lower for domain in domains):
                return category
        
        return "other"
    
    def _parse_message(self, line: str) -> Optional[tuple]:
        """
        Parse a WhatsApp message line.
        
        Returns:
            Tuple of (date, time, sender, message) or None if not a valid message
        """
        for pattern in MESSAGE_PATTERNS:
            match = pattern.match(line.strip())
            if match:
                return match.groups()
        
        return None
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract all URLs from text."""
        urls = URL_PATTERN.findall(text)
        
        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation that might have been captured
            url = re.sub(r'[.,;:!?\'"]+$', '', url)
            if url:
                cleaned_urls.append(url)
        
        return cleaned_urls
    
    def _clean_sender(self, sender: str) -> str:
        """Clean sender name."""
        sender = sender.strip()
        
        # Remove phone number formatting
        if sender.startswith('+'):
            # Keep just the number
            sender = re.sub(r'\s+', '', sender)
        
        return sender
    
    def process_file(self, file_path: Path) -> int:
        """
        Process a single chat file.
        
        Args:
            file_path: Path to the chat file
            
        Returns:
            Number of links extracted
        """
        if not file_path.exists():
            logger.warning(f"⚠️ File not found: {file_path}")
            return 0
        
        links_found = 0
        source_name = file_path.parent.name
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                current_message = None
                
                for line in f:
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Try to parse as a new message
                    parsed = self._parse_message(line)
                    
                    if parsed:
                        date, time, sender, message = parsed
                        current_message = {
                            'date': date,
                            'time': time,
                            'sender': self._clean_sender(sender),
                            'text': message
                        }
                        self.stats['messages_parsed'] += 1
                    elif current_message:
                        # Continuation of previous message
                        current_message['text'] += ' ' + line
                    
                    # Extract URLs from current line
                    if current_message:
                        urls = self._extract_urls(current_message['text'])
                        
                        for url in urls:
                            link = ExtractedLink(
                                date=current_message['date'],
                                time=current_message['time'],
                                sender=current_message['sender'],
                                link=url,
                                source_file=source_name,
                                category=self._detect_category(url)
                            )
                            self.links.append(link)
                            links_found += 1
            
            logger.info(f"   ✓ {file_path.name}: {links_found} links found")
            self.stats['files_processed'] += 1
            
        except UnicodeDecodeError:
            # Try with different encoding
            logger.warning(f"   Unicode error, trying latin-1 encoding...")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return self.process_file(file_path)  # Recursive retry
            except Exception as e:
                logger.error(f"❌ Failed to read {file_path.name}: {e}")
        
        except Exception as e:
            logger.error(f"❌ Error processing {file_path.name}: {e}")
        
        return links_found
    
    def process_all(self):
        """Process all configured chat files."""
        logger.info("📱 WHATSAPP LINK EXTRACTOR")
        logger.info("="*60)
        logger.info(f"Processing {len(self.chat_files)} chat files...")
        
        for file_path in self.chat_files:
            logger.info(f"\n📄 Processing: {file_path.name}")
            self.process_file(file_path)
        
        self.stats['links_found'] = len(self.links)
    
    def deduplicate(self):
        """Remove duplicate links, keeping the first occurrence."""
        logger.info("\n🔄 Deduplicating links...")
        
        seen_urls = set()
        unique_links = []
        
        for link in self.links:
            # Normalize URL for comparison
            normalized = link.link.lower().rstrip('/')
            
            if normalized not in seen_urls:
                seen_urls.add(normalized)
                unique_links.append(link)
        
        removed = len(self.links) - len(unique_links)
        self.links = unique_links
        self.stats['links_unique'] = len(unique_links)
        
        logger.info(f"   Removed {removed} duplicates")
        logger.info(f"   Unique links: {len(unique_links)}")
    
    def _categorize_stats(self):
        """Calculate category statistics."""
        for link in self.links:
            category = link.category
            self.stats['links_per_category'][category] = \
                self.stats['links_per_category'].get(category, 0) + 1
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert links to DataFrame."""
        if not self.links:
            return pd.DataFrame()
        
        data = [link.to_dict() for link in self.links]
        df = pd.DataFrame(data)
        
        # Rename columns for consistency with downstream processing
        df = df.rename(columns={
            'link': 'Link',
            'date': 'Date',
            'time': 'Time',
            'sender': 'Sender',
            'source_file': 'Source',
            'category': 'Category'
        })
        
        # Reorder columns
        columns = ['Date', 'Time', 'Sender', 'Link', 'Category', 'Source']
        df = df[[col for col in columns if col in df.columns]]
        
        return df
    
    def save(
        self,
        excel_path: Path = OUTPUT_EXCEL,
        csv_path: Path = OUTPUT_CSV,
        json_path: Path = OUTPUT_JSON,
        formats: List[str] = None
    ):
        """
        Save extracted links to files.
        
        Args:
            excel_path: Path for Excel output
            csv_path: Path for CSV output
            json_path: Path for JSON output
            formats: List of formats to save ('excel', 'csv', 'json')
        """
        if not self.links:
            logger.warning("⚠️ No links to save")
            return
        
        formats = formats or ['excel', 'csv']
        df = self.to_dataframe()
        
        logger.info(f"\n💾 Saving {len(df)} links...")
        
        if 'excel' in formats:
            df.to_excel(excel_path, index=False)
            logger.info(f"   ✓ Excel: {excel_path.name}")
        
        if 'csv' in formats:
            df.to_csv(csv_path, index=False)
            logger.info(f"   ✓ CSV: {csv_path.name}")
        
        if 'json' in formats:
            data = [link.to_dict() for link in self.links]
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"   ✓ JSON: {json_path.name}")
    
    def print_summary(self):
        """Print extraction summary."""
        self._categorize_stats()
        
        logger.info("\n" + "="*60)
        logger.info("📊 EXTRACTION SUMMARY")
        logger.info("="*60)
        logger.info(f"   Files Processed:  {self.stats['files_processed']}")
        logger.info(f"   Messages Parsed:  {self.stats['messages_parsed']}")
        logger.info(f"   Links Found:      {self.stats['links_found']}")
        logger.info(f"   Unique Links:     {self.stats['links_unique']}")
        
        if self.stats['links_per_category']:
            logger.info("\n   Links by Category:")
            for category, count in sorted(
                self.stats['links_per_category'].items(), 
                key=lambda x: x[1], 
                reverse=True
            ):
                logger.info(f"      {category:12s}: {count}")
        
        logger.info("="*60)
        logger.info("\n🎉 Next step: Run cleaner.py to validate links")

# ==========================================
# CLI INTERFACE
# ==========================================

def main():
    """Command-line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract links from WhatsApp chat exports")
    parser.add_argument(
        'files', 
        nargs='*', 
        help="Chat files to process (default: configured files)"
    )
    parser.add_argument(
        '--output', '-o', 
        type=str, 
        help="Output directory"
    )
    parser.add_argument(
        '--format', '-f',
        nargs='+',
        choices=['excel', 'csv', 'json'],
        default=['excel', 'csv'],
        help="Output formats"
    )
    parser.add_argument(
        '--no-dedup',
        action='store_true',
        help="Don't remove duplicates"
    )
    
    args = parser.parse_args()
    
    # Determine files to process
    if args.files:
        chat_files = [Path(f) for f in args.files]
    else:
        chat_files = CHAT_FILES
    
    # Determine output paths
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        excel_path = output_dir / "whatsapp_links.xlsx"
        csv_path = output_dir / "whatsapp_links.csv"
        json_path = output_dir / "whatsapp_links.json"
    else:
        excel_path = OUTPUT_EXCEL
        csv_path = OUTPUT_CSV
        json_path = OUTPUT_JSON
    
    # Run extractor
    extractor = WhatsAppLinkExtractor(chat_files)
    extractor.process_all()
    
    if not args.no_dedup:
        extractor.deduplicate()
    
    extractor.save(
        excel_path=excel_path,
        csv_path=csv_path,
        json_path=json_path,
        formats=args.format
    )
    
    extractor.print_summary()

if __name__ == "__main__":
    main()
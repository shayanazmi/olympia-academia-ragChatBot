import os
import re
import json
import time
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.utils.config import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR as RAW_DIR,
    PROCESSED_DATA_DIR as PROCESSED_DIR,
    NVIDIA_FAST_MODEL,
)
from src.utils.nim_client import NIMClient

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
client = NIMClient()

# --- SCRAPING STRATEGIES ---

def get_youtube_transcript(url):
    """Extracts title and context from YouTube videos."""
    try:
        import yt_dlp
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            title = info.get('title', 'Unknown Title')
            description = info.get('description', '')
            uploader = info.get('uploader', '')
            tags = info.get('tags', []) or []
            return f"Title: {title}\nChannel: {uploader}\nTags: {', '.join(tags[:10])}\nDescription: {description[:2000]}"
    except Exception as e:
        print(f"YT Error: {e}")
        return None

def get_website_content(url):
    """Extracts main text from general websites."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        page_title = soup.title.string.strip() if soup.title and soup.title.string else 'No Title'
        return f"Page Title: {page_title}\n\nContent: {text[:4000]}"
    except Exception as e:
        print(f"Web Error: {e}")
        return None

# --- AI ENRICHMENT VIA NVIDIA NIM ---

def analyze_with_nim(context_text):
    """Sends content to NVIDIA NIM for structured academic categorization."""
    prompt = f"""Analyze the following academic resource content:
{context_text[:3500]} 

Task:
1. Summarize it clearly for a university student or researcher (60-100 words).
2. Extract 5 precise technical keywords.
3. Categorize it into [Domain] > [Field] (e.g., Mathematics > Category Theory, Biology > Quantum Biology).
4. List 3 key academic topics.

Output pure JSON only:
{{
    "summary": "...",
    "keywords": ["..."],
    "category": "...",
    "topics": ["..."]
}}
"""
    try:
        content = client.chat(
            messages=[{'role': 'user', 'content': prompt}],
            model=NVIDIA_FAST_MODEL,
            temperature=0.2,
            json_mode=True,
        )
        content = re.sub(r'```json\n|\n```', '', content).strip()
        return json.loads(content)
    except Exception as e:
        print(f"NIM AI Error: {e}")
        return None

# Backward compatibility alias
analyze_with_ollama = analyze_with_nim

# --- MAIN INGESTION LOOP ---

def process_links_batch(input_file, output_file, batch_size=5):
    """Main function to process and enrich links."""
    print(f"📂 Loading: {input_file}")
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return
        
    xls = pd.read_excel(input_file, sheet_name=None)
    processed_sheets = {}
    
    for sheet_name, df in xls.items():
        print(f"Processing Sheet: {sheet_name}")
        for col in ['AI_Summary', 'Keywords', 'Category', 'Status', 'Final_Title']:
            if col not in df.columns:
                df[col] = ""
                
        for index, row in df.iterrows():
            if str(row.get('Status')) == "Success":
                continue
                
            link = row.get('Link')
            if pd.isna(link) or "http" not in str(link):
                continue
                
            print(f"   🔗 Processing: {link}")
            if "youtube.com" in str(link) or "youtu.be" in str(link):
                context = get_youtube_transcript(str(link))
            else:
                context = get_website_content(str(link))
                
            if not context:
                df.at[index, 'Status'] = "Scrape_Failed"
                print("      ❌ Content Fetch Failed")
                continue
                
            data = analyze_with_nim(context)
            if data:
                df.at[index, 'AI_Summary'] = data.get('summary', '')
                df.at[index, 'Keywords'] = ", ".join(data.get('keywords', []))
                df.at[index, 'Category'] = data.get('category', 'General')
                df.at[index, 'Status'] = "Success"
                print("      ✅ Enriched via NVIDIA NIM")
            else:
                df.at[index, 'Status'] = "AI_Failed"
                print("      ⚠️ AI Enrichment Failed")
                
        processed_sheets[sheet_name] = df
        
    with pd.ExcelWriter(output_file) as writer:
        for name, df in processed_sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    print(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    IN_FILE = PROCESSED_DIR / "oa_cleaned.xlsx"
    OUT_FILE = PROCESSED_DIR / "oa_enriched.xlsx"
    process_links_batch(IN_FILE, OUT_FILE)
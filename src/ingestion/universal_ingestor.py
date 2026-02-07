import pandas as pd
import yt_dlp
import requests
from bs4 import BeautifulSoup
import time
import json
import re
import os
import shutil
from datetime import datetime
from pathlib import Path
from ollama import Client

# --- CONFIGURATION ---
# Path Configuration - Updated for new project structure
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Ollama Configuration
OLLAMA_API_KEY = "your_key_here"  # Recommend using os.getenv in production
OLLAMA_MODEL = "deepseek-v3.1:671b-cloud"
OLLAMA_HOST = "https://ollama.com"

client = Client(host=OLLAMA_HOST, headers={'Authorization': 'Bearer ' + OLLAMA_API_KEY})

# --- SCRAPING STRATEGIES ---

def get_youtube_transcript(url):
    """Extracts title and transcript from YouTube videos."""
    ydl_opts = {
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'quiet': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            
            # This is a simplified fetch for manual captions; 
            # In production, you might need to parse the VTT file or use youtube_transcript_api
            # For now, we return the description as fallback if subs aren't easily grabbed without download
            description = info.get('description', '')
            return f"Title: {title}\n\nDescription/Context: {description}"
    except Exception as e:
        print(f"YT Error: {e}")
        return None

def get_website_content(url):
    """Extracts main text from general websites."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Kill script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.extract()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return f"Page Title: {soup.title.string if soup.title else 'No Title'}\n\nContent: {text[:5000]}" # Limit context
    except Exception as e:
        print(f"Web Error: {e}")
        return None

# --- AI ENRICHMENT ---

def analyze_with_ollama(context_text):
    """Sends content to DeepSeek via Ollama for structured analysis."""
    prompt = f"""
    Analyze the following academic resource content:
    {context_text[:4000]} 

    Task:
    1. Summarize it for a university student.
    2. Extract 5 technical keywords.
    3. Categorize it (e.g., Mathematics, Physics, CS).
    4. List 3 key academic topics.

    Output pure JSON:
    {{
        "summary": "...",
        "keywords": ["..."],
        "category": "...",
        "topics": ["..."]
    }}
    """
    try:
        response = client.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        # Clean markdown code blocks if present
        content = re.sub(r'```json\n|\n```', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# --- MAIN INGESTION LOOP ---

def process_links_batch(input_file, output_file, batch_size=5):
    """Main function to process mixed links."""
    print(f"📂 Loading: {input_file}")
    
    # Load Excel with multiple sheets
    xls = pd.read_excel(input_file, sheet_name=None)
    
    processed_sheets = {}
    
    for sheet_name, df in xls.items():
        print(f"Processing Sheet: {sheet_name}")
        
        # Ensure columns exist
        for col in ['AI_Summary', 'Keywords', 'Category', 'Status']:
            if col not in df.columns:
                df[col] = ""
        
        unsaved = 0
        
        for index, row in df.iterrows():
            if str(row.get('Status')) == "Success":
                continue
                
            link = row.get('Link')
            if pd.isna(link) or "http" not in str(link):
                continue
                
            print(f"   🔗 Processing: {link}")
            
            # --- ROUTING LOGIC ---
            context = None
            if "youtube.com" in link or "youtu.be" in link:
                context = get_youtube_transcript(link)
            else:
                context = get_website_content(link)
                
            if not context:
                df.at[index, 'Status'] = "Scrape_Failed"
                print("      ❌ Content Fetch Failed")
                continue
                
            # --- AI ANALYSIS ---
            data = analyze_with_ollama(context)
            
            if data:
                df.at[index, 'AI_Summary'] = data.get('summary', '')
                df.at[index, 'Keywords'] = ", ".join(data.get('keywords', []))
                df.at[index, 'Category'] = data.get('category', 'General')
                df.at[index, 'Status'] = "Success"
                print("      ✅ Enriched")
            else:
                df.at[index, 'Status'] = "AI_Failed"
                print("      ⚠️ AI Failed")
            
            unsaved += 1
            if unsaved >= batch_size:
                # In production, save logic goes here
                unsaved = 0
                
        processed_sheets[sheet_name] = df
        
    # Save final
    with pd.ExcelWriter(output_file) as writer:
        for name, df in processed_sheets.items():
            df.to_excel(writer, sheet_name=name, index=False)
    print(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    # File paths - Updated for new project structure
    IN_FILE = PROCESSED_DIR / "oa_cleaned.xlsx"
    OUT_FILE = PROCESSED_DIR / "oa_enriched.xlsx"
    
    process_links_batch(IN_FILE, OUT_FILE)
import pandas as pd
import ollama
import json
import re
import os
import time
import shutil
from datetime import datetime
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================
# Path Configuration - Updated for new project structure
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
BACKUP_DIR = DATA_DIR / "backups"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# File paths
INPUT_FILE = PROCESSED_DIR / "oa_cleaned.xlsx"
OUTPUT_FILE = PROCESSED_DIR / "oa_enriched.xlsx"

API_KEY = "a48f579723f34e0ab56c4ef8cb58bc73.nYkG9XvkGfwZ6fRk1AZW0noI"
MODEL_NAME = "deepseek-v3.1:671b-cloud"
BATCH_SIZE = 10 

client = ollama.Client(host="https://ollama.com", headers={'Authorization': f'Bearer {API_KEY}'})

# ==========================================
# 1. SAFETY SYSTEMS
# ==========================================
def create_backup(filepath):
    if filepath.exists():
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = filepath.name
        shutil.copy2(filepath, BACKUP_DIR / f"{timestamp}_{filename}")

def initialize_files():
    """Sets up the enriched database file."""
    if OUTPUT_FILE.exists():
        print(f"📄 Resuming Enriched DB: {OUTPUT_FILE.name}")
        create_backup(OUTPUT_FILE)
        return OUTPUT_FILE
    
    if INPUT_FILE.exists():
        print(f"🆕 Creating Enriched DB from Cleaned File...")
        shutil.copy2(INPUT_FILE, OUTPUT_FILE)
        return OUTPUT_FILE
    
    print(f"❌ Run 'cleaner.py' first!")
    return None

def save_safely(sheets_dict, filename):
    for i in range(3):
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for name, data in sheets_dict.items():
                    data.to_excel(writer, sheet_name=name, index=False)
            print("💾 Batch Saved.")
            return
        except PermissionError:
            print("⚠️ File Open. Retrying...")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return

# ==========================================
# 2. PROMPT ENGINEERING (BATCH)
# ==========================================
def generate_batch_prompt(records):
    """
    Constructs the XML payload for 10 records.
    """
    xml_body = ""
    for r in records:
        xml_body += f"""
<resource id="{r['id']}">
 <url>{r['url']}</url>
 <context>{r['ctx']}</context>
</resource>
"""
    return f"""
SYSTEM: You are an Expert Data Classifier for an Academic Database.
TASK: Analyze these {len(records)} resources based on their URL and Context.

REQUIREMENTS:
1. title: Generate a clear, academic title if the current one is vague.
2. type: Classify strictly as one of: [Research Paper, Video Resource, Article/Blog, Course/Lecture, Tool/Repo].
3. topic: Standardize the topic (e.g., merge "Quantum Mech" -> "Quantum Mechanics").
4. category: Assign broad Domain > Sub-Domain (e.g., "Physics > Quantum Computing").

INPUT DATA:
<batch>
{xml_body}
</batch>

OUTPUT FORMAT:
Return ONLY a valid JSON list.
Example:
[
  {{"id": "1", "title": "...", "type": "Research Paper", "topic": "...", "category": "..."}},
  ...
]
"""

# ==========================================
# 3. BATCH PROCESSOR
# ==========================================
def run_batch_enrichment():
    file_to_process = initialize_files()
    if not file_to_process: return

    try:
        xls = pd.read_excel(file_to_process, sheet_name=None)
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    processed_sheets = {name: df for name, df in xls.items()}

    for sheet_name, df in processed_sheets.items():
        print(f"\n=== Enriching Sheet: {sheet_name} ===")
        
        # Init Columns
        for col in ['Final_Title', 'Resource_Type', 'Enriched_Topic', 'Enriched_Category']:
            if col not in df.columns: df[col] = ""

        # Filter: Active Links AND Empty Resource_Type
        if 'Link_Status' not in df.columns:
            print("⚠️ Sheet missing validation. Run cleaner.py first.")
            continue

        mask = (df['Link_Status'] == 'Active') & (df['Resource_Type'] == "")
        indices = df[mask].index.tolist()
        
        total_pending = len(indices)
        if total_pending == 0:
            print("✅ Sheet fully enriched.")
            continue

        print(f"🚀 Processing {total_pending} records in batches of {BATCH_SIZE}...")

        # Loop in Batches
        for i in range(0, total_pending, BATCH_SIZE):
            batch_idxs = indices[i : i + BATCH_SIZE]
            
            # Prepare Payload
            records = []
            for idx in batch_idxs:
                ctx = f"Title: {df.at[idx, 'Scraped_Title']}. Desc: {df.at[idx, 'Scraped_Context']}"
                records.append({
                    'id': str(idx),
                    'url': str(df.at[idx, 'Link']),
                    'ctx': ctx[:400] # Token Limit
                })

            print(f"   Sending Batch {i//BATCH_SIZE + 1} ({len(records)} items)...")

            try:
                # API Call
                prompt = generate_batch_prompt(records)
                response = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
                raw_json = response['message']['content']

                # Extract & Parse JSON
                json_match = re.search(r'\[.*\]', raw_json, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
                    
                    # Map back to DF
                    for item in data:
                        idx = int(item.get('id', -1))
                        if idx != -1 and idx in batch_idxs:
                            df.at[idx, 'Final_Title'] = item.get('title', '')
                            df.at[idx, 'Resource_Type'] = item.get('type', 'Web Resource')
                            df.at[idx, 'Enriched_Topic'] = item.get('topic', '')
                            df.at[idx, 'Enriched_Category'] = item.get('category', '')
                    
                    print("     ✅ Batch Success")
                else:
                    print("     ⚠️ JSON Parse Failed (Skipping Batch)")

            except Exception as e:
                print(f"     ❌ API Error: {e}")
                time.sleep(5)

            # Save every 2 batches
            if i % (BATCH_SIZE * 2) == 0:
                save_safely(processed_sheets, file_to_process)

        # Final Sheet Save
        save_safely(processed_sheets, file_to_process)

    print("\n🎉 Enrichment Complete. Database Ready.")

if __name__ == "__main__":
    run_batch_enrichment()
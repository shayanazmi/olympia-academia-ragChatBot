import pandas as pd
import google.generativeai as genai
import yt_dlp
import time
import json
import re
import os
from datetime import datetime



# Optional: set your expected per-day request cap for the model you are using.
# If you don't know it, keep None and it will only track "used" not "remaining".
DAILY_LIMIT_PER_KEY = None  # e.g., 20  OR 1500 etc.

# Local per-key counters (resets when you restart the script)
key_stats = {}  # index -> {"used": int, "last_429": str, "disabled_until": datetime|None}

# ==========================================
# CONFIGURATION
# ==========================================
# 1. PASTE ALL YOUR 6 API KEYS HERE
API_KEYS = [
    "AIzaSyBk-WnR4fbHM6zniKmoCBBOqhDL55q4bCI",#Shayanazmi04
    "AIzaSyATvfUJjkyo4ZcHzNkrDx4k94u6tkdoihg",#
    "AIzaSyBfMPPYP8zru01m-hj12cn51RuNSheX7no",#
    
]


# 2. FILE PATHS
INPUT_FILE = r"D:\college\Olympia Academia\oa_chatbot\whatsapp_links_unique_segregated.xlsx"
OUTPUT_FILE = r"D:\college\Olympia Academia\oa_chatbot\Olympia_Database_Final.xlsx"

# Optional: set your expected per-day cap per key for this model.
# If you don’t know it, keep None. It will still show "used".
DAILY_LIMIT_PER_KEY = None  # example: 20

# Global Variables
current_key_index = 0
model = None

# local per-key counters (persist only while script runs)
key_stats = {}  # idx -> {"used": int, "last_error": str, "last_429_at": str}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# --- USING AVAILABLE MODEL ---
MODEL_NAME = "models/gemini-flash-lite-latest"

# ==========================================
# QUOTA / LOG HELPERS
# ==========================================
def mask_key(k: str) -> str:
    if not k or len(k) < 10:
        return str(k)
    return k[:5] + "..." + k[-4:]


def ensure_key_stats(i: int):
    if i not in key_stats:
        key_stats[i] = {"used": 0, "last_error": "", "last_429_at": ""}


def print_key_status(prefix: str):
    ensure_key_stats(current_key_index)
    k = API_KEYS[current_key_index]
    used = key_stats[current_key_index]["used"]
    extra = ""
    if isinstance(DAILY_LIMIT_PER_KEY, int):
        remaining = max(DAILY_LIMIT_PER_KEY - used, 0)
        extra = f", est remaining today: {remaining}/{DAILY_LIMIT_PER_KEY}"
    print(f"{prefix} Key #{current_key_index + 1} ({mask_key(k)}), used(local): {used}{extra}")


def parse_quota_details(err_str: str) -> dict:
    """
    Extract useful info from Gemini quota errors.
    """
    d = {}

    # retry delay
    m = re.search(r"Please retry in\s+(\d+(\.\d+)?)s", err_str)
    if m:
        d["retry_in_s"] = float(m.group(1))
    m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_str)
    if m:
        d["retry_in_s"] = float(m.group(1))

    # quota metric
    m = re.search(r'quota_metric:\s*"([^"]+)"', err_str)
    if m:
        d["quota_metric"] = m.group(1)

    # quota value
    m = re.search(r"quota_value:\s*(\d+)", err_str)
    if m:
        d["quota_value"] = int(m.group(1))

    # limit: 20
    m = re.search(r"limit:\s*(\d+)", err_str)
    if m and "quota_value" not in d:
        d["quota_value"] = int(m.group(1))

    # model in quota_dimensions
    m = re.search(r'quota_dimensions\s*\{\s*key:\s*"model"\s*value:\s*"([^"]+)"', err_str)
    if m:
        d["quota_model"] = m.group(1)

    return d


def record_success():
    ensure_key_stats(current_key_index)
    key_stats[current_key_index]["used"] += 1


# ==========================================
# KEY ROTATION LOGIC
# ==========================================
def initialize_model():
    """Initializes the model with the current API Key."""
    global model, current_key_index

    if not API_KEYS or API_KEYS[0].startswith("PASTE_KEY"):
        print("ERROR: You forgot to paste your API Keys!")
        raise SystemExit(1)

    active_key = API_KEYS[current_key_index]
    genai.configure(api_key=active_key)
    model = genai.GenerativeModel(MODEL_NAME, safety_settings=safety_settings)

    print_key_status("--> [SYSTEM] Using")


def switch_api_key(reason: str = ""):
    """Moves to the next key in the list."""
    global current_key_index
    if reason:
        print(f"      [SYSTEM] Switching key because: {reason}")
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    initialize_model()


# Start up
initialize_model()

# ==========================================
# 1. METADATA EXTRACTION
# ==========================================
def get_video_context(url):
    # sanitize Watch Later
    if "list=WL" in url:
        url = url.split("&list=WL")[0]

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True,
        "ignoreerrors": True,

        # stronger timeouts/retries
        "socket_timeout": 10,
        "retries": 2,
        "extractor_retries": 2,
        "fragment_retries": 2,

        # slow down YouTube scraping a bit (reduces stalls)
        "sleep_interval": 1,
        "max_sleep_interval": 3,

        # sometimes helps on certain networks
        "nocheckcertificate": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None

            title = info.get("title", "Unknown Title")
            desc = info.get("description", "") or ""
            uploader = info.get("uploader", "") or ""
            tags = info.get("tags", []) or []
            duration = info.get("duration_string", "Unknown")
            views = info.get("view_count", 0)

            # Reduce payload to Gemini
            desc = re.sub(r"\s+", " ", desc).strip()
            if len(desc) < 50:
                desc_content = f"Description missing. Infer from tags: {', '.join(tags[:15])}"
            else:
                desc_content = desc[:2000]

            context = f"""Title: {title}
Channel: {uploader}
Duration: {duration}
Views: {views}
Tags: {', '.join(tags[:15])}
Description: {desc_content}
"""
            return context

    except Exception as e:
        print(f"      [!] yt-dlp error, skipping: {e}")
        return None


# ==========================================
# 2. AI ANALYSIS
# ==========================================
def analyze_with_gemini(context_text):
    prompt = f"""
ROLE: Chief Knowledge Engineer for RAG database.

INPUT METADATA:
{context_text}

STRICT INSTRUCTIONS:
1. SUMMARY: High-density abstract (60-100 words). No filler like "In this video...".
2. KEYWORDS: 6-10 Standardized Academic Keywords (normalize slang to academic terms).
3. CATEGORY: [Broad Domain] > [Specific Field].
4. TOPICS: Specific entities/equations.

OUTPUT FORMAT:
Return ONLY JSON with keys "summary", "keywords", "category", "topics".
"""

    keys_tried = 0
    max_total_attempts = len(API_KEYS) * 3  # 3 cycles through all keys

    for _ in range(max_total_attempts):
        try:
            resp = model.generate_content(prompt)
            text = resp.text

            m = re.search(r"\{.*\}", text, re.DOTALL)
            if m:
                # count this as a successful request for current key
                record_success()
                return json.loads(m.group(0))

            # No JSON returned => treat as AI failure (not quota)
            print("      [!] AI response was not valid JSON (first 120 chars):")
            print(f"      {text[:120]}")
            return None

        except Exception as e:
            s = str(e)
            ensure_key_stats(current_key_index)
            key_stats[current_key_index]["last_error"] = s[:1000]

            if "429" in s or "ResourceExhausted" in s:
                key_stats[current_key_index]["last_429_at"] = datetime.now().isoformat(timespec="seconds")
                details = parse_quota_details(s)

                print("\n      [429] Quota/Rate limit hit")
                print_key_status("      Active")
                if details:
                    print(f"      Details: {details}")
                else:
                    print(f"      Raw error (first 250 chars): {s[:250]}")

                # figure out a good delay
                delay = int(details.get("retry_in_s", 30))
                delay = max(delay, 10)

                # switch key
                switch_api_key(reason=f"429 hit; suggested retry {delay}s")
                keys_tried += 1

                # if we tried all keys -> global cooldown
                if keys_tried >= len(API_KEYS):
                    cooldown = max(60, delay)
                    print(f"      [!!!] All keys hit limits. Global cooldown {cooldown}s...\n")
                    time.sleep(cooldown)
                    keys_tried = 0
                else:
                    time.sleep(2)

            else:
                # non-429 error
                print("\n      [!] Gemini error (non-429):")
                print_key_status("      Active")
                print(f"      Error snippet: {s[:250]}")
                time.sleep(5)

    return None


# ==========================================
# 3. MAIN EXECUTION
# ==========================================
def save_safely(sheets_dict, filename):
    try:
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            for name, data in sheets_dict.items():
                data.to_excel(writer, sheet_name=name, index=False)
        print(f"   -> Saved to {filename}")
    except PermissionError:
        print(f"   [!] WARN: File is OPEN. Close it!")
    except Exception:
        pass


def get_real_sheet_name(xls_keys, target):
    for key in xls_keys:
        if key.lower() == target.lower():
            return key
    return None


def process_database():
    if os.path.exists(OUTPUT_FILE):
        print(f"Resuming from {OUTPUT_FILE}...")
        load_file = OUTPUT_FILE
    elif os.path.exists(INPUT_FILE):
        print(f"Starting from {INPUT_FILE}...")
        load_file = INPUT_FILE
    else:
        print("Error: No file found.")
        return

    xls = pd.read_excel(load_file, sheet_name=None)
    targets = ["YouTube_Videos", "YouTube_Shorts"]
    processed_sheets = {name: df for name, df in xls.items()}

    for target in targets:
        sheet_name = get_real_sheet_name(xls.keys(), target)
        if not sheet_name:
            print(f"Skip: Sheet '{target}' not found.")
            continue

        df = processed_sheets[sheet_name]
        print(f"\n=== PROCESSING: {sheet_name} ===")

        cols = ["Link", "AI_Summary", "Keywords", "Category", "Topics", "Status"]
        for col in cols:
            if col not in df.columns:
                df[col] = ""

        total_rows = len(df)

        for index, row in df.iterrows():
            if str(row["Status"]) == "Success":
                continue

            link = row["Link"]
            if pd.isna(link) or "http" not in str(link):
                continue

            print(f"[{index+1}/{total_rows}] {link}")

            context = get_video_context(link)
            if not context:
                df.at[index, "Status"] = "Bad_Link_or_Metadata_Fail"
                print("   -> Metadata fail, skipping")
                continue

            data = analyze_with_gemini(context)

            if data:
                df.at[index, "AI_Summary"] = data.get("summary", "")
                df.at[index, "Keywords"] = ", ".join(data.get("keywords", []))
                df.at[index, "Topics"] = ", ".join(data.get("topics", []))
                df.at[index, "Category"] = data.get("category", "General")
                df.at[index, "Status"] = "Success"
                print("   -> Success")
            else:
                df.at[index, "Status"] = "AI_Failed"
                print("   -> AI Error")

            # small pacing so we don't hammer YouTube
            time.sleep(2)

            if index % 5 == 0:
                processed_sheets[sheet_name] = df
                save_safely(processed_sheets, OUTPUT_FILE)

        processed_sheets[sheet_name] = df

    save_safely(processed_sheets, OUTPUT_FILE)
    print("\nDONE! Videos and Shorts processed.")


if __name__ == "__main__":
    process_database()
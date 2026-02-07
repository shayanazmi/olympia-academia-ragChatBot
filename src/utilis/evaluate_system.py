import pandas as pd
import ollama
import json
import os
import re
import time
import concurrent.futures
from datetime import datetime
from pathlib import Path
import sys

# --- PATH CONFIGURATION ---
PROJECT_ROOT = Path("D:/college/Olympia Academia/oa_chatbot/olympia-academia")
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directory exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- IMPORT YOUR ENGINE ---
sys.path.insert(0, str(PROJECT_ROOT / "src" / "engine"))
try:
    from rag_engine import Librarian
except ImportError:
    from src.engine.rag_engine import Librarian

# ==========================================
# CONFIGURATION
# ==========================================
API_KEY = "a48f579723f34e0ab56c4ef8cb58bc73.nYkG9XvkGfwZ6fRk1AZW0noI"
MODEL_NAME = "deepseek-v3.1:671b-cloud"
OUTPUT_CSV = PROCESSED_DIR / "evaluation_report.csv"
OUTPUT_SUMMARY = PROCESSED_DIR / "evaluation_summary.md"

# Initialize
client = ollama.Client(host="https://ollama.com", headers={'Authorization': f'Bearer {API_KEY}'})
librarian = Librarian()

# ==========================================
# 1. THE GOLDEN DATASET
# ==========================================
TEST_SUITE = [
    {
        "id": 1,
        "question": "What is the content of Grothendieck's letter to Daniel Quillen?",
        "target_link": "golem.ph.utexas.edu",
        "ground_truth_concepts": ["Superconnections", "Derivators", "Homotopy Theory"]
    },
    {
        "id": 2,
        "question": "How do birds use quantum mechanics for navigation?",
        "target_link": "youtube.com/watch?v=0SPD2r0xV8k",
        "ground_truth_concepts": ["Cryptochrome", "Radical Pair Mechanism", "European Robin"]
    },
    {
        "id": 3,
        "question": "Who is Michael Atiyah?",
        "target_link": "youtube.com/shorts/g5EyChOEi9o",
        "ground_truth_concepts": ["Fields Medal", "Index Theorem", "Royal Society"]
    },
    {
        "id": 4,
        "question": "Explain the Feynman Technique.",
        "target_link": "youtube.com/shorts/9iUPepjoPog", 
        "ground_truth_concepts": ["Simplicity", "Teaching", "Richard Feynman"]
    },
    {
        "id": 5,
        "question": "Resources on Formal Verification using Lean.",
        "target_link": "youtube.com/@terencetao27",
        "ground_truth_concepts": ["Terence Tao", "Lean Proof Assistant", "AI"]
    },
    {
        "id": 6,
        "question": "How to make a Lasagna?",
        "target_link": "NONE", # Negative Test
        "ground_truth_concepts": ["I don't know", "No resources found"]
    }
]

# ==========================================
# 2. THE AI JUDGE (LLM-as-a-Judge)
# ==========================================
def llm_judge(question, context, answer):
    prompt = f"""
    You are an AI Evaluator. Grade the following RAG interaction.
    
    USER QUESTION: "{question}"
    
    RETRIEVED CONTEXT:
    {context[:2000]}... (truncated)
    
    BOT ANSWER:
    "{answer}"
    
    TASK: Provide a JSON output with two scores (1-5):
    1. "faithfulness": (1-5) Is the answer derived PURELY from the context? (5 = Yes, 1 = Hallucinated/Made up info).
    2. "relevance": (1-5) Does the answer actually address the user's question? (5 = Perfect Answer, 1 = Irrelevant/Vague).
    3. "reason": Short explanation.

    OUTPUT JSON ONLY.
    """
    try:
        response = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
        content = response['message']['content']
        
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return {"faithfulness": 0, "relevance": 0, "reason": "JSON Parse Error"}
    except Exception as e:
        return {"faithfulness": 0, "relevance": 0, "reason": str(e)}

# ==========================================
# 3. TEST RUNNER (Single Case)
# ==========================================
def run_single_test(case):
    start_time = time.time()
    
    # A. RETRIEVAL STEP
    results = librarian.search(case['question'], top_k=5)
    
    # Check Hit Rate
    if case['target_link'] == "NONE":
        # For "NONE", Hit is 0 (we found nothing relevant), but that's okay.
        hit = 0 
    else:
        # Check if target link substring exists in any retrieved result link
        hit = any(case['target_link'] in str(r.get('link', '')) for r in results)
    
    # Prepare Context for Generation
    context_str = "\n".join([f"Source: {r.get('title','')} | Link: {r.get('link','')} | Text: {r.get('context','')}" for r in results])
    
    # B. GENERATION STEP
    if not results and case['target_link'] != "NONE":
        answer = "I couldn't find any resources."
    else:
        gen_prompt = f"""
        Use the following context to answer the question. If answer is not in context, say 'I don't know'.
        Context: {context_str}
        Question: {case['question']}
        Answer:
        """
        try:
            answer = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': gen_prompt}])['message']['content']
        except:
            answer = "Error generating answer."

    # C. JUDGING STEP
    scores = llm_judge(case['question'], context_str, answer)
    
    duration = round(time.time() - start_time, 2)
    
    return {
        "ID": case['id'],
        "Question": case['question'],
        "Target_Link": case['target_link'],
        "Hit_Rate": 1 if hit else 0,
        "Faithfulness": scores.get('faithfulness', 0),
        "Relevance": scores.get('relevance', 0),
        "Judge_Reason": scores.get('reason', 'N/A'),
        "Latency_Sec": duration,
        "Generated_Answer": answer[:100] + "...", 
        "Top_Link_Retrieved": results[0]['link'] if results else "None"
    }

# ==========================================
# 4. MAIN EXECUTOR (Parallel)
# ==========================================
def run_evaluation_suite():
    print(f"🚀 Starting Evaluation of {len(TEST_SUITE)} Test Cases...")
    print(f"   Model: {MODEL_NAME}")
    
    final_results = []
    
    # Run in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(run_single_test, case): case for case in TEST_SUITE}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            final_results.append(res)
            
            # --- INTELLIGENT STATUS CHECK ---
            if res['Target_Link'] == "NONE":
                # For negative tests, we Pass if Faithfulness is High (Bot refused to answer)
                passed = (res['Faithfulness'] >= 4)
            else:
                # For positive tests, we need the Link AND High Faithfulness
                passed = (res['Hit_Rate'] == 1 and res['Faithfulness'] >= 4)

            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"[{i+1}/{len(TEST_SUITE)}] {status} | Q: {res['Question'][:30]}... | Faith: {res['Faithfulness']}/5")

    # --- REPORTING ---
    df = pd.DataFrame(final_results)
    
    # 1. Save CSV
    df.to_csv(OUTPUT_CSV, index=False)
    
    # 2. Calculate Stats
    # Only calc Hit Rate for positive tests
    positive_tests = df[df['Target_Link'] != "NONE"]
    avg_hit = positive_tests['Hit_Rate'].mean() * 100 if not positive_tests.empty else 0
    
    avg_faith = df['Faithfulness'].mean()
    avg_rel = df['Relevance'].mean()
    avg_lat = df['Latency_Sec'].mean()
    
    summary = f"""
# 📊 Olympia RAG Evaluation Report
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}

## 📈 Key Metrics
| Metric | Score | Target |
| :--- | :--- | :--- |
| **Retrieval Hit Rate (Positive Tests)** | **{avg_hit:.1f}%** | >80% |
| **Faithfulness (1-5)** | **{avg_faith:.2f}** | >4.0 |
| **Relevance (1-5)** | **{avg_rel:.2f}** | >4.0 |
| **Avg Latency** | **{avg_lat:.2f}s** | <10s |

## 🔍 Failure Analysis
*(Cases where the System failed expectations)*
"""
    # Logic for Failures in Summary
    for _, row in df.iterrows():
        is_fail = False
        if row['Target_Link'] == "NONE":
            if row['Faithfulness'] < 4: is_fail = True
        else:
            if row['Hit_Rate'] == 0 or row['Faithfulness'] < 3: is_fail = True
            
        if is_fail:
            summary += f"\n- **Q:** {row['Question']}\n  - **Reason:** {row['Judge_Reason']}\n  - **Top Link:** {row['Top_Link_Retrieved']}\n"

    if "Reason:" not in summary:
        summary += "\n🎉 No critical failures detected!"

    # --- SAFE WRITE (UTF-8) ---
    try:
        with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
            f.write(summary)
    except Exception as e:
        print(f"⚠️ Could not write summary markdown: {e}")
        
    print(f"\n✅ Evaluation Complete.")
    print(f"   📂 Details saved to: {OUTPUT_CSV}")
    print(f"   📄 Summary saved to: {OUTPUT_SUMMARY}")
    print("\n" + "-"*30)
    print(summary)
    print("-"*30)

if __name__ == "__main__":
    run_evaluation_suite()
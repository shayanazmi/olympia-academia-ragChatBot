import sys
import os
from pathlib import Path

# Force project root onto sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.engine.rag_engine import Librarian
from src.database.build_db import DatabaseBuilder
from src.utils.nim_client import NIMClient, NIMAuthenticationError, NIMRateLimitError
from src.utils.config import (
    NVIDIA_PRIMARY_MODEL,
    NVIDIA_FAST_MODEL,
    NVIDIA_API_KEY,
    FAISS_INDEX_PATH,
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. STREAMLIT PAGE CONFIG & STYLING
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Olympia Academia",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #ffffff;
    }
    .stChatMessage {
        background-color: #1a1c24;
        border-radius: 15px;
        padding: 15px;
        border: 1px solid #2d2f3b;
        margin-bottom: 10px;
    }
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #13151b;
    }
    .source-card {
        background-color: #262730;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #76b900; /* NVIDIA Green */
        margin-bottom: 10px;
    }
    .source-title {
        font-weight: bold;
        color: #a3e635;
        font-size: 1.05em;
    }
    .source-meta {
        font-size: 0.85em;
        color: #b0bec5;
        margin-top: 3px;
    }
    section[data-testid="stSidebar"] {
        background-color: #161920;
    }
    .stButton button {
        background-color: #2d2f3b;
        color: white;
        border: 1px solid #4a4d5e;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #76b900;
        border-color: #76b900;
        color: black;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2. INITIALIZE SERVICES
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource
def get_nim_client():
    return NIMClient()

@st.cache_resource
def get_librarian():
    try:
        if FAISS_INDEX_PATH.exists():
            return Librarian()
        return None
    except Exception:
        return None

nim_client = get_nim_client()
librarian = get_librarian()

# ══════════════════════════════════════════════════════════════════════════════
# 3. HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def refine_query(client: NIMClient, user_input: str, history: list):
    """Uses NVIDIA NIM fast model to determine if retrieval is needed and generate sub-queries."""
    if not history:
        return True, [user_input]
        
    recent_history = history[-3:]
    history_str = "\n".join([f"{msg['role']}: {msg['content'][:250]}..." for msg in recent_history])

    router_prompt = f"""You are a query analysis agent for an academic RAG system.
Analyze the user's latest input in the context of recent chat history.
Determine if the input requires a NEW database search or is conversational.
If search is required, generate 3 specific, diverse search queries.

CHAT HISTORY:
{history_str}

USER INPUT: "{user_input}"

OUTPUT JSON ONLY with this exact schema:
{{
  "search": true,
  "queries": ["query 1", "query 2", "query 3"]
}}
"""
    try:
        content = client.chat(
            messages=[{"role": "user", "content": router_prompt}],
            model=NVIDIA_FAST_MODEL,
            temperature=0.2,
            json_mode=True,
        )
        data = json.loads(content)
        queries = data.get("queries", [user_input])
        if isinstance(queries, str):
            queries = [queries]
        return data.get("search", True), queries
    except Exception:
        return True, [user_input]

# ══════════════════════════════════════════════════════════════════════════════
# 4. SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_context" not in st.session_state:
    st.session_state.last_context = ""

# ══════════════════════════════════════════════════════════════════════════════
# 5. SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.title("🏛️ Olympia Academia")
    st.caption(f"Powered by NVIDIA NIM & Hybrid Search")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        db_status = "Active" if librarian is not None else "Unindexed"
        st.metric("Database", db_status)
    with col2:
        st.metric("Primary Model", NVIDIA_PRIMARY_MODEL.split("/")[-1][:12])
        
    st.markdown("### ⚙️ Database & Controls")
    
    if librarian is None:
        st.warning("Database indices not found.")
        if st.button("🌱 Build Seed Academic Database", use_container_width=True):
            with st.spinner("Building FAISS & BM25 indices from curated academic data..."):
                builder = DatabaseBuilder(use_sample=True)
                builder.build_all()
                st.cache_resource.clear()
                st.success("Database built successfully!")
                time.sleep(1)
                st.rerun()
    else:
        stats = librarian.get_stats()
        st.caption(f"📚 **Indexed Docs:** {stats['total_documents']} | ⚡ **Vectors:** {stats['vector_count']}")
        st.caption(f"🎯 **Cache Rate:** {stats['cache_hit_rate']}")

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_context = ""
        st.rerun()

    st.markdown("---")
    if not NVIDIA_API_KEY:
        st.error("⚠️ NVIDIA_API_KEY missing! Add it to your `.env` file.")
    else:
        st.success("🟢 NVIDIA NIM Connected")

# ══════════════════════════════════════════════════════════════════════════════
# 6. HERO SECTION
# ══════════════════════════════════════════════════════════════════════════════

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; margin-bottom: 40px;">
        <h1 style="font-size: 2.8em;">Olympia Academia</h1>
        <p style="font-size: 1.15em; color: #b0bec5;">Academic Research Assistant with Grounded Hybrid Retrieval</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🐦 Quantum Avian Navigation", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "How do migratory birds use quantum mechanics to navigate?"})
            st.rerun()
    with col2:
        if st.button("📐 Grothendieck to Quillen", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What is the content of Grothendieck's letter to Daniel Quillen?"})
            st.rerun()
    with col3:
        if st.button("💻 Lean 4 Theorem Prover", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What is the Lean programming language and how is it used in formal mathematics?"})
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# 7. CHAT HISTORY RENDERING
# ══════════════════════════════════════════════════════════════════════════════

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🏛️" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])

# ══════════════════════════════════════════════════════════════════════════════
# 8. MAIN QUERY PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

if prompt := st.chat_input("Ask an academic or scientific research question..."):
    
    # Verify API key first
    if not NVIDIA_API_KEY:
        st.error("❌ NVIDIA_API_KEY is not configured. Please add `NVIDIA_API_KEY=nvapi-...` to your `.env` file.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Missing database guard
    if librarian is None:
        with st.chat_message("assistant", avatar="🏛️"):
            st.warning("⚠️ The knowledge base index has not been built yet. Please click **'Build Seed Academic Database'** in the sidebar to initialize the search database.")
        st.stop()

    final_results = []
    
    with st.status("🧠 Processing Research Query...", expanded=False) as status:
        # Step A: Query Routing
        needs_search, queries = refine_query(nim_client, prompt, st.session_state.messages[:-1])
        
        if needs_search:
            status.update(label=f"🔎 Hybrid Search: {queries[0]}...", state="running")
            all_results = {}
            
            for q in queries:
                res = librarian.search(q, top_k=5)
                for r in res:
                    if r['id'] not in all_results or r['score'] > all_results[r['id']]['score']:
                        all_results[r['id']] = r
                        
            final_results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)[:8]
            
            # Format Context String
            context_str = ""
            if final_results:
                context_str += "### RETRIEVED ACADEMIC RESOURCES:\n"
                for i, r in enumerate(final_results, 1):
                    context_str += (
                        f"Record {i}: [Type: {r.get('type', 'Resource')}] "
                        f"Title: {r.get('title', 'Untitled')} | "
                        f"Link: {r.get('link', '#')} | "
                        f"Topic: {r.get('topic', 'General')} | "
                        f"Summary: {r.get('summary', '')} | "
                        f"Insights: {r.get('insights', '')}\n"
                    )
            else:
                context_str = "No specific database records found."
                
            st.session_state.last_context = context_str
            status.update(label=f"✅ Retrieved {len(final_results)} Academic Sources", state="complete", expanded=False)
        else:
            status.update(label="🧠 Reasoning over existing context", state="complete")
            context_str = st.session_state.last_context

    # Step B: Source Cards Expander
    if needs_search and final_results:
        with st.expander(f"📚 View {len(final_results)} Retrieved Sources", expanded=False):
            for r in final_results:
                st.markdown(f"""
                <div class="source-card">
                    <div class="source-title">📄 {r.get('title', 'Untitled')}</div>
                    <div class="source-meta">
                        <b>Topic:</b> {r.get('topic', 'General')} | <b>Type:</b> {r.get('type', 'Resource')} | <b>Relevance:</b> {r.get('score', 0):.2f}
                    </div>
                    <div style="font-size: 0.9em; margin-top: 6px;">
                        {r.get('summary', '')}
                    </div>
                    <div style="margin-top: 6px;">
                        <a href="{r.get('link', '#')}" target="_blank" style="color: #a3e635; text-decoration: none;">🔗 Access Source</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Step C: Generation via NVIDIA NIM
    system_instruction = f"""You are Olympia, an expert academic and scientific research assistant.

ACTIVE KNOWLEDGE CONTEXT:
{context_str}

USER INPUT: "{prompt}"

INSTRUCTIONS:
1. Synthesize a comprehensive answer grounded in the Active Knowledge Context.
2. If the context does not contain sufficient details to answer, state clearly: "I couldn't find specific resources for this in the current database."
3. Strictly format your response using this academic structure:

**Direct Answer:**
[Provide a clear, detailed, synthesized answer here.]

**Primary Resource:**
- **Title:** [Best title from context] (Link: [URL])
- **Summary:** [1-2 sentences]

**Related Research Papers / Articles:**
[List papers or articles from the context, or omit this header if none]
- [Title] (Link: [URL])

**Related Videos:**
[List video resources from the context, or omit this header if none]
- [Title] (Link: [URL])

**Related Topics to Understand This:**
[List 3-4 specific foundational academic prerequisites or related topics]
"""

    with st.chat_message("assistant", avatar="🏛️"):
        response_container = st.empty()
        full_response = ""
        
        try:
            stream_gen = nim_client.chat_stream(
                messages=[{"role": "user", "content": system_instruction}],
                model=NVIDIA_PRIMARY_MODEL,
                temperature=0.5,
            )
            for chunk in stream_gen:
                full_response += chunk
                response_container.markdown(full_response + "▌")
            response_container.markdown(full_response)
            
            # Step D: Fact-Check / Grounding Evaluation
            if "RETRIEVED ACADEMIC RESOURCES" in context_str and len(full_response) > 50:
                critique_prompt = f"""Fact Check: Does this answer:
"{full_response}"
contain claims contrary to or completely unsupported by:
"{context_str}"?
Output ONLY 'SUPPORTED' or 'UNSUPPORTED' followed by a 1-sentence note."""
                try:
                    critique = nim_client.chat(
                        messages=[{"role": "user", "content": critique_prompt}],
                        model=NVIDIA_FAST_MODEL,
                        temperature=0.1,
                    ).strip()
                    if "UNSUPPORTED" in critique.upper():
                        st.warning(f"⚠️ Note: Some claims may draw on general knowledge: {critique}")
                    else:
                        st.caption("✅ Verified: Grounded in Academic Database")
                except Exception:
                    pass

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except NIMAuthenticationError as auth_err:
            st.error(f"❌ {auth_err}")
        except NIMRateLimitError as rl_err:
            st.warning(f"⏳ {rl_err}")
        except Exception as e:
            st.error(f"Error during response generation: {e}")

    # Step E: Interactive Follow-up Suggestions
    if len(full_response) > 50:
        suggestion_prompt = f"""Based on this academic answer, generate 3 short, thought-provoking follow-up research questions.
Answer: "{full_response[:400]}"
Output format: Q1 | Q2 | Q3 (separated by pipes ONLY, no numbers or extra text)."""
        try:
            sug_resp = nim_client.chat(
                messages=[{"role": "user", "content": suggestion_prompt}],
                model=NVIDIA_FAST_MODEL,
                temperature=0.7,
            )
            suggestions = [s.strip() for s in sug_resp.split('|') if len(s.strip()) > 5][:3]
            if suggestions:
                st.markdown("---")
                cols = st.columns(len(suggestions))
                for i, sug in enumerate(suggestions):
                    clean_sug = sug.lstrip("0123456789. -")
                    if cols[i].button(clean_sug, key=f"sug_{int(time.time())}_{i}"):
                        st.session_state.messages.append({"role": "user", "content": clean_sug})
                        st.rerun()
        except Exception:
            pass
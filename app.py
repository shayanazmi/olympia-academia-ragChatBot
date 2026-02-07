import sys
import os

# --- 0. FORCE PATH FIX ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import ollama
import json
import time
from dotenv import load_dotenv

# --- 1. CONFIGURATION & STYLING ---
load_dotenv()

st.set_page_config(
    page_title="Olympia Academia",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Academic Studio" Look
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Header Styling */
    h1 {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Chat Bubble Styling */
    .stChatMessage {
        background-color: #1a1c24;
        border-radius: 15px;
        padding: 15px;
        border: 1px solid #2d2f3b;
        margin-bottom: 10px;
    }
    
    /* User Message distinct color */
    div[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #13151b;
    }

    /* Source Card Styling */
    .source-card {
        background-color: #262730;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin-bottom: 10px;
    }
    .source-title {
        font-weight: bold;
        color: #81c784;
        font-size: 1.05em;
    }
    .source-meta {
        font-size: 0.85em;
        color: #b0bec5;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #161920;
    }
    
    /* Button Styling */
    .stButton button {
        background-color: #2d2f3b;
        color: white;
        border: 1px solid #4a4d5e;
        border-radius: 8px;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #4CAF50;
        border-color: #4CAF50;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

try:
    from architecture.rag_engine import Librarian
except ImportError as e:
    st.error(f"❌ Configuration Error: {e}")
    st.stop()

# API Configuration
MODEL_NAME = "deepseek-v3.1:671b-cloud"
API_KEY = os.getenv("OLLAMA_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key Missing! Check .env file.")
    st.stop()

# --- 2. INITIALIZE ENGINE ---
@st.cache_resource
def get_librarian():
    try:
        return Librarian()
    except Exception:
        return None

librarian = get_librarian()

# --- 3. HELPER FUNCTIONS ---
def refine_query(client, user_input, history):
    if not history: return True, [user_input]
    recent_history = history[-3:] 
    history_str = "\n".join([f"{msg['role']}: {msg['content'][:300]}..." for msg in recent_history])

    router_prompt = f"""
    Analyze conversation. Determine if User Input requires a NEW Database Search.
    CHAT HISTORY: {history_str}
    USER INPUT: "{user_input}"
    RULES: "search": true for new info. "search": false for chat/follow-up.
    If true, generate 3 varied search queries.
    OUTPUT JSON: {{ "search": <bool>, "queries": ["q1", "q2", "q3"] }}
    """
    try:
        response = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': router_prompt}])
        content = response['message']['content']
        if "{" in content:
            content = content[content.find("{"):content.rfind("}")+1]
            data = json.loads(content)
            queries = data.get("queries", [user_input])
            if isinstance(queries, str): queries = [queries]
            return data.get("search", True), queries
        return True, [user_input]
    except:
        return True, [user_input]

# --- 4. SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_context" not in st.session_state:
    st.session_state.last_context = ""

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Olympia")
    st.caption("v2.4 | Research Mode")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Database", "Active", delta="On")
    with col2:
        st.metric("Guardrails", "Strict", delta="High")
        
    st.markdown("### ⚙️ Controls")
    if st.button("🗑️ Clear Memory", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_context = ""
        st.rerun()

    st.info("**System Status:** All Systems Operational.")

# --- 6. HERO SECTION ---
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; margin-bottom: 50px;">
        <h1 style="font-size: 3em;">Olympia Academia</h1>
        <p style="font-size: 1.2em; color: #b0bec5;">Your Context-Aware Research Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🐦 Bird Navigation", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "How do birds navigate?"})
            st.rerun()
    with col2:
        if st.button("📐 Grothendieck", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "Explain the relationship between Grothendieck and Quillen"})
            st.rerun()
    with col3:
        if st.button("💻 Lean Language", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "What is the Lean programming language?"})
            st.rerun()

# --- 7. CHAT INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="🏛️" if message["role"] == "assistant" else "👤"):
        st.markdown(message["content"])

# --- 8. REGENERATION BUTTON ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    if st.button("🔄 Regenerate Answer", key="regen_btn"):
        st.session_state.messages.pop()
        st.rerun()

# --- 9. MAIN LOGIC PIPELINE ---
if prompt := st.chat_input("Ask a research question..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    client = ollama.Client(host='https://ollama.com', headers={'Authorization': f'Bearer {API_KEY}'})

    # --- ROUTING ---
    final_results = []
    with st.status("🧠 Processing...", expanded=False) as status:
        needs_search, queries = refine_query(client, prompt, st.session_state.messages[:-1])
        
        if needs_search:
            status.update(label=f"🔎 Searching: {queries[0]}...", state="running")
            all_results = {}
            for q in queries:
                res = librarian.search(q, top_k=5) 
                for r in res:
                    if r['id'] not in all_results or r['score'] > all_results[r['id']]['score']:
                        all_results[r['id']] = r
            
            final_results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)[:8]
            
            # IMPROVED CONTEXT STRING: Now includes explicit [TYPE] tag
            context_str = ""
            if final_results:
                context_str += "### RETRIEVED RESOURCES:\n"
                for i, r in enumerate(final_results):
                    # Use .get() with defaults to prevent crashes
                    rtype = r.get('type', 'General Resource')
                    title = r.get('title', 'Untitled')
                    link = r.get('link', '#')
                    summary = r.get('summary', 'No summary.')
                    context_str += f"Record {i+1}: [Type: {rtype}] Title: {title} | Link: {link} | Summary: {summary}\n"
            else:
                context_str = "No specific database records found."
            
            st.session_state.last_context = context_str
            status.update(label="✅ Context Retrieved", state="complete", expanded=False)
        else:
            status.update(label="🧠 Using Memory", state="complete")
            context_str = st.session_state.last_context

    # --- SOURCE CARDS ---
    if needs_search and final_results:
        with st.expander(f"📚 View {len(final_results)} Retrieved Sources", expanded=False):
            for r in final_results:
                st.markdown(f"""
                <div class="source-card">
                    <div class="source-title">📄 {r.get('title', 'Untitled')}</div>
                    <div class="source-meta">
                        <b>Type:</b> {r.get('type', 'Resource')} | <b>Relevance:</b> {r.get('score', 0):.2f}
                    </div>
                    <div style="font-size: 0.9em; margin-top: 5px;">
                        {r.get('summary', '')[:200]}...
                    </div>
                    <div style="margin-top: 5px;">
                        <a href="{r.get('link', '#')}" target="_blank" style="color: #64b5f6; text-decoration: none;">🔗 Open Resource</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # --- GENERATION (CATEGORIZED FORMAT) ---
    system_instruction = f"""
    You are Olympia, an expert academic assistant.
    
    ACTIVE KNOWLEDGE CONTEXT:
    {context_str}
    
    USER INPUT: "{prompt}"
    
    INSTRUCTIONS:
    1. Answer purely based on the Context.
    2. **CRITICAL:** If the context is empty, say "I couldn't find specific resources."
    
    3. **OUTPUT FORMAT (Strictly Follow This Structure):**
       
       **Direct Answer:**
       [Provide a detailed, synthesized answer here.]
       
       **Primary Resource:**
       - **Title:** [Best Title] (Link: [URL])
       - **Summary:** [1 sentence]
       
       **Related Research Papers/Articles:**
       [List ONLY items marked as "Non-YouTube", "Article", "Paper", or "PDF" in the context.]
       - [Title] (Link: [URL])
       
       **Related Videos:**
       [List ONLY items marked as "Video" or "YouTube" in the context.]
       - [Title] (Link: [URL])
       
       **Related Channels:**
       [List ONLY items marked as "Channel" in the context.]
       - [Channel Name] (Link: [URL])
       
       **Related Topics to Understand This:**
       [List 3-4 specific academic concepts or prerequisites the user should study to understand the answer better (e.g. "Eigenvalues", "Radical Pair Mechanism").]
       
    4. If a category (e.g. "Channels") has no records in the context, omit that specific header.
    """

    with st.chat_message("assistant", avatar="🏛️"):
        response_container = st.empty()
        full_response = ""
        
        try:
            stream = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': system_instruction}], stream=True)
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                response_container.markdown(full_response + "▌")
            response_container.markdown(full_response)
            
            # CRITIQUE LOOP
            if "RETRIEVED RESOURCES" in context_str:
                critique_prompt = f"Fact Check: Does this answer: '{full_response}' contain claims NOT in: '{context_str}'? Output UNSUPPORTED or SUPPORTED."
                critique = client.generate(model=MODEL_NAME, prompt=critique_prompt)['response'].strip().upper()
                if "UNSUPPORTED" in critique:
                    st.warning("⚠️ Note: Some details may be general knowledge.")
                else:
                    st.caption("✅ Verified: Grounded in Database")
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error: {e}")

    # --- FOLLOW-UP BUTTONS ---
    if len(full_response) > 50:
        suggestion_prompt = f"Suggest 3 short follow-up questions based on: '{full_response[:500]}'. Output separated by pipes |."
        try:
            sug_resp = client.generate(model=MODEL_NAME, prompt=suggestion_prompt)
            suggestions = [s.strip() for s in sug_resp['response'].split('|') if len(s) > 5]
            if suggestions:
                st.markdown("---")
                cols = st.columns(len(suggestions))
                for i, sug in enumerate(suggestions):
                    if cols[i].button(sug, key=f"sug_{int(time.time())}_{i}"):
                        st.session_state.messages.append({"role": "user", "content": sug})
                        st.rerun()
        except: pass
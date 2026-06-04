import sys
# Override sqlite3 with pysqlite3 for ChromaDB compatibility on Linux (Streamlit Cloud)
if sys.platform.startswith("linux"):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    except ImportError:
        pass

import os
import re
import json
import logging
import streamlit as st
import pandas as pd
from backend.generator import RAGResponseGenerator
from backend.scraper import VERIFIED_SCHEME_DB

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="WealthSearchAI - RAG Mutual Fund Chatbot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern Glassmorphism look
st.markdown("""
<style>
    /* Main Background and Typography */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Title and Header styling */
    .app-header {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    }
    
    .app-title {
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem;
        font-weight: 700;
        margin-bottom: 8px;
    }
    
    .app-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        font-weight: 300;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Scoped fund card styling */
    .fund-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }
    
    .fund-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    
    /* Compliance disclaimer */
    .compliance-box {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 12px;
        padding: 16px;
        color: #fca5a5;
        margin-bottom: 16px;
    }
    
    /* Citation badge */
    .citation-badge {
        display: inline-block;
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.2);
        color: #38bdf8 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 8px;
        margin-top: 8px;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    
    .citation-badge:hover {
        background: rgba(56, 189, 248, 0.15);
        border-color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="app-header">
    <div class="app-title">WealthSearchAI</div>
    <div class="app-subtitle">Compliance-First Hybrid RAG Mutual Fund Chatbot</div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("## ⚙️ Configuration")

# Read credentials from env
groq_key_default = os.getenv("GROQ_API_KEY", "")
gemini_key_default = os.getenv("GEMINI_API_KEY", "")

groq_key = st.sidebar.text_input("Groq API Key", value=groq_key_default, type="password", help="Required for LLM answer generation using Llama-3.")
gemini_key = st.sidebar.text_input("Gemini API Key", value=gemini_key_default, type="password", help="Optional: Enables high-fidelity Google text-embedding-004. If empty, falls back to offline SentenceTransformers.")

# Dynamically apply key changes
if groq_key != groq_key_default:
    os.environ["GROQ_API_KEY"] = groq_key
if gemini_key != gemini_key_default:
    os.environ["GEMINI_API_KEY"] = gemini_key

# Developer Ingestion Trigger
st.sidebar.markdown("## 🔄 Data Operations")
if st.sidebar.button("Trigger Scraper Ingestion"):
    with st.spinner("Scraping schemes & updating index..."):
        try:
            from backend.scraper import GrowwScraper
            from backend.indexer import run_indexing_pipeline
            
            scraper = GrowwScraper(use_headless_browser=True)
            results = scraper.scrape_all_scoped_schemes()
            
            os.makedirs('data', exist_ok=True)
            out_path = 'data/scraped_schemes.json'
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
                
            run_indexing_pipeline(out_path)
            st.sidebar.success("Ingestion & re-indexing completed successfully!")
        except Exception as e:
            st.sidebar.error(f"Ingestion run failed: {e}")

# SEBI Guardrail Notice
st.sidebar.markdown("## 🛡️ SEBI Compliance")
st.sidebar.markdown("""
<div class="compliance-box" style="font-size: 0.85rem; margin-top: 10px;">
    <strong>Strict Compliance Scoping:</strong><br/>
    Assists only with objective data retrieved from factsheets. Speculative advice or general buying tips are auto-blocked to conform to regulatory disclaimers.
</div>
""", unsafe_allow_html=True)

# Scoped Mutual Funds list
st.sidebar.markdown("## 📊 Scoped Mutual Funds")
with st.sidebar.expander("View Supported Schemes (8)", expanded=True):
    for key, data in VERIFIED_SCHEME_DB.items():
        st.markdown(f"""
        <div class="fund-card">
            <strong>{data['fund_name']}</strong><br/>
            <span style="font-size: 0.82rem; color: #94a3b8;">
                NAV: ₹{data['current_nav']:.2f} | AUM: ₹{data['aum_in_crores']:.1f} Cr<br/>
                Rating: {data['public_rating']['stars']} ⭐ ({data['public_rating']['total_reviews']} reviews)
            </span>
        </div>
        """, unsafe_allow_html=True)


# --- CHAT & RAG ENGINE ---
# Instantiate response generator
@st.cache_resource
def get_generator():
    return RAGResponseGenerator()

generator = get_generator()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "Welcome to **WealthSearchAI**! I am an AI assistant grounded in official factsheet databases.\n\nAsk me about NAVs, expense ratios, holdings, manager backgrounds, or exit loads for our scoped mutual funds.",
            "citations": [],
            "chart_data": []
        }
    ]

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("chart_data"):
            # Render comparison chart
            st.markdown("### 📊 Fund Comparison Chart")
            
            # Map display names to keys in VERIFIED_SCHEME_DB
            mapped_keys = []
            for display in msg["chart_data"]:
                for key, data in VERIFIED_SCHEME_DB.items():
                    if display.lower() in data["fund_name"].lower() or key in display.lower().replace(" ", "-"):
                        mapped_keys.append(key)
                        break
                        
            if mapped_keys:
                chart_records = []
                for key in mapped_keys:
                    data = VERIFIED_SCHEME_DB[key]
                    perf = data["performance_timelines"]
                    chart_records.append({
                        "Fund": data["fund_name"].replace(" Direct Growth", "").replace(" Direct Plan Growth", "").strip(),
                        "3-Year Return (%)": perf.get("3_year_return_pct") or 0.0,
                        "5-Year Return (%)": perf.get("5_year_return_pct") or 0.0,
                        "10-Year Return (%)": perf.get("10_year_return_pct") or 0.0,
                        "Expense Ratio (%)": data["expense_ratio_pct"] or 0.0,
                        "AUM (₹ Cr)": data["aum_in_crores"] or 0.0
                    })
                df = pd.DataFrame(chart_records)
                
                t1, t2, t3 = st.tabs(["📈 Returns (%)", "💸 Expense Ratio (%)", "🏦 AUM (₹ Cr)"])
                with t1:
                    st.bar_chart(df.set_index("Fund")[["3-Year Return (%)", "5-Year Return (%)", "10-Year Return (%)"]])
                with t2:
                    st.bar_chart(df.set_index("Fund")[["Expense Ratio (%)"]])
                with t3:
                    st.bar_chart(df.set_index("Fund")[["AUM (₹ Cr)"]])

        if msg.get("citations"):
            st.markdown("**Sources & Factsheets:**")
            cols = st.columns(len(msg["citations"]))
            for idx, cite in enumerate(msg["citations"]):
                cols[idx].markdown(f'<a href="{cite["url"]}" target="_blank" class="citation-badge">🔗 {cite["fund_name"]}</a>', unsafe_allow_html=True)

# Click-to-ask follow-up questions
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]
    if last_msg.get("suggested_followups"):
        st.markdown("**Suggested Questions:**")
        cols = st.columns(len(last_msg["suggested_followups"]))
        for idx, q_text in enumerate(last_msg["suggested_followups"]):
            if cols[idx].button(q_text, key=f"btn_{idx}_{len(st.session_state.messages)}"):
                st.session_state.current_question = q_text
                st.rerun()

# Capture input
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

user_query = st.chat_input("Ask a question about the mutual funds...")

# Override query if button was clicked
if st.session_state.current_question:
    user_query = st.session_state.current_question
    st.session_state.current_question = "" # Reset

# Run prompt lifecycle
if user_query:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
    
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Generate RAG response
    with st.chat_message("assistant"):
        with st.spinner("Retrieving compliance context and synthesizing answer..."):
            res = generator.generate_response(user_query)
            
            # Print response
            st.markdown(res["answer"])
            
            # Comparison chart if triggered
            if res.get("comparison_funds"):
                st.markdown("### 📊 Fund Comparison Chart")
                mapped_keys = []
                for display in res["comparison_funds"]:
                    for key, data in VERIFIED_SCHEME_DB.items():
                        if display.lower() in data["fund_name"].lower() or key in display.lower().replace(" ", "-"):
                            mapped_keys.append(key)
                            break
                            
                if mapped_keys:
                    chart_records = []
                    for key in mapped_keys:
                        data = VERIFIED_SCHEME_DB[key]
                        perf = data["performance_timelines"]
                        chart_records.append({
                            "Fund": data["fund_name"].replace(" Direct Growth", "").replace(" Direct Plan Growth", "").strip(),
                            "3-Year Return (%)": perf.get("3_year_return_pct") or 0.0,
                            "5-Year Return (%)": perf.get("5_year_return_pct") or 0.0,
                            "10-Year Return (%)": perf.get("10_year_return_pct") or 0.0,
                            "Expense Ratio (%)": data["expense_ratio_pct"] or 0.0,
                            "AUM (₹ Cr)": data["aum_in_crores"] or 0.0
                        })
                    df = pd.DataFrame(chart_records)
                    
                    t1, t2, t3 = st.tabs(["📈 Returns (%)", "💸 Expense Ratio (%)", "🏦 AUM (₹ Cr)"])
                    with t1:
                        st.bar_chart(df.set_index("Fund")[["3-Year Return (%)", "5-Year Return (%)", "10-Year Return (%)"]])
                    with t2:
                        st.bar_chart(df.set_index("Fund")[["Expense Ratio (%)"]])
                    with t3:
                        st.bar_chart(df.set_index("Fund")[["AUM (₹ Cr)"]])
            
            # Print citations
            if res.get("citations"):
                st.markdown("**Sources & Factsheets:**")
                cols = st.columns(len(res["citations"]))
                for idx, cite in enumerate(res["citations"]):
                    cols[idx].markdown(f'<a href="{cite["url"]}" target="_blank" class="citation-badge">🔗 {cite["fund_name"]}</a>', unsafe_allow_html=True)
                    
    # Store assistant response to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": res["answer"],
        "citations": res.get("citations", []),
        "chart_data": res.get("comparison_funds", []),
        "suggested_followups": res.get("suggested_followups", [])
    })
    st.rerun()

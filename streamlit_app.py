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
import numpy as np
import plotly.graph_objects as go
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

# --- CUSTOM CSS & TYPOGRAPHY ---
st.markdown("""
<style>
    /* Main Background, Typography & Scrollbars */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6, .app-title, .chat-terminal-title {
        font-family: 'Outfit', sans-serif !important;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0a0b10 0%, #06070a 100%) !important;
    }
    
    /* Background Blobs */
    .bg-blob {
        position: fixed;
        width: 450px;
        height: 450px;
        border-radius: 50%;
        filter: blur(140px);
        opacity: 0.12;
        z-index: -1;
        pointer-events: none;
    }
    
    .blob-1 {
        background-color: #0088ff;
        top: -120px;
        left: 20%;
    }
    
    .blob-2 {
        background-color: #00e5ff;
        bottom: -120px;
        right: 15%;
    }
    
    /* Custom Sidebar override */
    section[data-testid="stSidebar"] {
        background-color: #10131a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 0px !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        padding: 0px !important;
        gap: 0px !important;
    }
    
    /* Custom Sidebar Card Styling */
    .sidebar-container {
        padding: 24px 16px;
        background-color: #10131a;
        height: 100vh;
        display: flex;
        flex-direction: column;
        overflow-y: auto;
    }
    
    .brand-header {
        display: flex;
        align-items: center;
        margin-bottom: 28px;
        gap: 12px;
    }
    
    .brand-icon-square {
        width: 44px;
        height: 44px;
        background-color: #a8c8ff;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .brand-svg-icon {
        width: 24px;
        height: 24px;
        fill: #003061;
    }
    
    .brand-name {
        color: #e0e2ec;
        font-size: 1.35rem;
        font-weight: 700;
        line-height: 1.1;
    }
    
    .brand-subtitle {
        color: #8a919f;
        font-size: 0.72rem;
        font-weight: 400;
    }
    
    .funds-list-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 24px;
    }
    
    .fund-card {
        display: flex;
        align-items: center;
        padding: 12px 14px;
        border-radius: 12px;
        text-decoration: none !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    .fund-card-icon-container {
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 10px;
    }
    
    .fund-card-icon {
        width: 18px;
        height: 18px;
        stroke: #8a919f;
        stroke-width: 2;
        fill: none;
    }
    
    .fund-card-details {
        flex-grow: 1;
    }
    
    .fund-card-title {
        color: #e0e2ec;
        font-size: 0.88rem;
        font-weight: 600;
    }
    
    .fund-card-nav {
        color: #8a919f;
        font-size: 0.72rem;
        margin-top: 1px;
    }
    
    .fund-card-rating {
        color: #e0e2ec;
        font-size: 0.78rem;
        font-weight: 500;
    }
    
    /* Highlighted active card */
    .fund-card.active {
        background: linear-gradient(90deg, #00daf3 0%, #00f0ff 100%) !important;
        border: none !important;
    }
    
    .fund-card.active .fund-card-title {
        color: #0a0e15 !important;
        font-weight: 700;
    }
    
    .fund-card.active .fund-card-nav {
        color: rgba(10, 14, 21, 0.8) !important;
    }
    
    .fund-card.active .fund-card-rating {
        color: #0a0e15 !important;
        font-weight: 600;
    }
    
    .fund-card.active .fund-card-icon {
        stroke: #0a0e15 !important;
    }
    
    .fund-card:not(.active):hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: #00daf3;
        transform: translateY(-1px);
    }
    
    /* Transactions Section */
    .transactions-section {
        margin-top: auto;
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 16px;
    }
    
    .section-title {
        color: #8a919f;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    
    .transaction-card {
        background: rgba(255, 255, 255, 0.015);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 10px 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .tx-left {
        display: flex;
        flex-direction: column;
        gap: 1px;
    }
    
    .tx-title {
        color: #e0e2ec;
        font-size: 0.82rem;
        font-weight: 600;
    }
    
    .tx-date {
        color: #8a919f;
        font-size: 0.68rem;
    }
    
    .tx-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 1px;
    }
    
    .tx-amount {
        font-size: 0.82rem;
        font-weight: 700;
    }
    
    .tx-amount.success {
        color: #00daf3;
    }
    
    .tx-amount.settled {
        color: #feb019;
    }
    
    .tx-status {
        font-size: 0.62rem;
        font-weight: 700;
    }
    
    .tx-status.success {
        color: #00daf3;
    }
    
    .tx-status.settled {
        color: #feb019;
    }
    
    .see-all-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 2px;
    }
    
    .see-all-link {
        color: #8a919f;
        text-decoration: none;
        font-size: 0.78rem;
        font-weight: 600;
        transition: color 0.2s ease;
    }
    
    .see-all-link:hover {
        color: #00daf3;
    }
    
    .sidebar-footer {
        border-top: 1px solid rgba(255, 255, 255, 0.04);
        padding-top: 12px;
        text-align: center;
        color: rgba(138, 145, 159, 0.4);
        font-size: 0.68rem;
        line-height: 1.3;
    }
    
    /* Top Navigation bar */
    .top-nav-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        background: rgba(16, 19, 26, 0.4);
        backdrop-filter: blur(15px);
        margin-bottom: 24px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.04);
    }
    
    .top-nav-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .hamburger-icon {
        width: 22px;
        height: 22px;
        cursor: pointer;
    }
    
    .chat-terminal-title {
        color: #e0e2ec;
        font-size: 1.2rem;
        font-weight: 700;
        margin: 0;
    }
    
    .top-nav-right {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .compliance-badge {
        background: rgba(0, 218, 243, 0.06);
        border: 1px solid rgba(0, 218, 243, 0.15);
        color: #00daf3;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
        letter-spacing: 0.02em;
    }
    
    .badge-dot {
        width: 6px;
        height: 6px;
        background-color: #00daf3;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #00daf3;
    }
    
    .avatar-container {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        padding: 1.5px;
        background: linear-gradient(135deg, #00daf3 0%, #0088ff 100%);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .avatar-image {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid #0a0e15;
    }
    
    /* Native Chat Message styling overrides for Glassmorphism */
    div[data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 16px !important;
        padding: 18px 22px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12) !important;
    }
    
    div[data-testid="stChatMessage"] img {
        border-radius: 10px !important;
    }
    
    /* Style Chat Input */
    div[data-testid="stChatInput"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 14px !important;
        padding: 6px !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #e0e2ec !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    
    /* Citation badges */
    .citation-badge {
        display: inline-block;
        background: rgba(0, 218, 243, 0.08);
        border: 1px solid rgba(0, 218, 243, 0.2);
        color: #00daf3 !important;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        margin-right: 6px;
        margin-top: 6px;
        text-decoration: none;
        transition: all 0.2s ease;
    }
    
    .citation-badge:hover {
        background: rgba(0, 218, 243, 0.15);
        border-color: #00daf3;
    }
</style>
""", unsafe_allow_html=True)

# Render Background Blobs
st.markdown('<div class="bg-blob blob-1"></div><div class="bg-blob blob-2"></div>', unsafe_allow_html=True)


# --- AVATAR CONSTANTS (matching brand icon in design) ---
# Blue square with trend-line icon — exactly as shown in image1.png
ASSISTANT_AVATAR = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 44 44'%3E"
    "%3Crect width='44' height='44' rx='10' fill='%23a8c8ff'/%3E"
    "%3Cpolyline points='8,32 17,20 25,26 36,11' stroke='%23003061' stroke-width='2.8' "
    "fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E"
    "%3Cpolyline points='30,11 36,11 36,17' stroke='%23003061' stroke-width='2.8' "
    "fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E"
    "%3C/svg%3E"
)
# Dark rounded square with person silhouette for user
USER_AVATAR = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 44 44'%3E"
    "%3Crect width='44' height='44' rx='10' fill='%231c2027'/%3E"
    "%3Ccircle cx='22' cy='17' r='7' fill='%238a919f'/%3E"
    "%3Cpath d='M7 40 C7 30 37 30 37 40' fill='%238a919f'/%3E"
    "%3C/svg%3E"
)


# --- MUTUAL FUND DATA VISUAL SCHEMES ---
FUND_VISUAL_METADATA = {
    "nippon-india-small-cap-fund-direct-growth": {
        "visual_name": "Bluechip Fund",
        "icon_svg": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline>',
        "nav": "₹164.50",
        "rating": "4.8"
    },
    "parag-parikh-long-term-value-fund-direct-growth": {
        "visual_name": "Flexi Cap Fund",
        "icon_svg": '<rect x="2" y="5" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line>',
        "nav": "₹82.12",
        "rating": "4.6"
    },
    "edelweiss-mid-and-small-cap-fund-direct-growth": {
        "visual_name": "Tax Saver ELSS",
        "icon_svg": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>',
        "nav": "₹45.30",
        "rating": "4.7"
    },
    "bandhan-small-cap-fund-direct-growth": {
        "visual_name": "Midcap Opportunities",
        "icon_svg": '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
        "nav": "₹112.45",
        "rating": "4.9"
    },
    "bandhan-midcap-fund-direct-growth": {
        "visual_name": "Small Cap Index",
        "icon_svg": '<rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect>',
        "nav": "₹28.90",
        "rating": "4.5"
    },
    "bandhan-multi-cap-fund-direct-growth": {
        "visual_name": "Liquid Debt Fund",
        "icon_svg": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>',
        "nav": "₹18.90",
        "rating": "4.4"
    },
    "zerodha-multi-asset-passive-fof-direct-growth": {
        "visual_name": "Passive FoF Fund",
        "icon_svg": '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
        "nav": "₹12.40",
        "rating": "4.2"
    },
    "nippon-india-multi-asset-allocation-fund-direct-growth": {
        "visual_name": "Multi Asset Alloc",
        "icon_svg": '<path d="M12 2L2 7l10 5 10-5-10-5z"></path><path d="M2 17l10 5 10-5"></path><path d="M2 12l10 5 10-5"></path>',
        "nav": "₹15.60",
        "rating": "4.6"
    }
}


# --- NAV HISTORY CHART HELPER ---
def render_nav_chart(mapped_keys: list):
    """
    Render a smooth area/line chart of simulated 24-month NAV history for the given fund keys.
    Matches the design in image1.png: dark background, cyan + blue traces, minimal grid.
    """
    CHART_COLORS = ["#00daf3", "#a8c8ff", "#feb019", "#00e5ff"]
    months = pd.date_range(end=pd.Timestamp.now(), periods=24, freq="ME")

    fig = go.Figure()

    for i, key in enumerate(mapped_keys):
        db_fund = VERIFIED_SCHEME_DB.get(key)
        if not db_fund:
            continue

        nav = db_fund["current_nav"]
        visual_name = FUND_VISUAL_METADATA.get(key, {}).get("visual_name", db_fund["fund_name"])
        color = CHART_COLORS[i % len(CHART_COLORS)]

        # Simulate 24-month NAV history working backward from current NAV
        perf = db_fund.get("performance_timelines", {})
        annual_return = (perf.get("3_year_return_pct") or 18.0) / 100.0
        monthly_avg = (1 + annual_return) ** (1 / 12) - 1

        np.random.seed(i * 17 + 31)
        noise = np.random.normal(0, 0.022, 24)

        nav_series = [float(nav)]
        for j in range(23):
            prev = nav_series[0]
            step = prev / (1 + monthly_avg + noise[j])
            nav_series.insert(0, max(step, 1.0))

        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        fig.add_trace(go.Scatter(
            x=months,
            y=nav_series,
            name=visual_name,
            mode="lines",
            line=dict(color=color, width=2.5, shape="spline", smoothing=1.2),
            fill="tozeroy",
            fillcolor=f"rgba({r},{g},{b},0.07)",
            hovertemplate=f"<b>{visual_name}</b><br>%{{x|%b %Y}}<br>NAV: ₹%{{y:.2f}}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8a919f", family="Plus Jakarta Sans"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#e0e2ec", size=12),
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="#8a919f", size=11),
            showline=False,
            zeroline=False,
            tickformat="%b",
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.04)",
            tickfont=dict(color="#8a919f", size=11),
            tickprefix="₹",
            showline=False,
            zeroline=False,
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=280,
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(16,19,26,0.95)",
            bordercolor="rgba(255,255,255,0.08)",
            font=dict(color="#e0e2ec", family="Plus Jakarta Sans"),
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# --- SIDEBAR GENERATION ---
# Get active fund selection from URL query parameters (defaults to nippon small cap)
query_params = st.query_params
selected_fund_key = query_params.get("fund", "nippon-india-small-cap-fund-direct-growth")

if selected_fund_key not in FUND_VISUAL_METADATA:
    selected_fund_key = "nippon-india-small-cap-fund-direct-growth"

# Compile Sidebar HTML
sidebar_html = f"""
<div class="sidebar-container">
    <!-- Brand Header -->
    <div class="brand-header">
        <div class="brand-icon-square">
            <svg class="brand-svg-icon" viewBox="0 0 24 24">
                <path d="M4 10h3v7H4zM10.5 5h3v12h-3zM17 12h3v5h-3z"/>
                <path d="M2 20h20v2H2z"/>
            </svg>
        </div>
        <div class="brand-text-container">
            <div class="brand-name">WealthSearchAI</div>
            <div class="brand-subtitle">Scoped Groww RAG Assistant</div>
        </div>
    </div>
    
    <!-- Funds List -->
    <div class="funds-list-container">
"""

for key, meta in FUND_VISUAL_METADATA.items():
    is_active = (key == selected_fund_key)
    active_class = "active" if is_active else ""
    
    # Read dynamic NAV and ratings from actual scraping database if available
    db_fund = VERIFIED_SCHEME_DB.get(key)
    nav_val = f"₹{db_fund['current_nav']:.2f}" if db_fund else meta["nav"]
    rating_val = f"{db_fund['public_rating']['stars']}" if db_fund else meta["rating"]
    
    sidebar_html += f"""
        <a href="?fund={key}" target="_self" class="fund-card {active_class}">
            <div class="fund-card-icon-container">
                <svg class="fund-card-icon" viewBox="0 0 24 24">
                    {meta['icon_svg']}
                </svg>
            </div>
            <div class="fund-card-details">
                <div class="fund-card-title">{meta['visual_name']}</div>
                <div class="fund-card-nav">NAV: {nav_val}</div>
            </div>
            <div class="fund-card-rating">{rating_val} ★</div>
        </a>
    """

sidebar_html += """
    </div>

    <!-- Recent Transactions Section -->
    <div class="transactions-section">
        <div class="section-title">RECENT TRANSACTIONS</div>
        <div class="transaction-card">
            <div class="tx-left">
                <div class="tx-title">Buy: Bluechip Fund</div>
                <div class="tx-date">24 Oct 2023</div>
            </div>
            <div class="tx-right">
                <div class="tx-amount success">+₹5,000.00</div>
                <div class="tx-status success">● SUCCESS</div>
            </div>
        </div>
        <div class="transaction-card">
            <div class="tx-left">
                <div class="tx-title">Sell: Arbitrage Fund</div>
                <div class="tx-date">21 Oct 2023</div>
            </div>
            <div class="tx-right">
                <div class="tx-amount settled">-₹12,450.00</div>
                <div class="tx-status settled">● SETTLED</div>
            </div>
        </div>
        <div class="transaction-card">
            <div class="tx-left">
                <div class="tx-title">SIP: Midcap Opp.</div>
                <div class="tx-date">15 Oct 2023</div>
            </div>
            <div class="tx-right">
                <div class="tx-amount success">+₹2,000.00</div>
                <div class="tx-status success">● PROCESSED</div>
            </div>
        </div>
        <div class="see-all-container">
            <a href="#" class="see-all-link">See All &gt;</a>
            <svg class="filter-icon" viewBox="0 0 24 24" style="width: 14px; height: 14px; stroke: #8a919f; stroke-width: 2; fill: none;">
                <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
            </svg>
        </div>
    </div>

    <!-- Sidebar Footer -->
    <div class="sidebar-footer">
        Premium Mutual Fund AI<br/>v2.4.0–STABLE
    </div>
</div>
"""

# Render Sidebar HTML
with st.sidebar:
    st.markdown(sidebar_html, unsafe_allow_html=True)


# --- MAIN CONTENT PANEL ---
# Top Navigation bar
st.markdown("""
<div class="top-nav-bar">
    <div class="top-nav-left">
        <svg class="hamburger-icon" viewBox="0 0 24 24" style="width: 22px; height: 22px; fill: none; stroke: #8a919f; stroke-width: 2;">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
        <span class="chat-terminal-title">Chat Terminal</span>
    </div>
    <div class="top-nav-right">
        <span class="compliance-badge"><span class="badge-dot"></span>SEBI COMPLIANCE GROUNDED</span>
        <div class="avatar-container">
            <img class="avatar-image" src="https://api.dicebear.com/7.x/bottts-neutral/svg?seed=WealthAI" alt="Avatar"/>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- CHAT & RAG PROCESSOR ENGINE ---
# Instantiate response generator
@st.cache_resource
def get_generator():
    return RAGResponseGenerator()

generator = get_generator()

# Initialize chat history with design mockup parameters
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome to **WealthSearchAI**. How can I help with your mutual fund queries today?\n\nI have real-time access to SEBI-grounded data and Groww product metrics.",
            "citations": [],
            "chart_data": ["nippon-india-small-cap-fund-direct-growth", "bandhan-small-cap-fund-direct-growth"],
            "suggested_followups": [
                f"Compare exit load of {FUND_VISUAL_METADATA['nippon-india-small-cap-fund-direct-growth']['visual_name']} and {FUND_VISUAL_METADATA['parag-parikh-long-term-value-fund-direct-growth']['visual_name']}",
                f"Who manages {FUND_VISUAL_METADATA['parag-parikh-long-term-value-fund-direct-growth']['visual_name']}?",
                f"Show expense ratio of {FUND_VISUAL_METADATA['edelweiss-mid-and-small-cap-fund-direct-growth']['visual_name']}"
            ]
        }
    ]

# Display past messages
for msg in st.session_state.messages:
    avatar_url = ASSISTANT_AVATAR if msg["role"] == "assistant" else USER_AVATAR

    with st.chat_message(msg["role"], avatar=avatar_url):
        st.markdown(msg["content"])

        # Render NAV history area chart if chart_data is present
        if msg.get("chart_data"):
            mapped_keys = []
            for display in msg["chart_data"]:
                # Direct key match first (used in initial welcome message)
                if display in VERIFIED_SCHEME_DB:
                    mapped_keys.append(display)
                    continue
                # Fallback: fuzzy name/key match (used in RAG comparison responses)
                for key, data in VERIFIED_SCHEME_DB.items():
                    visual_name = FUND_VISUAL_METADATA.get(key, {}).get("visual_name", "")
                    if (display.lower() in data["fund_name"].lower() or
                            display.lower() in visual_name.lower() or
                            key in display.lower().replace(" ", "-")):
                        mapped_keys.append(key)
                        break

            # De-duplicate while preserving order
            mapped_keys = list(dict.fromkeys(mapped_keys))

            if mapped_keys:
                render_nav_chart(mapped_keys)

        # Render citations
        if msg.get("citations"):
            st.markdown("**Sources & Factsheets:**")
            cols = st.columns(len(msg["citations"]))
            for idx, cite in enumerate(msg["citations"]):
                cols[idx].markdown(f'<a href="{cite["url"]}" target="_blank" class="citation-badge">🔗 {cite["fund_name"]}</a>', unsafe_allow_html=True)

# Click-to-ask follow-up questions
if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
    last_msg = st.session_state.messages[-1]
    if last_msg.get("suggested_followups"):
        st.markdown("<div style='margin-top: 12px; margin-bottom: 4px; font-size: 0.85rem; font-weight: 700; color: #8a919f;'>SUGGESTED QUESTIONS:</div>", unsafe_allow_html=True)
        cols = st.columns(len(last_msg["suggested_followups"]))
        for idx, q_text in enumerate(last_msg["suggested_followups"]):
            btn_label = q_text
            if len(btn_label) > 42:
                btn_label = btn_label[:40] + "..."
            if cols[idx].button(btn_label, key=f"btn_{idx}_{len(st.session_state.messages)}", use_container_width=True):
                st.session_state.current_question = q_text
                st.rerun()

# Capture query input
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

user_query = st.chat_input("Ask about fund performance, exit loads, or expense ratios...")

# Override query if button was clicked
if st.session_state.current_question:
    user_query = st.session_state.current_question
    st.session_state.current_question = ""  # Reset

# Ingestion trigger
if user_query:
    # Display user input bubble
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_query)

    st.session_state.messages.append({"role": "user", "content": user_query})

    # Process RAG generation
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("Retrieving compliance context and synthesizing answer..."):
            res = generator.generate_response(user_query)

            # Print response
            st.markdown(res["answer"])

            # Render NAV history chart if comparison funds returned
            if res.get("comparison_funds"):
                mapped_keys = []
                for display in res["comparison_funds"]:
                    if display in VERIFIED_SCHEME_DB:
                        mapped_keys.append(display)
                        continue
                    for key, data in VERIFIED_SCHEME_DB.items():
                        visual_name = FUND_VISUAL_METADATA.get(key, {}).get("visual_name", "")
                        if (display.lower() in data["fund_name"].lower() or
                                display.lower() in visual_name.lower() or
                                key in display.lower().replace(" ", "-")):
                            mapped_keys.append(key)
                            break

                mapped_keys = list(dict.fromkeys(mapped_keys))

                if mapped_keys:
                    render_nav_chart(mapped_keys)

            # Print citations
            if res.get("citations"):
                st.markdown("**Sources & Factsheets:**")
                cols = st.columns(len(res["citations"]))
                for idx, cite in enumerate(res["citations"]):
                    cols[idx].markdown(f'<a href="{cite["url"]}" target="_blank" class="citation-badge">🔗 {cite["fund_name"]}</a>', unsafe_allow_html=True)

    # Map back standard visual display names in suggested follow-ups
    formatted_followups = []
    for f in res.get("suggested_followups", []):
        modified_f = f
        for key, visual in FUND_VISUAL_METADATA.items():
            db_fund = VERIFIED_SCHEME_DB.get(key)
            if db_fund:
                modified_f = modified_f.replace(db_fund["fund_name"].replace(" Direct Growth", "").replace(" Direct Plan Growth", "").strip(), visual["visual_name"])
                modified_f = modified_f.replace(db_fund["fund_name"], visual["visual_name"])
        formatted_followups.append(modified_f)

    # Store assistant response to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": res["answer"],
        "citations": res.get("citations", []),
        "chart_data": res.get("comparison_funds", []),
        "suggested_followups": formatted_followups
    })
    st.rerun()

# Footer SEBI Advisory Note
st.markdown("""
<div style="text-align: center; color: rgba(138, 145, 159, 0.6); font-size: 0.75rem; margin-top: 16px; display: flex; align-items: center; justify-content: center; gap: 6px;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="stroke-linecap: round; stroke-linejoin: round;">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
    </svg>
    All information is scraped daily from verified Groww product details. Mutual fund investments are subject to market risks.
</div>
""", unsafe_allow_html=True)

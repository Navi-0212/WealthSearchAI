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
import textwrap
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from backend.generator import RAGResponseGenerator
from backend.scraper import VERIFIED_SCHEME_DB
import streamlit.components.v1 as components

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
        color: #0088ff;
    }
    
    .tx-status {
        font-size: 0.62rem;
        font-weight: 700;
    }
    
    .tx-status.success {
        color: #00daf3;
    }
    
    .tx-status.settled {
        color: #0088ff;
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

    /* Sidebar fund button styling (Streamlit native buttons override) */
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.025) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        color: #e0e2ec !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        min-height: 0 !important;
        line-height: 1.35 !important;
        transition: all 0.25s ease !important;
        width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.055) !important;
        border-color: rgba(0, 218, 243, 0.5) !important;
        transform: translateY(-1px) !important;
    }
    
    section[data-testid="stSidebar"] button[kind="primary"],
    div[data-testid="stVerticalBlock"] button[kind="primary"],
    button[kind="primary"] {
        background: #0088ff !important;
        border: none !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-align: left !important;
        padding: 10px 14px !important;
        min-height: 0 !important;
        line-height: 1.35 !important;
        width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    section[data-testid="stSidebar"] button[kind="primary"]:hover,
    div[data-testid="stVerticalBlock"] button[kind="primary"]:hover,
    button[kind="primary"]:hover {
        background: #0077e6 !important;
    }
    
    /* Force override any Streamlit default orange colors */
    section[data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    div[data-testid="stVerticalBlock"] button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"] {
        background-color: #0088ff !important;
    }
    
    /* Override any inline styles that might set orange */
    button[style*="background"] {
        background: #0088ff !important;
    }
    
    /* Fund Summary Page Styling */
    
    /* Enhanced Search Bar - 1.5x size */
    section[data-testid="stSidebar"] input[type="text"] {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e0e2ec !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 500 !important;
        padding: 14px 18px !important;
        height: 54px !important;
        line-height: 1.4 !important;
        transition: all 0.25s ease !important;
    }
    section[data-testid="stSidebar"] input[type="text"]:focus {
        border-color: #00daf3 !important;
        box-shadow: 0 0 0 2px rgba(0, 218, 243, 0.15) !important;
        background: rgba(255, 255, 255, 0.06) !important;
    }
    section[data-testid="stSidebar"] input[type="text"]::placeholder {
        color: #6b7280 !important;
        font-size: 1.0rem !important;
    }
    /* Search bar container spacing — increased gap to fund list */
    section[data-testid="stSidebar"] div[data-testid="stTextInput"] {
        padding: 8px 14px 0 14px !important;
        margin-bottom: 20px !important;
    }
    
    .fund-summary-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 20px;
    }
    
    .fund-summary-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .fund-summary-icon {
        width: 48px;
        height: 48px;
        background: rgba(0, 218, 243, 0.08);
        border: 1px solid rgba(0, 218, 243, 0.15);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .fund-summary-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.4rem;
        font-weight: 700;
        color: #e0e2ec;
    }
    
    .fund-summary-subtitle {
        color: #8a919f;
        font-size: 0.78rem;
        margin-top: 2px;
    }
    
    .fund-stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 24px;
    }
    
    .fund-stat-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 14px 16px;
    }
    
    .fund-stat-label {
        color: #8a919f;
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    
    .fund-stat-value {
        color: #e0e2ec;
        font-size: 1.1rem;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
    }
    
    .fund-stat-value.highlight {
        color: #00daf3;
    }
    
    .fund-section-title {
        color: #e0e2ec;
        font-family: 'Outfit', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 12px;
        margin-top: 8px;
    }
    
    .fund-holdings-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    
    .fund-holdings-table th {
        color: #8a919f;
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .fund-holdings-table td {
        color: #e0e2ec;
        font-size: 0.82rem;
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    
    .fund-holdings-table tr:hover td {
        background: rgba(255, 255, 255, 0.02);
    }
    
    .fund-manager-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .fund-manager-name {
        color: #e0e2ec;
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .fund-manager-meta {
        color: #8a919f;
        font-size: 0.75rem;
        line-height: 1.5;
    }
    
    .perf-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    
    .perf-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 10px;
        padding: 12px;
        text-align: center;
    }
    
    .perf-period {
        color: #8a919f;
        font-size: 0.70rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .perf-return {
        color: #00daf3;
        font-size: 1.15rem;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
    }
    
    .perf-return.inactive {
        color: #8a919f;
        font-size: 0.82rem;
    }
    
    .view-toggle-container {
        display: flex;
        gap: 8px;
        margin-bottom: 16px;
    }

    /* Hide Streamlit default UI chrome */
    header[data-testid="stHeader"] { display: none !important; }
    .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
    .block-container { padding-top: 1rem !important; }
    section[data-testid="stSidebar"] { background-color: #10131a !important; }
    section[data-testid="stSidebar"] > div { padding: 0 !important; }
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
        "visual_name": "Nippon India Small Cap Fund Direct Growth",
        "icon_svg": '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline>',
        "nav": "₹164.50",
        "rating": "4.8"
    },
    "parag-parikh-long-term-value-fund-direct-growth": {
        "visual_name": "Parag Parikh Flexi Cap Fund Direct Growth",
        "icon_svg": '<rect x="2" y="5" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line>',
        "nav": "₹84.60",
        "rating": "4.8"
    },
    "edelweiss-mid-and-small-cap-fund-direct-growth": {
        "visual_name": "Edelweiss Midcap Fund Direct Growth",
        "icon_svg": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline>',
        "nav": "₹94.30",
        "rating": "4.5"
    },
    "bandhan-small-cap-fund-direct-growth": {
        "visual_name": "Bandhan Small Cap Fund Direct Growth",
        "icon_svg": '<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
        "nav": "₹36.80",
        "rating": "4.6"
    },
    "bandhan-midcap-fund-direct-growth": {
        "visual_name": "Bandhan Midcap Fund Direct Growth",
        "icon_svg": '<rect x="3" y="3" width="7" height="9"></rect><rect x="14" y="3" width="7" height="5"></rect><rect x="14" y="12" width="7" height="9"></rect><rect x="3" y="16" width="7" height="5"></rect>',
        "nav": "₹24.15",
        "rating": "4.5"
    },
    "bandhan-multi-cap-fund-direct-growth": {
        "visual_name": "Bandhan Multi Cap Fund Direct Growth",
        "icon_svg": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>',
        "nav": "₹18.90",
        "rating": "4.4"
    },
    "zerodha-multi-asset-passive-fof-direct-growth": {
        "visual_name": "Zerodha Multi Asset Passive FoF Direct Growth",
        "icon_svg": '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
        "nav": "₹12.40",
        "rating": "4.2"
    },
    "nippon-india-multi-asset-allocation-fund-direct-growth": {
        "visual_name": "Nippon India Multi Asset Allocation Fund Direct Growth",
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
    CHART_COLORS = ["#00daf3", "#a8c8ff", "#0088ff", "#00e5ff"]
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
# Initialize selected fund in session state
if "selected_fund_key" not in st.session_state:
    query_params = st.query_params
    _init_fund = query_params.get("fund", "nippon-india-small-cap-fund-direct-growth")
    if _init_fund not in FUND_VISUAL_METADATA:
        _init_fund = "nippon-india-small-cap-fund-direct-growth"
    st.session_state.selected_fund_key = _init_fund

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "chat"  # "chat" or "summary"

selected_fund_key = st.session_state.selected_fund_key


def _select_fund(fund_key):
    """Callback to select a fund and switch to summary view."""
    st.session_state.selected_fund_key = fund_key
    st.session_state.view_mode = "summary"


# Use columns instead of sidebar for reliable fund list display
col_funds, col_main = st.columns([1, 3])

with col_funds:
    # Brand header
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;padding:24px 16px 16px 16px;">
        <div style="width:44px;height:44px;min-width:44px;background:#a8c8ff;border-radius:10px;display:flex;align-items:center;justify-content:center;">
            <svg viewBox="0 0 24 24" style="width:24px;height:24px;fill:#003061;"><path d="M4 10h3v7H4zM10.5 5h3v12h-3zM17 12h3v5h-3z"/><path d="M2 20h20v2H2z"/></svg>
        </div>
        <div>
            <div style="color:#e0e2ec;font-size:1.2rem;font-weight:700;line-height:1.1;font-family:'Outfit',sans-serif;">WealthSearchAI</div>
            <div style="color:#8a919f;font-size:0.70rem;font-weight:400;margin-top:2px;">Scoped Groww RAG Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search input
    sidebar_search = st.text_input(
        "Search",
        placeholder="🔍  Search by fund name, category...",
        label_visibility="collapsed",
        key="sidebar_search_input"
    )

    # Fund cards as Streamlit buttons
    _search_query = sidebar_search.lower().strip() if sidebar_search else ""
    _search_words = _search_query.split() if _search_query else []
    _match_count = 0

    st.markdown('<div style="padding: 0 4px; display: flex; flex-direction: column; gap: 6px;">', unsafe_allow_html=True)
    for _key, _meta in FUND_VISUAL_METADATA.items():
        _fund = VERIFIED_SCHEME_DB.get(_key)
        _full_name = _fund["fund_name"] if _fund else _meta["visual_name"]
        _nav = f"\u20b9{_fund['current_nav']:.2f}" if _fund else _meta["nav"]
        _rat = f"{_fund['public_rating']['stars']}" if _fund else _meta["rating"]
        _search_tags = f"{_full_name} {_meta['visual_name']} {_key}".lower()

        # Filter: all search words must match somewhere in the tags
        if _search_words and not all(w in _search_tags for w in _search_words):
            continue
        _match_count += 1

        _is_active = (_key == selected_fund_key)
        _btn_type = "primary" if _is_active else "secondary"
        _label = f"{_full_name}"

        if st.button(_label, key=f"fund_btn_{_key}", type=_btn_type, use_container_width=True,
                     on_click=_select_fund, args=(_key,)):
            pass

    st.markdown('</div>', unsafe_allow_html=True)

    # Show "no results" message if search yielded nothing
    if _search_query and _match_count == 0:
        st.markdown('<div style="text-align:center;color:#8a919f;font-size:0.82rem;padding:16px 8px;">No funds match your search.</div>', unsafe_allow_html=True)

    # Transactions section
    st.markdown("""
    <div style="padding: 16px 16px 0 16px;">
        <div style="color:#8a919f;font-size:0.68rem;font-weight:700;letter-spacing:0.09em;text-transform:uppercase;margin-bottom:10px;">Recent Transactions</div>
        <div style="background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:9px 12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div><div style="color:#e0e2ec;font-size:0.80rem;font-weight:600;">Buy: Bluechip Fund</div><div style="color:#8a919f;font-size:0.66rem;">24 Oct 2023</div></div>
            <div style="text-align:right;"><div style="font-size:0.80rem;font-weight:700;color:#00daf3;">+₹5,000.00</div><div style="font-size:0.60rem;font-weight:700;color:#00daf3;">● SUCCESS</div></div>
        </div>
        <div style="background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:9px 12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div><div style="color:#e0e2ec;font-size:0.80rem;font-weight:600;">Sell: Arbitrage Fund</div><div style="color:#8a919f;font-size:0.66rem;">21 Oct 2023</div></div>
            <div style="text-align:right;"><div style="font-size:0.80rem;font-weight:700;color:#0088ff;">-₹12,450.00</div><div style="font-size:0.60rem;font-weight:700;color:#0088ff;">● SETTLED</div></div>
        </div>
        <div style="background:rgba(255,255,255,0.015);border:1px solid rgba(255,255,255,0.04);border-radius:10px;padding:9px 12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div><div style="color:#e0e2ec;font-size:0.80rem;font-weight:600;">SIP: Midcap Opp.</div><div style="color:#8a919f;font-size:0.66rem;">15 Oct 2023</div></div>
            <div style="text-align:right;"><div style="font-size:0.80rem;font-weight:700;color:#00daf3;">+₹2,000.00</div><div style="font-size:0.60rem;font-weight:700;color:#00daf3;">● PROCESSED</div></div>
        </div>
    </div>
    <div style="border-top:1px solid rgba(255,255,255,0.05);padding:12px 16px;text-align:center;color:rgba(138,145,159,0.45);font-size:0.66rem;line-height:1.4;">Premium Mutual Fund AI<br/>v2.4.0–STABLE</div>
    """, unsafe_allow_html=True)

with col_main:
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

    # View toggle tabs
    tab_summary, tab_chat = st.tabs(["Fund Summary", "Chat Terminal"])

    with tab_summary:
        st.session_state.view_mode = "summary"
        # Call fund summary function
        fund = VERIFIED_SCHEME_DB.get(selected_fund_key)
        if fund:
            meta = FUND_VISUAL_METADATA.get(selected_fund_key, {})
            full_name = fund["fund_name"]
            source_url = fund.get("source_url", "#")
            nav = fund["current_nav"]
            aum = fund["aum_in_crores"]
            expense = fund["expense_ratio_pct"]
            exit_load = fund.get("exit_load_text", "N/A")
            rating = fund["public_rating"]["stars"]
            reviews = fund["public_rating"]["total_reviews"]
            managers = fund.get("fund_managers", [])
            perf = fund.get("performance_timelines", {})
            holdings = fund.get("top_holdings", [])

            # Header + Stats + Exit Load
            st.markdown(textwrap.dedent(f"""\
            <div class="fund-summary-container">
              <div class="fund-summary-header">
                <div class="fund-summary-icon">
                  <svg viewBox="0 0 24 24" style="width:24px;height:24px;stroke:#00daf3;stroke-width:2;fill:none;">
                    <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline>
                    <polyline points="16 7 22 7 22 13"></polyline>
                  </svg>
                </div>
                <div>
                  <div class="fund-summary-title">{full_name}</div>
                  <div class="fund-summary-subtitle">Source: <a href="{source_url}" target="_blank" style="color:#00daf3;text-decoration:none;">Groww Factsheet</a> &nbsp;|&nbsp; {meta.get('visual_name', '')}</div>
                </div>
              </div>
              <div class="fund-stats-grid">
                <div class="fund-stat-card">
                  <div class="fund-stat-label">Current NAV</div>
                  <div class="fund-stat-value highlight">\u20b9{nav:.2f}</div>
                </div>
                <div class="fund-stat-card">
                  <div class="fund-stat-label">AUM</div>
                  <div class="fund-stat-value">\u20b9{aum:,.0f} Cr</div>
                </div>
                <div class="fund-stat-card">
                  <div class="fund-stat-label">Expense Ratio</div>
                  <div class="fund-stat-value">{expense:.2f}%</div>
                </div>
                <div class="fund-stat-card">
                  <div class="fund-stat-label">Rating</div>
                  <div class="fund-stat-value highlight">{rating} \u2605 <span style="font-size:0.72rem;color:#8a919f;font-weight:400;">({reviews:,} reviews)</span></div>
                </div>
              </div>
              <div style="margin-bottom:20px;">
                <div class="fund-stat-label" style="margin-bottom:6px;">EXIT LOAD</div>
                <div style="color:#e0e2ec;font-size:0.85rem;line-height:1.5;">{exit_load}</div>
              </div>
            </div>
            """), unsafe_allow_html=True)

            # Performance returns
            st.markdown(textwrap.dedent("""\
            <div class="fund-section-title">Performance Returns</div>
            """), unsafe_allow_html=True)
            perf_cols = st.columns(4)
            for idx, (period, label) in enumerate([("3_year_return_pct", "3Y"), ("5_year_return_pct", "5Y"), ("7_year_return_pct", "7Y"), ("10_year_return_pct", "10Y")]):
                val = perf.get(period)
                with perf_cols[idx]:
                    if val is not None:
                        st.markdown(textwrap.dedent(f"""\
                        <div class="perf-card">
                          <div class="perf-period">{label}</div>
                          <div class="perf-return">{val:.2f}%</div>
                        </div>
                        """), unsafe_allow_html=True)
                    else:
                        st.markdown(textwrap.dedent(f"""\
                        <div class="perf-card">
                          <div class="perf-period">{label}</div>
                          <div class="perf-return inactive">N/A</div>
                        </div>
                        """), unsafe_allow_html=True)

            # Fund Manager
            st.markdown(textwrap.dedent("""\
            <div class="fund-section-title" style="margin-top:20px;">Fund Manager</div>
            """), unsafe_allow_html=True)
            for mgr in managers:
                work_history_html = "<br>".join([f"\u2022 {w}" for w in mgr.get("work_history", [])])
                st.markdown(textwrap.dedent(f"""\
                <div class="fund-manager-card">
                  <div class="fund-manager-name">{mgr['name']}</div>
                  <div class="fund-manager-meta">
                    <strong>Tenure:</strong> Since {mgr.get('tenure_start', 'N/A')}<br>
                    <strong>Education:</strong> {mgr.get('education', 'N/A')}<br>
                    <strong style="color:#e0e2ec;">Work History:</strong><br>
                    {work_history_html}
                  </div>
                </div>
                """), unsafe_allow_html=True)

            # Top Holdings
            st.markdown(textwrap.dedent("""\
            <div class="fund-section-title" style="margin-top:20px;">Top Holdings</div>
            """), unsafe_allow_html=True)
            rows = ""
            for h in holdings:
                rows += f'<tr><td>{h["company"]}</td><td>{h["sector"]}</td><td style="color:#00daf3;font-weight:600;">{h["allocation_pct"]:.2f}%</td></tr>'
            st.markdown(textwrap.dedent(f"""\
            <table class="fund-holdings-table">
              <thead><tr><th>Company</th><th>Sector</th><th>Allocation</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
            """), unsafe_allow_html=True)
        else:
            st.warning("Fund data not available.")

    with tab_chat:
        st.session_state.view_mode = "chat"

        # --- CHAT & RAG PROCESSOR ENGINE ---
        # Instantiate response generator
        @st.cache_resource
        def get_generator():
            return RAGResponseGenerator()

        generator = get_generator()

        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Proactive suggestions based on selected fund
        if not st.session_state.messages:
            fund = VERIFIED_SCHEME_DB.get(selected_fund_key)
            if fund:
                fund_name = fund["fund_name"]
                st.markdown("### 💡 Suggested Questions:")
                suggestions = [
                    f"What is the current NAV of {fund_name}?",
                    f"Who is the fund manager of {fund_name}?",
                    f"What are the top holdings of {fund_name}?",
                    f"What is the expense ratio of {fund_name}?",
                    f"What is the exit load for {fund_name}?"
                ]
                for suggestion in suggestions:
                    if st.button(suggestion, key=f"suggestion_{suggestion[:20]}"):
                        st.session_state.messages.append({"role": "user", "content": suggestion})
                        with st.chat_message("user"):
                            st.markdown(suggestion)
                        
                        # Generate response
                        with st.chat_message("assistant"):
                            response_placeholder = st.empty()
                            
                            # Check compliance
                            is_compliant, rejection_msg = generator.is_query_compliant(suggestion)
                            if not is_compliant:
                                response_placeholder.markdown(rejection_msg)
                                st.session_state.messages.append({"role": "assistant", "content": rejection_msg})
                            else:
                                # Generate RAG response
                                response = generator.generate_response(suggestion)
                                
                                # Parse and display follow-up questions
                                main_response = response["answer"] if isinstance(response, dict) else response
                                follow_up_questions = []
                                
                                # Extract follow-up questions in <<Question>> format
                                import re
                                question_pattern = r'<<([^>]+)>>'
                                questions = re.findall(question_pattern, main_response)
                                if questions:
                                    main_response = re.sub(question_pattern, '', main_response).strip()
                                    follow_up_questions = questions[:3]  # Take first 3 questions
                                
                                response_placeholder.markdown(main_response)
                                st.session_state.messages.append({"role": "assistant", "content": main_response})
                                
                                # Display follow-up questions as clickable buttons
                                if follow_up_questions:
                                    st.markdown("### 🤔 Follow-up Questions:")
                                    for i, q in enumerate(follow_up_questions):
                                        if st.button(q, key=f"followup_{i}_{len(st.session_state.messages)}"):
                                            st.session_state.messages.append({"role": "user", "content": q})
                                            with st.chat_message("user"):
                                                st.markdown(q)
                                            
                                            # Generate response for follow-up
                                            with st.chat_message("assistant"):
                                                followup_placeholder = st.empty()
                                                is_compliant, rejection_msg = generator.is_query_compliant(q)
                                                if not is_compliant:
                                                    followup_placeholder.markdown(rejection_msg)
                                                    st.session_state.messages.append({"role": "assistant", "content": rejection_msg})
                                                else:
                                                    followup_response = generator.generate_response(q)
                                                    
                                                    # Parse follow-up questions from follow-up response
                                                    followup_main = followup_response["answer"] if isinstance(followup_response, dict) else followup_response
                                                    followup_questions = []
                                                    followup_qs = re.findall(question_pattern, followup_main)
                                                    if followup_qs:
                                                        followup_main = re.sub(question_pattern, '', followup_main).strip()
                                                        followup_questions = followup_qs[:3]
                                                    
                                                    followup_placeholder.markdown(followup_main)
                                                    st.session_state.messages.append({"role": "assistant", "content": followup_main})
                                                    
                                                    if followup_questions:
                                                        st.markdown("### 🤔 Follow-up Questions:")
                                                        for j, fq in enumerate(followup_questions):
                                                            if st.button(fq, key=f"followup_{j}_{len(st.session_state.messages)}"):
                                                                st.session_state.messages.append({"role": "user", "content": fq})
                                                                with st.chat_message("user"):
                                                                    st.markdown(fq)
                                                                
                                                                with st.chat_message("assistant"):
                                                                    fq_placeholder = st.empty()
                                                                    is_compliant, rejection_msg = generator.is_query_compliant(fq)
                                                                    if not is_compliant:
                                                                        fq_placeholder.markdown(rejection_msg)
                                                                        st.session_state.messages.append({"role": "assistant", "content": rejection_msg})
                                                                    else:
                                                                        fq_response = generator.generate_response(fq)
                                                                        fq_main = fq_response["answer"] if isinstance(fq_response, dict) else fq_response
                                                                        fq_main = re.sub(question_pattern, '', fq_main).strip()
                                                                        fq_placeholder.markdown(fq_main)
                                                                        st.session_state.messages.append({"role": "assistant", "content": fq_main})
                                                st.rerun()

        # Chat input
        if prompt := st.chat_input("Ask about mutual funds..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                
                # Check compliance
                is_compliant, rejection_msg = generator.is_query_compliant(prompt)
                if not is_compliant:
                    response_placeholder.markdown(rejection_msg)
                    st.session_state.messages.append({"role": "assistant", "content": rejection_msg})
                else:
                    # Generate RAG response
                    response = generator.generate_response(prompt)
                    
                    # Parse and display follow-up questions
                    main_response = response["answer"] if isinstance(response, dict) else response
                    follow_up_questions = []
                    
                    # Extract follow-up questions in <<Question>> format
                    import re
                    question_pattern = r'<<([^>]+)>>'
                    questions = re.findall(question_pattern, main_response)
                    if questions:
                        main_response = re.sub(question_pattern, '', main_response).strip()
                        follow_up_questions = questions[:3]  # Take first 3 questions
                    
                    response_placeholder.markdown(main_response)
                    st.session_state.messages.append({"role": "assistant", "content": main_response})
                    
                    # Display follow-up questions as clickable buttons
                    if follow_up_questions:
                        st.markdown("### 🤔 Follow-up Questions:")
                        for i, q in enumerate(follow_up_questions):
                            if st.button(q, key=f"followup_{i}_{len(st.session_state.messages)}"):
                                st.session_state.messages.append({"role": "user", "content": q})
                                with st.chat_message("user"):
                                    st.markdown(q)
                                
                                # Generate response for follow-up
                                with st.chat_message("assistant"):
                                    followup_placeholder = st.empty()
                                    is_compliant, rejection_msg = generator.is_query_compliant(q)
                                    if not is_compliant:
                                        followup_placeholder.markdown(rejection_msg)
                                        st.session_state.messages.append({"role": "assistant", "content": rejection_msg})
                                    else:
                                        followup_response = generator.generate_response(q)
                                        
                                        # Parse follow-up questions from follow-up response
                                        followup_main = followup_response["answer"] if isinstance(followup_response, dict) else followup_response
                                        followup_questions = []
                                        followup_qs = re.findall(question_pattern, followup_main)
                                        if followup_qs:
                                            followup_main = re.sub(question_pattern, '', followup_main).strip()
                                            followup_questions = followup_qs[:3]
                                        
                                        followup_placeholder.markdown(followup_main)
                                        st.session_state.messages.append({"role": "assistant", "content": followup_main})
                                        
                                        if followup_questions:
                                            st.markdown("### 🤔 Follow-up Questions:")
                                            for j, fq in enumerate(followup_questions):
                                                if st.button(fq, key=f"followup_{j}_{len(st.session_state.messages)}"):
                                                    st.session_state.messages.append({"role": "user", "content": fq})
                                                    with st.chat_message("user"):
                                                        st.markdown(fq)
                                                    
                                                    with st.chat_message("assistant"):
                                                        fq_placeholder = st.empty()
                                                        is_compliant, rejection_msg = generator.is_query_compliant(fq)
                                                        if not is_compliant:
                                                            fq_placeholder.markdown(rejection_msg)
                                                            st.session_state.messages.append({"role": "assistant", "content": rejection_msg})
                                                        else:
                                                            fq_response = generator.generate_response(fq)
                                                            fq_main = fq_response["answer"] if isinstance(fq_response, dict) else fq_response
                                                            fq_main = re.sub(question_pattern, '', fq_main).strip()
                                                            fq_placeholder.markdown(fq_main)
                                                            st.session_state.messages.append({"role": "assistant", "content": fq_main})
                                    st.rerun()

# Phase-wise Implementation Plan: RAG-Based Mutual Fund FAQ Chatbot

This document details the complete, phase-wise implementation plan for the compliance-first, highly accurate **Retrieval-Augmented Generation (RAG)** virtual wealth assistant. This plan outlines the technical setup, indexing strategy, grounded LLM reasoning loop, and interactive visualization dashboard scoped strictly to 8 targeted Groww mutual fund scheme detail pages.

---

## 1. Project Overview & Boundaries

The chatbot serves as a secure virtual financial assistant for retail investors, relationship managers, and advisors. In accordance with SEBI/SEC compliance standards, it is designed to strictly eliminate hallucinations by operating as a "closed-book" system grounded solely in verified facts scraped daily.

### Scoped Data Sources
1.  **Bandhan Small Cap Fund (Direct Growth)**
2.  **Bandhan Midcap Fund (Direct Growth)**
3.  **Bandhan Multi Cap Fund (Direct Growth)**
4.  **Edelweiss Mid and Small Cap Fund (Direct Growth)**
5.  **Zerodha Multi Asset Passive FoF (Direct Growth)**
6.  **Parag Parikh Long Term Value Fund (Direct Growth)**
7.  **Nippon India Small Cap Fund (Direct Growth)**
8.  **Nippon India Multi Asset Allocation Fund (Direct Growth)**

---

## 2. Phase-by-Phase Development Checklist

### Phase 1: Ingestion & In-Memory Scraping Pipeline (Playwright & BeautifulSoup4)
Verify the asynchronous headless execution engine that hydrates standard React tables, extracts financial metrics daily at 09:15 AM IST, and prepares semantic chunk inputs.
- [x] Configure headless Playwright with sync APIs to fully load target URLs.
- [x] Extract core quantitative fields with safeguards (only overwrite exit loads if specific rate details like %, nil, or zero are present, preserving high-fidelity verified factsheet rates).
- [x] Extract monthly holdings tables dynamically using robust column-mapping headers.
- [x] Parse dynamic top holdings safely into structured JSON arrays without calculator overlaps.
- [x] Extract qualitative details: current Fund Manager names, academic tenures, and educational profiles.
- [x] Scrape comprehensive chronological **Fund Manager Work Histories** (past roles and managed schemes).
- [x] Scrape official **Groww Public Ratings** (Star rating score and review count).
- [x] Extract historical annualized performance returns over **3Y, 5Y, 7Y, and 10Y** timelines.
- [x] Design a high-fidelity static fallback database containing compliance-verified fund facts.
- [x] **Ingestion Semantic-Functional Chunking Strategy**: 
  - Convert portfolio holdings dynamically into rich markdown table grids to preserve visual structures.
  - Separate fund manager biographies from work history details to eliminate context bleed.
  - Package temporal return matrices into descriptive sentence streams (e.g. `Return over 3 Years: X%`).

---

### Phase 2: Semantic Chunking & Enriched Metadata
Split scraped documents into semantic paragraphs to ensure tables, careers, and performance timelines remain coherent.
- [x] Convert dynamic holdings grids and exit loads into clean markdown tables.
- [x] Chunk manager bios and chronological career paths, prefixing them with contextual header tags.
- [x] Package return timelines into descriptive sentence-structured matrices.
- [x] Enrich each generated chunk with a structured metadata schema:
  - `chunk_id`: Unique hash checksum.
  - `source_url`: Verified Groww product link.
  - `fund_name`: Standardized name of the mutual fund.
  - `metric_category`: Enum classifying the content (`NAV`, `Holdings`, `Work History`, `Public Rating`, etc.).
  - `last_scraped`: Ingestion timestamp.
  - `hash_checksum`: MD5 integrity hash.

---

### Phase 3: Knowledge Base & Hybrid Dense-Sparse Indexing
Build a robust dual-indexing layer that combines semantic similarity search with exact keyword matching.
- [x] Generate 768-dimensional dense vector embeddings using Google's `text-embedding-004` API.
- [x] Persist embeddings in local **ChromaDB** storage using cosine similarity metrics.
- [x] Implement a local `SentenceTransformers` model (`all-MiniLM-L6-v2`) and statistical fallsafes as offline vectors.
- [x] Tokenize chunk contents and build an in-memory **BM25** sparse index.
- [x] Serialize the BM25 model to disk as a serialized pickle binary (`data/bm25_store.pkl`).
- [x] Purge obsolete database collections during indexing pipeline runs to prevent stale vector chunks from leaking into query responses.

> [!NOTE]
> **Architecture & Design Decisions:**
> *   **Vector Database (ChromaDB vs. FAISS):** We chose ChromaDB over FAISS. ChromaDB natively supports rich metadata filtering (enabling granular scoping by `fund_name` and `metric_category` at search time), keeps both document texts and embeddings in a single persistent local store (`./db/chroma_store`), and provides very high speed at our corpus size. FAISS was excluded because it requires building a custom text/metadata relational mapping layer and lacks simple native metadata query mechanics.
> *   **Embedding Dimensions & Local Fallback:** 
>     *   *Primary Cloud:* Google's `text-embedding-004` (768 dimensions) for superior accuracy without local CPU overhead.
>     *   *Offline Local Fallback:* `all-MiniLM-L6-v2` (384 dimensions) or `bge-small-en-v1.5`. Heavy models such as `bge-large-en-v1.5` (1024 dimensions, 1.34 GB) were explicitly rejected due to significant loading and inference CPU latency on local setups lacking dedicated NVIDIA CUDA hardware.

---

### Phase 4: Grounded Retrieval & Re-ranking (RRF & Cross-Encoder)
Combine sparse keyword ranks and dense vector ranks to fetch the top context candidates.
- [x] Execute parallel dense vector search and sparse token search.
- [x] Fuse search ranks using **Reciprocal Rank Fusion (RRF)**:
  $$Score_{RRF}(d) = \frac{1}{k + R_{dense}(d)} + \frac{1}{k + R_{sparse}(d)}$$
  *(Where smoothing factor $k = 60$ is applied to minimize outlier ranks).*
- [x] Integrate a **Cross-Encoder Re-ranker** (`ms-marco-MiniLM-L-6-v2`) or a TF-IDF cosine similarity model to filter out noisy context blocks.
- [x] Formulate the final grounded retrieval context containing the top-5 highly relevant chunks.

---

### Phase 5: LLM Grounding & Compliance Guardrails
Configure structured prompt instructions that completely eliminate hallucinations and verify citations.
- [x] Integrate a pre-query **Compliance Router** that screens incoming requests for subjective recommendations or speculative advice, returning a SEBI advisory block without invoking LLM tokens.
- [x] Set up a "closed-book" grounded prompt commanding **Groq Llama 3 (`llama3-70b-8192`)** to only answer based on the retrieved context chunks.
- [x] Design a flexible regular expression parser that extracts inline markdown citations (with optional backticks and ignoring `Source:` prefixes) and strips them from the response text for a cleaner presentation.
- [x] Create an offline local synthesis engine that dynamically extracts facts/rates from retrieved tables when the **Groq API** is inaccessible.

---

### Phase 6: Conversational Web Interface & Dynamic Visualizations
Assemble the presentation tier featuring responsive chat flows, star sentiment widgets, and dynamic comparison line plots.
- [x] Establish a translucent glassmorphic interface with outfit-jakarta typography and custom scrolls.
- [x] Render message bubbles supporting HTML markdown tables and star-rating badges.
- [x] Design a custom **ApexCharts** Multi-Fund Comparison Widget:
  - Supports side-by-side comparative plots for up to 3 selected funds.
  - Features tabbed toggle controls to view **3Y, 5Y, 7Y, and 10Y** return curves.
  - Employs interactive shared guide-lines to view simultaneous tooltip metrics on cursor hover.
  - Implements **Inactive-State Alerts** that hide series lines and display clean warnings if a fund (e.g., Zerodha Multi Asset Passive FoF) was not yet active during the selected horizon.
- [x] Allow the project to track the transactions with the user's permission from their original broking app.
- [x] Implement a real-time sidebar search bar (placed below the logo and above the schemes list) to dynamically filter mutual funds by name and transaction history by name or date.

---

## 3. Integrated Verification Plan

### Standalone Validation Runs
- Run the indexing suite to verify that metadata files and Chroma stores populate cleanly:
  ```powershell
  python backend/indexer.py
  ```
- Run the Q&A generation suite to verify that the compliance router blocks buying queries and extracts citations perfectly:
  ```powershell
  python backend/generator.py
  ```

### Local Application Execution
- Start the FastAPI web service:
  ```powershell
  python backend/main.py
  ```
- Open a web browser to **`http://127.0.0.1:8000/`** to interact with the single page conversational wealth dashboard.

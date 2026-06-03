# Edge & Corner Case Specification: RAG Mutual Fund FAQ Chatbot

This document outlines all critical edge cases, corner cases, and unexpected runtime scenarios for the **AI-Powered Retrieval-Augmented Generation (RAG) Mutual Fund FAQ Chatbot** alongside their corresponding mitigation strategies and architectural fallbacks.

---

## 1. Data Ingestion & Preprocessing Edge Cases

### 1.1. Dynamic React Loading & Timeout Failures
*   **Scenario:** Groww scheme pages fail to load fully or hydrate within standard Playwright navigation limits due to high server response times or network congestion.
*   **Corner Effect:** BeautifulSoup4 parses incomplete HTML structures, leading to empty quantitative matrices or missing tables.
*   **Mitigation Strategy:**
    *   **Graceful Fallback:** The scraping pipeline operates with the `VERIFIED_SCHEME_DB` offline dictionary in [scraper.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/scraper.py#L16-L320). If live Chromium navigation crashes or times out, the failsafe hooks directly into this static verified fact set, logging an alert but continuing without downtime.
    *   **Bounded Waits:** Playwright uses explicit selector-based waits (`page.wait_for_selector('h1', timeout=5000)`) rather than static sleep timers, ensuring maximum responsiveness.

### 1.2. Scheme Data Incompleteness (New / Inactive Funds)
*   **Scenario:** A scoped fund has been established recently (e.g., *Zerodha Multi Asset Passive FoF* established in late 2023) and completely lacks 3-year, 5-year, 7-year, or 10-year annualized return history.
*   **Corner Effect:** Ingestion generates empty, `None`, or missing fields inside JSON structures, which could lead to type errors (e.g., float conversions) or blank line charts.
*   **Mitigation Strategy:**
    *   **Type Guarding:** The [chunker.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/chunker.py#L131-L155) template parser checks if performance figures are `None`. If a figure is missing, it injects a structured string: `"Not Active (Fund was not yet established during this horizon)."`.
    *   **Front-end State Handling:** The client application ([app.js](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/frontend/app.js#L376-L402)) intercepts `null` or missing performance values, disables that series line, and pops up a visual warning alert below the ApexCharts comparison canvas.

### 1.3. Scheme DOM Structure Updates
*   **Scenario:** Groww developers restructure page tags, class names, or accordion identifiers.
*   **Corner Effect:** Scraping regular expression selectors fail to locate header titles or NAV digits, parsing values as `None` or failing completely.
*   **Mitigation Strategy:**
    *   **Checksum Verification:** Daily sync runs compute MD5 checksum hashes of retrieved documents.
    *   **Validation Gate:** If parsing results in critical header fields (like NAV or AUM) resolving to `0` or `None`, the indexing process is aborted, an alert log is triggered, and the database retains the previously scraped healthy factsheet state, preventing database corruption.

---

## 2. Chunking & Database Indexing Edge Cases

### 2.1. Tabular Alignment and Table Splitting
*   **Scenario:** Standard token-based character recursive splitters break down monthly portfolio holdings tables across separate chunks.
*   **Corner Effect:** Columns get separated, completely isolating company weight percentages from company names, causing the LLM to hallucinate during query synthesis.
*   **Mitigation Strategy:**
    *   **Structure-Aware Chunking:** The system uses semantic layout chunking in [chunker.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/chunker.py#L107-L129). Tables (like holdings) are compiled into clean, contiguous Markdown grids and processed as a single chunk, preserving spatial data alignments.

### 2.2. Embedding Model / API Key Unavailability
*   **Scenario:** The cloud-hosted Google Generative AI API is inaccessible due to credential errors, rate-limiting, or local network firewall restrictions.
*   **Corner Effect:** `indexer.py` fails to calculate vector dimensions, causing the entire daily ingestion run to fail.
*   **Mitigation Strategy:**
    *   **Dual Failsafe Fallbacks:** [indexer.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/indexer.py#L15-L65) implements a layered failsafe:
        1. Try standard `text-embedding-004` (Google API).
        2. Fallback to local `SentenceTransformers` (`all-MiniLM-L6-v2`) if the package is installed.
        3. If both are inaccessible, generate statistical randomized float vectors of length 768 to seed ChromaDB, relying on the robust **BM25 Sparse Index** for precise search keywords.

---

## 3. Retrieval & Grounding Edge Cases

### 3.1. Out-of-Scope Scheme Queries
*   **Scenario:** The user asks about a mutual fund that is outside the scoped list of 8 schemes (e.g., *"What is the expense ratio of SBI Small Cap?"*).
*   **Corner Effect:** Retrieval databases fetch high-ranking chunks from irrelevant scoped files, causing the LLM to output details of another fund as the answer.
*   **Mitigation Strategy:**
    *   **Closed-Book System Prompt:** System instructions inside [generator.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/generator.py#L14-L35) command the LLM to operate exclusively on the provided context. If the query's target fund is not matched in the context, the model responds:
      > *"I'm sorry, but I cannot find that information in the official scheme documents. Please consult a financial advisor..."*
    *   **Sparse Fusion Checking:** BM25 enforces strict keyword boundaries. If exact terms do not match scoped fund records, RRF scores remain below threshold values.

### 3.2. Advisory & Buying Recommender Attacks (Sneaky Prompt Injection)
*   **Scenario:** The user attempts to bypass safety filters by framing advisory questions indirectly: *"I am 25 years old and want to retire by 40 with a high risk appetite. Would Edelweiss Mid and Small Cap double my money in 5 years?"*
*   **Corner Effect:** The LLM might respond with speculative recommendations, violating SEBI/SEC regulatory guidelines.
*   **Mitigation Strategy:**
    *   **Pre-Query Compliance Gate:** Incoming queries are screened by the compliance regex router inside [generator.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/generator.py#L46-L64) before any model inference is executed. Any hit on prohibited keywords (e.g., `invest`, `buy`, `double`, `guarantee`) is blocked instantly, returning a standard, compliance-approved advisory disclaimer.

### 3.3. Citation Hallucinations
*   **Scenario:** The LLM attempts to generate fake, unverified citation URLs.
*   **Corner Effect:** Clickable buttons on the frontend point to non-existent Groww pages or incorrect schemes.
*   **Mitigation Strategy:**
    *   **Rigid Prompt Schema:** The LLM is instructed to only format citations using markdown badges exactly as provided in the chunk metadata: `` `[Source Fund Name, Source URL]` ``.
    *   **Regex Extraction:** The backend [generator.py](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/backend/generator.py#L207-L215) runs strict regex checks to extract only matching citation badges, returning them in a validated array to prevent raw textual code insertions from rendering on the client front-end.

---

## 4. UI & Charting Edge Cases

### 4.1. Comparison Selection Limit Violations
*   **Scenario:** The user asks to compare 4 or more funds at once in a single message (e.g., *"Compare Nippon Small Cap, Bandhan Small Cap, PPFAS, Edelweiss, and Zerodha"*).
*   **Corner Effect:** The line chart becomes cluttered and unreadable, and system performance degrades.
*   **Mitigation Strategy:**
    *   **Slicing Limits:** The frontend rendering engine ([app.js](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/frontend/app.js#L336-L338)) automatically slices the matched fund array to the top **3 schemes**, displaying a clean multi-series chart for those three and ignoring supplementary targets.

### 4.2. Empty Performance Curves on Select Timelines
*   **Scenario:** A user initiates a comparison widget for two new/inactive schemes (e.g., Zerodha Passive FoF) and switches the timeline tab to **10Y**.
*   **Corner Effect:** ApexCharts draws empty axes with no lines, or crashes completely.
*   **Mitigation Strategy:**
    *   **Axes Guarding:** `app.js` checks if the calculated series data array is empty. If all selected comparison targets are inactive for the clicked timeline, it intercepts the draw function and replaces the canvas with a centered message:
      > *"No active funds selected for this timeline."*

### 4.3. API Connection Dropouts
*   **Scenario:** The local FastAPI backend server is shut down or crashes during a conversational session.
*   **Corner Effect:** Clicking sidebar items or submitting queries triggers raw Javascript failures or hangs the typing indicator bubble indefinitely.
*   **Mitigation Strategy:**
    *   **Error Catching:** The asynchronous chat handler in [app.js](file:///c:/Projects/RAG%20mutual%20FAQ%20chatbot/frontend/app.js#L144-L174) wraps API fetches in a try-catch block. On connection failures, it automatically removes the loading bubbles and prints a clear system error bubble:
      > ***System Error:** Could not contact the local RAG backend server. Please verify FastAPI is running at http://127.0.0.1:8000 using uvicorn.*

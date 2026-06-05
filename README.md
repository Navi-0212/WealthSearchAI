# WealthSearchAI - RAG Mutual Fund Chatbot

A compliance-first, AI-powered Retrieval-Augmented Generation (RAG) chatbot for mutual fund queries. This application provides accurate, grounded answers about mutual funds by leveraging real-time data from Groww, with strict adherence to SEBI compliance guidelines.

## 🚀 Features

- **Hybrid Search System**: Combines dense vector search (semantic understanding) with sparse BM25 search (keyword matching) for precise information retrieval
- **Grounded Responses**: All answers are strictly based on retrieved context with verifiable source citations
- **Compliance Guardrails**: Built-in safety filters to prevent investment advice or speculative predictions
- **Real-Time Data**: Automated daily scraping of 8 target mutual fund schemes from Groww
- **Interactive Visualizations**: Multi-fund comparison charts with interactive timeline selection (3, 5, 7, 10 years)
- **Modern UI**: Premium glassmorphic design built with Streamlit, featuring dark theme and smooth animations
- **Multi-Model Support**: Fallback mechanisms for embeddings (Google Gemini → SentenceTransformers) and LLM (Groq → Local synthesis)
- **Scheduled Ingestion**: Automated daily data updates using APScheduler

## 📊 Scoped Data Sources

The chatbot's knowledge base is restricted to data from these 8 Groww mutual fund schemes:

1. **Bandhan Small Cap Fund (Direct Growth)** - https://groww.in/mutual-funds/bandhan-small-cap-fund-direct-growth
2. **Bandhan Midcap Fund (Direct Growth)** - https://groww.in/mutual-funds/bandhan-midcap-fund-direct-growth
3. **Bandhan Multi Cap Fund (Direct Growth)** - https://groww.in/mutual-funds/bandhan-multi-cap-fund-direct-growth
4. **Edelweiss Mid and Small Cap Fund (Direct Growth)** - https://groww.in/mutual-funds/edelweiss-mid-and-small-cap-fund-direct-growth
5. **Zerodha Multi Asset Passive FoF (Direct Growth)** - https://groww.in/mutual-funds/zerodha-multi-asset-passive-fof-direct-growth
6. **Parag Parikh Long Term Value Fund (Direct Growth)** - https://groww.in/mutual-funds/parag-parikh-long-term-value-fund-direct-growth
7. **Nippon India Small Cap Fund (Direct Growth)** - https://groww.in/mutual-funds/nippon-india-small-cap-fund-direct-growth
8. **Nippon India Multi Asset Allocation Fund (Direct Growth)** - https://groww.in/mutual-funds/nippon-india-multi-asset-allocation-fund-direct-growth

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**
- **FastAPI** - REST API framework
- **ChromaDB** - Vector database for semantic search
- **rank-bm25** - Sparse search implementation
- **sentence-transformers** - Local embedding model fallback
- **Google Generative AI** - Primary embedding service
- **Groq** - LLM for response generation
- **Playwright** - Web scraping with headless browser
- **BeautifulSoup4** - HTML parsing
- **APScheduler** - Task scheduling for daily ingestion
- **Pydantic** - Data validation

### Frontend
- **Streamlit** - Primary web interface
- **Plotly** - Interactive data visualization
- **HTML/CSS/JavaScript** - Alternative frontend (legacy)

### Deployment
- **Streamlit Cloud** - Primary deployment platform
- **Heroku** - Alternative deployment (via Procfile)
- **Uvicorn** - ASGI server

## 📁 Project Structure

```
RAG mutual FAQ chatbot/
├── backend/
│   ├── chunker.py          # Semantic chunking of scraped data
│   ├── generator.py        # RAG response generation with LLM
│   ├── indexer.py          # Vector embedding and indexing pipeline
│   ├── main.py             # FastAPI application entry point
│   ├── retriever.py        # Hybrid retrieval (dense + sparse)
│   ├── scheduler.py        # Automated daily ingestion scheduler
│   └── scraper.py          # Web scraping from Groww with verified data
├── data/
│   ├── bm25_store.pkl      # Serialized BM25 sparse index
│   └── scraped_schemes.json # Raw scraped mutual fund data
├── db/
│   └── chroma_store/       # ChromaDB persistent vector storage
├── frontend/
│   ├── app.js              # Frontend JavaScript logic
│   ├── index.html          # Frontend HTML structure
│   └── style.css           # Frontend styling
├── streamlit_app.py        # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── Procfile               # Heroku deployment configuration
└── README.md             # This file
```

## 🔧 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/Navi-0212/WealthSearchAI.git
   cd RAG\ mutual\ FAQ\ chatbot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key
   GROQ_API_KEY=your_groq_api_key
   GROQ_LLM_MODEL=llama3-70b-8192
   ```

   **Note**: The application has fallback mechanisms and will work without API keys using local models.

5. **Initialize the database**
   ```bash
   # Run the indexing pipeline to create the vector database
   python -c "from backend.indexer import run_indexing_pipeline; run_indexing_pipeline('data/scraped_schemes.json')"
   ```

## 🚀 Usage

### Running the Streamlit Application

1. **Start the Streamlit app**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

### Running the FastAPI Backend (Optional)

1. **Start the FastAPI server**
   ```bash
   uvicorn backend.main:app --reload
   ```

2. **Access the API**
   - API documentation: `http://localhost:8000/docs`
   - API endpoint: `http://localhost:8000`

### Running the Scheduled Ingestion

1. **Run immediate ingestion**
   ```bash
   python backend/scheduler.py --immediate
   ```

2. **Run as a scheduled service**
   ```bash
   python backend/scheduler.py
   ```
   This will run daily at 9:15 AM IST.

## 📝 API Endpoints

### FastAPI Endpoints (backend/main.py)

- `POST /query` - Submit a query to the RAG system
  - Request body: `{"query": "your question here"}`
  - Response: `{"answer": "grounded response", "sources": [...]}`

- `GET /health` - Health check endpoint
  - Response: `{"status": "healthy"}`

## 🔐 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Generative AI API key for embeddings | No | Uses local fallback |
| `GROQ_API_KEY` | Groq API key for LLM inference | No | Uses local synthesis |
| `GROQ_LLM_MODEL` | Groq model name | No | `llama3-70b-8192` |

## 🎯 Key Modules

### 1. Data Ingestion (backend/scraper.py)
- Scrapes mutual fund data from Groww using Playwright
- Extracts quantitative metrics (NAV, AUM, expense ratio, returns)
- Extracts qualitative details (fund managers, ratings, holdings)
- Includes verified high-fidelity data fallback for reliability

### 2. Semantic Chunking (backend/chunker.py)
- Breaks scraped data into semantically coherent chunks
- Preserves tabular structures and biographical information
- Enriches chunks with metadata (source URL, fund name, timestamps)
- Generates checksums for data integrity verification

### 3. Vector Indexing (backend/indexer.py)
- Generates dense vector embeddings using Google Gemini or SentenceTransformers
- Builds sparse BM25 index for keyword matching
- Stores vectors in ChromaDB for efficient retrieval
- Supports multiple embedding dimensions

### 4. Hybrid Retrieval (backend/retriever.py)
- Combines dense semantic search with sparse BM25 search
- Implements re-ranking using CrossEncoder
- Filters results by fund metadata
- Aggregates top-ranked chunks for context

### 5. Response Generation (backend/generator.py)
- Enforces strict grounding rules (no hallucinations)
- Provides compliance guardrails for financial queries
- Generates citations for all information
- Suggests relevant follow-up questions
- Falls back to local synthesis if API unavailable

### 6. Scheduled Ingestion (backend/scheduler.py)
- Automates daily data scraping at 9:15 AM IST
- Triggers chunking and indexing pipelines
- Supports immediate execution for testing
- Logs all operations for monitoring

## 🎨 UI Features

### Streamlit Interface
- **Sidebar Navigation**: Searchable list of 8 scoped mutual funds
- **Chat Interface**: Conversational AI with message history
- **Fund Summary View**: Detailed fund information with metrics
- **Interactive Charts**: NAV history comparison with timeline selection
- **Citation Badges**: Clickable links to source documents
- **Dark Theme**: Premium glassmorphic design with gradient backgrounds

### Visualization Features
- Multi-fund NAV comparison charts
- Historical returns visualization (3, 5, 7, 10 years)
- Hover tooltips for exact values
- Responsive design for all screen sizes

## 🚢 Deployment

### Streamlit Cloud Deployment

1. Push code to GitHub repository
2. Connect repository to Streamlit Cloud
3. Set environment variables in Streamlit Cloud dashboard
4. Deploy

### Heroku Deployment

1. Create a Heroku app
2. Set buildpacks for Python
3. Configure environment variables
4. Deploy using the Procfile

## 🧪 Testing

### Manual Testing
1. Test basic queries about fund metrics
2. Test fund manager information retrieval
3. Test multi-fund comparison queries
4. Verify citation links work correctly
5. Check compliance guardrails (try asking for investment advice)

### Automated Testing
```bash
# Run immediate ingestion to test data pipeline
python backend/scheduler.py --immediate

# Test Streamlit app locally
streamlit run streamlit_app.py
```

## 📊 Data Flow

```
User Query → Compliance Check → Hybrid Retrieval (ChromaDB + BM25)
    ↓
Context Aggregation → LLM Generation (Groq/Local) → Citation Mapping
    ↓
Response with Sources → Display in Streamlit UI
```

## 🔒 Compliance & Safety

- **No Investment Advice**: System rejects queries asking for recommendations
- **Grounded Responses**: All answers based strictly on retrieved context
- **Source Citations**: Every fact includes source URL and fund name
- **No Predictions**: Blocks speculative performance predictions
- **SEBI Guidelines**: Designed to comply with Indian financial regulations

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Groww** - For providing mutual fund data
- **Google Generative AI** - For embedding services
- **Groq** - For fast LLM inference
- **ChromaDB** - For vector database functionality
- **Streamlit** - For the web framework

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

## 🔄 Version History

- **v2.4.0** - Current stable version with enhanced UI and improved retrieval
- **v2.0.0** - Added hybrid search and re-ranking
- **v1.0.0** - Initial release with basic RAG functionality

---

**Built with ❤️ for compliant financial AI assistance**

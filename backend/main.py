import os
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure sibling path imports are active
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.generator import RAGResponseGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Mutual Fund FAQ Chatbot API",
    description="Compliance-first virtual wealth assistant API grounding answers in scoped Groww mutual fund details.",
    version="1.0.0"
)

# Enable CORS for local front-end debugging
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize generator instance
generator = RAGResponseGenerator()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    query: str
    answer: str
    citations: list
    is_advisory_rejection: bool
    comparison_funds: list
    suggested_followups: list = []

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    RAG Chat endpoint matching user natural queries to verified knowledge databases
    and returning grounded compliance responses.
    """
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
        
    try:
        logger.info(f"API received chat request: '{query}'")
        response_payload = generator.generate_response(query)
        return response_payload
    except Exception as e:
        logger.error(f"Error executing RAG chat generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# In-memory broker connection state
connected_broker = None

MOCK_TRANSACTIONS = {
    "Groww": [
        {"type": "Buy", "fund_name": "Nippon India Small Cap Fund", "amount": 5000.0, "date": "24 May 2026", "status": "SUCCESS"},
        {"type": "Sell", "fund_name": "Bandhan Midcap Fund", "amount": -12450.0, "date": "10 May 2026", "status": "SETTLED"},
        {"type": "SIP", "fund_name": "Parag Parikh Long Term Value Fund", "amount": 2000.0, "date": "05 May 2026", "status": "PROCESSED"},
        {"type": "Buy", "fund_name": "Edelweiss Mid and Small Cap Fund", "amount": 10000.0, "date": "28 Apr 2026", "status": "SUCCESS"},
        {"type": "SIP", "fund_name": "Zerodha Multi Asset Passive FoF", "amount": 1500.0, "date": "15 Apr 2026", "status": "PROCESSED"},
        {"type": "Sell", "fund_name": "Nippon India Multi Asset Allocation Fund", "amount": -4200.0, "date": "10 Apr 2026", "status": "SETTLED"}
    ],
    "Zerodha": [
        {"type": "Buy", "fund_name": "Bandhan Small Cap Fund", "amount": 3000.0, "date": "20 May 2026", "status": "SUCCESS"},
        {"type": "SIP", "fund_name": "Nippon India Small Cap Fund", "amount": 5000.0, "date": "18 May 2026", "status": "PROCESSED"},
        {"type": "Sell", "fund_name": "Parag Parikh Long Term Value Fund", "amount": -8500.0, "date": "14 May 2026", "status": "SETTLED"},
        {"type": "Buy", "fund_name": "Zerodha Multi Asset Passive FoF", "amount": 2500.0, "date": "02 May 2026", "status": "SUCCESS"}
    ],
    "Upstox": [
        {"type": "Buy", "fund_name": "Nippon India Multi Asset Allocation Fund", "amount": 6000.0, "date": "25 May 2026", "status": "SUCCESS"},
        {"type": "SIP", "fund_name": "Bandhan Multi Cap Fund", "amount": 3000.0, "date": "15 May 2026", "status": "PROCESSED"},
        {"type": "Sell", "fund_name": "Edelweiss Mid and Small Cap Fund", "amount": -5000.0, "date": "08 May 2026", "status": "SETTLED"}
    ]
}

class ConnectRequest(BaseModel):
    broker: str

@app.get("/api/transactions")
async def get_transactions():
    global connected_broker
    if connected_broker is None:
        return {"connected": False, "broker": None, "transactions": []}
    return {
        "connected": True,
        "broker": connected_broker,
        "transactions": MOCK_TRANSACTIONS.get(connected_broker, [])
    }

@app.post("/api/transactions/connect")
async def connect_broker_api(request: ConnectRequest):
    global connected_broker
    broker = request.broker.strip()
    if broker not in MOCK_TRANSACTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported broker: {broker}")
    connected_broker = broker
    logger.info(f"Broker connected: {broker}")
    return {
        "connected": True,
        "broker": connected_broker,
        "transactions": MOCK_TRANSACTIONS.get(connected_broker, [])
    }

@app.post("/api/transactions/disconnect")
async def disconnect_broker_api():
    global connected_broker
    logger.info(f"Broker disconnected: {connected_broker}")
    connected_broker = None
    return {"connected": False, "broker": None, "transactions": []}

# Mount premium frontend assets
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    logger.info(f"Mounted static frontend directories from {frontend_dir}")
else:
    logger.warning(f"Static frontend assets directory not found at {frontend_dir}. API running in headless backend mode.")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting standalone FastAPI development server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

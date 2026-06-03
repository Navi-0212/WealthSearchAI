import os
import re
import sys
import json
import logging

# Add parent path to import sibling files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.retriever import HybridRetriever

logger = logging.getLogger(__name__)

# Helper to dynamically load environment variables from the root .env file
def load_env_file():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(backend_dir)
    env_path = os.path.join(project_root, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        val = val.strip().strip('"').strip("'")
                        os.environ[key.strip()] = val
            logger.info("Successfully loaded local environment variables from .env file.")
        except Exception as e:
            logger.error(f"Error parsing local .env file: {e}")

load_env_file()

# Strict System Prompt Enforcement (Closed-Book RAG Guardrails)
SYSTEM_PROMPT = """
You are a highly professional, compliance-first Virtual Assistant for Mutual Fund Investors and Advisors.
Your sole purpose is to answer questions accurately and objectively based ONLY on the provided verified context.

STRICT OPERATIONAL RULES:
1. Grounding: Rely strictly on the information provided in the Context section below. Do not extrapolate, infer, or bring in any outside knowledge.
2. Unanswerable Queries: If the provided Context does not contain sufficient details to confidently answer the user's question (e.g., if a specific rate or figure is asked but not present), state:
   "I'm sorry, but I cannot find that information in the official scheme documents. Please consult a financial advisor or the mutual fund's helpdesk."
   Do NOT try to guess, invent, or generalize.
3. Citations: Every statement or figure you state must be followed by an exact inline citation pointing to the source document and Groww URL.
   Format citations using markdown badges, e.g., `[Source Fund Name, Source URL]`.
4. Compliance: Do NOT provide subjective investment recommendations, speculative performance projections, or comparisons unless explicitly backed by the retrieved factsheet context.
5. Tone and Style: Maintain a crisp, direct, empathetic, and professional financial tone.
   - Answer the question directly without verbose introductory sentences or filler.
   - If the context contains a generic definition of a term (such as explaining what an exit load is) rather than the specific rate/charges for the fund, do not output the verbose definition. Instead, state directly and professionally that the specific rate is not available in the provided factsheet, and offer a very brief, empathetic definition if helpful.
6. Suggested Follow-up Questions: At the very end of your response, after any citations, you MUST suggest exactly 3 closely related, factual follow-up questions that the user might want to ask next based on the provided context. Format them strictly as:
   <<Suggested Question 1>>
   <<Suggested Question 2>>
   <<Suggested Question 3>>
   Do NOT use markdown list markers or numbering for these suggestions. Write them inside double angle brackets on separate lines.

CONTEXT DETAILS:
{retrieved_context}

USER QUERY:
{user_query}

ANSWER:
"""

class RAGResponseGenerator:
    def __init__(self):
        self.retriever = HybridRetriever()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv("GROQ_LLM_MODEL", "llama3-70b-8192")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not found. Initializing high-fidelity local synthesis engine.")

    def is_query_compliant(self, query: str) -> tuple[bool, str]:
        """
        Compliance Router: Screens incoming queries for general financial advice or performance predictions
        in violation of SEBI/SEC guidelines, rejecting them before LLM inference.
        """
        q_lower = query.lower()
        
        # Prohibited generic advisory keywords
        prohibited_rules = [
            (r"\b(should i invest|is it good to buy|best fund to invest|will it double|guarantee|prediction|predict)\b", 
             "I'm sorry, but as a compliance-first assistant, I am not permitted to provide investment advice, speculative performance projections, or subjective buying/selling recommendations. I can, however, provide objective facts, expense ratios, holdings, exit loads, manager histories, and ratings for our scoped schemes.")
        ]
        
        for pattern, rejection_msg in prohibited_rules:
            if re.search(pattern, q_lower):
                logger.warning(f"Compliance violation blocked query: '{query}'")
                return False, rejection_msg
                
        return True, ""

    def generate_local_synthesis(self, query: str, context_chunks: list) -> str:
        """
        Failsafe Local Synthesis Engine: High-fidelity mock LLM that parses the retrieved context
        dynamically and outputs a compliant, structured response when Gemini API is unavailable.
        """
        logger.info("Executing local synthesis engine fallback...")
        if not context_chunks:
            return "I'm sorry, but I cannot find that information in the official scheme documents. Please consult a financial advisor or the mutual fund's helpdesk."
            
        q_lower = query.lower()
        
        # 1. Ask about fund managers
        if "manager" in q_lower or "who manages" in q_lower or "background" in q_lower or "experience" in q_lower:
            manager_chunks = [c for c in context_chunks if c["metadata"]["metric_category"] in ["Fund Manager", "Work History"]]
            if manager_chunks:
                ans = ""
                for c in manager_chunks[:2]:
                    # Clean tags
                    text_clean = c['text'].replace('### [Fund Manager Bio]', '').replace('### [Fund Manager Work History]', '').strip()
                    ans += f"- {text_clean}\n"
                first = manager_chunks[0]
                ans += f"\n`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
                return ans.strip()
                
        # 2. Ask about exit load
        if "exit load" in q_lower or "redeem" in q_lower or "penalty" in q_lower or "charges" in q_lower:
            load_chunks = [c for c in context_chunks if c["metadata"]["metric_category"] == "NAV"]
            if load_chunks:
                first = load_chunks[0]
                text = first["text"]
                # Try to extract the exit load conditions from the table
                match = re.search(r'\|\s*\*\*Exit Load Conditions\*\*\s*\|\s*([^|]+)\|', text)
                if match:
                    exit_load_val = match.group(1).strip()
                    ans = (
                        f"The exit load for **{first['metadata']['fund_name']}** is: {exit_load_val}\n\n"
                        f"`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
                    )
                    return ans
                else:
                    ans = (
                        f"The exit load details for **{first['metadata']['fund_name']}** are as follows:\n\n"
                        f"{text}\n\n"
                        f"`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
                    )
                    return ans
 
        # 3. Ask about holdings
        if "holdings" in q_lower or "stocks" in q_lower or "portfolio" in q_lower or "owns" in q_lower:
            holdings_chunks = [c for c in context_chunks if c["metadata"]["metric_category"] == "Holdings"]
            if holdings_chunks:
                first = holdings_chunks[0]
                return f"Latest holdings for **{first['metadata']['fund_name']}**:\n\n{first['text']}\n\n`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
 
        # 4. Ask about rating
        if "rating" in q_lower or "stars" in q_lower or "score" in q_lower or "reviews" in q_lower:
            rating_chunks = [c for c in context_chunks if c["metadata"]["metric_category"] == "Public Rating"]
            if rating_chunks:
                first = rating_chunks[0]
                rating_detail = first['text'].replace('Public Sentiment and Groww Rating metrics for ', '').replace('This fund has earned an official Groww User Rating of ', '').strip()
                ans = f"Official rating details: {rating_detail}\n\n`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
                return ans
 
        # 5. Ask about performance timeline or return
        if "performance" in q_lower or "return" in q_lower or "growth" in q_lower or "year" in q_lower or "comparison" in q_lower or "compare" in q_lower:
            perf_chunks = [c for c in context_chunks if c["metadata"]["metric_category"] == "Performance Timeline"]
            if perf_chunks:
                ans = "Annualized historical returns:\n\n"
                for idx, c in enumerate(perf_chunks[:3]):
                    clean_perf = c['text'].replace('### [Performance Timeline]', '').replace('Annualized Historical Percentage Return Metrics for ', '').strip()
                    ans += f"**{c['metadata']['fund_name']}**:\n{clean_perf}\n\n"
                first = perf_chunks[0]
                ans += f"`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
                return ans.strip()
 
        # 6. Standard context synthesis fallback
        first = context_chunks[0]
        ans = f"{first['text']}\n\n`[{first['metadata']['fund_name']}, {first['metadata']['source_url']}]`"
        return ans

    def generate_response(self, user_query: str) -> dict:
        """
        Orchestrates RAG lifecycle: checks compliance, retrieves relevant context,
        prompts Groq Llama 3 model, parses citations, and returns structured API payload.
        """
        logger.info(f"Received query payload: '{user_query}'")
        
        # 1. Screen compliance
        is_compliant, rejection_msg = self.is_query_compliant(user_query)
        if not is_compliant:
            return {
                "query": user_query,
                "answer": rejection_msg,
                "context_used": [],
                "citations": [],
                "is_advisory_rejection": True,
                "comparison_funds": [],
                "suggested_followups": []
            }
            
        # 2. Retrieve Top-K context chunks
        context_chunks = self.retriever.retrieve_context(user_query, top_k=5)
        
        # Detect if query triggers comparison charting (looks for multiple scoped fund names)
        comparison_funds = []
        q_lower = user_query.lower()
        target_funds = [
            ("bandhan-small-cap", "Bandhan Small Cap"),
            ("bandhan-midcap", "Bandhan Midcap"),
            ("bandhan-multi-cap", "Bandhan Multi Cap"),
            ("edelweiss", "Edelweiss Mid and Small Cap"),
            ("zerodha", "Zerodha Multi Asset Passive FoF"),
            ("parag-parikh", "Parag Parikh Long Term Value"),
            ("nippon-india-small-cap", "Nippon India Small Cap"),
            ("nippon-india-multi-asset", "Nippon India Multi Asset Allocation")
        ]
        
        for key, display in target_funds:
            if key.replace('-', ' ') in q_lower or key in q_lower or display.lower() in q_lower:
                comparison_funds.append(display)
                
        # If user explicitly asks for "compare" or inputs 2+ funds, we treat it as a comparison charting intent
        is_comparison_query = "compare" in q_lower or len(comparison_funds) >= 2
        
        # 3. Generate response using Groq Llama 3 (or local synthesis fallback)
        answer = ""
        if self.api_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.api_key)
                
                # Assemble system prompt
                context_str = "\n\n".join([f"--- Context Chunk {idx+1} (Source: {c['metadata']['fund_name']}) ---\n{c['text']}" for idx, c in enumerate(context_chunks)])
                formatted_prompt = SYSTEM_PROMPT.format(retrieved_context=context_str, user_query=user_query)
                
                logger.info(f"Invoking Groq API model ({self.model_name})...")
                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": formatted_prompt,
                        }
                    ],
                    model=self.model_name,
                    temperature=0.0, # Fully deterministic for grounding
                )
                answer = chat_completion.choices[0].message.content
                logger.info("Groq response generated successfully.")
            except Exception as e:
                logger.error(f"Groq LLM generation failed: {e}. Activating local synthesis engine.")
                answer = self.generate_local_synthesis(user_query, context_chunks)
        else:
            answer = self.generate_local_synthesis(user_query, context_chunks)

        # 4. Extract suggested follow-up questions from <<...>> tags
        suggested_followups = re.findall(r'<<([^>]+)>>', answer)
        # Strip follow-up tags from the final printed answer
        answer = re.sub(r'<<[^>]+>>\s*', '', answer).strip()

        # If LLM didn't generate enough, or we need fallback follow-ups
        if not suggested_followups:
            suggested_followups = self.get_default_followups(user_query, context_chunks)
        else:
            # Clean up the followups (limit to 3)
            suggested_followups = [f.strip() for f in suggested_followups[:3]]

        # 5. Extract citations and package metadata
        citations = []
        # Find citation tags formatted as `[Fund Name, URL]`, `[Source: Fund Name, URL]`, or without backticks
        citation_matches = re.findall(r'`?\[(?:Source:?\s*)?([^,\]]+),\s*(https?://[^\s\]`]+)\]`?', answer)
        for fund_name, url in citation_matches:
            citations.append({
                "fund_name": fund_name.strip(),
                "url": url.strip()
            })
        
        # Clean up citation markup from the answer text to prevent redundant text display
        answer = re.sub(r'\s*`?\[(?:Source:?\s*)?[^,\]]+,\s*https?://[^\s\]`]+\]`?', '', answer).strip()
        # Clean up any resulting double periods
        answer = re.sub(r'\.\.+', '.', answer)
            
        logger.info(f"Packaged response successfully with {len(citations)} citations.")
        return {
            "query": user_query,
            "answer": answer,
            "context_used": context_chunks,
            "citations": citations,
            "is_advisory_rejection": False,
            "comparison_funds": comparison_funds if is_comparison_query else [],
            "suggested_followups": suggested_followups
        }

    def get_default_followups(self, query: str, context_chunks: list) -> list:
        q_lower = query.lower()
        
        # 1. Resolve fund name from context or query
        fund_name = None
        if context_chunks:
            fund_names = [c["metadata"]["fund_name"] for c in context_chunks if "metadata" in c and "fund_name" in c["metadata"]]
            if fund_names:
                fund_name = max(set(fund_names), key=fund_names.count)
                
        if not fund_name:
            matched_funds = self.retriever.get_metadata_funds(query)
            if matched_funds:
                fund_name = matched_funds[0]
                
        # Clean up fund name for natural display in follow-ups
        display_fund = fund_name
        if display_fund:
            display_fund = display_fund.replace(" Direct Growth", "").replace(" Direct Plan Growth", "").strip()
        else:
            display_fund = "Bandhan Small Cap Fund" # default safe fallback
            
        # 2. Resolve manager name from query or context
        manager_name = None
        known_managers = [
            "Saurabh Sharma", "Sachin Relekar", "Daylynn Pinto", 
            "Trideep Bhattacharya", "Kedarnath Mirajkar", "Rajeev Thakkar", 
            "Samir Rachh", "Ashwin Sheth"
        ]
        # Check query first
        for mgr in known_managers:
            if mgr.lower() in q_lower:
                manager_name = mgr
                break
                
        # Check context chunks text if query doesn't match
        if not manager_name and context_chunks:
            for c in context_chunks:
                for mgr in known_managers:
                    if mgr.lower() in c["text"].lower():
                        manager_name = mgr
                        break
                if manager_name:
                    break
                    
        if not manager_name:
            manager_name = "the fund manager"
            
        # Determine based on context or query keywords
        if "manager" in q_lower or "who manages" in q_lower or "background" in q_lower or "experience" in q_lower or "work" in q_lower:
            return [
                f"What other schemes are managed by {manager_name}?",
                f"What is the educational background of {manager_name}?",
                f"Can you show the chronological career history of {manager_name}?"
            ]
        elif "exit load" in q_lower or "redeem" in q_lower or "penalty" in q_lower or "fee" in q_lower or "charges" in q_lower:
            return [
                f"What is the expense ratio of {display_fund}?",
                f"What is the current NAV of {display_fund}?",
                f"Does {display_fund} have any exit load penalty after 1 year?"
            ]
        elif "holdings" in q_lower or "stocks" in q_lower or "portfolio" in q_lower or "owns" in q_lower:
            compare_target = "Nippon India Small Cap Fund" if "nippon" not in display_fund.lower() else "Bandhan Small Cap Fund"
            return [
                f"What are the top sector allocations of {display_fund}?",
                f"What is the expense ratio and asset size of {display_fund}?",
                f"Compare the holdings of {display_fund} with {compare_target}."
            ]
        elif "rating" in q_lower or "stars" in q_lower or "sentiment" in q_lower or "reviews" in q_lower:
            compare_target = "Bandhan Small Cap Fund" if "bandhan" not in display_fund.lower() else "Nippon India Small Cap Fund"
            return [
                f"How many reviews does {display_fund} have on Groww?",
                f"What is the historical performance return of {display_fund}?",
                f"Compare the star rating of {display_fund} with {compare_target}."
            ]
        elif "performance" in q_lower or "return" in q_lower or "grow" in q_lower or "compare" in q_lower or "annualized" in q_lower:
            return [
                f"Compare the 3-year and 5-year returns of {display_fund}.",
                f"Which of the scoped funds has the highest 10-year return?",
                f"What is the historical return of Parag Parikh Long Term Value Fund?"
            ]
            
        # Standard default follow-up questions
        return [
            f"What is the expense ratio of {display_fund}?",
            f"Who manages the {display_fund} mutual fund scheme?",
            f"What are the exit load charges for {display_fund}?"
        ]

if __name__ == "__main__":
    # Test runner for verification
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    generator = RAGResponseGenerator()
    
    print("\n--- TEST 1: Compliance Rejection Check ---")
    res1 = generator.generate_response("Should I invest in small cap funds today?")
    print(res1["answer"])
    
    print("\n--- TEST 2: Grounded Q&A Ingestion Check ---")
    res2 = generator.generate_response("What is the exit load for Parag Parikh?")
    print(res2["answer"])

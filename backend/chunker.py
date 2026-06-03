import hashlib
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class SemanticChunker:
    def __init__(self):
        pass

    def calculate_checksum(self, text: str) -> str:
        """
        Generates MD5 hash of string to detect updates and verify data integrity.
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def generate_chunks(self, scheme_data: dict) -> list:
        """
        Breaks down single scheme JSON structure into structured semantic chunks with rich metadata.
        """
        fund_name = scheme_data["fund_name"]
        source_url = scheme_data["source_url"]
        scraped_time = scheme_data["last_scraped_timestamp"]
        
        # Safe lowercase slug for chunk_id uniqueness
        fund_slug = re.sub(r'[^a-z0-9]+', '_', fund_name.lower()).strip('_')
        
        chunks = []
        
        # 1. Summary Chunk: NAV, AUM, Expense Ratio, Rating, and Exit Load Markdown Table
        # Convert exit load text into a clean markdown table
        exit_load_table = (
            f"| Metric / Property | Conditions & Details |\n"
            f"| :--- | :--- |\n"
            f"| **Exit Load Conditions** | {scheme_data['exit_load_text']} |"
        )
        
        summary_text = (
            f"Mutual Fund Scheme Overview: {fund_name}\n"
            f"Source URL: {source_url}\n"
            f"Current Net Asset Value (NAV): INR {scheme_data['current_nav']:.2f}\n"
            f"Assets Under Management (AUM): INR {scheme_data['aum_in_crores']:.2f} Crores\n"
            f"Expense Ratio: {scheme_data['expense_ratio_pct']:.2f}%\n"
            f"Official Public Star Rating: {scheme_data['public_rating']['stars']:.1f}/5 stars "
            f"(Total reviews: {scheme_data['public_rating']['total_reviews']} users)\n\n"
            f"Exit Load Details:\n{exit_load_table}"
        )
        
        summary_hash = self.calculate_checksum(summary_text)
        chunks.append({
            "text": summary_text,
            "metadata": {
                "chunk_id": f"chk_{fund_slug}_summary_{summary_hash[:8]}",
                "source_url": source_url,
                "fund_name": fund_name,
                "metric_category": "NAV",
                "section_header": "Overview & Exit Load",
                "last_scraped": scraped_time,
                "hash_checksum": summary_hash
            }
        })
        
        # 2. Fund Manager Biographical Chunks
        for idx, manager in enumerate(scheme_data.get("fund_managers", [])):
            mgr_name = manager["name"]
            mgr_slug = re.sub(r'[^a-z0-9]+', '_', mgr_name.lower()).strip('_')
            
            # Chunk manager bios with prefix contextual header tag
            bio_text = (
                f"### [Fund Manager Bio] {mgr_name} - {fund_name}\n"
                f"Fund Management details for {fund_name}:\n"
                f"The fund is managed by {mgr_name} (Tenure Start: {manager['tenure_start']}).\n"
                f"Educational Background: {manager['education']}"
            )
            bio_hash = self.calculate_checksum(bio_text)
            chunks.append({
                "text": bio_text,
                "metadata": {
                    "chunk_id": f"chk_{fund_slug}_bio_{mgr_slug}_{bio_hash[:8]}",
                    "source_url": source_url,
                    "fund_name": fund_name,
                    "metric_category": "Fund Manager",
                    "section_header": f"Fund Management - {mgr_name}",
                    "last_scraped": scraped_time,
                    "hash_checksum": bio_hash
                }
            })
            
            # Chronological career paths prefixed with contextual header tags
            work_text = (
                f"### [Fund Manager Work History] {mgr_name} - {fund_name}\n"
                f"Chronological Career and Work History of Fund Manager {mgr_name} (managing {fund_name}):\n"
                + "\n".join([f"- {job}" for job in manager.get("work_history", [])])
            )
            work_hash = self.calculate_checksum(work_text)
            chunks.append({
                "text": work_text,
                "metadata": {
                    "chunk_id": f"chk_{fund_slug}_history_{mgr_slug}_{work_hash[:8]}",
                    "source_url": source_url,
                    "fund_name": fund_name,
                    "metric_category": "Work History",
                    "section_header": f"Work History - {mgr_name}",
                    "last_scraped": scraped_time,
                    "hash_checksum": work_hash
                }
            })
            
        # 3. Public Rating & User Reviews
        rating_text = (
            f"Public Sentiment and Groww Rating metrics for {fund_name}:\n"
            f"This fund has earned an official Groww User Rating of {scheme_data['public_rating']['stars']:.1f} out of 5 stars.\n"
            f"The rating is aggregated from a total of {scheme_data['public_rating']['total_reviews']} submitted user reviews."
        )
        rating_hash = self.calculate_checksum(rating_text)
        chunks.append({
            "text": rating_text,
            "metadata": {
                "chunk_id": f"chk_{fund_slug}_rating_{rating_hash[:8]}",
                "source_url": source_url,
                "fund_name": fund_name,
                "metric_category": "Public Rating",
                "section_header": "User Ratings & Sentiment",
                "last_scraped": scraped_time,
                "hash_checksum": rating_hash
            }
        })
        
        # 4. Top Holdings Table Chunk (Rendered in Markdown to preserve grid schema)
        holdings_lines = [
            f"Top Asset Portfolio Holdings for {fund_name}:",
            "",
            "| Company Name | Industry/Sector | Allocation Weight (%) |",
            "| :--- | :--- | :--- |"
        ]
        for stock in scheme_data.get("top_holdings", []):
            holdings_lines.append(f"| {stock['company']} | {stock['sector']} | {stock['allocation_pct']:.2f}% |")
            
        holdings_text = "\n".join(holdings_lines)
        holdings_hash = self.calculate_checksum(holdings_text)
        chunks.append({
            "text": holdings_text,
            "metadata": {
                "chunk_id": f"chk_{fund_slug}_holdings_{holdings_hash[:8]}",
                "source_url": source_url,
                "fund_name": fund_name,
                "metric_category": "Holdings",
                "section_header": "Portfolio Top Holdings",
                "last_scraped": scraped_time,
                "hash_checksum": holdings_hash
            }
        })
        
        # 5. Performance Timeline Chunks (3Y, 5Y, 7Y, 10Y)
        # Package return timelines into descriptive sentence-structured matrices
        perf = scheme_data.get("performance_timelines", {})
        returns_lines = [
            f"### [Performance Timeline] {fund_name}",
            f"Annualized Historical Percentage Return Metrics for {fund_name}:"
        ]
        
        periods = [("3_year_return_pct", "3 Years"), ("5_year_return_pct", "5 Years"), 
                   ("7_year_return_pct", "7 Years"), ("10_year_return_pct", "10 Years")]
                   
        for key, label in periods:
            val = perf.get(key)
            if val is not None:
                returns_lines.append(f"- Annualized Return over {label}: {val:.2f}%")
            else:
                returns_lines.append(f"- Annualized Return over {label}: Not Active (Fund was not yet established during this horizon).")
                
        returns_text = "\n".join(returns_lines)
        returns_hash = self.calculate_checksum(returns_text)
        chunks.append({
            "text": returns_text,
            "metadata": {
                "chunk_id": f"chk_{fund_slug}_performance_{returns_hash[:8]}",
                "source_url": source_url,
                "fund_name": fund_name,
                "metric_category": "Performance Timeline",
                "section_header": "Historical Performance Timeline",
                "last_scraped": scraped_time,
                "hash_checksum": returns_hash
            }
        })
        
        return chunks

    def process_all_scraped_data(self, scraped_json_path: str) -> list:
        """
        Reads scraped JSON file and yields a flattened list of all semantic chunks.
        """
        logger.info(f"Chunker parsing scraped file: {scraped_json_path}")
        with open(scraped_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        all_chunks = []
        for scheme in data:
            scheme_chunks = self.generate_chunks(scheme)
            all_chunks.extend(scheme_chunks)
            
        logger.info(f"Chunker generated {len(all_chunks)} semantic chunks in total.")
        return all_chunks

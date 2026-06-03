import os
import sys
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# Ensure the parent directory is on the path so we can import scraper.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.scraper import GrowwScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_daily_ingestion_task():
    """
    Executes the full ingestion pipeline: crawls the 8 schemes, splits into semantic chunks,
    generates dense/sparse vectors, and indexes them into the vector database.
    """
    logger.info("Scheduler triggered daily ingestion task at 09:15 AM IST.")
    start_time = datetime.utcnow()
    
    try:
        # Initialize scraper
        scraper = GrowwScraper(use_headless_browser=True)
        results = scraper.scrape_all_scoped_schemes()
        logger.info(f"Ingestion component scraped {len(results)} schemes.")
        
        # Save scraped data to temp storage for downstream chunker/indexer to ingest
        os.makedirs('data', exist_ok=True)
        out_path = 'data/scraped_schemes.json'
        with open(out_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Ingestion results written to {out_path}.")
        
        # Execute chunker and indexing triggers
        try:
            from backend.indexer import run_indexing_pipeline
            run_indexing_pipeline(out_path)
            logger.info("Indexing pipeline successfully executed post-ingestion.")
        except ImportError:
            logger.warning("Downstream Indexer/Chunker modules not implemented yet. Skipping index run.")
            
        end_time = datetime.utcnow()
        elapsed = (end_time - start_time).total_seconds()
        logger.info(f"Ingestion task completed successfully in {elapsed:.2f} seconds.")
        
    except Exception as e:
        logger.error(f"Failed to execute automated ingestion scheduler run: {e}")

def main():
    scheduler = BlockingScheduler()
    
    # Configure Cron Trigger for 09:15 AM IST (timezone 'Asia/Kolkata')
    # everyday at hour 9, minute 15
    trigger = CronTrigger(hour=9, minute=15, timezone='Asia/Kolkata')
    
    scheduler.add_job(
        run_daily_ingestion_task,
        trigger=trigger,
        id='groww_daily_ingestion',
        name='Daily scraping of 8 target Groww schemes at 09:15 AM IST',
        replace_existing=True
    )
    
    logger.info("Ingestion scheduler successfully initialized.")
    logger.info("Automated job registered: Daily at 09:15 AM IST (Asia/Kolkata timezone).")
    
    # Allow passing an '--immediate' flag to trigger scraping right now for verification
    if len(sys.argv) > 1 and sys.argv[1] == '--immediate':
        logger.info("Immediate execution flag detected. Running scraper run now...")
        run_daily_ingestion_task()
        logger.info("Immediate execution run completed.")
        return

    try:
        logger.info("Starting scheduler loop. Waiting for scheduled runs...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shut down cleanly.")

if __name__ == "__main__":
    main()

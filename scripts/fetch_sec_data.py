"""
SEC Data Fetcher for GitHub Actions backend.
Fetches filings, extracts risks, and gets financial data, then saves to JSON.
"""
import os
import sys
import json
import time

# Add root directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sec_client

from sec_client import SECClient
import forensic_modules
from llm_client import InvestigativeEditor

# Configuration
TICKERS = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"]
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HF_TOKEN = os.environ.get("HF_TOKEN")

def save_json(path, data):
    """Save data to JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {path}")

def main():
    # Initialize client without proxies (direct connection)
    sec = SECClient(use_proxies=False)
    
    # Initialize LLM Editor if token available
    editor = InvestigativeEditor(HF_TOKEN) if HF_TOKEN else None
    if not editor:
        print("Warning: HF_TOKEN not found. Skipping LLM intelligence.")

    for ticker in TICKERS:
        print(f"\nProcessing {ticker}...")
        try:
            # 1. Resolve CIK
            cik = sec.get_cik(ticker)
            if not cik:
                print(f"Could not resolve CIK for {ticker}")
                continue
            
            # 2. Get Filings (10-K/Q)
            filings = sec.get_filings(cik, "10-Q", count=2)
            if not filings:
                filings = sec.get_filings(cik, "10-K", count=2)
            
            if not filings:
                print(f"No filings found for {ticker}")
                continue
                
            save_json(os.path.join(DATA_DIR, ticker, "filings.json"), filings)
            
            # 3. Extract Risks (Item 1A)
            risks_data = {}
            current_risks_text = ""
            previous_risks_text = ""
            
            for i, filing in enumerate(filings[:2]):
                print(f"Downloading {filing['primary_doc']}...")
                html = sec.download_filing(filing['url'])
                if html:
                    text = sec_client.extract_item_1a(html)
                    risks_data[filing['accession']] = text
                    print(f"Extracted {len(text)} chars from {filing['date']}")
                    
                    if i == 0: current_risks_text = text
                    if i == 1: previous_risks_text = text
                else:
                    print(f"Failed to download {filing['url']}")
            
            save_json(os.path.join(DATA_DIR, ticker, "risks.json"), risks_data)
            
            # Analyze Risks
            risk_analysis = {}
            if current_risks_text and previous_risks_text:
                risk_analysis = forensic_modules.analyze_textual_changes(current_risks_text, previous_risks_text)
            
            # 4. Get Financials (XBRL)
            print("Fetching XBRL data...")
            financials = {}
            facts = sec.get_company_facts(cik)
            if facts:
                financials = forensic_modules.analyze_financials(facts, cik)
                save_json(os.path.join(DATA_DIR, ticker, "financials.json"), financials)
                print("Saved financials")
            else:
                print("Failed to fetch XBRL data")
            
            # 5. Get Whale Data (13-F) - Simplified 
            # (Fetching 13-F would require a separate lookup, skipping for now to keep script simple)
            whale_analysis = {}

            # 6. Generate Intelligence (LLM)
            if editor:
                print("Generating Scoop Leads...")
                scoop = editor.generate_scoop_leads(
                    risk_analysis,
                    whale_analysis,
                    financials
                )
                
                intelligence = {
                    "generated_at": time.time(),
                    "scoop_leads": scoop,
                    "model": editor.MODEL
                }
                save_json(os.path.join(DATA_DIR, ticker, "intelligence.json"), intelligence)
                print("Saved intelligence report")
                
            # Be nice to SEC rates
            time.sleep(0.2)
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()

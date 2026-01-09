"""
LLM Client - HuggingFace Integration
"""
import requests
import json
from urllib.parse import quote

class InvestigativeEditor:
    """LLM-powered investigative analysis."""
    
    MODEL = "meta-llama/Llama-3.1-70B-Instruct"
    API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"
    
    def __init__(self, token: str):
        self.token = token
    
    def generate_scoop_leads(self, risk_analysis: dict, whale_analysis: dict = None, financials: dict = None) -> str:
        """Generate 3 investigative scoop leads."""
        
        # Build context
        context_parts = []
        
        if risk_analysis:
            context_parts.append("## RISK FACTOR CHANGES")
            if risk_analysis.get("escalations"):
                context_parts.append("NEW RISK ESCALATIONS:")
                for e in risk_analysis["escalations"][:5]:
                    context_parts.append(f"- {e['keyword'].upper()}: {e['text'][:150]}...")
            if risk_analysis.get("silent_deletions"):
                context_parts.append("\nSILENT DELETIONS:")
                for d in risk_analysis["silent_deletions"][:5]:
                    context_parts.append(f"- {d['keyword'].upper()}: {d['text'][:150]}...")
        
        if financials and financials.get("alerts"):
            context_parts.append("\n## FINANCIAL ALERTS")
            for alert in financials["alerts"]:
                context_parts.append(f"🚨 {alert['type']}: {alert['message']}")
        
        if whale_analysis and not whale_analysis.get("error"):
            context_parts.append(f"\n## 13-F WHALE ACTIVITY")
            context_parts.append(f"Net Conviction: {whale_analysis.get('conviction_signal', 'N/A')}")
        
        data_context = "\n".join(context_parts) if context_parts else "No significant findings."
        
        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are an Investigative Editor at a financial news desk. Find newsworthy stories from SEC filings.
Be specific and highlight red flags.<|eot_id|><|start_header_id|>user<|end_header_id|>

Review the data below. Flag if whales are selling while management adds "Going Concern" risk language.

Provide exactly 3 'Scoop Leads' with:
1. A catchy headline
2. 2-3 sentence explanation
3. Significance for investors

DATA:
{data_context}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 500,
                "temperature": 0.3,
                "return_full_text": False
            }
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            print("[LLM] Calling Hugging Face API...")
            resp = requests.post(self.API_URL, headers=headers, json=payload, timeout=120)
            
            if resp.status_code == 200:
                result = resp.json()
                if isinstance(result, list) and result:
                    return result[0].get("generated_text", str(result))
                return str(result)
            else:
                return f"LLM Error {resp.status_code}: {resp.text[:300]}"
        except Exception as e:
            # CORS blocked - provide helpful message
            return f"""⚠️ **LLM Access Blocked by CORS**

The Hugging Face API cannot be accessed directly from the browser due to CORS restrictions.

**Why this happens:**
Browsers block direct API calls to different domains (like Hugging Face) for security.

**Fix (Static Strategy):**
Run the **"Fetch SEC Data"** workflow in GitHub Actions.
This generates the insights server-side (where CORS doesn't exist) and saves them to `intelligence.json`.
The app will then load that file instead of trying to call the API here.
"""

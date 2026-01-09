"""
LLM Client - HuggingFace Integration
"""
import requests
import json
from urllib.parse import quote

class InvestigativeEditor:
    """LLM-powered investigative analysis."""
    
    MODEL = "google/gemini-2.0-flash-exp:free" # Switching to Gemini 2.0 Flash (Free)
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, token: str):
        self.token = token
    
    def generate_scoop_leads(self, risk_analysis: dict, whale_analysis: dict = None, financials: dict = None) -> str:
        """Generate 3 investigative scoop leads using OpenRouter."""
        
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
        
        system_prompt = """You are an Investigative Editor at a financial news desk. Find newsworthy stories from SEC filings.
Be specific and highlight red flags.

Review the data below. Flag if whales are selling while management adds "Going Concern" risk language.

Provide exactly 3 'Scoop Leads' with:
1. A catchy headline
2. 2-3 sentence explanation
3. Significance for investors"""

        # OpenRouter / OpenAI Format
        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"DATA:\n{data_context}"}
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/iamjohnwatson/Forensic-Filing-Assistant",
                "X-Title": "Forensic Newsroom Auditor"
            }
            
            print(f"[LLM] Calling OpenRouter ({self.MODEL})...")
            resp = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
            
            if resp.status_code == 200:
                result = resp.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                return str(result)
            else:
                return f"OpenRouter Error {resp.status_code}: {resp.text[:300]}"
                
        except Exception as e:
            return f"""⚠️ **LLM Error**
            
{str(e)}

**Troubleshooting:**
1. Check your OpenRouter API Key
2. Ensure you have credits (if not using free model)
"""

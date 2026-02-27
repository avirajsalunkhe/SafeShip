
# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v5.6.0

import requests
import json
import sys

class SafeShipEngine:
    def __init__(self, gemini_key, groq_key=None):
        self.gemini_key = gemini_key
        self.groq_key = groq_key
        self.model = "gemini-2.5-flash-preview-09-2025"

    def audit_source(self, code_content):
        prompt = f"""
        Act as a senior security researcher. Conduct a deep SAST audit of the following code.
        CHECK FOR: Secrets, XSS, CSRF, IDOR, Memory Leaks, Insecure Crypto.
        Return JSON structure: {{ "score": 0-100, "findings": [{{ "title": "", "severity": "", "fix": "", "description": "" }}] }}
        CODE: {code_content}
        """
        return self._call_neural_api(prompt)

    def audit_url(self, target_url):
        prompt = f"""
        Act as a web security auditor. Verify and analyze infrastructure for: {target_url}.
        Return JSON structure: {{ "score": 0-100, "findings": [{{ "title": "", "severity": "", "fix": "", "description": "" }}] }}
        """
        return self._call_neural_api(prompt)

    def _call_neural_api(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": { "responseMimeType": "application/json" }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text)
        except Exception as e:
            return {"error": str(e), "score": 0, "findings": []}

if __name__ == "__main__":
    # Example usage
    KEY = "YOUR_GEMINI_KEY"
    engine = SafeShipEngine(KEY)
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"[*] SafeShip Neural Trace started for: {target}")
        result = engine.audit_url(target) if target.startswith('http') else engine.audit_source(target)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python audit_engine.py <url_or_code>")

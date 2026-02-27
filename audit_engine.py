# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v6.0.0 (High Precision)

import requests
import json
import sys
import os

class SafeShipEngine:
    def __init__(self):
        # Env variable priority
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.model = "gemini-2.5-flash-preview-09-2025"

        if not self.gemini_key:
            print("[!] CRITICAL: GEMINI_API_KEY not found in environment.")
            sys.exit(1)

    def audit_source(self, code_content):
        prompt = f"Conduct a deep SAST audit on the following code. Detect Secrets, Injection, and Logical flaws.\nCODE:\n{code_content}"
        return self._call_neural_api(prompt)

    def audit_url(self, target_url):
        prompt = f"Conduct a web infrastructure and security header audit for: {target_url}."
        return self._call_neural_api(prompt)

    def _call_neural_api(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        
        # Structured Output Schema (Mandatory for precision)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "object",
                    "properties": {
                        "score": {"type": "number"},
                        "summary": {"type": "string"},
                        "findings": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "description": {"type": "string"},
                                    "location": {"type": "string"},
                                    "fix": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            res_json = response.json()
            
            if 'candidates' in res_json:
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
            return {"error": "No response from Neural Node."}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    engine = SafeShipEngine()
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"[*] SafeShip Neural Trace v6.0 [CLI] started for: {target}")
        if target.startswith('http'):
            result = engine.audit_url(target)
        elif os.path.isfile(target):
            with open(target, 'r', encoding='utf-8') as f:
                result = engine.audit_source(f.read())
        else:
            result = engine.audit_source(target)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python audit_engine.py <url_or_filepath>")

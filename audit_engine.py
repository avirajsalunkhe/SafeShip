# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v6.0.0 (Secure Edition)

import requests
import json
import sys
import os

class SafeShipEngine:
    def __init__(self, gemini_key=None, groq_key=None):
        # Prioritize passed arguments, fallback to Environment Variables
        self.gemini_key = gemini_key or os.getenv('GEMINI_API_KEY')
        self.groq_key = groq_key or os.getenv('GROQ_API_KEY')
        self.model = "gemini-2.5-flash-preview-09-2025"

        if not self.gemini_key:
            print("[!] Error: GEMINI_API_KEY not found in environment.")
            print("[*] Fix: Run 'export GEMINI_API_KEY=your_key_here' or use a .env file.")
            sys.exit(1)

    def audit_source(self, code_content):
        prompt = f"""
        Act as a senior security researcher. Conduct a deep SAST audit.
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
            "generationConfig": { 
                "responseMimeType": "application/json"
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            
            if 'candidates' in res_json:
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
            else:
                return {"error": "No candidates returned from API", "score": 0, "findings": []}
        except Exception as e:
            return {"error": str(e), "score": 0, "findings": []}

if __name__ == "__main__":
    # The engine now automatically looks for GEMINI_API_KEY in your system environment
    engine = SafeShipEngine()
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"[*] SafeShip Neural Trace started for: {target}")
        
        # Check if target is a file or a URL
        if target.startswith('http'):
            result = engine.audit_url(target)
        elif os.path.isfile(target):
            with open(target, 'r') as f:
                result = engine.audit_source(f.read())
        else:
            result = engine.audit_source(target)
            
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python audit_engine.py <url_or_filepath_or_code>")

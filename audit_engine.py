# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v6.2.4

import requests
import json
import sys
import os

class SafeShipEngine:
    def __init__(self):
        # Neural Handshake: Load from env
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.model = "gemini-2.5-flash-preview-09-2025"

        if not self.gemini_key:
            print("[!] CRITICAL: GEMINI_API_KEY environment variable is missing.")
            sys.exit(1)
        else:
            print(f"[*] Neural Handshake Verified. Model: {self.model}")

    def audit_source(self, code_content):
        prompt = (
            "Perform a high-precision security audit (SAST) on the following code. "
            "Detect hardcoded secrets, XSS, and SQL injection.\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            "  \"score\": number (0-100),\n"
            "  \"summary\": \"string\",\n"
            "  \"findings\": [{\"title\": \"string\", \"severity\": \"string\", \"description\": \"string\", \"location\": \"string\", \"fix\": \"string\"}]\n"
            "}\n"
            f"CODE TO AUDIT:\n{code_content}"
        )
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
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                return {"error": f"API Error {response.status_code}", "raw": response.text}

            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            return json.loads(raw_text)

        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    engine = SafeShipEngine()
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"[*] Initiating Trace for: {target}")
        
        if os.path.isfile(target):
            with open(target, 'r') as f:
                content = f.read()
            result = engine.audit_source(content)
        else:
            result = engine.audit_source(target)
            
        print("\n=== NEURAL TELEMETRY REPORT ===")
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python audit_engine.py <filepath_or_code_string>")

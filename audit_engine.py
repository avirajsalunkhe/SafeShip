# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v6.2.0 (Deep Telemetry)

import requests
import json
import sys
import os

class SafeShipEngine:
    def __init__(self):
        # Environment configuration
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.model = "gemini-2.5-flash-preview-09-2025"

        if not self.gemini_key:
            print("[!] CRITICAL TELEMETRY: GEMINI_API_KEY not found in environment.")
            print("[*] FIX: Run 'export GEMINI_API_KEY=your_key' or add it to system variables.")
            sys.exit(1)

    def audit_source(self, code_content):
        prompt = f"Conduct a high-precision SAST audit on the following code snippet. Focus on IDOR, XSS, and hardcoded secrets.\nCODE:\n{code_content}"
        return self._call_neural_api(prompt)

    def audit_url(self, target_url):
        prompt = f"Analyze web infrastructure and DNS security posture for: {target_url}."
        return self._call_neural_api(prompt)

    def _call_neural_api(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        
        # Enforce Strict Schema for precision
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
                    },
                    "required": ["score", "summary", "findings"]
                }
            }
        }
        
        try:
            print("[*] Handshaking with Neural Node...")
            response = requests.post(url, json=payload, timeout=60)
            
            # Detailed Error Interception
            if response.status_code != 200:
                print(f"[!] HANDSHAKE FAILED: HTTP {response.status_code}")
                try:
                    error_json = response.json()
                    print(f"[DEBUG-LOG]: {json.dumps(error_json, indent=2)}")
                except:
                    print(f"[DEBUG-LOG]: Raw Response: {response.text}")
                response.raise_for_status()

            res_json = response.json()
            if 'candidates' in res_json:
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
            
            return {"error": "Trace Failed: No response candidates."}

        except requests.exceptions.Timeout:
            return {"error": "Connection Timeout: Neural node is too slow."}
        except Exception as e:
            return {"error": f"Internal Engine Error: {str(e)}"}

if __name__ == "__main__":
    engine = SafeShipEngine()
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"[*] SafeShip Neural Trace v6.2 [CLI] started for: {target}")
        
        if target.startswith('http'):
            result = engine.audit_url(target)
        elif os.path.isfile(target):
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    result = engine.audit_source(f.read())
            except Exception as e:
                result = {"error": f"File Read Error: {str(e)}"}
        else:
            result = engine.audit_source(target)
            
        print("\n" + "="*40)
        print("NEURAL AUDIT REPORT")
        print("="*40)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python audit_engine.py <url_or_filepath_or_raw_code>")

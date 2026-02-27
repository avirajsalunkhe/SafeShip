# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v6.2.1 (High Precision Telemetry)

import requests
import json
import sys
import os

class SafeShipEngine:
    def __init__(self):
        # Neural Handshake: Environment variable configuration
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.model = "gemini-2.5-flash-preview-09-2025"

        if not self.gemini_key:
            print("[!] CRITICAL TELEMETRY: GEMINI_API_KEY not found in system environment.")
            print("[*] HANDSHAKE FAILED: Handover to manual configuration required.")
            print("[*] FIX: Run 'export GEMINI_API_KEY=your_key' or add it to your .env file.")
            sys.exit(1)
        else:
            print(f"[*] Handshake Successful: Node linked via environment entropy.")

    def audit_source(self, code_content):
        prompt = f"Conduct a high-precision SAST audit on the following code. Identify hardcoded secrets, IDOR, and XSS.\nCODE:\n{code_content}"
        return self._call_neural_api(prompt)

    def audit_url(self, target_url):
        prompt = f"Analyze web infrastructure, headers, and DNS security posture for: {target_url}."
        return self._call_neural_api(prompt)

    def _call_neural_api(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        
        # Enforce Strict Schema to prevent logical debt in parsing
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
            print("[*] Initiating Trace: Syncing with Neural Node...")
            response = requests.post(url, json=payload, timeout=60)
            
            # Deep Error Interception
            if response.status_code != 200:
                print(f"[!] NEURAL DISRUPTION: Node returned HTTP {response.status_code}")
                try:
                    error_payload = response.json()
                    reason = error_payload.get('error', {}).get('message', 'Unknown Node Failure')
                    print(f"[DEBUG-LOG]: {reason}")
                    
                    if response.status_code == 403:
                        print("[*] ADVISORY: API Key may be invalid or restricted to a different project.")
                    elif response.status_code == 429:
                        print("[*] ADVISORY: Rate limit reached. Cool down node for 60 seconds.")
                except:
                    print(f"[DEBUG-LOG]: Raw Response: {response.text}")
                return {"error": f"Node Failure {response.status_code}", "score": 0, "findings": []}

            res_json = response.json()
            if 'candidates' in res_json:
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(raw_text)
            
            return {"error": "Trace Failed: No logical candidates returned."}

        except requests.exceptions.Timeout:
            return {"error": "Signal Lost: Neural node timed out."}
        except Exception as e:
            return {"error": f"Internal Runtime Exception: {str(e)}"}

if __name__ == "__main__":
    engine = SafeShipEngine()
    
    if len(sys.argv) > 1:
        target = sys.argv[1]
        print(f"[*] SafeShip Neural Trace v6.2.1 [CLI] started for: {target}")
        
        if target.startswith('http'):
            result = engine.audit_url(target)
        elif os.path.isfile(target):
            try:
                with open(target, 'r', encoding='utf-8') as f:
                    result = engine.audit_source(f.read())
            except Exception as e:
                result = {"error": f"IO Error: {str(e)}"}
        else:
            result = engine.audit_source(target)
            
        print("\n" + "="*50)
        print("NEURAL TELEMETRY REPORT")
        print("="*50)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python audit_engine.py <url_or_filepath_or_raw_code>")

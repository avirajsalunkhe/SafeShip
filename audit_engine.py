# File: audit_engine.py
# Description: Python CLI version of SafeShip Trace Engine v6.2.4

import requests
import json
import sys
import os

class SafeShipEngine:
    def __init__(self):
        self.gemini_key   = os.getenv('GEMINI_API_KEY')
        self.groq_key     = os.getenv('GROQ_API_KEY')
        # ✅ FIXED: was "gemini-2.5-flash-preview-09-2025" — caused 404
        self.gemini_model = "gemini-2.0-flash"
        self.groq_model   = "llama-3.3-70b-versatile"

        if not self.gemini_key and not self.groq_key:
            print("[!] CRITICAL: Neither GEMINI_API_KEY nor GROQ_API_KEY is set.")
            sys.exit(1)
        if self.gemini_key:
            print(f"[*] Neural Handshake Verified. Primary: {self.gemini_model}")
        else:
            print(f"[!] Gemini key missing. Fallback: {self.groq_model}")

    def audit_source(self, code_content):
        prompt = (
            "Perform a high-precision security audit (SAST) on the following code. "
            "Detect hardcoded secrets, XSS, and SQL injection.\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            "  \"score\": number (0-100),\n"
            "  \"summary\": \"string\",\n"
            "  \"findings\": [{\"title\": \"string\", \"severity\": \"string\", "
            "\"description\": \"string\", \"location\": \"string\", \"fix\": \"string\"}]\n"
            "}\n"
            f"CODE TO AUDIT:\n{code_content}"
        )
        if self.gemini_key:
            print("[*] Attempting Gemini node...")
            result = self._call_gemini(prompt)
            if "error" not in result:
                return result
            print(f"[!] Gemini failed: {result.get('error')}. Falling back to Groq...")
        if self.groq_key:
            print("[*] Attempting Groq fallback node...")
            return self._call_groq(prompt)
        return {"error": "All neural nodes exhausted."}

    def _call_gemini(self, prompt):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.gemini_model}:generateContent?key={self.gemini_key}")
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        try:
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code != 200:
                return {"error": f"Gemini API Error {r.status_code}", "raw": r.text}
            return json.loads(r.json()['candidates'][0]['content']['parts'][0]['text'])
        except Exception as e:
            return {"error": str(e)}

    def _call_groq(self, prompt):
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": "You are a security auditor. Respond with valid JSON only. No markdown."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2048
        }
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers=headers, json=payload, timeout=60)
            if r.status_code != 200:
                return {"error": f"Groq API Error {r.status_code}", "raw": r.text}
            raw = r.json()['choices'][0]['message']['content']
            raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            return json.loads(raw)
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

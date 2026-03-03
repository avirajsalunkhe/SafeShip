// SafeShip Trace Engine v6.2.4 - Secure Backend Proxy
// This server proxies API calls and keeps API keys SECRET on the server

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// ──────────────────────────────────────────────────────────────────
// API Key Management (loaded from environment variables)
// ──────────────────────────────────────────────────────────────────
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';

if (!GEMINI_API_KEY && !GROQ_API_KEY) {
  console.warn('[!] WARNING: Neither GEMINI_API_KEY nor GROQ_API_KEY is set. Audit will fail.');
}

console.log('[*] SafeShip Engine initialized');
console.log(`[*] Gemini available: ${!!GEMINI_API_KEY}`);
console.log(`[*] Groq available: ${!!GROQ_API_KEY}`);

// ──────────────────────────────────────────────────────────────────
// Gemini Audit Endpoint
// ──────────────────────────────────────────────────────────────────
app.post('/api/audit/gemini', async (req, res) => {
  try {
    const { code } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'No code provided' });
    }

    if (!GEMINI_API_KEY) {
      return res.status(503).json({ 
        error: 'Gemini API key not configured',
        fallback: 'Try Groq endpoint'
      });
    }

    const prompt = `Perform a high-precision security audit (SAST) on the following code. Detect hardcoded secrets, XSS, SQL injection, and other vulnerabilities.

Respond ONLY with a valid JSON object matching this schema:
{
  "score": number (0-100),
  "summary": "string",
  "findings": [{"title": "string", "severity": "CRITICAL|HIGH|MEDIUM|LOW", "description": "string", "location": "string", "fix": "string"}]
}

CODE TO AUDIT:
${code}`;

    const response = await axios.post(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${GEMINI_API_KEY}`,
      {
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          responseMimeType: 'application/json',
          temperature: 0.3,
          maxOutputTokens: 2048
        }
      },
      { timeout: 30000 }
    );

    if (response.data?.candidates?.[0]?.content?.parts?.[0]?.text) {
      const auditResult = JSON.parse(response.data.candidates[0].content.parts[0].text);
      res.json({ success: true, engine: 'gemini', data: auditResult });
    } else {
      throw new Error('Unexpected Gemini response format');
    }
  } catch (error) {
    console.error('[!] Gemini Error:', error.message);
    res.status(500).json({ 
      error: 'Gemini audit failed',
      message: error.message,
      fallback: 'Try Groq endpoint'
    });
  }
});

// ──────────────────────────────────────────────────────────────────
// Groq Audit Endpoint (Fallback)
// ──────────────────────────────────────────────────────────────────
app.post('/api/audit/groq', async (req, res) => {
  try {
    const { code } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'No code provided' });
    }

    if (!GROQ_API_KEY) {
      return res.status(503).json({ 
        error: 'Groq API key not configured'
      });
    }

    const prompt = `Perform a high-precision security audit (SAST) on the following code. Detect hardcoded secrets, XSS, SQL injection, and other vulnerabilities.

Respond ONLY with a valid JSON object matching this schema:
{
  "score": number (0-100),
  "summary": "string",
  "findings": [{"title": "string", "severity": "CRITICAL|HIGH|MEDIUM|LOW", "description": "string", "location": "string", "fix": "string"}]
}

CODE TO AUDIT:
${code}`;

    const response = await axios.post(
      'https://api.groq.com/openai/v1/chat/completions',
      {
        model: 'mixtral-8x7b-32768',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 2048
      },
      {
        headers: {
          'Authorization': `Bearer ${GROQ_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 30000
      }
    );

    if (response.data?.choices?.[0]?.message?.content) {
      const auditResult = JSON.parse(response.data.choices[0].message.content);
      res.json({ success: true, engine: 'groq', data: auditResult });
    } else {
      throw new Error('Unexpected Groq response format');
    }
  } catch (error) {
    console.error('[!] Groq Error:', error.message);
    res.status(500).json({ 
      error: 'Groq audit failed',
      message: error.message
    });
  }
});

// ──────────────────────────────────────────────────────────────────
// Health Check
// ──────────────────────────────────────────────────────────────────
app.get('/api/health', (req, res) => {
  res.json({
    status: 'online',
    engines: {
      gemini: !!GEMINI_API_KEY,
      groq: !!GROQ_API_KEY
    },
    timestamp: new Date().toISOString()
  });
});

// ──────────────────────────────────────────────────────────────────
// Serve Static Files (Frontend)
// ──────────────────────────────────────────────────────────────────
app.use(express.static(path.join(__dirname, 'public')));
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// ──────────────────────────────────────────────────────────────────
// Error Handler
// ──────────────────────────────────────────────────────────────────
app.use((err, req, res, next) => {
  console.error('[!] Unhandled Error:', err);
  res.status(500).json({ error: 'Internal Server Error' });
});

// ──────────────────────────────────────────────────────────────────
// Start Server
// ──────────────────────────────────────────────────────────────────
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`[*] SafeShip Engine running on port ${PORT}`);
  console.log(`[*] Neural Handshake Complete`);
});

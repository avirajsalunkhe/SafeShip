/**
 * SafeShip Trace Engine — server.js (Cloudflare Worker)
 * 
 * DEPLOY: https://workers.cloudflare.com → Create Worker → paste this
 * SECRETS: Worker Dashboard → Settings → Variables → add:
 *   GEMINI_API_KEY  = your key (get from aistudio.google.com)
 *   GROQ_API_KEY    = your NEW key (old one was exposed — regenerate at console.groq.com)
 */

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
  'Content-Type': 'application/json',
};

const reply = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: CORS });

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null, { headers: CORS });
    if (request.method !== 'POST') return reply({ error: 'Method Not Allowed' }, 405);

    let body;
    try { body = await request.json(); }
    catch { return reply({ error: 'Invalid JSON body' }, 400); }

    const path = new URL(request.url).pathname;

    // ── /gemini ────────────────────────────────────────────────────────
    if (path === '/gemini') {
      if (!env.GEMINI_API_KEY) return reply({ error: 'GEMINI_API_KEY not set in Worker env' }, 500);
      try {
        // ✅ FIXED model name — was "gemini-2.5-flash-preview-09-2025" (caused 404)
        const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${env.GEMINI_API_KEY}`;
        const r = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const d = await r.json();
        if (!r.ok) return reply({ error: `Gemini API ${r.status}`, details: d }, r.status);
        return reply(d);
      } catch (e) {
        return reply({ error: 'Gemini fetch failed', message: e.message }, 502);
      }
    }

    // ── /groq ──────────────────────────────────────────────────────────
    if (path === '/groq') {
      if (!env.GROQ_API_KEY) return reply({ error: 'GROQ_API_KEY not set in Worker env' }, 500);
      try {
        const r = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${env.GROQ_API_KEY}`,
          },
          body: JSON.stringify(body),
        });
        const d = await r.json();
        if (!r.ok) return reply({ error: `Groq API ${r.status}`, details: d }, r.status);
        return reply(d);
      } catch (e) {
        return reply({ error: 'Groq fetch failed', message: e.message }, 502);
      }
    }

    // ── /health ────────────────────────────────────────────────────────
    if (path === '/health') {
      return reply({
        status: 'online',
        gemini: env.GEMINI_API_KEY ? 'configured' : 'MISSING',
        groq:   env.GROQ_API_KEY   ? 'configured' : 'MISSING',
      });
    }

    return reply({ error: 'Unknown route. Use /gemini or /groq' }, 404);
  }
};

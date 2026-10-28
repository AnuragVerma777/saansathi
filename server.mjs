import { createServer } from 'node:http';
import { readFile, access } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));
try {
  const env = await readFile(join(root, '.env'), 'utf8');
  for (const line of env.split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (match && !process.env[match[1]]) process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
  }
} catch { /* .env is optional when variables are supplied by the host */ }

const port = Number(process.env.PORT || 3000);
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.svg': 'image/svg+xml' };
const emergencyPattern = /\b(can't breathe|cannot breathe|struggling to breathe|severe shortness of breath|blue lips|blue face|unconscious|passed out|crushing chest pain|severe chest pain)\b/i;

function reply(res, status, data) {
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' });
  res.end(JSON.stringify(data));
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  if (req.method === 'GET' && url.pathname === '/api/health') {
    return reply(res, 200, { ok: true, provider: 'Nebius Token Factory', model: process.env.NEBIUS_MODEL || 'nvidia/Nemotron-3_5-Lightning', configured: Boolean(process.env.NEBIUS_API_KEY) });
  }
  if (req.method === 'POST' && url.pathname === '/api/guide') {
    let raw = '';
    for await (const chunk of req) {
      raw += chunk;
      if (raw.length > 16_000) return reply(res, 413, { error: 'Please keep your note under 16 KB.' });
    }
    let input;
    try { input = JSON.parse(raw); } catch { return reply(res, 400, { error: 'Request must be valid JSON.' }); }
    const message = typeof input.message === 'string' ? input.message.trim().slice(0, 3000) : '';
    const details = typeof input.details === 'string' ? input.details.trim().slice(0, 3000) : '';
    const language = input.language === 'Bahasa Indonesia' ? 'Bahasa Indonesia' : 'English';
    const text = [details && `Symptom notes: ${details}`, message && `Question: ${message}`].filter(Boolean).join('\n');
    if (!text) return reply(res, 400, { error: 'Add a question or symptom note first.' });
    if (emergencyPattern.test(text)) {
      return reply(res, 200, { answer: 'Your message mentions symptoms that can be an emergency. Please contact your local emergency number or go to the nearest emergency department now. Do not wait for an AI response. If possible, ask someone nearby to stay with you.' , urgent: true });
    }
    if (!process.env.NEBIUS_API_KEY) return reply(res, 503, { error: 'Nebius is not configured yet. Copy .env.example to .env and add your Nebius Token Factory API key.' });
    const endpoint = (process.env.NEBIUS_BASE_URL || 'https://api.tokenfactory.nebius.com/v1').replace(/\/+$/, '') + '/chat/completions';
    const system = `You are Saansathi, a calm respiratory-care navigation assistant for adults. Reply in ${language}. You provide general health education and help people prepare for a conversation with a clinician. You are not a doctor and cannot diagnose, rule out disease, interpret test results, recommend prescriptions, or replace professional care. Never assign a probability or risk score. Encourage users with ongoing, worsening, or concerning symptoms to contact a qualified clinician; do not delay care for this chat. If a user describes severe trouble breathing, blue lips/face, fainting, or severe chest pain, clearly tell them to contact local emergency services now. Ask at most one short follow-up question if important context is missing. Use simple language, be concise, and avoid pretending certainty. End non-emergency answers with one practical next step. Do not request names, addresses, or other identifying details.`;
    try {
      const upstream = await fetch(endpoint, {
        method: 'POST',
        headers: { authorization: `Bearer ${process.env.NEBIUS_API_KEY}`, 'content-type': 'application/json' },
        body: JSON.stringify({ model: process.env.NEBIUS_MODEL || 'nvidia/Nemotron-3_5-Lightning', temperature: 0.25, max_tokens: 420, messages: [{ role: 'system', content: system }, { role: 'user', content: text }] }),
        signal: AbortSignal.timeout(45_000)
      });
      if (!upstream.ok) {
        const detail = await upstream.text();
        console.error(`Nebius returned ${upstream.status}: ${detail.slice(0, 1200)}`);
        return reply(res, 502, { error: upstream.status === 401 || upstream.status === 403 ? 'Nebius did not accept the API key. Check your token and model access.' : `Nebius request failed (${upstream.status}). Check your model ID and try again.` });
      }
      const result = await upstream.json();
      const answer = result.choices?.[0]?.message?.content;
      if (typeof answer !== 'string' || !answer.trim()) return reply(res, 502, { error: 'Nebius returned an empty response. Please try again.' });
      return reply(res, 200, { answer: answer.trim(), model: result.model || process.env.NEBIUS_MODEL || 'Nemotron' });
    } catch (error) {
      console.error('Nebius request error:', error.message);
      return reply(res, 502, { error: error.name === 'TimeoutError' ? 'The model took too long to respond. Please try again.' : 'Could not reach Nebius Token Factory. Check your connection and try again.' });
    }
  }
  if (req.method !== 'GET' && req.method !== 'HEAD') return reply(res, 405, { error: 'Method not allowed.' });
  let pathname = url.pathname === '/' ? '/index.html' : decodeURIComponent(url.pathname);
  pathname = normalize(pathname).replace(/^([.][.][/\\])+/, '');
  const path = join(root, pathname);
  if (!path.startsWith(root)) return reply(res, 403, { error: 'Forbidden.' });
  try {
    await access(path);
    const body = await readFile(path);
    res.writeHead(200, { 'content-type': types[extname(path)] || 'application/octet-stream', 'x-content-type-options': 'nosniff', 'referrer-policy': 'no-referrer' });
    res.end(req.method === 'HEAD' ? undefined : body);
  } catch { reply(res, 404, { error: 'Not found.' }); }
});

server.listen(port, '0.0.0.0', () => console.log(`Saansathi listening on http://localhost:${port}`));

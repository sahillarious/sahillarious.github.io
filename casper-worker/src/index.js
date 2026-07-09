import { KNOWLEDGE } from "./knowledge.js";

// ── Config ────────────────────────────────────────────────────────────────
// OpenAI gpt-4o-mini — fast and cheap, plenty for portfolio Q&A.
const MODEL = "gpt-4o-mini";
const MAX_TOKENS = 1024;
const MAX_HISTORY_TURNS = 12; // cap conversation length to bound token cost
const MAX_MESSAGE_CHARS = 1000; // reject absurdly long user inputs
const OPENAI_URL = "https://api.openai.com/v1/chat/completions";

const SYSTEM_INSTRUCTIONS = `You are Casper, a friendly cat-themed assistant embedded in Sahil Sawant's
portfolio website. Sahil named you after his real cat. Your job is to answer visitors'
questions about Sahil — his experience, projects, skills, education, and how to reach him —
using ONLY the information in the knowledge base below.

Rules:
- Answer in the third person about Sahil ("Sahil built…", "He worked at…").
- Be concise and direct. Skip preambles like "Based on the information provided". Lead with
  the answer. A few sentences is usually plenty; use short bullet lists for multiple items.
- Only use facts from the knowledge base. If something isn't covered, say you don't have that
  detail and point them to Sahil's email or LinkedIn — never invent facts, dates, or numbers.
- If asked something unrelated to Sahil or his work, politely decline and steer back to what
  you can help with.
- Keep a professional, plain tone — recruiters read this. Do NOT use emoji, emoticons, ASCII
  art, or decorative characters of any kind.
- Formatting: you may use **bold** for role titles or key terms, and simple "- " bullet lines
  for lists. Do NOT use markdown headings (#), tables, code fences, blockquotes, or numbered
  lists — keep responses to short paragraphs, **bold**, and "- " bullets.

KNOWLEDGE BASE:
${KNOWLEDGE}`;

// ── CORS ──────────────────────────────────────────────────────────────────
function corsHeaders(env, requestOrigin) {
  const allowed = (env.ALLOWED_ORIGIN || "*").split(",").map((s) => s.trim());
  let origin = "*";
  if (!allowed.includes("*")) {
    origin = allowed.includes(requestOrigin) ? requestOrigin : allowed[0];
  }
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

// ── Worker ────────────────────────────────────────────────────────────────
export default {
  async fetch(request, env) {
    const cors = corsHeaders(env, request.headers.get("Origin") || "");

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }
    if (request.method !== "POST") {
      return json({ error: "Method not allowed" }, 405, cors);
    }
    if (!env.OPENAI_API_KEY) {
      return json({ error: "Server not configured" }, 500, cors);
    }

    // Parse + validate the incoming conversation.
    let payload;
    try {
      payload = await request.json();
    } catch {
      return json({ error: "Invalid JSON" }, 400, cors);
    }

    const incoming = Array.isArray(payload?.messages) ? payload.messages : null;
    if (!incoming || incoming.length === 0) {
      return json({ error: "Missing 'messages'" }, 400, cors);
    }

    // Keep only well-formed user/assistant turns, trim history, enforce length.
    const turns = incoming
      .filter(
        (m) =>
          m &&
          (m.role === "user" || m.role === "assistant") &&
          typeof m.content === "string" &&
          m.content.trim().length > 0
      )
      .slice(-MAX_HISTORY_TURNS)
      .map((m) => ({ role: m.role, content: m.content.slice(0, MAX_MESSAGE_CHARS) }));

    if (turns.length === 0 || turns[turns.length - 1].role !== "user") {
      return json({ error: "Last message must be from the user" }, 400, cors);
    }

    // OpenAI takes the system prompt as the first message in the array.
    const messages = [{ role: "system", content: SYSTEM_INSTRUCTIONS }, ...turns];

    try {
      const res = await fetch(OPENAI_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${env.OPENAI_API_KEY}`,
        },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: MAX_TOKENS,
          messages,
        }),
      });

      if (!res.ok) {
        const detail = await res.text();
        console.error(`Casper worker error: ${res.status} ${detail}`);
        if (res.status === 429) {
          return json({ error: "Busy right now — please try again in a moment." }, 429, cors);
        }
        return json({ error: "Something went wrong. Please try again." }, 502, cors);
      }

      const data = await res.json();
      const reply = data?.choices?.[0]?.message?.content?.trim();

      return json({ reply: reply || "Sorry, I couldn't come up with a response." }, 200, cors);
    } catch (err) {
      console.error("Casper worker error:", err?.message || err);
      return json({ error: "Something went wrong. Please try again." }, 502, cors);
    }
  },
};

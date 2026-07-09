# Casper Worker

Cloudflare Worker backend for **Casper**, the assistant on Sahil Sawant's portfolio.
It holds the OpenAI API key server-side and answers questions using the résumé/project
content in [`src/knowledge.js`](src/knowledge.js) as the system prompt.

Architecture: static site → `fetch(WORKER_URL)` → this Worker → OpenAI API → reply.

## One-time setup

```bash
cd casper-worker
npm install
npx wrangler login          # opens a browser to connect your Cloudflare account
```

## Add your OpenAI API key (as a secret — never commit it)

```bash
npx wrangler secret put OPENAI_API_KEY
# paste your key from https://platform.openai.com/api-keys when prompted
```

## Run locally

```bash
npm run dev        # serves at http://localhost:8787
```

For local dev the secret can instead live in a `.dev.vars` file (git-ignored):

```
OPENAI_API_KEY=sk-...
```

Test it:

```bash
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What did Sahil build at Arta?"}]}'
```

## Deploy

```bash
npm run deploy
```

Wrangler prints the live URL, e.g. `https://casper-worker.<your-subdomain>.workers.dev`.

## Wire up the frontend

In [`../script.js`](../script.js), set the Casper `WORKER_URL` constant to that URL.

## Lock down CORS (after you know your site's URL)

Edit `[vars] ALLOWED_ORIGIN` in [`wrangler.toml`](wrangler.toml) from `"*"` to your real
origin(s), comma-separated, e.g.:

```toml
[vars]
ALLOWED_ORIGIN = "https://sahilsawant.dev,http://localhost:8000"
```

Then redeploy.

## Notes & knobs

- **Model** — defaults to `gpt-4o-mini` in [`src/index.js`](src/index.js). Change the
  `MODEL` constant to use a different OpenAI model.
- **Cost** — `gpt-4o-mini` is very cheap; each answer is a fraction of a cent at this size.
- **Abuse guards** — history is capped to the last 12 turns and each message to 1000 chars.
  For a public endpoint, also consider adding Cloudflare rate limiting or Turnstile.
- **Updating Sahil's info** — edit `src/knowledge.js` and `npm run deploy`.

## Growing later (your roadmap)

- **Agent behavior**: add OpenAI tool/function definitions to the request in `src/index.js`.
- **Retrieval**: if the knowledge base outgrows the prompt, replace the static `KNOWLEDGE`
  string with a retrieval call before the model request. Contained change, not a rewrite.

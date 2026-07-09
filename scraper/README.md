# Job Apply Automation — Scraper Backend

Stage 1 of the pipeline: **discover → enrich → filter → export** fresh,
US-based, junior/new-grad postings for a few target roles, then write them to
`jobs.json` and `jobs.xlsx`.

## How it works

```
roles × platforms                "AI Engineer" site:greenhouse.io remote   (Google, last week)
        │  search.py  ───────────────────────────────────────────────►  SERP results
        ▼
   parser.py        attribute platform, extract company slug, clean title, drop non-postings
        ▼
   dedup            collapse by canonical URL
        ▼
   enrich.py        greenhouse/lever/ashby public JSON APIs; others via schema.org JobPosting
        ▼
   filters.py       seniority (drop senior/lead/staff/VP…) → US-only location → posted < 3 days
        ▼
   storage.py       jobs.json  +  jobs.xlsx
```

Roles, platforms, and every filter list live in [`config.py`](config.py).
Current defaults: roles = *AI Engineer, Machine Learning Engineer, Forward
Deployed Engineer*; platforms = *greenhouse, ashby, lever, jobs.\* subdomains,
careers sites*.

## Setup

```bash
cd scraper
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env                               # then add SERPER_API_KEY
```

### Search backend

| Provider      | Reliability | Cost                     | Notes                         |
|---------------|-------------|--------------------------|-------------------------------|
| `serper`      | High        | Free tier (~2.5k queries)| Set `SERPER_API_KEY` ([serper.dev](https://serper.dev)) |
| `google_html` | Low         | Free                     | Scrapes google.com; gets CAPTCHA'd fast |

`auto` (default) uses Serper if a key is present, otherwise the HTML scraper.

## Run

```bash
# Full pipeline (from the repo root, so the package resolves)
python -m scraper.main

# Narrow it down
python -m scraper.main --platforms greenhouse lever --roles "AI Engineer"
python -m scraper.main --max-age-days 3 --pages 2 --require-junior

# See what the search returns without enriching or saving
python -m scraper.main --dry-run

# Offline sanity check of parser + filters (no network)
python -m scraper.selftest
```

Output lands in `scraper/output/` by default. The console prints a breakdown of
how many postings were dropped and why (seniority / location / recency).

## Output columns

`company, title, platform, location, date_posted, age_days, employment_type,
url, description, snippet, source_query, scraped_at, metadata, id`

## Notes / next steps

- Filtering keeps an audit trail: postings aren't silently discarded — each
  carries a `drop_reason`, summarized at the end of a run.
- Ambiguous "remote" with no geo qualifier is **kept** (bias toward recall).
  Flip individual lists in `config.py` to tighten precision.
- Next stages (not built yet): dedup against an applied-history store, resume/
  cover-letter generation, and the apply step + a web UI to review the queue.

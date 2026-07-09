# Sahil [TODO: surname] — Portfolio

Personal portfolio site for an AI/ML Engineer. Plain HTML + CSS + vanilla JS. No build step required.

## Deployment (GitHub Pages)

1. Create a GitHub repo named **exactly** `<username>.github.io` (replace `<username>` with your GitHub username).
2. Place `index.html` at the repo root (it's already there).
3. Commit and push all files to the `main` branch.
4. In GitHub: **Settings → Pages → Source → Deploy from branch → main / (root)**.
5. Your site will be live at `https://<username>.github.io` within a minute or two.

## Before you publish — fill in the TODOs

Search for `[TODO:` in `index.html` and `script.js` and replace each placeholder:

| Placeholder | What to put |
|---|---|
| `[TODO: surname]` | Your last name |
| `[TODO: email]` | Your email address (appears in contact links and the mailto form) |
| `[TODO: GitHub URL]` | Full URL to your GitHub profile, e.g. `https://github.com/username` |
| `[TODO: GitHub username]` | Your GitHub username (display text) |
| `[TODO: LinkedIn URL]` | Full URL to your LinkedIn profile |
| `[TODO: dates]` | Employment dates for each role |
| `[TODO: Bachelor's degree]` | Degree name, university, years, location |

Also update `TO_EMAIL` in `script.js` (line near the contact form section) with your real email.

## Assets

Drop files into the `/assets` folder:

- `resume.pdf` — your resume (linked from the nav Resume button and the contact section)
- `headshot.jpg` (optional) — your photo; uncomment the `<img>` tag in `index.html` inside `.about-photo-wrap` and remove the placeholder `<div>`

## Local preview

Open `index.html` directly in any modern browser. No server or build step needed.

For the cleanest preview (avoids some browser CORS quirks with local fonts), you can run a minimal server:

```bash
# Python 3
python -m http.server 8080
# then open http://localhost:8080
```

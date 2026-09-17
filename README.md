# Daily Coloring Book Factory

Every day, this generates a complete coloring book (cover + numbered pages)
with Gemini, pauses for your one-tap approval, then publishes it to Gumroad.
Runs entirely on GitHub Actions - $0, no card, works from your phone.

## How it works

1. **`generate` job** (fully automatic): picks a fresh theme, writes page
   concepts, generates every illustration, assembles the PDF, writes the
   listing copy.
2. It pauses. You get a notification to review.
3. **`upload` job** (only runs after you tap Approve): publishes the PDF to
   Gumroad as a priced product.

## One-time setup (all from your phone browser)

### 1. Create the repo
Go to github.com → tap **+** → **New repository** → name it (e.g.
`coloring-book-factory`) → Create. Then use **Add file → Upload files** to
upload everything in this folder, keeping the same file structure
(the `.github/workflows/` and `scripts/` folders need to stay intact).

### 2. Add your Gemini API key as a secret
You already have one from your AI Quantum project - reuse it, no need to
make a new one.

Repo → **Settings** → **Secrets and variables** → **Actions** →
**New repository secret**
- Name: `GEMINI_API_KEY`
- Value: your key

### 3. Create a Gumroad account + access token
- Sign up free at gumroad.com (no card needed).
- Go to **Settings → Advanced → Applications** → create an application →
  this gives you a way to generate an **access token**.
- Add it as a repo secret:
  - Name: `GUMROAD_ACCESS_TOKEN`
  - Value: your token

### 4. Turn on the review gate
Repo → **Settings** → **Environments** → **New environment** → name it
exactly `production` → turn on **Required reviewers** → add yourself.

This is what makes the upload step wait for your tap instead of publishing
automatically.

### 5. Test it
Repo → **Actions** tab → **Daily Coloring Book** → **Run workflow**.
Once the `generate` job finishes, you'll get a notification to review the
`upload` job. Open the run, download the `coloring-book` artifact to look
at the actual PDF on your phone, then tap **Review deployments → Approve
and deploy** if it looks good.

After that, it runs automatically every day at the time set in
`.github/workflows/daily-coloring-book.yml` (`cron: "0 13 * * *"` = 1pm
UTC - change the number to shift the time).

## Things you'll likely want to tune

All in `scripts/config.py`:
- `NUM_INTERIOR_PAGES` - how many pages per book (starts at 24)
- `PRICE_USD` - fixed at $4.99 to start; change anytime
- `AUDIENCE_HINT` - who it's aimed at

## If something breaks on a future run

Two moving parts here are the most likely to shift under you over time,
since both are on the newer/less-stable side:

- **The Gemini text model name** (`scripts/config.py` → `TEXT_MODEL`).
  Google retires model names periodically - if a run fails with a 404
  mentioning the model, the error message itself usually tells you the
  current replacement. Swap the one line in `config.py` and you're done.
- **Gumroad's product-creation API** — new, and I couldn't fully verify
  every field name against their live docs while building this. If
  `upload_gumroad.py` errors out, the Action log prints Gumroad's exact
  response - copy that back to me and it's a one-function fix.

Image generation runs on Pollinations.ai (`scripts/pollinations_client.py`),
which needs no API key at all - Gemini's image models turned out not to
have a real free tier, so there's nothing to configure or renew there.

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

## If the Gumroad step fails on first run

Gumroad's product-creation API is new, and I couldn't fully verify every
field name against their live docs while building this. If `upload.py`
errors out, the Action log will print Gumroad's exact response - copy that
error back to me and it's a quick fix in `scripts/upload_gumroad.py`
(the generation side is unaffected either way - you'd just upload that
day's PDF manually as a one-off while it's fixed).

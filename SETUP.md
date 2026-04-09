# BlackBirdDS — Publishing & Auto-Sync Setup

This guide takes you from zero to a live documentation site that **automatically updates whenever you publish styles or components in Figma**.

---

## How it works

```
You publish in Figma
        ↓
Figma sends a webhook → Make.com (free) receives it
        ↓
Make.com calls GitHub API → triggers a GitHub Action
        ↓
Action runs sync_from_figma.py → pulls fresh tokens
        ↓
Commits updated blackbirdds-docs.html → pushes to GitHub
        ↓
Netlify detects the push → deploys in ~30 seconds
        ↓
Your public URL is always up to date ✅
```

---

## Step 1 — Push to GitHub

1. Create a new GitHub repository (can be private).
2. Push this folder to it:

```bash
cd /path/to/BlackBirdDS
git init
git add .
git commit -m "initial: BlackBirdDS documentation"
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

---

## Step 2 — Get a Figma access token

1. Open Figma → click your avatar (top-left) → **Settings**
2. Scroll to **Personal access tokens** → **Generate new token**
3. Give it a name (e.g. `blackbirdds-sync`) and copy the token — you won't see it again.

---

## Step 3 — Add the token to GitHub Secrets

1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
   - Name: `FIGMA_TOKEN`
   - Value: the token from Step 2
3. *(Optional)* Add a variable (not secret) for the file ID if you ever change it:
   - Name: `FIGMA_FILE_ID`
   - Value: `2Ov115BSkN5jNisHpc6ZXq`

---

## Step 4 — Connect Netlify

1. Go to [app.netlify.com](https://app.netlify.com) → **Add new site → Import an existing project**
2. Connect your GitHub account and select the repo
3. Build settings (already in `netlify.toml`, nothing to change):
   - Build command: *(leave empty)*
   - Publish directory: `.`
4. Click **Deploy site** — your docs are now live at a URL like `random-name.netlify.app`
5. *(Optional)* Go to **Site configuration → Domain management** to set a custom domain

Every time GitHub Actions pushes a commit, Netlify automatically redeploys within ~30 seconds.

---

## Step 5 — Set up Figma Webhooks (auto-trigger on publish)

> **Note:** Figma webhooks require a **Professional or Organization plan**. If you're on the free plan, skip to the [Scheduled fallback](#scheduled-fallback-free-plan) section.

Figma webhooks fire when you **publish styles or components** (File → Publish styles & components).

The webhook needs to call the GitHub API to trigger the Action. The easiest way is through **Make.com** (free tier, no code):

### 5a — Create a Make.com automation

1. Sign up at [make.com](https://make.com) (free)
2. Create a new **Scenario**
3. Add a **Webhooks → Custom webhook** trigger — copy the webhook URL Make gives you
4. Add an **HTTP → Make a request** module with:
   - URL: `https://api.github.com/repos/<owner>/<repo>/dispatches`
   - Method: `POST`
   - Headers:
     - `Authorization`: `Bearer <github_pat>` *(create a GitHub PAT with `repo` scope)*
     - `Accept`: `application/vnd.github+json`
   - Body (JSON):
     ```json
     {"event_type": "figma-publish"}
     ```
5. Save and activate the scenario

### 5b — Register the webhook in Figma

Figma doesn't yet have a UI for webhooks — use the API directly:

```bash
curl -X POST https://api.figma.com/v2/webhooks \
  -H "X-Figma-Token: <your-figma-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "LIBRARY_PUBLISH",
    "team_id": "<your-team-id>",
    "endpoint": "<make.com-webhook-url>",
    "passcode": "blackbirdds"
  }'
```

To find your `team_id`: open Figma in the browser — it's the number in the URL when you're on a team page (`figma.com/files/<team_id>/...`).

### Supported event types

| Event | When it fires |
|---|---|
| `LIBRARY_PUBLISH` | Styles or components published |
| `FILE_UPDATE` | Any save to the file (noisy — not recommended) |
| `FILE_VERSION_UPDATE` | A named version is created |

---

## Scheduled fallback (free plan)

If you're on Figma's free plan, the GitHub Action is already configured to run **every day at 02:00 UTC**. No webhook setup needed — your docs stay at most 24 hours behind Figma.

To change the schedule, edit `.github/workflows/figma-sync.yml`:

```yaml
schedule:
  - cron: "0 2 * * *"   # daily at 2am UTC
  # - cron: "0 */6 * * *"  # every 6 hours
  # - cron: "0 * * * *"    # every hour
```

---

## Manual sync

You can trigger a sync at any time from GitHub:

1. Go to your repo → **Actions → Sync from Figma**
2. Click **Run workflow**

Or via the GitHub CLI:

```bash
gh workflow run figma-sync.yml
```

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Action fails with 401 | Check that `FIGMA_TOKEN` secret is set correctly |
| Variables API returns 403 | Your Figma plan doesn't include REST variable access — the script falls back to existing data |
| Netlify not redeploying | Check that Netlify is connected to the correct branch (`main`) |
| Webhook not firing | Verify the Make.com scenario is active and the Figma webhook is registered |

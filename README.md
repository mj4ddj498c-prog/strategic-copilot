# Strategic Copilot

An automated job search pipeline for anyone actively looking for their next role. Every weekday morning it scans your target companies' job boards, scores each posting against your profile using OpenAI, and writes only the relevant roles to a Google Sheet. You open it over breakfast and your shortlist is ready. No coding required to set up or run.

**What it costs to run:** ~$0 infrastructure (GitHub and Google Sheets are free). OpenAI API usage runs roughly $0.50–$2/month at steady state for 20–30 companies. The first week is higher while the system learns which jobs it's already seen — after that, only genuinely new postings that match your title and location filters get scored, which is typically 5–15 jobs per day.

---

## Before you start

You'll need accounts at three services. All are free or have free tiers adequate for this use case.

- **GitHub** — where the code lives and runs on a schedule ([github.com](https://github.com))
- **Google account** — for Google Sheets (your output) and Google Cloud (one-time setup)
- **OpenAI** — the AI that scores the jobs (). You'll need to add a payment method; typical usage is under $1/month.

---

## Setup

**Recommended: let OpenAI walk you through it.**

Open OpenAI (free account works) and paste this:

> I'm setting up an automated job search pipeline using GitHub Actions and Google Sheets. The repo is at https://github.com/jordanmilner-lgtm/strategic-copilot — can you walk me through the full setup step by step, starting with Step 1? I'll also need help finding the ATS job board handles for my list of target companies — I'll give you the company names and you can look them up.

OpenAI will read this README, guide you through each step interactively, and look up the ATS handles for your target companies directly — you just give it a list of company names. This is the fastest path, especially for the Google Cloud steps and company setup.

**Prefer to follow the steps yourself?** Full instructions are below.

---

## Setup — overview

1. Set up your Google Sheet
2. Get a Google Service Account (lets the script write to your sheet)
3. Fork this repo to your GitHub account
4. Add your secrets to GitHub
5. Build your scoring profile
6. Add your target companies and detect their ATS handles
7. Run your first scan

Each step is covered in detail below. The whole process takes about 30–45 minutes the first time.

---

## Step 1: Set up Google Sheets

1. Go to [sheets.google.com](https://sheets.google.com) and create a new blank spreadsheet
2. Give it a name like `Strategic Copilot`
3. Copy the Sheet ID from the URL — it's the long string between `/d/` and `/edit`:
   `https://docs.google.com/spreadsheets/d/`**`YOUR_SHEET_ID`**`/edit`

That's it for now. **The script automatically creates all the tabs and headers the first time it runs.** You'll fill in your companies and profile in Steps 5 and 6.

### Optional tabs to add yourself

These two tabs are for your own use — the script doesn't read or write them, but they're useful as part of your search workflow:

**`1 - Master Connections`** — Your network. Export your LinkedIn connections (LinkedIn → Settings → Data Privacy → Get a copy of your data → Connections) and paste them here. Add a `Network Tier` column and mark your 20–30 highest-trust contacts as `Tier 1`. When a qualifying role appears, use this tab to find who can bridge you in.

**`4 - Proactive Targets`** — Where you log warm paths to target executives. Suggested columns:
```
Target Company | Target Executive | Their Title | LinkedIn URL | Tier 1 Bridge | Shared History | Strategic Rationale
```

---

## Step 2: Get a Google Service Account

A service account lets the script read and write your Google Sheet automatically without you having to log in each time. This is the most technical step — follow it carefully.

**2.1 Create a Google Cloud project**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click the project dropdown at the top → **New Project**
3. Name it `Strategic Copilot` → click **Create**
4. Make sure your new project is selected in the dropdown

**2.2 Enable the Google Sheets API**

1. In the left menu, go to **APIs & Services → Library**
2. Search for `Google Sheets API` → click it → click **Enable**

**2.3 Create a service account**

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → Service Account**
3. Name it `strategic-copilot` → click **Create and Continue**
4. Skip the optional steps → click **Done**
5. You'll see your new service account listed. Click on it.
6. Go to the **Keys** tab → **Add Key → Create new key → JSON → Create**
7. A `.json` file downloads to your computer. Keep it somewhere safe — you'll need it in Step 4, then you can delete it.

**2.4 Note the service account email**

On the service account page, copy the email address — it looks like:
```
strategic-copilot@your-project-name.iam.gserviceaccount.com
```

**2.5 Share your Google Sheet with the service account**

1. Open your Google Sheet
2. Click **Share** (top right)
3. Paste the service account email
4. Set permission to **Editor**
5. Uncheck "Notify people" → click **Share**

The script can now read and write your sheet.

---

## Step 3: Copy this repo to your GitHub account

**New to GitHub?** GitHub is a free service that stores code and can run it on a schedule — think of it like Google Drive for code, with a built-in timer. You need a free account to use it. If you'd prefer a guided walkthrough, paste this into Claude:

> I'm setting up a GitHub repository for an automated job search tool. I have no GitHub experience. Can you walk me through creating a free GitHub account and importing a repository as a private repo? The repo URL is [copy it from your browser address bar right now].

Otherwise, follow the steps below:

1. Create a free account at [github.com](https://github.com) if you don't have one
2. Go to [github.com/new/import](https://github.com/new/import)
3. In **Your old repository's clone URL**, paste: `https://github.com/jordanmilner-lgtm/strategic-copilot`
4. Name your new repository (e.g. `strategic-copilot`)
5. Set visibility to **Private** — your target company list and profile will live here, so keep it private
6. Click **Begin import** — GitHub copies all the code into your new private repo in about 30 seconds
7. **Enable GitHub Actions** — go to the **Actions** tab on your new repo and click **I understand my workflows, go ahead and enable them**. Without this step, the scan will never run.

*Note: GitHub's "Fork" button creates a public copy by default and free accounts cannot change a fork to private. The import method above creates a private repo from the start.*

---

## Step 4: Add your secrets to GitHub

Secrets are how GitHub securely stores the credentials the script needs to connect to Anthropic and Google. You don't create these values yourself — each one comes from a service you already set up or can get in under a minute. GitHub stores them encrypted so they're never visible in your code or to anyone else.

Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**.

Add these four secrets, one at a time:

**Secret 1: `OPENAI_API_KEY`**
- *Where it comes from:* OpenAI generates this for you automatically
- Go to [console.anthropic.com](https://console.anthropic.com) → **API Keys** → **Create Key** → copy the key it shows you (it starts with `sk-ant-`)
- Paste it as the value of this secret

**Secret 2: `GOOGLE_SHEETS_ID`**
- *Where it comes from:* it's already in your Google Sheet's URL — you don't need to generate anything
- Open your Google Sheet and look at the URL in your browser. Copy the long string between `/d/` and `/edit` — that string is your Sheet ID
- Paste that string as the value of this secret

**Secret 3: `GOOGLE_CREDENTIALS`**
- *Where it comes from:* this is the JSON file Google generated for you in Step 2.3, converted to a text format GitHub can store
- On a Mac: open Terminal and run:
  ```
  base64 -i ~/Downloads/your-key-file.json | pbcopy
  ```
  (Replace `your-key-file.json` with your actual filename. This copies the encoded value to your clipboard — paste it directly into the secret field.)
- On Windows: open PowerShell and run:
  ```
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\Users\you\Downloads\your-key-file.json")) | clip
  ```

**Secret 4: `RAPIDAPI_KEY`**
- *Where it comes from:* RapidAPI — this powers the broad job board search (LinkedIn, Indeed, Glassdoor) in Step 7
- Go to [rapidapi.com](https://rapidapi.com) and create a free account
- Search for **JSearch** and subscribe to the **OpenWeb Ninja** provider on the free tier (200 requests/month, no credit card required)
- Go to your RapidAPI dashboard → **Apps** → copy your API key
- Paste it as the value of this secret

*The broad search feature is optional — if you skip this secret, the pipeline still monitors your target company list. You can add it later.*

After adding all four secrets, you can delete the JSON file from your computer.

---

## Step 5: Build your scoring profile

The scoring profile is what makes this system work for *you* specifically. You provide your resume and a handful of sample job postings — the system analyzes them with Claude and writes your profile directly into your Google Sheet. No copy-paste needed.

**5.1 Add your resume**

In your GitHub repo, click **Add file → Create new file**. Name the file `setup/resume.txt`. Paste your full resume into the editor and click **Commit changes**.

**5.2 Add sample job descriptions**

Click **Add file → Create new file** again. Name it `setup/sample_jobs.txt`. Paste 3–5 job postings — include 2–3 roles that feel like strong fits AND 1–2 that are close but not quite right. The contrast is what helps Claude identify your real criteria. Click **Commit changes**.

*If you're using a public repo, make it private before adding these files (Settings → Change repository visibility). Delete the files after Step 5.4.*

**5.3 Run the profile builder**

Go to the **Actions** tab → click **Build Scoring Profile** in the left sidebar → click **Run workflow → Run workflow**.

The workflow reads your files, calls Claude, and writes your profile directly to the `Config - Profile` tab in your Google Sheet. It takes about 30 seconds.

**5.4 Review and complete your profile**

Open your Google Sheet and go to the `Config - Profile` tab. Review what was generated — the Background, Anchors, Keywords, and Negative Signals are filled in automatically. The **Comp Target** row is optional: if you fill it in (e.g. `$300K–$400K OTE`), each job will be flagged as `IN_RANGE`, `BELOW_RANGE`, or `NOT_LISTED`. Leave it blank to skip compensation filtering entirely.

Then delete `setup/resume.txt` from your repo — navigate to the file on GitHub, click the trash icon, and commit the deletion. Your resume is personal; don't leave it in a repo.

`setup/sample_jobs.txt` is optional to keep. If you leave it in place, the Generate Search Terms workflow (Step 7) will use your sample job descriptions alongside your profile to produce more targeted search queries — it learns from the actual language used in roles you found relevant. If you delete it, the workflow falls back to generating queries from your profile alone, which still works well.

**Score threshold:** defaults to 6. A score of 6 means "interesting but not obvious." Raise it to 7 if you're getting too much noise; lower it to 5 if you're missing roles you'd want to see.

**Filter settings** — the bottom four rows of the profile tab control which job titles get passed to the AI scorer. The Build Scoring Profile workflow sets these automatically, but you can adjust them:

| Field | What it does | Example |
|---|---|---|
| `Location` | Geography filter | `US only`, `Remote only`, or `Any` |
| `Seniority Keywords` | Title must contain one of these | `director, vp, head of, principal` |
| `Target Functions` | Title must also contain one of these | `gtm, sales, strategy, operations` |
| `Exclude Functions` | Title must NOT contain any of these | `engineer, legal, finance, recruiter` |

Use commas to separate values. Jobs that don't match your seniority + function criteria are skipped before scoring, keeping API costs low.

**Updating your profile later:** if your search evolves, repeat Steps 5.1–5.4 with updated materials at any time. Changes take effect on the next daily scan.

---

## Step 6: Add your target companies

Fill in your `Config - Companies` tab with the companies you want to monitor daily. Aim for 20–30 companies to start — enough for daily signal without noise.

Add your company names to the `Config - Companies` tab, then give Claude your list and it will look up the ATS type and handle for each one and tell you exactly what to enter. Some companies use job board systems that aren't publicly accessible — Claude will flag those and suggest alternatives.

**Think in tiers.** Not all companies on your list are equal, and that's fine — the system monitors them all the same way. But building your list with tiers in mind helps you prioritize when results come in.

**Tier A — Dream companies.** If they called tomorrow with the right role, you'd accept without hesitation. These are the companies where the mission, stage, leadership, product, and brand all align with what you're optimizing for. You know exactly why you'd want to work there. Aim for 8–12 of these.

**Tier B — Strong fits you'd pursue seriously.** Good companies where you'd be excited to interview and would likely say yes to a strong offer — but you haven't fully committed to them as your top choices. Maybe the industry is slightly adjacent, the stage isn't ideal, or you don't have a strong existing connection. These are where most of your active pipeline will come from. Aim for 10–15.

**Tier C — Worth watching.** Companies you're curious about or want to stay informed on, but wouldn't necessarily prioritize a proactive outreach. Good to have in the system so you don't miss a surprise opening, but not where you'd focus networking energy. Aim for 5–10.

**Practical sources for each tier:**
- Tier A: companies that came up in your last search that you didn't land at but wish you had; companies whose leadership you respect; companies your highest-trust network contacts have joined or spoken highly of
- Tier B: companies in your target industry at the right stage (Series B–D, growth-stage, pre-IPO); companies where you have second-degree connections; competitors to Tier A companies
- Tier C: companies you keep seeing in job alerts; adjacent industries you're open to; companies that are early but on a trajectory you find interesting


**Supported ATS platforms:** Ashby, Greenhouse, Lever, Gem, Workday, and SmartRecruiters. These cover the majority of tech and growth-stage companies.

**Unsupported platforms:** iCIMS, Taleo, Comeet, and SAP SuccessFactors don't expose public APIs. For companies on those platforms, check their job boards manually or set a Google Alert. Claude will flag these when you give it your company list.

---

## Step 7: Set up your broad search terms

In addition to monitoring your specific company list, the pipeline can search across LinkedIn, Indeed, Glassdoor, and other major job boards by role type — so you don't miss relevant postings at companies not on your radar.

You define the search terms as query strings in the `Config - Search Terms` tab. Each row is one query (e.g. `Director of Revenue Operations`, `VP of AI Strategy`, `Head of GTM`). The pipeline runs every active query every morning and scores the results against your profile the same way it scores your target company results.

**Generate your search terms automatically (recommended)**

The easiest way: run the **Generate Search Terms** workflow. It reads your scoring profile (built from your resume in Step 5) and, if you kept `setup/sample_jobs.txt`, your sample job descriptions — and uses Claude to generate 8–10 optimized search queries tailored to your background, level, and target functions. The sample job descriptions give it richer signal about how the roles you're targeting are actually titled and described.

1. Go to **Actions** → **Generate Search Terms** → **Run workflow → Run workflow**
2. Open `Config - Search Terms` in your sheet when it finishes
3. Review the queries — set `Active = N` for any you want to skip, and add your own rows at any time

**Writing your own search terms**

If you prefer to write them yourself, or want to add to what was generated, think about how recruiters actually title these roles — `Head of Revenue Operations` surfaces different results than `GTM Operations Leader`, even if they mean the same thing. A few principles:

- Combine a seniority level with a function: `Director of AI Strategy`, `VP of Sales Operations`, `Head of Enterprise GTM`
- Vary the combinations — don't repeat the same words in every query
- 5–10 active queries is a good starting point; more than that and you'll burn through your API quota quickly

Not sure where to start? Paste this into Claude along with a summary of your background:

> I'm setting up automated job board search queries for my job search. My background is [2-3 sentences]. I'm targeting [level] roles in [function area]. Generate 8-10 search query strings I can use to search LinkedIn, Indeed, and Glassdoor — written the way a recruiter would actually title these roles.

---

## Step 8: Run your first scan

1. Go to your forked repo on GitHub
2. Click the **Actions** tab
3. Click **Strategic Copilot Daily Scan** in the left sidebar
4. Click **Run workflow → Run workflow**

The scan will start within a few seconds. Click into the running job to watch the logs in real time.

**What to expect on first run:**
- Each company fetches all current jobs, applies the title/location filter, then scores what's new
- For large companies (100+ open roles), this takes a few minutes per company
- Total first-run time: 15–45 minutes depending on how many companies you have
- Anthropic API cost on first run: higher than normal, because the dedup cache is empty and every job gets scored. From the second day onward, only genuinely new postings are scored and costs drop dramatically.

After the run, open your Google Sheet and check the `3 - Opportunities CRM` tab. If you see results, you're set up correctly.

**After that:** the scan runs automatically every weekday at 11:23 AM UTC (7:23 AM Eastern / 4:23 AM Pacific). No action needed.

---

## Daily use

Open the `3 - Opportunities CRM` tab each morning. New rows from the overnight scan appear at the bottom. The columns to focus on:

- **Fit Score** (1–10) — your primary filter
- **Abstract Fit Flag** (YES/NO) — Claude's assessment of whether this is a genuine mandate match, not just keyword overlap
- **Corporate Bottleneck** — what business pain the company is trying to solve with this hire
- **Strategic Thesis** — why you are or aren't a fit, in two sentences

For roles that look promising: use the `1 - Master Connections` tab to find who in your network is connected to that company, then log the warm path in `4 - Proactive Targets`.

Add a **Status** column value (`Applied`, `Networking`, `Passed`, etc.) to keep track of what you've acted on.

---

## This is not set-it-and-forget-it

The pipeline runs itself, but getting value from it requires active management. Think of it less like a subscription and more like a search strategy you're running — one that needs tuning as the market moves and your thinking evolves.

**Review your results weekly, not just daily.** After the first week, look at what's surfacing:
- Are the scores making sense? If 8s and 9s feel mediocre when you read them, your profile thresholds or keywords may be off.
- Are you seeing roles at all? Low yield often means your title filters are too narrow, your company list is too small, or the companies you're watching simply don't have open roles right now.
- Are you missing roles you would have wanted? If you're finding better jobs through LinkedIn or word of mouth than through this system, that's a signal to expand your company list or loosen a filter.

**Update your company list as your search evolves.** Your Tier A and B lists will shift — companies get acquired, announce layoffs, move off your radar, or come onto it. Add new ones, mark stale ones inactive. A company list that's two months old is probably stale.

**Revisit your profile if your narrative changes.** Your profile drives scoring. If you're pivoting emphasis — different function, different stage, different geo — re-run the profile builder (Step 5) with updated materials and re-check your filter settings. The system scores what you tell it to care about; if your criteria shift but your profile doesn't, scores become misleading.

**Check the logs after your initial setup and after any changes.** GitHub Actions shows you exactly what happened per company — how many jobs were fetched, how many passed the title/location filter, and how many were new and got scored. Go to the **Actions** tab → click the most recent completed run → click into the job to see the full log.

Watch for a large gap between **Fetched** and **After filters** — for example, 200 jobs fetched and 0 after filters. That's a signal something is misconfigured, not that there are no open roles. This kind of silent failure is easy to miss: the system runs without errors, writes nothing to your Sheet, and it's impossible to tell from the Sheet alone whether that means "no new jobs today" or "a filter is blocking everything." The logs are the only place you'll see it.

Check the logs specifically:
- After your initial setup, to confirm the first run is producing output as expected
- After any changes to your profile, filters, or company list, to confirm the change had the intended effect
- Any time results drop suddenly or go to zero for multiple days in a row

**Use the output to sharpen your outreach, not just to track jobs.** The `Strategic Thesis` and `Corporate Bottleneck` columns are most useful when you act on them quickly — while the role is new and before your competition applies. If you're regularly seeing good roles but not acting on them within a day or two, the pipeline is doing its job but the system isn't.

---

## Adding a new company

1. Open the `Config - Companies` tab
2. Add a new row: company name, ATS type, handle, `Y` in Active
3. The next scheduled scan will include it automatically — no code changes needed

The first run for a new company scores all its current jobs. Subsequent runs only score new postings.

**If a company uses non-standard job titles** (e.g. "Lead" instead of "Director" or "VP"), add the relevant seniority keywords to the `Seniority Override` column for that company. This replaces the global seniority filter for that company only — leave it blank for all others.

---

## Pausing or removing a company

- **Pause:** Change `Active` from `Y` to `N` in the `Config - Companies` tab
- **Remove:** Delete the row entirely

---

## Adjusting your scoring profile

Edit the values in your `Config - Profile` tab at any time. Changes take effect on the next scan.

After your first week of results, review what's coming through and ask Claude:
> "Here are some roles that scored too high [paste examples]. And some that scored too low [paste examples]. What should I adjust in my scoring profile?"

A few targeted refinements after seeing real output will improve accuracy more than trying to perfect the profile upfront.

---

## Troubleshooting

**"No results in my sheet after the scan"**
Check the Actions log (click the completed run → click the job → expand the steps). Common causes:
- The title filter is blocking everything — your target companies may have few VP/Director-level GTM/ops roles open right now. Check the "After filters" count in the log.
- All jobs are already in the dedup cache (Scored URLs tab) — expected after the first run, means the system is working correctly
- The score threshold is too high — try lowering it to 5 temporarily to verify scores are being generated

**"The scan failed / showed an error"**
- Check that all three GitHub Secrets are set correctly (Settings → Secrets and variables → Actions)
- Verify the service account email is shared on your Google Sheet with Editor access
- If this is your first run, make sure the script ran all the way through — it creates the tabs automatically on first run

**"I'm seeing duplicate jobs"**
The `Scored URLs` tab is the dedup cache — every scored URL is written there so it's never scored again. If that tab was accidentally deleted, re-run the script and it will recreate it, but the history will be gone and the first run will re-score everything.

**"The scan is scoring too many jobs and costs are high"**
This is normal for the first 1–3 days after adding a new large company. The system scores all current jobs once, adds them to the dedup cache, and then only scores new postings going forward. Costs drop sharply after the first run per company.

**"A company's ATS handle isn't working"**
Test the API URL directly in your browser. For Ashby: `https://api.ashbyhq.com/posting-api/job-board/HANDLE` — if it returns JSON, the handle is correct. If it returns an error, double-check the handle from the company's careers page.

---

## Section A: Finding a company's ATS handle

1. Go to the company's careers page
2. Look at the URL when you click on a job posting:
   - **Ashby:** `jobs.ashbyhq.com/**handle**/job-id` → handle is the part after the first slash
   - **Greenhouse:** `boards.greenhouse.io/**handle**/jobs/job-id` → handle is after `boards.greenhouse.io/`
   - **Lever:** `jobs.lever.co/**handle**/job-id` → handle is after `jobs.lever.co/`
   - **Gem:** `jobs.gem.com/**handle**/job-id` → handle is after `jobs.gem.com/`
3. If the URL contains `myworkdayjobs.com`, see the Workday note below
4. If the URL doesn't match any of these patterns, the company uses an unsupported ATS (Comeet, iCIMS, SmartRecruiters, etc.) and can't be monitored directly

**Quick check:** paste this URL in your browser and replace HANDLE with your guess. If it returns a page of jobs, you've got the right handle and ATS.
- Ashby: `https://api.ashbyhq.com/posting-api/job-board/HANDLE`
- Greenhouse: `https://boards-api.greenhouse.io/v1/boards/HANDLE/jobs`
- Lever: `https://api.lever.co/v0/postings/HANDLE?mode=json`
- Gem: `https://api.gem.com/job_board/v0/HANDLE/job_posts/`

**Workday handles** use a different format: `subdomain.wdN/board` — for example `crowdstrike.wd5/crowdstrikecareers`. Find it by going to the company's careers page and looking at the URL: `https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers` → handle is `crowdstrike.wd5/crowdstrikecareers`.

---

*Built with Claude Code.*

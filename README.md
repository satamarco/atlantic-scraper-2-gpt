Atlantic Scraper 2 GPT

Overview
- Scrapes news from The Atlantic (global) and Unione Sarda (local Sardinia), aggregates an article, and uses OpenCode Zen (GPT-5 Nano) to generate a detailed dossier.
- Uses a health-check before hitting the OpenCode endpoint to ensure resilience.
- When the OpenCode endpoint is unavailable, the system emits a bilingual fallback article to keep CI and workflows flowing.

Configuration
- OpenCode Zen base URL: https://opencode.ai/zen/v1
- Model: gpt-5-nano
- Secrets (GitHub Actions):
  - OPENCODE_API_KEY: Your OpenCode API key
  - OPENCODE_BASE_URL: https://opencode.ai/zen/v1
- Local environment (.env):
  - AI_PROVIDER=opencode
  - OPENCODE_API_KEY=your-key
  - OPENCODE_BASE_URL=https://opencode.ai/zen/v1

How to run
- Local:
  - Set up a Python venv and install requirements
  - Run: cron_scraper.py (via Python) or streamlit app as appropriate
- CI (GitHub Actions):
  - Ensure secrets are set as above
  - Trigger the daily workflow from Actions (or manual Run workflow)

Observations
- The system prints the provider in use and logs health check outcomes to stdout for debugging.
- The pool generation aims for at least 2 international and 2 local articles in a light mode run.

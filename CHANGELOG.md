# Changelog

## Unreleased

### Patch 0.1.1
- Remove image generation in cron_scraper.py: archived articles now saved without image paths.
- Remove automatic 12-hour cron trigger in GitHub Actions: release is now manual via workflow_dispatch only.
- Set Opencode as primary AI provider with explicit test integration, and remove automatic Google fallback.
- Add local test_integration_provider script to verify provider configuration without triggering network calls.
- Add .env.local guidance in README and update .env.example to reflect required Opencode keys (OPENCODE_API_KEY, OPENCODE_BASE_URL).
- Adjust Python typing for Python 3.9 compatibility in several modules.


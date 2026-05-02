# Atlantic Scraper 2 GPT

Sistema Python/Streamlit basato su `atlantic-scraper`: raccoglie articoli da fonti internazionali e sarde, genera un dossier con GPT, crea un'immagine e salva tutto in `archivio.json`.

## Struttura

- `app.py`: interfaccia Streamlit con countdown e archivio cumulativo.
- `scraper.py`: scraping multi-source con Playwright e BeautifulSoup.
- `cron_scraper.py`: orchestrazione scraping, generazione GPT, immagine e salvataggio archivio.
- `.github/workflows/daily_update.yml`: esecuzione automatica ogni 12 ore su GitHub Actions.
- `archivio.json`, `used_links.json`, `assets/`: dati generati dal sistema.

## Setup locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Poi inserisci la chiave in `.env`:

```bash
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

## Comandi

```bash
streamlit run app.py
python cron_scraper.py
```

## GitHub

Prima del push su GitHub, crea nel repository il secret `OPENAI_API_KEY`.

Il workflow esegue `cron_scraper.py` ogni 12 ore, poi committa automaticamente gli aggiornamenti di `archivio.json`, `used_links.json` e `assets/`.

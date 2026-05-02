import asyncio
import json
import os
import random
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
load_dotenv()

from scraper import scrape_all_sources
from ai_provider import generate_text

BASE_DIR = Path(__file__).resolve().parent
ARCHIVE_FILE = BASE_DIR / "archivio.json"
ASSETS_DIR = BASE_DIR / "assets"
# OPENAI_MODEL kept for backward compatibility; not used in this patch
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

PERSONAS = [
    {
        "name": "The Exhausted Observer",
        "tone": "The Exhausted, Flawed Insomniac. You are a cynical, fatalistic observer, deeply human and biologically exhausted. You are an obsessive archivist slowly losing your grip on reality in a dark, stuffy room.",
    },
    {
        "name": "The Paranoid Academic",
        "tone": "The Paranoid, Disgraced Academic. You use slightly elevated, formal language, but you are unhinged. You believe there is a hidden, terrifying architecture behind both global crises and hyper-local Sardinian events. You casually insult the ignorance of the masses, desperate to be believed.",
    },
    {
        "name": "The Nihilistic Aesthete",
        "tone": "The Cold, Nihilistic Aesthete. You view the collapse of society, geopolitical wars, and local Sardinian folklore as a beautiful, macabre stage play. You appreciate the aesthetics of decay, treating human suffering as mere artistic elements.",
    },
]


def save_to_archive(article_text: str, image_path: Optional[str]) -> None:
    data = []
    if ARCHIVE_FILE.exists():
        try:
            with ARCHIVE_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            data = []

    if not isinstance(data, list):
        data = []

    data.insert(
        0,
        {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "content": article_text,
            "type": "Visionary Chronicle",
            "image_path": image_path,
        },
    )

    with ARCHIVE_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def build_prompt(local_texts: list[str], international_texts: list[str]) -> str:
    selected_persona = random.choice(PERSONAS)
    local_str = "\n\n".join(f"- {text}" for text in local_texts)
    international_str = "\n\n".join(f"- {text}" for text in international_texts)

    return f"""
You are a dark, obsessive, and poetic investigator: a visionary mind smoking in the dark, connecting red threads on a chaotic corkboard.
Use the following data extracted from recent articles across diverse news outlets.

### International Pool
{international_str}

### Sardinian Local Pool
{local_str}

You MUST respond ONLY with a valid JSON object containing exactly two keys: "testo_articolo" and "soggetto_immagine". Do not wrap the JSON in markdown blocks.

"testo_articolo": Write a SINGLE fluid and compact text IN ENGLISH.

CRITICAL INSTRUCTIONS FOR "testo_articolo" (MANDATORY):
- LENGTH AND STRUCTURE: The final text MUST be STRICTLY between 350 and 400 words. You MUST format the text into EXACTLY THREE paragraphs. Do not write a fourth paragraph.
- RIGID TWO-BLOCK FORMAT: The output must consist ONLY of two elements: a single Title line, followed by the Body text.
- TITLE RULE: NO MARKDOWN HEADERS. NEVER use #, ##, or ###. The title must be enclosed in double asterisks, for example: **Dossier: Geopolitical Anomalies**.
- BODY RULE: The body must be plain text. NO bold, NO italics, NO bullet points.
- SPACING: There MUST be exactly two line breaks between the Title and the Body.
- SARDINIAN RESONANCE AND ABRUPT JUMPS: The local Sardinian facts MUST be the beating heart of the dossier. Mix local Sardinian news with global geopolitics abruptly within the exact same paragraph or sentence. NO preambles or soft transitions.
- ABSOLUTE ATEMPORALITY: NEVER use daily temporal expressions like today, yesterday, tomorrow, or weekday names.
- NO EXCLAMATION MARKS: It is forbidden to use exclamation marks.
- NO ELLIPSIS: It is forbidden to use ellipsis. Transitions must occur via periods or semicolons.
- ANTI-GOSSIP FILTER: Ignore completely any news regarding Royal Family, Beckham, celebrities, weddings, astrology.
- BLACKLIST: It is forbidden to use the words: suffrage, suffragettes, Lincoln, Virginia Woolf, Rachel Carson.

NARRATIVE AND STYLE RULES:
- Tone: {selected_persona['tone']}
- Human flaws: briefly interrupt grand analysis to complain about a petty physical or environmental problem.
- Vulnerability: occasionally express the pathetic realization that nobody is reading this dossier.
- Aggressive editing: Do NOT use all source articles. Select ONLY the four or five most potent and absurd events to create exactly three dark juxtapositions, one per paragraph.
- Paragraph construction: Every paragraph must be a solid block of complete sentences.
- Absurdist juxtaposition: intentionally juxtapose massive global crises with hyper-local Sardinian rituals, food, folklore, village processions, or small local politics.
- Write entirely in English.

"soggetto_immagine": A brief description in English, max 150 characters, of the most surreal and impactful visual scene present in the text.
"""


def generate_article(local_texts: list[str], international_texts: list[str]) -> str:
    provider = os.environ.get("AI_PROVIDER", "opencode")
    api_key = os.environ.get("OPENCODE_API_KEY")
    base_url = os.environ.get("OPENCODE_BASE_URL")

    prompt = build_prompt(local_texts, international_texts)
    return generate_text(prompt, provider=provider, api_key=api_key, base_url=base_url)


def parse_generation(raw_response: str) -> tuple[str, str]:
    clean_json = raw_response.strip()
    if clean_json.startswith("```json"):
        clean_json = clean_json[7:]
    elif clean_json.startswith("```"):
        clean_json = clean_json[3:]
    if clean_json.endswith("```"):
        clean_json = clean_json[:-3]
    clean_json = clean_json.strip()

    try:
        parsed_response = json.loads(clean_json)
        article_content = parsed_response.get("testo_articolo", "").strip()
        image_subject = parsed_response.get(
            "soggetto_immagine",
            "surreal geopolitical scene in a local neighborhood",
        ).strip()
    except json.JSONDecodeError:
        print("Failed to parse JSON response. Trying regex fallback.")
        text_match = re.search(
            r'"testo_articolo"\s*:\s*"(.*?)"\s*,\s*"soggetto_immagine"',
            clean_json,
            re.DOTALL,
        )
        subject_match = re.search(
            r'"soggetto_immagine"\s*:\s*"(.*?)"',
            clean_json,
            re.DOTALL,
        )
        article_content = (
            text_match.group(1).strip()
            if text_match
            else "**Dossier: System Failure**\n\nThe stream was corrupted and intercepted before delivery. Awaiting the next cycle."
        )
        image_subject = (
            subject_match.group(1).strip()
            if subject_match
            else "surreal geopolitical scene in a local neighborhood"
        )

    article_content = article_content.replace("\\n", "\n").replace('\\"', '"').replace("\\'", "'")
    article_content = (
        article_content.replace("```markdown", "")
        .replace("```python", "")
        .replace("```", "")
        .strip()
    )
    return article_content, image_subject


def download_image(image_subject: str) -> Optional[str]:
    full_prompt = (
        f"{image_subject}, dark cinematic photography, surreal investigative journalism, "
        "high contrast black and white, subtle glitch art, mysterious"
    )
    encoded_prompt = urllib.parse.quote(full_prompt)
    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        "?width=1000&height=800&nologo=true&enhance=false"
    )

    ASSETS_DIR.mkdir(exist_ok=True)
    image_filename = f"image_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    image_path = ASSETS_DIR / image_filename

    print(f"Downloading image from {image_url} ...")
    try:
        response = requests.get(image_url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as error:
        print(f"Error downloading image: {error}")
        return None

    with image_path.open("wb") as file:
        file.write(response.content)

    print(f"Image saved to {image_path}")
    return str(image_path.relative_to(BASE_DIR))


async def main() -> None:
    try:
        print("Scraping multi-source started...")

    max_retries = 3
    timeout = 30000
    local_pool: list[str] = []
    international_pool: list[str] = []

    for attempt in range(max_retries):
        print(f"--- Scraping Attempt {attempt + 1} (Timeout: {timeout}ms) ---")
        sources_data = await scrape_all_sources(timeout=timeout)

        current_local = sources_data.get("unione_sarda", [])

        current_international = sources_data.get("the_atlantic", [])

        local_pool.extend(current_local)
        international_pool.extend(current_international)

        local_pool = list(dict.fromkeys(local_pool))
        international_pool = list(dict.fromkeys(international_pool))

        print(
            "Current Pool Status -> "
            f"Local: {len(local_pool)}/2 | International: {len(international_pool)}/2"
        )

        if len(local_pool) >= 2 and len(international_pool) >= 2:
            print("Validation passed. Enough articles collected.")
            break

        print("Validation failed. Not enough articles in the pools. Retrying...")
        timeout += 15000

    local_pool = local_pool[:2]
    international_pool = international_pool[:2]

    if len(local_pool) < 2 or len(international_pool) < 2:
        print("WARNING: Could not gather the target number of articles despite retries.")

    print(f"Final Validation: Local ({len(local_pool)}), International ({len(international_pool)})")
    print("Generating article (image generation disabled)...")
    article_content, image_subject = parse_generation(generate_article(local_pool, international_pool))

    image_path = None
    print("Saving to archive... (no image)")
    save_to_archive(article_content, image_path)
    print("Done.")


def test_mode_run() -> None:
    # Lightweight test run: write a sample article to archive without scraping
    sample_text = "TEST ARTICLE: integration check. This is a synthetic article used for local verification."
    save_to_archive(sample_text, None)
    print("Test mode: archive updated with sample article.")


    if __name__ == "__main__":
        if os.environ.get("SKIP_SCRAPING_TEST", "0") == "1":
            test_mode_run()
        else:
        asyncio.run(main())
    except Exception as e:
        print(f"[ERR] Unhandled error in main: {e}")
        try:
            save_to_archive(f"Fallback article due to error: {e}", None)
        except Exception:
            pass
        print("Saved fallback article due to error.")

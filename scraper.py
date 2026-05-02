import asyncio
import json
import random
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import Page, async_playwright


BASE_DIR = Path(__file__).resolve().parent
USED_LINKS_FILE = BASE_DIR / "used_links.json"

SOURCES = {
    "the_atlantic": {
        "base_url": "https://www.theatlantic.com",
        "sections": ["/world/", "/politics/", "/science/", "/technology/", "/business/"],
        "link_selector": "a[href*='/archive/']",
    },
    "unione_sarda": {
        "base_url": "https://www.unionesarda.it",
        "sections": ["/news-sardegna/", "/tempo-libero/", "/cultura/"],
        "link_selector": "article a, h2 a, h3 a",
    },
    "sardinia_post": {
        "base_url": "https://www.sardiniapost.it",
        "sections": ["/category/cucina-e-cibo/", "/category/culture/", "/category/eventi/"],
        "link_selector": "h3 a, .entry-title a",
    },
    "nbc_news": {
        "base_url": "https://www.nbcnews.com",
        "sections": ["/world", "/politics", "/tech", "/science", "/business"],
        "link_selector": "h2 a, .v-f a",
    },
    "vice": {
        "base_url": "https://www.vice.com/en",
        "sections": ["/section/news", "/section/tech", "/section/world", "/section/politics"],
        "link_selector": "h3 a, .hdg a",
    },
    "cronache_nuoresi": {
        "base_url": "https://www.cronachenuoresi.it",
        "sections": ["/category/cultura-e-societa/", "/category/eventi/"],
        "link_selector": "h2 a, .entry-title a",
    },
}


def load_used_links() -> set[str]:
    if not USED_LINKS_FILE.exists():
        return set()

    try:
        with USED_LINKS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return set()

    return set(data) if isinstance(data, list) else set()


def save_used_links(links: set[str]) -> None:
    with USED_LINKS_FILE.open("w", encoding="utf-8") as file:
        json.dump(sorted(links), file, indent=4)


async def fetch_article_data(page: Page, url: str, timeout: int = 30000) -> str | None:
    try:
        await page.goto(url, timeout=timeout)
        await page.wait_for_load_state("domcontentloaded")
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        date_meta = (
            soup.find("meta", {"property": "article:published_time"})
            or soup.find("meta", {"name": "pubdate"})
            or soup.find("meta", {"name": "parsely-pub-date"})
        )

        if date_meta:
            date_str = date_meta.get("content")
            if date_str:
                try:
                    clean_date = date_str.split("T")[0]
                    published_at = datetime.strptime(clean_date, "%Y-%m-%d")
                    if (datetime.now() - published_at).days > 180:
                        return None
                except ValueError:
                    pass

        paragraphs = soup.find_all("p")
        text = " ".join(
            paragraph.get_text().strip()
            for paragraph in paragraphs
            if len(paragraph.get_text().strip()) > 40
        )
        text_snippet = " ".join(text.split()[:400])

        if len(text_snippet) < 100:
            return None

        return text_snippet
    except Exception:
        return None


async def scrape_all_sources(timeout: int = 30000) -> dict[str, list[str]]:
    used_links = load_used_links()
    new_used_links = set(used_links)
    sources_data: dict[str, list[str]] = {source_name: [] for source_name in SOURCES}

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        for source_name, source_info in SOURCES.items():
            print(f"\n=== Exploring {source_name.upper()} ===")
            valid_articles: list[str] = []
            collected_links: set[str] = set()

            sections = list(source_info["sections"])
            random.shuffle(sections)

            for section in sections:
                if len(collected_links) >= 15:
                    break

                section_url = source_info["base_url"] + section
                print(f"-> Scanning section: {section_url}")

                try:
                    await page.goto(section_url, timeout=timeout)
                    await page.wait_for_timeout(2000)
                    links = await page.query_selector_all(source_info["link_selector"])

                    for link in links:
                        href = await link.get_attribute("href")
                        if not href:
                            continue

                        if href.startswith("/"):
                            href = source_info["base_url"] + href

                        if (
                            href.startswith(source_info["base_url"])
                            and href not in used_links
                            and href not in collected_links
                        ):
                            collected_links.add(href)
                except Exception:
                    print(f"   [!] Failed scanning section {section_url}")

            shuffled_links = list(collected_links)
            random.shuffle(shuffled_links)

            for url in shuffled_links:
                if len(valid_articles) >= 3:
                    break

                print(f"   - Testing article: {url}")
                text = await fetch_article_data(page, url, timeout=timeout)
                if text:
                    print("     [+] Valid. Added to collection.")
                    valid_articles.append(text)
                else:
                    print("     [-] Discarded: too old, short, or inaccessible.")

                new_used_links.add(url)

            sources_data[source_name] = valid_articles
            print(f"-> Completed {source_name}: {len(valid_articles)}/3 articles collected.")

        await browser.close()

    save_used_links(new_used_links)
    return sources_data


if __name__ == "__main__":
    data = asyncio.run(scrape_all_sources())
    for source, texts in data.items():
        print(f"Final count {source}: {len(texts)}")

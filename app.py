import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ARCHIVE_FILE = BASE_DIR / "archivio.json"

st.set_page_config(page_title="Atlantic Scraper 2 GPT", layout="centered")

st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    .viewerBadge_container {display: none !important;}

    *, html, body, [class*="css"], .stApp, .block-container {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        color: #000000 !important;
        font-weight: bold !important;
        letter-spacing: -0.05em !important;
    }

    .main-title {
        font-size: 3.5rem !important;
        font-weight: bold;
        margin-top: 0 !important;
        padding-top: 0 !important;
        margin-bottom: 0 !important;
        letter-spacing: -0.05em;
        line-height: 0.95;
    }

    hr {
        border: none !important;
        border-top: 1px solid #000000 !important;
        margin: 1.5rem 0 !important;
    }

    .countdown-text {
        font-size: 5rem;
        font-weight: bold;
        color: #000000;
        text-align: left;
        letter-spacing: -0.05em;
        line-height: 1;
        margin-bottom: 0 !important;
    }

    [data-testid="stImage"] img {
        filter: grayscale(100%) !important;
        border-radius: 0 !important;
        margin-bottom: 2rem !important;
    }

    .archive-date {
        font-size: 1rem;
        font-weight: bold;
        color: #000000;
        text-transform: uppercase;
        display: block;
        margin-bottom: 1rem;
    }

    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 4rem !important;
        max-width: 800px !important;
    }

    p, div {
        line-height: 1.6 !important;
        font-size: 1.1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<div class='main-title'>Atlantic Scraper 2 GPT</div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)
countdown_placeholder = st.empty()
st.markdown("<hr>", unsafe_allow_html=True)

article_placeholder = st.empty()


def _load_archive() -> list[dict[str, str | None]]:
    if not ARCHIVE_FILE.exists():
        return []

    try:
        with ARCHIVE_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        article_placeholder.error("Error reading archivio.json")
        return []

    return data if isinstance(data, list) else []


def render_article() -> None:
    archive_data = _load_archive()
    if not archive_data:
        article_placeholder.info("No article available yet.")
        return

    with article_placeholder.container():
        for index, entry in enumerate(archive_data):
            st.markdown(
                f"<div class='archive-date'>{entry.get('timestamp', '')}</div>",
                unsafe_allow_html=True,
            )

            content = (entry.get("content") or "").strip()
            lines = content.split("\n")
            title = lines[0].replace("*", "").strip() if lines else ""
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

            st.markdown(
                f"<div class='article-container' style='font-weight:bold; margin-bottom: 1rem;'>{title}</div>",
                unsafe_allow_html=True,
            )

            image_path = entry.get("image_path")
            if image_path:
                absolute_image_path = BASE_DIR / image_path
                if absolute_image_path.exists():
                    st.image(str(absolute_image_path), use_container_width=True)

            for paragraph in [part.strip() for part in body.split("\n\n") if part.strip()]:
                st.markdown(f"<p>{paragraph}</p>", unsafe_allow_html=True)

            if index < len(archive_data) - 1:
                st.markdown("<hr>", unsafe_allow_html=True)


def next_utc_cycle(now: datetime) -> datetime:
    if now.hour < 12:
        return now.replace(hour=12, minute=0, second=0, microsecond=0)
    return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


render_article()

while True:
    current_time = datetime.now(timezone.utc)
    diff = next_utc_cycle(current_time) - current_time
    hours, remainder = divmod(int(diff.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown_placeholder.markdown(
        f"<div class='countdown-text'>{hours:02d}:{minutes:02d}:{seconds:02d}</div>",
        unsafe_allow_html=True,
    )
    time.sleep(1)

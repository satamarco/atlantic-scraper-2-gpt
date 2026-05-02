import json
import os
from typing import Optional

import google.generativeai as genai


def _generate_text_google(prompt: str, api_key: Optional[str] = None) -> str:
    # Configure Gemini via Google Generative AI
    if api_key:
        genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="text/plain"
        ),
    )
    return getattr(response, "text", "")


def _generate_text_opencode(prompt: str, api_key: str, base_url: str) -> str:
    import requests

    headers = {"Authorization": f"Bearer {api_key}"}
    url = base_url.rstrip("/") + "/generate"
    resp = requests.post(url, json={"prompt": prompt}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("text", data.get("response", ""))


def generate_text(prompt: str, provider: str = "google", api_key: Optional[str] = None, base_url: Optional[str] = None) -> str:
    provider = (provider or "google").lower()
    if provider == "opencode":
        if api_key and base_url:
            return _generate_text_opencode(prompt, api_key, base_url)
        raise RuntimeError("OPENCODE_API_KEY and OPENCODE_BASE_URL must be set to use Opencode as provider.")
    # default to Google Gemini (no fallback)
    return _generate_text_google(prompt, api_key)

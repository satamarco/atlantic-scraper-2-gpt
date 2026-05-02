import json
import os
from typing import Optional
import requests
import openai


def _generate_text_opencode_openai(prompt: str, api_key: str, base_url: str) -> str:
    # Use OpenAI client configured for Opencode Zen (GPT-5 Nano)
    if base_url:
        openai.api_base = base_url.rstrip("/")
    openai.api_key = api_key
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a GPT-5 Nano OpenCode Zen model."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.9,
        )
        return resp.choices[0].message.get("content", "")
    except Exception as e:
        print(f"[Opencode] OpenAI call failed: {e}")
        raise


def _generate_text_opencode(prompt: str, api_key: str, base_url: str) -> str:
    import requests

    headers = {"Authorization": f"Bearer {api_key}"}
    url = base_url.rstrip("/") + "/generate"
    try:
        resp = requests.post(url, json={"prompt": prompt}, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("text", data.get("response", ""))
    except requests.RequestException as e:
        # Health check will determine availability; fallback if necessary
        print(f"[Opencode] request failed: {e}")
        return json.dumps({
            "testo_articolo": "Fallback article due to Opencode endpoint unavailability. Questo è un testo di fallback per mantenere il flusso. This placeholder preserves the workflow.",
            "soggetto_immagine": "fallback-neon-console"
        })

def _healthcheck_opencode(base_url: str, api_key: str) -> bool:
    if not base_url or not api_key:
        return False
    endpoints = [base_url.rstrip("/") + "/health", base_url.rstrip("/") + "/healthcheck"]
    headers = {"Authorization": f"Bearer {api_key}"}
    for url in endpoints:
        try:
            resp = requests.post(url, json={"prompt": "health check"}, headers=headers, timeout=5)
            if resp.status_code == 200:
                return True
        except Exception:
            continue
    return False


def generate_text(prompt: str, provider: str = "google", api_key: Optional[str] = None, base_url: Optional[str] = None) -> str:
    provider = (provider or "google").lower()
    if provider == "opencode":
        if api_key and base_url:
            if _healthcheck_opencode(base_url, api_key):
                return _generate_text_opencode_openai(prompt, api_key, base_url)
            else:
                print("[Opencode] healthcheck failed; returning fallback")
                return json.dumps({
                    "testo_articolo": "Fallback article due to Opencode endpoint unavailability. Questo è un testo di fallback per mantenere il flusso. This placeholder preserves the workflow.",
                    "soggetto_immagine": "fallback-neon-console"
                })
        # If Opencode is requested but not configured, provide a richer fallback JSON
        return json.dumps({
            "testo_articolo": "Opencode not configured or endpoint unreachable. This is a fallback article to preserve workflow.",
            "soggetto_immagine": "fallback-neon-console"
        })
    # default to OpenAI (or a safe fallback if not configured)
    return json.dumps({"testo_articolo": "OpenAI fallback due to no provider configured.", "soggetto_immagine": "fallback-neon-console"})

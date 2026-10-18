#!/usr/bin/env python3
"""
Minimal local YouTube → creator name + LinkedIn extractor.
Uses yt-dlp + Playwright. Optional Ollama for better extraction.
No external paid APIs required.
"""

import argparse
import json
import re
import subprocess
import sys
from typing import Optional

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

OLLAMA_URL = "http://localhost:11434/api/generate"
SEARXNG_URL = "http://localhost:8888/search"


def get_youtube_info(url: str) -> dict:
    """Extract channel info using yt-dlp."""
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--print",
        "%(channel)s|||%(uploader)s|||%(channel_id)s|||%(description)s|||%(webpage_url)s",
        url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        parts = result.stdout.strip().split("|||")
        if len(parts) < 5:
            raise ValueError("Unexpected yt-dlp output")
        return {
            "channel": parts[0],
            "uploader": parts[1],
            "channel_id": parts[2],
            "description": parts[3],
            "webpage_url": parts[4],
        }
    except Exception as e:
        print(f"[!] yt-dlp failed: {e}", file=sys.stderr)
        return {}


def search_local(query: str) -> list:
    """Query local SearXNG if available."""
    try:
        r = requests.get(SEARXNG_URL, params={"q": query, "format": "json"}, timeout=15)
        if r.status_code == 200:
            return r.json().get("results", [])[:5]
    except Exception:
        pass
    return []


def extract_linkedin_from_page(url: str) -> Optional[str]:
    """Use Playwright to load a page and find LinkedIn profile URLs."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=20000)
            content = page.content()
            browser.close()

        # Look for linkedin.com/in/ in the full rendered HTML (catches onclick too)
        matches = re.findall(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?", content)
        if matches:
            return matches[0].rstrip("/")
    except Exception as e:
        print(f"[!] Playwright failed on {url}: {e}", file=sys.stderr)
    return None


def ask_ollama(text: str) -> dict:
    """Ask local Ollama model to extract name + LinkedIn."""
    prompt = (
        "Extract the person's full name and LinkedIn profile URL from the text below. "
        "Return ONLY valid JSON with keys 'name' and 'linkedin'. "
        "If not found, use null.\n\nText:\n" + text[:4000]
    )
    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False},
            timeout=60,
        )
        if r.status_code == 200:
            raw = r.json().get("response", "")
            # Try to pull JSON out of the response
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
    except Exception:
        pass
    return {}


def main():
    parser = argparse.ArgumentParser(description="YouTube URL → creator name + LinkedIn")
    parser.add_argument("url", help="YouTube video, channel, or playlist URL")
    parser.add_argument("--no-search", action="store_true", help="Skip local web search")
    parser.add_argument("--no-llm", action="store_true", help="Skip Ollama extraction")
    args = parser.parse_args()

    print("[*] Fetching YouTube metadata...")
    info = get_youtube_info(args.url)
    if not info:
        print(json.dumps({"error": "Could not extract YouTube info"}, indent=2))
        sys.exit(1)

    result = {
        "channel": info.get("channel"),
        "uploader": info.get("uploader"),
        "channel_id": info.get("channel_id"),
        "possible_name": None,
        "linkedin": None,
        "sources": [],
    }

    # Direct LinkedIn in description?
    desc = info.get("description") or ""
    direct = re.findall(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?", desc)
    if direct:
        result["linkedin"] = direct[0].rstrip("/")
        result["sources"].append("youtube_description")

    # Search for personal sites
    candidates = []
    if not args.no_search and info.get("channel"):
        print("[*] Searching locally for personal site / LinkedIn...")
        queries = [
            f'"{info["channel"]}" LinkedIn',
            f'"{info["channel"]}" (portfolio OR about OR personal OR site)',
        ]
        for q in queries:
            for hit in search_local(q):
                url = hit.get("url")
                if url and "youtube.com" not in url:
                    candidates.append(url)

    # Visit top candidates with Playwright
    seen = set()
    for url in candidates[:4]:
        if url in seen:
            continue
        seen.add(url)
        print(f"[*] Checking {url}")
        li = extract_linkedin_from_page(url)
        if li:
            result["linkedin"] = li
            result["sources"].append(url)
            break

    # Optional LLM cleanup
    if not args.no_llm and (result["linkedin"] or info.get("description")):
        print("[*] Asking local LLM for name...")
        context = f"Channel: {info.get('channel')}\nDescription: {desc}\nLinkedIn: {result.get('linkedin')}"
        llm = ask_ollama(context)
        if llm.get("name"):
            result["possible_name"] = llm["name"]
        if llm.get("linkedin") and not result["linkedin"]:
            result["linkedin"] = llm["linkedin"]

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

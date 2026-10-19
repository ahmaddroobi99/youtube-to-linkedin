#!/usr/bin/env python3
"""
Simple local server that serves index.html and exposes /extract endpoint.
Uses the same logic as main.py.
"""

import json
import re
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional

import requests
from playwright.sync_api import sync_playwright

OLLAMA_URL = "http://localhost:11434/api/generate"
SEARXNG_URL = "http://localhost:8888/search"
PORT = 8000


def get_youtube_info(url: str) -> dict:
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
        return {"error": str(e)}


def search_local(query: str) -> list:
    try:
        r = requests.get(SEARXNG_URL, params={"q": query, "format": "json"}, timeout=15)
        if r.status_code == 200:
            return r.json().get("results", [])[:5]
    except Exception:
        pass
    return []


def extract_linkedin_from_page(url: str) -> Optional[str]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=20000)
            content = page.content()
            browser.close()
        matches = re.findall(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?", content)
        if matches:
            return matches[0].rstrip("/")
    except Exception as e:
        print(f"[!] Playwright failed on {url}: {e}", file=sys.stderr)
    return None


def ask_ollama(text: str) -> dict:
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
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return json.loads(m.group(0))
    except Exception:
        pass
    return {}


def extract(url: str) -> dict:
    info = get_youtube_info(url)
    if "error" in info:
        return {"error": info["error"]}

    result = {
        "channel": info.get("channel"),
        "uploader": info.get("uploader"),
        "channel_id": info.get("channel_id"),
        "possible_name": None,
        "linkedin": None,
        "sources": [],
    }

    desc = info.get("description") or ""
    direct = re.findall(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?", desc)
    if direct:
        result["linkedin"] = direct[0].rstrip("/")
        result["sources"].append("youtube_description")

    candidates = []
    if info.get("channel"):
        queries = [
            f'"{info["channel"]}" LinkedIn',
            f'"{info["channel"]}" (portfolio OR about OR personal OR site)',
        ]
        for q in queries:
            for hit in search_local(q):
                u = hit.get("url")
                if u and "youtube.com" not in u:
                    candidates.append(u)

    seen = set()
    for u in candidates[:4]:
        if u in seen:
            continue
        seen.add(u)
        li = extract_linkedin_from_page(u)
        if li:
            result["linkedin"] = li
            result["sources"].append(u)
            break

    if result["linkedin"] or desc:
        context = f"Channel: {info.get('channel')}\nDescription: {desc}\nLinkedIn: {result.get('linkedin')}"
        llm = ask_ollama(context)
        if llm.get("name"):
            result["possible_name"] = llm["name"]
        if llm.get("linkedin") and not result["linkedin"]:
            result["linkedin"] = llm["linkedin"]

    return result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = Path("index.html").read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/extract":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                url = data.get("url", "").strip()
                if not url:
                    raise ValueError("Missing url")
                result = extract(url)
            except Exception as e:
                result = {"error": str(e)}

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode("utf-8"))
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")


if __name__ == "__main__":
    print(f"Serving on http://localhost:{PORT}")
    print("Open the URL in your browser and paste a YouTube link.")
    HTTPServer(("", PORT), Handler).serve_forever()

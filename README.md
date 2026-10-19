# youtube-to-linkedin

Minimal local tool that takes a YouTube URL (video, channel, or playlist) and tries to find the creator's real name + LinkedIn (or personal profile page).

**No Google APIs required.** Everything runs on your machine.

## Requirements

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Playwright](https://github.com/microsoft/playwright)
- Optional: [Ollama](https://github.com/ollama/ollama) + a small model
- Optional: [SearXNG](https://github.com/searxng/searxng) for local web search

## Install

```bash
git clone https://github.com/ahmaddroobi99/youtube-to-linkedin.git
cd youtube-to-linkedin
pip install -r requirements.txt
playwright install chromium
```

Optional:
```bash
ollama pull qwen2.5:7b
docker run -d -p 8888:8080 searxng/searxng
```

## CLI usage

```bash
python main.py "https://www.youtube.com/watch?v=Ynqfo_Vxpp8"
```

## Web UI

```bash
python server.py
```

Then open **http://localhost:8000** in your browser.

Paste a YouTube URL into the text field and click **Extract**. The result appears as JSON below the form.

## How it works

1. `yt-dlp` extracts channel handle, title, and description.
2. Optional local search (SearXNG) for the channel + LinkedIn / personal site.
3. Playwright visits candidate sites and extracts LinkedIn URLs (including ones hidden in JavaScript).
4. Optional local Ollama model cleans up the name.

## Limitations

- Works best when the creator has a public personal site or LinkedIn mention.
- LinkedIn scraping itself is limited without a logged-in session.
- Results depend on channel name uniqueness.

## License

MIT

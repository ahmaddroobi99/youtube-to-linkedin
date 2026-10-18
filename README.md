# youtube-to-linkedin

Minimal local tool that takes a YouTube URL (video, channel, or playlist) and tries to find the creator's real name + LinkedIn (or personal profile page).

**No Google APIs required.** Everything runs on your machine.

## Requirements

- Python 3.9+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Playwright](https://github.com/microsoft/playwright) (for JS-rendered personal sites)
- Optional: [Ollama](https://github.com/ollama/ollama) + a small model for better name/LinkedIn extraction
- Optional: [SearXNG](https://github.com/searxng/searxng) for local web search

## Install

```bash
git clone https://github.com/ahmaddroobi99/youtube-to-linkedin.git
cd youtube-to-linkedin
pip install -r requirements.txt
playwright install chromium
```

Optional (recommended for better results):
```bash
# Ollama
# Install from https://ollama.com then:
ollama pull qwen2.5:7b

# SearXNG (local search)
docker run -d -p 8888:8080 searxng/searxng
```

## Usage

```bash
python main.py "https://www.youtube.com/watch?v=Ynqfo_Vxpp8"
```

Or with a channel/playlist URL.

### Example output
```json
{
  "channel": "ProjectMaria",
  "uploader": "ProjectMaria",
  "possible_name": "Maria Kuprikova",
  "linkedin": "https://www.linkedin.com/in/maria-kuprikova-084b95283",
  "sources": ["projectmaria.net"]
}
```

## How it works

1. Uses `yt-dlp` to extract channel handle, title, and description.
2. Optionally searches locally (SearXNG) for the channel + "LinkedIn" / personal site.
3. Uses Playwright to visit candidate sites and extract LinkedIn URLs (including ones hidden in JavaScript `onclick` handlers).
4. Optionally asks a local Ollama model to clean up the name and confirm the profile.

## Limitations

- Works best when the creator has a personal site or LinkedIn linked somewhere public.
- LinkedIn itself is hard to scrape without a logged-in session; this tool prefers extracting the URL from the creator's own pages.
- Results depend on how unique the channel name is.

## License

MIT

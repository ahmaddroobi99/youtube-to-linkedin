# Deploy Online

This tool uses Playwright (headless Chromium) and yt-dlp, so it needs a container host rather than pure serverless (Vercel free tier will timeout or fail on browser install).

## Recommended: Render.com (free tier)

1. Push this repo to GitHub (already done).
2. Go to https://render.com → New → Web Service.
3. Connect the GitHub repo `ahmaddroobi99/youtube-to-linkedin`.
4. Render detects the `Dockerfile`.
5. Deploy. It will build and run `python server.py`.
6. You get a public URL like `https://youtube-to-linkedin.onrender.com`.

## Alternative: Railway.app

Same flow — connect the repo, it detects the Dockerfile.

## Alternative: Fly.io

```bash
fly launch
fly deploy
```

## Notes

- First build takes a few minutes because of Chromium.
- Free tiers sleep after inactivity; first request after sleep is slow.
- Optional local Ollama / SearXNG are not included in the container (they stay on your machine if you run locally).
- For pure serverless demo you can strip Playwright and only return yt-dlp metadata, but that loses the LinkedIn extraction from personal sites.

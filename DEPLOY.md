# Deploy Online

This tool uses Playwright (headless Chromium) and yt-dlp, so it needs a container host rather than pure serverless.

## Recommended: Render.com (free tier)

1. Go to https://render.com and sign in with GitHub.
2. **New → Web Service**.
3. Connect the repo `ahmaddroobi99/youtube-to-linkedin`.
4. Render detects the `Dockerfile` automatically.
5. Click **Create Web Service**.

After the build finishes you get a public URL (e.g. `https://youtube-to-linkedin.onrender.com`).

The Docker image installs:
- Latest `yt-dlp`
- Deno (JS runtime for YouTube)
- Playwright + Chromium

## Notes

- First build takes several minutes (Chromium + Deno).
- Free tiers sleep after inactivity; the first request after sleep is slow.
- YouTube bot detection can still happen on shared IPs. For best results use the local version with browser cookies.
- Optional local Ollama / SearXNG are not included in the container.

## Alternative: Railway.app

Same flow — connect the repo, it detects the Dockerfile.

## Alternative: Fly.io

```bash
fly launch
fly deploy
```

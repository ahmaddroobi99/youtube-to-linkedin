FROM python:3.11-slim

WORKDIR /app

# System deps for Playwright + yt-dlp + Deno
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (JS runtime required for full YouTube support)
RUN curl -fsSL https://deno.land/install.sh | sh && \
    ln -s /root/.deno/bin/deno /usr/local/bin/deno

COPY requirements.txt .
RUN pip install --no-cache-dir -U yt-dlp && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

ENV PORT=8000
CMD ["python", "server.py"]

FROM python:3.11-slim

WORKDIR /app

# Install system deps for Playwright + yt-dlp
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

COPY . .

EXPOSE 8000

CMD ["python", "server.py"]

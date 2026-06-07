FROM python:3.13-slim

# Instala Node.js + Chrome pro Puppeteer
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    chromium \
    chromium-sandbox \
    && rm -rf /var/lib/apt/lists/*

# Node.js 22.x
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Diz pro Puppeteer usar o Chromium do sistema
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Node.js
COPY package.json package-lock.json ./
RUN npm ci --omit=dev || npm install --omit=dev

# Codigo
COPY . .

# Porta do Render
EXPOSE 10000

# Script de start
CMD ["bash", "start.sh"]

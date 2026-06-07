FROM python:3.13-slim

# Node.js 22.x
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

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

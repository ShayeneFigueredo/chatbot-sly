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

# Node.js (backend WhatsApp)
COPY package.json package-lock.json ./
RUN npm ci --omit=dev || npm install --omit=dev

# Node.js (painel React + Vite)
COPY frontend/painel/package.json frontend/painel/package-lock.json ./frontend/painel/
RUN cd frontend/painel && npm install && npm run build

# Codigo
COPY . .

# Porta do Render
EXPOSE 10000

# Script de start
CMD ["bash", "start.sh"]

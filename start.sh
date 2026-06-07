#!/bin/bash
set -e

echo "==========================================="
echo " Maya Sly Design - Iniciando servicos"
echo "==========================================="

# Inicia o servidor Python (Maya) em background
echo "[1/2] Iniciando servidor Python (Maya)..."
cd /app
PORT=${PORT:-8000}
python -m uvicorn backend.webhook_server:app --host 0.0.0.0 --port $PORT &
PYTHON_PID=$!

# Espera o Python estar pronto
echo "       Aguardando Python na porta $PORT..."
for i in $(seq 1 15); do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo "       Python OK"
        break
    fi
    sleep 1
done

# Inicia o wppconnect (WhatsApp Web)
echo "[2/2] Iniciando wppconnect..."
node connect_whatsapp.js

# Se o Node morrer, mata o Python tambem
kill $PYTHON_PID 2>/dev/null

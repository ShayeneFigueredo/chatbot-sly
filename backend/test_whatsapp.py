"""
Teste rápido: enviar mensagem da Maya pro seu WhatsApp.
Rode: .venv/bin/python backend/test_whatsapp.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Configurações da Meta
TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = "1174471599080821"  
SEU_NUMERO = "+5538997507651"  

# URL da API
url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"

# Cabeçalhos
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# Mensagem de texto livre (funciona por 24h depois do cliente falar primeiro)
data = {
    "messaging_product": "whatsapp",
    "to": SEU_NUMERO,
    "type": "text",
    "text": {"body": "Oie! Sou a Maya, atendente da Sly Design! 💜 Deu certo o teste!"},
}

print("📤 Enviando mensagem de teste...")
resposta = requests.post(url, headers=headers, json=data)
print(f"Status: {resposta.status_code}")
print(f"Resposta: {resposta.json()}")

if resposta.status_code == 200:
    print("\n✅ Mensagem enviada! Olha seu WhatsApp!")
else:
    print("\n❌ Algo deu errado. Confere o token e o número.")

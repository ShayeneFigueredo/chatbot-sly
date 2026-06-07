"""
Simulador da Maya (terminal). Mesmo código do WhatsApp.
"""
import sys, re
sys.path.insert(0, '/mnt/c/aprendendo-IA/chatbot-sly')
from backend.webhook_server import maya_responder, clientes

print("=" * 55)
print("🤖 Maya — Simulador Local")
print("   Digite 'sair' pra encerrar, 'reset' pra limpar")
print("=" * 55)

tel = "5511999999999"

while True:
    msg = input("\n▶️  Você: ").strip()
    if not msg:
        continue
    if msg.lower() == "sair":
        print("👋 Até mais!")
        break
    if msg.lower() == "reset":
        clientes.clear()
        print("🔄 Conversa reiniciada!")
        continue

    resposta = maya_responder(msg, tel)
    # Formata igual WhatsApp
    resposta = re.sub(r'\[(\d)\]', r'*[ \1 ]*', resposta)
    print(f"\n🤖 Maya:\n{resposta}")
    print("-" * 55)

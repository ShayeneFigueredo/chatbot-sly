"""
Teste LOCAL da Maya (sem depender da Meta).
Simula mensagens de WhatsApp e vê as respostas.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.webhook_server import maya_responder

# Simula clientes mandando mensagens reais
testes = [
    "quanto custa um slide?",
    "tem tema do minecraft?",
    "faz pra hoje urgente?",
    "quais temas vocês tem?",
    "comprei um slide e não consigo abrir",
    "me ajuda a editar o slide?",
    "qual a diferença entre canva e powerpoint?",
    "batata frita",  # não tem no catálogo
]

print("=" * 55)
print("🤖 TESTE LOCAL — Maya respondendo como no WhatsApp")
print("=" * 55)

for msg in testes:
    resposta = maya_responder(msg, "5511999999999")
    print(f"\n💬 Cliente: {msg}")
    print(f"🤖 Maya:   {resposta[:120]}...")
    print("-" * 55)

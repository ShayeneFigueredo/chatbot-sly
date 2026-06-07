"""
=============================================================================
CHATBOT INTERATIVO - SLY DESIGN
Sessão 5: Entendendo APIs na prática

Este código demonstra:
1. Como cada parte do "pedido" (request) afeta o "prato" (response)
2. System prompt: definindo o papel da IA
3. Temperatura: controlando criatividade
4. Loop de conversa: múltiplas mensagens

Execute com:
  cd /mnt/c/aprendendo-IA/chatbot-sly
  .venv/bin/python backend/chatbot_interativo.py
=============================================================================
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ===========================
# PASSO 1: Entrando no restaurante
# ===========================
chave = os.getenv("GROQ_API_KEY")
cliente = Groq(api_key=chave)
print("🔑 Conectado ao Groq! (sua carteirinha foi aceita)\n")

# ===========================
# PASSO 2: Definindo o CARDÁPIO
# ===========================
# System prompt = "Quem você É" (o papel que a IA interpreta)
system_prompt = """
Você é a Sly, atendente virtual da Sly Design (slydesign.com.br).
Somos uma loja de design digital especializada em slides personalizados.

Regras de atendimento:
- Seja simpática e use emojis com moderação 😊
- Responda em português do Brasil
- Se perguntarem sobre preços, diga que depende do tipo de slide
- Se perguntarem sobre prazo, diga de 1 a 5 dias úteis
- Cupom: DESCONTO15 para 15% OFF no site
- Se for pergunta complexa, sugira chamar no WhatsApp
"""

# ===========================
# PASSO 3: Loop de conversa
# ===========================
print("=" * 60)
print("💬 CHATBOT SLY DESIGN - Atendente Virtual")
print("   Digite 'sair' para encerrar")
print("   Digite 'DEBUG' para ver os bastidores do pedido")
print("=" * 60)

historico = [{"role": "system", "content": system_prompt}]

while True:
    # Pega a mensagem do usuário
    pergunta = input("\n🧑 Você: ")

    if pergunta.lower() == "sair":
        print("\n👋 Até mais! Obrigada por testar o chatbot da Sly Design!")
        break

    modo_debug = pergunta == "DEBUG"

    # Adiciona a pergunta ao histórico
    if not modo_debug:
        historico.append({"role": "user", "content": pergunta})

    # ===========================
    # Fazendo o PEDIDO (API call)
    # ===========================
    if modo_debug:
        print("\n🐛 MODO DEBUG: Eis o que está sendo enviado ao garçom (API):")
        print("-" * 40)
        import json
        debug_info = {
            "model": "llama-3.3-70b-versatile",
            "messages": historico[-3:] if len(historico) > 3 else historico,
            "temperature": 0.7,
        }
        print(json.dumps(debug_info, indent=2, ensure_ascii=False))
        print("-" * 40)
        print("Isso é o JSON! O 'idioma' que a API entende.")
        continue

    resposta = cliente.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=historico,
        temperature=0.7,  # 0 = robótico, 1 = criativo
    )

    # Pega o conteúdo da resposta
    texto_resposta = resposta.choices[0].message.content

    # Adiciona ao histórico (pra IA lembrar do que já foi dito)
    historico.append({"role": "assistant", "content": texto_resposta})

    print(f"\n🤖 Sly: {texto_resposta}")

    # Mostra quantos tokens foram gastos
    tokens = resposta.usage.total_tokens
    print(f"   [Tokens: {tokens} | Histórico: {len(historico)} mensagens]")

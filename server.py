"""
Servidor Webhook — MAYA NO WHATSAPP 💜
Máquina de estados completa + NLP + LLM fallback.

Local: .venv/bin/python server.py
Render: uvicorn server:app --host 0.0.0.0 --port 10000
"""
import os
import sys
import json
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# Carrega .env localmente (no Render usa Environment Variables direto)
load_dotenv("backend/.env")

from app.nlp import detectar_intencao
from app.buscador import buscar_tema
from app.config import SYSTEM_PROMPT, PRECOS, TEMAS_DISPONIVEIS

app = FastAPI()

# ── Configurações de notificação ──
SHAY_NUMERO = "+5538997507651"
META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = "1174471599080821"

# ── Clientes em atendimento humano (Maya não responde) ──
atendimento_humano = {}  # {telefone: True}


def enviar_whatsapp(telefone: str, mensagem: str):
    """Envia uma mensagem de volta pro cliente via WhatsApp Cloud API."""
    if not META_TOKEN:
        print("⚠️ META_TOKEN não configurado. Mensagem NÃO enviada!")
        return False

    # Garante que o numero tem o + na frente (Meta exige)
    if not telefone.startswith("+"):
        telefone = "+" + telefone

    url = f"https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {META_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": mensagem},
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resultado = resp.json()
        print(f"📤 Meta API: {resp.status_code} — {resultado}")
        if resp.status_code == 200:
            print(f"📤 Maya → {telefone}: enviado ✅")
        else:
            print(f"⚠️ Erro ao enviar p/ {telefone}: {resp.status_code} — {resultado}")
        return resp.status_code == 200
    except Exception as e:
        print(f"⚠️ Exceção ao enviar p/ {telefone}: {e}")
        return False


def notificar_shay(mensagem: str):
    """Envia uma notificação WhatsApp pro número pessoal da Shay."""
    enviar_whatsapp(SHAY_NUMERO, mensagem)


def cliente_em_atendimento_humano(telefone: str) -> bool:
    """Verifica se o cliente está sendo atendido por um humano."""
    return atendimento_humano.get(telefone, False)

# ── Estado dos clientes ──
clientes = {}


def mostrar_menu():
    return (
        "Oie! Seja bem-vindo(a) à Sly Design! 💜\n\n"
        "Aqui a gente tem slides prontos super legais "
        "e também criamos do zero, do seu jeitinho. ✨\n\n"
        "Temos MUITA coisa legal no site e com super descontos! 💜\n"
        "Dá uma olhadinha:\n\n"
        "👉 https://slydesign.com.br/loja/\n\n"
        "No que posso te ajudar?\n\n"
        "[1] 🛍️ Ver Slides Prontos\n"
        "[2] 🎨 Quero um Slide Personalizado\n"
        "[3] 🔍 Consultar um Tema\n"
        "[4] 💰 Quanto Custa?\n"
        "[5] 💬 Tirar uma Dúvida\n\n"
        "💡 Você pode digitar o número ou escrever sua pergunta!"
    )


def maya_responder(mensagem: str, telefone: str) -> str:
    t = mensagem.lower().strip()

    # ── COMANDOS DA SHAY (dona) ──
    if telefone == SHAY_NUMERO:
        if t.startswith("assumir "):
            cliente_alvo = t.replace("assumir ", "").strip()
            atendimento_humano[cliente_alvo] = True
            print(f"🙋 Shay assumiu atendimento de {cliente_alvo}")
            return f"✅ Você agora está atendendo {cliente_alvo}! A Maya vai silenciar pra esse número. Quando terminar, mande 'liberar {cliente_alvo}'"
        if t.startswith("liberar "):
            cliente_alvo = t.replace("liberar ", "").strip()
            atendimento_humano.pop(cliente_alvo, None)
            print(f"🤖 Maya voltou a atender {cliente_alvo}")
            return f"✅ Maya voltou a responder {cliente_alvo}!"
        if t == "humanos":
            lista = "\n".join(atendimento_humano.keys()) if atendimento_humano else "Nenhum no momento."
            return f"👥 Clientes em atendimento humano:\n{lista}"
        # Shay falando algo normal → ignora (não chama IA)

    # ── Cliente sendo atendido por humano? Maya fica quieta ──
    if cliente_em_atendimento_humano(telefone):
        print(f"🤫 Maya silenciada para {telefone} (atendimento humano)")
        return None  # não responde nada

    # Inicializa
    novo_cliente = telefone not in clientes
    if novo_cliente:
        clientes[telefone] = {"tela": "menu", "dados_pedido": {}}
    estado = clientes[telefone]
    tela = estado["tela"]
    dados = estado["dados_pedido"]

    print(f"   📍 Tela: {tela} | {'🆕' if novo_cliente else ''} | 💬 {t[:80]}")

    # ── PRIMEIRA MENSAGEM: sempre menu, ignora tudo ──
    if novo_cliente:
        return mostrar_menu()

    # ── ATENDIMENTO HUMANO (qualquer tela) ──
    if any(p in t for p in ["humano", "atendente", "pessoa", "falar com", "gente de verdade"]) or t in ("7", "🆘"):
        estado["tela"] = "menu"
        estado["dados_pedido"] = {}
        notificar_shay(
            f"🆘 {telefone} pediu atendimento humano!\n"
            f"Última mensagem: \"{mensagem[:100]}\""
        )
        return (
            "Claro! Aguarde uns minutinhos que já já um de nossos "
            "atendentes entrará em contato com você por aqui mesmo! 💜\n\n"
            "Fique de olho nas notificações! ✨\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # ── VOLTAR AO MENU ──
    if t in ("menu", "voltar", "🔙 voltar ao menu", "0"):
        estado["tela"] = "menu"
        estado["dados_pedido"] = {}
        return mostrar_menu()

    # ── SAUDAÇÃO ──
    saudacoes = ["oi", "olá", "ola", "oie", "bom dia", "boa tarde", "boa noite", "tudo bem"]
    if tela == "menu" and any(t == s or t.startswith(s) for s in saudacoes) and len(t.split()) <= 3:
        return mostrar_menu()

    # ═══════════════════════════════════════════
    # MENU PRINCIPAL
    # ═══════════════════════════════════════════
    if tela == "menu":
        if t in ("1", "ver slides prontos"):
            estado["tela"] = "slides_prontos"
            return (
                "Nossa, temos MUITA coisa legal no site! 💜\n"
                "De trabalhos da escola até temas de facul, "
                "dá uma olhadinha:\n\n"
                "👉 https://slydesign.com.br/loja/\n\n"
                "É só escolher, comprar e já cai no seu e-mail! 📧\n\n"
                "Ou se quiser, me fala um tema que eu procuro pra você 🔍\n\n"
                "[2] 🎨 Quero um Slide Personalizado\n"
                "[0] 🔙 Voltar ao menu"
            )

        if t in ("2", "quero um slide personalizado"):
            estado["tela"] = "pedido_tema"
            estado["dados_pedido"] = {}
            return (
                "Ihuuul! 🎉 Vamos criar seu slide personalizado!\n\n"
                "Vou te fazer umas perguntinhas rápidas, ok?\n\n"
                "📝 Primeiro: qual o ASSUNTO do slide?\n\n"
                "[0] 🔙 Voltar ao menu"
            )

        if t in ("3", "consultar um tema"):
            estado["tela"] = "buscando_tema"
            return "Qual tema você está procurando? 🔍"

        if t in ("4", "quanto custa?"):
            estado["tela"] = "precos"
            return _msg_precos()

        if t in ("5", "tirar uma dúvida"):
            estado["tela"] = "duvida"
            return "Pode perguntar! O que você quer saber? 💜"

        # NLP
        intencao = detectar_intencao(mensagem)

        if intencao == "preco":
            estado["tela"] = "precos"
            return _msg_precos()

        if intencao == "prazo":
            return (
                "Sobre prazos, funciona assim: 💜\n\n"
                "📅 Prazo normal: até 2 dias.\n"
                "⚡ Pedido para o mesmo dia: taxa adicional de R$ 5,00 "
                "(se houver vaga na agenda).\n\n"
                "💡 Recomendamos pedir com pelo menos 1 dia de antecedência "
                "da sua apresentação.\n\n"
                "Se quiser, já podemos começar seu pedido! 🎨\n\n"
                "[2] 🎨 Quero fazer um pedido!\n"
                "[0] 🔙 Voltar ao menu"
            )

        if intencao == "listar_temas":
            return (
                "Temos VÁRIOS temas! Dá uma olhadinha na loja: 💜\n\n"
                "👉 https://slydesign.com.br/loja/\n\n"
                "Ou me fala um tema específico que eu procuro pra você! 🔍"
            )

        if intencao == "suporte_tecnico":
            estado["tela"] = "duvida_compra"
            return (
                "Entendo! Vamos resolver isso. 💜\n\n"
                "Primeiro: qual o tema do slide que você comprou? 🛒"
            )

        if intencao == "ajuda_montagem":
            return (
                "Claro! Pra editar ou montar seu slide, "
                "dá uma olhada nesses tutoriais: 🎨\n\n"
                "📹 Como editar no Canva: https://youtu.be/hI56FSKNg0c\n"
                "📹 Como comprar (passo a passo): https://youtu.be/wyuXppcptrk\n\n"
                "Se quiser um modelo específico, me fala qual tema "
                "que eu te mando o link direto! 💜"
            )

        if intencao == "buscar_tema":
            return _buscar_tema_handler(mensagem, estado)

        # Fallback: IA
        return _chamar_ia(mensagem, estado)

    # ═══════════════════════════════════════════
    # SLIDES PRONTOS
    # ═══════════════════════════════════════════
    if tela == "slides_prontos":
        if t in ("2",) or "personalizado" in t:
            estado["tela"] = "pedido_tema"
            estado["dados_pedido"] = {}
            return "Ihuuul! 🎉 Vamos criar seu slide personalizado!\n\n📝 Qual o ASSUNTO do slide?\n\n[0] 🔙 Voltar ao menu"
        if "buscar" in t or len(t) > 3:
            estado["tela"] = "buscando_tema"
            return _buscar_tema_handler(mensagem, estado)
        estado["tela"] = "menu"
        return mostrar_menu()

    # ═══════════════════════════════════════════
    # BUSCANDO TEMA
    # ═══════════════════════════════════════════
    if tela == "buscando_tema":
        return _buscar_tema_handler(mensagem, estado)

    # ═══════════════════════════════════════════
    # PREÇOS
    # ═══════════════════════════════════════════
    if tela == "precos":
        if t in ("2",) or "pedido" in t or "comprar" in t:
            estado["tela"] = "pedido_tema"
            estado["dados_pedido"] = {}
            return "📝 Qual o ASSUNTO do slide?\n\n[0] 🔙 Voltar ao menu"
        estado["tela"] = "menu"
        return mostrar_menu()

    # ═══════════════════════════════════════════
    # DÚVIDA
    # ═══════════════════════════════════════════
    if tela == "duvida":
        if any(p in t for p in ["comprei", "não consigo abrir", "deu erro", "não chegou"]):
            estado["tela"] = "duvida_compra"
            return "Qual o tema do slide que você comprou? 🛒"
        estado["tela"] = "menu"
        return _chamar_ia(mensagem, estado)

    # ═══════════════════════════════════════════
    # DÚVIDA DE COMPRA
    # ═══════════════════════════════════════════
    if tela == "duvida_compra":
        if any(p in t for p in ["não comprei", "nao comprei", "não", "nao", "nunca"]):
            estado["tela"] = "menu"
            return "Ahh, entendi! Você quer fazer um pedido novo, não dar suporte. 💜\n\n" + mostrar_menu()
        estado["tela"] = "menu"
        return _chamar_ia(
            f"A cliente comprou o slide '{mensagem}' no site slydesign.com.br "
            f"e está com um problema. Pergunte qual o problema específico "
            f"e tente ajudar. Slides do site são em Canva ou PowerPoint. "
            f"Se não conseguir resolver, passe para um humano: (34) 99930-6554.",
            estado
        )

    # ═══════════════════════════════════════════
    # FLUXO DE PEDIDO
    # ═══════════════════════════════════════════

    # PASSO 1: Tema
    if tela == "pedido_tema":
        dados["tema"] = mensagem
        if estado.pop("modo_edicao", False):
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado["tela"] = "pedido_tipo"
        return (
            "Certo, anotei o tema! 📝\n\n"
            "Agora me conta: qual TIPO de slide você prefere?\n\n"
            "Você pode conferir exemplos de cada tipo aqui:\n"
            "👉 https://slydesign.com.br/personalizados/\n\n"
            "[1] 📄 PDF — R$ 20,00\n"
            "   Slide com design sobre seu assunto, sem animações\n\n"
            "[2] 🎬 Canva (Transições) — R$ 25,00\n"
            "   Design feito com base no seu assunto, com movimentos,\n"
            "   efeitos e animações. Link online\n\n"
            "[3] 🎬 PowerPoint (Transições) — R$ 35,00\n"
            "   Mesmo do Canva, mas arquivo PPTX offline\n\n"
            "[4] 🎨 Slide Temas Canva — R$ 28,00\n"
            "   Tema visual criativo (ex: Netflix, Spotify). Link online\n\n"
            "[5] 🎨 Slide Temas PPTX — R$ 38,00\n"
            "   Tema visual criativo em arquivo PPTX offline\n\n"
            "[6] 🤔 Diferença entre Canva e PowerPoint\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2: Tipo
    if tela == "pedido_tipo":
        tipos = {
            "1": "📄 PDF", "2": "🎬 Canva (Transições)", "3": "🎬 PowerPoint (Transições)",
            "4": "🎨 Canva Temas", "5": "🎨 PPTX Temas"
        }

        if t == "6" or "diferença" in t or "diferenca" in t:
            return (
                "Visualmente são iguais! 🎨\n\n"
                "📱 Canva — link online, acessa pelo navegador.\n"
                "💻 PowerPoint — arquivo PPTX offline e app.\n\n"
                "Só muda a forma de acessar. Qual tipo você prefere?\n\n"
                "[1] 🎬 Canva (Transições) — R$ 25,00\n"
                "[2] 🎬 PowerPoint (Transições) — R$ 35,00\n"
                "[3] 🎨 Canva Temas — R$ 28,00\n"
                "[4] 🎨 PPTX Temas — R$ 38,00\n"
                "[0] 🔙 Voltar ao menu"
            )

        # Mapeia números da tela de diferença
        diff_map = {"1": "🎬 Canva (Transições)", "2": "🎬 PowerPoint (Transições)",
                    "3": "🎨 Canva Temas", "4": "🎨 PPTX Temas"}
        if t in tipos:
            dados["modelo"] = tipos[t]
        elif t in tipos.values():
            dados["modelo"] = t
        elif t in diff_map:
            dados["modelo"] = diff_map[t]
        elif t in diff_map.values():
            dados["modelo"] = t
        elif t in ("canva", "📱 canva", "📱"):
            dados["modelo"] = "🎬 Canva (Transições)"
        elif t in ("powerpoint", "ppt", "💻", "pptx", "💻 powerpoint"):
            dados["modelo"] = "🎬 PowerPoint (Transições)"
        else:
            dados["modelo"] = mensagem

        modo_edicao = estado.pop("modo_edicao", False)

        # Se escolheu Temas, guarda o assunto e pergunta QUAL tema
        if "Temas" in dados.get("modelo", ""):
            # Salva o assunto original (ex: "povos astecas") antes de perguntar o tema visual
            dados["assunto"] = dados.get("tema", "")
            estado["tela"] = "pedido_qual_tema"
            if modo_edicao:
                estado["modo_edicao"] = True  # mantém o flag pra pedido_qual_tema
            top5 = ", ".join(TEMAS_DISPONIVEIS[:5])
            return (
                "Legal! Temos vários temas prontos. 💜\n\n"
                f"Os mais pedidos: {top5}...\n\n"
                "E tem mais no site:\n"
                "👉 https://slydesign.com.br/loja/\n\n"
                "Se quiser um tema que não está na lista, "
                "podemos criar do zero. Me diga qual tema você quer?\n\n"
                "[0] 🔙 Voltar ao menu"
            )

        # Se está editando tipo (não-Temas), volta pro resumo
        if modo_edicao:
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)

        # Se não é Temas e não está editando, continua fluxo normal
        estado["tela"] = "pedido_prazo"
        return (
            "Anotado! ✅\n\n"
            "Agora sobre o PRAZO: até que dia posso te entregar?\n\n"
            "💡 Recomendamos pedir com pelo menos 1 dia de antecedência "
            "da sua apresentação.\n\n"
            "Me conta: qual data você precisa? 📅\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2.5: Qual tema? (slides temas)
    if tela == "pedido_qual_tema":
        dados["tema_design"] = mensagem  # tema visual (ex: "pequena sereia"), NÃO sobrescreve o assunto
        if estado.pop("modo_edicao", False):
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado["tela"] = "pedido_prazo"
        return (
            "Anotado! ✅\n\n"
            "Agora sobre o PRAZO: até que dia posso te entregar?\n\n"
            "Me conta: qual data você precisa? 📅\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 3: Prazo
    if tela == "pedido_prazo":
        dados["prazo"] = mensagem
        if any(p in t for p in ["hoje", "hj", "mesmo dia", "ainda hoje"]):
            msg = (
                "⚠️ Como é para hoje, temos uma taxa adicional de R$ 5,00 "
                "e preciso verificar se ainda há vaga na agenda. "
                "Vou confirmar com a equipe, um momento!\n\n"
            )
        else:
            msg = ""
        if estado.pop("modo_edicao", False):
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado["tela"] = "pedido_nomes"
        return (
            f"{msg}"
            f"Anotei o prazo! 📅\n\n"
            f"Quer adicionar os NOMES de vocês no slide?\n"
            f"Se sim, me diga quais nomes.\n"
            f"Se não, é só responder 'não'. 💜\n\n"
            f"[0] 🔙 Voltar ao menu"
        )

    # PASSO 4: Nomes
    if tela == "pedido_nomes":
        if t in ("não", "nao", "n", "não quero", "nao quero", "🚫 não quero"):
            dados["nomes"] = "Não"
        else:
            dados["nomes"] = mensagem
        if estado.pop("modo_edicao", False):
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado["tela"] = "pedido_extras"
        dados["extras"] = ""
        return (
            "Quase lá! 📝\n\n"
            "Quer adicionar mais alguma informação?\n"
            "Ex: resumo, tópicos específicos, jeito que quer o design, "
            "referências, arquivos...\n"
            "Ah, e a pesquisa do conteúdo é por nossa conta se você "
            "preferir! 🔍\n\n"
            "⚠️ Importante: depois que o slide estiver pronto, qualquer "
            "alteração tem uma taxa de R$ 1,50 por página editada.\n\n"
            "📄 Nosso limite padrão é de 10 páginas. A partir da 11ª, "
            "cada página extra tem custo de R$ 1,50.\n\n"
            "Se o conteúdo for muito grande, você prefere:\n"
            "[1] 📝 Pode resumir para caber em 10 páginas\n"
            "[2] ➕ Pode adicionar tudo (te aviso quantas páginas deu)\n\n"
            "Pode mandar quantas mensagens quiser. 💜\n\n"
            "[3] ✅ Finalizar Pedido\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 5: Extras
    if tela == "pedido_extras":
        if t in ("3", "finalizar", "finalizar pedido", "✅ finalizar pedido", "✅ Finalizar Pedido"):
            pass  # vai pro resumo
        elif t in ("não", "nao", "nenhum"):
            if not dados.get("extras") or dados["extras"] in ("Nenhum",):
                dados["extras"] = "Nenhum"
        elif t in ("1", "resumir"):
            # Cliente prefere resumir em 10 páginas
            dados["extras"] = "Prefere resumir em 10 págs"
            dados["paginas_extra"] = False
            return (
                "Anotado! 📝 Vamos resumir em até 10 páginas. "
                "Quer adicionar mais alguma coisa? 💜\n\n"
                "[3] ✅ Finalizar Pedido\n"
                "[0] 🔙 Voltar ao menu"
            )
        elif t in ("2", "adicionar tudo", "+"):
            # Cliente quer adicionar tudo (mais de 10 págs possível)
            dados["paginas_extra"] = True
            dados["extras"] = "Quer adicionar todo conteúdo"
            return (
                "Certo! ✨ Vamos colocar todo o conteúdo. Te aviso "
                "quantas páginas deu no final. Quer adicionar mais "
                "alguma coisa? 💜\n\n"
                "[3] ✅ Finalizar Pedido\n"
                "[0] 🔙 Voltar ao menu"
            )
        else:
            if dados.get("extras") and dados["extras"] not in ("Nenhum",):
                dados["extras"] += " | " + mensagem
            else:
                dados["extras"] = mensagem
            return (
                "Recebi! ✅ Pode mandar mais se quiser. 💜\n\n"
                "[3] ✅ Finalizar Pedido\n"
                "[0] 🔙 Voltar ao menu"
            )

        # Só chega aqui se for finalizar ou não/nenhum
        if not dados.get("extras"):
            dados["extras"] = "Nenhum"
        estado["tela"] = "resumo"
        return _mostrar_resumo(dados)

    # PASSO 6: Resumo
    if tela == "resumo":
        if t in ("1", "confirmar", "✅ confirmar", "confirmar pedido"):
            estado["tela"] = "pagamento"
            notificar_shay(
                f"🎨 NOVO PEDIDO de {telefone}!\n\n"
                f"📝 Tema: {dados.get('tema', '?')}\n"
                f"🎨 Tipo: {dados.get('modelo', '?')}\n"
                f"📅 Prazo: {dados.get('prazo', '?')}\n"
                f"👤 Nomes: {dados.get('nomes', 'Não')}\n"
                f"📎 Extras: {dados.get('extras', 'Nenhum')}\n\n"
                f"💡 Pra revisar: use 'assumir {telefone}' pra assumir o atendimento"
            )
            return _msg_pagamento(dados)
        if t in ("3", "cancelar", "❌ cancelar"):
            estado["tela"] = "menu"
            estado["dados_pedido"] = {}
            return (
                "Sem problemas! 💜\n\n"
                "Quando precisar, tô aqui! É só dar um oi "
                "que eu apareço na hora. ✨\n\n" + mostrar_menu()
            )
        # Mudar algo
        if t in ("2",) or "mudar" in t:
            estado["tela"] = "mudar"
            return (
                "Claro! O que você quer mudar? ✏️\n\n"
                "[1] 📝 Mudar tema\n"
                "[2] 🎨 Mudar tipo\n"
                "[3] 📅 Mudar prazo\n"
                "[4] 👤 Mudar nomes\n"
                "[5] 📎 Mudar extras\n"
                "[0] 🔙 Voltar ao resumo"
            )
        estado["tela"] = "menu"
        return mostrar_menu()

    # Mudar algo
    if tela == "mudar":
        if t == "0":
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        if t == "1":
            estado["tela"] = "pedido_tema"
            estado["modo_edicao"] = True
            return "Qual o novo assunto do slide? 📝"
        if t == "2":
            estado["tela"] = "pedido_tipo"
            estado["modo_edicao"] = True
            return (
                "Qual o novo tipo de slide?\n\n"
                "[1] PDF | [2] Canva Transições | [3] PPT Transições\n"
                "[4] Canva Temas | [5] PPTX Temas\n"
            )
        if t == "3":
            estado["tela"] = "pedido_prazo"
            estado["modo_edicao"] = True
            return "Qual o novo prazo? 📅"
        if t == "4":
            estado["tela"] = "pedido_nomes"
            estado["modo_edicao"] = True
            return "Quais nomes você quer? (ou responda 'não')"
        if t == "5":
            estado["tela"] = "pedido_extras"
            estado["modo_edicao"] = True
            dados["extras"] = ""
            return "Mande suas observações. Quando terminar, responda 'finalizar'. 💜"
        estado["tela"] = "resumo"
        return _mostrar_resumo(dados)

    # PASSO 7: Pagamento
    if tela == "pagamento":
        estado["tela"] = "menu"
        estado["dados_pedido"] = {}
        return (
            "Recebi! 💜\n\n"
            "Seu comprovante vai ser olhado pela nossa equipe agora. "
            "Assim que confirmarmos o pagamento, já te aviso e "
            "começamos a produzir seu slide. ✨\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # ═══════════════════════════════════════════
    # FALLBACK: IA
    # ═══════════════════════════════════════════
    estado["tela"] = "menu"
    return _chamar_ia(mensagem, estado)


# ── FUNÇÕES AUXILIARES ──

def _msg_precos():
    return (
        "O valor depende do tipo de slide que você escolher. 💜\n\n"
        "📄 PDF — R$ 20,00\n"
        "🎬 Canva (Transições) — R$ 25,00\n"
        "🎬 PowerPoint (Transições) — R$ 35,00\n"
        "🎨 Slide Temas Canva — R$ 28,00\n"
        "🎨 Slide Temas PPTX — R$ 38,00\n\n"
        "💡 No nosso catálogo você consegue ver exemplos "
        "e explicações detalhadas de cada tipo:\n"
        "👉 https://slydesign.com.br/personalizados/\n\n"
        "[2] 🎨 Quero fazer meu pedido!\n"
        "[0] 🔙 Voltar ao menu"
    )


def _buscar_tema_handler(mensagem, estado):
    """Busca inteligente no catálogo."""
    # Tenta limpar a mensagem pra extrair só o nome do tema
    termos = mensagem
    for p in ["quero", "queria", "tem", "tema", "sobre", "faz", "vcs",
               "voces", "voce", "vc", "procurando", "procuro", "slide",
               "slides", "algum", "alguma", "dos", "das", "the"]:
        termos = " " + termos + " "
        termos = termos.replace(f" {p} ", " ")
        termos = termos.strip()

    melhor, todos = buscar_tema(termos) if termos else (None, [])
    if not melhor:
        melhor, todos = buscar_tema(mensagem)

    if melhor and len(todos) == 1:
        estado["tela"] = "menu"
        return (
            f"Temos esse tema disponível no catálogo "
            f"com entrega imediata. 💜\n\n"
            f"📄 {melhor['tema']}\n"
            f"👉 {melhor['link']}\n\n"
            f"É só comprar e receber na hora!\n\n"
            f"[2] 🎨 Quero um personalizado\n"
            f"[0] 🔙 Voltar ao menu"
        )
    elif melhor and len(todos) > 1:
        temas_lista = "\n".join(f"• {t['tema']} — {t['link']}" for t in todos[:5])
        return (
            f"Encontrei esses temas. Qual você procura? 💜\n\n"
            f"{temas_lista}\n\n"
            f"[0] 🔙 Voltar ao menu"
        )
    else:
        estado["tela"] = "pedido_tema"
        estado["dados_pedido"] = {}
        return (
            f"Não encontrei \"{mensagem}\" no nosso catálogo pronto.\n\n"
            f"Mas podemos criar um slide personalizado "
            f"exatamente como você precisa. 💜\n\n"
            f"[2] 🎨 Quero um slide personalizado\n"
            f"[7] 🆘 Falar com humano\n"
            f"[0] 🔙 Voltar ao menu"
        )


def _mostrar_resumo(dados):
    modelo = dados.get("modelo", "")
    modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
    preco = PRECOS.get(modelo_limpo, "a combinar")

    # Calcula 50%
    try:
        valor_str = preco.replace("R$ ", "").replace(",", ".")
        metade = float(valor_str) / 2
        metade_str = f"R$ {metade:.2f}".replace(".", ",")
    except (ValueError, AttributeError):
        metade_str = "a combinar"

    # Monta o resumo conforme o tipo
    if "Temas" in modelo:
        assunto = dados.get("assunto", dados.get("tema", ""))
        tema_design = dados.get("tema_design", "")
        linha_tema = f"📝 Assunto: {assunto}\n🎨 Tema: {modelo} — {tema_design}\n"
    else:
        linha_tema = f"📝 Tema: {dados.get('tema', '')}\n🎨 Tipo: {modelo}\n"

    # Aviso de páginas extras
    aviso_paginas = ""
    if dados.get("paginas_extra"):
        aviso_paginas = (
            "\n⚠️ Como você quer adicionar todo o conteúdo, "
            "o número final de páginas (e valor) será confirmado "
            "após a produção. Você paga os 50% do valor base agora "
            "e o restante no final, quando soubermos quantas páginas deu! 💜\n"
        )

    return (
        "Aqui está o resumo do seu pedido: 💜\n\n"
        f"{linha_tema}"
        f"📅 Prazo: {dados.get('prazo', '')}\n"
        f"👤 Nomes: {dados.get('nomes', 'Não')}\n"
        f"📎 Extras: {dados.get('extras', 'Nenhum')}\n\n"
        f"💰 Valor total: {preco}\n"
        f"💳 Agora (50%): {metade_str} — o restante na entrega! 💜\n"
        f"{aviso_paginas}\n"
        f"Tá tudo certo?\n"
        f"[1] ✅ Confirmar pedido\n"
        f"[2] ✏️ Quero mudar algo\n"
        f"[3] ❌ Cancelar"
    )


def _msg_pagamento(dados):
    modelo = dados.get("modelo", "")
    modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
    preco = PRECOS.get(modelo_limpo, "a combinar")

    # Calcula 50%
    try:
        valor_str = preco.replace("R$ ", "").replace(",", ".")
        metade = float(valor_str) / 2
        metade_str = f"R$ {metade:.2f}".replace(".", ",")
    except (ValueError, AttributeError):
        metade_str = "a combinar"

    return (
        "Perfeito! Pra finalizar, precisamos de 50% do valor. 💜\n\n"
        f"💰 Valor total: {preco}\n"
        f"💳 Agora (50%): {metade_str}\n\n"
        "📱 Chave Pix (telefone):\n"
        "38997507651\n"
        "Shayene Lopes Figueredo\n\n"
        "Assim que pagar, me manda o comprovante aqui. "
        "Um humano vai dar uma olhadinha e já confirmamos! ✅\n\n"
        "[0] 🔙 Voltar ao menu"
    )


def _chamar_ia(mensagem: str, estado: dict) -> str:
    """LLM como último recurso — mas antes tenta buscar tema no catálogo."""
    # Tenta achar tema na mensagem antes de gastar tokens com IA
    tema_encontrado, _ = buscar_tema(mensagem)
    if tema_encontrado:
        print(f"   🎯 Tema encontrado: {tema_encontrado['tema']}")
        return (
            f"Temos esse tema sim! 💜\n\n"
            f"📄 {tema_encontrado['tema']}\n"
            f"👉 {tema_encontrado['link']}\n\n"
            f"É só comprar e receber na hora!\n\n"
            f"[2] 🎨 Quero um personalizado\n"
            f"[0] 🔙 Voltar ao menu  |  [7] 🆘 Falar com humano"
        )

    print("   🤖 IA fallback...")
    try:
        from app.config import cliente, MODELO
        historico = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": mensagem},
        ]
        resposta = cliente.chat.completions.create(
            model=MODELO, messages=historico, temperature=0.7
        )
        return resposta.choices[0].message.content + "\n\n[2] 🎨 Quero um Slide Personalizado  |  [0] 🔙 Voltar ao menu  |  [7] 🆘 Falar com humano"
    except Exception as e:
        print(f"   ⚠️ Erro LLM: {e}")
        return (
            "Hmm, não consegui processar isso agora. 💜\n"
            "Me chama no WhatsApp: (34) 99930-6554\n\n"
            "[2] 🎨 Quero um Slide Personalizado  |  [0] 🔙 Voltar ao menu  |  [7] 🆘 Falar com humano"
        )


# ── ENDPOINTS ──

# Token de verificação do webhook (você define qualquer string no painel da Meta)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "slydesign2026")

@app.get("/webhook")
async def webhook_verify(request: Request):
    """Verificação do webhook da Meta (GET)."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado pela Meta!")
        return int(challenge) if challenge.isdigit() else challenge
    return {"status": "ok", "maya": "online 💜"}


@app.post("/webhook")
async def webhook_receive(request: Request):
    """Recebe mensagens do WhatsApp (POST)."""
    data = await request.json()

    # 🔍 Log do payload completo (só aparece no console do Render)
    import json as _json
    print(f"\n📨 WEBHOOK RECEBIDO: {_json.dumps(data, ensure_ascii=False)[:500]}")

    # Extrai mensagem do payload da Meta
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [{}])[0]
        texto = messages.get("text", {}).get("body", "")
        telefone = messages.get("from", "")
    except (IndexError, KeyError, AttributeError) as e:
        print(f"⚠️ Payload em formato inesperado: {e}")
        texto = data.get("body", "")
        telefone = data.get("from", "")

    if not texto:
        print(f"⚠️ Webhook ignorado — sem texto. Telefone: {telefone!r} | Chaves: {list(data.keys())}")
        return {"status": "ignored"}

    print(f"\n💬 {telefone}: {texto}")
    resposta = maya_responder(texto, telefone)

    if resposta is None:
        print(f"🤫 Maya silenciada (atendimento humano)")
        return {"status": "silenced"}

    print(f"🤖 Maya: {resposta[:100]}...")

    # Formata botões pra WhatsApp: [1] → *[ 1 ]*
    import re
    resposta = re.sub(r'\[(\d)\]', r'*[ \1 ]*', resposta)

    # 🔥 ENVIA a resposta de volta pro cliente via WhatsApp Cloud API
    enviar_whatsapp(telefone, resposta)

    return {"status": "sent"}


@app.get("/health")
async def health():
    return {"status": "ok", "maya": "online 💜"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("🤖 Maya — Atendente Sly Design 💜")
    print("   Webhook WhatsApp rodando em http://localhost:8000")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8000)

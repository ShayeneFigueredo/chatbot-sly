"""
Servidor Webhook — MAYA NO WHATSAPP 💜
Máquina de estados completa + NLP + LLM fallback.

Rode: .venv/bin/python backend/webhook_server.py
"""
import os
import sys
import json
import time
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv("backend/.env")

from app.nlp import detectar_intencao
from app.buscador import buscar_tema
from app.config import SYSTEM_PROMPT, PRECOS, TEMAS_DISPONIVEIS

app = FastAPI()

# ── Sistema de Login ──
USUARIO = "shayenelf"
SENHA = "135790"
sessoes = {}  # token -> timestamp


def verificar_login(request: Request) -> bool:
    """Verifica se a sessao e valida."""
    token = request.cookies.get("maya_token")
    if token and token in sessoes:
        # Sessao expira em 24h
        if time.time() - sessoes[token] < 86400:
            return True
        del sessoes[token]
    return False


def gerar_token() -> str:
    import secrets
    token = secrets.token_hex(16)
    sessoes[token] = time.time()
    return token


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, erro: str = ""):
    """Pagina de login (rota GET)."""
    return HTMLResponse(_html_login(request, erro))


def _html_login(request: Request, erro: str = ""):
    """Gera HTML da pagina de login (funcao interna, sem decorator)."""
    if verificar_login(request):
        return _pagina_portal()
    msg = '<p style="color:#f87171;text-align:center">Senha incorreta</p>' if erro else ""
    return f"""
    <html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Maya — Login</title>
    <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:#0a0a14;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif}}
    form{{background:#1a1a2e;padding:30px;border-radius:16px;border:1px solid #333;width:90%;max-width:340px}}
    h1{{color:#c084fc;text-align:center;margin-bottom:20px;font-size:1.3em}}
    input{{width:100%;background:#0a0a14;border:1px solid #333;color:#ddd;padding:12px;border-radius:8px;margin-bottom:10px;font-size:.9em}}
    button{{width:100%;background:#c084fc;color:#0a0a14;border:none;padding:12px;border-radius:8px;font-weight:bold;cursor:pointer;font-size:.9em}}
    button:hover{{background:#a855f7}}
    </style></head><body>
    <form method="post" action="/login">
    <h1>Maya — Sly Design</h1>
    {msg}
    <input name="usuario" placeholder="Usuario" required>
    <input name="senha" type="password" placeholder="Senha" required>
    <button type="submit">Entrar</button>
    </form></body></html>"""


@app.post("/login")
async def login_action(request: Request):
    """Processa o login."""
    form = await request.form()
    usuario = form.get("usuario", "")
    senha = form.get("senha", "")
    if usuario == USUARIO and senha == SENHA:
        token = gerar_token()
        resp = HTMLResponse(_pagina_portal())
        resp.set_cookie("maya_token", token, httponly=True, max_age=86400)
        return resp
    return HTMLResponse(_html_login(request, erro="1"))


def _pagina_portal():
    """Portal interno apos login — botoes para Painel e WhatsApp."""
    return """
    <html><head>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Maya — Portal</title>
    <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#0a0a14;display:flex;align-items:center;justify-content:center;min-height:100vh;font-family:'Segoe UI',sans-serif}
    .box{background:#1a1a2e;padding:30px;border-radius:16px;border:1px solid #333;width:90%;max-width:340px;text-align:center}
    h1{color:#c084fc;margin-bottom:25px}
    a{display:block;background:#2a2a4e;color:#c084fc;padding:14px;border-radius:10px;margin-bottom:10px;text-decoration:none;font-weight:bold;font-size:.95em}
    a:hover{background:#3a3a5e}
    a.wpp{background:#1a3a2a;color:#4ade80}
    a.wpp:hover{background:#2a4a3a}
    </style></head><body>
    <div class="box">
    <h1>Maya — Portal</h1>
    <a href="/painel">Painel de Gestao</a>
    <a href="/qrcode" class="wpp">WhatsApp QR Code</a>
    <a href="#" onclick="resetarWhatsApp()" style="background:#3a1a1a;color:#fca5a5">Resetar WhatsApp</a>
    <script>
    async function resetarWhatsApp(){
      if(!confirm('Isso vai desconectar o WhatsApp. Depois voce precisara escanear o QR Code de novo. Continuar?'))return;
      const r=await fetch('/qrcode/reset',{method:'POST'});
      const d=await r.json();
      alert(d.msg);if(d.status==='ok')location.href='/qrcode';
    }
    </script>
    </div></body></html>"""


# Middleware de protecao para /painel*, /qrcode e APIs internas
@app.middleware("http")
async def proteger_rotas(request: Request, call_next):
    path = request.url.path
    rotas_protegidas = ("/painel", "/qrcode")
    if any(path == r or path.startswith(r + "/") or path.startswith(r + "?") for r in rotas_protegidas):
        if not verificar_login(request):
            return HTMLResponse(_html_login(request))
    return await call_next(request)

# ── Configurações de notificação ──
SHAY_NUMERO = "+5538997507651"
META_TOKEN = os.getenv("META_TOKEN")
PHONE_NUMBER_ID = "1174471599080821"

# ── Clientes em atendimento humano (Maya não responde) ──
atendimento_humano = {}  # {telefone: True}

# Persistencia do estado dos clientes (sobrevive a reinicios)
import os as _os
# Salva no disco persistente do Render
ARQUIVO_ESTADO = "/app/auth_info_baileys/estado_clientes.json"

def _salvar_estado_clientes():
    """Salva o estado de todos os clientes em disco."""
    try:
        dados = {
            "clientes": clientes,
            "atendimento_humano": atendimento_humano,
        }
        with open(ARQUIVO_ESTADO, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar estado: {e}")

def _carregar_estado_clientes():
    """Carrega o estado dos clientes do disco (se existir)."""
    global clientes, atendimento_humano
    if _os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            clientes = dados.get("clientes", {})
            atendimento_humano = dados.get("atendimento_humano", {})
            print(f"📂 Estado restaurado: {len(clientes)} clientes")
        except Exception as e:
            print(f"⚠️ Erro ao carregar estado: {e}")

# Carrega estado salvo ao iniciar o servidor
_carregar_estado_clientes()


def notificar_shay(mensagem: str):
    """Envia uma notificacao WhatsApp pro numero pessoal da Shay via Baileys."""
    try:
        resp = requests.post(
            "http://127.0.0.1:8080/send",
            json={"to": SHAY_NUMERO, "text": mensagem},
            timeout=10,
        )
        print(f"📤 Notificacao Shay: {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Erro ao notificar Shay (ponte interna): {e}")


def cliente_em_atendimento_humano(telefone: str) -> bool:
    """Verifica se o cliente está sendo atendido por um humano."""
    return atendimento_humano.get(telefone, False)

# ── Estado dos clientes ──
clientes = {}


def mostrar_menu():
    return (
        "Oieee! Eu sou a Maya, atendente virtual da Sly Design! 💜\n\n"
        "Aqui a gente tem slides prontos super legais "
        "e também criamos do zero, do seu jeitinho. ✨\n\n"
        "Temos MUITA coisa legal no site e com super descontos! 💜\n"
        "Dá uma olhadinha:\n\n"
        "👉 https://slydesign.com.br\n\n"
        "No que posso te ajudar?\n\n"
        "[1] 🛍️ Ver Slides Prontos\n"
        "[2] 🎨 Quero um Slide Personalizado\n"
        "[3] 🔍 Consultar um Tema\n"
        "[4] 💰 Quanto Custa?\n"
        "[5] 💬 Tirar uma Dúvida\n\n"
        "💡 Você pode digitar o número ou escrever sua pergunta!"
    )


def maya_responder(mensagem: str, telefone: str, tipo_msg: str = "texto") -> str:
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
        clientes[telefone] = {"tela": "menu", "dados_pedido": {}, "historico_ia": []}
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
                "👉 https://slydesign.com.br\n\n"
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
                "👉 https://slydesign.com.br\n\n"
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
        # Cliente mandou foto em vez de digitar o assunto?
        if tipo_msg == "imagem":
            dados["tem_imagem"] = True
            if mensagem.strip():
                # Tem legenda na foto → usa como tema
                dados["tema"] = mensagem.strip()
                estado["tela"] = "pedido_tipo"
                return (
                    "Vi a imagem e a legenda! 📸\n\n"
                    f"Entendi que o assunto é \"{mensagem.strip()}\".\n\n"
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
            # Imagem sem legenda → pede pra digitar
            return (
                "Vi que você mandou uma imagem! 📸\n\n"
                "Mas eu ainda não consigo ler o que está escrito nela..."
                "Preciso que você DIGITE qual é o assunto do slide, ok?\n\n"
                "📝 Qual o ASSUNTO do slide?\n\n"
                "[0] 🔙 Voltar ao menu"
            )

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
            estado["tela"] = "pedido_tipo_diferenca"
            return (
                "Visualmente sao iguais! 🎨\n\n"
                "📱 Canva — e um link online. Precisa de internet "
                "pra apresentar, mas nao ocupa espaco no celular/PC.\n\n"
                "💻 PowerPoint — e um arquivo PPTX que voce baixa. "
                "Nao precisa de internet pra apresentar.\n\n"
                "Qual tipo voce prefere?\n\n"
                "[1] 🎬 Canva (Transicoes) — R$ 25,00\n"
                "[2] 🎬 PowerPoint (Transicoes) — R$ 35,00\n"
                "[3] 🎨 Canva Temas — R$ 28,00\n"
                "[4] 🎨 PPTX Temas — R$ 38,00\n"
                "[5] 📄 PDF — R$ 20,00\n"
                "[0] 🔙 Voltar ao menu"
            )

        # Mapeia numeros normais
        if t in tipos:
            dados["modelo"] = tipos[t]
        elif t in tipos.values():
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
            dados["assunto"] = dados.get("tema", "")
            estado["tela"] = "pedido_qual_tema"
            if modo_edicao:
                estado["modo_edicao"] = True
            top5 = ", ".join(TEMAS_DISPONIVEIS[:5])
            return (
                "Legal! Temos varios temas prontos. 💜\n\n"
                f"Os mais pedidos: {top5}...\n\n"
                "E tem mais no site:\n"
                "👉 https://slydesign.com.br\n\n"
                "Se quiser um tema que nao esta na lista, "
                "podemos criar do zero. Me diga qual tema voce quer?\n\n"
                "[8] 🎨 Quero o design sobre o MEU assunto\n"
                "[0] 🔙 Voltar ao menu"
            )

        if modo_edicao:
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)

        estado["tela"] = "pedido_prazo"
        return (
            "Anotado! ✅\n\n"
            "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
            "💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
            "da sua apresentacao.\n\n"
            "Me conta: qual data voce precisa? 📅\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2b: Tipo apos ver diferenca (numeros diferentes!)
    if tela == "pedido_tipo_diferenca":
        diff_map = {
            "1": "🎬 Canva (Transições)", "2": "🎬 PowerPoint (Transições)",
            "3": "🎨 Canva Temas", "4": "🎨 PPTX Temas", "5": "📄 PDF"
        }

        if t in diff_map:
            dados["modelo"] = diff_map[t]
        elif t in diff_map.values():
            dados["modelo"] = t
        elif t in ("canva", "📱 canva", "📱"):
            dados["modelo"] = "🎬 Canva (Transições)"
        elif t in ("powerpoint", "ppt", "💻", "pptx", "💻 powerpoint"):
            dados["modelo"] = "🎬 PowerPoint (Transições)"
        elif t in ("pdf", "📄 pdf", "📄"):
            dados["modelo"] = "📄 PDF"
        else:
            dados["modelo"] = mensagem

        modo_edicao = estado.pop("modo_edicao", False)

        if "Temas" in dados.get("modelo", ""):
            dados["assunto"] = dados.get("tema", "")
            estado["tela"] = "pedido_qual_tema"
            if modo_edicao:
                estado["modo_edicao"] = True
            top5 = ", ".join(TEMAS_DISPONIVEIS[:5])
            return (
                "Legal! Temos varios temas prontos. 💜\n\n"
                f"Os mais pedidos: {top5}...\n\n"
                "E tem mais no site:\n"
                "👉 https://slydesign.com.br\n\n"
                "Se quiser um tema que nao esta na lista, "
                "podemos criar do zero. Me diga qual tema voce quer?\n\n"
                "[8] 🎨 Quero o design sobre o MEU assunto\n"
                "[0] 🔙 Voltar ao menu"
            )

        if modo_edicao:
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)

        estado["tela"] = "pedido_prazo"
        return (
            "Anotado! ✅\n\n"
            "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
            "💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
            "da sua apresentacao.\n\n"
            "Me conta: qual data voce precisa? 📅\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2.5: Qual tema? (slides temas)
    if tela == "pedido_qual_tema":
        # Cliente quer o design sobre o proprio assunto, nao um tema pronto
        if t == "8" or "design sobre" in t or "meu assunto" in t:
            # Troca de "Temas" para "Transicoes" mantendo Canva ou PPTX
            modelo_atual = dados.get("modelo", "")
            if "PPTX" in modelo_atual or "PowerPoint" in modelo_atual:
                dados["modelo"] = "🎬 PowerPoint (Transições)"
            else:
                dados["modelo"] = "🎬 Canva (Transições)"
            # Remove o tema_design e o assunto extra (vai usar o tema original)
            dados.pop("tema_design", None)
            dados.pop("assunto", None)
            estado["tela"] = "pedido_prazo"
            return (
                "Certo! Vamos criar o design com base no SEU assunto. 🎨\n\n"
                "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
                "Me conta: qual data voce precisa? 📅\n\n"
                "[0] 🔙 Voltar ao menu"
            )

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
        if any(p in t for p in ["hoje", "hj", "mesmo dia", "ainda hoje", "ate 00", "ate as", "ate meia"]):
            dados["taxa_urgencia"] = True
            msg = (
                "⚠️ Como e para hoje, temos uma taxa adicional de R$ 5,00 "
                "e preciso verificar se ainda ha vaga na agenda. "
                "Vou confirmar com a equipe, um momento!\n\n"
            )
        else:
            dados.pop("taxa_urgencia", None)  # remove taxa se mudou pra outro dia
            msg = ""
        if estado.pop("modo_edicao", False):
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado["tela"] = "pedido_nomes"
        return (
            f"{msg}"
            f"Anotei o prazo! 📅\n\n"
            f"Quer adicionar os NOMES de voces no slide?\n"
            f"Se sim, mande todos os nomes em uma unica mensagem.\n"
            f"Se nao, e so responder 'nao'. 💜\n\n"
            f"[0] 🔙 Voltar ao menu"
        )

    # PASSO 4: Nomes
    if tela == "pedido_nomes":
        if t in ("não", "nao", "n", "não quero", "nao quero", "🚫 não quero"):
            dados["nomes"] = "Não"
        else:
            # Limpa frase tipo "quero, vai ser joão e maria" → "joão e maria"
            nomes_limpo = mensagem
            for p in ["quero", "vai ser", "vai ser:", "quero,", "quero:"]:
                nomes_limpo = nomes_limpo.replace(p, "")
            dados["nomes"] = nomes_limpo.strip().strip(",").strip() or mensagem
        if estado.pop("modo_edicao", False):
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado["tela"] = "pedido_extras"
        dados["extras"] = ""
        return (
            "Quer adicionar alguma informacao extra? 💜\n"
            "Ex: resumo, topicos, referencias, como quer o design...\n"
            "(a pesquisa do conteudo e por nossa conta! 🔍)\n\n"
            "⚠️ Alteracoes pos-entrega: R$ 1,50/pagina editada.\n"
            "📄 Limite: 10 pags. Extra: +R$ 1,50/pag.\n\n"
            "Se o conteudo for muito grande:\n"
            "[1] 📝 Resumir em 10 paginas\n"
            "[2] ➕ Adicionar tudo (te aviso quantas deu)\n\n"
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
            estado["tela"] = "aguardando_pagamento"
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

    # PASSO 7: Aguardando pagamento (Maya NAO responde)
    if tela == "aguardando_pagamento":
        # Cliente manda comprovante, "ok", "paguei", etc
        # Maya fica quieta — um humano (Shay) assume
        if t in ("menu", "voltar", "🔙 voltar ao menu", "0"):
            estado["tela"] = "menu"
            estado["dados_pedido"] = {}
            return mostrar_menu()
        # Qualquer outra coisa → Maya nao responde
        print(f"🤫 Maya silenciada para {telefone} (aguardando pagamento)")
        return None

    # ═══════════════════════════════════════════
    # FALLBACK: IA
    # ═══════════════════════════════════════════
    estado["tela"] = "menu"
    return _chamar_ia(mensagem, estado)


# ── FUNÇÕES AUXILIARES ──

def _msg_precos():
    return (
        "O valor depende do tipo de slide que voce escolher. 💜\n\n"
        "📄 PDF — R$ 20,00\n"
        "🎬 Canva (Transicoes) — R$ 25,00\n"
        "🎬 PowerPoint (Transicoes) — R$ 35,00\n"
        "🎨 Slide Temas Canva — R$ 28,00\n"
        "🎨 Slide Temas PPTX — R$ 38,00\n\n"
        "💡 No nosso site voce consegue ver exemplos "
        "e explicacoes detalhadas de cada tipo:\n"
        "👉 https://slydesign.com.br/personalizados/\n\n"
        "🛍️ Tambem temos varios slides e modelos JA PRONTOS "
        "com entrega imediata no site:\n"
        "👉 https://slydesign.com.br\n\n"
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
            f"Poderia ser mais especifico na sua pergunta? 💜\n\n"
            f"Se quiser, posso chamar um de nossos atendentes "
            f"para conversar melhor com voce.\n\n"
            f"[2] 🎨 Quero um slide personalizado\n"
            f"[7] 🆘 Falar com humano\n"
            f"[0] 🔙 Voltar ao menu"
        )


def _mostrar_resumo(dados):
    modelo = dados.get("modelo", "")
    modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
    preco_base = PRECOS.get(modelo_limpo, "a combinar")

    # Adiciona taxa de urgencia se for pra hoje
    taxa_urgencia = dados.get("taxa_urgencia", False)
    preco = preco_base
    if taxa_urgencia:
        try:
            valor_str = preco_base.replace("R$ ", "").replace(",", ".")
            total = float(valor_str) + 5
            preco = f"R$ {total:.2f}".replace(".", ",")
        except (ValueError, AttributeError):
            pass

    # Calcula 50%
    try:
        valor_str = preco.replace("R$ ", "").replace(",", ".")
        metade = float(valor_str) / 2
        metade_str = f"R$ {metade:.2f}".replace(".", ",")
    except (ValueError, AttributeError):
        metade_str = "a combinar"

    # Monta o resumo conforme o tipo
    img_tag = " (imagem anexada)" if dados.get("tem_imagem") else ""
    if "Temas" in modelo:
        assunto = dados.get("assunto", dados.get("tema", ""))
        tema_design = dados.get("tema_design", "")
        linha_tema = f"📝 Assunto: {assunto}{img_tag}\n🎨 Tema: {modelo} — {tema_design}\n"
    else:
        linha_tema = f"📝 Tema: {dados.get('tema', '')}{img_tag}\n🎨 Tipo: {modelo}\n"

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
        f"📎 Extras: {_truncar_extras(dados.get('extras', 'Nenhum'))}\n\n"
        f"💰 Valor total: {preco}"
        f"{' (com taxa de urgencia R$ 5,00)' if taxa_urgencia else ''}\n"
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
    preco_base = PRECOS.get(modelo_limpo, "a combinar")
    taxa_urgencia = dados.get("taxa_urgencia", False)
    preco = preco_base
    if taxa_urgencia:
        try:
            valor_str = preco_base.replace("R$ ", "").replace(",", ".")
            total = float(valor_str) + 5
            preco = f"R$ {total:.2f}".replace(".", ",")
        except (ValueError, AttributeError):
            pass

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


def _truncar_extras(texto: str) -> str:
    """Limita extras a 50 caracteres no resumo pra nao poluir a tela."""
    if not texto or texto == "Nenhum":
        return texto or "Nenhum"
    if len(texto) > 50:
        return texto[:50] + "..."
    return texto


def _salvar_historico(estado: dict, papel: str, texto: str):
    """Guarda mensagem no historico da conversa (max 50, remove >7 dias)."""
    agora = time.time()
    hist = estado.setdefault("historico_ia", [])

    # Limpa mensagens com mais de 7 dias
    sete_dias = 7 * 24 * 3600
    hist[:] = [h for h in hist if agora - h.get("t", 0) < sete_dias]

    # Adiciona a nova
    hist.append({"role": papel, "content": texto[:2000], "t": agora})

    # Mantem so as ultimas 50
    if len(hist) > 50:
        hist[:] = hist[-50:]


def _chamar_ia(mensagem: str, estado: dict) -> str:
    """LLM com contexto completo da conversa (sem buscar catalogo antes)."""
    print("   🤖 IA fallback...")
    try:
        from app.config import cliente, MODELO

        # Monta historico com contexto completo
        hist = estado.get("historico_ia", [])
        mensagens_ia = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Adiciona Historico da conversa (sem o campo "t")
        for h in hist:
            mensagens_ia.append({"role": h["role"], "content": h["content"]})

        # Adiciona a mensagem atual
        mensagens_ia.append({"role": "user", "content": mensagem})

        print(f"   📚 Contexto IA: {len(mensagens_ia)} mensagens")
        resposta = cliente.chat.completions.create(
            model=MODELO, messages=mensagens_ia, temperature=0.7
        )
        texto = resposta.choices[0].message.content
        return texto + "\n\n[2] 🎨 Quero um Slide Personalizado  |  [0] 🔙 Voltar ao menu  |  [7] 🆘 Falar com humano"
    except Exception as e:
        print(f"   ⚠️ Erro LLM: {e}")
        return (
            "Hmm, não consegui processar isso agora. 💜\n"
            "Me chama no WhatsApp: (34) 99930-6554\n\n"
            "[2] 🎨 Quero um Slide Personalizado  |  [0] 🔙 Voltar ao menu  |  [7] 🆘 Falar com humano"
        )


# ── ENDPOINTS ──

@app.get("/webhook")
async def health():
    return {"status": "ok", "maya": "online 💜"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "maya": "online 💜"}


@app.post("/qrcode/reset")
async def qrcode_reset(request: Request):
    """Reseta a sessao do WhatsApp (apaga auth e força novo QR Code).
    NAO apaga o estado dos clientes (estado_clientes.json)."""
    import glob as _glob
    auth_dir = "/app/auth_info_baileys"
    try:
        # Apaga apenas arquivos de sessao do Baileys, preservando estado_clientes.json
        for f in _glob.glob(f"{auth_dir}/*"):
            if "estado_clientes" not in f:
                if _os.path.isdir(f):
                    import shutil
                    shutil.rmtree(f, ignore_errors=True)
                else:
                    _os.remove(f)
        print("🔁 Sessao WhatsApp resetada — novo QR Code necessario")
        return {"status": "ok", "msg": "Sessao resetada. Recarregue a pagina /qrcode"}
    except Exception as e:
        return {"status": "erro", "msg": str(e)}


@app.get("/qrcode", response_class=HTMLResponse)
async def qrcode():
    """Pagina com QR Code pra escanear no celular."""
    try:
        conteudo = open("/tmp/qrcode.html", "r").read()
        # Adiciona link clicavel pra abrir no WhatsApp (celular)
        link_match = None
        import re as _re
        match = _re.search(r'https://wa\.me/settings/linked_devices[^"\s<]+', conteudo)
        if match:
            link_match = match.group(0)
        if link_match:
            conteudo = conteudo.replace("</body>",
                f'<p style="text-align:center;margin-top:20px">'
                f'📱 <a href="{link_match}" style="color:#c084fc;font-size:1.1em">'
                f'Abrir no WhatsApp (se nao conseguir escanear)</a></p></body>')
        return conteudo
    except FileNotFoundError:
        return """
        <html><head>
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <style>body{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:Montserrat,sans-serif}
        h2{color:#e0aaff;margin-bottom:20px}
        button{background:#3a1a1a;color:#fca5a5;border:1px solid #7f1d1d;padding:12px 24px;border-radius:8px;cursor:pointer;font-size:.9em}
        button:hover{background:#5a2a2a}
        </style></head><body>
        <h2>Maya ja esta conectada! 💜</h2>
        <button onclick="resetar()">Resetar WhatsApp</button>
        <script>
        async function resetar(){
          if(!confirm('Resetar sessao WhatsApp? Precisara escanear o QR Code novamente.'))return;
          await fetch('/qrcode/reset',{method:'POST'});
          location.reload();
        }
        </script>
        </body></html>"""


@app.post("/responder")
async def responder(request: Request):
    data = await request.json()
    texto = data.get("body", "")
    telefone = data.get("from", "")
    tipo = data.get("tipo", "texto")

    print(f"\n💬 {telefone}: {texto}")
    resposta = maya_responder(texto, telefone, tipo)

    # Salva no historico da IA (pra ter contexto em conversas futuras)
    if telefone in clientes and resposta:
        estado = clientes[telefone]
        _salvar_historico(estado, "user", texto)
        _salvar_historico(estado, "assistant", resposta)

    if resposta is None:
        print(f"🤫 Maya silenciada (atendimento humano)")
        _salvar_estado_clientes()
        return {"resposta": None}

    print(f"🤖 Maya: {resposta[:100]}...")

    # Formata botões pra WhatsApp: [1] → *[ 1 ]*
    import re
    resposta = re.sub(r'\[(\d)\]', r'*[ \1 ]*', resposta)

    _salvar_estado_clientes()
    return {"resposta": resposta}


@app.post("/historico")
async def salvar_historico(request: Request):
    """Recebe mensagens da Shay pra salvar no historico do cliente."""
    data = await request.json()
    telefone = data.get("telefone", "")
    papel = data.get("papel", "assistant")
    texto = data.get("texto", "")
    if telefone and texto:
        estado = clientes.setdefault(telefone, {"tela": "menu", "dados_pedido": {}, "historico_ia": []})
        _salvar_historico(estado, papel, texto)
        # Marca o cliente como "shay_respondeu" pra aparecer no painel
        if papel == "assistant" and "[Shay]:" in texto:
            estado["shay_respondeu"] = True
        print(f"📝 Historico salvo: {papel} → {telefone}")
        return {"status": "ok"}
    return {"status": "ignored"}


@app.get("/painel", response_class=HTMLResponse)
async def painel():
    """Painel de gestao profissional (HTML do frontend/)."""
    try:
        with open("frontend/painel.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Painel nao encontrado</h1>"


# ── API do Painel (endpoints JSON) ──

@app.get("/painel/dados")
async def painel_dados():
    """Retorna JSON com todos os clientes ativos."""
    cli_list = []
    aguardando = 0
    for tel, est in clientes.items():
        tela = est.get("tela", "?")
        dados = est.get("dados_pedido", {})
        shay_msg = est.get("shay_respondeu", False)
        is_humano = atendimento_humano.get(tel, False)

        # Mostrar se: tem pedido, ou ta bloqueado, ou Shay mandou msg
        tem_atividade = (tela != "menu" or dados or is_humano or shay_msg)
        if not tem_atividade:
            continue

        if tela == "aguardando_pagamento":
            aguardando += 1

        modelo = dados.get("modelo", "")
        modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
        preco_base = PRECOS.get(modelo_limpo, "-")

        is_aguardando = tela == "aguardando_pagamento"

        # Determina status visual
        if is_humano:
            status_cls = "status-humano"
            status_txt = "Bloqueado"
        elif is_aguardando:
            status_cls = "status-pagamento"
            status_txt = "Aguardando pagamento"
        elif shay_msg:
            status_cls = "status-shay"
            status_txt = "Shay respondeu"
        else:
            status_cls = "status-ativo"
            status_txt = "Ativo"

        cli_list.append({
            "telefone": tel,
            "tela": tela,
            "tema": dados.get("tema", dados.get("assunto", "-")),
            "modelo": modelo,
            "prazo": dados.get("prazo", "-"),
            "nomes": dados.get("nomes", "-"),
            "valor": preco_base,
            "humano": is_humano,
            "aguardando": is_aguardando,
            "shay_msg": shay_msg,
            "statusCls": status_cls,
            "statusTxt": status_txt,
        })

    return {"clientes": cli_list, "total": len(cli_list), "aguardando": aguardando}


@app.post("/painel/bloquear")
async def painel_bloquear(request: Request):
    """Bloqueia Maya para um numero (atendimento humano)."""
    data = await request.json()
    tel = data.get("telefone", "")
    if tel:
        atendimento_humano[tel] = True
        _salvar_estado_clientes()
        print(f"🙋 Painel: Maya bloqueada para {tel}")
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/liberar")
async def painel_liberar(request: Request):
    """Libera Maya para um numero."""
    data = await request.json()
    tel = data.get("telefone", "")
    if tel:
        atendimento_humano.pop(tel, None)
        _salvar_estado_clientes()
        print(f"🤖 Painel: Maya liberada para {tel}")
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/rejeitar")
async def painel_rejeitar(request: Request):
    """Rejeita pedido (ex: sem vaga hoje) e notifica cliente."""
    data = await request.json()
    tel = data.get("telefone", "")
    motivo = data.get("motivo", "sem disponibilidade")
    if tel and tel in clientes:
        est = clientes[tel]
        est["tela"] = "menu"
        est["dados_pedido"] = {}
        _salvar_estado_clientes()

        # Notifica o cliente
        msg = (
            f"Infelizmente nao temos mais vagas para hoje... 😕\n\n"
            f"Mas podemos entregar amanha sem a taxa de urgencia! "
            f"Se preferir, faremos a devolucao do Pix agora mesmo.\n\n"
            f"Me diga como prefere? 💜\n\n"
            f"[0] 🔙 Voltar ao menu"
        )
        # Envia via ponte interna
        try:
            import requests as req
            req.post("http://127.0.0.1:8080/send",
                     json={"to": tel, "text": msg}, timeout=5)
        except Exception:
            pass

        print(f"❌ Painel: pedido de {tel} rejeitado ({motivo})")
        return {"status": "ok"}
    return {"status": "erro"}


# ── Webhook do Site (Yampi) ──

@app.post("/webhook/site")
async def webhook_site(request: Request):
    """Recebe eventos do site (Yampi) e processa conforme o tipo.

    Eventos suportados:
    - order.created / order.approved / order.paid: adiciona pedido
    - order.payment_denied: ignora
    - cart.abandoned / notification.cart_abandoned: ignora
    - outros: ignora (nao sabemos o que e)
    """
    try:
        data = await request.json()
        print(f"📨 Webhook Yampi: {json.dumps(data, ensure_ascii=False)[:300]}")

        # Detecta o tipo de evento (Yampi usa 'event' ou 'type')
        evento = str(data.get("event", data.get("type", ""))).lower()
        if not evento:
            # Tenta achar em outros campos comuns
            evento = str(data.get("hook", {}).get("event", "")).lower()

        # Eventos que devem ser IGNORADOS
        ignorar = ["abandoned", "abandonado", "cart.", "denied", "negado",
                    "recusado", "created", "updated", "criado", "atualizado",
                    "nota fiscal", "cashback", "produto", "cliente",
                    "endereco", "estoque"]
        if any(p in evento for p in ignorar):
            print(f"🛒 Evento Yampi ignorado: {evento}")
            return {"status": "ignored", "evento": evento}

        # So processa pedidos PAGOS/APROVADOS
        if not any(p in evento for p in ["approved", "aprovado", "paid", "pago"]):
            print(f"🛒 Evento Yampi nao processado: {evento}")
            return {"status": "skipped", "evento": evento}

        # Extrai dados do pedido (Yampi pode mandar em varios formatos)
        order = data.get("order", data.get("data", data))
        nome = order.get("customer", {}).get("name", order.get("nome", ""))
        items = order.get("items", order.get("products", []))
        produto = items[0].get("name", items[0].get("title", "")) if items else order.get("produto", "")
        valor = float(order.get("total", order.get("valor", order.get("amount", 0))))

        # So adiciona se tiver valor real
        if valor <= 0:
            print(f"⚠️ Pedido site com valor R$0 ignorado: {nome} — {produto}")
            return {"status": "ignored", "motivo": "valor zerado"}

        from backend.pedidos import adicionar
        from datetime import datetime

        mes = datetime.now().month
        adicionar({
            "cliente": nome or "Site",
            "arquivo": produto or "Slide",
            "tema": f"Site — {produto or 'Slide'}",
            "valor": f"R$ {valor:.2f}".replace(".", ","),
            "situacao": "Pago (Site)",
            "pg": "Pago",
            "responsavel": "SF",
            "origem": "site",
            "mes": mes,
            "data": datetime.now().strftime("%d/%m"),
        })
        # Atualiza faturamento do site no mes atual
        from backend.pedidos import _carregar, _salvar
        db = _carregar()
        atual = float(db.get("faturamento_site", {}).get(str(mes), 0))
        db.setdefault("faturamento_site", {})[str(mes)] = round(atual + valor, 2)
        _salvar(db)
        print(f"🛒 Pedido site adicionado: {nome} — {produto} — R$ {valor}")
        return {"status": "ok"}
    except Exception as e:
        print(f"⚠️ Erro webhook site: {e}")
        return {"status": "erro", "msg": str(e)}


# ── Taxas ──

@app.get("/taxas")
async def taxas():
    """Retorna informacoes sobre taxas do site."""
    return {
        "yampi": "2.5% por transacao",
        "mercado_pago": "~0.87% (ex: R$ 14,99 -> R$ 14,86)",
        "exemplo": {
            "valor_venda": "R$ 14,99",
            "taxa_yampi": "R$ 0,37",
            "taxa_mercado_pago": "R$ 0,13",
            "liquido": "R$ 14,49",
        }
    }


# ── API de Pedidos e Faturamento ──

@app.get("/painel/mes/{mes}")
async def painel_mes(mes: int):
    """Retorna pedidos e faturamento de um mes (ordenado por data de entrega)."""
    from backend.pedidos import listar_por_mes, faturamento
    pedidos = listar_por_mes(mes)
    # Ordena por data de entrega (dd/mm)
    def _ordenar_data(p):
        try:
            partes = p.get("entrega", p.get("data", "99/99")).split("/")
            return (int(partes[0]), int(partes[1]))
        except:
            return (99, 99)
    pedidos.sort(key=_ordenar_data)
    fat = faturamento()
    return {
        "pedidos": pedidos,
        "faturamento": fat["mensal"].get(mes, {"pedidos": 0, "site": 0, "total": 0})
    }


@app.get("/painel/hoje")
async def painel_hoje():
    """Retorna pedidos com entrega para hoje."""
    from backend.pedidos import _carregar
    from datetime import datetime
    hoje = datetime.now().strftime("%d/%m")
    db = _carregar()
    pedidos_hoje = [p for p in db["pedidos"] if p.get("entrega", p.get("data", "")) == hoje]
    return {"pedidos": pedidos_hoje, "data": hoje}


@app.get("/painel/faturamento")
async def painel_faturamento():
    """Retorna faturamento completo do ano."""
    from backend.pedidos import faturamento
    return faturamento()


@app.post("/painel/adicionar-manual")
async def painel_adicionar_manual(request: Request):
    """Adiciona pedido manual (Instagram, telefone, etc)."""
    from backend.pedidos import adicionar
    data = await request.json()
    adicionar(data)
    return {"status": "ok"}


@app.post("/painel/editar-pedido")
async def painel_editar_pedido(request: Request):
    """Edita campos de um pedido."""
    from backend.pedidos import _carregar, _salvar
    data = await request.json()
    pid = data.get("id")
    db = _carregar()
    for p in db["pedidos"]:
        if p["id"] == pid:
            for campo in ["situacao", "pg", "valor", "tema", "cliente", "responsavel"]:
                if campo in data and data[campo]:
                    p[campo] = data[campo]
            break
    _salvar(db)
    return {"status": "ok"}


@app.post("/painel/cutucar")
async def painel_cutucar(request: Request):
    """Cutuca cliente que parou de responder."""
    data = await request.json()
    tel = data.get("telefone", "")
    if tel:
        msg = (
            "Oie! Quer continuar o seu pedido? 💜\n"
            "Se preferir, posso chamar um de nossos atendentes "
            "para continuar a conversa com voce."
        )
        try:
            import requests as _req
            _req.post("http://127.0.0.1:8080/send",
                     json={"to": tel, "text": msg}, timeout=5)
            print(f" Cutucando {tel}")
        except Exception:
            pass
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/finalizar")
async def painel_finalizar(request: Request):
    """Finaliza atendimento de um cliente manualmente."""
    data = await request.json()
    tel = data.get("telefone", "")
    if tel and tel in clientes:
        clientes[tel]["tela"] = "menu"
        clientes[tel]["dados_pedido"] = {}
        atendimento_humano.pop(tel, None)
        _salvar_estado_clientes()
        print(f" Atendimento finalizado: {tel}")
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/deletar-pedido")
async def painel_deletar_pedido(request: Request):
    """Remove um pedido."""
    from backend.pedidos import _carregar, _salvar
    data = await request.json()
    pid = data.get("id")
    db = _carregar()
    db["pedidos"] = [p for p in db["pedidos"] if p["id"] != pid]
    _salvar(db)
    return {"status": "ok"}


@app.post("/painel/confirmar")
async def painel_confirmar(request: Request):
    """Confirma pedido e adiciona ao banco."""
    from backend.pedidos import adicionar
    data = await request.json()
    tel = data.get("telefone", "")
    if tel and tel in clientes:
        est = clientes[tel]
        dados = est.get("dados_pedido", {})
        modelo = dados.get("modelo", "")
        modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
        preco_base = PRECOS.get(modelo_limpo, "")
        if dados.get("taxa_urgencia"):
            try:
                total = float(preco_base.replace("R$ ", "").replace(",", ".")) + 5
                preco_base = f"R$ {total:.2f}".replace(".", ",")
            except (ValueError, AttributeError):
                pass
        adicionar({
            "cliente": tel,
            "arquivo": dados.get("modelo", ""),
            "tema": dados.get("tema", dados.get("assunto", "")),
            "valor": preco_base,
            "situacao": "Novo",
            "pg": "50% pago",
            "responsavel": "SF",
            "origem": "whatsapp",
        })
        est["tela"] = "menu"
        est["dados_pedido"] = {}
        _salvar_estado_clientes()
        # Envia mensagem final ao cliente
        msg_final = (
            "Pagamento confirmado! 💜\n\n"
            "Seu pedido ja esta em producao. Assim que estiver pronto, "
            "um de nossos atendentes entrara em contato por aqui "
            "com uma pre-visualizacao de como ficou. ✨\n\n"
            "Apos a aprovacao e o pagamento do valor restante, "
            "liberamos o arquivo final pra voce!\n\n"
            "Qualquer duvida e so chamar! 💜"
        )
        try:
            import requests as _req
            _req.post("http://127.0.0.1:8080/send",
                     json={"to": tel, "text": msg_final}, timeout=5)
        except Exception:
            pass
        print(f"✅ Pedido de {tel} confirmado e salvo")
        return {"status": "ok"}
    return {"status": "erro"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("🤖 Maya — Atendente Sly Design 💜")
    print("   Webhook WhatsApp rodando em http://localhost:8000")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8000)

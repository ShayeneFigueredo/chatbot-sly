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


def _encontrar_chave_cliente(telefone: str) -> str:
    """Encontra a chave real do cliente no dicionario (pode ter @lid ou @s.whatsapp.net)."""
    if telefone in clientes:
        return telefone
    for key in clientes:
        if key.startswith(telefone):
            return key
    return telefone  # nao encontrado, retorna o original


def cliente_em_atendimento_humano(telefone: str) -> bool:
    """Verifica se o cliente está sendo atendido por um humano."""
    return atendimento_humano.get(telefone, False) or atendimento_humano.get(_encontrar_chave_cliente(telefone), False)

# ── Estado dos clientes ──
clientes = {}


def mostrar_menu():
    return (
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

    # Inicializa (precisa vir antes dos checks de estado)
    novo_cliente = telefone not in clientes
    if novo_cliente:
        clientes[telefone] = {"tela": "aguardando_primeira_msg", "dados_pedido": {}, "historico_ia": [],
                              "mensagens_pendentes": [], "primeira_msg_ts": time.time()}
    estado = clientes[telefone]
    tela = estado["tela"]
    dados = estado["dados_pedido"]

    print(f"   📍 Tela: {tela} | {'🆕' if novo_cliente else ''} | 💬 {t[:80]}")

    # ── AGUARDANDO PRIMEIRAS MENSAGENS (delay 10s pra evitar respostas precipitadas) ──
    if tela == "aguardando_primeira_msg":
        estado.setdefault("mensagens_pendentes", []).append(mensagem)
        agora = time.time()
        # Processa depois de 10s OU se já tem 2+ mensagens (cliente mandou várias de uma vez)
        if agora - estado.get("primeira_msg_ts", agora) >= 10 or len(estado["mensagens_pendentes"]) >= 2:
            return _processar_primeiras_mensagens(estado, telefone)
        # Ainda dentro da janela de espera → não responde
        print(f"⏳ Aguardando mais mensagens de {telefone}... "
              f"({len(estado['mensagens_pendentes'])} msgs, "
              f"{agora - estado.get('primeira_msg_ts', agora):.0f}s)")
        _salvar_estado_clientes()
        return None

    # ── Cliente em aguardando_humano? Maya TRAVADA até destravar ──
    if tela == "aguardando_humano":
        # Bloqueio permanente (pós-confirmação) → nunca destrava
        if estado.get("bloqueio_permanente"):
            print(f"🔒 Maya permanentemente bloqueada para {telefone}")
            return None
        # Cliente escolheu esperar humano ([1] nas boas-vindas) — pode destravar
        if t in ("2",) or "maya" in t or "quero ser atendido" in t or "fazer meu pedido" in t:
            estado["tela"] = "explicacao"
            atendimento_humano.pop(telefone, None)  # remove bloqueio
            return _msg_explicacao()
        print(f"🔒 Maya travada para {telefone} (aguardando humano)")
        return None

    # ── Cliente sendo atendido por humano? Maya fica quieta ──
    if cliente_em_atendimento_humano(telefone):
        print(f"🤫 Maya silenciada para {telefone} (atendimento humano)")
        return None  # não responde nada

    # ── ATENDIMENTO HUMANO (qualquer tela, exceto estados iniciais e fluxo de pedido) ──
    # ⚠️ Durante o fluxo de pedido (pedido_*), NÃO interrompe por palavras soltas como "pessoa".
    # Só aciona se for o botão explícito [7] ou "🆘" ou frases claras de socorro.
    if tela not in ("boas_vindas", "aguardando_humano", "explicacao"):
        em_pedido = tela.startswith("pedido_") or tela in ("resumo", "mudar", "pedido_confirmado")
        if em_pedido:
            # Durante o pedido: só aciona atendente se for EXPLÍCITO (botão 7, 🆘, ou frases curtas de socorro)
            gatilho_explicito = t in ("7", "🆘") or any(
                t == p or t.startswith(p + " ") or t.endswith(" " + p)
                for p in ["quero falar com um atendente", "quero falar com atendente",
                          "chamar um atendente", "chama um atendente", "falar com um humano",
                          "falar com atendente", "preciso de um humano", "preciso de atendente"]
            )
            if not gatilho_explicito:
                pass  # não interrompe o fluxo de pedido por palavras soltas
            else:
                estado["tela"] = "menu"
                estado["dados_pedido"] = {}
                notificar_shay(
                    f"🆘 {telefone} pediu atendimento humano durante pedido!\n"
                    f"Última mensagem: \"{mensagem[:100]}\""
                )
                return (
                    "Claro! Aguarde uns minutinhos que já já um de nossos "
                    "atendentes entrará em contato com você por aqui mesmo! 💜\n\n"
                    "Fique de olho nas notificações! ✨\n\n"
                    "[0] 🔙 Voltar ao menu"
                )
        else:
            # Fora do pedido: mantém o comportamento original
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
    # BOAS-VINDAS (novo fluxo inicial)
    # ═══════════════════════════════════════════
    if tela == "boas_vindas":
        # Gatilhos para HUMANO (exato "1" OU contém palavra-chave)
        humano_gatilhos = ["humano", "atendente", "falar com", "pessoa", "gente"]
        if t == "1" or any(p in t for p in humano_gatilhos):
            estado["tela"] = "aguardando_humano"
            # Bloqueia Maya para este cliente (igual ao botão Bloquear do painel)
            atendimento_humano[telefone] = True
            # Se tinha assunto detectado, inclui na notificação
            extra = f"\nJá mencionou: {estado.get('assunto_detectado', '')}" if estado.get("assunto_detectado") else ""
            notificar_shay(
                f"👤 {telefone} quer falar com um humano!{extra}\n"
                f"Mensagem: \"{mensagem[:100]}\""
            )
            return _msg_aguardando_humano()
        # Gatilhos para MAYA (exato "2" OU contém palavra-chave)
        maya_gatilhos = ["maya", "quero fazer", "pedido", "assistente", "slide"]
        if t == "2" or any(p in t for p in maya_gatilhos):
            # Se já detectou assunto na primeira mensagem, pula explicação e vai direto
            assunto = estado.pop("assunto_detectado", None)
            if assunto:
                dados = estado.setdefault("dados_pedido", {})
                dados["tema"] = assunto
                estado["tela"] = "pedido_tipo"
                return (
                    f"Perfeito! Vou preparar seu slide sobre *{assunto}*! 🎉\n\n"
                    f"Agora me conta: qual TIPO de slide você prefere?\n\n"
                    f"Você pode ver exemplos em vídeo de cada tipo aqui "
                    f"(é só rolar pra baixo no site):\n"
                    f"👉 https://slydesign.com.br/personalizados/\n\n"
                    f"[1] ✅ Já escolhi o meu tipo de slide\n"
                    f"[2] 🤔 Diferença entre Canva e PowerPoint\n"
                    f"[3] 🎨 Diferença entre Transições e Temas\n\n"
                    f"[0] 🔙 Voltar ao menu"
                )
            # Sem assunto pré-detectado → explicação normal
            estado["tela"] = "explicacao"
            return _msg_explicacao()
        # Qualquer outra coisa → repete boas-vindas
        return _msg_boas_vindas()

    # ═══════════════════════════════════════════
    # EXPLICAÇÃO (como a Maya funciona)
    # ═══════════════════════════════════════════
    if tela == "explicacao":
        # Aceita: "ok", "entendi", "sim", "1", "bora", "vamos", "pronto"
        ok_triggers = ["ok", "entendi", "sim", "1", "pronto", "pronta", "bora", "vamos", "pode"]
        if any(t.startswith(p) for p in ok_triggers) or any(p in t for p in ok_triggers):
            estado["tela"] = "menu"
            return mostrar_menu()
        # Qualquer outra coisa → repete explicação
        return _msg_explicacao()

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

    # ── BOTÃO VOLTAR À PERGUNTA ANTERIOR (funciona em qualquer etapa) ──
    # ⚠️ Em pedido_extras com texto longo: NÃO ativa por palavras soltas no conteúdo
    if tela.startswith("pedido_") or tela in ("resumo", "pedido_confirmado"):
        em_extras = (tela == "pedido_extras")
        msg_longa = len(t) > 30  # texto longo = conteúdo, não comando
        if not (em_extras and msg_longa):
            if t == "9" or any(p in t for p in ["anterior", "errei", "ops", "volta anterior",
                                                  "pergunta anterior", "voltar anterior", "voltei"]):
                return _voltar_etapa_anterior(estado)

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
                    "Você pode ver exemplos em vídeo de cada tipo aqui "
                    "(é só rolar pra baixo no site):\n"
                    "👉 https://slydesign.com.br/personalizados/\n\n"
                    "[1] ✅ Já escolhi o meu tipo de slide\n"
                    "[2] 🤔 Diferença entre Canva e PowerPoint\n"
                    "[3] 🎨 Diferença entre Transições e Temas\n\n"
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
            "Você pode ver exemplos em vídeo de cada tipo aqui "
            "(é só rolar pra baixo no site):\n"
            "👉 https://slydesign.com.br/personalizados/\n\n"
            "[1] ✅ Já escolhi o meu tipo de slide\n"
            "[2] 🤔 Diferença entre Canva e PowerPoint\n"
            "[3] 🎨 Diferença entre Transições e Temas\n\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2: Tipo
    if tela == "pedido_tipo":
        # ── Menu simplificado (primeira visita) ──
        if not estado.get("mostrou_opcoes"):
            if t in ("1", "ja escolhi", "já escolhi", "escolhi", "escolher", "quero escolher"):
                estado["mostrou_opcoes"] = True
                return _msg_tipos_completo()
            # Cliente já especificou Transições + formato? → direto ao ponto
            if ("transic" in t) and ("canva" in t or "powerpoint" in t or "ppt" in t):
                # Já sabe que quer Transições, só precisa escolher Canva ou PPT
                if "powerpoint" in t or "ppt" in t:
                    dados["modelo"] = "🎬 PowerPoint (Transições)"
                else:
                    dados["modelo"] = "🎬 Canva (Transições)"
                estado.pop("mostrou_opcoes", None)
                estado["tela"] = "pedido_prazo"
                return (
                    f"Anotado! ✅\n\n"
                    f"Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
                    f"💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
                    f"da sua apresentacao.\n\n"
                    f"Me conta: qual data voce precisa? 📅\n\n"
                    f"[9] ↩️ Voltar à pergunta anterior\n"
                    f"[0] 🔙 Voltar ao menu"
                )
            # Cliente mencionou só "transições" → pergunta qual formato (Canva ou PPT)?
            if "transic" in t:
                estado["tela"] = "pedido_tipo_transicoes_formato"
                return (
                    "Certo, Transições! 🎬\n\n"
                    "Agora me diz: você prefere Canva ou PowerPoint?\n\n"
                    "📱 Canva — link online. Precisa de internet pra apresentar, "
                    "mas não ocupa espaço no celular/PC.\n"
                    "💻 PowerPoint — arquivo PPTX que você baixa. "
                    "Não precisa de internet pra apresentar.\n\n"
                    "Visualmente são iguais! 💜\n\n"
                    "[1] 📱 Canva (Transições) — R$ 25,00\n"
                    "[2] 💻 PowerPoint (Transições) — R$ 35,00\n\n"
                    "[9] ↩️ Voltar à pergunta anterior\n"
                    "[0] 🔙 Voltar ao menu"
                )
            if t in ("2",) or "canva" in t or "powerpoint" in t or "diferenca" in t or "diferença" in t:
                estado["tela"] = "pedido_tipo_diferenca"
                return _msg_diferenca_canva_ppt()
            if t in ("3",) or "temas" in t:
                estado["tela"] = "pedido_tipo_temas_diferenca"
                return _msg_diferenca_transicoes_temas()
            # Qualquer outra coisa → repete menu simplificado
            return (
                "Certo, anotei o tema! 📝\n\n"
                "Agora me conta: qual TIPO de slide você prefere?\n\n"
                "Você pode ver exemplos em vídeo de cada tipo aqui "
                "(é só rolar pra baixo no site):\n"
                "👉 https://slydesign.com.br/personalizados/\n\n"
                "[1] ✅ Já escolhi o meu tipo de slide\n"
                "[2] 🤔 Diferença entre Canva e PowerPoint\n"
                "[3] 🎨 Diferença entre Transições e Temas\n\n"
                "[0] 🔙 Voltar ao menu"
            )

        # ── Opções completas (depois de "Já escolhi") ──
        tipos = {
            "1": "📄 PDF", "2": "🎬 Canva (Transições)", "3": "🎬 PowerPoint (Transições)",
            "4": "🎨 Canva Temas", "5": "🎨 PPTX Temas"
        }

        # "6" ou palavras de dúvida → ainda pode tirar dúvida mesmo nas opções completas
        if t == "6" or "diferença" in t or "diferenca" in t:
            estado["tela"] = "pedido_tipo_diferenca"
            return _msg_diferenca_canva_ppt()
        if t == "7" or "transic" in t or "tema " in t:
            estado["tela"] = "pedido_tipo_temas_diferenca"
            return _msg_diferenca_transicoes_temas()

        # Mapeia numeros normais
        if t in tipos:
            dados["modelo"] = tipos[t]
        elif t in tipos.values():
            dados["modelo"] = t
        elif t in ("canva", "📱 canva", "📱"):
            dados["modelo"] = "🎬 Canva (Transições)"
        elif t in ("powerpoint", "ppt", "💻", "pptx", "💻 powerpoint"):
            dados["modelo"] = "🎬 PowerPoint (Transições)"
        elif t in ("pdf", "📄 pdf", "📄"):
            dados["modelo"] = "📄 PDF"
        else:
            # Não reconheceu → repete as opções
            return (
                "Não entendi qual tipo você quer... 😅\n\n"
                "Digite o número do tipo de slide:\n\n"
                "[1] 📄 PDF — R$ 20,00\n"
                "[2] 🎬 Canva (Transições) — R$ 25,00\n"
                "[3] 🎬 PowerPoint (Transições) — R$ 35,00\n"
                "[4] 🎨 Canva Temas — R$ 28,00\n"
                "[5] 🎨 PPTX Temas — R$ 38,00\n\n"
                "[0] 🔙 Voltar ao menu"
            )

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
                "[9] ↩️ Voltar à pergunta anterior\n"
                "[0] 🔙 Voltar ao menu"
            )

        if modo_edicao:
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)

        estado.pop("mostrou_opcoes", None)  # limpa flag
        estado["tela"] = "pedido_prazo"
        return (
            "Anotado! ✅\n\n"
            "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
            "💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
            "da sua apresentacao.\n\n"
            "Me conta: qual data voce precisa? 📅\n\n"
            "[9] ↩️ Voltar à pergunta anterior\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2b: Diferença Canva vs PowerPoint
    if tela == "pedido_tipo_diferenca":
        # "Já escolhi" → volta pras opções completas
        if t in ("1",) or "ja escolhi" in t or "já escolhi" in t or "escolhi" in t:
            estado["tela"] = "pedido_tipo"
            estado["mostrou_opcoes"] = True
            return _msg_tipos_completo()
        # Dúvida sobre transições vs temas
        if "transic" in t or "tema " in t:
            estado["tela"] = "pedido_tipo_temas_diferenca"
            return _msg_diferenca_transicoes_temas()

        # Tipo apos ver diferença (números 1-5)
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
            # Não reconheceu → repete a explicação
            return _msg_diferenca_canva_ppt()

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
                "[9] ↩️ Voltar à pergunta anterior\n"
                "[0] 🔙 Voltar ao menu"
            )
        if modo_edicao:
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        estado.pop("mostrou_opcoes", None)
        estado["tela"] = "pedido_prazo"
        return (
            "Anotado! ✅\n\n"
            "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
            "💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
            "da sua apresentacao.\n\n"
            "Me conta: qual data voce precisa? 📅\n\n"
            "[9] ↩️ Voltar à pergunta anterior\n"
            "[0] 🔙 Voltar ao menu"
        )

    # PASSO 2c: Diferença Transições vs Temas (NOVO)
    if tela == "pedido_tipo_temas_diferenca":
        # "Já escolhi" → volta pras opções completas
        if t in ("1",) or "ja escolhi" in t or "já escolhi" in t or "escolhi" in t:
            estado["tela"] = "pedido_tipo"
            estado["mostrou_opcoes"] = True
            return _msg_tipos_completo()
        # Dúvida sobre canva vs ppt
        if "canva" in t or "powerpoint" in t or "ppt" in t:
            estado["tela"] = "pedido_tipo_diferenca"
            return _msg_diferenca_canva_ppt()
        # Qualquer outra coisa → repete explicação
        return _msg_diferenca_transicoes_temas()

    # PASSO 2d: Cliente já escolheu Transições, só falta Canva ou PPT
    if tela == "pedido_tipo_transicoes_formato":
        if t in ("1", "canva", "📱 canva", "📱"):
            dados["modelo"] = "🎬 Canva (Transições)"
            estado["tela"] = "pedido_prazo"
            return (
                "Anotado! ✅\n\n"
                "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
                "💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
                "da sua apresentacao.\n\n"
                "Me conta: qual data voce precisa? 📅\n\n"
                "[9] ↩️ Voltar à pergunta anterior\n"
                "[0] 🔙 Voltar ao menu"
            )
        if t in ("2", "powerpoint", "ppt", "💻 powerpoint", "💻"):
            dados["modelo"] = "🎬 PowerPoint (Transições)"
            estado["tela"] = "pedido_prazo"
            return (
                "Anotado! ✅\n\n"
                "Agora sobre o PRAZO: ate que dia posso te entregar?\n\n"
                "💡 Recomendamos pedir com pelo menos 1 dia de antecedencia "
                "da sua apresentacao.\n\n"
                "Me conta: qual data voce precisa? 📅\n\n"
                "[9] ↩️ Voltar à pergunta anterior\n"
                "[0] 🔙 Voltar ao menu"
            )
        # Não entendeu → repete as opções
        return (
            "Certo, Transições! 🎬\n\n"
            "Você prefere Canva ou PowerPoint?\n\n"
            "📱 Canva — link online. Precisa de internet pra apresentar.\n"
            "💻 PowerPoint — arquivo PPTX que você baixa. Não precisa de internet.\n\n"
            "Visualmente são iguais! 💜\n\n"
            "[1] 📱 Canva (Transições) — R$ 25,00\n"
            "[2] 💻 PowerPoint (Transições) — R$ 35,00\n\n"
            "[9] ↩️ Voltar à pergunta anterior\n"
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
                "[9] ↩️ Voltar à pergunta anterior\n"
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
            f"[9] ↩️ Voltar à pergunta anterior\n"
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
            "[9] ↩️ Voltar à pergunta anterior\n"
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
                "[9] ↩️ Voltar à pergunta anterior\n"
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
                "[9] ↩️ Voltar à pergunta anterior\n"
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
                "[9] ↩️ Voltar à pergunta anterior\n"
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
            estado["tela"] = "pedido_confirmado"
            estado["dados_pedido"] = dados  # preserva os dados
            notificar_shay(
                f"🎨 NOVO PEDIDO de {telefone}!\n\n"
                f"📝 Tema: {dados.get('tema', '?')}\n"
                f"🎨 Tipo: {dados.get('modelo', '?')}\n"
                f"📅 Prazo: {dados.get('prazo', '?')}\n"
                f"👤 Nomes: {dados.get('nomes', 'Não')}\n"
                f"📎 Extras: {dados.get('extras', 'Nenhum')}\n\n"
                f"💡 Pra revisar: use 'assumir {telefone}' pra assumir o atendimento"
            )
            return _msg_pedido_confirmado(dados)
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
            # NÃO limpa os extras — só adiciona o que o cliente mandar
            return (
                "Os extras atuais são: "
                f"\"{_truncar_extras(dados.get('extras', 'Nenhum'))}\"\n\n"
                "Mande mais informações que quiser adicionar. "
                "Quando terminar, responda 'finalizar'. 💜"
            )
        estado["tela"] = "resumo"
        return _mostrar_resumo(dados)

    # PASSO 7: Pedido confirmado (mostra resumo + opção de editar)
    if tela == "pedido_confirmado":
        if t in ("1",) or any(p in t for p in ["editar", "mudar", "errei", "quero mudar",
                                                  "mudar algo", "alterar", "arrumar", "corrigir"]):
            estado["tela"] = "mudar"
            return "Claro! O que você quer mudar? ✏️\n\n[1] 📝 Mudar tema\n[2] 🎨 Mudar tipo\n[3] 📅 Mudar prazo\n[4] 👤 Mudar nomes\n[5] 📎 Mudar extras\n[0] 🔙 Voltar ao resumo"
        if t in ("2",) or any(p in t for p in ["ok", "certo", "tudo certo", "ta certo",
                                                  "tá certo", "isso", "isso mesmo", "perfeito",
                                                  "confirmado", "obrigado", "obrigada", "vlw",
                                                  "aguardar", "aguardo", "esperar"]):
            estado["tela"] = "aguardando_humano"
            estado["bloqueio_permanente"] = True  # Maya NUNCA mais responde — só Shay no painel
            atendimento_humano[telefone] = True
            _salvar_estado_clientes()
            return (
                "Perfeito! Seu pedido está confirmado! 💜\n\n"
                "Agora é só aguardar: um de nossos atendentes vai entrar "
                "em contato com você por aqui para confirmar o pagamento, "
                "combinar a entrega e alinhar os últimos detalhes. ✨\n\n"
                "Fique de olho nas notificações! 💜"
            )
        # Qualquer outra coisa → repete a mensagem de confirmação
        return _msg_pedido_confirmado(dados)

    # PASSO 7.5: Aguardando Pix (após Shay aceitar pedido)
    if tela == "aguardando_pix":
        # Maya fica quieta — quem responde é a Shay
        if t in ("menu", "voltar", "🔙 voltar ao menu", "0"):
            estado["tela"] = "menu"
            estado["dados_pedido"] = {}
            return mostrar_menu()
        print(f"🤫 Maya silenciada para {telefone} (aguardando Pix)")
        return None

    # PASSO 8: Aguardando pagamento (Maya NAO responde)
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

    # PASSO 8: Pedido rejeitado (após Shay rejeitar no painel)
    if tela == "pedido_rejeitado":
        if t == "1" or any(p in t for p in ["amanha", "amanhã", "entregar amanha", "pode ser"]):
            # Cliente aceita entregar amanhã sem taxa de urgência
            dados["prazo"] = "amanhã"
            dados.pop("taxa_urgencia", None)
            estado["tela"] = "resumo"
            return _mostrar_resumo(dados)
        if t == "2" or any(p in t for p in ["dinheiro", "reembolso", "devolucao", "devolução", "volta", "quero meu"]):
            # Cliente quer reembolso
            estado["tela"] = "menu"
            estado["dados_pedido"] = {}
            notificar_shay(
                f"💰 {telefone} quer reembolso!\n"
                f"Pedido rejeitado, cliente pediu dinheiro de volta."
            )
            return (
                "Entendo! Vou avisar a equipe aqui e eles vao fazer "
                "a devolucao do Pix pra voce. 💜\n\n"
                "Em ate 24h o valor volta pra sua conta. "
                "Qualquer duvida e so chamar! ✨\n\n"
                "[0] 🔙 Voltar ao menu"
            )
        # Qualquer outra coisa → repete as opções
        return (
            "Infelizmente nao temos mais vagas para hoje... 😕\n\n"
            "Mas podemos entregar amanha sem a taxa de urgencia! "
            "Se preferir, faremos a devolucao do Pix.\n\n"
            "Como prefere?\n\n"
            "[1] 📅 Pode ser entregue amanha\n"
            "[2] 💰 Quero meu dinheiro de volta"
        )

    # ═══════════════════════════════════════════
    # FALLBACK: IA
    # ═══════════════════════════════════════════

    # Se o cliente esta no meio de um pedido e mandou algo fora do fluxo
    if tela.startswith("pedido_"):
        return (
            "Para seguir com o seu pedido, siga o fluxo das mensagens "
            "e ao final tiramos suas duvidas. 💜\n\n"
            "Vamos continuar de onde paramos?\n\n"
            f"{_repetir_ultima_pergunta(estado)}"
        )

    estado["tela"] = "menu"
    return _chamar_ia(mensagem, estado)


# ── PROCESSAMENTO DE PRIMEIRAS MENSAGENS (delay 10s) ──

def _processar_primeiras_mensagens(estado: dict, telefone: str) -> str:
    """Processa as mensagens acumuladas do novo cliente.
    SEMPRE envia boas-vindas (escolha humano vs Maya).
    Se detectou assunto, guarda pra usar depois que o cliente escolher Maya."""
    mensagens = estado.pop("mensagens_pendentes", [])
    estado.pop("primeira_msg_ts", None)

    if not mensagens:
        estado["tela"] = "boas_vindas"
        return _msg_boas_vindas()

    # Se a última mensagem é curta (escolha de menu tipo "2", "sim", "ok"),
    # extrai o assunto só das mensagens anteriores pra não poluir
    if len(mensagens) >= 2 and len(mensagens[-1].split()) <= 2:
        texto_para_extrair = " ".join(mensagens[:-1])
    else:
        texto_para_extrair = " ".join(mensagens)

    texto_completo = " ".join(mensagens).strip()
    t = texto_completo.lower()

    # Detecta se cliente já falou o que quer (tema, tipo de slide)
    marcadores_pedido = [
        "slide sobre", "slide de", "slide do", "slide da",
        "queria um slide", "queria slide", "quero um slide", "quero slide",
        "preciso de um slide", "preciso de slide",
        "gostaria de um slide", "gostaria de slide",
        "faz um slide", "faz slide", "fazer um slide",
        "quero fazer", "queria fazer", "preciso fazer",
        "pedido", "personalizado",
    ]

    tem_pedido = any(m in t for m in marcadores_pedido)

    if tem_pedido:
        tema = _extrair_assunto(texto_para_extrair)
        if tema and len(tema) > 3:
            # Guarda o assunto detectado pra usar quando cliente escolher Maya [2]
            estado["assunto_detectado"] = tema

            # Verifica se é um TEMA CONHECIDO (ex: ChatGPT, Spotify, Netflix...)
            tema_link = None
            from app.buscador import buscar_tema as buscar_tema_catalogo
            try:
                melhor, _ = buscar_tema_catalogo(tema)
                if melhor:
                    tema_link = melhor.get("link", "")
            except Exception:
                pass

            estado["tela"] = "boas_vindas"
            if tema_link:
                return (
                    f"Oieee! Eu sou a Maya, atendente virtual da Sly Design! 💜\n\n"
                    f"Vi que você quer um slide sobre *{tema}*, né? 🎉\n\n"
                    f"Inclusive, temos esse tema prontinho no site! "
                    f"Dá uma olhadinha:\n"
                    f"👉 {tema_link}\n\n"
                    f"A gente também cria slides personalizados do zero e temos "
                    f"slides prontos com super descontos!\n"
                    f"Dá uma olhadinha: 👉 https://slydesign.com.br\n\n"
                    f"Como posso te ajudar?\n\n"
                    f"[1] 🙋 Quero falar com um atendente\n"
                    f"    (assim que possível alguém da equipe te responde)\n\n"
                    f"[2] 🤖 Quero fazer meu pedido com a Maya\n"
                    f"    (nossa assistente virtual, rapidinho!)\n\n"
                    f"💡 Digite o número 1 ou 2 para escolher!"
                )
            return (
                f"Oieee! Eu sou a Maya, atendente virtual da Sly Design! 💜\n\n"
                f"Vi que você quer um slide sobre *{tema}*, né? 🎉\n\n"
                f"A gente cria slides personalizados do zero e também temos "
                f"slides prontos no site com super descontos!\n"
                f"Dá uma olhadinha: 👉 https://slydesign.com.br\n\n"
                f"Como posso te ajudar?\n\n"
                f"[1] 🙋 Quero falar com um atendente\n"
                f"    (assim que possível alguém da equipe te responde)\n\n"
                f"[2] 🤖 Quero fazer meu pedido com a Maya\n"
                f"    (nossa assistente virtual, rapidinho!)\n\n"
                f"💡 Digite o número 1 ou 2 para escolher!"
            )
        else:
            # Detectou intenção de pedido mas não extraiu assunto → boas-vindas normais
            estado["tela"] = "boas_vindas"
            return _msg_boas_vindas()

    # Se não detectou pedido → boas-vindas normais
    estado["tela"] = "boas_vindas"
    return _msg_boas_vindas()


def _extrair_assunto(texto: str) -> str:
    """Tenta extrair o assunto/tema de uma mensagem do cliente."""
    import re

    # Padrões comuns: "slide sobre X", "queria um slide de X", etc.
    padroes = [
        r'(?:slide|slides)\s+(?:sobre|de|do|da|dos|das)\s+[""]?([^.!?,""]+)[""]?',
        r'(?:queria|quero|preciso|gostaria)\s+(?:de\s+)?(?:um\s+)?(?:slide|slides)\s+(?:sobre|de|do|da|dos|das)\s+[""]?([^.!?,""]+)[""]?',
        r'(?:sobre|assunto|tema)\s+(?:é|e|:)?\s*[""]?([^.!?,""]+)[""]?',
        r'(?:fazer|faz)\s+(?:um\s+)?(?:slide|slides)\s+(?:sobre|de|do|da)\s+[""]?([^.!?,""]+)[""]?',
    ]

    texto_lower = texto.lower().strip()
    for padrao in padroes:
        match = re.search(padrao, texto_lower)
        if match:
            assunto = match.group(1).strip()
            # Remove palavras de conexão se tiver
            for p in [" e ", " pra ", " para ", " com ", " no ", " na ", " em ", " mas "]:
                if p in assunto:
                    assunto = assunto.split(p)[0].strip()
            if len(assunto) > 3:
                return assunto

    # Fallback: pega o texto depois de "queria", "quero" ou "preciso"
    for marcador in ["queria", "quero", "preciso"]:
        if marcador in texto_lower:
            idx = texto_lower.find(marcador)
            resto = texto_lower[idx + len(marcador):].strip()
            # Remove palavras filler
            for filler in ["um", "uma", "slide", "slides", "sobre", "de", "do", "da", "o", "a"]:
                resto = re.sub(r'\b' + filler + r'\b', '', resto, count=1).strip()
            if len(resto) > 3:
                return resto

    return ""

# ── FUNÇÕES AUXILIARES ──

def _msg_boas_vindas():
    """Primeira mensagem: cliente escolhe entre humano ou Maya."""
    return (
        "Oieee! Eu sou a Maya, atendente virtual da Sly Design! 💜\n\n"
        "A gente cria slides personalizados do zero e também temos "
        "slides prontos no site com super descontos!\n"
        "Dá uma olhadinha: 👉 https://slydesign.com.br\n\n"
        "Como posso te ajudar?\n\n"
        "[1] 🙋 Quero falar com um atendente\n"
        "    (assim que possível alguém da equipe te responde)\n\n"
        "[2] 🤖 Quero fazer meu pedido com a Maya\n"
        "    (nossa assistente virtual, rapidinho!)\n\n"
        "💡 Digite o número 1 ou 2 para escolher!"
    )


def _msg_aguardando_humano():
    """Cliente escolheu esperar um humano — Maya trava."""
    return (
        "Ok! Aguarde um tempinho que assim que possível um de "
        "nossos atendentes vai te responder por aqui mesmo! 💜\n\n"
        "Mas se quiser, também pode fazer seu pedido comigo agora mesmo:\n\n"
        "[2] 🤖 Quero fazer meu pedido com a Maya!"
    )


def _msg_explicacao():
    """Explica como a Maya funciona antes de começar o fluxo."""
    return (
        "Combinado! Vou te guiar no seu pedido, é rapidinho! 😊\n\n"
        "📋 Como funciona:\n"
        "• Vou te fazer uma pergunta por vez\n"
        "• Quando aparecer [número] nas opções, é só digitar o número\n"
        "• Responda cada pergunta em uma única mensagem\n\n"
        "⚠️ Importante: não interrompa o processo! "
        "Responda apenas o que eu perguntar para o pedido dar "
        "certinho. Todas as suas dúvidas serão sanadas! 💜\n\n"
        "Pronto(a)?\n\n"
        "[Ok, entendi!]"
    )


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


def _msg_tipos_completo():
    """Opções completas de tipos de slide (após 'Já escolhi')."""
    return (
        "Agora me conta: qual TIPO de slide você prefere?\n\n"
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
        "[6] 🤔 Diferença entre Canva e PowerPoint\n"
        "[7] 🎨 Diferença entre Transições e Temas\n\n"
        "[9] ↩️ Voltar à pergunta anterior\n"
        "[0] 🔙 Voltar ao menu"
    )


def _msg_diferenca_canva_ppt():
    """Explica diferença Canva vs PowerPoint."""
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
        "[5] 📄 PDF — R$ 20,00\n\n"
        "💡 Digite 'ja escolhi' se ja souber qual quer"
        " ou 'transicoes vs temas' pra entender a diferença.\n\n"
        "[9] ↩️ Voltar à pergunta anterior\n"
        "[0] 🔙 Voltar ao menu"
    )


def _msg_diferenca_transicoes_temas():
    """Explica diferença Transições vs Temas com vídeos."""
    return (
        "🎬 TRANSICOES: O design e feito com base no SEU assunto. "
        "Cada slide e criado do zero com o conteudo que voce enviar.\n\n"
        "📺 Exemplo de Transicoes:\n"
        "👉 https://youtu.be/pHkjUpiV9Ds\n\n"
        "🎨 TEMAS: Seu assunto e inserido em um design TEMATICO "
        "(ex: Netflix, Spotify, Jovens Titas...). "
        "O visual segue um estilo pronto.\n\n"
        "📺 Exemplo de Temas:\n"
        "👉 https://youtu.be/beDVpp41KPc\n\n"
        "💡 Digite 'ja escolhi' quando estiver pronto(a) pra escolher"
        " ou 'canva vs ppt' pra ver a diferenca entre os formatos.\n\n"
        "[9] ↩️ Voltar à pergunta anterior\n"
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


def _msg_pedido_confirmado(dados):
    """Mostra o resumo completo do pedido após confirmar + opção de editar."""
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

    try:
        valor_str = preco.replace("R$ ", "").replace(",", ".")
        metade = float(valor_str) / 2
        metade_str = f"R$ {metade:.2f}".replace(".", ",")
    except (ValueError, AttributeError):
        metade_str = "a combinar"

    # Monta linha do tema conforme o tipo
    img_tag = " (imagem anexada)" if dados.get("tem_imagem") else ""
    if "Temas" in modelo:
        assunto = dados.get("assunto", dados.get("tema", ""))
        tema_design = dados.get("tema_design", "")
        linha_tema = f"📝 Assunto: {assunto}{img_tag}\n🎨 Tema: {modelo} — {tema_design}\n"
    else:
        linha_tema = f"📝 Tema: {dados.get('tema', '')}{img_tag}\n🎨 Tipo: {modelo}\n"

    aviso_paginas = ""
    if dados.get("paginas_extra"):
        aviso_paginas = (
            "\n⚠️ Conteúdo completo será adicionado. "
            "O número final de páginas (e valor) será confirmado "
            "após a produção.\n"
        )

    return (
        "✨ Pedido confirmado! Alguém da equipe vai analisar "
        "e confirmar seu pedido, aguarde uns minutinhos... 💜\n\n"
        "📋 Resumo do pedido:\n\n"
        f"{linha_tema}"
        f"📅 Prazo: {dados.get('prazo', '')}\n"
        f"👤 Nomes: {dados.get('nomes', 'Não')}\n"
        f"📎 Extras: {_truncar_extras(dados.get('extras', 'Nenhum'))}\n\n"
        f"💰 Valor total: {preco}"
        f"{' (taxa urgência R$ 5,00)' if taxa_urgencia else ''}\n"
        f"💳 50% para confirmar: {metade_str} — o restante na entrega! 💜\n"
        f"{aviso_paginas}\n"
        f"[1] ✏️ Quero editar algo\n\n"
        f"Se estiver tudo certo, basta aguardar alguém "
        f"da equipe vir confirmar seu pedido. 💜"
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


def _voltar_etapa_anterior(estado: dict) -> str:
    """Volta à etapa anterior no fluxo de pedido, preservando dados já coletados."""
    tela = estado.get("tela", "")
    dados = estado.get("dados_pedido", {})

    # Mapeamento: tela atual → tela anterior
    mapeamento = {
        "pedido_tema": "menu",
        "pedido_tipo": "pedido_tema",
        "pedido_tipo_diferenca": "pedido_tipo",
        "pedido_tipo_temas_diferenca": "pedido_tipo",
        "pedido_tipo_transicoes_formato": "pedido_tipo",
        "pedido_qual_tema": "pedido_tipo",
        "pedido_canva_ppt": "pedido_qual_tema",
        "pedido_prazo": "pedido_tipo",  # fallback — ajustado abaixo
        "pedido_nomes": "pedido_prazo",
        "pedido_extras": "pedido_nomes",
        "resumo": "pedido_extras",
        "pedido_confirmado": "resumo",
    }

    # Ajustes conforme o tipo de slide escolhido
    if tela == "pedido_prazo":
        if "Temas" in dados.get("modelo", ""):
            mapeamento["pedido_prazo"] = "pedido_qual_tema"
        elif dados.get("tema_design"):
            mapeamento["pedido_prazo"] = "pedido_canva_ppt"

    if tela == "pedido_nomes" and "Temas" in dados.get("modelo", "") and not dados.get("tema_design"):
        mapeamento["pedido_nomes"] = "pedido_qual_tema"

    # Primeira etapa: voltar = menu
    if tela == "pedido_tema":
        estado["tela"] = "menu"
        estado["dados_pedido"] = {}
        return "Voltando ao início... 💜\n\n" + mostrar_menu()

    nova_tela = mapeamento.get(tela, "menu")
    if nova_tela == "menu":
        estado["tela"] = "menu"
        estado["dados_pedido"] = {}
        return "Voltando ao início... 💜\n\n" + mostrar_menu()

    estado["tela"] = nova_tela
    # Remove o dado da etapa para onde estamos voltando (vai ser perguntado de novo)
    if nova_tela == "pedido_tema":
        dados.pop("tema", None)
    elif nova_tela == "pedido_tipo":
        dados.pop("modelo", None)
        estado["mostrou_opcoes"] = True  # já mostra opções completas
    elif nova_tela == "pedido_qual_tema":
        dados.pop("tema_design", None)
    elif nova_tela == "pedido_prazo":
        dados.pop("prazo", None)
        dados.pop("taxa_urgencia", None)
    elif nova_tela == "pedido_nomes":
        dados.pop("nomes", None)
    elif nova_tela == "pedido_extras":
        dados.pop("extras", None)

    msg = _repetir_ultima_pergunta(estado)
    if nova_tela not in ("menu",):
        msg += "\n[9] ↩️ Voltar à pergunta anterior"
    return msg


def _repetir_ultima_pergunta(estado: dict) -> str:
    """Retorna a pergunta adequada para o estado atual do pedido."""
    tela = estado.get("tela", "")
    dados = estado.get("dados_pedido", {})
    if tela == "aguardando_primeira_msg":
        return (
            "Oie! Tô aqui esperando você terminar de digitar... 💜\n\n"
            "Pode mandar tudo de uma vez que eu entendo! Me conta: "
            "no que posso te ajudar?"
        )
    elif tela == "boas_vindas":
        return _msg_boas_vindas()
    elif tela == "aguardando_humano":
        return _msg_aguardando_humano()
    elif tela == "explicacao":
        return _msg_explicacao()
    elif tela == "pedido_tema":
        return "📝 Qual o ASSUNTO do slide?\n\n[0] 🔙 Voltar ao menu"
    elif tela == "pedido_tipo":
        # Menu simplificado ou completo?
        if not estado.get("mostrou_opcoes"):
            return (
                "Veja os exemplos no site e me diga qual tipo prefere:\n"
                "👉 https://slydesign.com.br/personalizados/\n\n"
                "[1] ✅ Já escolhi o meu tipo de slide\n"
                "[2] 🤔 Diferença entre Canva e PowerPoint\n"
                "[3] 🎨 Diferença entre Transições e Temas\n\n"
                "[0] 🔙 Voltar ao menu"
            )
        return _msg_tipos_completo()
    elif tela == "pedido_tipo_diferenca":
        return _msg_diferenca_canva_ppt()
    elif tela == "pedido_tipo_temas_diferenca":
        return _msg_diferenca_transicoes_temas()
    elif tela == "pedido_tipo_transicoes_formato":
        return (
            "Certo, Transições! 🎬\n\n"
            "Você prefere Canva ou PowerPoint?\n\n"
            "[1] 📱 Canva (Transições) — R$ 25,00\n"
            "[2] 💻 PowerPoint (Transições) — R$ 35,00\n\n"
            "[9] ↩️ Voltar à pergunta anterior\n"
            "[0] 🔙 Voltar ao menu"
        )
    elif tela == "pedido_qual_tema":
        top5 = ", ".join(TEMAS_DISPONIVEIS[:5])
        return (
            f"Os mais pedidos: {top5}...\n"
            "Me diga qual tema voce quer?\n\n"
            "[8] 🎨 Quero o design sobre o MEU assunto\n"
            "[0] 🔙 Voltar ao menu"
        )
    elif tela == "pedido_prazo":
        return "Qual a data que voce precisa? 📅\n\n[0] 🔙 Voltar ao menu"
    elif tela == "pedido_nomes":
        return "Mande todos os nomes em uma unica mensagem ou responda 'nao'. 💜\n\n[0] 🔙 Voltar ao menu"
    elif tela == "pedido_extras":
        return (
            "Quer adicionar alguma informacao extra? 💜\n\n"
            "[1] 📝 Resumir em 10 paginas\n"
            "[2] ➕ Adicionar tudo\n"
            "[3] ✅ Finalizar Pedido\n"
            "[0] 🔙 Voltar ao menu"
        )
    elif tela == "resumo":
        return "Tudo certo? [1] Confirmar [2] Mudar algo [3] Cancelar"
    elif tela == "pedido_confirmado":
        return _msg_pedido_confirmado(dados)
    elif tela == "mudar":
        return "O que quer mudar? [1] Tema [2] Tipo [3] Prazo [4] Nomes [5] Extras [0] Voltar"
    elif tela == "aguardando_pagamento":
        return "Seu pedido esta aguardando confirmacao de pagamento. 💜\n\n[0] 🔙 Voltar ao menu"
    elif tela == "aguardando_pix":
        return "Seu pedido foi aceito! Assim que o pagamento for confirmado, começamos a produção. 💜\n\n[0] 🔙 Voltar ao menu"
    elif tela == "pedido_rejeitado":
        return (
            "Infelizmente nao temos mais vagas para hoje... 😕\n\n"
            "Como prefere?\n\n"
            "[1] 📅 Pode ser entregue amanha\n"
            "[2] 💰 Quero meu dinheiro de volta"
        )
    return "No que posso te ajudar? 💜"


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

    # Normaliza numero: remove sufixos e deixa so os digitos
    import re as _re
    telefone = _re.sub(r'[@:].*$', '', telefone)  # remove @lid, @s.whatsapp.net, @g.us, :port etc
    telefone = _re.sub(r'[^\d]', '', telefone)    # deixa so os numeros
    if not telefone.startswith('55') and len(telefone) >= 10:
        telefone = '55' + telefone  # adiciona DDI Brasil se faltar

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
    # Normaliza numero
    import re as _re2
    telefone = _re2.sub(r'[@:].*$', '', telefone)
    telefone = _re2.sub(r'[^\d]', '', telefone)
    if not telefone.startswith('55') and len(telefone) >= 10:
        telefone = '55' + telefone
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
    aguardando_humano_count = 0
    aguardando_pix_count = 0
    pedido_realizado_count = 0
    for tel, est in clientes.items():
        tela = est.get("tela", "?")
        dados = est.get("dados_pedido", {})
        shay_msg = est.get("shay_respondeu", False)
        shay_assumiu = est.get("shay_assumiu", False)
        is_humano = atendimento_humano.get(tel, False)

        # Mostrar se: tem pedido, ou ta bloqueado, ou Shay mandou msg,
        # ou esta esperando atendente humano, ou pedido confirmado/aguardando pix
        tem_atividade = (tela not in ("menu", "boas_vindas", "explicacao") or dados or is_humano or shay_msg
                        or tela in ("pedido_confirmado", "aguardando_pix"))
        if not tem_atividade:
            continue

        if tela == "aguardando_pagamento":
            aguardando += 1
        if tela == "aguardando_humano":
            aguardando_humano_count += 1
        if tela == "aguardando_pix":
            aguardando_pix_count += 1
        if tela == "pedido_confirmado":
            pedido_realizado_count += 1

        modelo = dados.get("modelo", "")
        modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
        preco_base = PRECOS.get(modelo_limpo, "-")

        is_aguardando = tela == "aguardando_pagamento"
        is_aguardando_pix = tela == "aguardando_pix"
        is_pedido_confirmado = tela == "pedido_confirmado"

        # Determina status visual
        if is_humano and shay_assumiu:
            status_cls = "status-shay-assumiu"
            status_txt = "Sendo atendido por Shay"
        elif is_humano:
            status_cls = "status-humano"
            status_txt = "Bloqueado"
        elif tela == "aguardando_humano":
            status_cls = "status-aguardando-humano"
            status_txt = "Quer atendente"
        elif is_aguardando:
            status_cls = "status-pagamento"
            status_txt = "Aguardando pagamento"
        elif is_aguardando_pix:
            status_cls = "status-pix"
            status_txt = "Aguardando Pix"
        elif is_pedido_confirmado:
            status_cls = "status-confirmado"
            status_txt = "Pedido Realizado"
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
            "extras": dados.get("extras", "-"),
            "humano": is_humano,
            "aguardando": is_aguardando,
            "aguardando_pix": is_aguardando_pix,
            "pedido_confirmado": is_pedido_confirmado,
            "quer_atendente": tela == "aguardando_humano",
            "shay_assumiu": shay_assumiu,
            "shay_msg": shay_msg,
            "statusCls": status_cls,
            "statusTxt": status_txt,
        })

    # Limpa formato interno do telefone
    import re as _re3
    for c in cli_list:
        tel = c["telefone"]
        tel = _re3.sub(r'[@:].*$', '', tel)  # remove sufixos
        tel = _re3.sub(r'[^\d]', '', tel)    # so digitos
        if tel and not tel.startswith('55') and len(tel) >= 10:
            tel = '55' + tel
        c["telefone"] = tel

    return {"clientes": cli_list, "total": len(cli_list), "aguardando": aguardando, "aguardando_humano": aguardando_humano_count, "aguardando_pix": aguardando_pix_count, "pedido_realizado": pedido_realizado_count}


@app.post("/painel/bloquear")
async def painel_bloquear(request: Request):
    """Bloqueia Maya para um numero (atendimento humano). Marca que Shay assumiu."""
    data = await request.json()
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
    if tel:
        atendimento_humano[tel] = True
        if tel in clientes:
            clientes[tel]["shay_assumiu"] = True
        _salvar_estado_clientes()
        print(f"🙋 Painel: Shay assumiu atendimento de {tel}")
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/liberar")
async def painel_liberar(request: Request):
    """Libera Maya para um numero."""
    data = await request.json()
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
    if tel:
        atendimento_humano.pop(tel, None)
        _salvar_estado_clientes()
        print(f"🤖 Painel: Maya liberada para {tel}")
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/rejeitar")
async def painel_rejeitar(request: Request):
    """Rejeita pedido (ex: sem vaga hoje) e notifica cliente com botoes."""
    data = await request.json()
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
    motivo = data.get("motivo", "sem disponibilidade")
    if tel and tel in clientes:
        est = clientes[tel]
        # Preserva os dados do pedido (pra poder ajustar prazo depois)
        dados = est.get("dados_pedido", {})
        if dados:
            dados.pop("taxa_urgencia", None)  # remove taxa de urgencia
        est["tela"] = "pedido_rejeitado"
        _salvar_estado_clientes()

        # Notifica o cliente com botoes
        msg = (
            f"Infelizmente nao temos mais vagas para hoje... 😕\n\n"
            f"Mas podemos entregar amanha sem a taxa de urgencia! "
            f"Se preferir, faremos a devolucao do Pix.\n\n"
            f"Como prefere?\n\n"
            f"[1] 📅 Pode ser entregue amanha\n"
            f"[2] 💰 Quero meu dinheiro de volta"
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


@app.post("/painel/aceitar-pedido")
async def painel_aceitar_pedido(request: Request):
    """Aceita pedido e envia mensagem natural da Maya com Pix de 50%."""
    data = await request.json()
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
    if tel and tel in clientes:
        est = clientes[tel]
        dados = est.get("dados_pedido", {})

        # Calcula 50%
        modelo = dados.get("modelo", "")
        modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
        preco_base = PRECOS.get(modelo_limpo, "a combinar")
        if dados.get("taxa_urgencia"):
            try:
                total = float(preco_base.replace("R$ ", "").replace(",", ".")) + 5
                preco_base = f"R$ {total:.2f}".replace(".", ",")
            except (ValueError, AttributeError):
                pass
        try:
            valor_str = preco_base.replace("R$ ", "").replace(",", ".")
            metade = float(valor_str) / 2
            metade_str = f"R$ {metade:.2f}".replace(".", ",")
        except (ValueError, AttributeError):
            metade_str = "a combinar"

        # Mensagem natural, como se fosse a Shay escrevendo
        tema = dados.get("tema", dados.get("assunto", "seu slide"))
        msg = (
            f"Oiee! Seu pedido do slide sobre *{tema}* foi aceito, viu? 💜\n\n"
            f"Quer acrescentar mais alguma informação antes "
            f"da gente começar? Se não, sem problemas!\n\n"
            f"Pra confirmar o pedido, precisamos de 50% do valor:\n\n"
            f"💰 {metade_str}\n"
            f"📱 Pix: 38997507651\n"
            f"Shayene Lopes Figueredo\n\n"
            f"Assim que o pagamento for confirmado, "
            f"já começamos a produção! ✨"
        )

        # Envia via ponte interna
        try:
            import requests as req
            req.post("http://127.0.0.1:8080/send",
                     json={"to": tel, "text": msg}, timeout=5)
        except Exception:
            pass

        est["tela"] = "aguardando_pix"
        _salvar_estado_clientes()
        print(f"✅ Painel: pedido de {tel} aceito — aguardando Pix")
        return {"status": "ok", "msg": msg}
    return {"status": "erro"}


@app.post("/painel/cancelar-pedido-cliente")
async def painel_cancelar_pedido_cliente(request: Request):
    """Cancela pedido do cliente (ex: cliente sumiu após pedido aceito)."""
    data = await request.json()
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
    if tel and tel in clientes:
        est = clientes[tel]
        est["tela"] = "menu"
        est["dados_pedido"] = {}
        _salvar_estado_clientes()

        msg = (
            "Seu pedido foi cancelado. 💜\n\n"
            "Se ainda precisar, é só me chamar que "
            "a gente prepara tudo de novo pra você! ✨"
        )
        try:
            import requests as req
            req.post("http://127.0.0.1:8080/send",
                     json={"to": tel, "text": msg}, timeout=5)
        except Exception:
            pass

        print(f"❌ Painel: pedido de {tel} cancelado")
        return {"status": "ok"}
    return {"status": "erro"}


# ── Webhook do Site (Yampi) ──

@app.get("/webhook/site")
async def webhook_site_get():
    """Endpoint GET pra verificar se o webhook esta acessivel."""
    return {
        "status": "ok",
        "msg": "Webhook Yampi ativo! Use POST para enviar pedidos.",
        "url": "https://maya-sly.onrender.com/webhook/site",
    }

@app.post("/webhook/site")
async def webhook_site(request: Request):
    """Recebe eventos do site (Yampi) e processa pedidos pagos."""
    try:
        data = await request.json()
        print(f"📨 Webhook Yampi RECEBIDO: {json.dumps(data, ensure_ascii=False)[:800]}")

        # Detecta o tipo de evento em varios campos possiveis
        evento = str(
            data.get("event") or data.get("type") or
            data.get("hook", {}).get("event") or
            data.get("action") or ""
        ).lower()

        # Só ignora eventos claramente nao relacionados a pedido pago
        ignorar = ["abandoned", "abandonado", "cart.", "denied", "negado",
                    "recusado", "nota fiscal", "cashback", "endereco", "estoque"]
        if any(p in evento for p in ignorar):
            print(f"🛒 Yampi ignorado ({evento})")
            return {"status": "ignored", "evento": evento}

        # Tenta extrair dados do pedido de varios formatos possiveis
        order = data.get("order") or data.get("data") or data

        # Se tem 'resource' no payload do Yampi, usa ele
        if "resource" in data:
            resource = data["resource"]
            if isinstance(resource, dict):
                order = resource
            elif isinstance(resource, str):
                try:
                    order = json.loads(resource)
                except:
                    order = data

        # Nome do cliente
        customer = order.get("customer") or data.get("customer") or {}
        nome = (
            customer.get("name") or customer.get("full_name") or
            order.get("client_name") or order.get("nome") or
            order.get("billing", {}).get("name") or
            order.get("billing_address", {}).get("name") or
            "Site"
        )

        # Produto comprado
        items = order.get("items") or order.get("products") or order.get("line_items") or []
        produto = ""
        if items and len(items) > 0:
            item = items[0]
            produto = (
                item.get("name") or item.get("title") or
                item.get("product_name") or item.get("description") or ""
            )
        if not produto:
            produto = (
                order.get("produto") or order.get("product_name") or
                order.get("product") or order.get("title") or ""
            )
        if not produto:
            produto = "Slide"

        # Valor: tenta varios campos e formatos
        valor = 0.0
        valor_campos = [
            order.get("total"), order.get("amount"), order.get("total_price"),
            order.get("valor"), order.get("grand_total"), order.get("order_total"),
        ]
        for v in valor_campos:
            if v is not None and v != 0:
                try:
                    if isinstance(v, str):
                        v = v.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    valor = float(v)
                    if valor > 0:
                        break
                except (ValueError, TypeError):
                    continue

        # Se nao achou, tenta dos items
        if valor <= 0:
            for item in items:
                for f in ["price", "total", "unit_price", "subtotal"]:
                    try:
                        v = item.get(f)
                        if v:
                            if isinstance(v, str):
                                v = v.replace("R$", "").replace(".", "").replace(",", ".").strip()
                            valor = float(v)
                            if valor > 0:
                                break
                    except (ValueError, TypeError):
                        continue
                if valor > 0:
                    break

        # Status do pagamento — mais flexivel
        status_pg = str(
            order.get("status") or order.get("payment_status") or
            order.get("financial_status") or order.get("state") or
            evento or ""
        ).lower()
        pago = any(p in status_pg for p in [
            "paid", "pago", "approved", "aprovado", "completed", "complete",
            "authorized", "autorizado", "processing", "processando",
            "waiting_payment", "aguardando_pagamento", "pending",
        ])

        # Só ignora se NAO parece pago E valor zerado
        if not pago and valor <= 0:
            print(f"🛒 Yampi ignorado: evento={evento}, status={status_pg}, valor={valor}, produto={produto}")
            return {"status": "skipped", "evento": evento, "status_pg": status_pg}

        if valor <= 0:
            print(f"⚠️ Pedido site com valor R$0: {nome} — {produto} (evento={evento}, status={status_pg})")
            return {"status": "ignored", "motivo": "valor zerado"}

        from backend.pedidos import adicionar, hoje_str, mes_atual

        # Ignora pedidos de teste (Shayene e Samuel Amorim)
        nome_lower = (nome or "").lower()
        if any(t in nome_lower for t in ["shayene", "samuel amorim", "shay figueredo"]):
            print(f"🛒 Yampi ignorado (teste): {nome}")
            return {"status": "ignored", "motivo": "pedido de teste"}

        # Remove "Modelo – " e "Slide – " do prefixo pra nome mais limpo
        produto_limpo = produto.strip()
        for prefix in ["modelo – ", "modelo - ", "slide – ", "slide - ",
                        "modelo ", "slide "]:
            if produto_limpo.lower().startswith(prefix):
                produto_limpo = produto_limpo[len(prefix):].strip()
                break

        # Detecta se é modelo ou slide
        is_modelo = any(p in produto.lower() for p in ["modelo", "tema", "template"])

        mes = mes_atual()
        data_hoje = hoje_str()
        adicionar({
            "cliente": nome or "Site",
            "arquivo": f"Modelo Site — {produto_limpo}" if is_modelo else f"Slide Site — {produto_limpo}",
            "tema": produto_limpo,
            "valor": f"R$ {valor:.2f}".replace(".", ","),
            "situacao": "Pago (Site)",
            "pg": "Pago",
            "responsavel": "SF",
            "origem": "site",
            "mes": mes,
            "data": data_hoje,
            "entrega": data_hoje,
        })
        # Atualiza faturamento do site no mes atual
        from backend.pedidos import _carregar, _salvar
        db = _carregar()
        atual = float(db.get("faturamento_site", {}).get(str(mes), 0))
        db.setdefault("faturamento_site", {})[str(mes)] = round(atual + valor, 2)
        _salvar(db)
        print(f"✅ Pedido site ADICIONADO: {nome} — {produto_limpo} — R$ {valor:.2f} (evento={evento})")
        return {"status": "ok", "cliente": nome, "produto": produto_limpo, "valor": valor}
    except Exception as e:
        import traceback
        print(f"⚠️ Erro webhook site: {e}")
        traceback.print_exc()
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
    """Retorna pedidos com entrega para hoje (usa API de tempo real)."""
    from backend.pedidos import _carregar, hoje_str
    hoje = hoje_str()
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
    tel_data = data.get("telefone", "")
    tel = _encontrar_chave_cliente(tel_data) if tel_data else ""
    if tel:
        # Pega so o numero (sem @lid) pra enviar
        nr_limpo = tel.replace("@lid", "").replace("@s.whatsapp.net", "")
        msg = (
            "Oie! Quer continuar o seu pedido? 💜\n"
            "Se preferir, posso chamar um de nossos atendentes "
            "para continuar a conversa com voce."
        )
        try:
            import requests as _req
            _req.post("http://127.0.0.1:8080/send",
                     json={"to": nr_limpo, "text": msg}, timeout=5)
            print(f" Cutucando {tel}")
        except Exception:
            pass
        return {"status": "ok"}
    return {"status": "erro"}


@app.post("/painel/finalizar")
async def painel_finalizar(request: Request):
    """Finaliza atendimento de um cliente manualmente."""
    data = await request.json()
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
    if tel and tel in clientes:
        clientes[tel]["tela"] = "menu"
        clientes[tel]["dados_pedido"] = {}
        clientes[tel]["shay_respondeu"] = False
        clientes[tel].pop("shay_assumiu", None)
        clientes[tel].pop("bloqueio_permanente", None)
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
    tel = _encontrar_chave_cliente(data.get("telefone", ""))
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
        prazo = dados.get("prazo", "")
        pedido_data = {
            "cliente": tel,
            "arquivo": dados.get("modelo", ""),
            "tema": dados.get("tema", dados.get("assunto", "")),
            "valor": preco_base,
            "situacao": "Novo",
            "pg": "50% pago",
            "responsavel": "SF",
            "origem": "whatsapp",
        }
        if prazo:
            pedido_data["data"] = prazo
            pedido_data["entrega"] = prazo
        adicionar(pedido_data)
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


# ── EXTRATOR DE PEDIDOS POR IA ──

@app.post("/painel/extrair-pedido")
async def painel_extrair_pedido(request: Request):
    """Extrai dados do pedido de uma conversa via IA.
    Recebe um numero de telefone e retorna os dados estruturados do pedido.
    Primeiro tenta usar dados_pedido ativos, depois analisa o historico com IA."""
    data = await request.json()
    telefone_raw = data.get("telefone", "").strip()
    if not telefone_raw:
        return {"status": "erro", "msg": "Informe o numero do telefone"}

    # Normaliza o numero
    import re as _re4
    tel = _re4.sub(r'[@:].*$', '', telefone_raw)
    tel = _re4.sub(r'[^\d]', '', tel)
    if not tel.startswith('55') and len(tel) >= 10:
        tel = '55' + tel

    # Encontra a chave real no dicionario
    chave = _encontrar_chave_cliente(tel)
    if chave not in clientes:
        return {"status": "erro", "msg": f"Cliente {tel} nao encontrado nas conversas ativas. O historico pode ter expirado."}

    est = clientes[chave]
    dados = est.get("dados_pedido", {})
    historico = est.get("historico_ia", [])

    # Se tem dados_pedido completos, usa eles direto
    if dados.get("tema") and dados.get("modelo"):
        modelo = dados.get("modelo", "")
        modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
        preco = PRECOS.get(modelo_limpo, "")
        return {
            "status": "ok",
            "fonte": "dados_ativos",
            "pedido": {
                "cliente": chave,
                "tema": dados.get("tema", dados.get("assunto", "")),
                "arquivo": modelo,
                "prazo": dados.get("prazo", ""),
                "nomes": dados.get("nomes", ""),
                "extras": dados.get("extras", ""),
                "valor": preco,
            }
        }

    # Tenta extrair do historico com IA
    if not historico:
        return {"status": "erro", "msg": "Sem historico de conversa disponivel para este cliente."}

    try:
        from app.config import cliente, MODELO

        # Monta o prompt de extracao
        conversa = ""
        for h in historico[-30:]:  # ultimas 30 mensagens
            papel = "Cliente" if h["role"] == "user" else "Maya"
            conversa += f"{papel}: {h['content'][:500]}\n"

        prompt = f"""Analise a conversa abaixo entre um cliente e a Maya (atendente virtual da Sly Design).
Extraia as informações do pedido de slide no formato JSON.

Conversa:
{conversa}

Retorne APENAS um JSON com estes campos (use string vazia se nao encontrado):
{{
  "tema": "assunto do slide",
  "arquivo": "tipo de slide (ex: 🎬 Canva (Transições), 🎬 PowerPoint (Transições), 🎨 Canva Temas, 🎨 PPTX Temas, 📄 PDF)",
  "prazo": "data ou prazo de entrega",
  "nomes": "nomes que vao no slide ou 'Não'",
  "extras": "informacoes extras, resumo, conteudo adicional",
  "valor": "preco (ex: R$ 25,00)"
}}

IMPORTANTE:
- O tipo de slide (arquivo) deve ser EXATAMENTE um destes: "🎬 Canva (Transições)", "🎬 PowerPoint (Transições)", "🎨 Canva Temas", "🎨 PPTX Temas", "📄 PDF"
- Se o cliente mencionou "transições" ou "transicoes", o tipo é Canva ou PowerPoint (Transições)
- Se mencionou "temas" ou um tema visual (Netflix, Spotify, etc), é Temas
- Precos padrao: PDF R$ 20,00 | Canva Transições R$ 25,00 | PPT Transições R$ 35,00 | Canva Temas R$ 28,00 | PPTX Temas R$ 38,00"""

        resposta = cliente.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": "Voce e um extrator de dados. Retorne APENAS JSON valido, sem texto adicional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
        )

        texto = resposta.choices[0].message.content.strip()
        # Limpa markdown code blocks se houver
        if texto.startswith("```"):
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]
        texto = texto.strip()

        import json as _json
        dados_extraidos = _json.loads(texto)

        return {
            "status": "ok",
            "fonte": "ia_historico",
            "pedido": {
                "cliente": chave,
                "tema": dados_extraidos.get("tema", ""),
                "arquivo": dados_extraidos.get("arquivo", ""),
                "prazo": dados_extraidos.get("prazo", ""),
                "nomes": dados_extraidos.get("nomes", ""),
                "extras": dados_extraidos.get("extras", ""),
                "valor": dados_extraidos.get("valor", ""),
            }
        }
    except Exception as e:
        print(f"⚠️ Erro ao extrair pedido com IA: {e}")
        return {"status": "erro", "msg": f"Erro ao analisar conversa: {str(e)}"}


# ═══════════════════════════════════════════
# THREAD DE VERIFICAÇÃO — envia boas-vindas atrasadas (10s)
# ═══════════════════════════════════════════
import threading

def _thread_verificar_pendentes():
    """Verifica clientes em aguardando_primeira_msg e envia resposta após 10s."""
    while True:
        time.sleep(3)
        agora = time.time()
        for tel, est in list(clientes.items()):
            if est.get("tela") == "aguardando_primeira_msg":
                if agora - est.get("primeira_msg_ts", 0) >= 10:
                    # Processa as mensagens acumuladas e envia resposta
                    resposta = _processar_primeiras_mensagens(est, tel)
                    if resposta:
                        try:
                            nr_limpo = tel.replace("@lid", "").replace("@s.whatsapp.net", "")
                            requests.post("http://127.0.0.1:8080/send",
                                         json={"to": nr_limpo, "text": resposta}, timeout=5)
                            print(f"⏰ Boas-vindas atrasadas enviadas para {tel}")
                        except Exception as e:
                            print(f"⚠️ Erro ao enviar boas-vindas atrasadas: {e}")
                    _salvar_estado_clientes()


if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("🤖 Maya — Atendente Sly Design 💜")
    print("   Webhook WhatsApp rodando em http://localhost:8000")
    print("=" * 55)
    # Inicia thread de verificação de pendentes (boas-vindas atrasadas)
    _thread_pendentes = threading.Thread(target=_thread_verificar_pendentes, daemon=True)
    _thread_pendentes.start()
    print("⏰ Thread de verificação de pendentes iniciada")
    uvicorn.run(app, host="0.0.0.0", port=8000)

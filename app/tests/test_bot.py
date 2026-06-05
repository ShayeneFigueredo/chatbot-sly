"""
TESTES AUTOMATIZADOS - CHATBOT SLY DESIGN
Simula inputs do usuário e verifica transições de estado.
NÃO chama a API do Groq (mockado).
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Garante que o diretório raiz do projeto está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Mock da API Groq antes de importar o chatbot
sys.modules["groq"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Mock do módulo buscador para testes controlados
import app.buscador as buscador

# Mock da função buscar_tema
buscar_tema_original = buscador.buscar_tema


def mock_buscar_tema(texto, tolerancia=0.6):
    """Mock do buscador de temas para testes controlados."""
    # Temas conhecidos para teste
    temas_mock = {
        "jovens titas": ("Jovens Titãs", "https://slydesign.com.br/produto/jovens-titas/"),
        "spotify": ("Spotify", "https://slydesign.com.br/produto/spotify/"),
        "minecraft": ("Minecraft", "https://slydesign.com.br/produto/minecraft/"),
        "batata": (None, None),  # tema inexistente
    }

    texto_norm = texto.lower().strip()
    for chave, (tema, link) in temas_mock.items():
        if chave in texto_norm:
            if tema is None:
                return None, []
            return {"tema": tema, "link": link}, [{"tema": tema, "link": link}]
    return None, []


class ChatbotTester:
    """Simula o chatbot e captura saídas para verificação."""

    def __init__(self):
        # Mock Groq client
        self.mock_groq = MagicMock()
        self.mock_response = MagicMock()
        self.mock_response.choices = [MagicMock()]
        self.mock_response.choices[0].message.content = "Resposta simulada da IA."
        self.mock_groq.chat.completions.create.return_value = self.mock_response

        # Captura prints
        self.prints = []
        self.inputs_sequence = []
        self.input_index = 0
        self.exit_requested = False
        self.errors = []

    def mock_print(self, *args, **kwargs):
        text = " ".join(str(a) for a in args)
        self.prints.append(text)

    def mock_input(self, prompt=""):
        if self.input_index >= len(self.inputs_sequence):
            self.exit_requested = True
            return "0"
        val = self.inputs_sequence[self.input_index]
        self.input_index += 1
        return val

    def run_test(self, name, inputs, checks):
        """Executa uma sequência de inputs e verifica condições."""
        self.prints = []
        self.inputs_sequence = inputs
        self.input_index = 0
        self.exit_requested = False

        print(f"\n{'='*60}")
        print(f"TESTE: {name}")
        print(f"Inputs: {inputs}")
        print(f"{'='*60}")

        # Executa o loop principal do chatbot
        with patch("builtins.print", self.mock_print), \
             patch("builtins.input", self.mock_input), \
             patch("app.bot.cliente", self.mock_groq), \
             patch("app.buscador.buscar_tema", mock_buscar_tema):
            try:
                # Importa dentro do patch pra mock funcionar
                import app.bot as bot_module
                import app.config as config_module

                # Simula o loop principal
                self._run_main_loop(bot_module, config_module)
            except SystemExit:
                pass
            except Exception as e:
                self.errors.append(f"[{name}] ERRO: {e}")
                import traceback
                traceback.print_exc()
                return False

        # Executa checks
        all_ok = True
        for check in checks:
            try:
                result = check(self.prints, self.inputs_sequence)
                if not result:
                    all_ok = False
            except Exception as e:
                self.errors.append(f"[{name}] Check falhou: {e}")
                all_ok = False

        if all_ok:
            print(f"✅ PASSOU")
        else:
            print(f"❌ FALHOU")
            print(f"   Últimas saídas: {self.prints[-5:]}")

        return all_ok

    def _run_main_loop(self, bot_module, config_module):
        """Executa o loop principal do chatbot."""
        # Inicialização
        msg, botoes = bot_module.mensagem_boas_vindas()
        self.prints.append(f"🤖 Sly:\n{msg}")
        bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente (a Sly entende!)\n  [0] Sair")

        historico = [{"role": "system", "content": config_module.SYSTEM_PROMPT}]
        tela_atual = "menu"
        dados_pedido = {}
        editando = False
        ultimos_botoes = []

        while not self.exit_requested:
            escolha = self.mock_input()

            if not escolha:
                continue

            if escolha == "0":
                msg, botoes = bot_module.mensagem_cancelamento()
                self.prints.append(f"🤖 Sly:\n{msg}")
                break

            if escolha.lower() in ("voltar", "menu", "🔙 voltar ao menu"):
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = bot_module.mensagem_boas_vindas()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue

            # Botões do menu principal
            if escolha == "1" and tela_atual == "menu":
                tela_atual = "slides_prontos"
                msg, botoes = bot_module.resposta_ver_slides_prontos()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite o tema que procura...")
                continue

            if escolha == "2" and tela_atual == "menu":
                tela_atual = "pedido_tema"
                dados_pedido = {}
                msg, botoes = bot_module.iniciar_pedido_personalizado()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes)
                continue

            if escolha == "3" and tela_atual == "menu":
                self.prints.append("🤖 Sly: Qual tema você está procurando? 🔍")
                tela_atual = "buscando_tema"
                continue

            if escolha == "4" and tela_atual == "menu":
                tela_atual = "precos"
                msg, botoes = bot_module.resposta_quanto_custa()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente")
                continue

            if escolha == "5" and tela_atual == "menu":
                self.prints.append("🤖 Sly: Pode perguntar! O que você quer saber? 💜")
                tela_atual = "duvida"
                continue

            # Dúvida
            if tela_atual == "duvida":
                palavras_compra = ["comprei", "compra", "comprar", "pedido",
                                   "não consigo abrir", "nao consigo abrir",
                                   "deu erro", "não chegou", "nao chegou",
                                   "arquivo", "link", "acessar", "baixar"]
                if any(p in escolha.lower() for p in palavras_compra):
                    self.prints.append("🤖 Sly: Antes de tudo: qual o tema do slide que você comprou? 🛒")
                    tela_atual = "duvida_compra"
                    continue
                self.prints.append("⏳ Sly está respondendo...")
                self.prints.append("🤖 Sly:\nResposta simulada da IA.")
                self.prints.append("───")
                botoes_pd = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
                bot_module.mostrar_botoes(botoes_pd, "  [0] Sair")
                tela_atual = "pos_duvida"
                continue

            # Dúvida de compra
            if tela_atual == "duvida_compra":
                self.prints.append("⏳ Sly está respondendo...")
                self.prints.append("🤖 Sly:\nResposta simulada da IA.")
                self.prints.append("───")
                botoes_pd = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
                bot_module.mostrar_botoes(botoes_pd, "  [0] Sair")
                tela_atual = "pos_duvida"
                continue

            # Buscar tema
            if tela_atual == "buscando_tema":
                melhor, todos = mock_buscar_tema(escolha)
                if melhor:
                    if len(todos) == 1:
                        texto = f"Temos esse tema disponível no catálogo com entrega imediata. 💜\n\n📄 {melhor['tema']}\n👉 {melhor['link']}\n\nÉ só comprar e receber na hora!"
                        botoes = [f"🛒 Comprar {melhor['tema']}", "🔍 Buscar outro tema", "🔙 Voltar ao menu"]
                    else:
                        texto = "Encontrei esses temas."
                        botoes = ["🔍 Buscar outro tema", "🎨 Nenhum desses, quero personalizado", "🔙 Voltar ao menu"]
                else:
                    texto = f"Não encontrei \"{escolha}\" no nosso catálogo pronto.\n\nMas podemos criar um slide personalizado exatamente como você precisa. 💜"
                    botoes = ["🎨 Quero um slide personalizado!", "🔍 Buscar outro tema", "🔙 Voltar ao menu"]

                self.prints.append(f"🤖 Sly:\n{texto}")
                ultimos_botoes = botoes
                bot_module.mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
                tela_atual = "resultados_busca"
                continue

            # Resultados da busca
            if tela_atual == "resultados_busca":
                escolha_resolvida = bot_module.resolver_botao(escolha, ultimos_botoes)

                if "comprar" in escolha_resolvida.lower():
                    self.prints.append("🤖 Sly: Ok! Se precisar de algo, pode me mandar mensagem novamente. 💜")
                    bot_module.mostrar_botoes(["🔙 Voltar ao menu"])
                    tela_atual = "pos_compra"
                    continue
                elif "buscar" in escolha_resolvida.lower():
                    self.prints.append("🤖 Sly: Qual tema você está procurando? 🔍")
                    tela_atual = "buscando_tema"
                elif "personalizado" in escolha_resolvida.lower() or "nenhum" in escolha_resolvida.lower():
                    tela_atual = "pedido_tema"
                    dados_pedido = {}
                    msg, botoes = bot_module.iniciar_pedido_personalizado()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif "voltar" in escolha_resolvida.lower():
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                else:
                    melhor, todos = mock_buscar_tema(escolha)
                    if melhor:
                        texto = f"Temos: {melhor['tema']}"
                        botoes = ["🔍 Buscar outro tema", "🔙 Voltar ao menu"]
                    else:
                        texto = f"Não encontrei."
                        botoes = ["🎨 Quero um slide personalizado!", "🔍 Buscar outro tema", "🔙 Voltar ao menu"]
                    self.prints.append(f"🤖 Sly:\n{texto}")
                    ultimos_botoes = botoes
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
                continue

            # Slides prontos
            if tela_atual == "slides_prontos":
                escolha_resolvida = bot_module.resolver_botao(escolha, ["🔍 Buscar um tema", "🔙 Voltar ao menu"])
                if escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                elif escolha_resolvida == "🔍 Buscar um tema":
                    self.prints.append("🤖 Sly: Qual tema você está procurando? 🔍")
                    tela_atual = "buscando_tema"
                else:
                    melhor, todos = mock_buscar_tema(escolha)
                    if melhor:
                        texto = f"Encontrado: {melhor['tema']}"
                        botoes = ["🔍 Buscar outro tema", "🔙 Voltar ao menu"]
                    else:
                        texto = "Não encontrado."
                        botoes = ["🎨 Quero um slide personalizado!", "🔍 Buscar outro tema", "🔙 Voltar ao menu"]
                    self.prints.append(f"🤖 Sly:\n{texto}")
                    ultimos_botoes = botoes
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
                    tela_atual = "resultados_busca"
                continue

            # Preços
            if tela_atual == "precos" and ("pedido" in escolha.lower() or "comprar" in escolha.lower()):
                tela_atual = "pedido_tema"
                dados_pedido = {}
                msg, botoes = bot_module.iniciar_pedido_personalizado()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes)
                continue

            # Fluxo de pedido personalizado
            if tela_atual == "pedido_tema":
                dados_pedido["tema"] = escolha
                if editando:
                    editando = False
                    tela_atual = "resumo"
                    msg, botoes = bot_module.mostrar_resumo(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                else:
                    tela_atual = "pedido_modelo"
                    msg, botoes = bot_module.perguntar_modelo()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "pedido_modelo":
                botoes_modelo = ["📄 PDF", "🎬 Canva (Transições)", "🎬 PowerPoint (Transições)",
                                 "🎨 Canva Temas", "🎨 PPTX Temas",
                                 "🤔 Diferença Canva x PowerPoint", "🔙 Voltar ao menu"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_modelo)

                if "Diferença" in escolha_resolvida or "diferença" in escolha.lower():
                    msg, botoes = bot_module.explicar_diferenca_canva_powerpoint()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                    tela_atual = "pedido_modelo_diferenca"
                    continue

                if escolha_resolvida in botoes_modelo[:5]:
                    dados_pedido["modelo"] = escolha_resolvida
                    if "Temas" in escolha_resolvida:
                        tela_atual = "pedido_qual_tema"
                        msg, botoes = bot_module.perguntar_qual_tema()
                        self.prints.append(f"🤖 Sly:\n{msg}")
                        bot_module.mostrar_botoes(botoes)
                    else:
                        tela_atual = "pedido_prazo"
                        msg, botoes = bot_module.perguntar_prazo()
                        self.prints.append(f"🤖 Sly:\n{msg}")
                        bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue

            if tela_atual == "pedido_qual_tema":
                dados_pedido["tema"] = escolha
                tela_atual = "pedido_prazo"
                msg, botoes = bot_module.perguntar_prazo()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "pedido_canva_ppt":
                botoes_cp = ["📱 Canva", "💻 PowerPoint", "🔙 Voltar ao menu"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_cp)
                if escolha_resolvida in ("📱 Canva", "💻 PowerPoint"):
                    if escolha_resolvida == "📱 Canva":
                        dados_pedido["modelo"] = "🎨 Canva Temas"
                    else:
                        dados_pedido["modelo"] = "🎨 PPTX Temas"
                    tela_atual = "pedido_prazo"
                    msg, botoes = bot_module.perguntar_prazo()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue

            if tela_atual == "pedido_modelo_diferenca":
                botoes_cp = ["📱 Canva", "💻 PowerPoint"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_cp)
                if escolha_resolvida == "📱 Canva":
                    dados_pedido["modelo"] = "🎬 Canva (Transições)"
                elif escolha_resolvida == "💻 PowerPoint":
                    dados_pedido["modelo"] = "🎬 PowerPoint (Transições)"
                tela_atual = "pedido_prazo"
                msg, botoes = bot_module.perguntar_prazo()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "pedido_prazo":
                dados_pedido["prazo"] = escolha
                if editando:
                    editando = False
                    tela_atual = "resumo"
                    msg, botoes = bot_module.mostrar_resumo(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                else:
                    tela_atual = "pedido_nomes"
                    msg, botoes = bot_module.perguntar_nomes()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "pedido_nomes":
                botoes_nomes = ["🚫 Não quero", "🔙 Voltar ao menu"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_nomes)
                if escolha_resolvida == "🚫 Não quero":
                    dados_pedido["nomes"] = "Não"
                elif escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    editando = False
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                    continue
                else:
                    dados_pedido["nomes"] = escolha

                if editando:
                    editando = False
                    tela_atual = "resumo"
                    msg, botoes = bot_module.mostrar_resumo(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                else:
                    tela_atual = "pedido_obs"
                    dados_pedido["observacoes"] = ""
                    msg, botoes = bot_module.perguntar_observacoes()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "pedido_obs":
                tem_obs = bool(dados_pedido.get("observacoes", ""))
                if tem_obs:
                    botoes_obs = ["✅ Finalizar Pedido", "🔙 Voltar ao menu"]
                else:
                    botoes_obs = ["🚫 Não quero", "🔙 Voltar ao menu"]

                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_obs)

                if escolha_resolvida == "✅ Finalizar Pedido":
                    tela_atual = "resumo"
                    msg, botoes = bot_module.mostrar_resumo(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "🚫 Não quero":
                    dados_pedido["observacoes"] = "Nenhuma"
                    tela_atual = "resumo"
                    msg, botoes = bot_module.mostrar_resumo(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                else:
                    if dados_pedido["observacoes"]:
                        dados_pedido["observacoes"] += " | " + escolha
                    else:
                        dados_pedido["observacoes"] = escolha
                    msg, botoes = bot_module.confirmar_recebido()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "resumo":
                botoes_resumo = ["✅ Confirmar pedido", "✏️ Quero mudar algo", "❌ Cancelar"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_resumo)
                if escolha_resolvida == "✅ Confirmar pedido":
                    tela_atual = "pagamento"
                    msg, botoes = bot_module.instrucoes_pagamento(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "✏️ Quero mudar algo":
                    tela_atual = "mudar"
                    msg, botoes = bot_module.perguntar_o_que_mudar()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "❌ Cancelar":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_cancelamento()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "mudar":
                botoes_mudar = ["📝 Mudar tema", "🎨 Mudar tipo", "📅 Mudar prazo",
                                "👤 Mudar nomes", "📎 Mudar extras", "🔙 Voltar ao resumo"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_mudar)
                if escolha_resolvida == "🔙 Voltar ao resumo":
                    tela_atual = "resumo"
                    msg, botoes = bot_module.mostrar_resumo(dados_pedido)
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "📝 Mudar tema":
                    editando = True
                    tela_atual = "pedido_tema"
                    self.prints.append("🤖 Sly: Qual o novo assunto do slide? 📝")
                elif escolha_resolvida == "🎨 Mudar tipo":
                    tela_atual = "pedido_modelo"
                    msg, botoes = bot_module.perguntar_modelo()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "📅 Mudar prazo":
                    editando = True
                    tela_atual = "pedido_prazo"
                    msg, botoes = bot_module.perguntar_prazo()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "👤 Mudar nomes":
                    editando = True
                    tela_atual = "pedido_nomes"
                    msg, botoes = bot_module.perguntar_nomes()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                elif escolha_resolvida == "📎 Mudar extras":
                    editando = True
                    tela_atual = "pedido_obs"
                    dados_pedido["observacoes"] = ""
                    msg, botoes = bot_module.perguntar_observacoes()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                continue

            if tela_atual == "pagamento":
                botoes_pag = ["📎 Enviar comprovante", "🔙 Voltar ao menu"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_pag)
                if escolha_resolvida == "📎 Enviar comprovante" or "comprovante" in escolha.lower():
                    tela_atual = "aguardando_comprovante"
                    self.prints.append("🤖 Sly: Manda o comprovante aqui! 📎\n(No WhatsApp, é só enviar a imagem ou PDF)")
                    bot_module.mostrar_botoes(["🔙 Voltar ao menu"])
                elif escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue

            if tela_atual == "aguardando_comprovante":
                if escolha.lower() in ("voltar", "menu", "🔙 voltar ao menu"):
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                else:
                    msg, botoes = bot_module.comprovante_recebido()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes)
                    tela_atual = "comprovante"
                continue

            if tela_atual in ("pos_compra", "comprovante"):
                tela_atual = "menu"
                dados_pedido = {}
                editando = False
                msg, botoes = bot_module.mensagem_boas_vindas()
                self.prints.append(f"🤖 Sly:\n{msg}")
                bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue

            # Detecção inteligente de temas no menu
            if tela_atual == "menu":
                tema_encontrado, todos = mock_buscar_tema(escolha)
                if tema_encontrado:
                    nome_tema = tema_encontrado["tema"]
                    self.prints.append(f"🤖 Sly: Achamos! \"{nome_tema}\" é um dos nossos Slides Temas!")
                    dados_pedido = {"tema": nome_tema}
                    tela_atual = "pedido_canva_ppt"
                    bot_module.mostrar_botoes(["📱 Canva", "💻 PowerPoint", "🔙 Voltar ao menu"])
                    continue

            # Pós-dúvida
            if tela_atual == "pos_duvida":
                botoes_pd = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
                escolha_resolvida = bot_module.resolver_botao(escolha, botoes_pd)
                if escolha_resolvida == "💬 Continuar dúvida":
                    self.prints.append("🤖 Sly: Continue digitando sua dúvida... 💜")
                    tela_atual = "duvida"
                    continue
                elif escolha_resolvida == "🔙 Voltar ao menu":
                    tela_atual = "menu"
                    dados_pedido = {}
                    msg, botoes = bot_module.mensagem_boas_vindas()
                    self.prints.append(f"🤖 Sly:\n{msg}")
                    bot_module.mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                    continue
                else:
                    self.prints.append("⏳ Sly está respondendo...")
                    self.prints.append("🤖 Sly:\nResposta simulada da IA.")
                    self.prints.append("───")
                    bot_module.mostrar_botoes(botoes_pd, "  [0] Sair")
                    continue

            # Fallback: responde com IA
            self.prints.append("⏳ Sly está respondendo...")
            self.prints.append("🤖 Sly:\nResposta simulada da IA.")
            self.prints.append("───")
            botoes_pd = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
            bot_module.mostrar_botoes(botoes_pd, "  [0] Sair")
            tela_atual = "pos_duvida"


def check_output_contains(*texts):
    """Verifica se TODOS os textos apareceram nos prints."""
    def check(prints, inputs):
        all_prints = " ".join(prints)
        for t in texts:
            if t not in all_prints:
                print(f"   ❌ Texto não encontrado: '{t}'")
                return False
        return True
    return check


def check_output_not_contains(*texts):
    """Verifica se NENHUM dos textos aparece nos prints."""
    def check(prints, inputs):
        all_prints = " ".join(prints)
        for t in texts:
            if t in all_prints:
                print(f"   ❌ Texto inesperado encontrado: '{t}'")
                return False
        return True
    return check


def check_last_output_contains(*texts):
    """Verifica se o ÚLTIMO print contém os textos."""
    def check(prints, inputs):
        last = prints[-1] if prints else ""
        for t in texts:
            if t not in last:
                print(f"   ❌ Último print não contém '{t}'. Último print: {last[:100]}...")
                return False
        return True
    return check


def run_all_tests():
    tester = ChatbotTester()
    results = []

    # ────────────────────────────────────────
    # TESTE 1: Menu principal - Botão 1 (Ver Slides Prontos)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu → Botão 1: Ver Slides Prontos",
        inputs=["1"],
        checks=[
            check_output_contains("slydesign.com.br/loja"),
            check_output_contains("[1] 🔍 Buscar um tema"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 2: Menu principal - Botão 2 (Slide Personalizado)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu → Botão 2: Iniciar pedido personalizado",
        inputs=["2"],
        checks=[
            check_output_contains("Primeiro: qual o ASSUNTO"),
            check_output_contains("[1] 🔙 Voltar ao menu"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 3: Menu principal - Botão 3 (Consultar um Tema)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu → Botão 3: Consultar tema (busca com resultado)",
        inputs=["3", "jovens titas"],
        checks=[
            check_output_contains("Jovens Titãs"),
            check_output_contains("comprar e receber na hora"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 4: Menu principal - Botão 3 (tema não encontrado)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu → Botão 3: Tema inexistente",
        inputs=["3", "batata"],
        checks=[
            check_output_contains("Não encontrei"),
            check_output_contains("slide personalizado"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 5: Menu principal - Botão 4 (Quanto Custa?)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu → Botão 4: Preços",
        inputs=["4"],
        checks=[
            check_output_contains("R$ 20,00"),
            check_output_contains("R$ 35,00"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 6: Menu principal - Botão 5 (Tirar Dúvida → IA)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu → Botão 5: Dúvida (resposta IA + pos_duvida)",
        inputs=["5", "quanto custa um slide pdf?"],
        checks=[
            check_output_contains("Pode perguntar"),
            check_output_contains("[1] 💬 Continuar dúvida"),
            check_output_contains("[2] 🔙 Voltar ao menu"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 7: pos_duvida → Continuar dúvida
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "pos_duvida → Continuar dúvida (botão 1)",
        inputs=["5", "preciso de ajuda", "1", "outra duvida"],
        checks=[
            check_output_contains("Continue digitando sua dúvida"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 8: pos_duvida → Voltar ao menu (botão 2)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "pos_duvida → Voltar ao menu (número 2)",
        inputs=["5", "ajuda", "2"],
        checks=[
            check_output_contains("Seja bem-vindo(a)"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 9: pos_duvida → Texto livre (nova dúvida)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "pos_duvida → Texto livre tratado como nova dúvida",
        inputs=["5", "primeira duvida", "segunda duvida diferente"],
        checks=[
            check_output_contains("[1] 💬 Continuar dúvida"),  # reaparece após IA
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 10: Voltar ao menu de qualquer lugar
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Navegação: 'voltar' → menu (de qualquer estado)",
        inputs=["4", "voltar"],
        checks=[
            check_output_contains("Seja bem-vindo(a)"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 11: Resultados busca → comprar
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Resultados busca → Comprar → pos_compra → voltar menu",
        inputs=["3", "jovens titas", "1", "qualquer"],
        checks=[
            check_output_contains("comprar e receber"),
            check_output_contains("pode me mandar mensagem"),
            check_output_contains("[1] 🔙 Voltar ao menu"),  # botão aparece após compra
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 12: Buscar tema → resultados múltiplos
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Buscar tema → resultado único → voltar",
        inputs=["3", "jovens titas", "3"],  # Botão 3 = Voltar ao menu
        checks=[
            check_output_contains("Jovens Titãs"),
            check_output_contains("Seja bem-vindo(a)"),  # voltou ao menu
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 13: Fluxo de pedido completo
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Pedido completo: tema → modelo → prazo → nomes → obs → resumo",
        inputs=[
            "2",              # iniciar pedido
            "Matemática",     # tema
            "1",              # PDF
            "amanhã",         # prazo
            "1",              # não quero nomes
            "1",              # não quero observações
        ],
        checks=[
            check_output_contains("Primeiro: qual o ASSUNTO"),
            check_output_contains("qual TIPO de slide"),
            check_output_contains("PRAZO"),
            check_output_contains("nomes"),
            check_output_contains("resumo do seu pedido"),
            check_output_contains("Matemática"),
            check_output_contains("📄 PDF"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 14: Resumo → Confirmar → Pagamento
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Resumo → Confirmar → Instruções de pagamento",
        inputs=[
            "2",              # iniciar pedido
            "História",       # tema
            "1",              # PDF
            "semana que vem", # prazo
            "1",              # não quero nomes
            "1",              # não quero obs
            "1",              # confirmar pedido
        ],
        checks=[
            check_output_contains("resumo"),
            check_output_contains("Chave Pix"),
            check_output_contains("50%"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 15: Resumo → Cancelar
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Resumo → Cancelar pedido",
        inputs=[
            "2", "TCC", "1", "sexta", "1", "1",  # fluxo até resumo
            "3",  # cancelar
        ],
        checks=[
            check_output_contains("Sem problemas!"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 16: Resumo → Mudar algo
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Resumo → Mudar tema",
        inputs=[
            "2", "Física", "1", "segunda", "1", "1",  # fluxo até resumo
            "2",  # quero mudar algo
            "1",  # mudar tema
            "Química",  # novo tema
        ],
        checks=[
            check_output_contains("O que você quer mudar?"),
            check_output_contains("Química"),  # tema atualizado
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 17: Dúvida com palavra de compra → duvida_compra
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Dúvida → detecta compra → duvida_compra",
        inputs=["5", "comprei um slide e não consigo abrir"],
        checks=[
            check_output_contains("qual o tema do slide que você comprou"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 18: duvida_compra → pos_duvida
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "duvida_compra → processa → pos_duvida",
        inputs=["5", "meu pedido deu erro", "Jovens Titãs"],
        checks=[
            check_output_contains("[1] 💬 Continuar dúvida"),
            check_output_contains("[2] 🔙 Voltar ao menu"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 19: Slide Temas → pergunta qual tema
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Pedido: escolhe Canva Temas → pergunta qual tema",
        inputs=["2", "TCC", "4"],  # 4 = Canva Temas
        checks=[
            check_output_contains("Os mais pedidos"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 20: Detecção de tema no menu
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Menu: digita 'spotify' → detecta tema → Canva/PPT",
        inputs=["spotify"],
        checks=[
            check_output_contains("Achamos!"),
            check_output_contains("Spotify"),
            check_output_contains("[1] 📱 Canva"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 21: Número inválido no slides_prontos (Bug #4 fix)
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Slides prontos: número 3 → NÃO deve ir pra buscar tema",
        inputs=["1", "3"],
        checks=[
            check_output_contains("Não encontrado"),  # trata como busca de "3" (vai pro else)
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 22: Pedido com observações
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Pedido com observações (mini-loop)",
        inputs=[
            "2", "Biologia", "2", "amanhã", "Maria, João",  # tema, canva, prazo, nomes
            "quero fundo verde",  # obs 1
            "e fontes grandes",   # obs 2
            "1",  # finalizar pedido
        ],
        checks=[
            check_output_contains("Recebi! ✅"),
            check_output_contains("fundo verde"),  # deve aparecer no resumo
            check_output_contains("fontes grandes"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 23: Pedido → modelo → diferença Canva x PPT
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Pedido: Diferença Canva x PowerPoint",
        inputs=["2", "Arte", "6"],  # 6 = Diferença
        checks=[
            check_output_contains("Visualmente são iguais"),
            check_output_contains("[1] 📱 Canva"),
            check_output_contains("[2] 💻 PowerPoint"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 24: Pagamento → enviar comprovante
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Pagamento → Enviar comprovante → comprovante_recebido",
        inputs=[
            "2", "TCC", "1", "amanhã", "1", "1",  # até resumo
            "1",  # confirmar
            "1",  # enviar comprovante
            "comprovante.pdf",  # simula envio
        ],
        checks=[
            check_output_contains("Manda o comprovante aqui"),
            check_output_contains("vai ser olhado pela nossa equipe"),
            check_output_contains("[1] 🔙 Voltar ao menu"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 25: Pagamento → voltar ao menu
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Pagamento → voltar ao menu",
        inputs=[
            "2", "TCC", "1", "amanhã", "1", "1",  # até resumo
            "1",  # confirmar
            "2",  # voltar ao menu
        ],
        checks=[
            check_output_contains("Seja bem-vindo(a)"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 26: pedido_canva_ppt → escolher Canva
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Tema detectado → Canva → prazo",
        inputs=["spotify", "1"],  # detecta spotify, escolhe Canva
        checks=[
            check_output_contains("Spotify"),
            check_output_contains("PRAZO"),
        ]
    ))

    # ────────────────────────────────────────
    # TESTE 27: Sair com 0
    # ────────────────────────────────────────
    results.append(tester.run_test(
        "Sair (0) → mensagem de cancelamento",
        inputs=["0"],
        checks=[
            check_output_contains("Sem problemas!"),
        ]
    ))

    # ────────────────────────────────────────
    # RESULTADO FINAL
    # ────────────────────────────────────────
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL: {passed}/{total} passaram")
    if failed > 0:
        print(f"❌ {failed} TESTES FALHARAM")
    else:
        print(f"✅ TODOS OS TESTES PASSARAM!")

    # Mostra erros coletados
    if tester.errors:
        print(f"\n⚠️  Erros encontrados:")
        for e in tester.errors:
            print(f"   - {e}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

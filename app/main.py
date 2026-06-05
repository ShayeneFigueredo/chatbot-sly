"""
main.py — Ponto de entrada do chatbot Maya da Sly Design.
Execute com: python -m app.main   ou   python app/main.py
"""
from app.config import cliente, MODELO, SYSTEM_PROMPT
from app.bot import (
    mensagem_boas_vindas,
    resposta_ver_slides_prontos,
    resposta_quanto_custa,
    resposta_busca_tema,
    resposta_ia_livre,
    iniciar_pedido_personalizado,
    perguntar_modelo,
    perguntar_qual_tema,
    perguntar_canva_ou_powerpoint,
    explicar_diferenca_canva_powerpoint,
    perguntar_prazo,
    aviso_taxa_mesmo_dia,
    perguntar_nomes,
    perguntar_observacoes,
    confirmar_recebido,
    mostrar_resumo,
    perguntar_o_que_mudar,
    instrucoes_pagamento,
    comprovante_recebido,
    mensagem_cancelamento,
    mostrar_botoes,
    resolver_botao,
)
from app.buscador import buscar_tema
from app.nlp import detectar_intencao
from app.memoria import (
    carregar_conversa,
    bot_falou,
    cliente_falou,
    resumir_se_precisar,
)


def main():
    """Loop principal do chatbot Maya (versão terminal)."""
    print("=" * 55)
    print("🤖 Maya — Atendente Sly Design 💜")
    print("   (versão terminal — os botões simulam o WhatsApp)")
    print("=" * 55)

    # ── Tenta carregar conversa salva ──
    historico_salvo, tela_salva, pedido_salvo = carregar_conversa()
    if historico_salvo:
        print(f"\n💾 [Conversa anterior carregada! {len(historico_salvo)} mensagens]")
        historico = historico_salvo
        tela_atual = tela_salva
        dados_pedido = pedido_salvo
        if tela_atual == "menu":
            msg, botoes = mensagem_boas_vindas()
            print(f"\n🤖 Maya:\n{msg}\n")
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente (a Maya entende!)\n  [0] Sair")
        else:
            print(f"\n🤖 Maya: Continuando de onde paramos... (tela: {tela_atual}) 💜")
            print(f"   Última mensagem: {historico[-1]['content'][:80]}...")
    else:
        msg, botoes = mensagem_boas_vindas()
        print(f"\n🤖 Maya:\n{msg}\n")
        mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente (a Maya entende!)\n  [0] Sair")
        historico = [{"role": "system", "content": SYSTEM_PROMPT}]
        tela_atual = "menu"
        dados_pedido = {}

    editando = False
    ultimos_botoes = []

    while True:
        escolha = input("\n▶️  Você: ").strip()

        if not escolha:
            continue

        # ── Guarda no histórico ──
        if not escolha.isdigit() or escolha == "0":
            cliente_falou(historico, escolha, tela_atual, dados_pedido)

        if escolha == "0":
            msg, botoes = mensagem_cancelamento()
            print(f"\n🤖 Maya:\n{msg}\n")
            break

        if escolha.lower() in ("voltar", "menu", "🔙 voltar ao menu"):
            tela_atual = "menu"
            dados_pedido = {}
            msg, botoes = mensagem_boas_vindas()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            continue

        # ── BOTÃO 1: Ver Slides Prontos ──
        if escolha == "1" and tela_atual == "menu":
            tela_atual = "slides_prontos"
            msg, botoes = resposta_ver_slides_prontos()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou digite o tema que procura...")
            continue

        # ── BOTÃO 2: Quero um Slide Personalizado ──
        if escolha == "2" and tela_atual == "menu":
            tela_atual = "pedido_tema"
            dados_pedido = {}
            msg, botoes = iniciar_pedido_personalizado()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes)
            continue

        # ── BOTÃO 3: Consultar um Tema ──
        if escolha == "3" and tela_atual == "menu":
            msg_busca = "Qual tema você está procurando? 🔍"
            print(f"\n🤖 Maya: {msg_busca}")
            bot_falou(historico, msg_busca, tela_atual, dados_pedido)
            tela_atual = "buscando_tema"
            continue

        # ── BOTÃO 4: Quanto Custa? ──
        if escolha == "4" and tela_atual == "menu":
            tela_atual = "precos"
            msg, botoes = resposta_quanto_custa()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente")
            continue

        # ── BOTÃO 5: Tirar Dúvida ──
        if escolha == "5" and tela_atual == "menu":
            msg_duvida = "Pode perguntar! O que você quer saber? 💜"
            print(f"\n🤖 Maya: {msg_duvida}")
            bot_falou(historico, msg_duvida, tela_atual, dados_pedido)
            tela_atual = "duvida"
            continue

        # ── Tela de dúvida ──
        if tela_atual == "duvida":
            palavras_compra = ["comprei", "compra", "comprar", "pedido",
                               "não consigo abrir", "nao consigo abrir",
                               "deu erro", "não chegou", "nao chegou",
                               "arquivo", "link", "acessar", "baixar"]
            if any(p in escolha.lower() for p in palavras_compra):
                msg_compra = "Antes de tudo: qual o tema do slide que você comprou? 🛒"
                print(f"\n🤖 Maya: {msg_compra}")
                bot_falou(historico, msg_compra, tela_atual, dados_pedido)
                tela_atual = "duvida_compra"
                continue
            print("\n⏳ Maya está pensando... 💭")
            historico = resumir_se_precisar(historico)
            texto_ia, historico = resposta_ia_livre(escolha, historico)
            print(f"\n🤖 Maya:\n{texto_ia}")
            bot_falou(historico, texto_ia, tela_atual, dados_pedido)
            print("\n───")
            botoes_pos_duvida = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
            mostrar_botoes(botoes_pos_duvida, "  [0] Sair")
            tela_atual = "pos_duvida"
            continue

        # ── Dúvida de compra ──
        if tela_atual == "duvida_compra":
            tema_compra = escolha
            print("\n⏳ Maya está pensando... 💭")
            pergunta_contexto = (
                f"A cliente comprou o slide '{tema_compra}' no site slydesign.com.br "
                f"e está com um problema. Pergunte qual é o problema específico "
                f"e tente ajudar. Lembre-se: slides do site são em Canva ou PowerPoint. "
                f"Se não conseguir resolver, diga que um humano vai atender."
            )
            historico.append({"role": "user", "content": pergunta_contexto})
            historico = resumir_se_precisar(historico)
            resposta = cliente.chat.completions.create(
                model=MODELO,
                messages=historico,
                temperature=0.7,
            )
            texto_ia = resposta.choices[0].message.content
            historico.append({"role": "assistant", "content": texto_ia})
            print(f"\n🤖 Maya:\n{texto_ia}")
            bot_falou(historico, texto_ia, tela_atual, dados_pedido)
            print("\n───")
            botoes_pos_duvida = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
            mostrar_botoes(botoes_pos_duvida, "  [0] Sair")
            tela_atual = "pos_duvida"
            continue

        # ── Buscar tema ──
        if tela_atual == "buscando_tema":
            msg, botoes = resposta_busca_tema(escolha)
            ultimos_botoes = botoes
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
            tela_atual = "resultados_busca"
            continue

        # ── Resultados da busca ──
        if tela_atual == "resultados_busca":
            escolha_resolvida = resolver_botao(escolha, ultimos_botoes)

            if "comprar" in escolha_resolvida.lower():
                msg_pos = "Beleza! Qualquer coisa é só me chamar de novo, tá? 💜"
                print(f"\n🤖 Maya: {msg_pos}")
                bot_falou(historico, msg_pos, tela_atual, dados_pedido)
                mostrar_botoes(["🔙 Voltar ao menu"])
                tela_atual = "pos_compra"
                continue
            elif "buscar" in escolha_resolvida.lower():
                msg_buscar = "Qual tema você está procurando? 🔍"
                print(f"\n🤖 Maya: {msg_buscar}")
                bot_falou(historico, msg_buscar, tela_atual, dados_pedido)
                tela_atual = "buscando_tema"
            elif "personalizado" in escolha_resolvida.lower() or "nenhum" in escolha_resolvida.lower():
                tela_atual = "pedido_tema"
                dados_pedido = {}
                msg, botoes = iniciar_pedido_personalizado()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif "voltar" in escolha_resolvida.lower():
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            else:
                msg, botoes = resposta_busca_tema(escolha)
                ultimos_botoes = botoes
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
            continue

        # ── Slides prontos ──
        if tela_atual == "slides_prontos":
            escolha_resolvida = resolver_botao(escolha, ["🔍 Buscar um tema", "🔙 Voltar ao menu"])
            if escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            elif escolha_resolvida == "🔍 Buscar um tema":
                msg_buscar = "Qual tema você está procurando? 🔍"
                print(f"\n🤖 Maya: {msg_buscar}")
                bot_falou(historico, msg_buscar, tela_atual, dados_pedido)
                tela_atual = "buscando_tema"
            else:
                msg, botoes = resposta_busca_tema(escolha)
                ultimos_botoes = botoes
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
                tela_atual = "resultados_busca"
            continue

        # ── Preços → pedido ──
        if tela_atual == "precos" and ("pedido" in escolha.lower() or "comprar" in escolha.lower()):
            tela_atual = "pedido_tema"
            dados_pedido = {}
            msg, botoes = iniciar_pedido_personalizado()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes)
            continue

        # ── PASSO 1: Tema ──
        if tela_atual == "pedido_tema":
            dados_pedido["tema"] = escolha
            if editando:
                editando = False
                tela_atual = "resumo"
                msg, botoes = mostrar_resumo(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            else:
                tela_atual = "pedido_modelo"
                msg, botoes = perguntar_modelo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 2: Tipo de slide ──
        if tela_atual == "pedido_modelo":
            botoes_modelo = ["📄 PDF", "🎬 Canva (Transições)", "🎬 PowerPoint (Transições)",
                             "🎨 Canva Temas", "🎨 PPTX Temas",
                             "🤔 Diferença Canva x PowerPoint", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_modelo)

            if "Diferença" in escolha_resolvida or "diferença" in escolha.lower():
                msg, botoes = explicar_diferenca_canva_powerpoint()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
                tela_atual = "pedido_modelo_diferenca"
                continue

            if escolha_resolvida in botoes_modelo[:5]:
                dados_pedido["modelo"] = escolha_resolvida
                if "Temas" in escolha_resolvida:
                    tela_atual = "pedido_qual_tema"
                    msg, botoes = perguntar_qual_tema()
                    print(f"\n🤖 Maya:\n{msg}\n")
                    bot_falou(historico, msg, tela_atual, dados_pedido)
                    mostrar_botoes(botoes)
                else:
                    tela_atual = "pedido_prazo"
                    msg, botoes = perguntar_prazo()
                    print(f"\n🤖 Maya:\n{msg}\n")
                    bot_falou(historico, msg, tela_atual, dados_pedido)
                    mostrar_botoes(botoes)
            elif escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            else:
                print("\n🤖 Maya: Ops! Escolhe uma das opções abaixo 👇")
                msg, botoes = perguntar_modelo()
                print(f"\n{msg}\n")
                mostrar_botoes(botoes)
            continue

        # ── Diferença Canva x PowerPoint ──
        if tela_atual == "pedido_modelo_diferenca":
            botoes_cp = ["📱 Canva", "💻 PowerPoint"]
            escolha_resolvida = resolver_botao(escolha, botoes_cp)
            if escolha_resolvida == "📱 Canva":
                dados_pedido["modelo"] = "🎬 Canva (Transições)"
            elif escolha_resolvida == "💻 PowerPoint":
                dados_pedido["modelo"] = "🎬 PowerPoint (Transições)"
            tela_atual = "pedido_prazo"
            msg, botoes = perguntar_prazo()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes)
            continue

        # ── PASSO 2.5: Qual tema? ──
        if tela_atual == "pedido_qual_tema":
            if escolha == "🎬 Quero o tema sobre o meu assunto":
                tela_atual = "pedido_canva_ppt"
                msg, botoes = perguntar_canva_ou_powerpoint()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha == "🔍 Buscar no site":
                msg_site = ("Dá uma olhadinha aqui:\n👉 https://slydesign.com.br/loja/\n\n"
                           "Me fala qual tema você gostou? 💜")
                print(f"\n🤖 Maya: {msg_site}")
                bot_falou(historico, msg_site, tela_atual, dados_pedido)
            else:
                dados_pedido["tema"] = escolha
                tela_atual = "pedido_prazo"
                msg, botoes = perguntar_prazo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 2.6: Canva ou PowerPoint? ──
        if tela_atual == "pedido_canva_ppt":
            botoes_cp = ["📱 Canva", "💻 PowerPoint", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_cp)
            if escolha_resolvida in ("📱 Canva", "💻 PowerPoint"):
                if escolha_resolvida == "📱 Canva":
                    dados_pedido["modelo"] = "🎨 Canva Temas"
                else:
                    dados_pedido["modelo"] = "🎨 PPTX Temas"
                tela_atual = "pedido_prazo"
                msg, botoes = perguntar_prazo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            continue

        # ── PASSO 3: Prazo ──
        if tela_atual == "pedido_prazo":
            dados_pedido["prazo"] = escolha
            eh_mesmo_dia = any(p in escolha.lower() for p in
                ["hoje", "12h", "12:", "mesmo dia", "ainda hoje", "hj",
                 "consegue pra hoje", "até as", "ate as", "pra hoje"])
            if eh_mesmo_dia:
                msg_taxa = aviso_taxa_mesmo_dia()
                print(f"\n🤖 Maya:\n{msg_taxa}")
                bot_falou(historico, msg_taxa, tela_atual, dados_pedido)
            if editando:
                editando = False
                tela_atual = "resumo"
                msg, botoes = mostrar_resumo(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            else:
                tela_atual = "pedido_nomes"
                msg, botoes = perguntar_nomes()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 4: Nomes ──
        if tela_atual == "pedido_nomes":
            botoes_nomes = ["🚫 Não quero", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_nomes)
            if escolha_resolvida == "🚫 Não quero":
                dados_pedido["nomes"] = "Não"
            elif escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                editando = False
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue
            else:
                dados_pedido["nomes"] = escolha

            if editando:
                editando = False
                tela_atual = "resumo"
                msg, botoes = mostrar_resumo(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            else:
                tela_atual = "pedido_obs"
                dados_pedido["observacoes"] = ""
                msg, botoes = perguntar_observacoes()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 5: Observações ──
        if tela_atual == "pedido_obs":
            tem_obs = bool(dados_pedido.get("observacoes", ""))
            if tem_obs:
                botoes_obs = ["✅ Finalizar Pedido", "🔙 Voltar ao menu"]
            else:
                botoes_obs = ["🚫 Não quero", "🔙 Voltar ao menu"]

            escolha_resolvida = resolver_botao(escolha, botoes_obs)

            if escolha_resolvida == "✅ Finalizar Pedido":
                tela_atual = "resumo"
                msg, botoes = mostrar_resumo(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "🚫 Não quero":
                dados_pedido["observacoes"] = "Nenhuma"
                tela_atual = "resumo"
                msg, botoes = mostrar_resumo(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            else:
                if dados_pedido["observacoes"]:
                    dados_pedido["observacoes"] += " | " + escolha
                else:
                    dados_pedido["observacoes"] = escolha
                msg, botoes = confirmar_recebido()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 6: Resumo ──
        if tela_atual == "resumo":
            botoes_resumo = ["✅ Confirmar pedido", "✏️ Quero mudar algo", "❌ Cancelar"]
            escolha_resolvida = resolver_botao(escolha, botoes_resumo)
            if escolha_resolvida == "✅ Confirmar pedido":
                tela_atual = "pagamento"
                msg, botoes = instrucoes_pagamento(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "✏️ Quero mudar algo":
                tela_atual = "mudar"
                msg, botoes = perguntar_o_que_mudar()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "❌ Cancelar":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_cancelamento()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── Mudar algo ──
        if tela_atual == "mudar":
            botoes_mudar = ["📝 Mudar tema", "🎨 Mudar tipo", "📅 Mudar prazo",
                            "👤 Mudar nomes", "📎 Mudar extras", "🔙 Voltar ao resumo"]
            escolha_resolvida = resolver_botao(escolha, botoes_mudar)
            if escolha_resolvida == "🔙 Voltar ao resumo":
                tela_atual = "resumo"
                msg, botoes = mostrar_resumo(dados_pedido)
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "📝 Mudar tema":
                editando = True
                tela_atual = "pedido_tema"
                msg_mudar = "Qual o novo assunto do slide? 📝"
                print(f"\n🤖 Maya: {msg_mudar}")
                bot_falou(historico, msg_mudar, tela_atual, dados_pedido)
            elif escolha_resolvida == "🎨 Mudar tipo":
                tela_atual = "pedido_modelo"
                msg, botoes = perguntar_modelo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "📅 Mudar prazo":
                editando = True
                tela_atual = "pedido_prazo"
                msg, botoes = perguntar_prazo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "👤 Mudar nomes":
                editando = True
                tela_atual = "pedido_nomes"
                msg, botoes = perguntar_nomes()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "📎 Mudar extras":
                editando = True
                tela_atual = "pedido_obs"
                dados_pedido["observacoes"] = ""
                msg, botoes = perguntar_observacoes()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── Pagamento ──
        if tela_atual == "pagamento":
            botoes_pag = ["📎 Enviar comprovante", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_pag)
            if escolha_resolvida == "📎 Enviar comprovante" or "comprovante" in escolha.lower():
                tela_atual = "aguardando_comprovante"
                msg_comp = "Manda o comprovante aqui! 📎\n(No WhatsApp, é só enviar a imagem ou PDF)"
                print(f"\n🤖 Maya: {msg_comp}")
                bot_falou(historico, msg_comp, tela_atual, dados_pedido)
                mostrar_botoes(["🔙 Voltar ao menu"])
            elif escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            continue

        # ── Aguardando comprovante ──
        if tela_atual == "aguardando_comprovante":
            if escolha.lower() in ("voltar", "menu", "🔙 voltar ao menu"):
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            else:
                msg, botoes = comprovante_recebido()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
                tela_atual = "comprovante"
            continue

        # ── Pós-compra / Pós-comprovante ──
        if tela_atual in ("pos_compra", "comprovante"):
            tela_atual = "menu"
            dados_pedido = {}
            editando = False
            msg, botoes = mensagem_boas_vindas()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            continue

        # ── Pós-dúvida ──
        if tela_atual == "pos_duvida":
            botoes_pd = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_pd)
            if escolha_resolvida == "💬 Continuar dúvida":
                msg_cont = "Continue digitando sua dúvida... 💜"
                print(f"\n🤖 Maya: {msg_cont}")
                bot_falou(historico, msg_cont, tela_atual, dados_pedido)
                tela_atual = "duvida"
                continue
            elif escolha_resolvida == "🔙 Voltar ao menu":
                tela_atual = "menu"
                dados_pedido = {}
                msg, botoes = mensagem_boas_vindas()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
                continue
            else:
                print("\n⏳ Maya está pensando... 💭")
                historico = resumir_se_precisar(historico)
                texto_ia, historico = resposta_ia_livre(escolha, historico)
                print(f"\n🤖 Maya:\n{texto_ia}")
                bot_falou(historico, texto_ia, tela_atual, dados_pedido)
                print("\n───")
                mostrar_botoes(botoes_pd, "  [0] Sair")
                continue

        # ── NLP: Detector de intenções no menu ──
        if tela_atual == "menu":
            intencao = detectar_intencao(escolha)

            if intencao == "preco":
                tela_atual = "precos"
                msg, botoes = resposta_quanto_custa()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente")
                continue

            if intencao == "prazo":
                msg_prazo = (
                    "Sobre prazos, funciona assim: 💜\n\n"
                    "📅 Prazo normal: até 2 dias.\n"
                    "⚡ Pedido para o mesmo dia: taxa adicional de R$ 5,00 "
                    "(se houver vaga na agenda).\n\n"
                    "💡 Recomendamos pedir com pelo menos 1 dia de antecedência "
                    "da sua apresentação.\n\n"
                    "Se quiser, já podemos começar seu pedido! 🎨"
                )
                print(f"\n🤖 Maya:\n{msg_prazo}")
                bot_falou(historico, msg_prazo, tela_atual, dados_pedido)
                mostrar_botoes([
                    "🎨 Quero fazer um pedido!",
                    "🔙 Voltar ao menu",
                ], "\n  💬 Ou digite sua pergunta livremente")
                continue

            if intencao == "listar_temas":
                msg_lista = (
                    "Temos VÁRIOS temas! Dá uma olhadinha na loja: 💜\n\n"
                    "👉 https://slydesign.com.br/loja/\n\n"
                    "Ou me fala um tema específico que eu procuro pra você! 🔍"
                )
                print(f"\n🤖 Maya:\n{msg_lista}")
                bot_falou(historico, msg_lista, tela_atual, dados_pedido)
                mostrar_botoes([
                    "🔍 Buscar um tema",
                    "🎨 Quero um slide personalizado",
                    "🔙 Voltar ao menu",
                ])
                continue

            if intencao == "suporte_tecnico":
                msg_sup = (
                    "Entendo! Vamos resolver isso. 💜\n\n"
                    "Primeiro: qual o tema do slide que você comprou? 🛒"
                )
                print(f"\n🤖 Maya: {msg_sup}")
                bot_falou(historico, msg_sup, tela_atual, dados_pedido)
                tela_atual = "duvida_compra"
                continue

            if intencao == "ajuda_montagem":
                msg_ajuda = (
                    "Claro! 🎨\n\n"
                    "Pra editar ou montar seu slide, dá uma olhada nesse tutorial "
                    "que explica tudinho:\n\n"
                    "📹 Como editar no Canva: https://youtu.be/hI56FSKNg0c\n\n"
                    "📹 Como comprar no site (passo a passo): https://youtu.be/wyuXppcptrk\n\n"
                    "Se quiser um modelo específico, me fala qual tema que eu "
                    "te mando o link direto! 💜"
                )
                print(f"\n🤖 Maya:\n{msg_ajuda}")
                bot_falou(historico, msg_ajuda, tela_atual, dados_pedido)
                mostrar_botoes([
                    "🔍 Buscar um tema",
                    "💬 Ainda preciso de ajuda",
                    "🔙 Voltar ao menu",
                ])
                continue

            # intenções "buscar_tema" e "duvida" → continuam pro fluxo normal

        # ── Detecção inteligente de tema no menu ──
        if tela_atual == "menu":
            tema_encontrado, todos = buscar_tema(escolha)
            if tema_encontrado:
                nome_tema = tema_encontrado["tema"]
                msg_tema = (f"Achamos! \"{nome_tema}\" é um dos nossos Slides Temas! "
                           "É um slide com design baseado nesse tema visual. 💜\n\n"
                           "Você prefere:\n"
                           "📱 Canva — link online, acessa pelo navegador.\n"
                           "💻 PowerPoint — arquivo PPTX offline.\n\n"
                           "Visualmente são iguais, só muda a forma de acessar.")
                print(f"\n🤖 Maya: {msg_tema}")
                bot_falou(historico, msg_tema, tela_atual, dados_pedido)
                dados_pedido = {"tema": nome_tema}
                tela_atual = "pedido_canva_ppt"
                mostrar_botoes(["📱 Canva", "💻 PowerPoint", "🔙 Voltar ao menu"])
                continue

        # ── Fallback: resposta da IA ──
        print("\n⏳ Maya está pensando... 💭")
        historico = resumir_se_precisar(historico)
        texto_ia, historico = resposta_ia_livre(escolha, historico)
        print(f"\n🤖 Maya:\n{texto_ia}")
        bot_falou(historico, texto_ia, tela_atual, dados_pedido)
        print("\n───")
        botoes_pos_duvida = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
        mostrar_botoes(botoes_pos_duvida, "  [0] Sair")
        tela_atual = "pos_duvida"


if __name__ == "__main__":
    main()

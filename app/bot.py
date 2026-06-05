"""
bot.py — Funções de mensagem e fluxos de conversa da Maya.
"""
from app.config import cliente, MODELO, SYSTEM_PROMPT, PRECOS, TEMAS_DISPONIVEIS
from app.buscador import buscar_tema


# ─────────────────────────────────────────────
# MENSAGENS E BOTÕES
# ─────────────────────────────────────────────

def mensagem_boas_vindas():
    """Primeira mensagem que o cliente vê."""
    texto = (
        "Oie! Seja bem-vindo(a) à Sly Design! 💜\n\n"
        "Aqui a gente tem slides prontos super legais "
        "e também criamos do zero, do seu jeitinho. ✨\n\n"
        "Me conta: no que posso te ajudar hoje?"
    )
    botoes = [
        "Ver Slides Prontos",
        "Quero um Slide Personalizado",
        "Consultar um Tema",
        "Quanto Custa?",
        "Quero Tirar uma Dúvida",
    ]
    return texto, botoes


def resposta_busca_tema(termo_buscado):
    """Usa o buscador inteligente pra achar um tema no catálogo."""
    melhor, todos = buscar_tema(termo_buscado)

    if melhor:
        if len(todos) == 1:
            texto = (
                f"Temos esse tema disponível no catálogo "
                f"com entrega imediata. 💜\n\n"
                f"📄 {melhor['tema']}\n"
                f"👉 {melhor['link']}\n\n"
                f"É só comprar e receber na hora!"
            )
            botoes = [
                f"🛒 Comprar {melhor['tema']}",
                "🔍 Buscar outro tema",
                "🔙 Voltar ao menu",
            ]
        else:
            linhas = "Encontrei esses temas. Qual você procura? 💜\n\n"
            for i, t in enumerate(todos, 1):
                linhas += f"{i}. {t['tema']} — {t['link']}\n"
            texto = linhas
            botoes = [
                "🔍 Buscar outro tema",
                "🎨 Nenhum desses, quero personalizado",
                "🔙 Voltar ao menu",
            ]
    else:
        texto = (
            f"Não encontrei \"{termo_buscado}\" no nosso catálogo pronto.\n\n"
            f"Mas podemos criar um slide personalizado "
            f"exatamente como você precisa. 💜"
        )
        botoes = [
            "🎨 Quero um slide personalizado!",
            "🔍 Buscar outro tema",
            "🔙 Voltar ao menu",
        ]

    return texto, botoes


def resposta_ver_slides_prontos():
    """Botão 1: Ver Slides Prontos."""
    texto = (
        "Nossa, temos MUITA coisa legal no site! 💜\n"
        "De trabalhos da escola até temas de facul,\n"
        "dá uma olhadinha:\n\n"
        "👉 https://slydesign.com.br/loja/\n\n"
        "É só escolher, comprar e já cai no seu e-mail! 📧\n\n"
        "Ou se quiser, me fala um tema que eu procuro pra você 🔍"
    )
    botoes = [
        "🔍 Buscar um tema",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def resposta_quanto_custa():
    """Botão 4: Quanto Custa?"""
    texto = (
        "O valor depende do tipo de slide que você escolher. 💜\n\n"
        "📄 SLIDES EM PDF:\n"
        f"   • PDF — {PRECOS['PDF']}\n\n"
        "🎬 SLIDES COM TRANSIÇÕES:\n"
        f"   • Canva — {PRECOS['Canva (Transições)']}\n"
        f"   • PowerPoint — {PRECOS['PowerPoint (Transições)']}\n\n"
        "🎨 SLIDES TEMAS:\n"
        f"   • Canva — {PRECOS['Canva Temas']}\n"
        f"   • PPTX — {PRECOS['PPTX Temas']}\n\n"
        "💡 No nosso site você consegue ver exemplos "
        "e explicações detalhadas de cada tipo:\n"
        "👉 https://slydesign.com.br/personalizados/"
    )
    botoes = [
        "🛒 Ok! Quero fazer meu pedido",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def resposta_ia_livre(pergunta, historico=None):
    """Quando o cliente NÃO aperta um botão e digita algo livremente."""
    if historico is None:
        historico = [{"role": "system", "content": SYSTEM_PROMPT}]

    historico.append({"role": "user", "content": pergunta})

    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=historico,
        temperature=0.7,
    )

    texto = resposta.choices[0].message.content
    return texto, historico


# ─────────────────────────────────────────────
# FLUXO DE PEDIDO PERSONALIZADO (Botão 2)
# ─────────────────────────────────────────────

def iniciar_pedido_personalizado():
    """Passo 1: inicia o fluxo, pergunta o assunto do slide."""
    texto = (
        "Ihuuul! 🎉 Vamos criar seu slide personalizado!\n\n"
        "Vou te fazer umas perguntinhas rápidas, ok?\n\n"
        "📝 Primeiro: qual o ASSUNTO do slide?"
    )
    botoes = [
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def perguntar_modelo():
    """Passo 2: pergunta qual tipo de slide."""
    texto = (
        "Certo, anotei o tema! 📝\n\n"
        "Agora me conta: qual TIPO de slide você prefere?\n\n"
        "Você pode conferir exemplos de cada tipo aqui:\n"
        "👉 https://slydesign.com.br/personalizados/\n\n"
        "📄 PDF — R$ 20,00\n"
        "   Slide com design sobre o seu assunto, sem animações.\n"
        "\n"
        "🎬 Canva (Transições) — R$ 25,00\n"
        "   Slide com design sobre o seu assunto + movimentos e efeitos.\n"
        "   Recebe link online.\n"
        "\n"
        "🎬 PowerPoint (Transições) — R$ 35,00\n"
        "   Slide com design sobre o seu assunto + movimentos e efeitos.\n"
        "   Arquivo PPTX offline.\n"
        "\n"
        "🎨 Canva Temas — R$ 28,00\n"
        "   Tema visual criativo (ex: Netflix, Spotify). Link online.\n"
        "\n"
        "🎨 PPTX Temas — R$ 38,00\n"
        "   Temático em arquivo PPTX pra usar offline.\n"
        "\n"
        "Qual desses combina mais com você? 💜"
    )
    botoes = [
        "📄 PDF",
        "🎬 Canva (Transições)",
        "🎬 PowerPoint (Transições)",
        "🎨 Canva Temas",
        "🎨 PPTX Temas",
        "🤔 Diferença Canva x PowerPoint",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def perguntar_qual_tema():
    """Passo extra: se a pessoa escolheu Canva Temas ou PPTX Temas."""
    top5 = ", ".join(TEMAS_DISPONIVEIS[:5])
    texto = (
        "Legal! Temos vários temas prontos. 💜\n\n"
        f"Os mais pedidos: {top5}...\n\n"
        "E tem mais no site:\n"
        "👉 https://slydesign.com.br/loja/\n\n"
        "Se quiser um tema que não está na lista, "
        "podemos criar do zero. Me diga qual tema você quer?"
    )
    botoes = [
        "🎬 Quero o tema sobre o meu assunto",
        "🔍 Buscar no site",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def perguntar_canva_ou_powerpoint():
    """Quando a pessoa quer tema livre (sobre o assunto dela)."""
    texto = (
        "Certo! Vamos criar um slide com design sobre o seu assunto. 🎨\n\n"
        "Você prefere:\n\n"
        "📱 Canva — link online, acessa pelo navegador.\n"
        "💻 PowerPoint — arquivo PPTX, baixa no PC/pen-drive, "
        "funciona offline e também no celular com o app PowerPoint.\n\n"
        "Visualmente são iguais, só muda a forma de acessar."
    )
    botoes = [
        "📱 Canva",
        "💻 PowerPoint",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def explicar_diferenca_canva_powerpoint():
    """Quando perguntam diferença entre Canva e PowerPoint."""
    texto = (
        "Visualmente são iguais! 🎨\n\n"
        "📱 Canva — link online, acessa pelo navegador.\n"
        "💻 PowerPoint — arquivo PPTX, baixa no PC/pen-drive, "
        "funciona offline e também no celular com o app PowerPoint.\n\n"
        "Só muda isso. Qual você prefere?"
    )
    botoes = [
        "📱 Canva",
        "💻 PowerPoint",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def perguntar_prazo():
    """Passo 3: pergunta o prazo de entrega."""
    texto = (
        "Anotado! ✅\n\n"
        "Agora sobre o PRAZO: até que dia eu posso te entregar?\n\n"
        "💡 Recomendamos pedir com pelo menos 1 dia de antecedência "
        "da sua apresentação.\n\n"
        "Me conta: qual a data que você precisa? 📅"
    )
    botoes = [
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def aviso_taxa_mesmo_dia():
    """Aviso quando o cliente precisa do slide pra hoje."""
    texto = (
        "⚠️ Como é para hoje, temos uma taxa adicional de R$ 5,00 "
        "e preciso verificar se ainda há vaga na agenda. "
        "Vou confirmar com a equipe, um momento!"
    )
    return texto


def perguntar_nomes():
    """Passo 4: pergunta se quer nomes no slide."""
    texto = (
        "Anotei o prazo! 📅\n\n"
        "Quer adicionar os nomes de vocês no slide?\n\n"
        "Se sim, me diga quais nomes.\n"
        "Se não, é só apertar o botão abaixo. 💜"
    )
    botoes = [
        "🚫 Não quero",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def perguntar_observacoes():
    """Passo 5: pergunta se quer adicionar informações extras (mini-loop)."""
    texto = (
        "Quase lá! 📝\n\n"
        "Quer adicionar mais alguma informação?\n"
        "Ex: resumo, tópicos específicos, jeito que quer o design, "
        "referências, arquivos...\n"
        "Ah, e a pesquisa do conteúdo é por nossa conta se você "
        "preferir! 🔍\n\n"
        "⚠️ Importante: depois que o slide estiver pronto, qualquer "
        "alteração tem uma taxa de R$ 1,50 por página editada. "
        "Então quanto mais detalhes agora, melhor!\n\n"
        "Pode mandar quantas mensagens quiser. Quando terminar, "
        "é só clicar em 'Finalizar Pedido'. 💜"
    )
    botoes = [
        "🚫 Não quero",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def confirmar_recebido():
    """Confirma que recebeu a informação e mostra botão de finalizar."""
    texto = (
        "Recebi! ✅ Pode mandar mais se quiser.\n\n"
        "Quando terminar, clica em 'Finalizar Pedido'. 💜"
    )
    botoes = [
        "✅ Finalizar Pedido",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def mostrar_resumo(dados):
    """Passo 6: mostra o resumo do pedido."""
    modelo = dados.get("modelo", "")
    modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
    preco = PRECOS.get(modelo_limpo, "a combinar")

    texto = (
        "Aqui está o resumo do seu pedido: 💜\n\n"
        f"📝 Tema: {dados.get('tema', '')}\n"
        f"🎨 Tipo: {modelo}\n"
        f"📅 Prazo: {dados.get('prazo', '')}\n"
        f"👤 Nomes: {dados.get('nomes', 'Não')}\n"
        f"📎 Extras: {dados.get('observacoes', 'Nenhum')}\n\n"
        f"💰 Valor total: {preco}\n\n"
        "Tá tudo certo?"
    )
    botoes = [
        "✅ Confirmar pedido",
        "✏️ Quero mudar algo",
        "❌ Cancelar",
    ]
    return texto, botoes


def perguntar_o_que_mudar():
    """Pergunta QUAL parte do pedido a pessoa quer mudar."""
    texto = "Claro! O que você quer mudar? ✏️"
    botoes = [
        "📝 Mudar tema",
        "🎨 Mudar tipo",
        "📅 Mudar prazo",
        "👤 Mudar nomes",
        "📎 Mudar extras",
        "🔙 Voltar ao resumo",
    ]
    return texto, botoes


def instrucoes_pagamento(dados):
    """Só aparece DEPOIS que a pessoa confirma o pedido."""
    modelo = dados.get("modelo", "")
    modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
    preco = PRECOS.get(modelo_limpo, "a combinar")
    valor_str = preco.replace("R$ ", "").replace(",", ".")
    try:
        metade = float(valor_str) / 2
        metade_str = f"R$ {metade:.2f}".replace(".", ",")
    except (ValueError, AttributeError):
        metade_str = "a combinar"

    texto = (
        "Perfeito! Pra finalizar, precisamos de 50% do valor. 💜\n\n"
        f"💰 Valor total: {preco}\n"
        f"💳 Agora: {metade_str}\n\n"
        "📱 Chave Pix (telefone):\n"
        "38997507651\n"
        "Shayene Lopes Figueredo\n\n"
        "Assim que pagar, me manda o comprovante aqui. "
        "Um humano vai dar uma olhadinha e já confirmamos! ✅"
    )
    botoes = [
        "📎 Enviar comprovante",
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def comprovante_recebido():
    """Resposta após o cliente enviar o comprovante."""
    texto = (
        "Recebi! 💜\n\n"
        "Seu comprovante vai ser olhado pela nossa equipe agora. "
        "Assim que confirmarmos o pagamento, já te aviso e "
        "começamos a produzir seu slide."
    )
    botoes = [
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def mensagem_cancelamento():
    """Quando a pessoa cancela o pedido."""
    texto = (
        "Sem problemas! 💜\n\n"
        "Quando precisar, tô aqui! É só dar um oi que eu apareço na hora. ✨"
    )
    botoes = [
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


# ─────────────────────────────────────────────
# UTILITÁRIOS DE INTERFACE
# ─────────────────────────────────────────────

def mostrar_botoes(botoes, extra=""):
    """Exibe os botões numerados (número = atalho)."""
    for i, b in enumerate(botoes, 1):
        print(f"  [{i}] {b}")
    if extra:
        print(extra)


def resolver_botao(escolha, botoes):
    """Se for número, retorna o texto do botão. Senão, retorna igual."""
    if escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(botoes):
            return botoes[idx]
    return escolha

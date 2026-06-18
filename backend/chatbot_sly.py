"""
CHATBOT OFICIAL - SLY DESIGN 💜
Maya — a atendente virtual da Sly Design.
Arquivo principal do chatbot de atendimento no WhatsApp.
"""
import os
import json
from groq import Groq
from dotenv import load_dotenv
from buscador_temas import buscar_tema

load_dotenv()

# ─────────────────────────────────────────────
# CONFIGURAÇÕES
# ─────────────────────────────────────────────
cliente = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODELO = "llama-3.3-70b-versatile"

# Personalidade da Maya (system prompt)
SYSTEM_PROMPT = """
Você é a Maya, atendente virtual da Sly Design (slydesign.com.br).
Você é uma jovem de 18 anos, simpática, animada e muito prestativa.
Seu tom de voz é: amigável, caloroso, direto e com um toque jovem e descontraído.
Use emojis com moderação e um humor leve. Responda sempre em português do Brasil.
Trate o cliente como se fosse um amigo chegando na loja. 💜

⚠️ REGRA IMPORTANTE: Você está no MEIO de uma conversa. NUNCA cumprimente
(não diga "Olá", "Oi", "Tudo bem?"). Vá direto ao ponto.

SOBRE A SLY DESIGN:
- Vendemos slides prontos e personalizados para trabalhos escolares,
  acadêmicos, TCC, seminários e apresentações profissionais.
- Site: https://slydesign.com.br
- Página de personalizados: https://slydesign.com.br/personalizados/
- Cupom de desconto: DESCONTO15 (15% OFF no site).
- NÃO fazemos slides de graça.

PRAZOS:
- Prazo normal: até 2 dias.
- Pedidos para o mesmo dia: taxa adicional de R$ 5,00 (se houver vaga).

FORMAS DE PAGAMENTO:
- Pix ou Cartão de Crédito (cartão tem taxa adicional de R$ 2,50).
- Pagamento dividido: 50% antes (confirma o pedido) e 50% depois
  (quando o slide estiver finalizado).

TIPOS DE SLIDES (se o cliente perguntar, explique):

1. Slide PDF (R$ 20,00):
   Slide estático, sem animações. Visual organizado, bonito e profissional.
   Ideal pra quem quer algo simples e direto. Entrega: arquivo PDF.
   Pra ver exemplos: https://slydesign.com.br/personalizados/

2. Slide com Transições Canva (R$ 25,00):
   Movimentos, efeitos e animações entre as páginas. O design é criado
   do zero baseado no tema. Entrega: link online do Canva.
   Pra ver exemplos: https://slydesign.com.br/personalizados/

3. Slide com Transições PowerPoint (R$ 35,00):
   Mesmo conceito do Canva, mas entregue como arquivo PPTX que funciona
   offline. Ideal pra quem quer baixar o arquivo.
   Pra ver exemplos: https://slydesign.com.br/personalizados/

4. Slide Temas Canva (R$ 28,00):
   Slide com tema visual específico (ex: Netflix, Spotify, Bob Esponja).
   Conteúdo dentro de um estilo criativo. Entrega: link online do Canva.
   Pra ver exemplos: https://slydesign.com.br/personalizados/

5. Slide Temas PPTX (R$ 38,00):
   Mesmo do Temas Canva, mas em arquivo PPTX pra uso offline.
   Pra ver exemplos: https://slydesign.com.br/personalizados/

IMPORTANTE SOBRE ALTERAÇÕES:
Se o cliente pedir alterações após a finalização, será cobrado um valor adicional.

SUPORTE PARA QUEM COMPROU NO SITE:
Se o cliente relatar problema com slide comprado no site (ex: "comprei", "não consigo abrir",
"deu erro", "não chegou"), siga este fluxo ANTES de responder:

1. Primeiro pergunte: "Qual o tema do slide que você comprou?"
2. Depois entenda o problema. Slides do site são em Canva ou PowerPoint (PPTX).
   Se for problema pra abrir:
   - Canva: precisa de conta grátis no Canva + estar logada
   - PowerPoint: baixar o arquivo PPTX e abrir com app PowerPoint (PC ou celular)
3. Se não conseguir resolver: "Vou chamar um humano pra te ajudar, aguarda uns minutinhos! 💜"

TUTORIAIS EM VÍDEO (envie o link quando relevante):
- Como editar nomes no Canva e anexar no modelo:
  https://youtu.be/hI56FSKNg0c
  (problema comum no slide Jovens Titãs e outros do Canva)
- Como comprar no site (passo a passo):
  https://youtu.be/wyuXppcptrk

CONTATO HUMANO (se perguntarem):
WhatsApp: (34) 99930-6554
Instagram: @sly_desgn
E-mail: slydesgn@gmail.com
"""

# Preços oficiais (usado nas funções de resposta)
PRECOS = {
    "PDF": "R$ 20,00",
    "Canva (Transições)": "R$ 25,00",
    "PowerPoint (Transições)": "R$ 35,00",
    "Canva Temas": "R$ 28,00",
    "PPTX Temas": "R$ 38,00",
}


# Temas disponíveis (Temas)
TEMAS_DISPONIVEIS = [
    # Modelos
    "Jovens Titãs", "Interestellar", "Spotify", "Minecraft",
    "Duolingo", "Digital Circus", "Ursos Sem Curso", "Haikyuu",
    "Scooby-Doo", "Outer Banks", "Monster High", "DivertidaMente",
    "Avatar", "TinkerBell", "Barbie", "Steven Universe",
    "Dora Aventureira", "George O Curioso", "Meninas SuperPoderosas",
    "The Last of Us II", "La Casa de Papel", "Subway Surfers",
    "Homem Aranha", "Bob Esponja", "Tigrinho", "Peppa Pig",
    "O Incrível Mundo de Gumball", "ROBLOX 99 Noites na Floresta",
    "Fórmula 1", "Princesinha Sofia",
    # Slides
    "ChatGPT", "Neymar", "Romantismo", "Revolução Russa",
    "Primeira Guerra Mundial", "Netflix Arboviroses", "Portugal",
    "Modernismo", "Velozes e Furiosos", "Sistema Solar",
    "Filosofia da Ciência", "Revolução Chinesa", "Ascensão do Nazismo",
    "Reino da Espanha", "Vietnã", "Canadá", "União Europeia",
    "Basquete", "Guerra do Paraguai",
    "Vírus e Bactérias", "África Ocidental", "Antigo Egito",
    "Alimentos Sustentáveis",
    # Packs
    "Pack Famosinhos", "Pack História", "Pack Desenhos Animados",
]


# ─────────────────────────────────────────────
# MEMÓRIA PERSISTENTE (Salvar e Carregar Conversa)
# ─────────────────────────────────────────────
ARQUIVO_MEMORIA = "backend/memoria_conversa.json"


def salvar_conversa(historico, tela_atual, dados_pedido):
    """Salva a conversa num arquivo JSON. Se o programa fechar, não perde!"""
    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump({
            "historico": historico,
            "tela_atual": tela_atual,
            "dados_pedido": dados_pedido,
        }, f, ensure_ascii=False, indent=2)


def carregar_conversa():
    """Tenta carregar a conversa salva. Se não existir, volta vazio."""
    if not os.path.exists(ARQUIVO_MEMORIA):
        return None, "menu", {}
    with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dados["historico"], dados["tela_atual"], dados["dados_pedido"]


def contar_tokens_aproximado(historico):
    """Conta APROXIMADAMENTE quantos tokens o histórico está usando.
    Regra: 1 token ≈ 4 caracteres em português (Llama usa BPE).
    Isso ajuda a saber quando a 'mesa' está cheia demais."""
    total_chars = 0
    for msg in historico:
        total_chars += len(msg.get("content", ""))
    return total_chars // 4  # aproximação


def resumir_se_precisar(historico, max_tokens=7000):
    """Se o histórico tiver tokens DEMAIS, tira as mensagens mais antigas.
    Mas SEMPRE mantém o system prompt (mensagem 0)."""
    while contar_tokens_aproximado(historico) > max_tokens and len(historico) > 3:
        # Remove a mensagem mais antiga depois do system prompt (índice 1)
        removida = historico.pop(1)
        print(f"  🧹 [Memória cheia! Removendo mensagem antiga: "
              f"\"{removida.get('content', '')[:40]}...\"]")
    return historico


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
    """
    Usa o buscador inteligente pra achar um tema no catálogo.
    Chamado quando o cliente aperta 'Buscar um tema' ou digita um tema.
    """
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
            # Múltiplos resultados
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
    """
    Quando o cliente NÃO aperta um botão e digita algo livremente.
    Ex: "qual a diferença entre pdf e canva?" ou "faz sobre matemática?"
    """
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
        "Perfeito! Vou preparar seu slide personalizado. 💜\n\n"
        "Vou fazer algumas perguntas, bem rápido.\n\n"
        "📝 Qual o ASSUNTO do slide?"
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
    # Remove emojis pra achar o preço
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
    # Remove emojis pra achar o preço
    modelo_limpo = modelo.split(" ", 1)[1] if " " in modelo else modelo
    preco = PRECOS.get(modelo_limpo, "a combinar")
    # Calcula 50%
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
        "Tudo bem! Esperamos trabalhar com você em breve. 💜\n\n"
        "Se precisar, é só chamar!"
    )
    botoes = [
        "🔙 Voltar ao menu",
    ]
    return texto, botoes


def mostrar_botoes(botoes, extra=""):
    """Exibe os botões numerados (número = atalho)."""
    for i, b in enumerate(botoes, 1):
        print(f"  [{i}] {b}")
    if extra:
        print(extra)


def bot_falou(historico, texto, tela_atual, dados_pedido):
    """Registra que a Sly falou algo + salva a conversa + mostra tokens."""
    historico.append({"role": "assistant", "content": texto})
    salvar_conversa(historico, tela_atual, dados_pedido)
    tokens = contar_tokens_aproximado(historico)
    if tokens > 5000:
        print(f"  📊 [Tokens: ~{tokens} | ⚠️ Mesa quase cheia!]")
    else:
        print(f"  📊 [Tokens: ~{tokens}]")


def cliente_falou(historico, texto, tela_atual, dados_pedido):
    """Registra o que o cliente disse e salva."""
    historico.append({"role": "user", "content": texto})
    salvar_conversa(historico, tela_atual, dados_pedido)


def resolver_botao(escolha, botoes):
    """Se for número, retorna o texto do botão. Senão, retorna igual."""
    if escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(botoes):
            return botoes[idx]
    return escolha


# ─────────────────────────────────────────────
# LOOP PRINCIPAL (versão terminal - simula botões)
# ─────────────────────────────────────────────
if __name__ == "__main__":
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
        # Mostra onde a conversa parou
        if tela_atual == "menu":
            msg, botoes = mensagem_boas_vindas()
            print(f"\n🤖 Maya:\n{msg}\n")
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente (a Sly entende!)\n  [0] Sair")
        else:
            print(f"\n🤖 Maya: Continuando de onde paramos... (tela: {tela_atual}) 💜")
            print(f"   Última mensagem: {historico[-1]['content'][:80]}...")
    else:
        # Mostra boas-vindas
        msg, botoes = mensagem_boas_vindas()
        print(f"\n🤖 Maya:\n{msg}\n")
        mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente (a Sly entende!)\n  [0] Sair")

        # Histórico da conversa (pra IA lembrar o contexto)
        historico = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Estado: em qual "tela" o cliente está
        tela_atual = "menu"

        # Dados do pedido personalizado
        dados_pedido = {}
    editando = False  # True quando está editando um campo específico

    # Últimos botões exibidos (pra resolver números nos resultados da busca)
    ultimos_botoes = []

    while True:
        escolha = input("\n▶️  Você: ").strip()

        if not escolha:
            continue

        # ── Guarda no histórico (se for texto livre, não número de botão) ──
        if not escolha.isdigit() or escolha == "0":
            cliente_falou(historico, escolha, tela_atual, dados_pedido)

        # ── SAIR ──
        if escolha == "0":
            msg, botoes = mensagem_cancelamento()
            print(f"\n🤖 Maya:\n{msg}\n")
            break

        # ── VOLTAR AO MENU ──
        if escolha.lower() in ("voltar", "menu", "🔙 voltar ao menu"):
            tela_atual = "menu"
            dados_pedido = {}
            msg, botoes = mensagem_boas_vindas()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            continue

        # ─────────────────────────────────────
        # BOTÕES DO MENU PRINCIPAL
        # ─────────────────────────────────────

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

        # ── Se está na tela de dúvida ──
        if tela_atual == "duvida":
            # Detecta se é sobre compra no site
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
            # Dúvida normal → IA responde
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

        # ── Dúvida de compra: identificou o tema, agora processa ──
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

        # ─────────────────────────────────────
        # TELAS DE NAVEGAÇÃO
        # ─────────────────────────────────────

        # ── Se está na tela de buscar tema e digitou algo ──
        if tela_atual == "buscando_tema":
            msg, botoes = resposta_busca_tema(escolha)
            ultimos_botoes = botoes
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
            tela_atual = "resultados_busca"
            continue

        # ── Resultados da busca: processa os botões de ação ──
        if tela_atual == "resultados_busca":
            # Resolve números contra os últimos botões exibidos
            escolha_resolvida = resolver_botao(escolha, ultimos_botoes)

            if "comprar" in escolha_resolvida.lower():
                msg_pos_compra = "Beleza! Qualquer coisa é só me chamar de novo, tá? 💜"
                print(f"\n🤖 Maya: {msg_pos_compra}")
                bot_falou(historico, msg_pos_compra, tela_atual, dados_pedido)
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
                # Trata como nova busca
                msg, botoes = resposta_busca_tema(escolha)
                ultimos_botoes = botoes
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes, "\n  💬 Ou continue a conversa...")
            continue

        # ── Se está na tela de slides prontos e digitou algo ──
        if tela_atual == "slides_prontos":
            # Resolve número → botão (1 = buscar tema, 2 = voltar)
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

        # ── Tela de preços: "Quero fazer meu pedido" ──
        if tela_atual == "precos" and ("pedido" in escolha.lower() or "comprar" in escolha.lower()):
            tela_atual = "pedido_tema"
            dados_pedido = {}
            msg, botoes = iniciar_pedido_personalizado()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes)
            continue

        # ─────────────────────────────────────
        # FLUXO DE PEDIDO PERSONALIZADO
        # ─────────────────────────────────────

        # ── PASSO 1: Tema/Assunto ──
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

            if escolha_resolvida in botoes_modelo[:5]:  # os 5 tipos
                dados_pedido["modelo"] = escolha_resolvida
                # Se escolheu Temas, pergunta qual tema
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
                msg_erro = "Ops! Escolhe uma das opções abaixo 👇"
                print(f"\n🤖 Maya: {msg_erro}")
                msg, botoes = perguntar_modelo()
                print(f"\n{msg}\n")
                mostrar_botoes(botoes)
            continue

        # ── Depois de ver a diferença Canva x PowerPoint, voltar pro modelo ──
        if tela_atual == "pedido_modelo_diferenca":
            botoes_cp = ["📱 Canva", "💻 PowerPoint"]
            escolha_resolvida = resolver_botao(escolha, botoes_cp)
            if escolha_resolvida == "📱 Canva":
                dados_pedido["modelo"] = "🎬 Canva (Transições)"
                tela_atual = "pedido_prazo"
                msg, botoes = perguntar_prazo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha_resolvida == "💻 PowerPoint":
                dados_pedido["modelo"] = "🎬 PowerPoint (Transições)"
                tela_atual = "pedido_prazo"
                msg, botoes = perguntar_prazo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            else:
                # Volta pro menu de modelos
                tela_atual = "pedido_modelo"
                msg, botoes = perguntar_modelo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 2.5: Qual tema? (só pra quem escolheu Temas) ──
        if tela_atual == "pedido_qual_tema":
            if escolha == "🎬 Quero o tema sobre o meu assunto":
                tela_atual = "pedido_canva_ppt"
                msg, botoes = perguntar_canva_ou_powerpoint()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            elif escolha == "🔍 Buscar no site":
                msg_site = "Dá uma olhadinha aqui:\n👉 https://slydesign.com.br/loja/\n\nMe fala qual tema você gostou? 💜"
                print(f"\n🤖 Maya: {msg_site}")
                bot_falou(historico, msg_site, tela_atual, dados_pedido)
            else:
                # Guarda o tema escolhido e avança
                dados_pedido["tema"] = escolha
                tela_atual = "pedido_prazo"
                msg, botoes = perguntar_prazo()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
            continue

        # ── PASSO 2.6: Canva ou PowerPoint? (tema livre) ──
        if tela_atual == "pedido_canva_ppt":
            botoes_cp = ["📱 Canva", "💻 PowerPoint", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_cp)
            if escolha_resolvida in ("📱 Canva", "💻 PowerPoint"):
                # Atualiza o modelo pra Canva Temas ou PPTX Temas
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
            else:
                print("\n🤖 Maya: Ops! Escolhe uma das opções 👇")
                msg, botoes = perguntar_canva_ou_powerpoint()
                print(f"\n{msg}\n")
                mostrar_botoes(botoes)
            continue

        # ── PASSO 3: Prazo ──
        if tela_atual == "pedido_prazo":
            dados_pedido["prazo"] = escolha
            # Detecta se é pra hoje
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

        # ── PASSO 5: Observações (mini-loop) ──
        if tela_atual == "pedido_obs":
            # Os botões mudam conforme a fase:
            # 1ª vez: "🚫 Não quero" + "🔙 Voltar ao menu"
            # Depois: "✅ Finalizar Pedido" + "🔙 Voltar ao menu"
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
                # Acumula as observações
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

        # ── Mudar algo no pedido ──
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
                # Mudar tipo é mais complexo (tem subtipos), deixa o fluxo normal
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
                msg_comprovante = "Manda o comprovante aqui! 📎\n(No WhatsApp, é só enviar a imagem ou PDF)"
                print(f"\n🤖 Maya: {msg_comprovante}")
                bot_falou(historico, msg_comprovante, tela_atual, dados_pedido)
                botoes_aguardando = ["🔙 Voltar ao menu"]
                mostrar_botoes(botoes_aguardando)
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
                # No terminal não dá pra detectar tipo de arquivo.
                # No WhatsApp real: checar se message.type == "image" ou "document"
                msg, botoes = comprovante_recebido()
                print(f"\n🤖 Maya:\n{msg}\n")
                bot_falou(historico, msg, tela_atual, dados_pedido)
                mostrar_botoes(botoes)
                tela_atual = "comprovante"
            continue

        # ── Pós-compra / Pós-comprovante: espera o cliente falar algo ──
        if tela_atual in ("pos_compra", "comprovante"):
            tela_atual = "menu"
            dados_pedido = {}
            editando = False
            msg, botoes = mensagem_boas_vindas()
            print(f"\n🤖 Maya:\n{msg}\n")
            bot_falou(historico, msg, tela_atual, dados_pedido)
            mostrar_botoes(botoes, "\n  💬 Ou digite sua pergunta livremente\n  [0] Sair")
            continue

        # ── Pós-dúvida: continuar ou voltar ──
        if tela_atual == "pos_duvida":
            botoes_pd = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
            escolha_resolvida = resolver_botao(escolha, botoes_pd)
            if escolha_resolvida == "💬 Continuar dúvida":
                msg_continuar = "Continue digitando sua dúvida... 💜"
                print(f"\n🤖 Maya: {msg_continuar}")
                bot_falou(historico, msg_continuar, tela_atual, dados_pedido)
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
                # Trata como nova dúvida
                print("\n⏳ Maya está pensando... 💭")
                historico = resumir_se_precisar(historico)
                texto_ia, historico = resposta_ia_livre(escolha, historico)
                print(f"\n🤖 Maya:\n{texto_ia}")
                bot_falou(historico, texto_ia, tela_atual, dados_pedido)
                print("\n───")
                mostrar_botoes(botoes_pd, "  [0] Sair")
                continue

        # ── DETECÇÃO INTELIGENTE: tentou um tema conhecido? ──
        if tela_atual == "menu":
            tema_encontrado, todos = buscar_tema(escolha)
            if tema_encontrado:
                # Achou um tema conhecido → sugere Temas direto!
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

        # ── Responde dúvida livre (fallback: estados sem handler específico) ──
        print("\n⏳ Maya está pensando... 💭")
        historico = resumir_se_precisar(historico)
        texto_ia, historico = resposta_ia_livre(escolha, historico)
        print(f"\n🤖 Maya:\n{texto_ia}")
        bot_falou(historico, texto_ia, tela_atual, dados_pedido)

        # Depois de responder, mostra botões de continuar ou voltar
        print("\n───")
        botoes_pos_duvida = ["💬 Continuar dúvida", "🔙 Voltar ao menu"]
        mostrar_botoes(botoes_pos_duvida, "  [0] Sair")
        tela_atual = "pos_duvida"

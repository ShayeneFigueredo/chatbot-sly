"""
nlp.py — Detector de Intenções da Maya (NLP sem gastar tokens!)
Classifica a mensagem do cliente em 7 intenções usando palavras-chave.
"""


def detectar_intencao(texto: str) -> str:
    """
    Lê a mensagem do cliente e retorna a intenção.

    Intenções possíveis:
    - preco           (quanto custa, valor, desconto, de graça)
    - buscar_tema     (tem X?, quero X, sobre X)
    - prazo           (pra hoje, urgente, prazo, amanhã)
    - listar_temas    (quais temas, catálogo, todos)
    - suporte_tecnico (comprei, erro, não consigo, editar, página)
    - ajuda_montagem  (ajuda a fazer, montar, não sei editar)
    - duvida          (qualquer outra coisa → cai na IA)
    """
    t = texto.lower().strip()

    # ── DÚVIDA FORÇADA (palavras que NÃO são busca de tema) ──
    # Estas palavras indicam pergunta sobre políticas, features, etc.
    palavras_duvida_forcada = [
        "cancelar", "cancelamento", "reembolso", "revender",
        "música", "musica", "nota fiscal", "faz logo", "fazer logo",
        "cria logo", "criar logo", "fazem logo", "vocês fazem logo",
        "estudante", "vaga de emprego", "emprego",
        "seguro", "confiável", "confiavel", "parcelar",
        "parcelado", "picpay", "revisão", "revisao",
        "refazer", "garantia", "imprimir", "desconto",
        "cupom", "cartão", "cartao", "forma de pagamento",
        "aceita", "trocar", "troca",
        "de graça", "de graca", "grátis", "gratis", "graca",
    ]
    if any(p in t for p in palavras_duvida_forcada):
        return "duvida"

    # ── PRECO ── (apenas consultas DIRETAS de preço)
    palavras_preco = [
        "quanto custa", "preço", "preco", "valor",
        "custa quanto", "qual o valor", "taxa",
    ]
    if any(p in t for p in palavras_preco):
        return "preco"

    # ── AJUDA MONTAGEM ──
    palavras_ajuda = [
        "ajuda a fazer", "ajudar a fazer", "me ajuda",
        "montar", "como faz", "não sei",
        "nao sei", "não sei fazer", "nao sei fazer",
        "pode fazer", "faz pra mim", "faz para mim",
    ]
    if any(p in t for p in palavras_ajuda):
        return "ajuda_montagem"

    # ── SUPORTE TÉCNICO ──
    palavras_suporte = [
        "comprei", "não consigo abrir", "nao consigo abrir",
        "deu erro", "não chegou", "nao chegou", "não recebi",
        "nao recebi", "link quebrado", "problema pra abrir",
        "adicionar", "página", "pagina", "trocar nome",
        "editar", "como abrir", "como editar", "problema",
        "não funciona", "nao funciona",
    ]
    if any(p in t for p in palavras_suporte):
        return "suporte_tecnico"

    # ── PRAZO ──
    palavras_prazo = [
        "pra hoje", "pra amanhã", "pra amanha", "urgente",
        "prazo", "prazo", "mesmo dia", "rapido", "rápido",
        "hj", "hoje", "amanhã", "amanha", "consegue pra hoje",
        "até as", "ate as", "entrega", "final de semana",
    ]
    if any(p in t for p in palavras_prazo):
        return "prazo"

    # ── LISTAR TEMAS ──
    palavras_listar = [
        "quais temas", "todos temas", "todos os temas",
        "catálogo", "catalogo", "o que tem", "o que vcs tem",
        "quais slides", "lista de temas",
    ]
    if any(p in t for p in palavras_listar):
        return "listar_temas"

    # ── BUSCAR TEMA ── (só ativa pra frases CURTAS de busca)
    palavras_buscar = [
        "tem ", "tema ", "faz de ", "faz sobre ",
        "procurando", "procuro",
        "vcs tem", "vocês tem", "voce tem", "vc tem",
    ]
    if any(p in t for p in palavras_buscar):
        return "buscar_tema"

    # "quero/queria" → pode ser busca de tema ou dúvida
    palavras_quero = ["quero ", "queria "]
    if any(p in t for p in palavras_quero):
        # Marcadores de dúvida (palavras que indicam pergunta, não compra)
        duvida_markers = [
            "saber", "explicar", "funciona", "entender",
            "como funciona", "cancelar", "reembolso",
            "trocar", "mudar", "revender", "música",
            "musica", "falar com", "atendente", "humano",
        ]
        if any(m in t for m in duvida_markers):
            return "duvida"
        # Se não tem marcadores de dúvida → é busca/intenção de compra
        return "buscar_tema"

    # ── PERSONALIZADO (não é tema!) ──
    if "personalizado" in t:
        return "duvida"  # vai pro menu onde é tratado

    # ── TEMA DIRETO (frase curta que não bateu em nada) ──
    if len(t.split()) <= 3:
        # Palavras de pergunta → é dúvida, não busca
        perguntas = ["qual", "como", "quem", "onde", "quando", "porque",
                     "por que", "por quê", "será", "sera", "pode", "posso"]
        if any(p in t.split() for p in perguntas):
            return "duvida"
        return "buscar_tema"

    # ── DÚVIDA (fallback) ──
    return "duvida"


# ===== TESTE RÁPIDO =====
if __name__ == "__main__":
    testes = [
        # (frase, intenção esperada)
        ("quanto custa um slide?", "preco"),
        ("qual o valor do pdf?", "preco"),
        ("tem desconto?", "duvida"),  # "desconto" = duvida (IA responde melhor)
        ("faz de graça?", "duvida"),
        ("aceita picpay?", "duvida"),
        ("aceita cartão?", "duvida"),
        ("tem tema do naruto?", "buscar_tema"),
        ("quero um slide de história", "buscar_tema"),
        ("vcs tem spotify?", "buscar_tema"),
        ("faz pra hoje?", "prazo"),
        ("consegue entregar amanhã?", "prazo"),
        ("urgente!!!!", "prazo"),
        ("quais temas vocês tem?", "listar_temas"),
        ("me mostra o catálogo", "listar_temas"),
        ("comprei um slide e não consigo abrir", "suporte_tecnico"),
        ("deu erro no link", "suporte_tecnico"),
        ("como adiciono mais páginas?", "suporte_tecnico"),
        ("me ajuda a fazer o slide?", "ajuda_montagem"),
        ("não sei editar", "ajuda_montagem"),
        ("pode fazer pra mim?", "ajuda_montagem"),
        ("qual a diferença entre canva e ppt?", "duvida"),
        ("o que é slide pdf?", "duvida"),
        # Novos casos — dúvidas forçadas
        ("quero cancelar meu pedido", "duvida"),
        ("tem reembolso?", "duvida"),
        ("posso revender o slide?", "duvida"),
        ("dá pra colocar música?", "duvida"),
        ("vcs fazem logo também?", "duvida"),  # "fazem logo" bate em duvida_forcada
        ("tem desconto pra estudante?", "duvida"),  # "estudante" + "desconto" = duvida
        ("tem cupom?", "duvida"),  # "cupom" = duvida
        ("como posso parcelar?", "duvida"),
        ("vocês emitem nota fiscal?", "duvida"),
        ("dá pra imprimir o slide?", "duvida"),
        ("se eu não gostar, refaz?", "duvida"),
        ("faz final de semana?", "prazo"),
    ]

    acertos = 0
    for frase, esperada in testes:
        resultado = detectar_intencao(frase)
        ok = "✅" if resultado == esperada else "❌"
        if resultado == esperada:
            acertos += 1
        print(f"{ok} '{frase}' → {resultado} (esperado: {esperada})")

    print(f"\n{acertos}/{len(testes)} testes passaram!")

"""
BUSCADOR INTELIGENTE DE TEMAS - SLY DESIGN
Acha temas mesmo com erro de digitação, sem acento, singular/plural.

Usa difflib (já vem no Python, não precisa instalar nada).
"""
import csv
import difflib
import unicodedata


def normalizar(texto):
    """Remove acentos e deixa tudo minúsculo.
    'Fotossíntese' → 'fotossintese'
    'Revolução'    → 'revolucao'
    """
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def carregar_temas(arquivo_csv="app/data/temas-sly.csv"):
    """Lê o CSV e devolve lista de dicionários com os temas."""
    temas = []
    with open(arquivo_csv, newline="", encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            temas.append(linha)
    return temas


def buscar_tema( texto_cliente: str, tolerancia: float = 0.6):
    """
    Busca um tema no catálogo.
    tolerancia: 0.0 = só match exato | 1.0 = aceita qualquer coisa
    0.5 = pega erros de digitação e palavras parciais

    Estratégia:
    1. Tenta match com o nome completo (ex: 'sistema solar')
    2. Se não achar, tenta match PALAVRA POR PALAVRA (ex: 'nazismo' dentro de 'ascensao do nazismo')
    """
    temas = carregar_temas()
    texto_normalizado = normalizar(texto_cliente)
    palavras_busca = texto_normalizado.split()

    # --- Estratégia 1: match com o nome completo ---
    nomes_normalizados = [normalizar(t["tema"]) for t in temas]
    matches = difflib.get_close_matches(
        texto_normalizado, nomes_normalizados, n=5, cutoff=tolerancia
    )

    # --- Estratégia 2: match por palavra (útil pra 'nazismo' achar 'ascensao do nazismo') ---
    if not matches:
        for palavra in palavras_busca:
            if len(palavra) < 5:  # só palavras com 5+ letras (evita 'mo' achar 'modernismo')
                continue
            for i, nome_norm in enumerate(nomes_normalizados):
                # A palavra precisa estar DENTRO do nome, como parte inteira
                # Ex: 'nazismo' está dentro de 'ascensao do nazismo' ✓
                #     'batata' NÃO está dentro de 'canada' ✗
                if palavra in nome_norm.split() or palavra in nome_norm.replace(" ", ""):
                    if nome_norm not in matches:
                        matches.append(nome_norm)

    resultados = []
    for match_nome in matches:
        idx = nomes_normalizados.index(match_nome)
        resultados.append(temas[idx])

    if not resultados:
        return None, []

    return resultados[0], resultados  # primeiro = melhor match


# ===== TESTE RÁPIDO =====
if __name__ == "__main__":
    # Simula clientes digitando de qualquer jeito
    testes = [
        "fotossintese",      # sem acento
        "equinodermo",        # singular vs plural
        "fotosintese",        # erro de digitação
        "revolucao russa",    # sem acento
        "nazismo",            # palavra parcial
        "batata",             # não existe
        "sistema solar",      # com espaço a mais
    ]

    for busca in testes:
        melhor, todos = buscar_tema(busca)
        if melhor:
            print(f"🔍 '{busca}' → ✅ '{melhor['tema']}' ({melhor['link']})")
        else:
            print(f"🔍 '{busca}' → ❌ Nenhum tema encontrado")

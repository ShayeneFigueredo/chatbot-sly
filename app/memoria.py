"""
memoria.py — Gerencia o histórico, tokens, e persistência da conversa.
"""
import os
import json


ARQUIVO_MEMORIA = "app/data/memoria_conversa.json"


def salvar_conversa(historico, tela_atual, dados_pedido):
    """Salva a conversa num arquivo JSON. Se o programa fechar, não perde!"""
    os.makedirs(os.path.dirname(ARQUIVO_MEMORIA), exist_ok=True)
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
    Regra: 1 token ≈ 4 caracteres em português (Llama usa BPE)."""
    total_chars = 0
    for msg in historico:
        total_chars += len(msg.get("content", ""))
    return total_chars // 4


def resumir_se_precisar(historico, max_tokens=7000):
    """Se o histórico tiver tokens DEMAIS, remove as mensagens mais antigas.
    Mas SEMPRE mantém o system prompt (mensagem 0)."""
    while contar_tokens_aproximado(historico) > max_tokens and len(historico) > 3:
        removida = historico.pop(1)
        print(f"  🧹 [Memória cheia! Removendo mensagem antiga: "
              f"\"{removida.get('content', '')[:40]}...\"]")
    return historico


def bot_falou(historico, texto, tela_atual, dados_pedido):
    """Registra que a Maya falou algo + salva a conversa + mostra tokens."""
    historico.append({"role": "assistant", "content": texto})
    salvar_conversa(historico, tela_atual, dados_pedido)
    tokens = contar_tokens_aproximado(historico)
    if tokens > 5000:
        print(f"  📊 [Tokens: ~{tokens} | ⚠️ Memória quase cheia!]")
    else:
        print(f"  📊 [Tokens: ~{tokens}]")


def cliente_falou(historico, texto, tela_atual, dados_pedido):
    """Registra o que o cliente disse e salva."""
    historico.append({"role": "user", "content": texto})
    salvar_conversa(historico, tela_atual, dados_pedido)

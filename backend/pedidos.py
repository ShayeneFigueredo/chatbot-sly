"""
pedidos.py — Sistema de gestao de pedidos integrado ao painel.
Armazena em JSON e calcula faturamento mensal.
"""
import json
import os
from datetime import datetime

ARQUIVO = os.path.join(os.path.dirname(__file__), "pedidos.json")

MESES = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]


def _carregar():
    if not os.path.exists(ARQUIVO):
        return {"pedidos": [], "faturamento_site": {}}
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def _salvar(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def adicionar(dados: dict) -> dict:
    """Adiciona um pedido. Retorna o pedido com ID."""
    db = _carregar()
    agora = datetime.now()
    mes = dados.get("mes", agora.month)

    pedido = {
        "id": len(db["pedidos"]) + 1,
        "data": dados.get("data", agora.strftime("%d/%m")),
        "entrega": dados.get("entrega", dados.get("data", agora.strftime("%d/%m"))),
        "cliente": dados.get("cliente", dados.get("telefone", "")),
        "arquivo": dados.get("arquivo", dados.get("modelo", "")),
        "tema": dados.get("tema", ""),
        "valor": dados.get("valor", ""),
        "situacao": dados.get("situacao", "Novo"),
        "pg": dados.get("pg", "50% pago"),
        "responsavel": dados.get("responsavel", "SF"),
        "origem": dados.get("origem", "whatsapp"),
        "mes": mes,
    }
    db["pedidos"].append(pedido)
    _salvar(db)
    return pedido


def listar_por_mes(mes: int = None):
    """Lista pedidos do mes (1-12). Se None, lista todos."""
    db = _carregar()
    if mes:
        return [p for p in db["pedidos"] if p.get("mes") == mes]
    return db["pedidos"]


def faturamento():
    """Calcula faturamento: total por mes, total site, total geral."""
    db = _carregar()
    fat = {}
    for m in range(1, 13):
        fat[m] = {"pedidos": 0.0, "site": 0.0}

    for p in db["pedidos"]:
        m = p.get("mes", 1)
        try:
            val = float(p.get("valor", "0").replace("R$", "").replace(",", ".").strip())
            fat[m]["pedidos"] += val
        except (ValueError, AttributeError):
            pass

    for m_str, val in db.get("faturamento_site", {}).items():
        m = int(m_str)
        fat[m]["site"] = float(val)

    # Calcula totais
    for m in range(1, 13):
        fat[m]["total"] = fat[m]["pedidos"] + fat[m]["site"]

    total_ano = sum(fat[m]["total"] for m in range(1, 13))
    total_shay = 0.0
    total_samuel = 0.0
    for p in db["pedidos"]:
        try:
            val = float(p.get("valor", "0").replace("R$", "").replace(",", ".").strip())
            if p.get("responsavel") == "SA":
                total_samuel += val
            else:
                total_shay += val
        except (ValueError, AttributeError):
            pass

    return {
        "mensal": fat,
        "total_ano": round(total_ano, 2),
        "total_shay": round(total_shay, 2),
        "total_samuel": round(total_samuel, 2),
        "total_site": round(sum(fat[m]["site"] for m in range(1, 13)), 2),
    }


def atualizar_situacao(pedido_id: int, situacao: str):
    """Atualiza situacao de um pedido."""
    db = _carregar()
    for p in db["pedidos"]:
        if p["id"] == pedido_id:
            p["situacao"] = situacao
            p["pg"] = "Pago" if situacao == "Feito" else p.get("pg", "")
            break
    _salvar(db)


def adicionar_faturamento_site(mes: int, valor: float):
    """Adiciona/atualiza faturamento do site em um mes."""
    db = _carregar()
    db.setdefault("faturamento_site", {})[str(mes)] = round(valor, 2)
    _salvar(db)


def ultimo_id():
    db = _carregar()
    return len(db["pedidos"])

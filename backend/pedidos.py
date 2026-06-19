"""
pedidos.py — Sistema de gestao de pedidos integrado ao painel.
Armazena em JSON e calcula faturamento mensal.
"""
import json
import os
from datetime import datetime
import requests
import time as _time

# No Render, salva no disco persistente; localmente usa a pasta backend
_RENDER_DISK = "/app/auth_info_baileys"
_ARQUIVO_LOCAL = os.path.join(os.path.dirname(__file__), "pedidos.json")
if os.path.exists(_RENDER_DISK):
    ARQUIVO = os.path.join(_RENDER_DISK, "pedidos.json")
    # Migracao: se o disk estiver vazio mas existir local, copia
    if not os.path.exists(ARQUIVO) and os.path.exists(_ARQUIVO_LOCAL):
        import shutil
        shutil.copy2(_ARQUIVO_LOCAL, ARQUIVO)
        print(f"📦 pedidos.json migrado para disco persistente: {ARQUIVO}")
    # Se nao existir em nenhum lugar, cria vazio
    if not os.path.exists(ARQUIVO):
        with open(ARQUIVO, "w") as f:
            json.dump({"pedidos": [], "faturamento_site": {}}, f)
        print(f"📄 pedidos.json criado no disco persistente: {ARQUIVO}")
else:
    ARQUIVO = _ARQUIVO_LOCAL

MESES = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Cache da data real (evita chamadas repetidas a API)
_real_date_cache = {"date": None, "ts": 0}

def _obter_data_real() -> datetime:
    """Obtem a data/hora real de uma API externa (worldtimeapi.org).
    Com fallback para datetime.now() se a API falhar.
    O resultado fica em cache por 5 minutos."""
    agora = _time.time()
    if _real_date_cache["date"] and (agora - _real_date_cache["ts"]) < 300:
        return _real_date_cache["date"]
    try:
        resp = requests.get(
            "https://worldtimeapi.org/api/timezone/America/Sao_Paulo",
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            dt = datetime.fromisoformat(data["datetime"])
            _real_date_cache["date"] = dt
            _real_date_cache["ts"] = agora
            return dt
    except Exception:
        pass
    # Fallback: usa datetime.now() do servidor
    dt = datetime.now()
    _real_date_cache["date"] = dt
    _real_date_cache["ts"] = agora
    return dt

def hoje_str() -> str:
    """Retorna a data de hoje no formato dd/mm, usando API externa."""
    return _obter_data_real().strftime("%d/%m")

def mes_atual() -> int:
    """Retorna o mes atual (1-12), usando API externa."""
    return _obter_data_real().month

def ano_atual() -> int:
    """Retorna o ano atual, usando API externa."""
    return _obter_data_real().year


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
    agora = _obter_data_real()
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
        # Site tem faturamento separado, nao entra em "pedidos"
        if p.get("origem") == "site":
            continue
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

    # Filtra pedidos de teste (Shayene / Samuel Amorim)
    def _eh_teste(p):
        nome = (p.get("cliente", "") or "").lower()
        return any(t in nome for t in ["shayene", "samuel amorim"])

    total_ano = sum(fat[m]["total"] for m in range(1, 13))
    total_shay = 0.0
    total_samuel = 0.0
    a_receber = 0.0
    for p in db["pedidos"]:
        if _eh_teste(p):
            continue
        # Site nao entra no total Shay/Samuel (vai separado)
        if p.get("origem") == "site":
            continue
        try:
            val = float(p.get("valor", "0").replace("R$", "").replace(",", ".").strip())
            if p.get("responsavel") == "SA":
                total_samuel += val
            else:
                total_shay += val
            # Calcula 50% restante para pedidos nao pagos totalmente
            if p.get("pg", "") in ("50% pago", "Aguardando"):
                a_receber += val * 0.5
        except (ValueError, AttributeError):
            pass

    # Calcula bruto do site (sem taxas, ignora testes)
    site_bruto = 0.0
    for p in db["pedidos"]:
        if p.get("origem") == "site" and not _eh_teste(p):
            try:
                site_bruto += float(p.get("valor", "0").replace("R$", "").replace(",", ".").strip())
            except (ValueError, AttributeError):
                pass

    total_site_liquido = round(sum(fat[m]["site"] for m in range(1, 13)), 2)
    return {
        "mensal": fat,
        "total_ano": round(total_ano, 2),
        "total_shay": round(total_shay, 2),
        "total_samuel": round(total_samuel, 2),
        "total_site": total_site_liquido,
        "total_site_bruto": round(site_bruto, 2),
        "taxas_site": round(site_bruto - total_site_liquido, 2),
        "a_receber": round(a_receber, 2),
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

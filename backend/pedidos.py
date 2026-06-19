"""
pedidos.py — Sistema de gestao de pedidos integrado ao painel.
Armazena em SQLite e calcula faturamento mensal.
Arquivo: /app/auth_info_baileys/pedidos.db (Render) ou backend/pedidos.db (local)
"""
import sqlite3
import json
import os
import shutil
import hashlib
from datetime import datetime
import requests
import time as _time

# ── Caminho do banco ──
_RENDER_DISK = "/app/auth_info_baileys"
_ARQUIVO_LOCAL = os.path.join(os.path.dirname(__file__), "pedidos.db")
_ARQUIVO_JSON_ANTIGO = os.path.join(os.path.dirname(__file__), "pedidos.json")

if os.path.exists(_RENDER_DISK):
    DB_PATH = os.path.join(_RENDER_DISK, "pedidos.db")
else:
    DB_PATH = _ARQUIVO_LOCAL

MESES = [
    "", "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Cache da data real
_real_date_cache = {"date": None, "ts": 0}


def _get_db() -> sqlite3.Connection:
    """Retorna conexao com o banco (autocommit via WAL mode)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _init_db():
    """Cria tabelas se nao existirem e migra dados do JSON antigo ou DB do build."""
    print(f"🗄️  DB_PATH={DB_PATH} | RENDER_DISK={'SIM' if os.path.exists(_RENDER_DISK) else 'NAO'} | LOCAL={_ARQUIVO_LOCAL}")
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            entrega TEXT,
            cliente TEXT NOT NULL,
            arquivo TEXT,
            tema TEXT,
            tema_design TEXT,
            valor TEXT,
            situacao TEXT DEFAULT 'Novo',
            pg TEXT DEFAULT '50% pago',
            responsavel TEXT DEFAULT 'SF',
            origem TEXT DEFAULT 'whatsapp',
            mes INTEGER DEFAULT 1,
            nomes TEXT,
            extras TEXT
        );
        CREATE TABLE IF NOT EXISTS faturamento_site (
            mes INTEGER PRIMARY KEY,
            valor REAL NOT NULL
        );
    """)
    conn.commit()

    ja_migrou = conn.execute("SELECT COUNT(*) as c FROM pedidos").fetchone()["c"] > 0

    # Sincroniza DB do build → disco se forem diferentes
    if os.path.exists(_RENDER_DISK) and os.path.exists(_ARQUIVO_LOCAL) and DB_PATH != _ARQUIVO_LOCAL:
        try:
            build_hash = hashlib.md5(open(_ARQUIVO_LOCAL, 'rb').read()).hexdigest()
            disk_hash = hashlib.md5(open(DB_PATH, 'rb').read()).hexdigest() if os.path.exists(DB_PATH) else ""
        except:
            build_hash = disk_hash = ""
        if build_hash != disk_hash:
            conn.close()
            for suffix in ["-wal", "-shm"]:
                try: os.remove(DB_PATH + suffix)
                except: pass
            try:
                shutil.copy2(_ARQUIVO_LOCAL, DB_PATH)
                build_conn = sqlite3.connect(DB_PATH)
                n = build_conn.execute("SELECT COUNT(*) as c FROM pedidos").fetchone()[0]
                build_conn.close()
                print(f"📦 DB sincronizado build→disco ({n} pedidos)")
            except Exception as e:
                print(f"⚠️ Erro ao copiar DB do build: {e}")
            conn = _get_db()
            ja_migrou = True

    if not ja_migrou and os.path.exists(_ARQUIVO_JSON_ANTIGO):
        try:
            with open(_ARQUIVO_JSON_ANTIGO, "r", encoding="utf-8") as f:
                old = json.load(f)
            for p in old.get("pedidos", []):
                conn.execute("""
                    INSERT INTO pedidos (id, data, entrega, cliente, arquivo, tema, valor,
                                         situacao, pg, responsavel, origem, mes, nomes, extras)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    p.get("id"), p.get("data",""), p.get("entrega",""),
                    p.get("cliente",""), p.get("arquivo",""), p.get("tema",""),
                    p.get("valor",""), p.get("situacao","Novo"), p.get("pg","50% pago"),
                    p.get("responsavel","SF"), p.get("origem","whatsapp"),
                    p.get("mes",1), p.get("nomes",""), p.get("extras","")
                ))
            for mes_str, val in old.get("faturamento_site", {}).items():
                conn.execute("INSERT OR REPLACE INTO faturamento_site (mes, valor) VALUES (?,?)",
                             (int(mes_str), float(val)))
            conn.commit()
            print(f"📦 SQLite: {len(old.get('pedidos',[]))} pedidos migrados do JSON")
            os.rename(_ARQUIVO_JSON_ANTIGO, _ARQUIVO_JSON_ANTIGO + ".backup")
        except Exception as e:
            print(f"⚠️ Erro na migracao JSON→SQLite: {e}")

    conn.close()


# Inicializa na importacao
_init_db()


# ── Data real (timezone Sao Paulo) ──

def _obter_data_real() -> datetime:
    agora = _time.time()
    if _real_date_cache["date"] and (agora - _real_date_cache["ts"]) < 300:
        return _real_date_cache["date"]
    try:
        resp = requests.get(
            "https://worldtimeapi.org/api/timezone/America/Sao_Paulo", timeout=5
        )
        if resp.status_code == 200:
            dt = datetime.fromisoformat(resp.json()["datetime"])
            _real_date_cache["date"] = dt
            _real_date_cache["ts"] = agora
            return dt
    except Exception:
        pass
    dt = datetime.now()
    _real_date_cache["date"] = dt
    _real_date_cache["ts"] = agora
    return dt


def hoje_str() -> str:
    return _obter_data_real().strftime("%d/%m")


def mes_atual() -> int:
    return _obter_data_real().month


def ano_atual() -> int:
    return _obter_data_real().year


# ── CRUD ──

def _carregar():
    """Retorna dict no formato antigo (compatibilidade com webhook_server.py)."""
    conn = _get_db()
    pedidos = [dict(r) for r in conn.execute("SELECT * FROM pedidos ORDER BY id").fetchall()]
    site = {str(r["mes"]): r["valor"] for r in conn.execute("SELECT * FROM faturamento_site").fetchall()}
    conn.close()
    return {"pedidos": pedidos, "faturamento_site": site}


def _salvar(dados: dict):
    """Substitui todos os dados (compatibilidade com webhook_server.py)."""
    conn = _get_db()
    conn.execute("DELETE FROM pedidos")
    conn.execute("DELETE FROM faturamento_site")
    for p in dados.get("pedidos", []):
        conn.execute("""
            INSERT INTO pedidos (id, data, entrega, cliente, arquivo, tema, valor,
                                 situacao, pg, responsavel, origem, mes, nomes, extras)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            p.get("id"), p.get("data",""), p.get("entrega",""),
            p.get("cliente",""), p.get("arquivo",""), p.get("tema",""),
            p.get("valor",""), p.get("situacao","Novo"), p.get("pg","50% pago"),
            p.get("responsavel","SF"), p.get("origem","whatsapp"),
            p.get("mes",1), p.get("nomes",""), p.get("extras","")
        ))
    for mes_str, val in dados.get("faturamento_site", {}).items():
        conn.execute("INSERT INTO faturamento_site (mes, valor) VALUES (?,?)",
                     (int(mes_str), float(val)))
    conn.commit()
    conn.close()


def adicionar(dados: dict) -> dict:
    agora = _obter_data_real()
    mes = dados.get("mes", agora.month)
    pedido = {
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
        "nomes": dados.get("nomes", ""),
        "extras": dados.get("extras", ""),
    }
    conn = _get_db()
    cur = conn.execute("""
        INSERT INTO pedidos (data, entrega, cliente, arquivo, tema, valor,
                             situacao, pg, responsavel, origem, mes, nomes, extras)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        pedido["data"], pedido["entrega"], pedido["cliente"], pedido["arquivo"],
        pedido["tema"], pedido["valor"], pedido["situacao"], pedido["pg"],
        pedido["responsavel"], pedido["origem"], pedido["mes"],
        pedido["nomes"], pedido["extras"]
    ))
    pedido["id"] = cur.lastrowid
    conn.commit()
    conn.close()
    return pedido


def listar_por_mes(mes: int = None):
    conn = _get_db()
    if mes:
        rows = conn.execute("SELECT * FROM pedidos WHERE mes = ? ORDER BY entrega", (mes,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM pedidos ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def faturamento():
    conn = _get_db()
    fat = {m: {"pedidos": 0.0, "site": 0.0} for m in range(1, 13)}

    # Pedidos (nao-site)
    rows = conn.execute("""
        SELECT mes, valor, responsavel, pg, cliente, origem
        FROM pedidos
    """).fetchall()

    def _eh_teste(cliente):
        return any(t in (cliente or "").lower() for t in ["shayene", "samuel amorim"])

    def _parse_valor(v):
        try:
            return float((v or "0").replace("R$", "").replace(",", ".").strip())
        except (ValueError, AttributeError):
            return 0.0

    total_shay = 0.0
    total_samuel = 0.0
    a_receber = 0.0
    site_bruto = 0.0

    for r in rows:
        m = r["mes"] or 1
        val = _parse_valor(r["valor"])
        if r["origem"] == "site":
            if not _eh_teste(r["cliente"]):
                site_bruto += val
            continue
        fat[m]["pedidos"] += val
        if not _eh_teste(r["cliente"]):
            if r["responsavel"] == "SA":
                total_samuel += val
            else:
                total_shay += val
            if r["pg"] in ("50% pago", "Aguardando"):
                a_receber += val * 0.5

    # Site faturamento (tabela separada)
    for r in conn.execute("SELECT * FROM faturamento_site").fetchall():
        fat[r["mes"]]["site"] = r["valor"]

    for m in range(1, 13):
        fat[m]["total"] = fat[m]["pedidos"] + fat[m]["site"]

    total_ano = sum(fat[m]["total"] for m in range(1, 13))
    total_site_liquido = sum(fat[m]["site"] for m in range(1, 13))

    conn.close()
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
    conn = _get_db()
    pg = "Pago" if situacao == "Feito" else None
    if pg:
        conn.execute("UPDATE pedidos SET situacao=?, pg=? WHERE id=?",
                     (situacao, pg, pedido_id))
    else:
        conn.execute("UPDATE pedidos SET situacao=? WHERE id=?",
                     (situacao, pedido_id))
    conn.commit()
    conn.close()


def adicionar_faturamento_site(mes: int, valor: float):
    conn = _get_db()
    conn.execute("INSERT OR REPLACE INTO faturamento_site (mes, valor) VALUES (?,?)",
                 (mes, round(valor, 2)))
    conn.commit()
    conn.close()


def ultimo_id():
    conn = _get_db()
    r = conn.execute("SELECT MAX(id) as m FROM pedidos").fetchone()
    conn.close()
    return r["m"] or 0


def editar_pedido(pedido_id: int, dados: dict):
    """Atualiza campos editaveis de um pedido."""
    conn = _get_db()
    campos = ["data", "entrega", "cliente", "arquivo", "tema", "tema_design",
              "valor", "situacao", "pg", "responsavel", "mes", "nomes", "extras"]
    sets = []
    vals = []
    for c in campos:
        if c in dados:
            sets.append(f"{c}=?")
            vals.append(dados[c])
    if sets:
        vals.append(pedido_id)
        conn.execute(f"UPDATE pedidos SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
    conn.close()


def deletar_pedido(pedido_id: int):
    conn = _get_db()
    conn.execute("DELETE FROM pedidos WHERE id=?", (pedido_id,))
    conn.commit()
    conn.close()

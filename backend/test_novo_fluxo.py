"""
Teste do novo fluxo de boas-vindas da Maya.
Simula as 3 conversas problematicas para verificar se o novo fluxo resolve.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.webhook_server import maya_responder, clientes, atendimento_humano


def limpar_estado():
    clientes.clear()
    atendimento_humano.clear()


def simular_conversa(numero, mensagens, titulo):
    """Simula uma conversa com a Maya e imprime cada troca."""
    limpar_estado()
    print(f"\n{'='*60}")
    print(f"🧪 TESTE: {titulo}")
    print(f"{'='*60}")

    for i, msg in enumerate(mensagens):
        resp = maya_responder(msg, numero)
        if resp is None:
            resp_str = "🔇 (Maya silenciada)"
        else:
            resp_str = resp[:120] + ("..." if len(resp) > 120 else "")
        print(f"\n👤 [{i+1}] {msg}")
        print(f"🤖 Maya: {resp_str}")

    # Mostra estado final
    if numero in clientes:
        est = clientes[numero]
        dados = est.get("dados_pedido", {})
        print(f"\n📊 Estado final: tela={est['tela']}")
        print(f"   Dados: tema={dados.get('tema','?')} | modelo={dados.get('modelo','?')} | nomes={dados.get('nomes','?')} | prazo={dados.get('prazo','?')}")


# ═══════════════════════════════════════════════
# TESTE 1: Chat da Fran (Chat 3 — o pior caso)
# Problema original: "2" virou tema, "Simm" virou nome, dados todos errados
# ═══════════════════════════════════════════════
simular_conversa(
    "+558597241556",
    [
        "Olá bom dia",
        "Boa tarde",
        "Sou a Fran",
        "2",                    # Deveria ir pra boas-vindas → Maya
        "ok entendi",           # Deveria ir pra explicacao → Ok → menu
        "2",                    # Agora sim: menu → pedido personalizado
        "Crise de 1929 — Trabalho de História",  # Tema
        "2",                    # Canva Transições
        "Até quinta feira data 11/06",            # Prazo
        "Francielly e Maria",                     # Nomes
        "Quero adicionar fotos no final e referências",  # Extras
        "3",                    # Finalizar
        "1",                    # Confirmar
    ],
    "Chat da Fran — da bagunça ao pedido correto"
)


# ═══════════════════════════════════════════════
# TESTE 2: Chat do CRISPR (Chat 1)
# Problema original: menu duplicado, "FALAR COM HUMANO" confuso
# ═══════════════════════════════════════════════
simular_conversa(
    "+559885997971",
    [
        "oiii",
        "bom dia",
        "2",                    # Escolhe Maya
        "ok entendi",           # Entendeu
        "2",                    # Slide personalizado
        "Tecnologias de edição genética CRISPR",
        "2",                    # Canva
        "até hoje as 13h",      # Urgente
        "Victor, Francisco, Edinailson, Jonatas, Karleilson, Loruan, Kemilly",
        "3",                    # Finalizar extras
        # Agora simula "FALAR COM HUMANO" no resumo
        "FALAR COM HUMANO",
    ],
    "Chat CRISPR — fluxo normal + pedido de humano no resumo"
)


# ═══════════════════════════════════════════════
# TESTE 3: Chat do Slide pra Sexta (Chat 2)
# Problema original: Maya confusa, cliente ecoou mensagens
# ═══════════════════════════════════════════════
simular_conversa(
    "+5522991016567",
    [
        "bom dia",
        "2",                    # Escolhe Maya
        "ok",                   # Entendeu
        "teria como fazer um slide para sexta?",  # NLP → prazo
        "2",                    # Fazer pedido
        "Direito Constitucional — Controle de Constitucionalidade",
        "1",                    # PDF
        "consegue entregar até quinta?",
        "João e Pedro",
        "3",                    # Finalizar extras
        "1",                    # Confirmar
    ],
    "Chat Slide pra Sexta — cliente pergunta antes de começar pedido"
)


# ═══════════════════════════════════════════════
# TESTE 4: Cliente escolhe HUMANO primeiro, depois muda pra Maya
# ═══════════════════════════════════════════════
simular_conversa(
    "+551199999999",
    [
        "oi",
        "1",                    # Humano!
        "alguem me responde?",  # Deveria ser IGNORADO (Maya travada)
        "cade vcs????",         # Deveria ser IGNORADO
        "2",                    # Destrava → Maya
        "sim, entendi",         # Ok → menu
        "4",                    # Quanto custa?
    ],
    "Humano → travado → destrava Maya"
)


# ═══════════════════════════════════════════════
# TESTE 5: Cliente escreve "maya" pra destravar do aguardando humano
# ═══════════════════════════════════════════════
simular_conversa(
    "+551198888888",
    [
        "Boa noite",
        "quero falar com uma pessoa",
        "cade vcs",             # IGNORADO
        "por favor maya",       # Destrava (contém "maya")
        "pronto",               # Ok → menu
        "3",                    # Consultar tema
        "harry potter",         # Busca
    ],
    "Destrava com 'maya' escrito na mensagem"
)


print("\n\n" + "="*60)
print("✅ TODOS OS TESTES CONCLUÍDOS!")
print("="*60)
print("\nVerifique manualmente se:")
print("1. ❌ Nenhum dado errado nos pedidos (tema='2', nomes='Simm')")
print("2. ✅ Menu NUNCA aparece duplicado")
print("3. ✅ Clientes em aguardando_humano NÃO recebem resposta da Maya")
print("4. ✅ 'maya' ou '2' destravam o aguardando_humano")
print("5. ✅ Explicação aparece ANTES do menu com 5 opções")
print("6. ✅ Fluxo de pedido funciona normalmente depois do menu")

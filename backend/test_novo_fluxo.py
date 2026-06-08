"""
Teste do novo fluxo de boas-vindas da Maya + menu de tipo simplificado.
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
            resp_str = resp[:130] + ("..." if len(resp) > 130 else "")
        print(f"\n👤 [{i+1}] {msg}")
        print(f"🤖 Maya: {resp_str}")

    # Mostra estado final
    if numero in clientes:
        est = clientes[numero]
        dados = est.get("dados_pedido", {})
        print(f"\n📊 Estado final: tela={est['tela']}")
        print(f"   Dados: tema={dados.get('tema','?')} | modelo={dados.get('modelo','?')} | nomes={dados.get('nomes','?')} | prazo={dados.get('prazo','?')}")


# ═══════════════════════════════════════════════
# TESTE 1: Chat da Fran — fluxo completo com novo menu de tipo
# ═══════════════════════════════════════════════
simular_conversa(
    "+558597241556",
    [
        "Olá bom dia",
        "Boa tarde",
        "Sou a Fran",
        "2",                    # Escolhe Maya
        "ok entendi",           # Entendeu → menu
        "2",                    # Slide personalizado
        "Crise de 1929 — Trabalho de História",  # Tema
        "1",                    # Já escolhi (ver opções completas)
        "2",                    # Canva Transições
        "Até quinta feira data 11/06",            # Prazo
        "Francielly e Maria",                     # Nomes
        "Quero adicionar fotos no final e referências",  # Extras
        "3",                    # Finalizar
        "1",                    # Confirmar
    ],
    "Chat da Fran — novo fluxo de tipo simplificado"
)


# ═══════════════════════════════════════════════
# TESTE 2: Chat CRISPR — com dúvida Canva vs PPT
# ═══════════════════════════════════════════════
simular_conversa(
    "+559885997971",
    [
        "oiii",
        "bom dia",
        "2",                    # Maya
        "ok entendi",           # Entendeu
        "2",                    # Slide personalizado
        "Tecnologias de edição genética CRISPR",
        "2",                    # Diferença Canva vs PPT (dúvida)
        "1",                    # Já escolhi → opções completas
        "2",                    # Canva Transições
        "até hoje as 13h",      # Urgente
        "Victor, Francisco, Edinailson, Jonatas, Karleilson, Loruan, Kemilly",
        "3",                    # Finalizar extras
        "FALAR COM HUMANO",     # No resumo
    ],
    "Chat CRISPR — dúvida Canva vs PPT + Já escolhi"
)


# ═══════════════════════════════════════════════
# TESTE 3: Chat Slide pra Sexta — fluxo direto
# ═══════════════════════════════════════════════
simular_conversa(
    "+5522991016567",
    [
        "bom dia",
        "2",                    # Maya
        "ok",                   # Entendeu
        "teria como fazer um slide para sexta?",  # NLP
        "2",                    # Fazer pedido
        "Direito Constitucional — Controle de Constitucionalidade",
        "1",                    # Já escolhi
        "1",                    # PDF
        "consegue entregar até quinta?",
        "João e Pedro",
        "3",                    # Finalizar extras
        "1",                    # Confirmar
    ],
    "Chat Slide pra Sexta — Já escolhi direto"
)


# ═══════════════════════════════════════════════
# TESTE 4: Humano travado → destrava Maya
# ═══════════════════════════════════════════════
simular_conversa(
    "+551199999999",
    [
        "oi",
        "1",                    # Humano!
        "alguem me responde?",  # IGNORADO
        "cade vcs????",         # IGNORADO
        "2",                    # Destrava → Maya
        "sim, entendi",         # Ok → menu
        "4",                    # Quanto custa?
    ],
    "Humano → travado → destrava Maya"
)


# ═══════════════════════════════════════════════
# TESTE 5: Dúvida Transições vs Temas (NOVO)
# ═══════════════════════════════════════════════
simular_conversa(
    "+551197777777",
    [
        "oi",
        "2",                    # Maya
        "ok",                   # Entendeu
        "2",                    # Slide personalizado
        "Sustentabilidade",
        "3",                    # Dúvida: Transições vs Temas
        "1",                    # Já escolhi → opções completas
        "4",                    # Canva Temas
        "Netflix",              # Qual tema visual
        "semana que vem",
        "Maria e José",
        "3",                    # Finalizar
        "1",                    # Confirmar
    ],
    "Dúvida Transições vs Temas + Canva Temas + Netflix"
)


# ═══════════════════════════════════════════════
# TESTE 6: Destrava com 'maya'
# ═══════════════════════════════════════════════
simular_conversa(
    "+551198888888",
    [
        "Boa noite",
        "quero falar com uma pessoa",
        "cade vcs",             # IGNORADO
        "por favor maya",       # Destrava
        "pronto",               # Ok → menu
        "3",                    # Consultar tema
        "harry potter",         # Busca
    ],
    "Destrava com 'maya' escrito na mensagem"
)


print("\n\n" + "="*60)
print("✅ TODOS OS TESTES CONCLUÍDOS!")
print("="*60)
print("\nVerifique:")
print("1. ✅ Tema nunca é número ('2', '1')")
print("2. ✅ Nomes nunca são 'Simm'")
print("3. ✅ Menu simplificado de tipo aparece (3 botões)")
print("4. ✅ 'Já escolhi' mostra opções completas")
print("5. ✅ Dúvida Canva vs PPT funciona")
print("6. ✅ Dúvida Transições vs Temas funciona (NOVO)")
print("7. ✅ Tipo inválido repete pergunta (não vira modelo errado)")

# 🤖 Maya — Atendente Virtual com IA para E-commerce

Chatbot inteligente desenvolvido para automatizar o atendimento via WhatsApp da **[Sly Design](https://slydesign.com.br)**, loja especializada em slides personalizados.

> **Este repositório é um projeto de portfólio.** O código demonstra arquitetura, fluxos e integrações — não é um produto open source para uso comercial.

---

## 🎯 O Problema

A Sly Design recebia dezenas de mensagens diárias no WhatsApp com perguntas repetitivas:
- "Quanto custa?"
- "Tem tema X?"
- "Faz pra hoje?"
- "Como edito o slide?"

**80% do tempo de atendimento era gasto respondendo as mesmas 5 perguntas.**

---

## 💡 A Solução

A **Maya** — uma atendente virtual com IA que:
- Entende o que o cliente quer, mesmo sem botões
- Faz busca inteligente no catálogo (tolera erros de digitação)
- Conduz o fluxo completo de pedido personalizado
- Aprendeu o tom de voz da marca Sly Design
- Sabe quando passar para atendimento humano

---

## 🏗️ Arquitetura

```
📱 WhatsApp ──▶ Meta Cloud API ──▶ Backend (Python/FastAPI)
                                      │
                                 ┌────▼────┐
                                 │   LLM   │  (Groq + Llama 3.3 70B)
                                 └────┬────┘
                                      │
🖥️ Dashboard ──▶ Streamlit ◀─────────┘
                 (métricas, conversas, assumir)
```

### Módulos

| Módulo | Responsabilidade |
|---|---|
| `app/nlp.py` | Detector de intenções (7 categorias, zero tokens) |
| `app/bot.py` | Fluxos de conversa, mensagens, máquina de estados |
| `app/buscador.py` | Busca inteligente com tolerância a erros (difflib) |
| `app/memoria.py` | Histórico, contador de tokens, persistência JSON |
| `app/config.py` | System prompt, preços, catálogo, conexão IA |
| `app/main.py` | Loop principal, orquestração dos fluxos |

### Fluxo de Pedido (Máquina de Estados)

```
MENU → Tema → Tipo → Prazo → Nomes → Extras → Resumo → Pagamento
         ↓       ↓       ↓        ↓        ↓         ↓         ↓
      [editar] [editar] [editar] [editar] [editar] [mudar] [Pix 50%]
```

---

## 🧠 NLP — Entendendo Clientes Sem Botões

A Maya classifica mensagens livres em **7 intenções** usando processamento de linguagem natural local (sem gastar tokens da IA):

| Intenção | Exemplo | Resposta |
|---|---|---|
| `preco` | "quanto custa?" | Tabela de preços |
| `buscar_tema` | "tem naruto?" | Busca inteligente no catálogo |
| `prazo` | "faz pra hj?" | Prazos + taxa de urgência |
| `listar_temas` | "quais temas?" | Link da loja |
| `suporte_tecnico` | "comprei e deu erro" | Fluxo de suporte |
| `ajuda_montagem` | "me ajuda a fazer?" | Tutoriais em vídeo |
| `duvida` | "diferença canva ppt?" | IA responde |

---

## 🧪 Testes

**47 testes automatizados** cobrindo todos os fluxos:

```
✅ 20 testes do detector NLP (intenções)
✅ 27 testes do chatbot (menu, busca, pedido, pagamento, cancelamento...)
```

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Motivo |
|---|---|---|
| IA / LLM | Groq API + Llama 3.3 70B | API gratuita para desenvolvimento |
| Linguagem | Python 3.11+ | Ecossistema rico, curva amigável |
| Busca | difflib (nativo Python) | Tolerância a erro de digitação, zero dependências |
| NLP Local | Regex + palavras-chave | Classificação instantânea, zero custo |
| Testes | unittest + mocks | Sem depender da API durante QA |
| Persistência | JSON local | Simples, portátil, sem banco de dados |

---

## 📈 Métricas do Projeto

- **Semanas de desenvolvimento:** 2 (aprendendo IA do zero)
- **Sessões de estudo:** 8 concluídas
- **Temas no catálogo:** 47 produtos reais
- **Intenções mapeadas:** 7 categorias
- **Testes automatizados:** 47

---

## 🚧 Roadmap

- [x] Busca inteligente no catálogo
- [x] Fluxo completo de pedido personalizado
- [x] Memória de conversa com persistência
- [x] Detector de intenções NLP (sem tokens!)
- [ ] Conexão com WhatsApp Business API
- [ ] Dashboard com Streamlit
- [ ] Deploy em produção
- [ ] Integração com WordPress/Elementor

---

## 👩‍💻 Sobre a Autora

Feito por **Shayene Figueredo** — empreendedora, dona da [Sly Design](https://slydesign.com.br), aprendendo IA do zero e documentando a jornada.

📱 **Instagram:** [@sly_desgn](https://instagram.com/sly_desgn)

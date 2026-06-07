# Maya — Atendente Virtual da Sly Design

Chatbot com IA para atendimento automatizado via WhatsApp da **[Sly Design](https://slydesign.com.br)**, loja especializada em slides personalizados.

---

## O Problema

A Sly Design recebe dezenas de mensagens diarias no WhatsApp com perguntas repetitivas:
- "Quanto custa?"
- "Tem tema X?"
- "Faz pra hoje?"
- "Como edito o slide?"

**80% do tempo de atendimento era gasto respondendo as mesmas 5 perguntas.**

---

## A Solucao

A **Maya** — uma atendente virtual com IA que:
- Entende o que o cliente quer, mesmo sem botoes
- Faz busca inteligente no catalogo (tolera erros de digitacao)
- Conduz o fluxo completo de pedido personalizado
- Detecta quando o cliente envia imagens e orienta o proximo passo
- Mantem contexto da conversa por 7 dias para respostas coerentes
- Sabe quando passar para atendimento humano
- Silencia automaticamente apos confirmacao de pagamento

---

## Arquitetura

```
📱 WhatsApp ──▶ Baileys (WebSocket) ──▶ Backend Python (FastAPI)
                                              │
                                         ┌────▼────┐
                                         │   LLM   │  (Groq + Llama 3.3 70B)
                                         └────┬────┘
                                              │
📤 Notificacoes ──▶ Shay (WhatsApp pessoal) ◀┘
```

### Modulos

| Modulo | Responsabilidade |
|---|---|
| `backend/webhook_server.py` | Servidor principal: maquina de estados, endpoints, fallback IA |
| `connect_whatsapp.js` | Conexao WhatsApp via Baileys, delay natural, ponte de envio |
| `app/nlp.py` | Detector de intencoes — 7 categorias, zero tokens |
| `app/buscador.py` | Busca inteligente no catalogo com tolerancia a erros (difflib) |
| `app/config.py` | System prompt, precos, catalogo, conexao com Groq |

### Maquina de Estados — Fluxo de Pedido

```
MENU → Tema → Tipo → Tema Visual → Prazo → Nomes → Extras → Resumo → Aguardando Pagamento
        ↓       ↓         ↓          ↓        ↓         ↓         ↓              ↓
     [editar] [editar]  [editar]   [editar] [editar]  [editar]  [mudar]    [Maya silencia]
```

---

## NLP — Entendendo Clientes Sem Gastar Tokens

A Maya classifica mensagens em **7 intencoes** usando processamento local, antes de decidir se chama a IA:

| Intencao | Exemplo | Resposta |
|---|---|---|
| `preco` | "quanto custa?" | Tabela de precos completa |
| `buscar_tema` | "tem naruto?" | Busca inteligente no catalogo |
| `prazo` | "faz pra hj?" | Prazos + taxa de urgencia |
| `listar_temas` | "quais temas?" | Link da loja |
| `suporte_tecnico` | "comprei e deu erro" | Fluxo de suporte |
| `ajuda_montagem` | "me ajuda a fazer?" | Links de tutoriais |
| `duvida` | "diferenca canva ppt?" | IA responde com contexto |

---

## Stack Tecnologica

| Camada | Tecnologia | Motivo |
|---|---|---|
| Conexao WhatsApp | Baileys (WebSocket) | Sem navegador, leve, nao requer numero na Meta |
| Backend | Python 3.13 + FastAPI | Performance, tipagem, async nativo |
| IA / LLM | Groq API + Llama 3.3 70B | Gratuito para desenvolvimento, 128K contexto |
| NLP Local | Palavras-chave + regex | Classificacao instantanea, zero custo de tokens |
| Busca | difflib (nativo Python) | Tolerancia a erro de digitacao, zero dependencias |
| Container | Docker (Python + Node.js) | Isolamento, reproducibilidade |
| Deploy | Render (Docker) | CD automatico, HTTPS, 24/7 |

---

## Deploy

O servico roda 24/7 em um container Docker no Render.

| Endpoint | Uso |
|---|---|
| `/health` | Health check — monitoramento e keep-alive |
| `/qrcode` | QR Code para emparelhar WhatsApp via celular |
| `/responder` | Processamento interno de mensagens (Baileys → Python) |

### Variaveis de Ambiente

| Variavel | Descricao |
|---|---|
| `GROQ_API_KEY` | Chave da API Groq (modelo llama-3.3-70b-versatile) |
| `PORT` | Porta do servidor (Render define automaticamente) |

---

## Feito por

**Shayene Figueredo** — fundadora da [Sly Design](https://slydesign.com.br).

# Maya — Chatbot de Atendimento da Sly Design

Chatbot com IA para atendimento automatizado no WhatsApp Business da [Sly Design](https://slydesign.com.br), loja especializada em slides personalizados para estudantes.

A **Maya** é uma atendente virtual que ajuda clientes a encontrar slides prontos, fazer pedidos personalizados e tirar duvidas — 24 horas por dia. O **Painel de Controle** e a interface de gestao profissional para acompanhar todos os pedidos em tempo real.

---

## Funcionalidades

### Chatbot Maya
| Funcionalidade | Descricao |
|---|---|
| Busca de Slides | Busca inteligente no catalogo de 45 temas, com tolerancia a erros de digitacao |
| Pedido Personalizado | Fluxo completo: tema → tipo → prazo → nomes → extras → resumo → pagamento |
| Atendimento por IA | Duvidas livres respondidas com linguagem natural (Groq + Llama 3.3 70B) |
| Memoria de Conversa | Historico completo, contador de tokens, resumo automatico, persistencia em JSON |
| Conexao WhatsApp | Integracao real via wppconnect/Baileys — recebe e responde mensagens |
| Notificacoes | Alerta Shay no WhatsApp quando cliente precisa de atendimento humano |

### Painel de Controle (React + Vite)
| Funcionalidade | Descricao |
|---|---|
| Dashboard em Tempo Real | KPIs de faturamento, pedidos realizados, aguardando pagamento, atendentes |
| Cards de Clientes | Cada cliente com status, tema, modelo, prazo, valor e botoes de acao |
| Bloquear/Liberar Maya | Assume atendimento humano ou devolve para a IA |
| Confirmar/Rejeitar Pedidos | Aceita pedidos, envia cobranca Pix, ou rejeita com motivo |
| Tabela Mensal | Visualizacao e edicao de todos os pedidos do mes |
| Faturamento 2026 | Resumo anual com graficos de pizza (origem de clientes, regioes por DDD) |
| Pedido Manual | Adiciona pedidos via formulario ou extrai da conversa com IA |
| Auto-refresh | Atualizacao automatica a cada 30 segundos |
| Design Responsivo | Funciona no desktop, tablet e celular |

---

## Arquitetura

```
chatbot-sly/
├── backend/
│   ├── webhook_server.py   # Servidor FastAPI (Maya + Painel + APIs)
│   ├── chatbot_sly.py      # Maquina de estados da conversa
│   ├── pedidos.py           # Sistema de gestao de pedidos (JSON)
│   ├── buscador_temas.py    # Busca no catalogo de slides
│   └── wppconnect/          # Conexao com WhatsApp
├── frontend/
│   └── painel/              # React + Vite (Painel de Controle)
│       ├── src/
│       │   ├── components/  # 13 componentes React
│       │   ├── styles/      # 14 arquivos CSS
│       │   ├── hooks/       # useApi, useToast, useAutoRefresh
│       │   ├── data/        # Constantes (MESES, TIPOS, etc)
│       │   └── utils/       # Funcoes auxiliares
│       ├── dist/            # Build de producao (gerado)
│       └── vite.config.js   # Configuracao Vite + proxy API
├── app/                     # Modulo principal do chatbot
│   ├── config.py            # System prompt, precos, conexao IA
│   ├── bot.py               # Fluxos de conversa
│   ├── buscador.py          # Busca inteligente (difflib)
│   ├── memoria.py           # Historico, tokens, persistencia
│   └── main.py              # Loop CLI (desenvolvimento)
├── Dockerfile               # Build Python + Node.js para deploy
├── start.sh                 # Script de inicializacao (Maya + WhatsApp)
├── requirements.txt         # Dependencias Python
└── package.json             # Dependencias Node.js (WhatsApp)
```

---

## Como Rodar Localmente

### Pre-requisitos
- Python 3.11+
- Node.js 20+
- Chave da API Groq (gratis em [console.groq.com](https://console.groq.com))

### Backend (FastAPI)

```bash
git clone <seu-repositorio>
cd chatbot-sly

python -m venv .venv
source .venv/bin/activate   # Linux/WSL

pip install -r requirements.txt
python backend/webhook_server.py
# Servidor roda em http://localhost:8000
```

### Frontend (Painel React + Vite)

```bash
cd frontend/painel
npm install
npm run dev
# Dev server em http://localhost:5173
# APIs proxy → localhost:8000
```

### Build de Producao

```bash
cd frontend/painel
npm run build
# Gera arquivos estaticos em dist/
# Backend serve automaticamente em /painel
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| IA / LLM | Groq API + Llama 3.3 70B |
| Backend | FastAPI + Uvicorn (Python 3.13) |
| Frontend | React 19 + Vite 8 |
| Estilizacao | CSS Modules + Design Tokens |
| Fonte | Montserrat (Google Fonts) |
| WhatsApp | wppconnect + Baileys (Node.js) |
| Persistencia | JSON local + estado em memoria |
| Deploy | Render (Docker + Webhook) |

---

## Deploy no Render

O deploy e automatico via webhook do GitHub:

1. Push na branch `main` dispara o deploy
2. Dockerfile instala Python, Node.js e builda o painel React
3. `start.sh` inicia o servidor FastAPI + WhatsApp
4. Painel acessivel em `https://seu-app.onrender.com/painel`

### Variaveis de Ambiente (Render)

```
GROQ_API_KEY=sua_chave
PORT=10000
```

---

## Autora

Feito por **Shayene Figueredo** — dona da [Sly Design](https://slydesign.com.br), aprendendo IA e programacao do zero e construindo projetos reais.

---

## Licenca

Este projeto e privado. Codigo fonte proprietario da Sly Design.

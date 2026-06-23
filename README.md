# Maya — Chatbot de Atendimento da Sly Design

Chatbot com IA para atendimento automatizado no WhatsApp Business da [Sly Design](https://slydesign.com.br), loja especializada em slides personalizados para estudantes.

A **Maya** é uma atendente virtual que ajuda clientes a encontrar slides prontos, fazer pedidos personalizados e tirar dúvidas — 24 horas por dia. O **Painel de Controle** é a interface de gestão profissional para acompanhar todos os pedidos em tempo real.

---

## Funcionalidades

### Chatbot Maya
| Funcionalidade | Descrição |
|---|---|
| Busca de Slides | Busca inteligente no catálogo de 45 temas, com tolerância a erros de digitação |
| Pedido Personalizado | Fluxo completo: tema → tipo → prazo → nomes → extras → resumo → confirmação |
| Atendimento por IA | Dúvidas livres respondidas com linguagem natural (Groq + Llama 3.3 70B) |
| Memória de Conversa | Histórico completo, contador de tokens, resumo automático, persistência em JSON |
| Conexão WhatsApp | Integração real via Baileys — recebe e responde mensagens |
| Notificações | Alerta Shay no WhatsApp quando cliente precisa de atendimento humano |
| Extração com IA | Extrai dados do pedido da conversa automaticamente e preenche o formulário |

### Painel de Controle (React + Vite)
| Funcionalidade | Descrição |
|---|---|
| Dashboard em Tempo Real | KPIs de faturamento, pedidos realizados, aguardando pagamento, atendentes |
| Cards de Clientes | Cada cliente com status, tema, modelo, prazo, valor e botões de ação |
| Bloquear/Liberar Maya | Assume atendimento humano ou devolve para a IA |
| Confirmar/Rejeitar Pedidos | Aceita pedidos, envia cobrança Pix, ou rejeita com motivo |
| Tabela Mensal | Visualização e edição completa de todos os pedidos do mês |
| Faturamento 2026 | Resumo anual com sidebar detalhada (total, parcelado, site, por responsável) |
| Pedido Manual | Adiciona pedidos via formulário ou extrai da conversa com IA |
| Auto-refresh | Atualização automática a cada 30 segundos |
| Design Responsivo | Funciona no desktop, tablet e celular (padrão Apple) |
| App Installable (PWA) | Instalavel na tela inicial do iPhone/Android como app nativo, com icone, splash screen e sessao permanente |

---

## Arquitetura

```
chatbot-sly/
├── backend/
│   ├── webhook_server.py   # Servidor FastAPI (Maya + Painel + APIs)
│   ├── chatbot_sly.py      # Máquina de estados (versão standalone)
│   ├── pedidos.py           # Gestão de pedidos (SQLite)
│   ├── buscador_temas.py    # Busca no catálogo de slides
│   └── .env                 # Chaves de API e tokens
├── app/                     # Biblioteca do chatbot
│   ├── config.py            # System prompt, preços, conexão IA (Groq)
│   ├── bot.py               # Fluxos de conversa (legado)
│   ├── buscador.py          # Busca inteligente (difflib)
│   ├── memoria.py           # Histórico, tokens, persistência
│   ├── nlp.py               # Detecção de intenção (NLP)
│   └── main.py              # Loop CLI (desenvolvimento/testes)
├── frontend/
│   └── painel/              # React 19 + Vite 8 (Painel de Controle)
│       ├── src/
│       │   ├── components/  # 16 componentes React
│       │   ├── styles/      # 14 arquivos CSS (tokens + componentes)
│       │   ├── hooks/       # useApi, useToast, useAutoRefresh
│       │   ├── data/        # Constantes (MESES, TIPOS, etc)
│       │   └── utils/       # Funções auxiliares
│       ├── dist/            # Build de produção (gerado)
│       └── vite.config.js   # Configuração Vite + proxy API
├── connect_whatsapp.js      # Ponte Node.js → WhatsApp (Baileys)
├── Dockerfile               # Build Python + Node.js para deploy
├── start.sh                 # Script de inicialização (Maya + WhatsApp)
├── requirements.txt         # Dependências Python
└── package.json             # Dependências Node.js
```

---

## Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Node.js 20+
- Chave da API Groq (gratuita em [console.groq.com](https://console.groq.com))

### Backend (FastAPI)

```bash
git clone <seu-repositorio>
cd chatbot-sly

python -m venv .venv
source .venv/bin/activate   # Linux/WSL
# ou .venv\Scripts\activate no Windows

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

### Build de Produção

```bash
cd frontend/painel
npm run build
# Gera arquivos estáticos em dist/
# Backend serve automaticamente em /painel
```

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| IA / LLM | Groq API + Llama 3.3 70B Versatile |
| Backend | FastAPI + Uvicorn (Python 3.11+) |
| Frontend | React 19 + Vite 8 |
| Estilização | CSS puro + Design Tokens |
| Fonte | Montserrat (Google Fonts) |
| WhatsApp | Baileys (Node.js) |
| Persistência | SQLite (pedidos) + JSON (memória IA) |
| Deploy | Render (Docker + Webhook) |

---

## Deploy no Render

O deploy é automático via webhook do GitHub:

1. Push na branch `main` dispara o deploy
2. Dockerfile instala Python, Node.js e builda o painel React
3. `start.sh` inicia o servidor FastAPI + WhatsApp
4. Painel acessível em `https://seu-app.onrender.com/painel`

### Variáveis de Ambiente (Render)

```
GROQ_API_KEY=sua_chave
PORT=10000
```

---

## Licença

Este projeto é privado. Código fonte proprietário da Sly Design.

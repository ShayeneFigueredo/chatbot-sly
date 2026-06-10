# 🤖 Maya — Chatbot de Atendimento da Sly Design

Chatbot com IA para atendimento automatizado no WhatsApp Business da [Sly Design](https://slydesign.com.br), loja especializada em slides personalizados.

A **Maya** é uma atendente virtual que ajuda clientes a encontrar slides prontos, fazer pedidos personalizados e tirar dúvidas - 24 horas por dia. 💜

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 🛍️ **Busca de Slides** | Busca inteligente no catálogo de 45 temas, com tolerância a erros de digitação |
| 🎨 **Pedido Personalizado** | Fluxo completo: tema → tipo → prazo → nomes → extras → resumo → pagamento |
| 💬 **Atendimento por IA** | Dúvidas livres respondidas com linguagem natural (Groq + Llama 3.3 70B) |
| 💾 **Memória de Conversa** | Histórico completo, contador de tokens, resumo automático, persistência em JSON |
| 🧪 **27 Testes Automatizados** | Cobertura de todos os fluxos do chatbot |

---

## 🏗️ Arquitetura

```
app/
├── __init__.py          # Pacote principal
├── config.py            # Configurações: system prompt, preços, conexão IA
├── bot.py               # Funções de mensagem e fluxos de conversa
├── buscador.py          # Busca inteligente (difflib, tolerância a erros)
├── memoria.py           # Histórico, tokens, persistência JSON
├── main.py              # Loop principal (CLI / terminal)
├── data/
│   └── temas-sly.csv    # Catálogo com 45 temas reais
└── tests/
    ├── __init__.py
    └── test_bot.py      # 27 testes automatizados
```

---

## 🚀 Como Rodar

### Pré-requisitos
- Python 3.11+
- Chave da API Groq (grátis em [console.groq.com](https://console.groq.com))

### Instalação

```bash
git clone <seu-repositorio>
cd chatbot-sly

python -m venv .venv
source .venv/bin/activate  # Linux/WSL
# ou .venv\Scripts\activate  (Windows)

pip install -r requirements.txt
```

### Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
GROQ_API_KEY=sua_chave_aqui
```

### Executar

```bash
# Versão terminal (desenvolvimento)
python -m app.main
```

---

## 🧪 Testes

```bash
python app/tests/test_bot.py
```

---

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| IA / LLM | [Groq API](https://groq.com) + Llama 3.3 70B |
| Linguagem | Python 3.11+ |
| Busca | difflib (nativo Python, zero dependências extras) |
| Persistência | JSON local |
| Testes | unittest (nativo Python) |

---

## 📦 Próximos Passos

- [ ] Conexão com WhatsApp Business API (Meta Cloud API)
- [ ] Dashboard visual com Streamlit
- [ ] Deploy em produção (Railway / Render)
- [ ] Integração com WordPress/Elementor

---

## 👩‍💻 Autora

Feito por **Shayene Figueredo** — dona da [Sly Design](https://slydesign.com.br), aprendendo IA do zero e construindo projetos reais.

---

## 📄 Licença

Este projeto é privado. Código fonte proprietário da Sly Design.

# Guia de Uso — Maya (Sly Design)

Sistema de atendimento automatizado via WhatsApp com painel de gestao integrado.

---

## Indice

1. [Acesso ao Sistema](#acesso)
2. [Painel de Gestao](#painel)
3. [WhatsApp — Conectar Maya](#whatsapp)
4. [Fluxo de Atendimento](#fluxo)
5. [Pedidos Manuais](#manuais)
6. [Integracao com o Site](#site)
7. [Comandos Rapidos](#comandos)
8. [Manutencao](#manutencao)

---

## 1. Acesso ao Sistema

O portal central protege todas as ferramentas com login unico.

1. Acesse o portal (URL configurada no deploy)
2. Faca login com suas credenciais
3. Escolha entre **Painel de Gestao** ou **WhatsApp QR Code**

---

## 2. Painel de Gestao

O painel e dividido em abas:

### Aba: Clientes Ativos

Mostra todos os clientes que estao conversando com a Maya neste momento.

| Botao | Funcao |
|-------|--------|
| **Bloquear Maya** | Silencia o bot para aquele cliente (voce assume manualmente) |
| **Liberar Maya** | Devolve o atendimento para a Maya |
| **Confirmar** (amarelo) | Confirma pagamento e adiciona o pedido ao sistema |
| **Rejeitar** (laranja) | Recusa o pedido (ex: sem vaga hoje). O cliente recebe uma mensagem automatica |

### Abas: Jan, Fev, Mar... (Meses)

Cada mes mostra:
- Tabela completa de pedidos (entrega, cliente, arquivo, tema, valor, situacao, pagamento, responsavel)
- Botao **Editar** em cada pedido para alterar a situacao
- Sidebar com **faturamento do mes** (pedidos + site)

### Aba: Faturamento

Visao anual com:
- Total de cada mes (pedidos + site)
- Separacao Shay (SF) / Samuel (SA)
- Total do site no ano

### Botao: + Pedido Manual

Adiciona pedidos recebidos fora do WhatsApp (Instagram, telefone, email, etc).

Preencha os campos e clique em Adicionar.

---

## 3. WhatsApp — Conectar Maya

Quando o servidor e reiniciado (apos deploy ou manutencao), a Maya precisa ser reconectada ao WhatsApp:

1. No portal, clique em **WhatsApp QR Code**
2. Um QR Code aparece na tela
3. Abra o WhatsApp no celular
4. Va em **Aparelhos Conectados** (ou Linked Devices)
5. Toque em **Conectar Aparelho**
6. Escaneie o QR Code
7. Pronto — a Maya esta online

**Dica:** Se estiver acessando pelo celular e nao conseguir escanear, ha um link **"Abrir no WhatsApp"** abaixo do QR Code. E so clicar.

**Importante:** A sessao dura semanas. So precisa reconectar se:
- Houver um deploy (git push)
- O WhatsApp forcou a renovacao da sessao (raro)

---

## 4. Fluxo de Atendimento

### Como a Maya atende

1. Cliente manda mensagem no WhatsApp da Sly
2. Maya se apresenta e oferece o menu
3. Cliente pode usar os botoes numerados ou escrever livremente
4. Maya classifica a intencao e responde adequadamente
5. Se a Maya nao souber responder, chama a IA (Groq)
6. Se o cliente pedir atendimento humano, a Maya notifica voce

### Como voce assume um cliente

**Pelo celular:**
- Mande `assumir NUMERO` no WhatsApp da Sly (ex: `assumir 5511999999999`)
- A Maya silencia para aquele cliente
- Quando terminar, mande `liberar NUMERO`
- Mande `humanos` para ver quem esta em atendimento manual

**Pelo painel:**
- Clique em **Bloquear Maya** no cliente desejado
- Quando terminar, clique em **Liberar Maya**

### Confirmando pagamentos

1. Cliente confirma o pedido no WhatsApp
2. Maya mostra dados do Pix e silencia (estado "Aguardando Pagamento")
3. Cliente envia comprovante — Maya NAO responde (voce confere)
4. No painel, va em Clientes Ativos
5. Clique em **Confirmar** para adicionar o pedido ao sistema
6. Se nao houver vaga (ex: pedido para hoje sem disponibilidade), clique em **Rejeitar**
7. O cliente recebe a notificacao automatica

### Quando voce responde o cliente pelo celular

A Maya detecta que voce respondeu e salva o contexto. Quando o cliente responder depois, a Maya tera o historico da sua conversa.

---

## 5. Pedidos Manuais

Para adicionar pedidos de outras origens (Instagram, telefone, email):

1. No painel, va na aba do mes desejado
2. Clique em **+ Pedido Manual**
3. Preencha:
   - **Cliente**: telefone ou nome
   - **Data**: dia/mes (ex: 15/06)
   - **Arquivo**: tipo do slide (pdf, transicoes, modelo, etc)
   - **Tema**: assunto do slide
   - **Valor**: ex: 25,00 (sem R$)
   - **Mes**: numero do mes (1=Jan, 6=Jun, etc)
   - **Situacao**: Novo, Feito, Em andamento
   - **PG**: Pago, 50% pago
   - **Resp**: SF (Shay) ou SA (Samuel)
4. Clique em **Adicionar**

---

## 6. Integracao com o Site

O sistema recebe pedidos do site automaticamente via webhook (Yampi).

### Configurar na Yampi

1. Acesse o painel da Yampi
2. Va em **Configuracoes > Webhooks** (ou Eventos)
3. Adicione a URL do webhook (fornecida no deploy)
4. Marque os eventos:
   - **Pedido criado** (order.created) — adiciona ao sistema
   - **Pedido aprovado** (order.approved) — confirma pagamento
   - **Pagamento negado** (order.payment_denied) — registra falha

### O que NAO marcar

- **Carrinho abandonado**: nao e pedido real — o cliente nao pagou. O sistema ignora automaticamente.

### Como funciona

- Pedido pago no site → aparece automaticamente no painel do mes correspondente
- O faturamento do site e calculado separadamente e aparece no sidebar
- Taxas: Yampi ~2,5% + Mercado Pago ~0,87%

---

## 7. Comandos Rapidos

Mensagens que voce (Shay) pode mandar no WhatsApp da Sly:

| Comando | Efeito |
|---------|--------|
| `assumir 5511...` | Assume atendimento manual |
| `liberar 5511...` | Devolve para Maya |
| `humanos` | Lista clientes em atendimento manual |

Qualquer outra mensagem sua no WhatsApp e ignorada pela Maya.

---

## 8. Manutencao

### Deploy (atualizar o sistema)

1. Faca as alteracoes no codigo
2. `git add . && git commit -m "descricao" && git push`
3. O Render faz deploy automatico
4. **Importante:** Apos deploy, reconecte o WhatsApp (escaneie o QR Code)

### Verificar se esta online

Acesse a URL do servidor com `/health` no final.
Resposta esperada: `{"status":"ok","maya":"online"}`

### Reiniciar sem perder a sessao

No Render Dashboard:
1. Va em `chatbot-sly-oficial`
2. Clique em **Restart service** (NAO clique em Deploy)
3. A sessao do WhatsApp e preservada

### Logs

Para ver o que esta acontecendo:
1. Render Dashboard > `chatbot-sly-oficial` > aba **Logs**
2. Filtre por erros com o campo de busca

---

## Resumo Visual

```
PORTAL (login)
  ├── Painel de Gestao
  │   ├── Clientes Ativos (bloquear/liberar/confirmar)
  │   ├── Janeiro a Dezembro (tabelas + faturamento)
  │   └── Faturamento Anual
  └── WhatsApp QR Code
       └── QR + Link para conectar

WHATSAPP DA SLY
  ├── Maya atende automaticamente
  ├── Voce assume com "assumir NUMERO"
  └── Pedidos viram notificacao no seu WhatsApp pessoal

SITE (Yampi)
  └── Pedidos caiam automaticamente no painel
```

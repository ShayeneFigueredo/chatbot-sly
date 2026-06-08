const {
  makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const axios = require("axios");
const fs = require("fs");
const http = require("http");
const qrcode = require("qrcode-terminal");

const AUTH_DIR = "/app/auth_info_baileys";
const PORT = process.env.PORT || 10000;
const SEND_PORT = process.env.SEND_PORT || 8080;
const SHAY_NUMERO = "5538997507651";

// Guarda referencia global pro socket (usada pelo servidor HTTP)
let globalSock = null;
let reconnectTentativas = 0;

async function start() {
  // Carrega sessao salva (ou cria nova)
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  // Pega versao mais recente do WhatsApp Web
  const { version } = await fetchLatestBaileysVersion();
  console.log(" WhatsApp Web version:", version.join("."));

  const sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,
    syncFullHistory: false,
    fireInitQueries: false,
    emitOwnEvents: false,
    markOnlineOnConnect: false,
    defaultQueryTimeoutMs: 60000,
  });

  // Salva credenciais automaticamente (~2MB)
  sock.ev.on("creds.update", saveCreds);

  // QR Code / conexao
  sock.ev.on("connection.update", (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      // Gera QR code no terminal + salva como HTML
      console.log("\n QR Code - Escaneie com WhatsApp:");
      qrcode.generate(qr, { small: true });

      // Gera link do WhatsApp pra conectar sem escanear
      const waLink = `https://wa.me/settings/linked_devices#${encodeURIComponent(qr)}`;

      // Salva pagina HTML pra abrir no celular
      const html = `<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maya - QR Code</title>
<style>body{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:sans-serif}
h2{color:#e0aaff;margin:10px}h3{color:#aaa;font-weight:normal;margin:5px}
img{max-width:90vw;border-radius:12px;box-shadow:0 0 30px rgba(224,170,255,.3)}
a{color:#c084fc;font-size:1.1em;margin:15px;text-align:center}
p{color:#888;margin-top:20px}
</style></head><body>
<h2>Maya Sly Design</h2>
<h3>WhatsApp > Aparelhos Conectados</h3>
<img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qr)}">
<a href="${waLink}">📱 Abrir no WhatsApp (sem escanear)</a>
<p>Se o link nao funcionar, escaneie o QR Code acima</p>
</body></html>`;
      fs.writeFileSync("/tmp/qrcode.html", html);
      console.log(`\n📱 QR + Link: ${waLink.substring(0, 80)}...`);
    }

    if (connection === "close") {
      const code = lastDisconnect?.error instanceof Boom
        ? lastDisconnect.error.output.statusCode
        : null;

      // So apaga a sessao se for logout REAL
      if (code === DisconnectReason.loggedOut) {
        console.log(" Sessao encerrada pelo WhatsApp. Apagando auth...");
        try { fs.rmSync(AUTH_DIR, { recursive: true, force: true }); } catch {}
        reconnectTentativas = 0;
      }

      // Backoff: 3s, 6s, 12s, 24s, max 60s
      const delay = Math.min(3000 * Math.pow(2, reconnectTentativas), 60000);
      reconnectTentativas++;
      console.log(` Reconectando em ${delay/1000}s (tentativa ${reconnectTentativas})...`);
      setTimeout(start, delay);
    }

    if (connection === "open") {
      console.log("✅ Maya conectada ao WhatsApp!");
      reconnectTentativas = 0; // reset contador
      globalSock = sock;
      try { fs.unlinkSync("/tmp/qrcode.html"); } catch {}
    }
  });

  // Recebe mensagens
  sock.ev.on("messages.upsert", async (m) => {
    const msg = m.messages[0];
    if (!msg || !msg.message) return;

    // Mensagem enviada por Shay (do celular)? Salva no historico do cliente
    if (msg.key.fromMe) {
      const jid = msg.key.remoteJid;
      if (!jid || jid === "status@broadcast") return;
      const meuTexto =
        msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        msg.message.imageMessage?.caption ||
        "";
      if (meuTexto) {
        const telefone = jid.replace(/@s\.whatsapp\.net/, "").replace(/@lid/, "").replace(/@g\.us/, "").replace(/:.*/, "");
        try {
          await axios.post(
            `http://localhost:${PORT}/historico`,
            { telefone: telefone, papel: "assistant", texto: "[Shay]: " + meuTexto },
            { timeout: 5000 }
          );
          console.log(`📝 Contexto salvo: Shay → ${telefone}`);
        } catch (e) {
          // silencioso — nao atrapalha o fluxo
        }
      }
      return;
    }

    // Detecta o tipo de mensagem (texto, imagem, documento)
    let tipo = "texto";
    let texto = "";

    if (msg.message.imageMessage) {
      tipo = "imagem";
      texto = msg.message.imageMessage.caption || "";
    } else if (msg.message.documentMessage) {
      tipo = "documento";
      texto = msg.message.documentMessage.caption || "";
    } else {
      texto =
        msg.message.conversation ||
        msg.message.extendedTextMessage?.text ||
        "";
    }

    const jid = msg.key.remoteJid;
    if (!jid) return;
    // Imagens sem legenda passam adiante (Maya trata)
    if (!texto && tipo === "texto") return;

    // Extrai so o numero (remove @s.whatsapp.net, @lid, @g.us, e :XX)
    const telefone = jid.replace(/@s\.whatsapp\.net/, "").replace(/@lid/, "").replace(/@g\.us/, "").replace(/:.*/, "");
    const tag = tipo !== "texto" ? ` [${tipo}]` : "";
    console.log(`\n💬 ${telefone}${tag}: ${texto || "(sem legenda)"}`);

    const inicio = Date.now();
    try {
      // "digitando..."
      await sock.sendPresenceUpdate("composing", jid);

      const resp = await axios.post(
        `http://localhost:${PORT}/responder`,
        { from: telefone, body: texto, tipo: tipo },
        { timeout: 30000 }
      );

      // Delay minimo de 3.5s pra sentir que ta conversando com alguem
      const decorrido = Date.now() - inicio;
      const espera = Math.max(0, 3500 - decorrido);
      if (espera > 0) await new Promise((r) => setTimeout(r, espera));

      await sock.sendPresenceUpdate("paused", jid);

      const resposta = resp.data.resposta;
      if (resposta) {
        await sock.sendMessage(jid, { text: resposta });
        console.log(`🤖 Maya: ${resposta.slice(0, 80)}...`);
      }
    } catch (e) {
      await sock.sendPresenceUpdate("paused", jid);
      console.log(" Erro:", e.message);
    }
  });
}

// ── Servidor HTTP interno (ponte Python → WhatsApp) ──
const sendServer = http.createServer(async (req, res) => {
  if (req.method === "POST" && req.url === "/send") {
    let body = "";
    req.on("data", (chunk) => { body += chunk; });
    req.on("end", async () => {
      try {
        const { to, text } = JSON.parse(body);
        if (!globalSock) {
          console.log("⚠️ WhatsApp ainda nao conectado. Notificacao nao enviada.");
          res.writeHead(503, { "Content-Type": "application/json" });
          res.end(JSON.stringify({ status: "waiting" }));
          return;
        }
        // WhatsApp JID nao usa + no inicio
        const numeroLimpo = to.startsWith("+") ? to.slice(1) : to;
        const jid = numeroLimpo.includes("@") ? numeroLimpo : `${numeroLimpo}@s.whatsapp.net`;
        await globalSock.sendMessage(jid, { text });
        console.log(`📤 Notificacao enviada para ${to}`);
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "sent" }));
      } catch (e) {
        console.log(" Erro ao enviar:", e.message);
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ status: "error", error: e.message }));
      }
    });
  } else if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok" }));
  } else {
    res.writeHead(404);
    res.end();
  }
});

sendServer.listen(SEND_PORT, "127.0.0.1", () => {
  console.log(`📡 API interna de envio: porta ${SEND_PORT}`);
});

start().catch((err) => {
  console.log("Erro fatal:", err.message);
  setTimeout(start, 5000);
});

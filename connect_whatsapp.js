const {
  makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} = require("@whiskeysockets/baileys");
const { Boom } = require("@hapi/boom");
const axios = require("axios");
const fs = require("fs");
const qrcode = require("qrcode-terminal");

const AUTH_DIR = "/app/auth_info_baileys";
const PORT = process.env.PORT || 10000;

async function start() {
  // Carrega sessao salva (ou cria nova)
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  // Pega versao mais recente do WhatsApp Web
  const { version } = await fetchLatestBaileysVersion();
  console.log(" WhatsApp Web version:", version.join("."));

  const sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false, // vamos gerar o nosso proprio
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

      // Salva pagina HTML pra abrir no celular
      const html = `<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maya - QR Code</title>
<style>body{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:sans-serif}
h2{color:#e0aaff;margin:10px}h3{color:#aaa;font-weight:normal;margin:5px}
img{max-width:90vw;border-radius:12px;box-shadow:0 0 30px rgba(224,170,255,.3)}
p{color:#888;margin-top:30px}
</style></head><body>
<h2>Maya Sly Design</h2>
<h3>WhatsApp > Aparelhos Conectados</h3>
<img src="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qr)}">
<p>QR Code Maya</p>
</body></html>`;
      fs.writeFileSync("/tmp/qrcode.html", html);
      console.log("\n📱 Abra no celular: https://chatbot-sly-oficial.onrender.com/qrcode");
    }

    if (connection === "close") {
      const code = lastDisconnect?.error instanceof Boom
        ? lastDisconnect.error.output.statusCode
        : null;

      if (code === DisconnectReason.loggedOut) {
        console.log(" Sessao desconectada. Apagando auth...");
        fs.rmSync(AUTH_DIR, { recursive: true, force: true });
      }

      console.log(" Reconectando em 3s...");
      setTimeout(start, 3000);
    }

    if (connection === "open") {
      console.log("✅ Maya conectada ao WhatsApp!");
      // Remove o QR code antigo
      try { fs.unlinkSync("/tmp/qrcode.html"); } catch {}
    }
  });

  // Recebe mensagens
  sock.ev.on("messages.upsert", async (m) => {
    const msg = m.messages[0];
    if (!msg || !msg.message || msg.key.fromMe) return;

    // Pega o texto
    const texto =
      msg.message.conversation ||
      msg.message.extendedTextMessage?.text ||
      msg.message.imageMessage?.caption ||
      "";

    const jid = msg.key.remoteJid;
    if (!texto || !jid) return;

    // Extrai so o numero (remove @s.whatsapp.net)
    const telefone = jid.replace("@s.whatsapp.net", "").replace(/:.*/, "");
    console.log(`\n💬 ${telefone}: ${texto}`);

    try {
      // "digitando..."
      await sock.sendPresenceUpdate("composing", jid);

      const resp = await axios.post(
        `http://localhost:${PORT}/responder`,
        { from: telefone, body: texto },
        { timeout: 30000 }
      );

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

start().catch((err) => {
  console.log("Erro fatal:", err.message);
  setTimeout(start, 5000);
});

const wppconnect = require('@wppconnect-team/wppconnect');
const axios = require('axios');

// Usa o Chromium do sistema ou o do Puppeteer
const chromePath = process.env.PUPPETEER_EXECUTABLE_PATH || require('puppeteer').executablePath();
console.log(' Chrome:', chromePath);

wppconnect.create({
  session: 'maya-sly',
  headless: true,
  useChrome: false,
  autoClose: 0,
  catchQR: (base64Qr, asciiQR, attempts, urlCode) => {
    // Salva o QR code como imagem pra ser acessada pelo navegador
    const fs = require('fs');
    const html = `<html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maya - QR Code</title>
<style>body{background:#1a1a2e;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;font-family:sans-serif}
h2{color:#e0aaff;margin:10px}
h3{color:#aaa;font-weight:normal;margin:5px}
img{max-width:90vw;border-radius:12px;box-shadow:0 0 30px rgba(224,170,255,.3)}
p{color:#888;margin-top:30px}
</style></head><body>
<h2>Maya Sly Design</h2>
<h3>Escaneie com WhatsApp > Aparelhos Conectados</h3>
<img src="${base64Qr}">
<p>Att ${attempts} · QR expira em ~30s</p>
</body></html>`;
    fs.writeFileSync('/tmp/qrcode.html', html);
    console.log('\n══════════════════════════════════════════');
    console.log('📱 ABRA NO CELULAR (QR code):');
    console.log('   https://chatbot-sly-oficial.onrender.com/qrcode');
    console.log('   Depois: WhatsApp → Aparelhos Conectados');
    console.log('══════════════════════════════════════════\n');
  },
  puppeteerOptions: {
    executablePath: chromePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  }
}).then((client) => {
  console.log('✅ Conectado ao WhatsApp!');

  client.onMessage(async (message) => {
    if (message.isGroupMsg) return;
    if (!message.body || message.from === 'status@broadcast') return;

    const from = message.from.replace('@c.us', '');
    const body = message.body;
    console.log(`\n💬 ${from}: ${body}`);

    try {
      // ✨ Efeito "digitando..."
      await client.startTyping(message.from);

      const port = process.env.PORT || 8000;
      const resp = await axios.post(`http://localhost:${port}/responder`, {
        from: from, body: body
      }, { timeout: 30000 });

      // Para de "digitar" e envia a resposta
      await client.stopTyping(message.from);
      await client.sendText(message.from, resp.data.resposta);
      console.log(`🤖 Maya: ${resp.data.resposta.slice(0, 80)}...`);
    } catch (e) {
      await client.stopTyping(message.from);
      console.log('⚠️ Erro:', e.message);
    }
  });

  console.log('📱 Pronto! Mande "oi" no WhatsApp pra testar 💜');
}).catch((err) => console.log('Erro:', err.message));

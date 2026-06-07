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

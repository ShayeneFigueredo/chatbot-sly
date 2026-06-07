const puppeteer = require('puppeteer');
(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  console.log('✅ Puppeteer funciona!');
  const page = await browser.newPage();
  await page.goto('https://web.whatsapp.com', {waitUntil: 'domcontentloaded', timeout: 15000});
  console.log('✅ WhatsApp Web carregou!');
  console.log('Title:', await page.title());
  await browser.close();
})();

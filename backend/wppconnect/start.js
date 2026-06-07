const { initServer } = require('@wppconnect/server');

initServer({
  secretKey: "mayasly2026",
  port: 21465,
  host: "127.0.0.1",
  webhook: {
    url: "http://localhost:8000/webhook",
    autoDownload: false,
    readMessage: true,
    onMessage: true
  },
  createOptions: {
    browserArgs: ["--no-sandbox", "--disable-setuid-sandbox"]
  }
});

console.log("🚀 WPPConnect: http://localhost:21465");
console.log("📱 QR Code: http://localhost:21465/api/default/qrcode");

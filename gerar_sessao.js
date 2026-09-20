const { makeWASocket, useMultiFileAuthState } = require("@whiskeysockets/baileys");
const fs = require("fs");
const qrcode = require("qrcode-terminal");
const axios = require("axios");
const FormData = require("form-data");
const { execSync } = require("child_process");
require("dotenv").config({ path: "backend/.env" });

const AUTH_DIR = "./auth_info_baileys";
const RENDER_URL = "https://chatbot-sly-oficial.onrender.com";
const SENHA = process.env.PORTAL_SENHA || "135790";

async function zipFolder(source, out) {
  // Para funcionar no Windows nativamente com PowerShell
  try {
      execSync(`powershell Compress-Archive -Path ${source}\\* -DestinationPath ${out} -Force`);
      return true;
  } catch (e) {
      console.log("Tentando zipar com Node nativo...");
      const archiver = require('archiver');
      const output = fs.createWriteStream(out);
      const archive = archiver('zip', { zlib: { level: 9 } });
      
      return new Promise((resolve, reject) => {
          output.on('close', resolve);
          archive.on('error', reject);
          archive.pipe(output);
          archive.directory(source, false);
          archive.finalize();
      });
  }
}

async function uploadSession(zipPath) {
  console.log("\n🚀 Enviando sessão para o servidor na nuvem (Render)...");
  const form = new FormData();
  form.append("file", fs.createReadStream(zipPath));

  try {
    const res = await axios.post(`${RENDER_URL}/api/upload-session`, form, {
      headers: {
        ...form.getHeaders(),
        "X-API-KEY": SENHA
      }
    });
    console.log("✅ RESPOSTA DO SERVIDOR:", res.data.msg);
    console.log("\nTudo certo! A Maya já deve estar funcionando no Render.");
    console.log("Pode fechar esta janela.");
  } catch (error) {
    console.error("❌ Erro ao enviar para o Render:", error.response ? error.response.data : error.message);
  }
}

async function start() {
  if (fs.existsSync(AUTH_DIR)) {
      console.log("⚠️ Sessão antiga encontrada. Apagando para gerar nova...");
      fs.rmSync(AUTH_DIR, { recursive: true, force: true });
  }

  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

  const sock = makeWASocket({
    auth: state,
    printQRInTerminal: true, // Mostra o QR no terminal!
    browser: ["Ubuntu", "Chrome", "20.0.04"]
  });

  sock.ev.on("creds.update", saveCreds);

  sock.ev.on("connection.update", async (update) => {
    const { connection, qr } = update;

    if (qr) {
      console.log("\n📱 ESCANEIE O QR CODE ACIMA COM SEU WHATSAPP (Aparelhos Conectados)");
      // Também solicita pareamento por código se preferir
      const numeroBot = process.env.SHAY_WHATSAPP || "5534999306554";
      try {
          const code = await sock.requestPairingCode(numeroBot);
          console.log(`\nOu se preferir, use o CÓDIGO DE PAREAMENTO: ${code}`);
      } catch (e) {}
    }

    if (connection === "open") {
      console.log("\n✅ Conectado com sucesso no WhatsApp (Local)!");
      console.log("Preparando arquivos para enviar à nuvem...");
      
      // Espera uns segundos para as credenciais terminarem de salvar
      setTimeout(async () => {
          const zipPath = "./session.zip";
          await zipFolder(AUTH_DIR, zipPath);
          await uploadSession(zipPath);
          process.exit(0);
      }, 5000);
    }
  });
}

console.log("Iniciando Maya Local para Autenticação...");
start();

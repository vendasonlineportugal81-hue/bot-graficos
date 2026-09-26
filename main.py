import os
import json
import base64
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Captura os tokens do Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Pega a chave da variável GEMINI_API_KEY ou GROQ_API_KEY
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")

# Servidor HTTP para o Render não dar timeout
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot do Telegram Ativo!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

PROMPT_ANALISE = """
Atua como analista técnico rápido. Analisa a imagem do gráfico aplicando 3 indicadores à tua escolha (ex: RSI, Média Móvel, Bandas de Bollinger, MACD ou Price Action/Suporte e Resistência).

Responde EXCLUSIVAMENTE no formato abaixo, de forma resumida e sem introduções:

📉 **INDICADORES USADOS NA ANÁLISE:**
1. [Nome do Indicador 1]: [Sinal curto - ex: Sobrevendido / Alta]
2. [Nome do Indicador 2]: [Sinal curto - ex: Cruzamento de Média / Alta]
3. [Nome do Indicador 3]: [Sinal curto - ex: Rejeição no Suporte / Alta]

📊 **PROJEÇÃO PRÓXIMAS 3 VELAS:**
• Vela 1: [CALL ou PUT] | Probabilidade: [X]%
• Vela 2: [CALL ou PUT] | Probabilidade: [X]%
• Vela 3: [CALL ou PUT] | Probabilidade: [X]%

⏰ **ENTRADA E FUSO HORÁRIO:**
• Fuso Horário: Lisboa (WET/WEST)
• Ponto de Entrada: [Ex: Entrar no segundo 00:00 na virada da próxima vela]
"""

def analisar_imagem_directo(image_base64):
    # Requisição direta via REST API sem depender de SDKs
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": PROMPT_ANALISE},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": image_base64
                    }
                }
            ]
        }]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            return res_data['candidates'][0]['content']['parts'][0]['text']
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return f"Erro na API ({e.code}): {error_body}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Envia um print do gráfico para receberes a análise rápida com 3 indicadores (Fuso: Lisboa).")

async def analisar_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_aguarde = await update.message.reply_text("A analisar indicadores e velas...")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        file_bytes = await photo_file.download_as_bytearray()
        
        image_base64 = base64.b64encode(file_bytes).decode('utf-8')
        resposta = analisar_imagem_directo(image_base64)
        
        await mensagem_aguarde.edit_text(resposta)
        
    except Exception as e:
        await mensagem_aguarde.edit_text(f"Erro ao processar: {str(e)}")

def main():
    if not TELEGRAM_TOKEN or not API_KEY:
        print("ERRO: TELEGRAM_TOKEN e API_KEY/GROQ_API_KEY precisam estar configurados!")
        return

    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analisar_grafico))
    
    print("Bot operacional sem SDKs de terceiros...")
    app.run_polling()

if __name__ == '__main__':
    main()


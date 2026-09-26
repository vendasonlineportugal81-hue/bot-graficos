import os
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# Configuração dos Tokens através das Variáveis de Ambiente
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Servidor HTTP simples para o Render (Health Check)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot do Telegram com Groq ativo!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Inicialização do Cliente Groq
groq_client = Groq(api_key=GROQ_API_KEY)

# Prompt de Análise Técnica
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Envia um print do gráfico para receberes a análise rápida com 3 indicadores (Fuso: Lisboa).")

async def analisar_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_aguarde = await update.message.reply_text("A analisar indicadores e velas...")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        file_bytes = await photo_file.download_as_bytearray()
        
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        
        # Modelo ativo de visão na Groq
        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_ANALISE},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.2,
        )
        
        resposta = completion.choices[0].message.content
        await mensagem_aguarde.edit_text(resposta)
        
    except Exception as e:
        await mensagem_aguarde.edit_text(f"Erro ao analisar: {str(e)}")

def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("ERRO: As variáveis TELEGRAM_TOKEN e GROQ_API_KEY precisam estar configuradas!")
        return

    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analisar_grafico))
    
    print("Bot a rodar 24/7 com Groq...")
    app.run_polling()

if __name__ == '__main__':
    main()

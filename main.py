import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# Configuração dos Tokens através das Variáveis de Ambiente
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Servidor HTTP simples para o Render (Health Check)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot do Telegram ativo!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Inicialização do Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

PROMPT_ANALISE = """
Atua como um analista técnico sénior de mercados financeiros.
Analisa este gráfico com detalhe e fornece uma resposta estruturada:
1. Tendência Principal (Alta, Baixa ou Lateral)
2. Níveis Críticos (Suportes e Resistências)
3. Padrões de Velas ou Figuras Geométricas detetadas
4. Sugestão Operacional Resumida (Pontos de Atenção/Risco)
Seja claro, objetivo e profissional.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Envia-me um print de um gráfico financeiro e farei a análise técnica para ti.")

async def analisar_grafico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensagem_aguarde = await update.message.reply_text("A analisar o gráfico, aguarda um momento...")
    
    try:
        # Transferir a foto enviada pelo utilizador
        photo_file = await update.message.photo[-1].get_file()
        file_bytes = await photo_file.download_as_bytearray()
        
        image_part = {
            "mime_type": "image/jpeg",
            "data": bytes(file_bytes)
        }
        
        # Enviar imagem para a API do Gemini
        response = model.generate_content([PROMPT_ANALISE, image_part])
        
        # Enviar resposta de volta para o Telegram
        await mensagem_aguarde.edit_text(response.text)
        
    except Exception as e:
        await mensagem_aguarde.edit_text(f"Ocorreu um erro ao analisar a imagem: {str(e)}")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("ERRO: As variáveis TELEGRAM_TOKEN e GEMINI_API_KEY precisam estar configuradas!")
        return

    # Iniciar servidor de Health Check numa thread separada
    threading.Thread(target=run_health_check_server, daemon=True).start()

    # Iniciar Bot do Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analisar_grafico))
    
    print("Bot a rodar 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()

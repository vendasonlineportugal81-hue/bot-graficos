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

# Inicialização da API do Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Função para encontrar automaticamente o modelo disponível sem erros 404 ou de cota
def obter_modelo_ativo():
    modelos_prioritarios = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-2.0-flash-exp',
        'gemini-1.5-flash-latest'
    ]
    
    # Tenta primeiro os modelos conhecidos
    for m in modelos_prioritarios:
        try:
            return genai.GenerativeModel(m)
        except Exception:
            continue
            
    # Se nenhum dos prioritários funcionar, descobre dinamicamente da API do Google
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'flash' in m.name:
                nome_limpo = m.name.replace('models/', '')
                return genai.GenerativeModel(nome_limpo)
    except Exception:
        pass
        
    return genai.GenerativeModel('gemini-2.5-flash')

# Prompt objetivo ajustado para o Fuso Horário de Lisboa com 3 indicadores
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
        
        image_part = {
            "mime_type": "image/jpeg",
            "data": bytes(file_bytes)
        }
        
        # Obtém dinamicamente o modelo que está a funcionar na tua conta
        model = obter_modelo_ativo()
        response = model.generate_content([PROMPT_ANALISE, image_part])
        await mensagem_aguarde.edit_text(response.text)
        
    except Exception as e:
        await mensagem_aguarde.edit_text(f"Erro ao analisar: {str(e)}")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("ERRO: As variáveis TELEGRAM_TOKEN e GEMINI_API_KEY precisam estar configuradas!")
        return

    threading.Thread(target=run_health_check_server, daemon=True).start()

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analisar_grafico))
    
    print("Bot a rodar 24/7...")
    app.run_polling()

if __name__ == '__main__':
    main()



import os
import io
from PIL import Image
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Vai buscar as chaves das Variáveis de Ambiente por segurança
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

PROMPT_ANALISE = """
Atua como um especialista em análise técnica de mercados financeiros.
Analisa a imagem deste gráfico e fornece um relatório direto e estruturado:

1. 📈 **Tendência Principal:** (Alta, Baixa ou Lateralização)
2. 🎯 **Níveis Chave:** Identifica Suportes e Resistências visíveis.
3. 🕯️ **Padrões de Candles / Figuras:** (Ex: Martelo, Engolfo, Topo Duplo, Mastro e Bandeira, etc.)
4. 🚀 **Cenário Provável:** Qual a direção mais provável para os próximos candles.
5. ⚠️ **Gestão de Risco:** Zona sugerida para Invalidação / Stop Loss.

Responde em português, de forma clara e formatada com emojis.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Bot de Análise de Gráficos Ativo!**\nEnvia uma foto ou print de qualquer gráfico que eu analiso para ti."
    )

async def analisar_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🔍 *A analisar o gráfico... Aguarde uns segundos.*", parse_mode="Markdown")
    
    try:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        image = Image.open(io.BytesIO(photo_bytes))
        
        # Usa o modelo Gemini 2.5 Flash para análise de imagem rápida
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, PROMPT_ANALISE]
        )
        
        await status_msg.edit_text(response.text, parse_mode="Markdown")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Erro ao analisar a imagem: {str(e)}")

def main():
    if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
        print("ERRO: TELEGRAM_TOKEN ou GEMINI_API_KEY não configurados!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analisar_foto))
    
    print("Bot rodando 24/7...")
    app.run_polling()

if __name__ == "__main__":
    main()

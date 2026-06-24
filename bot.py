import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8999253238:AAExtYuaQxfGwcrdY2HN0U3-zWxMP-u52y8"

MENU = {
    "🍕 Пицца": [("Маргарита", 450), ("Пепперони", 550)],
    "🍔 Бургеры": [("Классик", 350), ("Чизбургер", 400)],
    "🥤 Напитки": [("Кола", 100), ("Вода", 60)],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🛍️ Меню", callback_data="menu")]]
    await update.message.reply_text("Добро пожаловать! 🍕", reply_markup=InlineKeyboardMarkup(keyboard))

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in MENU]
    await query.edit_message_text("Выбери категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data[4:]
    items = MENU.get(cat, [])
    keyboard = [[InlineKeyboardButton(f"{n} — {p}₽", callback_data="menu")] for n, p in items]
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu")])
    await query.edit_message_text(f"{cat}:", reply_markup=InlineKeyboardMarkup(keyboard))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_web():
    HTTPServer(("0.0.0.0", 10000), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(category, pattern="^cat_"))
app.run_polling()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8999253238:AAGdBsxcBOsbjstAH5e374VY8IBsPvC8bWY"

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

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
app.add_handler(CallbackQueryHandler(category, pattern="^cat_"))
app.run_polling()

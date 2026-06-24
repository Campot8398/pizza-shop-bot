import asyncio
import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

GETTING_ADDRESS, GETTING_PHONE = range(2)

logging.basicConfig(level=logging.INFO)

MENU = {
    "🍕 Пицца": [
        {"name": "Маргарита", "price": 450, "desc": "Томат, моцарелла, базилик"},
        {"name": "Пепперони", "price": 550, "desc": "Пепперони, моцарелла, томат"},
        {"name": "4 сыра", "price": 600, "desc": "Моцарелла, чеддер, пармезан, горгонзола"},
    ],
    "🍔 Бургеры": [
        {"name": "Классик", "price": 350, "desc": "Говядина, салат, томат, огурец"},
        {"name": "Чизбургер", "price": 400, "desc": "Говядина, чеддер, соус"},
        {"name": "Двойной", "price": 500, "desc": "Двойная котлета, бекон, сыр"},
    ],
    "🥤 Напитки": [
        {"name": "Кола 0.5л", "price": 100, "desc": "Холодная Coca-Cola"},
        {"name": "Сок апельсин", "price": 120, "desc": "Свежевыжатый"},
        {"name": "Вода 0.5л", "price": 60, "desc": "Негазированная"},
    ],
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["cart"] = []

    keyboard = [[InlineKeyboardButton("🛍️ Открыть меню", callback_data="menu")]]

    await update.message.reply_text(
        "🍕 Добро пожаловать!\n\nДоставка 30-45 минут 🚀",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("➕ Добавить ещё", callback_data="menu")],
        [InlineKeyboardButton(f"🛒 Корзина ({len(cart)}) — {total}₽", callback_data="cart")],
    ]

    await query.edit_message_text(
        f"✅ {item['name']} добавлен\n💰 {item['price']}₽",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cart = context.user_data.get("cart", [])

    if not cart:
        await query.edit_message_text(
            "🛒 Корзина пуста",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Меню", callback_data="menu")]])
        )
        return

    text = "🛒 Корзина:\n\n"
    total = 0

    for item in cart:
        text += f"• {item['name']} — {item['price']}₽\n"
        total += item["price"]

    text += f"\n💰 Итого: {total}₽"

    keyboard = [
        [InlineKeyboardButton("✅ Оформить", callback_data="order")],
        [InlineKeyboardButton("🗑 Очистить", callback_data="clear")],
        [InlineKeyboardButton("◀️ Меню", callback_data="menu")],
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: update.callback_query
    await: query.answer()

    context: user_data: cart

    await: query.edit_message_text(
        "🗑 Корзина очищена",
        reply_markup: InlineKeyboardMarkup([[InlineKeyboardButton("Меню", callback_data="menu")]])
    )

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: update.callback_query
    await: query.answer()

    await: query.edit_message_text("📍 Введи адрес доставки:")
    return GETTING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text

    await update.message.reply_text("📞 Введи телефон:")
    return GETTING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text

    if not re.match(r"^\+?\d[\d\s\-]{7,15}$", phone):
        await: update.message.reply_text("❌ Неверный формат. Попробуй снова:")
        return GETTING_PHONE

    cart = context.user_data.get("cart", [])
    address = context.user_data.get("address", "")

    user = update.effective_user
    username = f"@{user.username}" if user.username else "без username"

    total = sum(i["price"] for i in cart)

    text = f"🆕 Заказ\n\n👤 {user.first_name} ({username})\n📞 {phone}\n📍 {address}\n\n"

    for item in cart:
        text += f"• {item['name']} — {item['price']}₽\n"

    text += f"\n💰 {total}₽"

    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
    except Exception as e:
        logging.error(e)

    context.user_data.clear()

    await update.message.reply_text("✅ Заказ принят!")

    return ConversationHandler.END

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query: update.callback_query
    await: query.answer()
    await: query.edit_message_text("👋 До свидания")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено")
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Ошибка: {context.error}")

def main():
    if not TOKEN:
        raise ValueError("TOKEN не задан")

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_order, pattern="^order$")],
        states={
            GETTING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(show_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(show_cart, pattern="^cart$"))
    app.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear$"))
    app.add_handler(CallbackQueryHandler(close, pattern="^close$"))

    app.add_error_handler(error_handler)

    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = "8999253238:AAGdBsxcBOsbjstAH5e374VY8IBsPvC8bWY"
ADMIN_CHAT_ID = "7337131157"

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

GETTING_ADDRESS, GETTING_PHONE = range(2)
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = []
    keyboard = [[InlineKeyboardButton("🛍️ Открыть меню", callback_data="menu")]]
    await update.message.reply_text(
        "🍕 Добро пожаловать в наш магазин еды!\n\nДоставка за 30-45 минут 🚀\n\nНажми кнопку ниже 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    for category in MENU.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat_{category}")])
    cart = context.user_data.get("cart", [])
    if cart:
        total = sum(i["price"] for i in cart)
        keyboard.append([InlineKeyboardButton(f"🛒 Корзина ({len(cart)}) — {total}₽", callback_data="cart")])
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    await query.edit_message_text("📋 Выбери категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data[4:]
    items = MENU.get(category, [])
    keyboard = []
    for i, item in enumerate(items):
        keyboard.append([InlineKeyboardButton(f"{item['name']} — {item['price']}₽", callback_data=f"add_{i}_{category}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu")])
    await query.edit_message_text(f"{category}\n\nВыбери блюдо:", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_", 2)
    item_idx = int(parts[1])
    category = parts[2]
    item = MENU[category][item_idx]
    if "cart" not in context.user_data:
        context.user_data["cart"] = []
    context.user_data["cart"].append(item)
    cart = context.user_data["cart"]
    total = sum(i["price"] for i in cart)
    keyboard = [
        [InlineKeyboardButton("➕ Добавить ещё", callback_data="menu")],
        [InlineKeyboardButton(f"🛒 Корзина ({len(cart)}) — {total}₽", callback_data="cart")],
    ]
    await query.edit_message_text(
        f"✅ {item['name']} добавлен!\n💰 Цена: {item['price']}₽\n\n🛒 В корзине: {len(cart)} шт. на {total}₽",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cart = context.user_data.get("cart", [])
    if not cart:
        keyboard = [[InlineKeyboardButton("🛍️ В меню", callback_data="menu")]]
        await query.edit_message_text("🛒 Корзина пуста!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    text = "🛒 Твоя корзина:\n\n"
    for item in cart:
        text += f"• {item['name']} — {item['price']}₽\n"
    total = sum(i["price"] for i in cart)
    text += f"\n💰 Итого: {total}₽\n🚚 Доставка бесплатно"
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="order")],
        [InlineKeyboardButton("🗑️ Очистить", callback_data="clear")],
        [InlineKeyboardButton("◀️ В меню", callback_data="menu")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cart"] = []
    keyboard = [[InlineKeyboardButton("🛍️ В меню", callback_data="menu")]]
    await query.edit_message_text("🗑️ Корзина очищена!", reply_markup=InlineKeyboardMarkup(keyboard))

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📍 Введи адрес доставки:\n\nНапример: ул. Пушкина, д. 10, кв. 5")
    return GETTING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    await update.message.reply_text("📞 Введи номер телефона:\n\nНапример: +7 900 123 45 67")
    return GETTING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    cart = context.user_data.get("cart", [])
    address = context.user_data.get("address", "")
    user = update.effective_user
    total = sum(i["price"] for i in cart)
    order_text = f"🆕 НОВЫЙ ЗАКАЗ!\n\n👤 {user.first_name} (@{user.username})\n📞 {phone}\n📍 {address}\n\n🛒 Заказ:\n"
    for item in cart:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n💰 Итого: {total}₽"
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
    context.user_data["cart"] = []
    keyboard = [[InlineKeyboardButton("🛍️ Новый заказ", callback_data="menu")]]
    await update.message.reply_text(
        f"✅ Заказ принят!\n📍 Адрес: {address}\n💰 Сумма: {total}₽\n\n⏰ Доставим за 30-45 минут!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👋 До свидания!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено.")
    return ConversationHandler.END

def main():
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
    print("🤖 Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

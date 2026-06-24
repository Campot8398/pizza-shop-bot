import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# ========================================
# НАСТРОЙКИ — ИЗМЕНИ ЭТО!
# ========================================
TOKEN = "8999253238:AAGdBsxcBOsbjstAH5e374VY8IBsPvC8bWY"
ADMIN_CHAT_ID = "7337131157"

# ========================================
# МЕНЮ МАГАЗИНА — ДОБАВЛЯЙ СВОИ БЛЮДА!
# ========================================
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

# Состояния разговора
CHOOSING_CATEGORY, CHOOSING_ITEM, GETTING_ADDRESS, GETTING_PHONE = range(4)

logging.basicConfig(level=logging.INFO)

# ========================================
# КОМАНДА /start
# ========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cart"] = []
    
    keyboard = [[InlineKeyboardButton("🛍️ Открыть меню", callback_data="menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🍕 Добро пожаловать в наш магазин еды!\n\n"
        "У нас вкусно и быстро 🚀\n"
        "Доставка за 30-45 минут\n\n"
        "Нажми кнопку, чтобы открыть меню 👇",
        reply_markup=reply_markup
    )

# ========================================
# ПОКАЗАТЬ КАТЕГОРИИ
# ========================================
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for category in MENU.keys():
        keyboard.append([InlineKeyboardButton(category, callback_data=f"cat_{category}")])
    
    cart = context.user_data.get("cart", [])
    if cart:
        total = sum(item["price"] for item in cart)
        keyboard.append([InlineKeyboardButton(f"🛒 Корзина ({len(cart)} шт.) — {total}₽", callback_data="cart")])
    
    keyboard.append([InlineKeyboardButton("❌ Закрыть", callback_data="close")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("📋 Выбери категорию:", reply_markup=reply_markup)

# ========================================
# ПОКАЗАТЬ ТОВАРЫ В КАТЕГОРИИ
# ========================================
async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("cat_", "")
    items = MENU.get(category, [])
    
    keyboard = []
    for i, item in enumerate(items):
        keyboard.append([InlineKeyboardButton(
            f"{item['name']} — {item['price']}₽",
            callback_data=f"add_{category}_{i}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"{category}\n\nВыбери блюдо:", reply_markup=reply_markup)

# ========================================
# ДОБАВИТЬ В КОРЗИНУ
# ========================================
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_", 2)
    category = parts[1]
    item_idx = int(parts[2])
    
    # Найти правильную категорию
    for cat_name, items in MENU.items():
        if category in cat_name or cat_name in category:
            item = items[item_idx]
            break
    else:
        # Попробуем найти по точному совпадению
        item = None
        for cat_name, items in MENU.items():
            if cat_name == category:
                item = items[item_idx]
                break
    
    if item:
        if "cart" not in context.user_data:
            context.user_data["cart"] = []
        context.user_data["cart"].append(item)
        
        cart = context.user_data["cart"]
        total = sum(i["price"] for i in cart)
        
        keyboard = [
            [InlineKeyboardButton("➕ Добавить ещё", callback_data="menu")],
            [InlineKeyboardButton(f"🛒 Корзина ({len(cart)} шт.) — {total}₽", callback_data="cart")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ {item['name']} добавлен в корзину!\n"
            f"💰 Цена: {item['price']}₽\n\n"
            f"🛒 В корзине: {len(cart)} товар(ов) на {total}₽",
            reply_markup=reply_markup
        )

# ========================================
# ПОКАЗАТЬ КОРЗИНУ
# ========================================
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
    
    total = sum(item["price"] for item in cart)
    text += f"\n💰 Итого: {total}₽\n🚚 Доставка: бесплатно"
    
    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="order")],
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear")],
        [InlineKeyboardButton("◀️ В меню", callback_data="menu")],
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ========================================
# ОЧИСТИТЬ КОРЗИНУ
# ========================================
async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["cart"] = []
    
    keyboard = [[InlineKeyboardButton("🛍️ В меню", callback_data="menu")]]
    await query.edit_message_text("🗑️ Корзина очищена!", reply_markup=InlineKeyboardMarkup(keyboard))

# ========================================
# ОФОРМЛЕНИЕ ЗАКАЗА
# ========================================
async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📍 Введи адрес доставки:\n\n"
        "Например: ул. Пушкина, д. 10, кв. 5"
    )
    return GETTING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    
    await update.message.reply_text(
        "📞 Введи номер телефона:\n\n"
        "Например: +7 900 123 45 67"
    )
    return GETTING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    cart = context.user_data.get("cart", [])
    address = context.user_data.get("address", "")
    user = update.effective_user
    total = sum(item["price"] for item in cart)
    
    # Формируем заказ
    order_text = f"🆕 НОВЫЙ ЗАКАЗ!\n\n"
    order_text += f"👤 Клиент: {user.first_name} (@{user.username})\n"
    order_text += f"📞 Телефон: {phone}\n"
    order_text += f"📍 Адрес: {address}\n\n"
    order_text += "🛒 Состав заказа:\n"
    for item in cart:
        order_text += f"• {item['name']} — {item['price']}₽\n"
    order_text += f"\n💰 Итого: {total}₽"
    
    # Отправляем заказ администратору
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
    except Exception as e:
        logging.error(f"Ошибка отправки заказа: {e}")
    
    # Подтверждение клиенту
    context.user_data["cart"] = []
    
    keyboard = [[InlineKeyboardButton("🛍️ Сделать новый заказ", callback_data="menu")]]
    await update.message.reply_text(
        f"✅ Заказ принят! Спасибо!\n\n"
        f"📍 Адрес: {address}\n"
        f"💰 Сумма: {total}₽\n\n"
        f"⏰ Доставим за 30-45 минут\n"
        f"📞 Если есть вопросы — мы свяжемся с тобой!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

# ========================================
# ЗАКРЫТЬ
# ========================================
async def close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("👋 До свидания! Заходи ещё!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заказ отменён.")
    return ConversationHandler.END

# ========================================
# ЗАПУСК БОТА
# ========================================
def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_order, pattern="^order$")],
        states={
            GETTING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            GETTING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(show_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(show_cart, pattern="^cart$"))
    app.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear$"))
    app.add_handler(CallbackQueryHandler(close, pattern="^close$"))
    
    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()

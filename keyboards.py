from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

# Main menu keyboard
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton('🛍 Заказать'))
main_keyboard.add(KeyboardButton('📋 Мои заказы'))
main_keyboard.add(KeyboardButton('ℹ️ О нас'), KeyboardButton('⚙️ Настройки'))

# Category selection keyboard
def get_category_keyboard(categories):
    category_buttons = [KeyboardButton(category[1]) for category in categories]
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*category_buttons).add(cart_button, back_button)
    return keyboard

# Product selection keyboard
def get_products_keyboard(page: int, total_pages: int, items_per_page: int, products: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(row_width=5)

    # Numbered buttons for items on the current page
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(products))
    for i in range(start_idx, end_idx):
        keyboard.insert(InlineKeyboardButton(str(i + 1), callback_data=f"item_{i}"))

    # Pagination arrows
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{page + 1}"))
    keyboard.row(*navigation_buttons)

    return keyboard

# Product viewing keyboard
def get_product_keyboard(quantity):
    keyboard = InlineKeyboardMarkup(row_width=3)
    keyboard.add(
        InlineKeyboardButton("-", callback_data="decrease_quantity"),
        InlineKeyboardButton(f"{quantity}", callback_data="quantity"),
        InlineKeyboardButton("+", callback_data="increase_quantity")
    )
    keyboard.add(InlineKeyboardButton("Добавить в корзину", callback_data="add_to_cart"))
    return keyboard

# Cart keyboard
def get_cart_keyboard(cart):
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Кнопки очистки корзины и оформления заказа
    keyboard.add(
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout_order"),
        InlineKeyboardButton(text="➡️ Продолжить заказ", callback_data="continue_order"),
        InlineKeyboardButton(text="🔄 Очистить корзину", callback_data="clear_cart")
    )
    
    # Кнопки для каждого товара в корзине
    for item in cart:
        delete_button = InlineKeyboardButton(
            text=f"❌ {item['name']}",
            callback_data=f"delete_item_{item['product_id']}"
        )
        keyboard.add(delete_button)

    return keyboard

# Cart keyboard
def cart_keyboard(cart):
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    for item in cart:
        keyboard.add(
            InlineKeyboardButton(f"➖ {item['name']} ➕", callback_data=f"update_{item['product_id']}_quantity"),
            InlineKeyboardButton("❌", callback_data=f"remove_{item['product_id']}")
        )
    keyboard.add(InlineKeyboardButton("Оформить заказ", callback_data="checkout"))

    return keyboard


# Back button
back_button = KeyboardButton("⬅️ Назад")
back_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(back_button)

# Location request keyboard
location_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("📍 Отправить локацию", request_location=True)
).add(back_button)

# Phone request keyboard
phone_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("📞 Отправить номер телефона", request_contact=True)
).add(back_button)

# Cart keyboard
cart_button = KeyboardButton("📥 Корзина")
cart_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(cart_button, back_button)

# Order confirmation keyboard
confirm_keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton("✅ Подтвердить")
)

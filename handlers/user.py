from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from db import add_user, user_exists, create_order, get_categories, get_products_by_category, get_user_orders, get_user
from keyboards import main_keyboard, get_category_keyboard, get_products_keyboard, get_product_keyboard, cart_keyboard, get_cart_keyboard, location_keyboard, phone_keyboard, back_keyboard
from states import OrderStates, RegistrationStates, UserStates
from config import GROUP_CHAT_ID

items_per_page = 10

def registration_required(handler):
    async def wrapper(message: types.Message, state: FSMContext, *args, **kwargs):
        user_id = message.from_user.id
        if not user_exists(user_id):
            await start(message, state)
        else:
            return await handler(message, state)
    return wrapper

# Start
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not user_exists(user_id):
        await message.answer("👋 Добро пожаловать в наш магазин!")
        await message.answer("Пожалуйста, введите своё имя:", reply_markup=types.ReplyKeyboardRemove())
        await RegistrationStates.entering_name.set()
    else:
        await message.answer("👋 Добро пожаловать в наш магазин! \nВыберите опцию ниже для просмотра товаров или получения помощи.\n\n _⚠️ Бот работает в тестовом режиме_", reply_markup=main_keyboard, parse_mode="Markdown")
        await state.finish()

async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Пожалуйста, отправьте свой номер телефона", reply_markup=phone_keyboard)
    await RegistrationStates.entering_phone.set()

async def process_phone(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await message.answer("Пожалуйста, введите своё имя:", reply_markup=types.ReplyKeyboardRemove())
        await RegistrationStates.entering_name.set()
    elif message.content_type == ContentType.CONTACT:
        user_data = await state.get_data()
        name = user_data['name']
        phone = message.contact.phone_number

        # Register user in the database
        add_user(message.from_user.id, message.from_user.username, name, phone)
        await message.answer("✅ Регистрация завершена! \nВыберите опцию ниже для просмотра товаров или получения помощи.", reply_markup=main_keyboard)
        await state.finish()

@registration_required
async def request_location(message: types.Message, state: FSMContext):
    await message.answer("📍 Пожалуйста, отправьте свою локацию для продолжения.", reply_markup=location_keyboard)
    await OrderStates.entering_location.set()

async def location_handler(message: types.Message, state: FSMContext):
    if message.content_type == ContentType.LOCATION:
        location = [message.location.latitude, message.location.longitude]
        await state.update_data(location=location)
        await category_listing(message, state)
        
async def category_listing(message: types.Message, state: FSMContext):
    categories = get_categories()
    if categories:
        await message.answer("Выберите категорию:", reply_markup=get_category_keyboard(categories))
        await OrderStates.selecting_category.set()
    else:
        await message.answer("⚠️ Категории пока отсутствуют.", reply_markup=main_keyboard)
        await state.finish()

async def category_selection(message: types.Message, state: FSMContext):
    category_name = message.text
    categories = get_categories()
    category = next((c for c in categories if c[1] == category_name), None)
    await state.update_data(selected_category=category)
    if category:
        await product_listing(message, state)
    else:
        await message.answer("❌ Категория не найдена. Попробуйте снова.")

async def product_listing(message: types.Message, state: FSMContext, page: int = 1):
    user_data = await state.get_data()
    selected_category = user_data['selected_category']
    category_id = selected_category[0]
    products = get_products_by_category(category_id)
    if products:
        total_pages = (len(products) - 1) // items_per_page + 1
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(products))
        page_content = "\n".join(
            f"{i + 1}. {products[i][2]} - {products[i][3]:,} UZS".replace(",", " ")
            for i in range(start_idx, end_idx)
        )
        text = f"{page}/{total_pages}\n\n{page_content}\n\nВыберите продукт для просмотра"

        await message.answer("📦 Выберите товар для заказа:", reply_markup=cart_keyboard)
        product_list_message = await message.answer(text, reply_markup=get_products_keyboard(page, total_pages, items_per_page, products))
        await state.update_data(category_id=category_id, products=products, product_list_message_id=product_list_message.message_id)

        await OrderStates.selecting_product.set()
    else:
        await message.answer("⚠️ В этом каталоге нет товаров.")

async def change_page(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    products = user_data['products']
    page = int(callback_query.data.split("_")[1])
    total_pages = (len(products) - 1) // items_per_page + 1

    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(products))
    page_content = "\n".join(
        f"{i + 1}. {products[i][2]} - {products[i][3]:,} UZS".replace(",", " ")
        for i in range(start_idx, end_idx)
    )

    text = f"{page}/{total_pages}\n\n{page_content}\n\nВыберите продукт для просмотра"

    await callback_query.message.edit_text(text, reply_markup=get_products_keyboard(page, total_pages, items_per_page, products))
    await callback_query.answer()

async def product_selection(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    products = user_data['products']
    item_index = int(callback_query.data.split("_")[1])

    if item_index < len(products):
        selected_product = products[item_index]
        await state.update_data(selected_product=selected_product, quantity=1)
        
        await view_product(callback_query.message, state)
        await OrderStates.viewing_product.set()
        await callback_query.message.delete()
        await state.update_data(product_list_message_id=None)

async def view_product(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    selected_product = user_data['selected_product']
    quantity = user_data['quantity']
    text = f"🛒 {selected_product[2]}\nЦена: {selected_product[3]:,} UZS\nКоличество: {quantity}\nИтого: {selected_product[3] * quantity:,} UZS".replace(",", " ")

    await message.answer("Выберите количество продукта", reply_markup=back_keyboard)
    product_message = await message.answer(text, reply_markup=get_product_keyboard(quantity))

    await state.update_data(product_message_id=product_message.message_id)

async def increase_quantity(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    quantity = user_data.get('quantity', 1) + 1
    await state.update_data(quantity=quantity)

    await update_quantity_message(callback_query, state)

async def decrease_quantity(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    quantity = max(1, user_data.get('quantity', 1) - 1)
    await state.update_data(quantity=quantity)

    await update_quantity_message(callback_query, state)

async def update_quantity_message(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    quantity = user_data['quantity']
    product = user_data['selected_product']

    text = f"🛒 {product[2]}\nЦена: {product[3]:,} UZS\nКоличество: {quantity}\nИтого: {product[3] * quantity:,} UZS".replace(",", " ")

    await callback_query.message.edit_text(text, reply_markup=get_product_keyboard(quantity))
    await callback_query.answer()

async def add_to_cart_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    cart = user_data.get("cart", [])
    product = user_data['selected_product']
    quantity = user_data['quantity']
    
    for item in cart:
        if item["product_id"] == product[0]:
            item["quantity"] += quantity
            break
    else:
        cart.append({"product_id": product[0], "name": product[2], "price": product[3], "quantity": quantity})
    
    await state.update_data(cart=cart)
    await callback_query.message.delete()
    await callback_query.message.answer(f"✅ Товар добавлен в корзину: {quantity} шт.")
    await show_cart(callback_query.message, state)
    await callback_query.answer()

async def show_cart(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    cart = user_data.get("cart", [])
    product_list_message_id = user_data.get("product_list_message_id")
    
    if not cart:
        await message.answer("🛒 Ваша корзина пуста.")
        return
    if product_list_message_id:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=product_list_message_id)
        await state.update_data(product_list_message_id=None)

    cart_content = "\n".join(
        f"{item['name']} - {item['quantity']} шт. x {item['price']:,} UZS = {item['quantity'] * item['price']:,} UZS".replace(",", " ")
        for item in cart
    )
    total_price = sum(item['quantity'] * item['price'] for item in cart)
    text = f"🛒 Ваша корзина:\n\n{cart_content}\n\nИтого: {total_price:,} UZS".replace(",", " ")
    
    await message.answer("Корзина:", reply_markup=back_keyboard)
    cart_message = await message.answer(text, reply_markup=get_cart_keyboard(cart))
    await state.update_data(cart_message_id=cart_message.message_id)
    await OrderStates.showing_cart.set()
    

async def clear_cart_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await state.update_data(cart=[])
    await callback_query.message.edit_text("🛒 Корзина очищена.")
    await callback_query.answer()

async def delete_item_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    cart = user_data.get("cart", [])
    product_id = int(callback_query.data.split("_")[2])

    cart = [item for item in cart if item['product_id'] != product_id]
    await state.update_data(cart=cart)

    if cart:
        cart_content = "\n".join(
            f"{item['name']} - {item['quantity']} шт. x {item['price']:,} UZS = {item['quantity'] * item['price']:,} UZS".replace(",", " ")
            for item in cart
        )
        total_price = sum(item['quantity'] * item['price'] for item in cart)
        text = f"🛒 Ваша корзина:\n\n{cart_content}\n\nИтого: {total_price:,} UZS".replace(",", " ")
        await callback_query.message.edit_text(text, reply_markup=get_cart_keyboard(cart))
    else:
        await callback_query.message.edit_text("🛒 Ваша корзина пуста.")
    
    await callback_query.answer("Товар удалён из корзины.")

async def checkout_order_handler(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id

    # Проверка наличия товаров в корзине
    user_data = await state.get_data()
    cart = user_data.get("cart", [])
    if not cart:
        await callback_query.answer("Ваша корзина пуста.", show_alert=True)
        return

    # Получаем данные пользователя из базы данных
    user_info = get_user(user_id)
    if not user_info:
        await callback_query.answer("Ошибка получения данных пользователя.", show_alert=True)
        return

    full_name, phone_number = user_info

    # Формируем содержимое корзины
    cart_content = "\n".join(
        f"🔹 {item['name']} - {item['quantity']} шт. x {item['price']:,} UZS = {item['quantity'] * item['price']:,} UZS".replace(",", " ")
        for item in cart
    )
    total_price = sum(item['quantity'] * item['price'] for item in cart)
    order_summary = f"\n{cart_content}\n\n💵 Итого: {total_price:,} UZS".replace(",", " ")

    # Получаем локацию из состояния
    location = user_data.get('location')
    if not location:
        await callback_query.answer("Локация не указана.", show_alert=True)
        return

    # Создаем заказ в базе данных
    order_id = create_order(user_id, cart, f"{location[0]}, {location[1]}")
    if not order_id:
        await callback_query.answer("Ошибка создания заказа.", show_alert=True)
        return

    # Формируем текст сообщения
    customer_info = f"👤 Имя: {full_name}\n📞 Телефон: +{phone_number}"
    message_text = (
        f"🆕 Новый заказ #{order_id}:\n"
        f"{order_summary}\n\n"
        f"{customer_info}\n"
        f"📍 Локация: {location[0]}, {location[1]}"
    )

    # Отправляем сообщение в группу
    await callback_query.bot.send_location(GROUP_CHAT_ID, location[0], location[1])
    await callback_query.bot.send_message(GROUP_CHAT_ID, message_text)

    # Сообщаем пользователю об успешном заказе
    await callback_query.message.answer(
        "✅ Спасибо за заказ! Мы скоро с вами свяжемся для подтверждения.",
        reply_markup=main_keyboard
    )

    # Очищаем корзину и завершаем состояние
    await callback_query.message.delete()
    await state.update_data(cart=[])
    await state.finish()
    await callback_query.answer()

async def continue_order_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await handle_back(callback_query.message, state)

@registration_required
async def viewing_orders(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    orders = get_user_orders(user_id)

    if not orders:
        await message.answer("У вас пока нет заказов.")
        return

    # Format the orders into a message
    orders_text = "Ваши заказы:\n\n"
    for order in orders:
        order_id, product_name = order
        orders_text += (
            f"Заказ #{order_id}:\n"
            f"Товар: {product_name}\n\n"
        )
    await message.answer(orders_text, reply_markup=back_keyboard)
    await UserStates.viewing_orders.set()

async def viewing_info(message: types.Message):
    try:
        with open("statics/logo.jpg", 'rb') as photo:
            await message.answer_photo(photo=photo, caption="Alcho Market\n\nНомер телефона:\n+998999999999", reply_markup=back_keyboard)
        await UserStates.viewing_info.set()
    except Exception as e:
        print(f"Failed to send message with image: {e}")



async def handle_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    user_data = await state.get_data()
    if current_state == OrderStates.entering_location.state:
        await start(message, state)
    elif current_state == OrderStates.selecting_category.state:
        await request_location(message, state)
    elif current_state == OrderStates.selecting_product.state:
        product_list_message_id = user_data.get("product_list_message_id")

        if product_list_message_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=product_list_message_id)
        await category_listing(message, state)
    elif current_state == OrderStates.viewing_product.state:
        product_message_id = user_data.get("product_message_id")

        if product_message_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=product_message_id)
        await product_listing(message, state)
    elif current_state == OrderStates.showing_cart.state:
        cart_message_id = user_data.get("cart_message_id")

        if cart_message_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=cart_message_id)
        await category_listing(message, state)
    elif current_state == UserStates.viewing_orders.state or current_state == UserStates.viewing_info.state:
        await start(message, state)

# Register handlers
def register_user_handlers(dp):
    dp.register_message_handler(start, commands=['start'], state="*")
    dp.register_message_handler(handle_back, lambda message: message.text == '⬅️ Назад', state="*")
    dp.register_message_handler(show_cart, lambda message: message.text == '📥 Корзина', state=[OrderStates.selecting_category, OrderStates.selecting_product])
    dp.register_message_handler(process_name, state=RegistrationStates.entering_name)
    dp.register_message_handler(process_phone, content_types=[ContentType.CONTACT, ContentType.TEXT], state=RegistrationStates.entering_phone)
    
    dp.register_message_handler(request_location, lambda message: message.text == '🛍 Заказать')
    dp.register_message_handler(viewing_orders, lambda message: message.text == '📋 Мои заказы')
    dp.register_message_handler(viewing_info, lambda message: message.text == 'ℹ️ О нас')

    dp.register_message_handler(location_handler, content_types=[ContentType.LOCATION, ContentType.TEXT], state=OrderStates.entering_location)
    dp.register_message_handler(category_selection, state=OrderStates.selecting_category)
    dp.register_callback_query_handler(change_page, lambda c: c.data.startswith("page_"), state=OrderStates.selecting_product)
    dp.register_callback_query_handler(product_selection, lambda c: c.data.startswith("item_"), state=OrderStates.selecting_product)

    dp.register_callback_query_handler(increase_quantity, lambda c: c.data == "increase_quantity", state=OrderStates.viewing_product)
    dp.register_callback_query_handler(decrease_quantity, lambda c: c.data == "decrease_quantity", state=OrderStates.viewing_product)
    dp.register_callback_query_handler(add_to_cart_handler, lambda c: c.data == "add_to_cart", state=OrderStates.viewing_product)

    dp.register_callback_query_handler(clear_cart_handler, lambda c: c.data == "clear_cart", state=OrderStates.showing_cart)
    dp.register_callback_query_handler(checkout_order_handler, lambda c: c.data == "checkout_order", state=OrderStates.showing_cart)
    dp.register_callback_query_handler(continue_order_handler, lambda c: c.data == "continue_order", state=OrderStates.showing_cart)
    dp.register_callback_query_handler(delete_item_handler, lambda c: c.data.startswith("delete_item_"), state=OrderStates.showing_cart)
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher import FSMContext
from db import add_category, add_product, delete_category, delete_product, get_categories, get_products, get_product_by_id, get_category_by_id, get_users
from keyboards import get_products_keyboard
from config import ADMIN_ID
from states import AdminStates

items_per_page = 10
users_per_page = 20

# Главное меню администратора
async def admin_menu(message: types.Message):
    if message.from_user.id in ADMIN_ID:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add("🛒 Товары").add("📂 Категории").add("👤 Пользователи")
        await message.answer("🤖 Панель управления:", reply_markup=keyboard)
        await AdminStates.admin_menu.set()
    else:
        await message.answer("❌ Эта команда доступна только для администратора.")

async def product_listing(message: types.Message, state: FSMContext, page: int = 1):
    products = get_products()
    if products:
        total_pages = (len(products) - 1) // items_per_page + 1
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(products))
        page_content = "\n".join(
            f"{i + 1}. {products[i][2]} - {products[i][3]} UZS"
            for i in range(start_idx, end_idx)
        )
        text = f"{page}/{total_pages}\n\n{page_content}\n\nВыберите продукт для редактирования"
        
        await message.answer("Список товаров:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Назад"))
        product_list_message = await message.answer(text, reply_markup=
        get_products_keyboard(page, total_pages, items_per_page, products).add(
            InlineKeyboardButton("Добавить товар", callback_data="add_product")
            )
        )
        await state.update_data(products=products, product_list_message_id=product_list_message.message_id)

        await AdminStates.selecting_product.set()
    else:
        await message.answer("⚠️ Продуктов нет.", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Добавить товар", callback_data="add_product")))

async def change_page(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    products = admin_data['products']
    page = int(callback_query.data.split("_")[1])
    total_pages = (len(products) - 1) // items_per_page + 1

    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(products))
    page_content = "\n".join(
        f"{i + 1}. {products[i][2]} - {products[i][3]} UZS"
        for i in range(start_idx, end_idx)
    )

    text = f"{page}/{total_pages}\n\n{page_content}\n\nВыберите продукт для редактирования"

    await callback_query.message.edit_text(text, reply_markup=
        get_products_keyboard(page, total_pages, items_per_page, products).add(
            InlineKeyboardButton("Добавить товар", callback_data="add_product")
        )
    )
    await callback_query.answer()

async def product_selection(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    products = admin_data['products']
    item_index = int(callback_query.data.split("_")[1])

    if item_index < len(products):
        selected_product = products[item_index]
        await state.update_data(selected_product=selected_product)
        await AdminStates.viewing_product.set()
        await view_product(callback_query, state)

async def view_product(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    product = admin_data['selected_product']
    category_name = get_category_by_id(product[1])
    if product:
        product_id = product[0]
        product_text = (
            f"ID: {product[0]}\n"
            f"Название: {product[2]}\n"
            f"Категория: {category_name}\n"
            f"Цена: {product[3]} UZS"
        )

        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Удалить", callback_data=f"delete_product:{product_id}")
        )
        await callback_query.message.edit_text(product_text, reply_markup=keyboard)
    else:
        await callback_query.answer("⚠️ Товар не найден.")

async def delete_product_handler(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = int(callback_query.data.split(":")[1])

    try:
        delete_product(product_id)
        await callback_query.message.edit_text("✅ Товар успешно удалён.")
        
        await product_listing(callback_query.message, state)
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка при удалении товара: {e}")

    await callback_query.answer()

async def add_product_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("Введите название нового товара:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))
    await AdminStates.entering_product_name.set()

async def product_name_set(message: types.Message, state: FSMContext):
    categories = get_categories()
    await state.update_data(product_name=message.text, categories = categories)
    if categories:
        category_buttons = [KeyboardButton(category[1]) for category in categories]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(*category_buttons).add("Отмена")
        
        await message.answer("Выберите категорию для товара:", reply_markup=keyboard)
        await AdminStates.selecting_product_category.set()
    else:
        await message.answer("⚠️ Категории отсутствуют!")
        await admin_menu(message)

async def product_category_selection(message: types.Message, state: FSMContext):
    selected_category_name = message.text
    admin_data = await state.get_data()
    categories = admin_data['categories']
    
    category_id = next((category[0] for category in categories if category[1] == selected_category_name), None)
    
    if category_id:
        await state.update_data(product_category=category_id)
        await message.answer("Введите цену нового товара:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))
        await AdminStates.entering_product_price.set()
    else:
        await message.answer("❌ Категория не найдена. Попробуйте снова.")


async def product_price_set(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        admin_data = await state.get_data()
        product_name = admin_data['product_name']
        product_category = admin_data['product_category']
        
        add_product(product_category, product_name, price)

        await message.answer("✅ Новый товар успешно добавлен!", reply_markup=types.ReplyKeyboardRemove())
        await admin_menu(message)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректную цену.")

async def handle_cancel(message: types.Message, state: FSMContext):
    await admin_menu(message)



async def category_listing(message: types.Message, state: FSMContext, page: int = 1):
    categories = get_categories()
    if categories:
        total_pages = (len(categories) - 1) // items_per_page + 1
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(categories))
        page_content = "\n".join(
            f"{i + 1}. {categories[i][1]}"
            for i in range(start_idx, end_idx)
        )
        text = f"{page}/{total_pages}\n\n{page_content}\n\nВыберите категорию для редактирования"

        await message.answer("Список категорий:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Назад"))
        category_list_message = await message.answer(text, reply_markup=
            get_products_keyboard(page, total_pages, items_per_page, categories).add(
                InlineKeyboardButton("Добавить категорию", callback_data="add_category")
            )
        )
        await state.update_data(categories=categories, category_list_message_id=category_list_message.message_id)
        await AdminStates.selecting_category.set()
    else:
        await message.answer("⚠️ Категорий нет.", reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("Добавить категорию", callback_data="add_category")))

async def change_category_page(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    categories = admin_data['categories']
    page = int(callback_query.data.split("_")[1])
    total_pages = (len(categories) - 1) // items_per_page + 1

    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(categories))
    page_content = "\n".join(
        f"{i + 1}. {categories[i][1]}"
        for i in range(start_idx, end_idx)
    )
    text = f"{page}/{total_pages}\n\n{page_content}\n\nВыберите категорию для редактирования"

    await callback_query.message.edit_text(text, reply_markup=
        get_products_keyboard(page, total_pages, items_per_page, categories).add(
            InlineKeyboardButton("Добавить категорию", callback_data="add_category")
        )
    )
    await callback_query.answer()

async def category_selection(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    categories = admin_data['categories']
    item_index = int(callback_query.data.split("_")[1])

    if item_index < len(categories):
        selected_category = categories[item_index]
        await state.update_data(selected_category=selected_category)
        await AdminStates.viewing_category.set()
        await view_category(callback_query, state)

async def view_category(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    category = admin_data['selected_category']
    if category:
        category_id = category[0]
        category_text = (
            f"ID: {category[0]}\n"
            f"Название: {category[1]}"
        )

        keyboard = InlineKeyboardMarkup().add(
            InlineKeyboardButton("Удалить", callback_data=f"delete_category:{category_id}")
        )
        await callback_query.message.edit_text(category_text, reply_markup=keyboard)
    else:
        await callback_query.answer("⚠️ Категория не найдена.")

async def delete_category_handler(callback_query: types.CallbackQuery, state: FSMContext):
    category_id = int(callback_query.data.split(":")[1])

    try:
        delete_category(category_id)
        await callback_query.message.edit_text("✅ Категория успешно удалена.")
        await category_listing(callback_query.message, state)
    except Exception as e:
        await callback_query.message.answer(f"❌ Ошибка при удалении категории: {e}")

    await callback_query.answer()

async def add_category_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("Введите название новой категории:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Отмена"))
    await AdminStates.entering_category_name.set()

async def category_name_set(message: types.Message, state: FSMContext):
    category_name = message.text

    try:
        add_category(category_name)
        await message.answer("✅ Новая категория успешно добавлена!", reply_markup=types.ReplyKeyboardRemove())
        await admin_menu(message)
    except Exception as e:
        await message.answer(f"❌ Ошибка при добавлении категории: {e}")

async def user_listing(message: types.Message, state: FSMContext, page: int = 1):
    users = get_users()  # Получаем список пользователей из базы данных
    if users:
        total_pages = (len(users) - 1) // users_per_page + 1
        start_idx = (page - 1) * users_per_page
        end_idx = min(start_idx + users_per_page, len(users))
        page_content = "\n".join(
            f"{i + 1}. {users[i][1]} - ID: {users[i][0]}"
            for i in range(start_idx, end_idx)
        )
        text = f"{page}/{total_pages}\n\n{page_content}"

        await message.answer("Список пользователей:", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("Назад"))
        user_list_message = await message.answer(text, reply_markup=get_users_keyboard(page, total_pages))
        await state.update_data(users=users, user_list_message_id=user_list_message.message_id)

        await AdminStates.viewing_user_list.set()
    else:
        await message.answer("⚠️ Нет доступных пользователей.")

def get_users_keyboard(page: int, total_pages: int):
    keyboard = InlineKeyboardMarkup()
    if page > 1:
        keyboard.add(InlineKeyboardButton("⬅️", callback_data=f"usrpage_{page - 1}"))
    if page < total_pages:
        keyboard.add(InlineKeyboardButton("➡️", callback_data=f"usrpage_{page + 1}"))
    return keyboard

async def change_user_page(callback_query: types.CallbackQuery, state: FSMContext):
    admin_data = await state.get_data()
    users = admin_data['users']
    page = int(callback_query.data.split("_")[1])
    total_pages = (len(users) - 1) // users_per_page + 1

    start_idx = (page - 1) * users_per_page
    end_idx = min(start_idx + users_per_page, len(users))
    page_content = "\n".join(
        f"{i + 1}. {users[i][1]} - ID: {users[i][0]}"
        for i in range(start_idx, end_idx)
    )
    text = f"{page}/{total_pages}\n\n{page_content}"

    await callback_query.message.edit_text(text, reply_markup=get_users_keyboard(page, total_pages))
    await callback_query.answer()



async def handle_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    state_data = await state.get_data()
    if current_state == AdminStates.selecting_product.state or current_state == AdminStates.viewing_product.state:
        product_list_message_id = state_data.get("product_list_message_id")

        if product_list_message_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=product_list_message_id)
        await admin_menu(message)
    elif current_state == AdminStates.selecting_category.state or current_state == AdminStates.viewing_category.state:
        category_list_message_id = state_data.get("category_list_message_id")

        if category_list_message_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=category_list_message_id)
        await admin_menu(message)
    elif current_state == AdminStates.viewing_user_list.state:
        user_list_message_id = state_data.get("user_list_message_id")

        if user_list_message_id:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=user_list_message_id)
        await admin_menu(message)

# Регистрация обработчиков
def register_admin_handlers(dp):
    dp.register_message_handler(admin_menu, commands=['admin'], state="*")

    dp.register_message_handler(handle_back, lambda message: message.text == 'Назад', state="*")
    dp.register_message_handler(handle_cancel, lambda message: message.text == 'Отмена', state="*")

    dp.register_message_handler(product_listing, text="🛒 Товары", state=AdminStates.admin_menu)
    dp.register_message_handler(category_listing, text="📂 Категории", state=AdminStates.admin_menu)
    dp.register_message_handler(user_listing, text="👤 Пользователи", state=AdminStates.admin_menu)

    dp.register_callback_query_handler(change_page, lambda c: c.data.startswith("page_"), state=AdminStates.selecting_product)
    dp.register_callback_query_handler(product_selection, lambda c: c.data.startswith("item_"), state=AdminStates.selecting_product)
    dp.register_callback_query_handler(add_product_handler, lambda c: c.data == "add_product", state="*")
    dp.register_callback_query_handler(delete_product_handler, lambda c: c.data.startswith("delete_product:"), state=AdminStates.viewing_product)
    dp.register_message_handler(product_name_set, state=AdminStates.entering_product_name)
    dp.register_message_handler(product_category_selection, state=AdminStates.selecting_product_category)
    dp.register_message_handler(product_price_set, state=AdminStates.entering_product_price)

    dp.register_callback_query_handler(change_category_page, lambda c: c.data.startswith("page_"), state=AdminStates.selecting_category)
    dp.register_callback_query_handler(category_selection, lambda c: c.data.startswith("item_"), state=AdminStates.selecting_category)
    dp.register_callback_query_handler(add_category_handler, lambda c: c.data == "add_category", state="*")
    dp.register_callback_query_handler(delete_category_handler, lambda c: c.data.startswith("delete_category:"), state=AdminStates.viewing_category)
    dp.register_message_handler(category_name_set, state=AdminStates.entering_category_name)

    dp.register_callback_query_handler(change_user_page, lambda c: c.data.startswith("usrpage_"), state=AdminStates.viewing_user_list)
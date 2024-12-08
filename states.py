from aiogram.dispatcher.filters.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    entering_name = State()
    entering_phone = State()

class OrderStates(StatesGroup):
    selecting_category = State()
    selecting_product = State()
    viewing_product = State()
    showing_cart = State()
    entering_location = State()
    entering_details = State()
    adding_category = State()
    adding_product = State()

class UserStates(StatesGroup):
    viewing_info = State()
    viewing_orders = State()

class AdminStates(StatesGroup):
    admin_menu = State()
    selecting_product = State()
    viewing_product = State()
    entering_product_name = State()
    selecting_product_category = State()
    entering_product_price = State()
    selecting_category = State()
    viewing_category = State()
    entering_category_name = State()
    viewing_user_list = State()
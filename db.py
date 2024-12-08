import psycopg2
import logging
from typing import List, Tuple, Optional
from config import DATABASE_URL

# Подключаемся к базе данных
try:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            print("Database connected successfully!")
except psycopg2.Error as e:
    print(f"Error: {e}")


def create_tables() -> None:
    """Creates tables if they do not already exist."""
    with psycopg2.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone_number TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Categories (
                category_id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Products (
                product_id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER CHECK(price >= 0),
                FOREIGN KEY (category_id) REFERENCES Categories (category_id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Orders (
                order_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                location TEXT NOT NULL,
                status TEXT DEFAULT 'New',
                FOREIGN KEY (user_id) REFERENCES Users (user_id) ON DELETE SET NULL,
                FOREIGN KEY (product_id) REFERENCES Products (product_id) ON DELETE SET NULL
            )
        ''')
        conn.commit()

def get_users() -> List[Tuple[int, str]]:
    """Получает список пользователей из базы данных."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, username FROM Users ORDER BY username")
            return cursor.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Ошибка получения пользователей: {e}")
        return []

def user_exists(user_id: int) -> bool:
    """Checks if a user exists in the database."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM Users WHERE user_id = %s", (user_id,))
            return cursor.fetchone() is not None
    except psycopg2.Error as e:
        logging.error(f"Error checking if user exists: {e}")
        return False

def add_user(user_id: int, username: str, full_name: str, phone_number: str) -> None:
    """Adds a new user to the database if they do not already exist."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Users (user_id, username, full_name, phone_number) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (user_id, username, full_name, phone_number)
            )
            conn.commit()
    except psycopg2.Error as e:
        logging.error(f"Error adding user: {e}")

def get_user(user_id: int) -> Optional[Tuple[str, str]]:
    """Получаем полное имя и номер телефона пользователя из базы данных."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, phone_number FROM Users WHERE user_id = %s", (user_id,))
            return cursor.fetchone()
    except psycopg2.Error as e:
        logging.error(f"Ошибка получения данных пользователя: {e}")
        return None
    
def get_products_by_category(category_id: int):
    """Возвращает все товары в определенной категории, отсортированные по имени."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Products WHERE category_id = %s ORDER BY name", (category_id,))
            return cursor.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Ошибка при получении товаров по категории: {e}")
        return []

def get_category_by_id(category_id: int):
    """Получает название категории по её ID из базы данных PostgreSQL."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM Categories WHERE category_id = %s",
                (category_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except psycopg2.Error as e:
        logging.error(f"Ошибка при получении категории по ID: {e}")
        return None

def get_categories():
    """Получает все категории из базы данных PostgreSQL."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT category_id, name FROM Categories ORDER BY category_id")
            return cursor.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Ошибка получения категорий: {e}")
        return []

def add_category(name: str) -> None:
    """Adds a new category to the database."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Categories (name) VALUES (%s) ON CONFLICT DO NOTHING", (name,))
            conn.commit()
    except psycopg2.Error as e:
        logging.error(f"Error adding category: {e}")

def delete_category(category_id: int) -> bool:
    """
    Удаляет категорию по её ID из базы данных PostgreSQL.
    Возвращает True, если категория была успешно удалена, иначе False.
    """
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Categories WHERE category_id = %s", (category_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    except psycopg2.Error as e:
        logging.error(f"Ошибка удаления категории: {e}")
        return False

def get_product_by_id(product_id: int):
    """Получает данные продукта по его ID из PostgreSQL."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT product_id, category_id, name, price FROM Products WHERE product_id = %s",
                (product_id,)
            )
            product = cursor.fetchone()
            if product:
                return {
                    "product_id": product[0],
                    "category_id": product[1],
                    "name": product[2],
                    "price": product[3]
                }
            return None
    except psycopg2.Error as e:
        logging.error(f"Ошибка при получении продукта по ID: {e}")
        return None

def get_products():
    """Получает все продукты из базы данных PostgreSQL."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT product_id, category_id, name, price FROM Products ORDER BY product_id")
            return cursor.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Ошибка получения продуктов: {e}")
        return []

def add_product(category_id: int, name: str, price: int) -> None:
    """Adds a new product to a specified category with price as an integer."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO Products (category_id, name, price) VALUES (%s, %s, %s)",
                (category_id, name, price)
            )
            conn.commit()
    except psycopg2.Error as e:
        logging.error(f"Error adding product: {e}")

def delete_product(product_id: int) -> bool:
    """Deletes a product by ID."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM Products WHERE product_id = %s", (product_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
    except psycopg2.Error as e:
        logging.error(f"Ошибка удаления товара: {e}")
        return False
    
def create_order(user_id: int, cart: list, location: str):
    """Создает заказ для пользователя с множеством товаров в корзине и возвращает ID заказа."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            for item in cart:
                cursor.execute(
                    "INSERT INTO Orders (user_id, product_id, location, status) VALUES (%s, %s, %s, 'New')",
                    (user_id, item['product_id'], location)
                )
            conn.commit()
            cursor.execute("SELECT LASTVAL()")
            order_id = cursor.fetchone()[0]
            return order_id
    except psycopg2.Error as e:
        logging.error(f"Ошибка при создании заказа: {e}")
        return None

def get_user_orders(user_id: int) -> List[Tuple[int, str]]:
    """Retrieves all orders for a specific user."""
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT Orders.order_id, Products.name
                FROM Orders
                JOIN Products ON Orders.product_id = Products.product_id
                WHERE Orders.user_id = %s
                ORDER BY Orders.status, Orders.order_id
            ''', (user_id,))
            return cursor.fetchall()
    except psycopg2.Error as e:
        logging.error(f"Error retrieving user orders: {e}")
        return []
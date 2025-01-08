import psycopg2
from threading import Thread
import time


def create_user_counter_table(host, database, user, password):
    try:
        # Підключення до бази даних
        with psycopg2.connect(host=host, database=database, user=user, password=password) as connection:
            with connection.cursor() as cursor:
                # SQL-запит для створення таблиці
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_counter (
                    USER_ID SERIAL PRIMARY KEY,
                    Counter INTEGER NOT NULL DEFAULT 0,
                    Version INTEGER NOT NULL DEFAULT 1
                );
                """)
    except Exception as error:
        print("Помилка:", error)


def print_user_counter_table(host, database, user, password):
    try:
        # Підключення до бази даних
        with psycopg2.connect(host=host, database=database, user=user, password=password) as connection:
            with connection.cursor() as cursor:
                # Виконання запиту для отримання всіх записів з таблиці
                cursor.execute("SELECT * FROM user_counter;")
                rows = cursor.fetchall()

                # Вивід заголовків колонок
                print(f"{'USER_ID':<10}{'Counter':<10}{'Version':<10}")
                print("-" * 30)

                # Вивід рядків таблиці
                for row in rows:
                    print(f"{row[0]:<10}{row[1]:<10}{row[2]:<10}")
    except Exception as error:
        print("Помилка:", error)


def add_initial_users(host):
    try:
        with psycopg2.connect(host=host, database="lab2", user="oneey", password="secret") as conn:
            with conn.cursor() as cursor:
                # Додаємо користувачів із початковими значеннями
                cursor.execute("""
                INSERT INTO user_counter (USER_ID, Counter, Version) 
                VALUES (1, 0, 0)
                ON CONFLICT (USER_ID) DO NOTHING;
                """)
                cursor.execute("""
                INSERT INTO user_counter (USER_ID, Counter, Version) 
                VALUES (2, 0, 0)
                ON CONFLICT (USER_ID) DO NOTHING;
                """)
                cursor.execute("""
                INSERT INTO user_counter (USER_ID, Counter, Version) 
                VALUES (3, 0, 0)
                ON CONFLICT (USER_ID) DO NOTHING;
                """)
                cursor.execute("""
                INSERT INTO user_counter (USER_ID, Counter, Version) 
                VALUES (4, 0, 0)
                ON CONFLICT (USER_ID) DO NOTHING;
                """)
                conn.commit()
                print("Користувачі 1, 2, 3 успішно додані")
    except Exception as error:
        print("Помилка при додаванні користувачів:", error)


def lost_update_simulation(host, iterations):
    def update_counter():
        try:
            # Підключення до бази даних
            with psycopg2.connect(host=host, database="lab2", user="oneey", password="secret") as conn:
                with conn.cursor() as cursor:
                    for _ in range(iterations):
                        # Отримуємо поточне значення лічильника
                        cursor.execute(
                            "SELECT counter FROM user_counter WHERE user_id = 1;")
                        counter = cursor.fetchone()[0]

                        # Збільшуємо значення лічильника
                        counter += 1

                        # Оновлюємо лічильник в базі
                        cursor.execute(
                            "UPDATE user_counter SET counter = %s WHERE user_id = %s;", (counter, 1))

                        conn.commit()
        except Exception as error:
            print("Помилка:", error)

    threads = []
    for _ in range(10):
        thread = Thread(target=update_counter)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print("Симуляція завершена")


def in_place_update(host, user_id, iterations, num_threads=10):
    def update_counter():
        try:
            with psycopg2.connect(host=host, database="lab2", user="oneey", password="secret") as conn:
                with conn.cursor() as cursor:
                    for _ in range(iterations):
                        cursor.execute(
                            "UPDATE user_counter SET counter = counter + 1 WHERE user_id = %s;", (user_id,))
                        conn.commit()
        except Exception as error:
            print("Помилка:", error)

    start_time = time.time()

    threads = []
    for _ in range(num_threads):
        thread = Thread(target=update_counter)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Час виконання: {end_time - start_time} секунд")


def execute_update_with_locking(host, user_id, iterations, num_threads=10):
    def update_counter():
        try:
            with psycopg2.connect(host=host, database="lab2", user="oneey", password="secret") as conn:
                with conn.cursor() as cursor:
                    for _ in range(iterations):
                        cursor.execute(
                            "SELECT counter FROM user_counter WHERE user_id = %s FOR UPDATE;", (user_id,))
                        counter = cursor.fetchone()[0]

                        counter += 1

                        cursor.execute(
                            "UPDATE user_counter SET counter = %s WHERE user_id = %s;", (counter, user_id))
                        conn.commit()
        except Exception as error:
            print("Помилка:", error)

    start_time = time.time()

    threads = []
    for _ in range(num_threads):
        thread = Thread(target=update_counter)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Час виконання: {end_time - start_time:.2f} секунд")


def execute_update_with_version_check(host, user_id, iterations, num_threads=10):
    def update_counter():
        try:
            with psycopg2.connect(host=host, database="lab2", user="oneey", password="secret") as conn:
                with conn.cursor() as cursor:
                    for _ in range(iterations):
                        while True:
                            cursor.execute(
                                "SELECT counter, version FROM user_counter WHERE user_id = %s;", (user_id,))
                            counter, version = cursor.fetchone()

                            counter += 1

                            cursor.execute("""
                                UPDATE user_counter
                                SET counter = %s, version = %s
                                WHERE user_id = %s AND version = %s;
                            """, (counter, version + 1, user_id, version))

                            conn.commit()
                            count = cursor.rowcount
                            if count > 0:
                                break

        except Exception as error:
            print("Помилка:", error)

    start_time = time.time()

    threads = []
    for _ in range(num_threads):
        thread = Thread(target=update_counter)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    end_time = time.time()
    print(f"Час виконання: {end_time - start_time:.2f} секунд")


def reset_counter(host, user_id):
    try:
        with psycopg2.connect(host=host, database="lab2", user="oneey", password="secret") as conn:
            with conn.cursor() as cursor:
                # Оновлення значення counter до 0 для вказаного user_id
                cursor.execute(
                    "UPDATE user_counter SET counter = 0 WHERE user_id = %s;", (user_id,))
                conn.commit()
                print(f"Лічильник для user_id = {user_id} успішно обнулено")
    except Exception as error:
        print(
            f"Помилка при обнуленні лічильника для user_id = {user_id}:", error)


add_initial_users("localhost")
# execute_update_with_locking("localhost", 3, 10000)
execute_update_with_version_check("localhost", 4, 10000)
# reset_counter("localhost", user_id=2)
# in_place_update("localhost", 2, 10000)
# start_time = time.time()
# lost_update_simulation(
#     host="localhost",
#     iterations=10000  # Кількість ітерацій на потік
# )
# end_time = time.time()
create_user_counter_table(
    host="localhost",
    database="lab2",
    user="oneey",
    password="secret"
)

print_user_counter_table(
    host="localhost",
    database="lab2",
    user="oneey",
    password="secret"
)

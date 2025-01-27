from playwright.sync_api import sync_playwright
import json
import os

# Путь к файлу для сохранения сессии
SESSION_FILE = "session.json"

def save_session(context):
    """Сохранение сессии в файл."""
    try:
        storage = context.storage_state()
        with open(SESSION_FILE, "w") as f:
            json.dump(storage, f)
        print("Сессия успешно сохранена.")
    except Exception as e:
        print(f"Ошибка сохранения сессии: {e}")

with sync_playwright() as p:
    # Открываем браузер
    browser = p.chromium.launch(headless=False)

    # Создаём новый контекст
    context = browser.new_context()

    # Создаём новую вкладку
    page = context.new_page()

    # Переход на страницу авторизации
    page.goto("https://metrika.yandex.ru/")
    print("Если требуется авторизация, войдите вручную в браузере.")
    input("Нажмите Enter после авторизации, чтобы сохранить сессию...")

    # Сохраняем сессию
    save_session(context)

    # Закрываем браузер
    browser.close()

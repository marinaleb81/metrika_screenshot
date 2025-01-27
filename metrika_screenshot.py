from playwright.sync_api import sync_playwright
import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from typing import Dict, Optional


class MetrikaScreenshotter:
    def __init__(self, period: str, month: str, year: str, counter_id: str, base_path: str, company_name: str):
        self.period = period
        self.month = month
        self.year = year
        self.counter_id = counter_id
        self.base_path = base_path
        self.company_name = company_name
        self.session_file = Path("session.json")
        self.base_url = "https://metrika.yandex.ru/stat"
        self.pages_config = self._get_pages_config()

    def _get_pages_config(self) -> Dict[str, str]:
        """Конфигурация страниц для скриншотов."""
        base_params = f"period={self.period}&isMinSamplingEnabled=false&id={self.counter_id}&group=day"
        return {
            "Источники_сводка": f"sources?chart_type=bar-chart&{base_params}",
            "География": f"geo?chart_type=pie&{base_params}",
            "Долгосрочные_интересы": f"interest2?chart_type=bar-chart&{base_params}",
            "Возраст": f"demography_age?chart_type=bar-chart&{base_params}",
            "Пол": f"demography_structure?chart_type=bar-chart&{base_params}",
            "Время_на_сайте": f"deepness_time?{base_params}",
            "Посещаемость_по_времени_суток": f"hourly?{base_params}",
            "Общее_число_визитов": f"loyalty_visits?{base_params}",
            "Посещаемость": f"traffic?chart_type=line-chart&{base_params}",
            "Браузеры": f"browsers?chart_type=pie&{base_params}",
            "Глубина_просмотра": f"deepness_depth?{base_params}",
            "Трафик_по_минутам": f"traffic_by_minute?chart_type=line-chart&{base_params}",
            "Разрешение_дисплея": f"resolution?chart_type=pie&{base_params}",
            "Периодичность_визитов": f"loyalty_period?{base_params}"
        }

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Очистка имени файла от недопустимых символов."""
        return "".join(c if c.isalnum() or c in " _-" else "_" for c in filename)

    def get_screenshot_path(self, page_name: str) -> Path:
        """Формирование пути для сохранения скриншота."""
        # Формируем путь: базовый_путь/Отчеты/год/месяц/Метрика
        base_path = Path(self.base_path) / "Отчеты" / self.year / self.month / "Метрика"
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path / f"{self.sanitize_filename(page_name)}.png"

    def check_session(self) -> None:
        """Проверка наличия файла сессии."""
        if not self.session_file.exists():
            print("Файл сессии не найден. Запустите 'save_session.py' для авторизации.")
            sys.exit(1)

    def handle_captcha(self, page) -> None:
        """Обработка капчи."""
        if "Я не робот" in page.content():
            print(f"Обнаружена капча для {self.company_name}. Пожалуйста, решите её вручную.")
            input("После решения капчи нажмите Enter...")
            page.wait_for_timeout(3000)

    def take_screenshots(self) -> None:
        """Основной метод для создания скриншотов."""
        self.check_session()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=str(self.session_file))

            for page_name, page_path in self.pages_config.items():
                page = context.new_page()
                try:
                    url = f"{self.base_url}/{page_path}"
                    page.goto(url)
                    page.set_viewport_size({"width": 1920, "height": 1080})
                    page.wait_for_timeout(5000)

                    self.handle_captcha(page)

                    screenshot_path = self.get_screenshot_path(page_name)
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    print(f"[{self.company_name}] Сохранен скриншот: {screenshot_path}")

                except Exception as e:
                    print(f"[{self.company_name}] Ошибка при обработке {page_name}: {e}")

                finally:
                    page.close()

            browser.close()


def load_config():
    """Загрузка конфигурации из JSON файла."""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Ошибка: Файл config.json не найден")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Ошибка: Неверный формат файла config.json")
        sys.exit(1)


def get_period_dates():
    """Получение дат периода для предыдущего месяца."""
    today = datetime.now()

    # Получаем первый день предыдущего месяца
    first_day = (today.replace(day=1) - timedelta(days=1)).replace(day=1)

    # Получаем последний день предыдущего месяца
    last_day = today.replace(day=1) - timedelta(days=1)

    return first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")


# Пример использования для текущей даты (2025-01-27):
# first_day будет 2024-12-01
# last_day будет 2024-12-31


def main():
    try:
        # Загружаем конфигурацию
        config = load_config()

        # Получаем текущую дату
        current_date = datetime.now()

        # Получаем дату предыдущего месяца
        previous_date = (current_date.replace(day=1) - timedelta(days=1))
        previous_month = f"{previous_date.month:02d}"

        # Получаем период
        start_date, end_date = get_period_dates()
        period = f"{start_date}:{end_date}"

        # Формируем строку месяца для предыдущего месяца
        month_str = f"{previous_month}. {config['default_settings']['months'][previous_month]}"

        # Получаем год из конфигурации
        year = config['default_settings']['report_year']

        # Перебираем все ИТ компании
        for company in config['it_company']:
            if company['counter_id'] == "НОМЕР СЧЕТЧИКА":
                print(f"Пропуск {company['name']}: не указан номер счетчика")
                continue

            print(f"\nОбработка компании: {company['name']}")
            print(f"Путь сохранения: {company['path']}")

            screenshotter = MetrikaScreenshotter(
                period=period,
                month=month_str,
                year=year,
                counter_id=company['counter_id'],
                base_path=company['path'],
                company_name=company['name']
            )
            screenshotter.take_screenshots()

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
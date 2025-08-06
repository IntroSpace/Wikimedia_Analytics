import os
import time
import requests
from rich.console import Console
from rich.table import Table
from rich.live import Live


# URL нашего API
API_URL = "http://127.0.0.1:8000/stats"

# Создаем экземпляры Console и Table из библиотеки Rich
console = Console()


def generate_stats_table() -> Table:
    """
    Получает данные из API и генерирует из них таблицу Rich.
    """
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Вызовет ошибку, если статус не 2xx
        data = response.json()
        stats = data.get("stats", {})
    except requests.exceptions.RequestException as e:
        # Если API недоступен, показываем ошибку в таблице
        table = Table(title="Статистика правок Wikimedia (Ошибка!)")
        table.add_column("Статус", style="magenta")
        table.add_row(f"Не удалось подключиться к API: {e}")
        return table

    # Сортируем статистику по убыванию количества правок
    sorted_stats = sorted(stats.items(), key=lambda item: item[1], reverse=True)

    # Создаем таблицу
    table = Table(title=f"Статистика правок Wikimedia ({time.ctime()})")
    table.add_column("Домен", justify="left", style="cyan", no_wrap=True)
    table.add_column("Количество правок", justify="right", style="magenta")

    # Наполняем таблицу данными
    for domain, count in sorted_stats:
        table.add_row(domain, str(count))

    return table


if __name__ == "__main__":
    # Используем Live для плавного обновления таблицы без очистки всего экрана
    with Live(generate_stats_table(), screen=True, refresh_per_second=0.1) as live:
        while True:
            time.sleep(10)  # Обновляем данные каждые 10 секунд
            live.update(generate_stats_table())


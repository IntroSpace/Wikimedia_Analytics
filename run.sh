#!/bin/bash

# Скрипт для управления проектом аналитики
# Устанавливаем цвет для сообщений
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Первый аргумент, переданный скрипту (наша команда)
COMMAND=$1

# Функция для отображения помощи
show_help() {
    echo "Usage: ./run.sh {setup|producer|consumer|api|dashboard|stop|help}"
    echo
    echo "Commands:"
    echo "  setup       - Настраивает окружение: создает venv, устанавливает зависимости, запускает Docker."
    echo "  producer    - Запускает producer.py для отправки данных в Kafka."
    echo "  consumer    - Запускает consumer.py для обработки данных и сохранения в Redis."
    echo "  api         - Запускает FastAPI сервер (uvicorn)."
    echo "  dashboard   - Запускает консольный дашборд."
    echo "  stop        - Останавливает и удаляет Docker контейнеры (Kafka, Redis)."
    echo "  help        - Показывает это сообщение."
}

# Главная логика скрипта, которая решает, что делать в зависимости от команды
case "$COMMAND" in
    setup)
        echo -e "${GREEN}--- Настройка окружения ---${NC}"

        echo "1. Создание виртуального окружения 'venv'..."
        python3 -m venv venv

        echo "2. Активация venv и установка зависимостей из requirements.txt..."
        source venv/bin/activate && pip install -r requirements.txt

        echo "3. Запуск Docker контейнеров (Kafka & Redis) в фоновом режиме..."
        docker-compose up -d

        echo -e "${GREEN}--- Настройка завершена! ---${NC}"
        ;;
    producer|consumer|api|dashboard)
        echo -e "${GREEN}--- Запуск: ${COMMAND} ---${NC}"
        echo "Активация виртуального окружения..."
        source venv/bin/activate

        if [ "$COMMAND" = "api" ]; then
            echo "Запуск Uvicorn сервера для FastAPI..."
            uvicorn api:app --reload
        else
            echo "Запуск скрипта ${COMMAND}.py..."
            python "${COMMAND}.py"
        fi
        ;;
    stop)
        echo -e "${GREEN}--- Остановка Docker контейнеров ---${NC}"
        docker-compose down
        echo -e "${GREEN}--- Контейнеры остановлены и удалены. ---${NC}"
        ;;
    help|*)
        show_help
        ;;
esac

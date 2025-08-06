# Запуск: uvicorn api:app --reload

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict


# Создаем экземпляр FastAPI приложения
app = FastAPI(
    title="Wikimedia Stats API",
    description="API для получения статистики правок Wikimedia в реальном времени",
    version="1.0.0"
)


# Описываем модель данных для ответа с помощью Pydantic
# Это гарантирует, что наш API всегда будет возвращать данные в ожидаемом формате.
class StatsResponse(BaseModel):
    stats: Dict[str, int]


# Создаем клиент для подключения к Redis
# Мы вынесем его создание в функцию, чтобы можно было легко переиспользовать
def get_redis_client():
    try:
        # decode_responses=True важен, чтобы ключи и значения из Redis были строками, а не байтами
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return r
    except redis.exceptions.ConnectionError as e:
        # Если Redis недоступен, наш API вернет осмысленную ошибку
        raise HTTPException(status_code=503, detail=f"Сервис не доступен: не удалось подключиться к Redis. {e}")


# Создаем эндпоинт
@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Получает статистику правок по доменам из Redis.
    """
    redis_client = get_redis_client()
    redis_hash_name = 'wikimedia_stats'

    # Получаем все записи из хэша
    raw_stats = redis_client.hgetall(redis_hash_name)

    if not raw_stats:
        # Если данных еще нет, возвращаем пустой словарь
        return {"stats": {}}

    # Преобразуем значения из строк в целые числа
    processed_stats = {domain: int(count) for domain, count in raw_stats.items()}

    # Возвращаем данные. FastAPI автоматически преобразует этот словарь
    # в JSON-ответ, соответствующий нашей модели StatsResponse.
    return {"stats": processed_stats}


# Добавим корневой эндпоинт для приветствия
@app.get("/")
def read_root():
    return {"message": "Добро пожаловать на Wikimedia Stats API! С помощью маршрута /docs вы можете получить документацию API."}


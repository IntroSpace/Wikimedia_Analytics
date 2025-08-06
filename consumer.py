import json
import redis
from kafka import KafkaConsumer


def create_consumer(topic_name):
    """Создает и возвращает Kafka потребителя."""
    print("Подключение к Kafka consumer...")
    try:
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers='localhost:9092',
            # group_id важен для того, чтобы Kafka отслеживал, что мы уже прочитали.
            # Если мы перезапустим скрипт, он начнет с того места, где остановился.
            group_id='wikimedia_stats_group',
            # auto_offset_reset='earliest' означает, что если это новый group_id,
            # он начнет читать сообщения с самого начала топика.
            auto_offset_reset='earliest',
            # value_deserializer помогает автоматически преобразовать байты обратно в JSON.
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            api_version=(0, 10, 1)
        )
        print("Kafka Consumer подключен!")
        return consumer
    except Exception as e:
        print(f"Не получилось подключиться к Kafka Consumer: {e}")
        return None


def create_redis_client():
    """Создает и возвращает клиент для Redis."""
    print("Connecting to Redis...")
    try:
        # 'localhost' и порт 6379 - это то, что мы указали в docker-compose.
        # decode_responses=True означает, что ответы от Redis будут автоматически декодироваться в строки UTF-8.
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        # Проверяем соединение
        r.ping()
        print("Redis подключен!")
        return r
    except redis.exceptions.ConnectionError as e:
        print(f"Не удалось подключиться к Redis: {e}")
        return None


def process_events(consumer, redis_client):
    """Читает события из Kafka и обновляет счетчики в Redis."""
    if not consumer or not redis_client:
        print("Нельзя запустить процессы без подключений к Kafka и Redis")
        return

    redis_hash_name = 'wikimedia_stats'
    print(f"Сохраняем статистику в Redis hash '{redis_hash_name}'...")

    for message in consumer:
        # message.value уже является словарем благодаря value_deserializer
        event_data = message.value

        # Нас интересует поле 'server_name'
        domain = event_data.get('server_name')

        if domain:
            try:
                # Атомарно увеличиваем счетчик для данного домена в хэше 'wikimedia_stats'
                # Если домена еще нет в хэше, он будет создан со значением 1.
                redis_client.hincrby(redis_hash_name, domain, 1)
                print(f"Событие: {domain}")
            except Exception as e:
                print(f"Ошибка обновления Redis: {e}")
        else:
            print("Событие без 'server_name'")


if __name__ == "__main__":
    kafka_topic = 'wikimedia_events'

    kafka_consumer = create_consumer(kafka_topic)
    redis_conn = create_redis_client()

    process_events(kafka_consumer, redis_conn)

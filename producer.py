import json
import time
import sseclient
import requests
from kafka import KafkaProducer


def create_producer():
    """Создает и возвращает Kafka продюсера."""
    print("Подключение к Kafka...")
    try:
        # Пытаемся подключиться к Kafka. 'localhost:9092' - это адрес, который мы "пробросили" в docker-compose.
        # value_serializer говорит продюсеру, как превращать данные в байты.
        # В нашем случае, он берет JSON-объект, превращает его в строку, а затем кодирует в UTF-8.
        producer = KafkaProducer(
            bootstrap_servers='localhost:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5,  # Попробовать переподключиться 5 раз в случае ошибки
            request_timeout_ms=30000,  # Ждать ответа от Kafka 30 секунд
            api_version=(0, 10, 1)  # Указываем версию API для лучшей совместимости
        )
        print("Успешное подключение к Kafka!")
        return producer
    except Exception as e:
        print(f"Не удалось подключиться к Kafka: {e}")
        # Если не удалось подключиться, ждем 10 секунд и пробуем снова.
        time.sleep(10)
        return create_producer()


def stream_wikimedia_events(producer, topic_name):
    """Подключается к потоку Wikimedia и отправляет события в Kafka."""
    # URL потока последних правок со всех проектов Wikimedia
    url = 'https://stream.wikimedia.org/v2/stream/recentchange'
    print(f"Подключение к Wikimedia: {url}")

    try:
        # Используем requests с параметром stream=True для поддержания постоянного соединения
        response = requests.get(url, stream=True, timeout=30)
        client = sseclient.SSEClient(response)

        print("Успешное подключение. Ожидание событий...")
        for event in client.events():
            # События приходят в виде текста, который является JSON.
            # Проверяем, что событие не пустое.
            if event.data:
                try:
                    # Преобразуем текст в Python-словарь (JSON-объект)
                    event_data = json.loads(event.data)

                    # Отправляем данные в наш топик Kafka
                    producer.send(topic_name, value=event_data)

                    # Выводим информацию о том, что мы отправили.
                    # 'server_name' - это, например, 'en.wikipedia.org' или 'commons.wikimedia.org'
                    # 'title' - название статьи, которую отредактировали
                    print(f"Событие: {event_data.get('server_name')} - {event_data.get('title')}")

                except json.JSONDecodeError:
                    # Иногда могут приходить некорректные данные, просто игнорируем их.
                    print("Получено не JSON-сообщение")
                except Exception as e:
                    print(f"Ошибка во время отправки сообщения: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка подключения к Wikimedia: {e}")
        print("Повторная попытка через 15 секунд...")
        time.sleep(15)
        stream_wikimedia_events(producer, topic_name)  # Рекурсивный вызов для переподключения
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        print("Повторная попытка через 15 секунд...")
        # В случае других критических ошибок, ждем и пытаемся снова.
        time.sleep(15)
        stream_wikimedia_events(producer, topic_name)


if __name__ == "__main__":
    kafka_producer = create_producer()
    kafka_topic = 'wikimedia_events'
    stream_wikimedia_events(kafka_producer, kafka_topic)

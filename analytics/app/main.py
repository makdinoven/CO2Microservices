from fastapi import FastAPI
import os
import pika
import json
import requests

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")
STORAGE_HOST = os.getenv("STORAGE_HOST", "data_storage")

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
)
channel = connection.channel()
channel.queue_declare(queue='alerts_queue', durable=True)

@app.get("/analytics/process")
def process_data(sensor_id: str):
    # Запрос к сервису хранения данных
    r = requests.get(f"http://{STORAGE_HOST}:8000/storage/data", params={"sensor_id": sensor_id})
    data = r.json().get("data", [])
    if not data:
        return {"status": "no_data"}

    values = [d["value"] for d in data]
    avg = sum(values) / len(values)

    # Простой пример: если среднее значение > 400 ppm, формируем алерт
    if avg > 400:
        message = {"sensor_id": sensor_id, "alert": "CO2_LEVEL_HIGH", "avg": avg}
        channel.basic_publish(exchange='', routing_key='alerts_queue', body=json.dumps(message))
        return {"status": "alert_sent", "avg": avg}
    else:
        return {"status": "normal", "avg": avg}

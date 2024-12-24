from fastapi import FastAPI, Body
import json
import os
import pika

app = FastAPI()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
)
channel = connection.channel()
channel.queue_declare(queue='co2_data_queue', durable=True)

@app.post("/data")
def collect_data(value: float = Body(...), sensor_id: str = Body(...)):
    message = {"sensor_id": sensor_id, "value": value}
    channel.basic_publish(exchange='', routing_key='co2_data_queue', body=json.dumps(message))
    return {"status": "data_received"}

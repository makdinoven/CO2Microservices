from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .db import SessionLocal, CO2Measurement
import os
import pika
import json
import threading
import time

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/storage/data")
def store_data(sensor_id: str, value: float, db: Session = Depends(get_db)):
    measurement = CO2Measurement(sensor_id=sensor_id, value=value)
    db.add(measurement)
    db.commit()
    return {"status": "stored"}

@app.get("/storage/data")
def get_data(sensor_id: str, db: Session = Depends(get_db)):
    results = db.query(CO2Measurement).filter_by(sensor_id=sensor_id).all()
    return {"data": [{"id": r.id, "sensor_id": r.sensor_id, "value": r.value} for r in results]}


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

def consume_messages():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)

    # Попытки подключения к RabbitMQ с ретраями, если он не готов
    connection = None
    for i in range(10):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
            )
            break
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ not ready, retrying in 3 seconds...")
            time.sleep(3)

    if connection is None:
        print("Failed to connect to RabbitMQ after multiple attempts.")
        return

    channel = connection.channel()
    channel.queue_declare(queue='co2_data_queue', durable=True)

    def callback(ch, method, properties, body):
        data = json.loads(body)
        sensor_id = data.get("sensor_id")
        value = data.get("value")

        if sensor_id is not None and value is not None:
            db = SessionLocal()
            try:
                measurement = CO2Measurement(sensor_id=sensor_id, value=value)
                db.add(measurement)
                db.commit()
                print(f"Data stored for sensor {sensor_id}: {value}")
            finally:
                db.close()

        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='co2_data_queue', on_message_callback=callback)
    print("Data Storage Service started. Waiting for data in co2_data_queue...")
    channel.start_consuming()

@app.on_event("startup")
def startup_event():
    # Запускаем потребителя в отдельном потоке, чтобы не блокировать основной поток с Uvicorn
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)
    consumer_thread.start()

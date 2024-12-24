import os
import pika
import json
from sender import send_notification

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "user")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "password")

credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
)
channel = connection.channel()
channel.queue_declare(queue='alerts_queue', durable=True)

def callback(ch, method, properties, body):
    msg = json.loads(body)
    sensor_id = msg.get("sensor_id")
    avg = msg.get("avg")
    send_notification(sensor_id, avg)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='alerts_queue', on_message_callback=callback)
print("Notification Service started. Waiting for alerts...")
channel.start_consuming()

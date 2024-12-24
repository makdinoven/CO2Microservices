def send_notification(sensor_id, avg):
    # Здесь можно внедрить интеграцию с e-mail, Slack, SMS, push-уведомлениями и т.д.
    # Пока просто выводим предупреждение в консоль.
    print(f"ALERT: Sensor {sensor_id} exceeded threshold. AVG={avg}")

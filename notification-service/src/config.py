import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    # RabbitMQ
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_URL = os.getenv(
        "RABBITMQ_URL",
        f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}"
    )

    # Service Configuration
    SERVICE_PORT = int(os.getenv("NOTIFICATION_SERVICE_PORT", 8002))
    SERVICE_HOST = os.getenv("NOTIFICATION_SERVICE_HOST", "0.0.0.0")

    # Message Queue Configuration
    EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "order_exchange")
    ORDER_PROCESSED_QUEUE = os.getenv("ORDER_PROCESSED_QUEUE", "order.processed")
    DEAD_LETTER_QUEUE = os.getenv("DEAD_LETTER_QUEUE", "dead_letter_queue")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", 5))

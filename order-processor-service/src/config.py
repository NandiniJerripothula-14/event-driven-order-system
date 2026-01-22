import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    # Database
    DATABASE_HOST = os.getenv("DATABASE_HOST", "db")
    DATABASE_PORT = int(os.getenv("DATABASE_PORT", 5432))
    DATABASE_NAME = os.getenv("DATABASE_NAME", "order_db")
    DATABASE_USER = os.getenv("DATABASE_USER", "orderuser")
    DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "orderpass")
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )

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
    SERVICE_PORT = int(os.getenv("ORDER_PROCESSOR_PORT", 8001))
    SERVICE_HOST = os.getenv("ORDER_PROCESSOR_HOST", "0.0.0.0")

    # Message Queue Configuration
    EXCHANGE_NAME = os.getenv("EXCHANGE_NAME", "order_exchange")
    ORDER_CREATED_QUEUE = os.getenv("ORDER_CREATED_QUEUE", "order.created")
    ORDER_PROCESSED_QUEUE = os.getenv("ORDER_PROCESSED_QUEUE", "order.processed")
    DEAD_LETTER_QUEUE = os.getenv("DEAD_LETTER_QUEUE", "dead_letter_queue")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", 5))

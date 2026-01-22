import pika
import json
import logging
from datetime import datetime
from uuid import uuid4
from ..config import Config

logger = logging.getLogger(__name__)

class EventPublisher:
    """Handles publishing events to RabbitMQ"""
    
    _connection = None
    _channel = None

    @classmethod
    def connect(cls):
        """Establish connection to RabbitMQ"""
        if cls._connection is None or cls._connection.is_closed:
            try:
                credentials = pika.PlainCredentials(Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD)
                parameters = pika.ConnectionParameters(
                    host=Config.RABBITMQ_HOST,
                    port=Config.RABBITMQ_PORT,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
                cls._connection = pika.BlockingConnection(parameters)
                cls._channel = cls._connection.channel()
                
                # Declare exchange
                cls._channel.exchange_declare(
                    exchange=Config.EXCHANGE_NAME,
                    exchange_type='direct',
                    durable=True
                )
                
                # Declare queues
                cls._channel.queue_declare(queue=Config.ORDER_PROCESSED_QUEUE, durable=True)
                cls._channel.queue_declare(queue=Config.DEAD_LETTER_QUEUE, durable=True)
                
                # Bind queue to exchange
                cls._channel.queue_bind(
                    exchange=Config.EXCHANGE_NAME,
                    queue=Config.ORDER_PROCESSED_QUEUE,
                    routing_key='order.processed'
                )
                
                logger.info("Connected to RabbitMQ")
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise

    @classmethod
    def get_channel(cls):
        """Get or create RabbitMQ channel"""
        if cls._channel is None or cls._channel.is_closed:
            cls.connect()
        return cls._channel

    @classmethod
    def publish_order_processed(cls, order_id: str, status: str):
        """Publish OrderProcessed event"""
        try:
            channel = cls.get_channel()
            
            event_payload = {
                "event_id": str(uuid4()),
                "event_type": "OrderProcessed",
                "order_id": order_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            message = json.dumps(event_payload)
            
            channel.basic_publish(
                exchange=Config.EXCHANGE_NAME,
                routing_key='order.processed',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            
            logger.info(f"Published OrderProcessed event for order {order_id}")
            return event_payload
        except Exception as e:
            logger.error(f"Failed to publish OrderProcessed event: {e}")
            raise

    @classmethod
    def close(cls):
        """Close RabbitMQ connection"""
        if cls._connection and not cls._connection.is_closed:
            cls._connection.close()
            cls._connection = None
            cls._channel = None
            logger.info("RabbitMQ connection closed")

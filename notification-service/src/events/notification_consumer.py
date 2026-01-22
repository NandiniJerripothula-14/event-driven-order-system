import pika
import json
import logging
import sys
import time
from ..config import Config

logger = logging.getLogger(__name__)

class NotificationEventConsumer:
    """Consumer for OrderProcessed events"""
    
    _connection = None
    _channel = None
    _processed_events = set()  # Simple in-memory idempotency tracking

    @classmethod
    def connect(cls):
        """Connect to RabbitMQ"""
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
            
            # Declare exchange and queue
            cls._channel.exchange_declare(
                exchange=Config.EXCHANGE_NAME,
                exchange_type='direct',
                durable=True
            )
            
            cls._channel.queue_declare(queue=Config.ORDER_PROCESSED_QUEUE, durable=True)
            cls._channel.queue_declare(queue=Config.DEAD_LETTER_QUEUE, durable=True)
            
            # Bind queue
            cls._channel.queue_bind(
                exchange=Config.EXCHANGE_NAME,
                queue=Config.ORDER_PROCESSED_QUEUE,
                routing_key='order.processed'
            )
            
            # Set QoS
            cls._channel.basic_qos(prefetch_count=1)
            
            logger.info("Connected to RabbitMQ as consumer")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    @classmethod
    def start_consuming(cls):
        """Start consuming messages"""
        try:
            if cls._channel is None:
                cls.connect()
            
            cls._channel.basic_consume(
                queue=Config.ORDER_PROCESSED_QUEUE,
                on_message_callback=cls._handle_message,
                auto_ack=False
            )
            
            logger.info("Started consuming OrderProcessed events")
            cls._channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumption stopped by user")
            cls.close()
        except Exception as e:
            logger.error(f"Error in consuming: {e}")
            raise

    @classmethod
    def _handle_message(cls, ch, method, properties, body):
        """Handle incoming message"""
        retry_count = 0
        max_retries = Config.MAX_RETRIES
        
        while retry_count < max_retries:
            try:
                event_data = json.loads(body)
                event_id = event_data.get('event_id')
                order_id = event_data.get('order_id')
                status = event_data.get('status')
                
                logger.info(f"Processing OrderProcessed event {event_id} for order {order_id}")
                
                # Check if event was already processed (idempotency)
                if event_id in cls._processed_events:
                    logger.info(f"Event {event_id} already processed, skipping")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Send notification (log to stdout)
                print(f"Notification: Order {order_id} processed successfully with status {status}.")
                logger.info(f"Notification sent for order {order_id}")
                
                # Mark as processed
                cls._processed_events.add(event_id)
                
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Error processing message (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    logger.error(f"Max retries reached for event, sending to DLQ")
                    try:
                        # Send to dead-letter queue
                        ch.basic_publish(
                            exchange='',
                            routing_key=Config.DEAD_LETTER_QUEUE,
                            body=body,
                            properties=pika.BasicProperties(delivery_mode=2)
                        )
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception as dlq_error:
                        logger.error(f"Failed to send message to DLQ: {dlq_error}")
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return
                
                # Wait before retry
                time.sleep(Config.RETRY_DELAY_SECONDS)

    @classmethod
    def close(cls):
        """Close connection"""
        try:
            if cls._connection and not cls._connection.is_closed:
                cls._connection.close()
            cls._connection = None
            cls._channel = None
            logger.info("Consumer connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

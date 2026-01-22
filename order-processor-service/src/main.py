import logging
import sys
from .config import Config
from .db import Database
from .services.event_publisher import EventPublisher
from .consumers.order_consumer import OrderEventConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logger.info("Starting Order Processor Service...")
    
    try:
        # Initialize database connection
        Database.get_pool()
        logger.info("Database connection pool initialized")
        
        # Initialize RabbitMQ connection
        EventPublisher.connect()
        logger.info("RabbitMQ connection established")
        
        # Start consuming events
        logger.info("Starting to consume OrderCreated events...")
        OrderEventConsumer.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        Database.close_all()
        EventPublisher.close()
        logger.info("Order Processor Service stopped")

if __name__ == "__main__":
    main()

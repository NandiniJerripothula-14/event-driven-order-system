import logging
import sys
from .config import Config
from .consumers.notification_consumer import NotificationEventConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logger.info("Starting Notification Service...")
    
    try:
        # Start consuming events
        logger.info("Starting to consume OrderProcessed events...")
        NotificationEventConsumer.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        NotificationEventConsumer.close()
        logger.info("Notification Service stopped")

if __name__ == "__main__":
    main()

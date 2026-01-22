import logging
import sys
from .config import Config
from .consumers.inventory_consumer import InventoryEventConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    logger.info("Starting Inventory Service...")
    
    try:
        # Start consuming events
        logger.info("Starting to consume OrderCreated events...")
        InventoryEventConsumer.start_consuming()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        InventoryEventConsumer.close()
        logger.info("Inventory Service stopped")

if __name__ == "__main__":
    main()

import logging
from ..db import Database

logger = logging.getLogger(__name__)

class OrderProcessor:
    """Service for processing orders"""

    @staticmethod
    def is_event_processed(event_id: str) -> bool:
        """Check if event has been processed (idempotency)"""
        try:
            query = """
            SELECT id FROM processed_events WHERE event_id = %s
            """
            result = Database.execute_query_single(query, (event_id,))
            return result is not None
        except Exception as e:
            logger.error(f"Error checking event: {e}")
            return False

    @staticmethod
    def mark_event_processed(event_id: str, event_type: str, order_id: str):
        """Mark event as processed"""
        try:
            query = """
            INSERT INTO processed_events (event_id, event_type, order_id)
            VALUES (%s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
            """
            Database.execute_update(query, (event_id, event_type, order_id))
            logger.info(f"Marked event {event_id} as processed")
        except Exception as e:
            logger.error(f"Error marking event as processed: {e}")
            raise

    @staticmethod
    def update_order_status(order_id: str, status: str):
        """Update order status in database"""
        try:
            query = """
            UPDATE orders
            SET status = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id, customer_id, items, status, created_at, updated_at
            """
            result = Database.execute_update(query, (status, order_id))
            
            if not result:
                raise Exception(f"Order {order_id} not found")
            
            logger.info(f"Updated order {order_id} status to {status}")
            return result
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            raise

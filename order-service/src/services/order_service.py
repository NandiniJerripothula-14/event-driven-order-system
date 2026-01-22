import json
import logging
from uuid import uuid4
from datetime import datetime
import psycopg2
from ..db import Database
from .event_publisher import EventPublisher

logger = logging.getLogger(__name__)

class OrderService:
    """Service for managing orders"""

    @staticmethod
    def create_order(customer_id: str, items: list) -> dict:
        """
        Create a new order and publish OrderCreated event
        
        Args:
            customer_id: Customer ID
            items: List of order items
            
        Returns:
            Order details dict
        """
        order_id = f"ORD-{uuid4().hex[:12].upper()}"
        
        try:
            # Insert order into database
            query = """
            INSERT INTO orders (id, customer_id, items, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
            RETURNING id, customer_id, items, status, created_at, updated_at
            """
            
            items_json = json.dumps([{"product_id": item.product_id, "quantity": item.quantity} for item in items])
            
            result = Database.execute_insert(query, (order_id, customer_id, items_json, 'PENDING'))
            
            if not result:
                raise Exception("Failed to insert order into database")
            
            logger.info(f"Order {order_id} created successfully")
            
            # Publish OrderCreated event
            items_list = [{"product_id": item.product_id, "quantity": item.quantity} for item in items]
            EventPublisher.publish_order_created(order_id, customer_id, items_list)
            
            return {
                "order_id": result['id'],
                "customer_id": result['customer_id'],
                "items": json.loads(result['items']),
                "status": result['status'],
                "created_at": result['created_at'],
                "updated_at": result['updated_at']
            }
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            raise

    @staticmethod
    def get_order(order_id: str) -> dict:
        """
        Retrieve order details by ID
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details dict or None if not found
        """
        try:
            query = """
            SELECT id, customer_id, items, status, created_at, updated_at
            FROM orders
            WHERE id = %s
            """
            
            result = Database.execute_query_single(query, (order_id,))
            
            if not result:
                return None
            
            return {
                "id": result['id'],
                "customer_id": result['customer_id'],
                "items": json.loads(result['items']),
                "status": result['status'],
                "created_at": result['created_at'],
                "updated_at": result['updated_at']
            }
        except Exception as e:
            logger.error(f"Error retrieving order {order_id}: {e}")
            raise

    @staticmethod
    def get_all_orders() -> list:
        """Retrieve all orders"""
        try:
            query = """
            SELECT id, customer_id, items, status, created_at, updated_at
            FROM orders
            ORDER BY created_at DESC
            """
            
            results = Database.execute_query(query)
            
            return [
                {
                    "id": result['id'],
                    "customer_id": result['customer_id'],
                    "items": json.loads(result['items']),
                    "status": result['status'],
                    "created_at": result['created_at'],
                    "updated_at": result['updated_at']
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error retrieving orders: {e}")
            raise

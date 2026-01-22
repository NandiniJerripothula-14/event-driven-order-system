import pytest
import asyncio
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Configuration for test environment
TEST_DB_URL = "postgresql://orderuser:orderpass@localhost:5432/order_db"
RABBITMQ_URL = "amqp://guest:guest@localhost:5672"

@contextmanager
def get_db_connection():
    """Get database connection for testing"""
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="order_db",
        user="orderuser",
        password="orderpass"
    )
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_rabbitmq_connection():
    """Get RabbitMQ connection for testing"""
    credentials = pika.PlainCredentials("guest", "guest")
    parameters = pika.ConnectionParameters(
        host="localhost",
        port=5672,
        credentials=credentials
    )
    conn = pika.BlockingConnection(parameters)
    try:
        yield conn
    finally:
        conn.close()

class TestIntegrationE2E:
    """End-to-end integration tests"""

    def setup_method(self):
        """Setup before each test"""
        # Wait for services to be ready
        self._wait_for_services()

    def _wait_for_services(self, timeout=30):
        """Wait for all services to be ready"""
        import requests
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get("http://localhost:8000/health")
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        
        raise Exception("Order Service not ready after 30 seconds")

    def test_order_creation_flow(self):
        """
        Integration test: Create order and verify status transitions
        
        Expected flow:
        1. POST /orders creates order with PENDING status
        2. OrderCreated event published
        3. OrderProcessor consumes event and updates status to PROCESSING
        4. OrderProcessed event published
        5. Notification and Inventory services consume events
        6. Verify final state matches expectations
        """
        import requests
        
        # Step 1: Create an order
        order_payload = {
            "customer_id": "CUST-INT-001",
            "items": [
                {"product_id": "P001", "quantity": 2},
                {"product_id": "P002", "quantity": 1}
            ]
        }
        
        response = requests.post(
            "http://localhost:8000/orders",
            json=order_payload
        )
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data['status'] == 'PENDING'
        order_id = response_data['order_id']
        
        logger.info(f"Created order: {order_id}")
        
        # Step 2: Wait for event processing (Order Processor)
        time.sleep(3)
        
        # Step 3: Verify order status was updated to PROCESSING
        response = requests.get(f"http://localhost:8000/orders/{order_id}")
        assert response.status_code == 200
        
        order_data = response.json()
        assert order_data['id'] == order_id
        assert order_data['customer_id'] == 'CUST-INT-001'
        assert len(order_data['items']) == 2
        assert order_data['status'] == 'PROCESSING'
        
        logger.info(f"Order {order_id} status verified as PROCESSING")
        
        # Step 4: Verify database state
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT id, status FROM orders WHERE id = %s", (order_id,))
            db_order = cur.fetchone()
            cur.close()
            
            assert db_order is not None
            assert db_order['status'] == 'PROCESSING'

    def test_order_retrieval_multiple(self):
        """Test retrieving multiple orders"""
        import requests
        
        # Create multiple orders
        for i in range(3):
            order_payload = {
                "customer_id": f"CUST-MULTI-{i}",
                "items": [{"product_id": "P001", "quantity": 1}]
            }
            
            response = requests.post(
                "http://localhost:8000/orders",
                json=order_payload
            )
            assert response.status_code == 201
        
        # Retrieve all orders
        response = requests.get("http://localhost:8000/orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert len(data['orders']) >= 3

    def test_order_not_found(self):
        """Test retrieving non-existent order"""
        import requests
        
        response = requests.get("http://localhost:8000/orders/ORD-NOTEXIST")
        assert response.status_code == 404

    def test_invalid_order_payload(self):
        """Test creating order with invalid payload"""
        import requests
        
        # Missing required field
        order_payload = {
            "customer_id": "CUST001"
            # Missing items
        }
        
        response = requests.post(
            "http://localhost:8000/orders",
            json=order_payload
        )
        assert response.status_code in [400, 422]  # Validation error

    def test_message_queue_connectivity(self):
        """Test RabbitMQ connectivity"""
        try:
            with get_rabbitmq_connection() as conn:
                channel = conn.channel()
                
                # Check if exchange exists
                channel.exchange_declare(
                    exchange='order_exchange',
                    exchange_type='direct',
                    passive=True
                )
                
                # Check if queues exist
                for queue_name in ['order.created', 'order.processed']:
                    channel.queue_declare(queue=queue_name, passive=True)
                
                logger.info("RabbitMQ connectivity verified")
        except Exception as e:
            pytest.fail(f"RabbitMQ connectivity test failed: {e}")

    def test_database_connectivity(self):
        """Test database connectivity"""
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1")
                result = cur.fetchone()
                cur.close()
                
                assert result is not None
                logger.info("Database connectivity verified")
        except Exception as e:
            pytest.fail(f"Database connectivity test failed: {e}")

    def test_processed_events_idempotency(self):
        """Test that processed events are tracked for idempotency"""
        import requests
        
        # Create an order
        order_payload = {
            "customer_id": "CUST-IDEMPOTENT",
            "items": [{"product_id": "P001", "quantity": 1}]
        }
        
        response = requests.post(
            "http://localhost:8000/orders",
            json=order_payload
        )
        assert response.status_code == 201
        order_id = response.json()['order_id']
        
        # Wait for processing
        time.sleep(3)
        
        # Verify processed_events table has entries
        with get_db_connection() as conn:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(
                "SELECT COUNT(*) as count FROM processed_events WHERE order_id = %s",
                (order_id,)
            )
            result = cur.fetchone()
            cur.close()
            
            assert result['count'] >= 1
            logger.info(f"Processed events verified for order {order_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

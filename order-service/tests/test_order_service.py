import pytest
from unittest.mock import patch, MagicMock
from src.services.order_service import OrderService
from src.models.order import OrderItem


class TestOrderService:
    """Unit tests for OrderService"""

    @patch('src.services.order_service.Database.execute_insert')
    @patch('src.services.order_service.EventPublisher.publish_order_created')
    def test_create_order_success(self, mock_publish, mock_db):
        """Test successful order creation"""
        # Setup
        mock_db.return_value = {
            'id': 'ORD-TEST123',
            'customer_id': 'CUST001',
            'items': '[{"product_id": "P001", "quantity": 2}]',
            'status': 'PENDING',
            'created_at': '2024-01-22T10:00:00',
            'updated_at': '2024-01-22T10:00:00'
        }

        items = [OrderItem(product_id='P001', quantity=2)]
        
        # Execute
        result = OrderService.create_order('CUST001', items)
        
        # Assert
        assert result['order_id'] == 'ORD-TEST123'
        assert result['status'] == 'PENDING'
        assert result['customer_id'] == 'CUST001'
        assert len(result['items']) == 1
        assert result['items'][0]['product_id'] == 'P001'
        mock_publish.assert_called_once()

    @patch('src.services.order_service.Database.execute_query_single')
    def test_get_order_success(self, mock_db):
        """Test retrieving existing order"""
        # Setup
        mock_db.return_value = {
            'id': 'ORD-TEST123',
            'customer_id': 'CUST001',
            'items': '[{"product_id": "P001", "quantity": 2}]',
            'status': 'PROCESSING',
            'created_at': '2024-01-22T10:00:00',
            'updated_at': '2024-01-22T10:05:00'
        }
        
        # Execute
        result = OrderService.get_order('ORD-TEST123')
        
        # Assert
        assert result is not None
        assert result['id'] == 'ORD-TEST123'
        assert result['status'] == 'PROCESSING'

    @patch('src.services.order_service.Database.execute_query_single')
    def test_get_order_not_found(self, mock_db):
        """Test retrieving non-existent order"""
        # Setup
        mock_db.return_value = None
        
        # Execute
        result = OrderService.get_order('ORD-NOTEXIST')
        
        # Assert
        assert result is None

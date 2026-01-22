import pytest
from unittest.mock import patch, MagicMock
from src.services.order_processor import OrderProcessor


class TestOrderProcessor:
    """Unit tests for OrderProcessor"""

    @patch('src.services.order_processor.Database.execute_query_single')
    def test_is_event_processed_true(self, mock_db):
        """Test checking if event was already processed"""
        # Setup
        mock_db.return_value = {'id': 1}
        
        # Execute
        result = OrderProcessor.is_event_processed('EVENT-123')
        
        # Assert
        assert result is True

    @patch('src.services.order_processor.Database.execute_query_single')
    def test_is_event_processed_false(self, mock_db):
        """Test checking if event hasn't been processed"""
        # Setup
        mock_db.return_value = None
        
        # Execute
        result = OrderProcessor.is_event_processed('EVENT-456')
        
        # Assert
        assert result is False

    @patch('src.services.order_processor.Database.execute_update')
    def test_update_order_status_success(self, mock_db):
        """Test updating order status"""
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
        result = OrderProcessor.update_order_status('ORD-TEST123', 'PROCESSING')
        
        # Assert
        assert result is not None
        assert result['status'] == 'PROCESSING'
        mock_db.assert_called_once()

    @patch('src.services.order_processor.Database.execute_update')
    def test_update_order_status_not_found(self, mock_db):
        """Test updating status for non-existent order"""
        # Setup
        mock_db.return_value = None
        
        # Execute & Assert
        with pytest.raises(Exception):
            OrderProcessor.update_order_status('ORD-NOTEXIST', 'PROCESSING')

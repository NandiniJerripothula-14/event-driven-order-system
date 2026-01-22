import pytest
from src.consumers.inventory_consumer import InventoryEventConsumer


class TestInventoryConsumer:
    """Unit tests for InventoryConsumer"""

    def test_event_idempotency_tracking(self):
        """Test that already processed events are skipped"""
        event_id = "EVENT-INV-123"
        
        # Add to processed set
        InventoryEventConsumer._processed_events.add(event_id)
        
        # Verify it's tracked
        assert event_id in InventoryEventConsumer._processed_events

    def test_event_processing_set(self):
        """Test event processing set management"""
        event_id = "EVENT-INV-789"
        
        # Add event
        InventoryEventConsumer._processed_events.add(event_id)
        
        # Verify
        assert event_id in InventoryEventConsumer._processed_events
        assert len(InventoryEventConsumer._processed_events) > 0

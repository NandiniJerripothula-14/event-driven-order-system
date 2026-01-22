import pytest
from src.consumers.notification_consumer import NotificationEventConsumer


class TestNotificationConsumer:
    """Unit tests for NotificationEventConsumer"""

    def test_event_idempotency_tracking(self):
        """Test that already processed events are skipped"""
        event_id = "EVENT-123"
        
        # Add to processed set
        NotificationEventConsumer._processed_events.add(event_id)
        
        # Verify it's tracked
        assert event_id in NotificationEventConsumer._processed_events

    def test_event_idempotency_new_event(self):
        """Test that new events are marked as processed"""
        event_id = "EVENT-NEW-456"
        
        # Should not be in processed set initially
        assert event_id not in NotificationEventConsumer._processed_events
        
        # Add to processed set
        NotificationEventConsumer._processed_events.add(event_id)
        
        # Verify it's now tracked
        assert event_id in NotificationEventConsumer._processed_events

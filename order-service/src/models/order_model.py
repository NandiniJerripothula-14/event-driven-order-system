from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class OrderItem(BaseModel):
    """Order item model"""
    product_id: str
    quantity: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "P001",
                "quantity": 2
            }
        }

class OrderCreateRequest(BaseModel):
    """Request model for creating an order"""
    customer_id: str
    items: List[OrderItem]
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "CUST001",
                "items": [
                    {"product_id": "P001", "quantity": 2},
                    {"product_id": "P002", "quantity": 1}
                ]
            }
        }

class OrderResponse(BaseModel):
    """Response model for order creation"""
    order_id: str
    status: str
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD-12345",
                "status": "PENDING",
                "created_at": "2024-01-22T10:30:00Z"
            }
        }

class OrderDetailResponse(BaseModel):
    """Detailed order response"""
    id: str
    customer_id: str
    items: List[OrderItem]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ORD-12345",
                "customer_id": "CUST001",
                "items": [
                    {"product_id": "P001", "quantity": 2},
                    {"product_id": "P002", "quantity": 1}
                ],
                "status": "PROCESSING",
                "created_at": "2024-01-22T10:30:00Z",
                "updated_at": "2024-01-22T10:31:00Z"
            }
        }

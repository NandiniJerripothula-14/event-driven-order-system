from fastapi import APIRouter, HTTPException, status
from ..models.order_model import OrderCreateRequest, OrderResponse, OrderDetailResponse
from ..services.order_service import OrderService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrderResponse)
async def create_order(order_request: OrderCreateRequest):
    """
    Create a new order
    
    - **customer_id**: Customer identifier
    - **items**: List of items with product_id and quantity
    
    Returns order_id, status, and created_at timestamp
    """
    try:
        order = OrderService.create_order(order_request.customer_id, order_request.items)
        return OrderResponse(
            order_id=order['order_id'],
            status=order['status'],
            created_at=order['created_at']
        )
    except Exception as e:
        logger.error(f"Error in create_order endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(order_id: str):
    """
    Retrieve order details by ID
    
    - **order_id**: Order identifier
    
    Returns full order details including current status
    """
    try:
        order = OrderService.get_order(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        return OrderDetailResponse(**order)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_order endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve order"
        )

@router.get("")
async def list_orders():
    """Get all orders"""
    try:
        orders = OrderService.get_all_orders()
        return {"orders": orders}
    except Exception as e:
        logger.error(f"Error in list_orders endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve orders"
        )

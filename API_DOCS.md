# Event-Driven Order System - API Documentation

## Overview
This API documentation describes the endpoints available in the Order Service microservice. All endpoints are RESTful and return JSON responses.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required for API endpoints. In production, implement OAuth2 or JWT token validation.

---

## Endpoints

### 1. Create Order
**POST** `/orders`

Create a new order in the system. This endpoint accepts customer and item information, persists the order with PENDING status, and publishes an OrderCreated event.

#### Request
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "items": [
      {"product_id": "P001", "quantity": 2},
      {"product_id": "P002", "quantity": 1}
    ]
  }'
```

#### Request Body
```json
{
  "customer_id": "string (required)",
  "items": [
    {
      "product_id": "string (required)",
      "quantity": "integer (required)"
    }
  ]
}
```

#### Success Response
**HTTP 201 Created**
```json
{
  "order_id": "ORD-A1B2C3D4E5F6",
  "status": "PENDING",
  "created_at": "2024-01-22T10:30:00Z"
}
```

#### Error Responses
**HTTP 400 Bad Request** - Invalid request payload
```json
{
  "detail": "Validation error details"
}
```

**HTTP 500 Internal Server Error** - Server error during order creation
```json
{
  "detail": "Failed to create order"
}
```

---

### 2. Get Order Details
**GET** `/orders/{order_id}`

Retrieve detailed information about a specific order, including its current status and all items.

#### Request
```bash
curl -X GET http://localhost:8000/orders/ORD-A1B2C3D4E5F6
```

#### Success Response
**HTTP 200 OK**
```json
{
  "id": "ORD-A1B2C3D4E5F6",
  "customer_id": "CUST001",
  "items": [
    {
      "product_id": "P001",
      "quantity": 2
    },
    {
      "product_id": "P002",
      "quantity": 1
    }
  ],
  "status": "PROCESSING",
  "created_at": "2024-01-22T10:30:00Z",
  "updated_at": "2024-01-22T10:31:00Z"
}
```

#### Error Responses
**HTTP 404 Not Found** - Order does not exist
```json
{
  "detail": "Order ORD-NOTEXIST not found"
}
```

**HTTP 500 Internal Server Error** - Server error
```json
{
  "detail": "Failed to retrieve order"
}
```

---

### 3. List All Orders
**GET** `/orders`

Retrieve a list of all orders in the system (for testing/debugging).

#### Request
```bash
curl -X GET http://localhost:8000/orders
```

#### Success Response
**HTTP 200 OK**
```json
{
  "orders": [
    {
      "id": "ORD-A1B2C3D4E5F6",
      "customer_id": "CUST001",
      "items": [
        {
          "product_id": "P001",
          "quantity": 2
        }
      ],
      "status": "PROCESSING",
      "created_at": "2024-01-22T10:30:00Z",
      "updated_at": "2024-01-22T10:31:00Z"
    }
  ]
}
```

---

### 4. Health Check
**GET** `/health`

Check the health status of the Order Service, including database and RabbitMQ connectivity.

#### Request
```bash
curl -X GET http://localhost:8000/health
```

#### Success Response
**HTTP 200 OK**
```json
{
  "status": "healthy"
}
```

#### Error Response
**HTTP 503 Service Unavailable** - Service is unhealthy
```json
{
  "status": "unhealthy"
}
```

---

## Order Status Values

Orders transition through the following states:

| Status | Description | Set By |
|--------|-------------|--------|
| PENDING | Order created, awaiting processing | Order Service |
| PROCESSING | Order is being processed | Order Processor Service |
| COMPLETED | Order processing complete | (Future) |
| CANCELLED | Order was cancelled | (Future) |

---

## Event Flow Diagram

```
POST /orders
     ↓
[Order Service]
     ↓
Database Insert (status: PENDING)
     ↓
Publish OrderCreated Event
     ↓
┌────────────────────────────────────────┐
│         Message Queue (RabbitMQ)       │
│  order.created event (fanout)          │
└────────────────────────────────────────┘
     ↙              ↓              ↘
[Order Processor]  [Inventory]  [Others]
     ↓
Update Status to PROCESSING
     ↓
Publish OrderProcessed Event
     ↓
     ┌──────────────────────────────┐
     │    Message Queue (RabbitMQ)  │
     │  order.processed event       │
     └──────────────────────────────┘
     ↓
[Notification Service]
     ↓
Log Notification to stdout
```

---

## Testing with cURL

### Create an Order
```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-TEST-001",
    "items": [
      {"product_id": "P001", "quantity": 3},
      {"product_id": "P003", "quantity": 1}
    ]
  }'
```

### Retrieve Order (after capturing order_id)
```bash
curl -X GET http://localhost:8000/orders/ORD-ABC123DEF456
```

### Check System Health
```bash
curl -X GET http://localhost:8000/health
```

---

## Testing with Postman

1. **Import Collection**: Use the Postman collection JSON (if provided)
2. **Set Base URL**: `http://localhost:8000`
3. **Test Endpoints**: Execute requests in the collection

---

## Rate Limiting & Quotas

Currently, no rate limiting is implemented. For production deployments, implement:
- Request rate limiting per customer
- Concurrent connection limits
- Queue backpressure mechanisms

---

## Error Handling

All error responses follow this format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

HTTP Status Codes:
- `200` - Success
- `201` - Created (successful POST)
- `400` - Bad Request (invalid input)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Environment Variables

The Order Service uses the following environment variables:

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
RABBITMQ_URL=amqp://user:pass@host:5672
ORDER_SERVICE_PORT=8000
EXCHANGE_NAME=order_exchange
ORDER_CREATED_QUEUE=order.created
ORDER_PROCESSED_QUEUE=order.processed
```

See `.env.example` for complete configuration.

---

## Support

For issues or questions:
1. Check the logs: `docker logs order-service`
2. Verify connectivity: `curl http://localhost:8000/health`
3. Review the README.md for setup instructions

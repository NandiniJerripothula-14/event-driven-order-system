# Event-Driven Order System - Architecture Documentation

## System Overview

The Event-Driven Order System is a microservice-based architecture that processes e-commerce orders asynchronously. Services communicate via a message broker (RabbitMQ), ensuring loose coupling and high availability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Clients                              │
│                     (Browser, Mobile, CLI)                       │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  │ HTTP
                  ↓
        ┌─────────────────────┐
        │   Order Service     │ (FastAPI)
        │   Port: 8000        │
        ├─────────────────────┤
        │ • POST /orders      │
        │ • GET /orders/{id}  │
        │ • GET /health       │
        └──────┬──────────────┘
               │
        ┌──────┴──────────────────────────────────────┐
        │                                             │
        ↓                                             ↓
    ┌────────┐                                   ┌─────────┐
    │Database│                                   │RabbitMQ │
    │  (PG)  │                                   │ (MQ)    │
    └────────┘                                   └────┬────┘
                                                      │
                        ┌─────────────────────────────┼─────────────────────────┐
                        │                             │                         │
                        ↓                             ↓                         ↓
              ┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
              │ Order Processor  │      │ Inventory Svc    │      │ Notification Svc │
              │ Port: 8001       │      │ Port: 8003       │      │ Port: 8002       │
              ├──────────────────┤      ├──────────────────┤      ├──────────────────┤
              │ Consumes:        │      │ Consumes:        │      │ Consumes:        │
              │ OrderCreated     │      │ OrderCreated     │      │ OrderProcessed   │
              │                  │      │                  │      │                  │
              │ Updates DB:      │      │ Logs stdout:     │      │ Logs stdout:     │
              │ Status→PROCESSING│      │ Inventory rsrv   │      │ Order processed  │
              │                  │      │                  │      │                  │
              │ Publishes:       │      │ Publishes:       │      │ Publishes:       │
              │ OrderProcessed   │      │ (none)           │      │ (none)           │
              └──────────────────┘      └──────────────────┘      └──────────────────┘
```

## Core Components

### 1. Order Service
**Technology**: FastAPI (Python) + Uvicorn
**Port**: 8000
**Responsibility**: RESTful API for order management

**Features**:
- POST /orders - Create new orders
- GET /orders/{id} - Retrieve order details
- GET /orders - List all orders (for testing)
- GET /health - Health check endpoint

**Database Schema**:
```sql
CREATE TABLE orders (
    id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255),
    items JSONB,
    status order_status DEFAULT 'PENDING',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Event Publishing**:
- Publishes `OrderCreated` events to `order_exchange` after successful persistence
- Uses durable queues and persistent messages for reliability

---

### 2. Order Processor Service
**Technology**: Python with pika (RabbitMQ client)
**Port**: 8001
**Responsibility**: Processes OrderCreated events and updates order status

**Event Consumption**:
- Listens to `order.created` queue
- Consumes OrderCreated events

**Processing Logic**:
1. Checks idempotency (event already processed?)
2. Updates order status to PROCESSING in database
3. Marks event as processed (for idempotency)
4. Publishes OrderProcessed event
5. Acknowledges message from queue

**Error Handling**:
- Implements retry logic with exponential backoff
- Sends messages to Dead-Letter Queue (DLQ) after max retries
- Transaction-based database updates for consistency

---

### 3. Notification Service
**Technology**: Python with pika
**Port**: 8002
**Responsibility**: Sends notifications for processed orders

**Event Consumption**:
- Listens to `order.processed` queue
- Consumes OrderProcessed events

**Processing Logic**:
1. Checks idempotency (event already processed?)
2. Logs notification to stdout: "Notification: Order {id} processed successfully with status {status}."
3. Acknowledges message from queue

**Note**: In production, this would integrate with email, SMS, or push notification services.

---

### 4. Inventory Service
**Technology**: Python with pika
**Port**: 8003
**Responsibility**: Reserves inventory for orders (simulated)

**Event Consumption**:
- Listens to `order.created` queue (shared with order processor)
- Consumes OrderCreated events

**Processing Logic**:
1. Checks idempotency (event already processed?)
2. For each item in the order, simulates inventory reservation
3. Logs to stdout: "Inventory: Reserved {quantity} of product {product_id} for order {order_id}."
4. Acknowledges message from queue

**Note**: Simulation only. In production, this would update actual inventory database.

---

### 5. PostgreSQL Database
**Version**: 15-Alpine
**Container**: order_db
**Initialization**: Via `db/init.sql`

**Tables**:
- `products` - Product catalog with stock levels
- `orders` - Order records with status tracking
- `processed_events` - Event idempotency tracking

**Indexing**:
- Index on orders.id for fast lookups
- Index on orders.customer_id for customer queries
- Index on orders.status for status filtering
- Indexes on processed_events for idempotency checks

---

### 6. RabbitMQ Message Broker
**Version**: 3.12-Management-Alpine
**Ports**: 5672 (AMQP), 15672 (Management UI)

**Exchange Configuration**:
- Name: `order_exchange`
- Type: `direct` (for specific routing)
- Durable: Yes

**Queues**:
- `order.created` - OrderCreated events (consumed by Order Processor & Inventory Service)
- `order.processed` - OrderProcessed events (consumed by Notification Service)
- `dead_letter_queue` - Failed messages for later analysis

**Message Properties**:
- Persistent delivery mode (survives broker restarts)
- Content type: application/json
- Manual acknowledgment (QoS=1)

---

## Event Schemas

### OrderCreated Event
```json
{
  "event_id": "UUID",
  "event_type": "OrderCreated",
  "order_id": "ORD-ABC123",
  "customer_id": "CUST001",
  "items": [
    {"product_id": "P001", "quantity": 2},
    {"product_id": "P002", "quantity": 1}
  ],
  "timestamp": "2024-01-22T10:30:00Z"
}
```

### OrderProcessed Event
```json
{
  "event_id": "UUID",
  "event_type": "OrderProcessed",
  "order_id": "ORD-ABC123",
  "status": "PROCESSING",
  "timestamp": "2024-01-22T10:31:00Z"
}
```

---

## Data Flow & Eventual Consistency

### Happy Path
```
1. Client → POST /orders
   ↓
2. Order Service: INSERT order (PENDING status)
   ↓
3. Publish OrderCreated event
   ↓
4. Order Processor: Consume event
   ↓
5. Order Processor: UPDATE order status (PROCESSING)
   ↓
6. Order Processor: Publish OrderProcessed event
   ↓
7. Notification Service: Consume event & log
   ↓
8. Inventory Service: Already consumed OrderCreated & logged
   ↓
9. Client: Poll GET /orders/{id} → Status = PROCESSING
```

### Error Handling Path
```
1. Consumer: Attempt to process message
   ↓
2. Failure occurs (DB down, timeout, etc.)
   ↓
3. Retry attempt (up to MAX_RETRIES)
   ↓
4. If all retries fail:
   → Message sent to Dead-Letter Queue
   → Message acknowledged (removed from main queue)
   → No data loss
   ↓
5. Operator: Review DLQ messages, handle manually
```

---

## Idempotency Strategy

### Problem
Message processing failures can cause duplicate processing. Without idempotency safeguards, this leads to:
- Duplicate order status updates
- Duplicate inventory reservations
- Duplicate notifications

### Solution

**1. Database-Level Idempotency (Order Processor)**
```sql
-- processed_events table tracks consumed events
CREATE TABLE processed_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(100),
    order_id VARCHAR(255),
    processed_at TIMESTAMP
);

-- Before processing, check:
SELECT id FROM processed_events WHERE event_id = ?
-- If found, skip processing (already done)
-- If not found, process and insert record
```

**2. In-Memory Idempotency (Notification & Inventory Services)**
```python
# Simple set-based tracking
_processed_events = set()

# Check before processing
if event_id in _processed_events:
    ack_message()
    return

# Process...
_processed_events.add(event_id)
```

**3. Message Deduplication (RabbitMQ)**
- Messages include unique `event_id`
- Consumers track this ID
- Duplicate messages (from redelivery) are identified by ID

---

## Resilience Patterns

### 1. Circuit Breaker (Future Implementation)
```
Success Rate Monitoring
    ↓
    If errors < threshold → Circuit CLOSED (allow traffic)
    If errors > threshold → Circuit OPEN (reject traffic)
    → After timeout → Circuit HALF-OPEN (test recovery)
```

### 2. Retry Strategy
```
Initial Attempt
    ↓ Failure
Retry 1 (after 5s)
    ↓ Failure
Retry 2 (after 5s)
    ↓ Failure
Retry 3 (after 5s)
    ↓ Failure
Send to Dead-Letter Queue
```

### 3. Dead-Letter Queue (DLQ)
```
Failed Message
    ↓
DLQ Storage
    ↓
Operator Review
    ↓
Manual Intervention/Replay
```

### 4. Health Checks
```
Each service implements /health endpoint
Docker Compose monitors health status
Unhealthy containers are restarted automatically
```

---

## Scalability Considerations

### Horizontal Scaling
```
Order Service (Stateless)
    ↓ Load Balancer
    ├─ Instance 1
    ├─ Instance 2
    └─ Instance 3
    ↓
    Shared Database (Single)
    Shared Message Broker (Single)
```

**Why possible**: Services are stateless; database and MQ handle state.

### Vertical Scaling
- Increase container resource limits (CPU, memory)
- Configure RabbitMQ prefetch count (currently 1 for fairness)
- Implement database connection pooling

### Message Throughput
- Order Service: Limited by HTTP handlers (uvicorn workers)
- Consumers: Limited by RabbitMQ prefetch count (1 message at a time)
- Database: Limited by connection pool (20 connections)

---

## Security Considerations

### Current Implementation
- No authentication (suitable for internal services)
- No HTTPS (internal Docker network)
- Database credentials in environment variables
- RabbitMQ guest credentials (development only)

### Production Hardening

**Authentication**:
```python
# Add OAuth2/JWT token validation to Order Service
from fastapi.security import HTTPBearer

@app.get("/orders")
async def get_orders(token: str = Depends(HTTPBearer())):
    # Validate token
    # ...
```

**TLS/HTTPS**:
```yaml
# docker-compose.yml - Add TLS
order-service:
  environment:
    TLS_CERT: /etc/certs/cert.pem
    TLS_KEY: /etc/certs/key.pem
  volumes:
    - ./certs:/etc/certs:ro
```

**RabbitMQ Credentials**:
```yaml
# Use strong passwords from environment variables
RABBITMQ_USER: ${RABBITMQ_USER}
RABBITMQ_PASSWORD: ${RABBITMQ_PASSWORD}
```

**Database Encryption**:
```sql
-- Use pgcrypto for sensitive data
CREATE EXTENSION pgcrypto;
-- Encrypt customer_id and payment info
```

---

## Monitoring & Observability

### Logging
- All services log to stdout (Docker captures)
- JSON structured logging (future improvement)
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics (Future)
```
Prometheus collectors for:
- Request count
- Request latency
- Error rate
- Queue depth
- Database connection usage
```

### Tracing (Future)
```
Distributed tracing with OpenTelemetry:
- Request ID propagation through services
- Timeline visualization
- Performance bottleneck identification
```

---

## Technology Stack Rationale

### Python + FastAPI
- ✅ Fast startup and execution
- ✅ Excellent async support
- ✅ Built-in validation with Pydantic
- ✅ Auto API documentation (Swagger)

### PostgreSQL
- ✅ ACID compliance (data safety)
- ✅ JSONB support (flexible items storage)
- ✅ Connection pooling (efficiency)
- ✅ Full-text search (scalability)

### RabbitMQ
- ✅ Durable queues (no message loss)
- ✅ Priority queues (future)
- ✅ Clustering (high availability)
- ✅ Management UI (debugging)

### Docker & Docker Compose
- ✅ Consistent environments
- ✅ Easy scaling and deployment
- ✅ Service isolation
- ✅ Health checks

---

## Future Enhancements

1. **GraphQL API**: Alternative to REST for complex queries
2. **Event Sourcing**: Store all events as single source of truth
3. **CQRS Pattern**: Separate read/write models for better scalability
4. **Saga Pattern**: Distributed transactions across services
5. **Kubernetes**: Replace Docker Compose for cloud deployment
6. **Message Encryption**: Secure sensitive data in transit
7. **API Gateway**: Centralized authentication and rate limiting
8. **Analytics**: Track order metrics and trends
9. **Payment Processing**: Integration with payment gateways
10. **Admin Dashboard**: Monitor orders and system health

---

## Deployment Checklist

- [ ] Clone repository
- [ ] Copy `.env.example` to `.env` and configure
- [ ] Build Docker images: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Verify health: `curl http://localhost:8000/health`
- [ ] Run tests: `pytest order-service/tests -v`
- [ ] Create test order: `curl -X POST http://localhost:8000/orders ...`
- [ ] Monitor logs: `docker-compose logs -f`
- [ ] Stop services: `docker-compose down`


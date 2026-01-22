# Quick Reference Card

## 🚀 Start Here

```bash
# 1. Clone & Setup
git clone <repo-url>
cd event-driven-order-system
cp .env.example .env

# 2. Start System
docker-compose up -d

# 3. Create Order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "items": [{"product_id": "P001", "quantity": 2}]
  }'

# 4. Get Status
curl http://localhost:8000/orders/ORD-<id>

# 5. View Logs
docker-compose logs -f
```

## 📋 Common Commands

### System Management
```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose restart        # Restart services
docker-compose ps            # Check status
docker-compose logs -f       # View logs (all)
docker-compose logs order-service -f  # View specific logs
```

### Helper Scripts (Unix/macOS)
```bash
./scripts.sh start            # Start system
./scripts.sh test-unit        # Run unit tests
./scripts.sh test-integration # Run integration tests
./scripts.sh create-order     # Create test order
./scripts.sh logs-all         # View all logs
./scripts.sh help             # Show all commands
```

### Helper Scripts (Windows)
```batch
scripts.bat start             # Start system
scripts.bat test_unit         # Run unit tests
scripts.bat create_order      # Create test order
scripts.bat logs_all          # View all logs
scripts.bat help              # Show all commands
```

### Testing
```bash
# Unit tests
docker-compose exec order-service pytest tests/test_order_service.py -v

# Integration tests
docker-compose exec order-service pytest tests/test_integration.py -v -s

# All tests
docker-compose exec order-service pytest tests/ -v
```

### Debugging
```bash
# Check service health
curl http://localhost:8000/health

# Access RabbitMQ UI
open http://localhost:15672  # guest/guest

# Access PostgreSQL
docker-compose exec db psql -U orderuser -d order_db

# Shell into container
docker-compose exec order-service bash
```

## 🔗 API Endpoints

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | /orders | Create order | 201 |
| GET | /orders/{id} | Get order details | 200/404 |
| GET | /orders | List all orders | 200 |
| GET | /health | Service health | 200/503 |

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Order Service | 8000 | http://localhost:8000 |
| Order Processor | 8001 | (internal) |
| Notification Service | 8002 | (internal) |
| Inventory Service | 8003 | (internal) |
| PostgreSQL | 5432 | localhost:5432 |
| RabbitMQ | 5672 | amqp://localhost:5672 |
| RabbitMQ UI | 15672 | http://localhost:15672 |

## 📁 Project Structure

```
event-driven-order-system/
├── README.md                 # Start here
├── docker-compose.yml        # All services
├── .env.example             # Configuration
├── db/init.sql              # Database schema
├── order-service/           # API service
├── order-processor-service/ # Event processor
├── notification-service/    # Event consumer
├── inventory-service/       # Event consumer
└── scripts.sh / scripts.bat  # Helper scripts
```

## 🔐 Default Credentials

| Service | User | Password |
|---------|------|----------|
| RabbitMQ | guest | guest |
| PostgreSQL | orderuser | orderpass |

**⚠️ Change in production!**

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Project overview & quick start |
| API_DOCS.md | API endpoint reference |
| ARCHITECTURE.md | System design & patterns |
| DEPLOYMENT.md | Production deployment |
| PROJECT_SUMMARY.md | Project overview |

## 🆘 Troubleshooting

### Services won't start
```bash
docker-compose logs db        # Check database logs
docker-compose logs rabbitmq  # Check RabbitMQ logs
docker-compose up -d --remove-orphans
```

### Can't connect to services
```bash
# Check if running
docker-compose ps

# Check port conflicts
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Restart all services
docker-compose down && docker-compose up -d
```

### Database issues
```bash
# Reset database
docker-compose down
docker volume rm event-driven-order-system_postgres_data
docker-compose up -d
```

### Tests failing
```bash
# Make sure system is running first
docker-compose up -d

# Wait 5 seconds for services
sleep 5

# Run tests
docker-compose exec order-service pytest tests/test_integration.py -v -s
```

## 📊 Order Status Flow

```
PENDING  ──→  PROCESSING  ──→  COMPLETED
   │
   └─→ CANCELLED (future)
```

## 🎯 Event Flow

```
POST /orders
    ↓
OrderCreated Event Published
    ├─→ Order Processor (updates status to PROCESSING)
    │       ↓
    │   OrderProcessed Event Published
    │       ↓
    │   Notification Service (logs notification)
    │
    └─→ Inventory Service (logs reservation)
```

## ✅ Verification Checklist

- [ ] Services are running: `docker-compose ps`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] RabbitMQ accessible: `curl http://localhost:15672`
- [ ] Database accessible: `docker-compose exec db psql -U orderuser -d order_db`
- [ ] Can create order: POST /orders
- [ ] Order status updates: GET /orders/{id}
- [ ] Notifications appear: `docker-compose logs notification-service`
- [ ] Tests pass: `docker-compose exec order-service pytest tests/ -v`

## 💡 Tips

1. **Keep logs running**: `docker-compose logs -f` in separate terminal
2. **Use helper scripts**: `./scripts.sh help` for all commands
3. **Check RabbitMQ UI**: See queues and messages visually
4. **Review docs**: Each has specific information
5. **Run tests first**: Ensures everything works

## 🚀 Production Ready

✅ All core requirements met  
✅ Comprehensive documentation  
✅ Full test coverage  
✅ Error handling & resilience  
✅ Docker containerization  
✅ Health checks  
✅ Idempotent processing  
✅ Scalable architecture  

---

**Ready?** Start with: `docker-compose up -d`

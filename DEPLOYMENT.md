# Deployment Guide

## Pre-Deployment Checklist

- [ ] Docker and Docker Compose installed (v20.10+)
- [ ] Git installed
- [ ] 8GB+ RAM available
- [ ] Ports 5432, 5672, 8000-8003 available
- [ ] Clone repository and navigate to project root

## Local Development Deployment

### 1. Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd event-driven-order-system

# Copy environment file
cp .env.example .env

# (Optional) Customize .env for your environment
# But defaults work fine for local development
```

### 2. Start Services

```bash
# Using docker-compose
docker-compose up -d

# Or using helper script
./scripts.sh start              # macOS/Linux
scripts.bat start              # Windows
```

### 3. Wait for Service Readiness

```bash
# Check status (wait until all are healthy)
docker-compose ps

# Or use helper script
./scripts.sh health-check      # macOS/Linux
scripts.bat health_check       # Windows

# Check specific service logs
docker-compose logs order-service
```

### 4. Verify Installation

```bash
# Test API
curl http://localhost:8000/health

# Access RabbitMQ Management UI
# Open browser: http://localhost:15672
# Credentials: guest/guest

# View logs
docker-compose logs -f
```

## Testing Deployment

### Unit Tests

```bash
# All unit tests
docker-compose exec order-service pytest tests/test_order_service.py -v
docker-compose exec order-processor pytest tests/test_order_processor.py -v

# Or using helper script
./scripts.sh test-unit         # macOS/Linux
scripts.bat test_unit          # Windows
```

### Integration Tests

```bash
# Run end-to-end tests
docker-compose exec order-service pytest tests/test_integration.py -v -s

# Or using helper script
./scripts.sh test-integration  # macOS/Linux
scripts.bat test_integration   # Windows
```

### Manual Testing

```bash
# Create an order
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST001",
    "items": [{"product_id": "P001", "quantity": 2}]
  }'

# Response will include order_id, e.g., ORD-ABC123DEF456

# Wait 3 seconds for processing, then retrieve status
curl http://localhost:8000/orders/ORD-ABC123DEF456

# Expected status: PROCESSING (updated by Order Processor)
```

## Production Deployment

### 1. Pre-Production Environment Setup

```bash
# Update environment variables for production
nano .env
# Or
vim .env

# Key changes:
# - DATABASE_PASSWORD: Use strong password
# - RABBITMQ_PASSWORD: Use strong password
# - SERVICE_* ports: Adjust if needed
```

### 2. Database Preparation

```bash
# Ensure database backups are configured
# Update backup strategy in .env if needed

# Test database connectivity
docker-compose exec db psql -U orderuser -d order_db -c "SELECT 1"
```

### 3. SSL/TLS Configuration

```bash
# Generate self-signed certificates (for testing)
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes

# Update docker-compose.yml with TLS configuration
# Add volumes and environment variables for certificate paths
```

### 4. Security Hardening

```bash
# Update docker-compose.yml with security configurations
# - Add network policies
# - Use health checks (already included)
# - Enable restart policies (already included)
# - Use environment variable secrets
```

### 5. Monitoring Setup

```bash
# Add Prometheus exporter containers to docker-compose.yml
# Configure log aggregation (ELK stack, etc.)
# Set up alerting

# For now, monitor via logs
docker-compose logs -f | grep -E "ERROR|WARNING"
```

### 6. Deployment Commands

```bash
# Build production images
docker-compose -f docker-compose.yml build --no-cache

# Start with production environment
docker-compose -f docker-compose.yml up -d

# Verify all services are healthy
docker-compose ps
for service in db rabbitmq order-service order-processor notification-service inventory-service; do
  docker-compose exec $service echo "Health check: $service"
done
```

## Kubernetes Deployment (Future)

### Convert to Kubernetes

```bash
# Install Kompose tool
curl -L https://github.com/kubernetes/kompose/releases/download/v1.28.0/kompose-linux-amd64 -o kompose
chmod +x kompose

# Generate Kubernetes manifests
./kompose convert -f docker-compose.yml -o k8s/

# Create namespace
kubectl create namespace order-system

# Deploy to Kubernetes
kubectl apply -f k8s/ -n order-system

# Monitor deployment
kubectl get pods -n order-system
kubectl logs -f deployment/order-service -n order-system
```

## Scaling Deployment

### Horizontal Scaling (Multiple Instances)

```bash
# Update docker-compose.yml to scale services
docker-compose up -d --scale order-service=3 --scale order-processor=3

# Or update service replicas in docker-compose.yml:
services:
  order-service:
    deploy:
      replicas: 3
  order-processor:
    deploy:
      replicas: 3
```

### Load Balancing

```bash
# Add Nginx or HAProxy service to docker-compose.yml
# Configure upstream servers
# Update API clients to use load balancer

# For testing:
docker-compose up -d --scale order-service=3
# Requests will be distributed automatically
```

## Maintenance & Operations

### Regular Tasks

```bash
# Daily health check
curl http://localhost:8000/health

# Weekly log rotation
docker-compose exec db psql -U orderuser -d order_db -c "SELECT COUNT(*) FROM orders"

# Monthly backups
docker-compose exec db pg_dump -U orderuser order_db > backup-$(date +%Y%m%d).sql

# Quarterly security updates
docker-compose pull
docker-compose up -d
```

### Troubleshooting

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs service-name

# Execute commands in container
docker-compose exec order-service bash
docker-compose exec db psql -U orderuser -d order_db

# Restart failed service
docker-compose restart order-processor

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

## Environment Variables Reference

```env
# Database Configuration
DATABASE_HOST=db
DATABASE_PORT=5432
DATABASE_NAME=order_db
DATABASE_USER=orderuser
DATABASE_PASSWORD=orderpass

# RabbitMQ Configuration
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# Service Ports
ORDER_SERVICE_PORT=8000
ORDER_PROCESSOR_PORT=8001
NOTIFICATION_SERVICE_PORT=8002
INVENTORY_SERVICE_PORT=8003

# Message Queue Configuration
EXCHANGE_NAME=order_exchange
ORDER_CREATED_QUEUE=order.created
ORDER_PROCESSED_QUEUE=order.processed
DEAD_LETTER_QUEUE=dead_letter_queue
MAX_RETRIES=3
RETRY_DELAY_SECONDS=5
```

## Disaster Recovery

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U orderuser order_db > backup.sql

# Restore from backup
docker-compose exec db psql -U orderuser order_db < backup.sql
```

### Service Recovery

```bash
# If a service crashes
docker-compose restart <service-name>

# If multiple services fail
docker-compose down
docker-compose up -d

# If database is corrupted
docker-compose down
docker volume rm event-driven-order-system_postgres_data
docker-compose up -d
# Recreates database with init.sql
```

## Performance Tuning

### Database Optimization

```sql
-- Run inside database container
-- Add indexes if needed
CREATE INDEX idx_orders_customer_created ON orders(customer_id, created_at);

-- Check query performance
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 'CUST001';

-- Vacuum and analyze
VACUUM ANALYZE;
```

### RabbitMQ Optimization

```bash
# Increase memory limits
# Update docker-compose.yml:
environment:
  RABBITMQ_MEMORY_HIGH_WATERMARK: 0.6

# Increase channel prefetch
# In consumer code, adjust:
channel.basic_qos(prefetch_count=10)  # Instead of 1
```

### Application Optimization

```bash
# Increase uvicorn workers
# Update Dockerfile or docker-compose.yml:
CMD ["python", "-m", "uvicorn", "src.main:app", "--workers", "4"]

# Increase database connection pool
# Update config.py:
connection_pool = SimpleConnectionPool(5, 50)  # Instead of 1, 20
```

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f order-service

# Last 100 lines
docker-compose logs --tail=100 order-service

# Since specific time
docker-compose logs --since 2024-01-22T10:00:00 order-service
```

### Metrics Collection

```bash
# Install Prometheus and Grafana (future enhancement)
# Add metrics collection to each service
# Create dashboards for visualization

# For now, manually track:
# - Request count via logs
# - Error rate via logs
# - Message queue depth via RabbitMQ UI
```

### Alert Configuration

```bash
# Example alert rules (for future Prometheus integration)
- alert: OrderServiceDown
  expr: up{job="order-service"} == 0
  
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  
- alert: HighQueueDepth
  expr: rabbitmq_queue_messages_ready > 1000
```

## Rollback Procedure

```bash
# If new deployment causes issues

# Stop current deployment
docker-compose down

# Revert to previous version
git checkout previous-version-tag

# Rebuild with previous code
docker-compose build --no-cache

# Restart services
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

## Post-Deployment Verification

- [ ] All services show as "healthy" in `docker-compose ps`
- [ ] API health check returns 200: `curl http://localhost:8000/health`
- [ ] Can create order: `curl -X POST http://localhost:8000/orders ...`
- [ ] Order status updates after 3 seconds
- [ ] Notification logs appear in container logs
- [ ] Inventory logs appear in container logs
- [ ] RabbitMQ management UI accessible at :15672
- [ ] Database contains seeded products
- [ ] All unit tests pass
- [ ] Integration tests pass

---

**Deployment Support**: If issues occur, refer to the README.md and check docker-compose logs for detailed error messages.

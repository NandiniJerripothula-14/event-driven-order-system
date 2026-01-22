#!/bin/bash
# Event-Driven Order System - Helper Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Commands
start() {
    print_header "Starting Event-Driven Order System"
    docker-compose up -d
    print_success "System started. Waiting for services to be ready..."
    sleep 5
    health_check
}

stop() {
    print_header "Stopping Event-Driven Order System"
    docker-compose down
    print_success "System stopped"
}

restart() {
    print_header "Restarting Event-Driven Order System"
    docker-compose restart
    print_success "System restarted"
}

health_check() {
    print_header "Health Check"
    
    for service in db rabbitmq order-service; do
        if docker-compose ps | grep -q "$service"; then
            if [ "$service" = "order-service" ]; then
                if curl -s http://localhost:8000/health > /dev/null; then
                    print_success "$service is healthy"
                else
                    print_error "$service is unhealthy"
                fi
            else
                print_success "$service is running"
            fi
        else
            print_error "$service is not running"
        fi
    done
}

logs_order_service() {
    print_header "Order Service Logs"
    docker-compose logs -f order-service
}

logs_order_processor() {
    print_header "Order Processor Service Logs"
    docker-compose logs -f order-processor
}

logs_notification() {
    print_header "Notification Service Logs"
    docker-compose logs -f notification-service
}

logs_inventory() {
    print_header "Inventory Service Logs"
    docker-compose logs -f inventory-service
}

logs_all() {
    print_header "All Services Logs"
    docker-compose logs -f
}

test_unit() {
    print_header "Running Unit Tests"
    
    print_info "Testing Order Service..."
    docker-compose exec order-service pytest tests/test_order_service.py -v
    
    print_info "Testing Order Processor..."
    docker-compose exec order-processor pytest tests/test_order_processor.py -v
    
    print_info "Testing Notification Service..."
    docker-compose exec notification-service pytest tests/test_notification_consumer.py -v
    
    print_info "Testing Inventory Service..."
    docker-compose exec inventory-service pytest tests/test_inventory_consumer.py -v
    
    print_success "All unit tests completed"
}

test_integration() {
    print_header "Running Integration Tests"
    print_info "Make sure system is running: ./scripts.sh start"
    sleep 2
    docker-compose exec order-service pytest tests/test_integration.py -v -s
    print_success "Integration tests completed"
}

create_order() {
    print_header "Creating Test Order"
    
    response=$(curl -s -X POST http://localhost:8000/orders \
      -H "Content-Type: application/json" \
      -d '{
        "customer_id": "CUST-TEST-'$(date +%s)'",
        "items": [
          {"product_id": "P001", "quantity": 2},
          {"product_id": "P003", "quantity": 1}
        ]
      }')
    
    echo "$response" | python -m json.tool
    
    order_id=$(echo "$response" | grep -o '"order_id":"[^"]*"' | cut -d'"' -f4)
    print_success "Order created with ID: $order_id"
    print_info "Retrieve status in 3 seconds with: curl http://localhost:8000/orders/$order_id"
}

get_order() {
    if [ -z "$1" ]; then
        print_error "Usage: ./scripts.sh get_order <order_id>"
        exit 1
    fi
    
    print_header "Retrieving Order: $1"
    curl -s http://localhost:8000/orders/$1 | python -m json.tool
}

list_orders() {
    print_header "Listing All Orders"
    curl -s http://localhost:8000/orders | python -m json.tool
}

reset_db() {
    print_header "Resetting Database"
    print_info "Stopping system..."
    docker-compose down
    print_info "Removing database volume..."
    docker volume rm event-driven-order-system_postgres_data 2>/dev/null || true
    print_success "Database reset. Start system with: ./scripts.sh start"
}

shell_order_service() {
    print_header "Opening Shell in Order Service"
    docker-compose exec order-service /bin/bash
}

shell_order_processor() {
    print_header "Opening Shell in Order Processor"
    docker-compose exec order-processor /bin/bash
}

shell_db() {
    print_header "Opening PostgreSQL Shell"
    docker-compose exec db psql -U orderuser -d order_db
}

open_rabbitmq_ui() {
    print_header "Opening RabbitMQ Management UI"
    if command -v xdg-open > /dev/null; then
        xdg-open http://localhost:15672
    elif command -v open > /dev/null; then
        open http://localhost:15672
    else
        print_info "RabbitMQ UI available at: http://localhost:15672"
        print_info "Default credentials: guest / guest"
    fi
}

build() {
    print_header "Building Docker Images"
    docker-compose build
    print_success "Build completed"
}

clean() {
    print_header "Cleaning Up"
    docker-compose down
    docker volume prune -f
    print_success "Cleanup completed"
}

help() {
    cat << EOF
Event-Driven Order System - Helper Script

Usage: ./scripts.sh [COMMAND]

Commands:
    start               Start the entire system
    stop                Stop the entire system
    restart             Restart the entire system
    health_check        Check health of all services
    
    logs-order          View Order Service logs
    logs-processor      View Order Processor logs
    logs-notification   View Notification Service logs
    logs-inventory      View Inventory Service logs
    logs-all            View all services logs
    
    test-unit           Run all unit tests
    test-integration    Run integration tests
    
    create-order        Create a test order
    get-order <id>      Retrieve a specific order
    list-orders         List all orders
    
    shell-order         Open shell in Order Service
    shell-processor     Open shell in Order Processor
    shell-db            Open PostgreSQL shell
    
    reset-db            Reset database (removes all data)
    build               Build all Docker images
    clean               Clean up all containers and volumes
    
    rabbitmq-ui         Open RabbitMQ Management UI
    help                Show this help message

Examples:
    ./scripts.sh start
    ./scripts.sh test-unit
    ./scripts.sh create-order
    ./scripts.sh get-order ORD-ABC123DEF456
    ./scripts.sh logs-all
EOF
}

# Main
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    health-check|health_check)
        health_check
        ;;
    logs-order|logs_order)
        logs_order_service
        ;;
    logs-processor|logs_processor)
        logs_order_processor
        ;;
    logs-notification|logs_notification)
        logs_notification
        ;;
    logs-inventory|logs_inventory)
        logs_inventory
        ;;
    logs-all|logs_all)
        logs_all
        ;;
    test-unit|test_unit)
        test_unit
        ;;
    test-integration|test_integration)
        test_integration
        ;;
    create-order|create_order)
        create_order
        ;;
    get-order|get_order)
        get_order "$2"
        ;;
    list-orders|list_orders)
        list_orders
        ;;
    reset-db|reset_db)
        reset_db
        ;;
    shell-order|shell_order)
        shell_order_service
        ;;
    shell-processor|shell_processor)
        shell_order_processor
        ;;
    shell-db|shell_db)
        shell_db
        ;;
    rabbitmq-ui|rabbitmq_ui)
        open_rabbitmq_ui
        ;;
    build)
        build
        ;;
    clean)
        clean
        ;;
    help)
        help
        ;;
    *)
        print_error "Unknown command: $1"
        help
        exit 1
        ;;
esac

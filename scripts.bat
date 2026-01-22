@echo off
REM Event-Driven Order System - Helper Script for Windows

setlocal enabledelayedexpansion

set COMMAND=%1

if "%COMMAND%"=="" (
    call :show_help
    exit /b 0
)

goto :%COMMAND%
goto :show_help

:start
echo ========================================
echo Starting Event-Driven Order System
echo ========================================
docker-compose up -d
echo.
echo System started. Waiting for services...
timeout /t 5 /nobreak
call :health_check
exit /b 0

:stop
echo ========================================
echo Stopping Event-Driven Order System
echo ========================================
docker-compose down
echo System stopped
exit /b 0

:restart
echo ========================================
echo Restarting Event-Driven Order System
echo ========================================
docker-compose restart
echo System restarted
exit /b 0

:health_check
echo ========================================
echo Health Check
echo ========================================
echo Checking services...
docker-compose ps
exit /b 0

:logs_all
echo ========================================
echo All Services Logs
echo ========================================
docker-compose logs -f
exit /b 0

:logs_order
echo ========================================
echo Order Service Logs
echo ========================================
docker-compose logs -f order-service
exit /b 0

:logs_processor
echo ========================================
echo Order Processor Service Logs
echo ========================================
docker-compose logs -f order-processor
exit /b 0

:logs_notification
echo ========================================
echo Notification Service Logs
echo ========================================
docker-compose logs -f notification-service
exit /b 0

:logs_inventory
echo ========================================
echo Inventory Service Logs
echo ========================================
docker-compose logs -f inventory-service
exit /b 0

:test_unit
echo ========================================
echo Running Unit Tests
echo ========================================
echo Testing Order Service...
docker-compose exec order-service pytest tests/test_order_service.py -v
echo.
echo Testing Order Processor...
docker-compose exec order-processor pytest tests/test_order_processor.py -v
echo.
echo Testing Notification Service...
docker-compose exec notification-service pytest tests/test_notification_consumer.py -v
echo.
echo Testing Inventory Service...
docker-compose exec inventory-service pytest tests/test_inventory_consumer.py -v
echo All unit tests completed
exit /b 0

:test_integration
echo ========================================
echo Running Integration Tests
echo ========================================
echo Make sure system is running with: scripts.bat start
timeout /t 2 /nobreak
docker-compose exec order-service pytest tests/test_integration.py -v -s
echo Integration tests completed
exit /b 0

:create_order
echo ========================================
echo Creating Test Order
echo ========================================
setlocal enabledelayedexpansion
for /f "tokens=1-5 delims=/ " %%d in ('date /t') do set datestamp=%%h%%i%%j%%k%%l

curl -X POST http://localhost:8000/orders ^
  -H "Content-Type: application/json" ^
  -d "{\"customer_id\": \"CUST-TEST-!datestamp!\", \"items\": [{\"product_id\": \"P001\", \"quantity\": 2}, {\"product_id\": \"P003\", \"quantity\": 1}]}"

echo.
echo Order created. Check status in 3 seconds using: scripts.bat get_order ORDER_ID
exit /b 0

:get_order
if "%2"=="" (
    echo Usage: scripts.bat get_order ORDER_ID
    exit /b 1
)
echo ========================================
echo Retrieving Order: %2
echo ========================================
curl -s http://localhost:8000/orders/%2
echo.
exit /b 0

:list_orders
echo ========================================
echo Listing All Orders
echo ========================================
curl -s http://localhost:8000/orders
echo.
exit /b 0

:reset_db
echo ========================================
echo Resetting Database
echo ========================================
echo Stopping system...
docker-compose down
echo Removing database volume...
docker volume rm event-driven-order-system_postgres_data 2>nul
echo Database reset. Start system with: scripts.bat start
exit /b 0

:shell_order
echo ========================================
echo Opening Shell in Order Service
echo ========================================
docker-compose exec order-service /bin/bash
exit /b 0

:shell_processor
echo ========================================
echo Opening Shell in Order Processor
echo ========================================
docker-compose exec order-processor /bin/bash
exit /b 0

:shell_db
echo ========================================
echo Opening PostgreSQL Shell
echo ========================================
docker-compose exec db psql -U orderuser -d order_db
exit /b 0

:rabbitmq_ui
echo ========================================
echo Opening RabbitMQ Management UI
echo ========================================
echo RabbitMQ UI available at: http://localhost:15672
echo Default credentials: guest / guest
start http://localhost:15672
exit /b 0

:build
echo ========================================
echo Building Docker Images
echo ========================================
docker-compose build
echo Build completed
exit /b 0

:clean
echo ========================================
echo Cleaning Up
echo ========================================
docker-compose down
docker volume prune -f
echo Cleanup completed
exit /b 0

:show_help
echo Event-Driven Order System - Helper Script for Windows
echo.
echo Usage: scripts.bat [COMMAND]
echo.
echo Commands:
echo   start               Start the entire system
echo   stop                Stop the entire system
echo   restart             Restart the entire system
echo   health_check        Check health of all services
echo.
echo   logs_all            View all services logs
echo   logs_order          View Order Service logs
echo   logs_processor      View Order Processor logs
echo   logs_notification   View Notification Service logs
echo   logs_inventory      View Inventory Service logs
echo.
echo   test_unit           Run all unit tests
echo   test_integration    Run integration tests
echo.
echo   create_order        Create a test order
echo   get_order ORDER_ID  Retrieve a specific order
echo   list_orders         List all orders
echo.
echo   shell_order         Open shell in Order Service
echo   shell_processor     Open shell in Order Processor
echo   shell_db            Open PostgreSQL shell
echo.
echo   reset_db            Reset database (removes all data)
echo   build               Build all Docker images
echo   clean               Clean up all containers and volumes
echo.
echo   rabbitmq_ui         Open RabbitMQ Management UI
echo.
echo Examples:
echo   scripts.bat start
echo   scripts.bat test_unit
echo   scripts.bat create_order
echo   scripts.bat get_order ORD-ABC123
echo   scripts.bat logs_all
exit /b 0

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import logging
import sys
from .config import Config
from .db import Database
from .events.event_publisher import EventPublisher
from .routes import orders

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Order Service",
    description="Microservice for order management with event-driven architecture",
    version="1.0.0"
)

# Include routers
app.include_router(orders.router)

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("Starting Order Service...")
    try:
        # Test database connection
        Database.get_pool()
        logger.info("Database connection pool initialized")
        
        # Test RabbitMQ connection
        EventPublisher.connect()
        logger.info("RabbitMQ connection established")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    logger.info("Shutting down Order Service...")
    Database.close_all()
    EventPublisher.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        Database.execute_query("SELECT 1")
        # Check RabbitMQ
        EventPublisher.get_channel()
        return JSONResponse(status_code=200, content={"status": "healthy"})
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=503, content={"status": "unhealthy"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.SERVICE_HOST,
        port=Config.SERVICE_PORT
    )

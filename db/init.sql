-- Create ENUM type for order status
CREATE TYPE order_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED');

-- Create products table
CREATE TABLE products (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    available_stock INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE orders (
    id VARCHAR(255) PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    items JSONB NOT NULL,
    status order_status DEFAULT 'PENDING',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create processed events tracking table (for idempotency)
CREATE TABLE processed_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_processed_events_order_id ON processed_events(order_id);
CREATE INDEX idx_processed_events_event_id ON processed_events(event_id);

-- Insert sample products for testing
INSERT INTO products (id, name, price, available_stock) VALUES
('P001', 'Smartphone X', 799.99, 100),
('P002', 'Laptop Pro', 1200.00, 50),
('P003', 'Wireless Headphones', 199.99, 200),
('P004', 'USB-C Cable', 25.00, 500);

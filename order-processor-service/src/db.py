import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import logging
from .config import Config

logger = logging.getLogger(__name__)

class Database:
    """PostgreSQL Database connection manager"""
    
    _pool = None

    @classmethod
    def get_pool(cls):
        """Get or create connection pool"""
        if cls._pool is None:
            try:
                cls._pool = SimpleConnectionPool(
                    1, 20,
                    host=Config.DATABASE_HOST,
                    port=Config.DATABASE_PORT,
                    database=Config.DATABASE_NAME,
                    user=Config.DATABASE_USER,
                    password=Config.DATABASE_PASSWORD
                )
                logger.info("Database pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create database pool: {e}")
                raise
        return cls._pool

    @classmethod
    def get_connection(cls):
        """Get connection from pool"""
        pool = cls.get_pool()
        return pool.getconn()

    @classmethod
    def release_connection(cls, conn):
        """Release connection back to pool"""
        if conn and cls._pool:
            cls._pool.putconn(conn)

    @classmethod
    def close_all(cls):
        """Close all connections in pool"""
        if cls._pool:
            cls._pool.closeall()
            cls._pool = None
            logger.info("All database connections closed")

    @staticmethod
    def execute_query(query, params=None):
        """Execute a query and return results"""
        conn = Database.get_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())
            conn.commit()
            result = cur.fetchall()
            cur.close()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            Database.release_connection(conn)

    @staticmethod
    def execute_query_single(query, params=None):
        """Execute a query and return a single result"""
        conn = Database.get_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())
            conn.commit()
            result = cur.fetchone()
            cur.close()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            Database.release_connection(conn)

    @staticmethod
    def execute_update(query, params=None):
        """Execute an update query"""
        conn = Database.get_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())
            conn.commit()
            result = cur.fetchone() if cur.description else None
            cur.close()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"Update execution failed: {e}")
            raise
        finally:
            Database.release_connection(conn)

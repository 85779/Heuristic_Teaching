"""
MongoDB connection manager.

Manages MongoDB database connections and provides connection pooling.
"""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """
    MongoDB connection manager for async operations.

    Provides a singleton-like interface for database connections
    with connection pooling and automatic reconnection handling.
    """

    def __init__(self):
        """Initialize the MongoDB connection manager."""
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None

    async def connect(
        self,
        connection_string: Optional[str] = None,
        database_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Establish connection to MongoDB.

        Args:
            connection_string: MongoDB connection URI (defaults to settings.MONGODB_URI)
            database_name: Database name to use (defaults to settings.MONGODB_DB_NAME)
            **kwargs: Additional connection options (maxPoolSize, minPoolSize, etc.)
        """
        if self._client is not None:
            logger.warning("MongoDB client already connected, skipping connect")
            return

        uri = connection_string or settings.MONGODB_URI
        db_name = database_name or settings.MONGODB_DB_NAME

        # Set connection pool options with defaults
        connection_options = {
            "maxPoolSize": kwargs.pop("maxPoolSize", 100),
            "minPoolSize": kwargs.pop("minPoolSize", 10),
        }
        # Merge any additional kwargs
        connection_options.update(kwargs)

        try:
            self._client = AsyncIOMotorClient(uri, **connection_options)
            self._database = self._client[db_name]
            logger.info(f"MongoDB connected to {db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._database = None
            raise

    async def disconnect(self) -> None:
        """
        Close MongoDB connection.
        """
        if self._client is not None:
            try:
                self._client.close()
                logger.info("MongoDB disconnected")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
            finally:
                self._client = None
                self._database = None

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """
        Get the database instance.

        Returns:
            AsyncIOMotorDatabase: The database instance
        """
        if self._database is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self._database

    @property
    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._client is not None

    async def health_check(self) -> bool:
        """
        Verify database connection is healthy.

        Returns:
            bool: True if healthy, False otherwise
        """
        if self._client is None or self._database is None:
            return False
        try:
            await self._database.command("ping")
            return True
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            return False


# Singleton instance
_mongodb_instance: Optional[MongoDBConnection] = None


def get_mongodb() -> MongoDBConnection:
    """
    Get the singleton MongoDB connection instance.

    Returns:
        MongoDBConnection: The MongoDB connection instance
    """
    global _mongodb_instance
    if _mongodb_instance is None:
        _mongodb_instance = MongoDBConnection()
    return _mongodb_instance
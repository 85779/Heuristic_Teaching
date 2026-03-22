"""
Base repository implementation.

Provides the foundation for all repository classes with common CRUD operations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime
from bson.objectid import ObjectId as BsonObjectId

ObjectId = BsonObjectId  # Alias for convenience

ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository providing common CRUD operations.

    All repository implementations should inherit from this base class
    and implement the abstract methods as needed.
    """

    def __init__(self, collection_name: str):
        """
        Initialize the repository.

        Args:
            collection_name: Name of the MongoDB collection
        """
        self._collection_name = collection_name
        self._collection = None

    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Create a new document in the collection.

        Args:
            data: Dictionary containing document data

        Returns:
            ModelType: The created document

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Create operation not yet implemented")

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[ModelType]:
        """
        Find a document by its ID.

        Args:
            id: Document ID (string representation of ObjectId)

        Returns:
            Optional[ModelType]: The document if found, None otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Find by ID not yet implemented")

    @abstractmethod
    async def find_one(self, filter: Dict[str, Any]) -> Optional[ModelType]:
        """
        Find a single document matching the filter criteria.

        Args:
            filter: MongoDB filter query

        Returns:
            Optional[ModelType]: The document if found, None otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Find one not yet implemented")

    @abstractmethod
    async def find_many(
        self,
        filter: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Find multiple documents matching the filter criteria.

        Args:
            filter: MongoDB filter query (default: None = all documents)
            skip: Number of documents to skip (pagination)
            limit: Maximum number of documents to return

        Returns:
            List[ModelType]: List of matching documents

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Find many not yet implemented")

    @abstractmethod
    async def update(
        self,
        id: str,
        data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Update a document by its ID.

        Args:
            id: Document ID
            data: Updated data dictionary

        Returns:
            Optional[ModelType]: The updated document if found, None otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Update operation not yet implemented")

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a document by its ID.

        Args:
            id: Document ID

        Returns:
            bool: True if deleted, False if not found

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Delete operation not yet implemented")

    @abstractmethod
    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter criteria.

        Args:
            filter: MongoDB filter query (default: None = count all)

        Returns:
            int: Number of matching documents

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Count operation not yet implemented")

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """
        Check if a document exists.

        Args:
            id: Document ID

        Returns:
            bool: True if exists, False otherwise

        Raises:
            NotImplementedError: Method not yet implemented
        """
        raise NotImplementedError("Exists check not yet implemented")

    def _object_id(self, id: str) -> ObjectId:
        """
        Convert string ID to ObjectId.

        Args:
            id: String ID

        Returns:
            ObjectId: The ObjectId

        Raises:
            ValueError: If the ID is not a valid ObjectId
        """
        try:
            return ObjectId(id)
        except Exception as e:
            raise ValueError(f"Invalid ObjectId: {id}") from e

    def _serialize_datetime(self, dt: datetime) -> str:
        """
        Serialize datetime to ISO format string.

        Args:
            dt: DateTime object

        Returns:
            str: ISO format string
        """
        return dt.isoformat()
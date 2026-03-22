"""Repository interface - Base class for data access."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from ..context import ModuleContext

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Repository base interface.

    Provides data access abstraction for MongoDB collections.
    Generic type T represents the model type.
    """

    @property
    @abstractmethod
    def collection_name(self) -> str:
        """Name of the MongoDB collection.

        Returns:
            str: Collection name
        """
        raise NotImplementedError

    @abstractmethod
    async def initialize(self, context: "ModuleContext") -> None:
        """Initialize the repository.

        Called during application startup to set up indexes and
        prepare the collection.

        Args:
            context: Module execution context
        """
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: dict[str, Any] | T) -> str:
        """Create a new document.

        Args:
            data: Document data to create (dict or model instance)

        Returns:
            str: ID of the created document
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, document_id: str) -> T | None:
        """Get a document by its ID.

        Args:
            document_id: Document ID

        Returns:
            T | None: Document instance or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        document_id: str,
        data: dict[str, Any],
        upsert: bool = False,
    ) -> bool:
        """Update a document.

        Args:
            document_id: Document ID to update
            data: Data to update
            upsert: If True, create document if it doesn't exist

        Returns:
            bool: True if update was successful
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document.

        Args:
            document_id: Document ID to delete

        Returns:
            bool: True if deletion was successful
        """
        raise NotImplementedError

    @abstractmethod
    async def find(
        self,
        filter: dict[str, Any] | None = None,
        limit: int = 100,
        skip: int = 0,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[T]:
        """Find documents matching criteria.

        Args:
            filter: Query filter criteria
            limit: Maximum number of results
            skip: Number of results to skip
            sort: Sort specification (field, direction) tuples

        Returns:
            list[T]: List of matching documents
        """
        raise NotImplementedError

    @abstractmethod
    async def find_one(self, filter: dict[str, Any]) -> T | None:
        """Find a single document matching criteria.

        Args:
            filter: Query filter criteria

        Returns:
            T | None: Document instance or None if not found
        """
        raise NotImplementedError
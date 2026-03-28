"""
Intervention repository implementation.

Manages intervention data storage and retrieval using MongoDB.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.infrastructure.database.mongodb import get_mongodb

logger = logging.getLogger(__name__)


class InterventionRepository:
    """
    Repository for managing interventions and intervention contexts.

    Handles two collections:
    - intervention_contexts: stores InterventionContext per session
    - interventions: stores completed Intervention objects
    """

    def __init__(self):
        """Initialize the intervention repository."""
        self._contexts_collection_name = "intervention_contexts"
        self._interventions_collection_name = "interventions"

    def _get_contexts_collection(self):
        """Get the intervention_contexts collection."""
        mongodb = get_mongodb()
        return mongodb.database[self._contexts_collection_name]

    def _get_interventions_collection(self):
        """Get the interventions collection."""
        mongodb = get_mongodb()
        return mongodb.database[self._interventions_collection_name]

    def _serialize_doc(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Serialize a document, removing MongoDB _id.

        Args:
            doc: Document to serialize

        Returns:
            Optional[Dict[str, Any]]: Serialized document, or None
        """
        if doc is None:
            return None
        result = dict(doc)
        if "_id" in result:
            result.pop("_id")
        return result

    def _serialize_docs(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Serialize multiple documents.

        Args:
            docs: List of documents to serialize

        Returns:
            List[Dict[str, Any]]: List of serialized documents
        """
        results = []
        for doc in docs:
            if doc is not None:
                serialized = self._serialize_doc(doc)
                if serialized is not None:
                    results.append(serialized)
        return results

    async def create(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new intervention context.

        Args:
            data: Intervention context data

        Returns:
            Optional[Dict[str, Any]]: The created document, or None on failure
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping create")
                return None

            collection = self._get_contexts_collection()
            if data is None:
                data = {}
            result = await collection.insert_one(data)
            doc = await collection.find_one({"_id": result.inserted_id})
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to create intervention context: {e}")
            return None

    async def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Find an intervention context by ID.

        Args:
            id: Document ID

        Returns:
            Optional[Dict[str, Any]]: The document if found, None otherwise
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping find_by_id")
                return None

            from bson.objectid import ObjectId
            collection = self._get_contexts_collection()
            doc = await collection.find_one({"_id": ObjectId(id)})
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to find intervention context by id: {e}")
            return None

    async def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document matching the filter.

        Args:
            filter: MongoDB filter query

        Returns:
            Optional[Dict[str, Any]]: The document if found, None otherwise
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping find_one")
                return None

            collection = self._get_contexts_collection()
            doc = await collection.find_one(filter)
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to find one intervention context: {e}")
            return None

    async def find_many(
        self,
        filter: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents matching the filter.

        Args:
            filter: MongoDB filter query
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            List[Dict[str, Any]]: List of matching documents
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping find_many")
                return []

            collection = self._get_contexts_collection()
            if filter is None:
                filter = {}
            cursor = collection.find(filter).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            return self._serialize_docs(docs)
        except Exception as e:
            logger.warning(f"Failed to find many intervention contexts: {e}")
            return []

    async def update(
        self,
        id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a document by its ID.

        Args:
            id: Document ID
            data: Updated data dictionary

        Returns:
            Optional[Dict[str, Any]]: The updated document if found, None otherwise
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping update")
                return None

            from bson.objectid import ObjectId
            collection = self._get_contexts_collection()
            await collection.update_one(
                {"_id": ObjectId(id)},
                {"$set": data}
            )
            doc = await collection.find_one({"_id": ObjectId(id)})
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to update intervention context: {e}")
            return None

    async def delete(self, id: str) -> bool:
        """
        Delete a document by its ID.

        Args:
            id: Document ID

        Returns:
            bool: True if deleted, False if not found
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping delete")
                return False

            from bson.objectid import ObjectId
            collection = self._get_contexts_collection()
            result = await collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.warning(f"Failed to delete intervention context: {e}")
            return False

    async def count(self, filter: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter.

        Args:
            filter: MongoDB filter query

        Returns:
            int: Number of matching documents
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping count")
                return 0

            collection = self._get_contexts_collection()
            if filter is None:
                filter = {}
            return await collection.count_documents(filter)
        except Exception as e:
            logger.warning(f"Failed to count intervention contexts: {e}")
            return 0

    async def exists(self, id: str) -> bool:
        """
        Check if a document exists.

        Args:
            id: Document ID

        Returns:
            bool: True if exists, False otherwise
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping exists check")
                return False

            from bson.objectid import ObjectId
            collection = self._get_contexts_collection()
            count = await collection.count_documents({"_id": ObjectId(id)})
            return count > 0
        except Exception as e:
            logger.warning(f"Failed to check intervention context exists: {e}")
            return False

    async def find_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Find all intervention context documents for a session.

        Args:
            session_id: Session identifier

        Returns:
            List[Dict[str, Any]]: List of intervention contexts for the session
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping find_by_session")
                return []

            collection = self._get_contexts_collection()
            cursor = collection.find({"session_id": session_id})
            docs = await cursor.to_list(length=1000)
            return self._serialize_docs(docs)
        except Exception as e:
            logger.warning(f"Failed to find intervention contexts by session: {e}")
            return []

    async def upsert_context(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update or insert an intervention context for a session.

        Args:
            session_id: Session identifier
            data: Intervention context data

        Returns:
            Optional[Dict[str, Any]]: The upserted document, or None on failure
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping upsert_context")
                return None

            collection = self._get_contexts_collection()
            if "updated_at" not in data:
                data["updated_at"] = datetime.utcnow()
            await collection.update_one(
                {"session_id": session_id},
                {"$set": data},
                upsert=True
            )
            doc = await collection.find_one({"session_id": session_id})
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to upsert intervention context: {e}")
            return None

    async def get_latest_context(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest intervention context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Optional[Dict[str, Any]]: The latest context if found, None otherwise
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping get_latest_context")
                return None

            collection = self._get_contexts_collection()
            doc = await collection.find_one(
                {"session_id": session_id},
                sort=[("updated_at", -1)]
            )
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to get latest intervention context: {e}")
            return None

    async def save_intervention(self, intervention_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Save an intervention document (upsert by intervention id).

        Args:
            intervention_dict: Intervention data dictionary

        Returns:
            Optional[Dict[str, Any]]: The saved intervention document, or None on failure
        """
        try:
            mongodb = get_mongodb()
            if not mongodb.is_connected:
                logger.warning("MongoDB not connected, skipping save_intervention")
                return None

            interventions_collection = self._get_interventions_collection()

            intervention_id = intervention_dict.get("id")
            if not intervention_id:
                logger.warning("Intervention must have an id")
                return None

            # Remove _id if present to avoid conflicts
            data = {k: v for k, v in intervention_dict.items() if k != "_id"}

            await interventions_collection.update_one(
                {"id": intervention_id},
                {"$set": data},
                upsert=True
            )
            doc = await interventions_collection.find_one({"id": intervention_id})
            return self._serialize_doc(doc)
        except Exception as e:
            logger.warning(f"Failed to save intervention: {e}")
            return None

"""
Entity Linker

Identifies knowledge point entities from text using jieba segmentation
and in-memory dictionary matching.
"""
import os
import json
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field

import jieba

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LinkedEntity:
    """Represents a linked entity found in text."""
    label: str
    uri: str
    subject: Optional[str] = None
    start: int = 0
    end: int = 0
    context: Optional[str] = None


class EntityLinker:
    """
    Entity linker using jieba segmentation and dictionary matching.

    Loads entity dictionary from JSON files on initialization,
    adds entities to jieba custom dictionary for better segmentation.

    Usage:
        linker = EntityLinker()
        entities = linker.link("一元二次方程的解法")
        # Returns: [LinkedEntity(label="一元二次方程", uri="..."), ...]
    """

    _instance: Optional['EntityLinker'] = None

    def __new__(cls):
        """Singleton pattern to load dictionary only once."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_dir: str = None):
        """
        Initialize entity linker with dictionary.

        Args:
            data_dir: Directory containing entity JSON files
        """
        if self._initialized:
            return

        self._data_dir = data_dir or os.path.join(
            os.path.dirname(__file__),
            "..", "..", "data", "edukg", "entities"
        )

        # Entity dictionaries
        # {label: {uri, subject}} - for fast lookup by label
        self._entity_dict: Dict[str, Dict[str, str]] = {}
        # {subject: Set[labels]} - for subject filtering
        self._subject_entities: Dict[str, Set[str]] = {}

        # Load entities
        self._load_entities()

        # Add to jieba dictionary
        self._init_jieba()

        self._initialized = True
        logger.info(f"EntityLinker initialized with {len(self._entity_dict)} entities")

    def _load_entities(self):
        """Load entities from JSON files."""
        if not os.path.exists(self._data_dir):
            logger.warning(f"Entity data directory not found: {self._data_dir}")
            return

        # Subject mapping
        subject_files = {
            "math": "math_entities.json",
            "physics": "physics_entities.json",
            "chemistry": "chemistry_entities.json",
            "biology": "biology_entities.json",
            "chinese": "chinese_entities.json",
            "history": "history_entities.json",
            "geo": "geo_entities.json",
            "politics": "politics_entities.json",
            "english": "english_entities.json",
        }

        total_loaded = 0

        for subject, filename in subject_files.items():
            filepath = os.path.join(self._data_dir, filename)
            if not os.path.exists(filepath):
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    entities = json.load(f)

                self._subject_entities[subject] = set()

                for entity in entities:
                    label = entity.get("label", "").strip()
                    uri = entity.get("uri", "").strip()

                    if not label or not uri:
                        continue

                    # Skip invalid labels (URLs, empty, etc.)
                    if label.startswith("http") or len(label) < 2:
                        continue

                    # Add to dictionaries
                    if label not in self._entity_dict:
                        self._entity_dict[label] = {
                            "uri": uri,
                            "subject": subject
                        }
                        self._subject_entities[subject].add(label)
                        total_loaded += 1

            except Exception as e:
                logger.error(f"Failed to load {filename}: {e}")

        logger.info(f"Loaded {total_loaded} unique entities from {len(subject_files)} subjects")

    def _init_jieba(self):
        """Initialize jieba with custom dictionary."""
        # Add all entity labels to jieba dictionary
        for label in self._entity_dict.keys():
            jieba.add_word(label)

        logger.info(f"Added {len(self._entity_dict)} words to jieba dictionary")

    def link(
        self,
        text: str,
        subject: Optional[str] = None,
        enrich_context: bool = False
    ) -> List[LinkedEntity]:
        """
        Identify knowledge point entities in text.

        Args:
            text: Input text to analyze
            subject: Optional subject filter (e.g., "math", "physics")
            enrich_context: Whether to include entity context

        Returns:
            List of LinkedEntity objects
        """
        if not text:
            return []

        # Segment text with jieba
        words = list(jieba.cut(text))

        # Find entities
        entities = []
        current_pos = 0

        for word in words:
            word_start = text.find(word, current_pos)
            word_end = word_start + len(word)
            current_pos = word_end

            # Check if word is in entity dictionary
            if word in self._entity_dict:
                entity_info = self._entity_dict[word]

                # Apply subject filter
                if subject and entity_info["subject"] != subject:
                    continue

                entity = LinkedEntity(
                    label=word,
                    uri=entity_info["uri"],
                    subject=entity_info["subject"],
                    start=word_start,
                    end=word_end,
                )

                entities.append(entity)

        return entities

    def search(self, query: str, subject: Optional[str] = None, limit: int = 20) -> List[Dict[str, str]]:
        """
        Search entities by label (fuzzy match).

        Args:
            query: Search query
            subject: Optional subject filter
            limit: Maximum number of results

        Returns:
            List of entity dictionaries with label, uri, subject
        """
        results = []
        query_lower = query.lower()

        for label, info in self._entity_dict.items():
            # Apply subject filter
            if subject and info["subject"] != subject:
                continue

            # Fuzzy match (contains query)
            if query_lower in label.lower():
                results.append({
                    "label": label,
                    "uri": info["uri"],
                    "subject": info["subject"]
                })

                if len(results) >= limit:
                    break

        return results

    def get_entity(self, uri: str) -> Optional[Dict[str, str]]:
        """
        Get entity by URI.

        Args:
            uri: Entity URI

        Returns:
            Entity dictionary or None if not found
        """
        for label, info in self._entity_dict.items():
            if info["uri"] == uri:
                return {
                    "label": label,
                    "uri": uri,
                    "subject": info["subject"]
                }
        return None

    def get_subjects(self) -> List[str]:
        """Get list of available subjects."""
        return list(self._subject_entities.keys())

    def get_entity_count(self, subject: Optional[str] = None) -> int:
        """
        Get count of entities.

        Args:
            subject: Optional subject filter

        Returns:
            Number of entities
        """
        if subject:
            return len(self._subject_entities.get(subject, set()))
        return len(self._entity_dict)


# Global singleton instance
entity_linker: Optional[EntityLinker] = None


def get_entity_linker() -> EntityLinker:
    """
    Get the entity linker singleton instance.

    Returns:
        EntityLinker instance
    """
    global entity_linker
    if entity_linker is None:
        entity_linker = EntityLinker()
    return entity_linker


def init_entity_linker():
    """Initialize entity linker on application startup."""
    global entity_linker
    entity_linker = EntityLinker()
    logger.info("Entity linker initialized")
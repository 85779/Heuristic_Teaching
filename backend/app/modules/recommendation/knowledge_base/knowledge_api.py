"""Knowledge Base API for reading knowledge ontology."""

import json
import random
from pathlib import Path
from typing import Optional, List, Dict, Any


class KnowledgeBaseAPI:
    """Knowledge base API for querying knowledge points and methods.
    
    Loads all knowledge ontology JSON files into memory on initialization
    for fast querying during recommendation generation.
    """

    def __init__(self, kb_dir: str = "data/knowledge_ontology"):
        """Initialize the knowledge base API.
        
        Args:
            kb_dir: Directory containing knowledge ontology JSON files.
        """
        self._kps: Dict[str, dict] = {}
        self._methods: Dict[str, dict] = {}
        self._type_mappings: Dict[str, dict] = {}
        self._type_to_kps: Dict[str, List[str]] = {}
        self._kb_dir = kb_dir
        self._load_all(kb_dir)

    def _load_all(self, kb_dir: str) -> None:
        """Load all JSON files into memory.
        
        Args:
            kb_dir: Directory containing the JSON files.
        """
        base = Path(kb_dir)
        
        # Load knowledge points
        kp_file = base / "knowledge_points_all.json"
        if kp_file.exists():
            with open(kp_file, encoding="utf-8") as f:
                kps_data = json.load(f)
                kps_list = kps_data.get("knowledge_points", kps_data)
                for kp in kps_list:
                    self._kps[kp["kp_id"]] = kp
        
        # Load methods
        methods_file = base / "methods.json"
        if methods_file.exists():
            with open(methods_file, encoding="utf-8") as f:
                methods_data = json.load(f)
                methods_list = methods_data.get("methods", methods_data)
                for m in methods_list:
                    self._methods[m["name"]] = m

        # Load type-kp mappings and build reverse index
        type_file = base / "type_kp_mapping.json"
        if type_file.exists():
            with open(type_file, encoding="utf-8") as f:
                type_data = json.load(f)
                type_list = type_data.get("mappings", type_data)
                for item in type_list:
                    t = item.get("type", "")
                    self._type_mappings[t] = item
                    # Build type -> kp_ids mapping
                    kp_ids = item.get("knowledge_points", [])
                    if t not in self._type_to_kps:
                        self._type_to_kps[t] = []
                    for kid in kp_ids:
                        if kid not in self._type_to_kps[t]:
                            self._type_to_kps[t].append(kid)

    async def get_kp(self, kp_id: str) -> Optional[dict]:
        """Get a single knowledge point by ID.
        
        Args:
            kp_id: Knowledge point ID.
            
        Returns:
            Knowledge point dict or None if not found.
        """
        return self._kps.get(kp_id)

    async def get_kps(self, kp_ids: List[str]) -> List[dict]:
        """Get multiple knowledge points by IDs.
        
        Args:
            kp_ids: List of knowledge point IDs.
            
        Returns:
            List of knowledge point dicts.
        """
        return [self._kps[kid] for kid in kp_ids if kid in self._kps]

    async def get_prerequisites(self, kp_id: str) -> List[str]:
        """Get prerequisite KP IDs for a given KP.
        
        Args:
            kp_id: Knowledge point ID.
            
        Returns:
            List of prerequisite KP IDs.
        """
        kp = self._kps.get(kp_id, {})
        return kp.get("prerequisites", [])

    async def get_weak_kps(self, mastered_kps: List[str], count: int = 5) -> List[str]:
        """Get weak KPs (not yet mastered).
        
        For demo: randomly selects from all KPs excluding mastered ones.
        In production, this would use Module 4's mastery data.
        
        Args:
            mastered_kps: List of mastered KP IDs.
            count: Number of weak KPs to return.
            
        Returns:
            List of weak KP IDs.
        """
        all_kps = [k for k in self._kps.keys() if k not in mastered_kps]
        if not all_kps:
            return []
        return random.sample(all_kps, min(count, len(all_kps)))

    async def get_same_type_kps(
        self,
        kp_id: str,
        exclude_methods: Optional[List[str]] = None
    ) -> List[dict]:
        """Get KPs of the same type, optionally excluding certain methods.
        
        Args:
            kp_id: Reference KP ID.
            exclude_methods: List of method names to exclude.
            
        Returns:
            List of knowledge point dicts.
        """
        kp = self._kps.get(kp_id, {})
        related_types = kp.get("related_types", [])
        
        same_type_kps = []
        seen_ids = set()
        
        for t in related_types:
            kp_ids = self._type_to_kps.get(t, [])
            # Fall back to prefix match: short name "类型Ⅰ" vs full "类型Ⅰ：..."
            if not kp_ids:
                for full_type, ids in self._type_to_kps.items():
                    if full_type.startswith(t):
                        kp_ids = ids
                        break
            for kid in kp_ids:
                if kid == kp_id or kid in seen_ids:
                    continue
                if kid not in self._kps:
                    continue
                    
                kp_data = self._kps[kid]
                
                # Filter by exclude_methods
                if exclude_methods:
                    kp_methods = kp_data.get("methods", [])
                    if any(m in exclude_methods for m in kp_methods):
                        continue
                
                same_type_kps.append(kp_data)
                seen_ids.add(kid)
        
        return same_type_kps

    async def get_random_kps(self, count: int) -> List[str]:
        """Get random KP IDs for cold start scenarios.
        
        Args:
            count: Number of random KPs to return.
            
        Returns:
            List of random KP IDs.
        """
        all_ids = list(self._kps.keys())
        if not all_ids:
            return []
        return random.sample(all_ids, min(count, len(all_ids)))

    async def get_method(self, method_name: str) -> Optional[dict]:
        """Get method details by name.
        
        Args:
            method_name: Name of the method.
            
        Returns:
            Method dict or None if not found.
        """
        return self._methods.get(method_name)

    async def get_methods_for_kps(self, kp_ids: List[str]) -> List[dict]:
        """Get all methods applicable to given KPs.
        
        Args:
            kp_ids: List of KP IDs.
            
        Returns:
            List of method dicts.
        """
        method_names = set()
        for kid in kp_ids:
            kp = self._kps.get(kid, {})
            method_names.update(kp.get("methods", []))

        return [self._methods[m] for m in method_names if m in self._methods]

    async def identify_kps(self, problem_text: str, top_k: int = 3) -> List[str]:
        """Identify relevant KP IDs from problem text using ngram overlap."""
        def get_ngrams(text: str) -> set[str]:
            """Extract all 2-4 char CJK ngrams from text."""
            # Keep only CJK characters
            cjk_only = "".join(ch for ch in text if 0x4E00 <= ord(ch) <= 0x9FFF)
            ngrams = set()
            for n in (2, 3, 4):
                for i in range(len(cjk_only) - n + 1):
                    ngrams.add(cjk_only[i:i + n])
            return ngrams

        problem_ngrams = get_ngrams(problem_text)
        scored = []

        for kp_id, kp in self._kps.items():
            name_ngrams = get_ngrams(kp.get("name", ""))
            name_score = len(problem_ngrams & name_ngrams) * 5

            content_ngrams = get_ngrams(kp.get("content", ""))
            content_score = len(problem_ngrams & content_ngrams) * 2

            chapter_ngrams = get_ngrams(kp.get("chapter_name", ""))
            chapter_score = len(problem_ngrams & chapter_ngrams) * 1

            score = name_score + content_score + chapter_score
            if score > 0:
                scored.append((kp_id, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [kp_id for kp_id, _ in scored[:top_k]]
        return top if top else [kp_id for kp_id, _ in scored[:1]] if scored else []
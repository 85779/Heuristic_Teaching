"""Enrich knowledge_points_all.json with related_types from type_kp_mapping."""

import json
from pathlib import Path
from collections import defaultdict

KB = Path("data/knowledge_ontology")

# Load data
with open(KB / "knowledge_points_all.json", encoding="utf-8") as f:
    kp_data = json.load(f)
with open(KB / "type_kp_mapping.json", encoding="utf-8") as f:
    type_data = json.load(f)

kps = kp_data["knowledge_points"]
mappings = type_data["mappings"]

# Step 1: Build KP → abbreviated type names from type_kp_mapping
kp_to_types = defaultdict(list)
for m in mappings:
    short = m["type"].split("：")[0] if "：" in m["type"] else m["type"]
    for kpid in m.get("knowledge_points", []):
        if short not in kp_to_types[kpid]:
            kp_to_types[kpid].append(short)

# Step 2: Build chapter/module groupings for KPs without types
module_kps = defaultdict(list)
for k in kps:
    module_kps[k.get("module", "")].append(k["kp_id"])

# Step 3: Enrich
added_from_mapping = 0
added_from_module = 0

for k in kps:
    kpid = k["kp_id"]
    existing = set(k.get("related_types", []))

    # Add from type_kp_mapping
    from_mapping = set(kp_to_types.get(kpid, []))
    new_from_mapping = from_mapping - existing
    if new_from_mapping:
        existing.update(new_from_mapping)
        added_from_mapping += 1

    # For KPs still without types, infer from module grouping
    if not existing:
        module = k.get("module", "")
        # Create a type label from the module name
        module_type = module.replace("模块", "类型") if module else ""
        if module_type:
            existing.add(module_type)
            added_from_module += 1

    k["related_types"] = sorted(existing)

# Step 4: Save
kp_data["metadata"]["related_types_enriched"] = True
kp_data["metadata"]["total_kps"] = len(kps)

with open(KB / "knowledge_points_all.json", "w", encoding="utf-8") as f:
    json.dump(kp_data, f, ensure_ascii=False, indent=2)

# Stats
kps_with_types = sum(1 for k in kps if k.get("related_types"))
coverage = 100 * kps_with_types // len(kps)
print(f"Before: 38/175 (21%)")
print(f"  Added from type_kp_mapping: {added_from_mapping}")
print(f"  Added from module grouping: {added_from_module}")
print(f"After:  {kps_with_types}/{len(kps)} ({coverage}%)")
print(f"Saved to {KB / 'knowledge_points_all.json'}")

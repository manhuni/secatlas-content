#!/usr/bin/env python3
"""Synchronize catalog, shards, and search indexes in secatlas-content directly from content/*.json.

Usage:
    python sync_catalog.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PLACEHOLDER = "{{release}}"
STRIP_LESSON_KEYS = {"sections", "media", "objectives"}


def shard_of(key: str) -> str:
    return hashlib.sha256(str(key).encode("utf-8")).hexdigest()[:2]


def search_prefixes(word: str) -> set[str]:
    return {word[:length] for length in range(1, min(len(word), 24) + 1)}


def write_json_if_changed(path: pathlib.Path, data: dict) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == text:
                return False
        except OSError:
            pass
    path.write_text(text, encoding="utf-8")
    return True


def load_existing_lesson_order() -> list[str]:
    all_dir = ROOT / "catalog" / "lessons" / "all"
    order: list[str] = []
    if not all_dir.is_dir():
        return order
    for page in sorted(all_dir.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 0):
        try:
            doc = json.loads(page.read_text(encoding="utf-8"))
            for item in doc.get("items", []):
                if isinstance(item, dict) and "id" in item:
                    order.append(str(item["id"]))
        except Exception:
            pass
    return order


def sync() -> int:
    content_dir = ROOT / "content"
    if not content_dir.is_dir():
        return 0

    existing_order = load_existing_lesson_order()
    order_index = {lesson_id: idx for idx, lesson_id in enumerate(existing_order)}

    lessons_by_id: dict[str, dict] = {}
    changed_files = 0

    for path in sorted(content_dir.glob("*.json")):
        # Translation editions are <lesson_id>.<lang>.json; base articles have no dot in stem
        if "." in path.stem:
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        item = doc.get("item")
        if not isinstance(item, dict) or "id" not in item:
            continue
        lesson_id = str(item["id"])
        deps = sorted(set(re.findall(r"asset://([a-f0-9]{64})", json.dumps(item))))
        if doc.get("dependencies") != deps or doc.get("release") != PLACEHOLDER:
            doc["dependencies"] = deps
            doc["release"] = PLACEHOLDER
            doc["schemaVersion"] = 1
            if write_json_if_changed(path, doc):
                changed_files += 1
        summary_item = {k: v for k, v in item.items() if k not in STRIP_LESSON_KEYS}
        lessons_by_id[lesson_id] = summary_item

    sorted_lessons = [
        lessons_by_id[lid]
        for lid in sorted(
            lessons_by_id.keys(),
            key=lambda k: (order_index.get(k, 10**9), k),
        )
    ]

    groups: dict[str, list[dict]] = {"all": sorted_lessons}
    for item in sorted_lessons:
        for group in set(filter(None, [item.get("fieldId"), item.get("systemId"), item.get("parentFieldId")])):
            groups.setdefault(str(group), []).append(item)
        text = " ".join(str(item.get(key, "")) for key in ("name", "title", "term"))
        for word in re.findall(r"\w+", text.lower()):
            for prefix in search_prefixes(word):
                group = "search-" + hashlib.sha256(prefix.encode("utf-8")).hexdigest()
                groups.setdefault(group, []).append(item)

    lessons_catalog_dir = ROOT / "catalog" / "lessons"
    search_groups = {g: m for g, m in groups.items() if g.startswith("search-")}

    # Write group pages
    active_group_dirs: set[str] = set()
    for group, matches in groups.items():
        if group.startswith("search-"):
            continue
        active_group_dirs.add(group)
        group_dir = lessons_catalog_dir / group
        active_pages: set[str] = set()
        for offset in range(0, max(1, len(matches)), 40):
            page_name = f"{offset}.json"
            active_pages.add(page_name)
            page_doc = {
                "schemaVersion": 1,
                "release": PLACEHOLDER,
                "items": matches[offset : offset + 40],
                "nextCursor": str(offset + 40) if offset + 40 < len(matches) else None,
            }
            if write_json_if_changed(group_dir / page_name, page_doc):
                changed_files += 1
        if group_dir.is_dir():
            for old_page in group_dir.glob("*.json"):
                if old_page.name not in active_pages:
                    old_page.unlink()
                    changed_files += 1

    if lessons_catalog_dir.is_dir():
        for sub in lessons_catalog_dir.iterdir():
            if sub.is_dir() and sub.name not in active_group_dirs:
                for f in sub.rglob("*"):
                    if f.is_file():
                        f.unlink()
                sub.rmdir()
                changed_files += 1

    if search_groups:
        if write_json_if_changed(
            lessons_catalog_dir / "search-index.json",
            {"schemaVersion": 1, "release": PLACEHOLDER, "groups": search_groups},
        ):
            changed_files += 1

    # Write items/lessons/shards/*.json
    item_shards: dict[str, dict[str, dict]] = {}
    for item in sorted_lessons:
        item_shards.setdefault(shard_of(item["id"]), {})[item["id"]] = item

    shards_dir = ROOT / "items" / "lessons" / "shards"
    active_shards: set[str] = set()
    for shard, entries in item_shards.items():
        shard_name = f"{shard}.json"
        active_shards.add(shard_name)
        if write_json_if_changed(
            shards_dir / shard_name,
            {"schemaVersion": 1, "release": PLACEHOLDER, "items": entries},
        ):
            changed_files += 1
    if shards_dir.is_dir():
        for old_shard in shards_dir.glob("*.json"):
            if old_shard.name not in active_shards:
                old_shard.unlink()
                changed_files += 1

    print(f"Synced {len(sorted_lessons)} lessons ({changed_files} files updated).")
    return 0


if __name__ == "__main__":
    raise SystemExit(sync())

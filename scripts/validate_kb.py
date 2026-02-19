#!/usr/bin/env python3
"""Knowledge base integrity validator.

Checks the knowledge base for:
- Chunk count and completeness
- Embedding dimension consistency
- Source coverage
- Content quality indicators

Usage:
    python scripts/validate_kb.py
    python scripts/validate_kb.py --db-path /path/to/vectordb
"""

import argparse
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.store.vector_store import VectorStore


def validate(db_path: str, embedding_model: str) -> bool:
    """Validate the knowledge base integrity.

    Returns True if all checks pass.
    """
    logger = logging.getLogger(__name__)
    store = VectorStore(db_path=db_path)
    status = store.get_status(embedding_model=embedding_model)

    passed = True
    checks = []

    # Check 1: Store is initialized
    if status.is_initialized:
        checks.append(("Store initialized", "PASS", ""))
    else:
        checks.append(("Store initialized", "FAIL", "Store not initialized"))
        passed = False

    # Check 2: Has chunks
    if status.total_chunks > 0:
        checks.append(("Has chunks", "PASS", f"{status.total_chunks} chunks"))
    else:
        checks.append(("Has chunks", "FAIL", "No chunks found"))
        passed = False

    # Check 3: Has sources
    if status.total_sources > 0:
        checks.append(("Has sources", "PASS", f"{status.total_sources} sources"))
    else:
        checks.append(("Has sources", "FAIL", "No sources indexed"))
        passed = False

    # Check 4: Embedding dimensions
    if status.embedding_dimensions == 384:
        checks.append(("Embedding dims", "PASS", f"{status.embedding_dimensions}d"))
    elif status.embedding_dimensions > 0:
        checks.append((
            "Embedding dims", "WARN",
            f"{status.embedding_dimensions}d (expected 384)"
        ))
    else:
        checks.append(("Embedding dims", "FAIL", "No embedding info"))
        passed = False

    # Check 5: Topics coverage
    topics = store.get_topics()
    if len(topics) >= 5:
        checks.append(("Topic coverage", "PASS", f"{len(topics)} topics"))
    elif len(topics) > 0:
        checks.append(("Topic coverage", "WARN", f"Only {len(topics)} topics"))
    else:
        checks.append(("Topic coverage", "FAIL", "No topics found"))
        passed = False

    # Check 6: Average chunks per source
    if status.total_sources > 0:
        avg = status.total_chunks / status.total_sources
        if avg >= 10:
            checks.append(("Chunks/source", "PASS", f"{avg:.1f} avg"))
        else:
            checks.append(("Chunks/source", "WARN", f"{avg:.1f} avg (low)"))

    # Print results
    print("\n" + "=" * 60)
    print("KNOWLEDGE BASE VALIDATION")
    print("=" * 60)
    print(f"Store path: {db_path}")
    print(f"Model: {embedding_model}")
    print()

    for name, status_val, detail in checks:
        icon = {"PASS": "+", "FAIL": "X", "WARN": "!"}[status_val]
        print(f"  [{icon}] {name}: {status_val} {f'— {detail}' if detail else ''}")

    print()
    if passed:
        print("RESULT: ALL CHECKS PASSED")
    else:
        print("RESULT: SOME CHECKS FAILED")

    return passed


def main():
    parser = argparse.ArgumentParser(
        description="Validate FortiMonitor knowledge base integrity"
    )
    parser.add_argument(
        "--db-path",
        default=os.environ.get("KNOWLEDGE_BASE_PATH", "data/vectordb"),
        help="Path to vector store database (default: data/vectordb)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("KNOWLEDGE_EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        help="Embedding model name (default: all-MiniLM-L6-v2)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    success = validate(args.db_path, args.model)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

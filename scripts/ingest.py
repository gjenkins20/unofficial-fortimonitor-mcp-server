#!/usr/bin/env python3
"""CLI script for ingesting documentation into the knowledge base.

Usage:
    python scripts/ingest.py                    # Ingest all sources
    python scripts/ingest.py --source pdf       # Only PDF sources
    python scripts/ingest.py --source web       # Only web sources
    python scripts/ingest.py --force            # Force re-ingestion
    python scripts/ingest.py --config path.yaml # Custom config file
"""

import argparse
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.knowledge.ingestion.pipeline import IngestionPipeline
from src.knowledge.store.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(
        description="Ingest FortiMonitor documentation into the knowledge base"
    )
    parser.add_argument(
        "--source",
        choices=["pdf", "web"],
        help="Only ingest this source type (default: all)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion of already-processed sources",
    )
    parser.add_argument(
        "--config",
        default="data/sources.yaml",
        help="Path to sources configuration file (default: data/sources.yaml)",
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
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=int(os.environ.get("KNOWLEDGE_CHUNK_SIZE", "800")),
        help="Target chunk size in tokens (default: 800)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=int(os.environ.get("KNOWLEDGE_CHUNK_OVERLAP", "100")),
        help="Chunk overlap in tokens (default: 100)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info("FortiMonitor Knowledge Base Ingestion")
    logger.info(f"  Config: {args.config}")
    logger.info(f"  DB path: {args.db_path}")
    logger.info(f"  Model: {args.model}")
    logger.info(f"  Chunk size: {args.chunk_size}")
    logger.info(f"  Chunk overlap: {args.chunk_overlap}")
    logger.info(f"  Source filter: {args.source or 'all'}")
    logger.info(f"  Force: {args.force}")

    # Initialize components
    store = VectorStore(db_path=args.db_path)
    pipeline = IngestionPipeline(
        vector_store=store,
        embedding_model=args.model,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    # Run ingestion
    result = pipeline.ingest_from_config(
        config_path=args.config,
        source_filter=args.source,
        force=args.force,
    )

    # Report results
    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Sources processed: {result['sources_processed']}")
    print(f"Total chunks added: {result['total_chunks']}")

    if result["errors"]:
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result["errors"]:
            print(f"  - {err['source']}: {err['error']}")

    # Show final status
    status = store.get_status(embedding_model=args.model)
    print(f"\nKnowledge Base Status:")
    print(f"  Total chunks: {status.total_chunks}")
    print(f"  Total sources: {status.total_sources}")
    print(f"  PDF sources: {status.pdf_sources}")
    print(f"  Web sources: {status.web_sources}")
    print(f"  Store path: {status.store_path}")

    if result["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""CLI tool for ingesting PDF documents into the Socrates RAG knowledge base.

Usage:
    # Ingest a single PDF file
    python scripts/ingest_documents.py --file docs/math_induction.pdf --type knowledge_point

    # Ingest all PDFs in a directory
    python scripts/ingest_documents.py --dir docs/ --type method

    # Ingest with custom metadata
    python scripts/ingest_documents.py --file docs/example.pdf --type example \
        --name "等差数列例题" --keywords "等差数列,通项公式,求和"

Environment:
    DASHSCOPE_API_KEY     - DashScope API key (required)
    CHROMA_PERSIST_DIR   - ChromaDB persistence directory (default: ./data/chromadb)
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Fix Windows GBK console encoding for emoji output
import io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load .env before any other imports that might read API keys
from dotenv import load_dotenv
load_dotenv()

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.modules.knowledge_base.embedder import DashScopeEmbeddingClient
from app.modules.knowledge_base.vector_store import ChromaDBVectorStore
from app.modules.knowledge_base.ingestion import IngestionPipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ingest PDF documents into the Socrates RAG knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=str, help="Path to a single PDF file")
    group.add_argument("--dir", type=str, help="Path to a directory of PDF files")

    parser.add_argument(
        "--type",
        type=str,
        default="knowledge_point",
        choices=["knowledge_point", "method", "concept", "example", "strategy"],
        help="Document type (default: knowledge_point)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Document name (for metadata). If not provided, uses filename.",
    )
    parser.add_argument(
        "--keywords",
        type=str,
        default="",
        help="Comma-separated keywords for metadata",
    )
    parser.add_argument(
        "--grade",
        type=str,
        default="high_school",
        help="Target grade (default: high_school)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="medium",
        choices=["easy", "medium", "hard"],
        help="Document difficulty (default: medium)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=400,
        help="Target chunk size in characters (default: 400)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=50,
        help="Overlap between chunks (default: 50)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress",
    )

    return parser.parse_args()


def build_metadata(args: argparse.Namespace, filename: str = None) -> dict:
    """Build metadata dict from command line args."""
    name = args.name or (filename or "unknown")
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    return {
        "type": args.type,
        "name": name,
        "keywords": keywords,
        "grade": args.grade,
        "difficulty": args.difficulty,
    }


async def ingest_single_file(pipeline: IngestionPipeline, file_path: str, args: argparse.Namespace):
    """Ingest a single PDF file."""
    metadata = build_metadata(args, Path(file_path).stem)
    if args.verbose:
        print(f"  Processing: {file_path}")
        print(f"  Metadata: {metadata}")

    try:
        result = await pipeline.ingest_file(
            file_path=file_path,
            metadata=metadata,
        )
        status = result.get("status", "unknown")
        if status == "success":
            chunks = result.get("chunks", 0)
            print(f"  [OK] {Path(file_path).name}: {chunks} chunks ingested")
            return True
        else:
            print(f"  [FAIL] {Path(file_path).name}: {result.get('error', 'unknown error')}")
            return False
    except Exception as e:
        print(f"  [FAIL] {Path(file_path).name}: {e}")
        return False


async def main():
    args = parse_args()

    # Check API key
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("Error: DASHSCOPE_API_KEY environment variable not set.")
        print("Run: export DASHSCOPE_API_KEY=your_key")
        sys.exit(1)

    # Initialize components
    embedder = DashScopeEmbeddingClient(api_key=api_key)
    vector_store = ChromaDBVectorStore()
    pipeline = IngestionPipeline(vector_store=vector_store, embedder=embedder)

    print(f"Socrates RAG Document Ingestion Tool")
    print(f"  Type: {args.type}")
    print(f"  Grade: {args.grade}")
    print(f"  Difficulty: {args.difficulty}")
    print()

    if args.file:
        # Single file mode
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        print(f"Ingesting single file: {args.file}")
        success = await ingest_single_file(pipeline, args.file, args)

    elif args.dir:
        # Directory mode
        if not os.path.exists(args.dir):
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)

        pdf_files = list(Path(args.dir).glob("*.pdf"))
        if not pdf_files:
            print(f"Warning: No PDF files found in {args.dir}")
            return

        print(f"Ingesting {len(pdf_files)} PDF files from: {args.dir}")
        print()

        success_count = 0
        for pdf_file in pdf_files:
            ok = await ingest_single_file(pipeline, str(pdf_file), args)
            if ok:
                success_count += 1

        print()
        print(f"Done: {success_count}/{len(pdf_files)} files ingested successfully")

    # Print stats
    stats = vector_store.get_stats()
    print()
    print("Knowledge base stats:")
    print(f"  Total chunks: {stats.get('total_chunks', 0)}")
    print(f"  Unique documents: {stats.get('unique_docs', 0)}")


if __name__ == "__main__":
    asyncio.run(main())

"""Test script for document ingestion pipeline."""

import asyncio
import logging
import sys
import os
import argparse

# Add project root and ingestion to path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_path)
sys.path.insert(0, os.path.join(root_path, "ingestion"))

from ingestion.ingest import DocumentIngestionPipeline
from models.ingest import IngestionConfig


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Run ingestion pipeline on the documents folder or Google Drive."""

    parser = argparse.ArgumentParser(description="Test document ingestion")
    parser.add_argument("--gdrive", action="store_true", help="Ingest from Google Drive")
    parser.add_argument("--folder-id", default=os.getenv("GDRIVE_FOLDER_ID", ""), help="Drive folder ID")
    parser.add_argument("--s3", action="store_true", help="Ingest from S3 compatible storage")
    parser.add_argument("--s3-prefix", default="", help="S3 bucket prefix (folder)")
    parser.add_argument("--documents", "-d", default="documents", help="Local documents folder")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning existing data")
    args = parser.parse_args()

    config = IngestionConfig(
        max_tokens=512
    )

    if args.s3:
        source_type = "s3"
    elif args.gdrive:
        source_type = "gdrive"
    else:
        source_type = "local"

    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder=args.documents,
        clean_before_ingest=not args.no_clean,
        source_type=source_type,
        gdrive_folder_id=args.folder_id,
        s3_prefix=args.s3_prefix
    )

    def progress(current: int, total: int):
        print(f"  [{current}/{total}] documents processed")

    try:
        results = await pipeline.ingest_documents(progress_callback=progress)

        # Summary
        print("\n" + "=" * 50)
        print("INGESTION RESULTS")
        print("=" * 50)

        for r in results:
            status = "✅" if not r.errors else "❌"
            print(f"{status} {r.title}")
            print(f"   ID: {r.document_id}")
            print(f"   Chunks: {r.chunks_created}")
            print(f"   Time: {r.processing_time_ms:.0f}ms")
            if r.errors:
                for err in r.errors:
                    print(f"   Error: {err}")

        total_chunks = sum(r.chunks_created for r in results)
        total_errors = sum(len(r.errors) for r in results)
        print(f"\nTotal: {len(results)} docs, {total_chunks} chunks, {total_errors} errors")

    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        raise
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())

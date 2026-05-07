"""CLI entrypoint for worker pipeline orchestration."""

import argparse
import sys


def run_ingest() -> None:
    """W1: Extract + upload to MinIO raw."""
    import asyncio
    from pathlib import Path

    from worker.core.config import settings
    from worker.ingestion.ingest_w1 import ingest_csv

    source = Path(settings.csv_source_path)
    datasets = ["winners", "matches", "players"]

    async def _run() -> None:
        for ds in datasets:
            files = list(source.glob(f"{ds}*.csv"))
            for f in files:
                await ingest_csv(f, ds, settings)

    asyncio.run(_run())


def run_clean() -> None:
    """W2: Validate + mark valid/invalid."""
    print("W2: Clean pipeline — not yet implemented")


def run_load() -> None:
    """W3: Transform + load public.* + export Parquet."""
    print("W3: Load pipeline — not yet implemented")


def run_analysis() -> None:
    """Run all analysis workers."""
    from worker.analysis.runner import main as run_analysis

    run_analysis()


def main() -> None:
    """Parse arguments and execute requested pipeline stages."""
    parser = argparse.ArgumentParser(
        prog="fifa-worker",
        description="FIFA World Cup ETL Pipeline Worker",
    )
    parser.add_argument("--ingest", action="store_true", help="Run ingestion (W1)")
    parser.add_argument("--clean", action="store_true", help="Run cleaning (W2)")
    parser.add_argument("--load", action="store_true", help="Run loading (W3)")
    parser.add_argument("--analysis", action="store_true", help="Run analysis workers")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")

    args = parser.parse_args()

    if not any([args.ingest, args.clean, args.load, args.analysis, args.all]):
        parser.print_help()
        sys.exit(1)

    if args.all:
        run_ingest()
        run_clean()
        run_load()
        run_analysis()
    else:
        if args.ingest:
            run_ingest()
        if args.clean:
            run_clean()
        if args.load:
            run_load()
        if args.analysis:
            run_analysis()


if __name__ == "__main__":
    main()

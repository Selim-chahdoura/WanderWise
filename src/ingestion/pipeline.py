import argparse
from pathlib import Path

from src.ingestion.chunk import chunk_country
from src.ingestion.extract import extract_country
from src.ingestion.ingest import download_dump
from src.ingestion.process import process_country
from src.retrieval.embed import embed_country
from src.retrieval.index_documents import index_country


def run_pipeline(country: str) -> None:
    country = country.strip()

    if not country:
        raise ValueError("Country must not be empty.")

    print(f"\nStarting ingestion pipeline for {country}\n")

    dump_path = download_dump()

    raw_path = extract_country(
        country=country,
        dump_path= Path(dump_path),
    )

    processed_path = process_country(
        country=country,
        input_path=raw_path,
    )

    chunked_path = chunk_country(
        country=country,
        input_path=processed_path,
    )

    embedded_path = embed_country(
        country=country,
        input_path=chunked_path,
    )

    stored_count = index_country(
        country=country,
        input_path=embedded_path,
    )

    print(
        f"\nPipeline completed for {country}. "
        f"Indexed {stored_count} documents."
    )


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run the WanderWise ingestion pipeline."
    )

    parser.add_argument(
        "--country",
        required=True,
        help="Country to extract and index.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_arguments()
    run_pipeline(arguments.country)
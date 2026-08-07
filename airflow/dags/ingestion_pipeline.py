from datetime import datetime
from airflow.sdk import Param, dag, get_current_context, task

from src.ingestion.chunk import chunk_country
from src.ingestion.extract import extract_country
from src.ingestion.ingest import download_dump
from src.ingestion.process import process_country
from src.retrieval.embed import embed_country
from src.retrieval.index_documents import index_country


@dag(
    dag_id="wanderwise_country_ingestion",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    params={
        "country": Param(
            type="string",
            minLength=1,
            title="Country",
            description="Country to add to WanderWise",
        )
    },
    tags=["wanderwise", "ingestion"],
)
def run_country_data_ingestion_pipeline():

    @task
    def get_country() -> str:
        context = get_current_context()
        country = context["dag_run"].conf["country"]

        print(f"Starting ingestion for {country}")

        return country

    @task
    def ensure_dump_available() -> str:
        return str(download_dump())

    @task
    def extract_country_data(
        country: str,
        dump_path: str,
    ) -> str:
        return str(
            extract_country(
                country=country,
                dump_path=dump_path,
            )
        )

    @task
    def process_country_data(
        country: str,
        input_path: str,
    ) -> str:
        return str(
            process_country(
                country=country,
                input_path=input_path,
            )
        )

    @task
    def chunk_country_data(
        country: str,
        input_path: str,
    ) -> str:
        return str(
            chunk_country(
                country=country,
                input_path=input_path,
            )
        )

    @task
    def embed_country_data(
        country: str,
        input_path: str,
    ) -> str:
        return str(
            embed_country(
                country=country,
                input_path=input_path,
            )
        )

    @task
    def index_country_data(
        country: str,
        input_path: str,
    ) -> int:
        return index_country(
            country=country,
            input_path=input_path,
        )

    country = get_country()
    dump_path = ensure_dump_available()

    extracted_path = extract_country_data(
        country,
        dump_path,
    )

    processed_path = process_country_data(
        country,
        extracted_path,
    )

    chunked_path = chunk_country_data(
        country,
        processed_path,
    )

    embedded_path = embed_country_data(
        country,
        chunked_path,
    )

    index_country_data(
        country,
        embedded_path,
    )


run_country_data_ingestion_pipeline()
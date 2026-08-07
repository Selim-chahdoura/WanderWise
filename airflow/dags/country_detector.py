import json
import os
from pathlib import Path
from airflow.providers.standard.operators.trigger_dagrun import TriggerDagRunOperator

import psycopg
from airflow.sdk import dag, task


COUNTRIES_FILE = Path("config/countries.json")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pswd@host.docker.internal:5432/wanderwise",
)


@dag(
    dag_id="wanderwise_country_detector",
    schedule="*/1 * * * *",
    catchup=False,
    tags=["wanderwise", "detector"],
)
def country_detector():

    @task
    def load_configured_countries():
        with COUNTRIES_FILE.open(encoding="utf-8") as file:
            config = json.load(file)

        countries = config["countries"]

        print(f"Configured countries: {countries}")

        return countries

    @task
    def load_indexed_countries():
        with psycopg.connect(DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT country
                    FROM documents
                    """
                )

                countries = [
                    row[0]
                    for row in cursor.fetchall()
                ]

        print(f"Already indexed countries: {countries}")

        return countries

    @task
    def find_new_countries(
        configured_countries,
        indexed_countries,
    ):
        new_countries = [
            country
            for country in configured_countries
            if country not in indexed_countries
        ]

        print(f"New countries: {new_countries}")

        return new_countries

    @task
    def build_trigger_configs(countries):
        return [
            {"country": country}
            for country in countries
        ]

    configured = load_configured_countries()
    indexed = load_indexed_countries()

    new_countries = find_new_countries(
            configured,
            indexed,
        )

    trigger_configs = build_trigger_configs(new_countries)
    TriggerDagRunOperator.partial(
        task_id="trigger_ingestion",
        trigger_dag_id="wanderwise_country_ingestion",
    ).expand(
        conf=trigger_configs
    )

country_detector()
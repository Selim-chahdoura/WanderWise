import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector


load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:pswd@localhost:5432/wanderwise",
)


def connect():
    connection = psycopg.connect(DATABASE_URL)
    connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(connection)

    return connection


def load_documents(input_path):
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"File not found: {input_path}"
        )

    with input_path.open(encoding="utf-8") as file:
        documents = json.load(file)

    if not documents:
        raise ValueError(
            f"No documents found in {input_path}"
        )

    return documents


def create_table(connection, vector_size):
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            country TEXT NOT NULL,
            destination TEXT,
            place_type TEXT,
            section TEXT,
            subsection TEXT,
            chunk_index INTEGER,
            text TEXT NOT NULL,
            embedding VECTOR({vector_size}) NOT NULL,

            search_vector TSVECTOR GENERATED ALWAYS AS (
                setweight(
                    to_tsvector(
                        'english',
                        COALESCE(destination, '')
                    ),
                    'A'
                )
                ||
                setweight(
                    to_tsvector(
                        'english',
                        COALESCE(section, '')
                    ),
                    'B'
                )
                ||
                setweight(
                    to_tsvector(
                        'english',
                        COALESCE(subsection, '')
                    ),
                    'C'
                )
                ||
                setweight(
                    to_tsvector(
                        'english',
                        COALESCE(text, '')
                    ),
                    'D'
                )
            ) STORED
        )
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS documents_search_idx
        ON documents USING GIN (search_vector)
        """
    )

    connection.commit()


def store_documents(connection, documents):
    rows = []

    for document in documents:
        embedding = document.get("embedding")

        if not embedding:
            raise ValueError(
                f"Document {document.get('id')} has no embedding."
            )

        rows.append(
            (
                document["id"],
                document["country"],
                document.get("destination"),
                document.get("place_type"),
                document.get("section"),
                document.get("subsection"),
                document.get("chunk_index"),
                document["text"],
                embedding,
            )
        )

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO documents (
                id,
                country,
                destination,
                place_type,
                section,
                subsection,
                chunk_index,
                text,
                embedding
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (id) DO NOTHING
            """,
            rows,
        )

    connection.commit()

    return len(rows)


def index_country(country, input_path):
    country = country.strip()
    documents = load_documents(input_path)

    if any(
        document.get("country") != country
        for document in documents
    ):
        raise ValueError(
            f"The file contains documents outside {country}."
        )

    vector_size = len(documents[0]["embedding"])

    print(f"Indexing {country}...")

    with connect() as connection:
        create_table(connection, vector_size)
        stored_count = store_documents(
            connection,
            documents,
        )

    print(
        f"Stored {stored_count} documents for {country}."
    )

    return stored_count


if __name__ == "__main__":
    index_country(
        country="Japan",
        input_path="data/processed/embeddings/japan.json",
    )
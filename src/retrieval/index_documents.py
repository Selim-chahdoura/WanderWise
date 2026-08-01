import json
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer


data_path = Path("data/processed/chunked_documents.json")
database_url = "postgresql://user:pswd@localhost:5432/wanderwise"
model_name = "all-MiniLM-L6-v2"

def connect():
    return psycopg.connect(database_url)

def load_documents():
    with open(data_path, encoding="utf-8") as file:
        return json.load(file)


def build_text(document):
    parts = [
        document.get("country"),
        document.get("destination"),
        document.get("section"),
        document.get("subsection"),
        document.get("text"),
    ]

    return " ".join(part for part in parts if part)


def create_model():
    return SentenceTransformer(model_name)


def connect():
    connection = psycopg.connect(database_url)
    connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(connection)

    return connection


def create_table(connection, vector_size):
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            country TEXT,
            destination TEXT,
            place_type TEXT,
            section TEXT,
            subsection TEXT,
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
        ON documents
        USING GIN (search_vector)
        """
    )

    connection.commit()


def store_documents(connection, model, documents):
    texts = [build_text(document) for document in documents]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    rows = []

    for document, embedding in zip(documents, embeddings):
        rows.append(
            (
                document["id"],
                document.get("country"),
                document.get("destination"),
                document.get("place_type"),
                document.get("section"),
                document.get("subsection"),
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
                text,
                embedding
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                country = EXCLUDED.country,
                destination = EXCLUDED.destination,
                place_type = EXCLUDED.place_type,
                section = EXCLUDED.section,
                subsection = EXCLUDED.subsection,
                text = EXCLUDED.text,
                embedding = EXCLUDED.embedding
            """,
            rows,
        )

    connection.commit()

    print(f"Stored {len(rows)} documents.")


if __name__ == "__main__":
    documents = load_documents()
    model = create_model()

    with connect() as connection:
        create_table(
            connection,
            model.get_embedding_dimension(),
        )

        store_documents(
            connection,
            model,
            documents,
        )
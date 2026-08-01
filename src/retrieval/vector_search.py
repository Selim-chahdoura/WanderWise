import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer


database_url = "postgresql://user:pswd@localhost:5432/wanderwise"
model_name = "all-MiniLM-L6-v2"


def create_model():
    return SentenceTransformer(model_name)


def connect():
    connection = psycopg.connect(database_url)
    register_vector(connection)

    return connection


def search(
    connection,
    query,
    model = create_model(),
    country=None,
    destination=None,
    num_results=5,
):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    conditions = []
    parameters = [query_embedding]

    if country:
        conditions.append("country = %s")
        parameters.append(country)

    if destination:
        conditions.append("destination = %s")
        parameters.append(destination)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    parameters.extend(
        [
            query_embedding,
            num_results,
        ]
    )

    return connection.execute(
        f"""
        SELECT
            id,
            country,
            destination,
            place_type,
            section,
            subsection,
            text,
            1 - (embedding <=> %s) AS score
        FROM documents
        {where_clause}
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        parameters,
    ).fetchall()


def print_results(results):
    for result in results:
        (
            document_id,
            country,
            destination,
            place_type,
            section,
            subsection,
            text,
            score,
        ) = result

        print()
        print(f"Score: {score:.3f}")
        print(f"ID: {document_id}")
        print(f"Country: {country}")
        print(f"Destination: {destination}")
        print(f"Section: {section}")
        print(f"Subsection: {subsection}")
        print(text[:400])


if __name__ == "__main__":
    model = create_model()

    with connect() as connection:
        results = search(
            connection=connection,
            query="How can I get around Marrakech?",
            model=model
            
        )

        print_results(results)
import psycopg
from src.retrieval.index_documents import connect

database_url = "postgresql://user:pswd@localhost:5432/wanderwise"



def search(
    connection,
    query,
    country=None,
    destination=None,
    num_results=5,
    destination_weight=1.0,
    section_weight=0.7,
    subsection_weight=0.5,
    text_weight=0.2,
):
    weights = [
        text_weight,
        subsection_weight,
        section_weight,
        destination_weight,
    ]

    conditions = [
        "search_vector @@ websearch_to_tsquery('english', %s)"
    ]

    filter_parameters = [query]

    if country:
        conditions.append("country = %s")
        filter_parameters.append(country)

    if destination:
        conditions.append("destination = %s")
        filter_parameters.append(destination)

    where_clause = " AND ".join(conditions)

    # Parameters must follow the exact placeholder order in the SQL:
    # 1. weights for ts_rank
    # 2. query for ts_rank
    # 3. query for WHERE
    # 4. optional filters
    # 5. limit
    parameters = [
        weights,
        query,
        *filter_parameters,
        num_results,
    ]

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
            ts_rank(
                %s::real[],
                search_vector,
                websearch_to_tsquery('english', %s)
            ) AS score
        FROM documents
        WHERE {where_clause}
        ORDER BY score DESC
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
    with connect() as connection:
        results = search(
            connection=connection,
            query="How can I get around Marrakech?",
            country="Morocco",
            destination="Marrakech",
        )

        print_results(results)
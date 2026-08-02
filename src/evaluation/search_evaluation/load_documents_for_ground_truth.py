import psycopg  

database_url = "postgresql://user:pswd@localhost:5432/wanderwise"


def load_documents(number_of_documents):
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                country,
                destination,
                place_type,
                section,
                subsection,
                text
            FROM documents
            WHERE LENGTH(text) > 500
            ORDER BY RANDOM()
            LIMIT %s
            """,
            [number_of_documents],
        ).fetchall()

    documents = []

    for row in rows:
        documents.append(
            {
                "id": row[0],
                "country": row[1],
                "destination": row[2],
                "place_type": row[3],
                "section": row[4],
                "subsection": row[5],
                "text": row[6],
            }
        )

    return documents
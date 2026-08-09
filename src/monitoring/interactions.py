import json

from src.retrieval.index_documents import connect


def ensure_interactions_table():
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id SERIAL PRIMARY KEY,

                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,

                    response_time_ms DOUBLE PRECISION,
                    model_time_ms DOUBLE PRECISION,

                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,

                    model_call_count INTEGER,
                    tool_call_count INTEGER,

                    search_history JSONB,

                    feedback INTEGER,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        connection.commit()


def save_interaction(question, result):
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO interactions (
                    question,
                    answer,
                    response_time_ms,
                    model_time_ms,
                    input_tokens,
                    output_tokens,
                    total_tokens,
                    model_call_count,
                    tool_call_count,
                    search_history
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                RETURNING id;
                """,
                (
                    question,
                    result["answer"],
                    result["response_time_ms"],
                    result["model_time_ms"],
                    result["input_tokens"],
                    result["output_tokens"],
                    result["total_tokens"],
                    result["model_call_count"],
                    result["tool_call_count"],
                    json.dumps(result["search_history"]),
                ),
            )

            interaction_id = cursor.fetchone()[0]

        connection.commit()

    return interaction_id


def update_feedback(interaction_id, feedback):
    if feedback not in (1, -1):
        raise ValueError("Feedback must be 1 or -1.")

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE interactions
                SET feedback = %s
                WHERE id = %s;
                """,
                (
                    feedback,
                    interaction_id,
                ),
            )

        connection.commit()


if __name__ == "__main__":
    ensure_interactions_table()
    print("Interactions table is ready.")
import json
from pathlib import Path

import ollama
import psycopg
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

from src.evaluation.evaluation_utils import load_ground_truth
from src.rag.rag import answer_question_with_trace


database_url = "postgresql://user:pswd@localhost:5432/wanderwise"

output_path = Path(
    "data/evaluation/rag_evaluation_answers.json"
)

number_of_questions = 100
reference_model = "qwen3:4b"


class ExpectedAnswer(BaseModel):
    answer: str


def load_relevant_documents(document_ids):
    with psycopg.connect(database_url) as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                country,
                destination,
                section,
                subsection,
                text
            FROM documents
            WHERE id = ANY(%s)
            """,
            [document_ids],
        ).fetchall()

    return rows


def build_reference_context(documents):
    context_parts = []

    for document in documents:
        (
            document_id,
            country,
            destination,
            section,
            subsection,
            text,
        ) = document

        context_parts.append(
            f"""
Country: {country}
Destination: {destination or ""}
Section: {section}
Subsection: {subsection or ""}
Content:
{text}
""".strip()
        )

    return "\n\n".join(context_parts)


def generate_expected_answer(question, documents):
    context = build_reference_context(documents)

    prompt = f"""
Answer the question using only the reference context.

Rules:
- Give a concise and complete answer.
- Do not use outside knowledge.
- Do not mention the context or document.
- If the context does not answer the question, say that clearly.

Question:
{question}

Reference context:
{context}
""".strip()

    response = ollama.chat(
        model=reference_model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        format=ExpectedAnswer.model_json_schema(),
        think=False,
        keep_alive=-1,
        options={
            "temperature": 0,
            "num_predict": 150,
        },
    )

    result = ExpectedAnswer.model_validate_json(
        response.message.content
    )

    return result.answer


def create_evaluation_item(
    ground_truth_item,
    expected_answer,
    rag_result,
):
    return {
        "question": ground_truth_item["question"],
        "country": ground_truth_item.get("country"),
        "destination": ground_truth_item.get("destination"),
        "relevant_document_ids": ground_truth_item[
            "relevant_document_ids"
        ],
        "expected_answer": expected_answer,
        "generated_answer": rag_result["answer"],
        "tool_call_count": rag_result["tool_call_count"],
        "search_history": rag_result["search_history"],
    }


def process_question(item):
    relevant_documents = load_relevant_documents(
        item["relevant_document_ids"]
    )

    if not relevant_documents:
        raise ValueError(
            f"No documents found for {item['relevant_document_ids']}"
        )

    expected_answer = generate_expected_answer(
        question=item["question"],
        documents=relevant_documents,
    )

    rag_result = answer_question_with_trace(
        item["question"]
    )

    return create_evaluation_item(
        ground_truth_item=item,
        expected_answer=expected_answer,
        rag_result=rag_result,
    )


def generate_answers(ground_truth):
    selected_questions = ground_truth[:number_of_questions]
    evaluation_data = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(process_question, item): item
            for item in selected_questions
        }

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Generating evaluation answers",
        ):
            item = futures[future]

            try:
                evaluation_data.append(future.result())

            except Exception as error:
                evaluation_data.append(
                    {
                        "question": item["question"],
                        "country": item.get("country"),
                        "destination": item.get("destination"),
                        "relevant_document_ids": item[
                            "relevant_document_ids"
                        ],
                        "expected_answer": None,
                        "generated_answer": None,
                        "tool_call_count": 0,
                        "search_history": [],
                        "error": str(error),
                    }
                )

    return evaluation_data


def save_answers(evaluation_data):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            evaluation_data,
            file,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    ground_truth = load_ground_truth()

    evaluation_data = generate_answers(ground_truth)

    save_answers(evaluation_data)

    print()
    print(f"Saved {len(evaluation_data)} items to {output_path}")
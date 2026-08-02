import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import ollama
from pydantic import BaseModel, Field
from tqdm import tqdm


INPUT_PATH = Path(
    "data/evaluation/rag_evaluation_answers.json"
)

OUTPUT_PATH = Path(
    "data/evaluation/rag_evaluation_results.json"
)

JUDGE_MODEL = "qwen3:4b"
MAX_WORKERS = 2


class JudgeResult(BaseModel):
    correctness: int = Field(ge=1, le=5)
    faithfulness: int = Field(ge=1, le=5)
    relevance: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    explanation: str = Field(
        max_length=300,
        description="A brief explanation of no more than 40 words.",
    )


JUDGE_INSTRUCTIONS = """
You are evaluating answers produced by a travel RAG system.

Evaluate the generated answer using only the question, expected answer,
generated answer, and retrieved context.

Scores:
1 = very poor
2 = poor
3 = acceptable
4 = good
5 = excellent

Criteria:
- Correctness: The generated answer agrees with the expected answer.
- Faithfulness: Every factual claim is supported by the retrieved context.
- Relevance: The answer directly addresses the question.
- Completeness: The answer includes the important information from the expected answer.

Rules:
- Do not use your own travel knowledge.
- Do not penalize different wording when the meaning is the same.
- Extra details are acceptable only when supported and useful.
- Lower faithfulness for unsupported claims.
- Lower relevance for unnecessary details.
- Keep the explanation under 40 words.
""".strip()


def load_data():
    with open(INPUT_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_results(results):
    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            ensure_ascii=False,
            indent=2,
        )


def build_context(search_history):
    return "\n\n".join(
        search["context"]
        for search in search_history
        if search.get("context")
    )


def evaluate_item(item):
    context = build_context(
        item.get("search_history", [])
    )

    prompt = f"""
Question:
{item["question"]}

Expected answer:
{item["expected_answer"]}

Generated answer:
{item["generated_answer"]}

Retrieved context:
{context}
""".strip()

    response = ollama.chat(
        model=JUDGE_MODEL,
        messages=[
            {
                "role": "system",
                "content": JUDGE_INSTRUCTIONS,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        format=JudgeResult.model_json_schema(),
        think=False,
        keep_alive=-1,
        options={
            "temperature": 0,
        },
    )

    evaluation = JudgeResult.model_validate_json(
        response.message.content
    )

    return {
        **item,
        "evaluation": evaluation.model_dump(),
    }


def evaluate_answers(data):
    valid_items = [
        item
        for item in data
        if item.get("expected_answer")
        and item.get("generated_answer")
    ]

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        results = list(
            tqdm(
                executor.map(
                    evaluate_item,
                    valid_items,
                ),
                total=len(valid_items),
                desc="Judging RAG answers",
            )
        )

    return results


def average_score(results, metric):
    scores = [
        item["evaluation"][metric]
        for item in results
    ]

    return sum(scores) / len(scores)


def print_results(results):
    print()
    print(f"Evaluated answers: {len(results)}")
    print(
        f"Correctness: "
        f"{average_score(results, 'correctness'):.3f}"
    )
    print(
        f"Faithfulness: "
        f"{average_score(results, 'faithfulness'):.3f}"
    )
    print(
        f"Relevance: "
        f"{average_score(results, 'relevance'):.3f}"
    )
    print(
        f"Completeness: "
        f"{average_score(results, 'completeness'):.3f}"
    )


if __name__ == "__main__":
    data = load_data()

    results = evaluate_answers(data)

    save_results(results)
    print_results(results)

    print()
    print(f"Saved results to {OUTPUT_PATH}")
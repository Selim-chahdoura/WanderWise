import json
from pathlib import Path

import ollama
from pydantic import BaseModel, Field

from load_documents_for_ground_truth import load_documents


output_path = Path("data/evaluation/generated_ground_truth.json")

model_name = "qwen3:4b"
number_of_documents = 100

class Questions(BaseModel):
    questions: list[str] = Field(
        min_length=2,
        max_length=2,
        description="Exactly two natural travel questions",
    )


data_gen_instructions = """
You are creating evaluation questions for a travel assistant.

Generate exactly 2 different questions that can be answered using the
source text provided by the user.

Rules:
- Return exactly 2 questions.
- Both questions must be answerable using the source text.
- Ask about different information when possible.
- Do not copy full sentences from the source text.
- Do not mention the source text or document.
- Do not turn metadata into questions.
- Do not output labels such as Country, Destination, Section, or Subsection.
- Each question must have a clear answer.
- Questions must be complete and natural.
- Use fewer exact words from the source text when possible.
- Write questions like real people ask them online.
- Do not make the questions too formal, too short, or too long.
""".strip()


def generate_questions(document):
    context = [
        f"Country: {document['country']}",
        f"Section: {document['section']}",
    ]

    if document.get("destination"):
        context.append(f"Destination: {document['destination']}")

    if document.get("subsection"):
        context.append(f"Subsection: {document['subsection']}")

    metadata = "\n".join(context)

    prompt = f"""
Context:
{metadata}

SOURCE TEXT START
{document["text"]}
SOURCE TEXT END
""".strip()

    response = ollama.chat(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": data_gen_instructions,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        format=Questions.model_json_schema(),
        think=False,
        options={
            "temperature": 0.3,
            "num_predict": 100,
            "num_ctx": 2048,
        },
    )

    result = Questions.model_validate_json(
        response.message.content
    )

    return result.questions


def generate_ground_truth(documents):
    ground_truth = []

    for number, document in enumerate(documents, start=1):
        destination = document.get("destination") or document["country"]

        print(
            f"Generating questions {number}/{len(documents)} "
            f"for {destination}..."
        )

        try:
            questions = generate_questions(document)

            for question in questions:
                ground_truth.append(
                    {
                        "question": question,
                        "country": document["country"],
                        "destination": document.get("destination"),
                        "relevant_document_ids": [document["id"]],
                        "source_section": document["section"],
                        "source_subsection": document.get(
                            "subsection",
                            "",
                        ),
                    }
                )

        except Exception as error:
            print(
                f"Could not process document "
                f"{document['id']}: {error}"
            )

    return ground_truth


def save_ground_truth(ground_truth):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            ground_truth,
            file,
            ensure_ascii=False,
            indent=2,
        )


if __name__ == "__main__":
    documents = load_documents(number_of_documents)

    ground_truth = generate_ground_truth(documents)
    save_ground_truth(ground_truth)

    print()
    print(f"Generated {len(ground_truth)} questions.")
    print(f"Saved to {output_path}")
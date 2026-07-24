import json
from pathlib import Path


input_path = Path("data/processed/documents.json")


def check_text_lengths():
    with open(input_path, encoding="utf-8") as file:
        documents = json.load(file)

    lengths = [len(document["text"]) for document in documents]

    print(f"Documents: {len(lengths)}")
    print(f"Min length: {min(lengths)}")
    print(f"Max length: {max(lengths)}")
    print(f"Average length: {sum(lengths) / len(lengths):.2f}")


if __name__ == "__main__":
    check_text_lengths()
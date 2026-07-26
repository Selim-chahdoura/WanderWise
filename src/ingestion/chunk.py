import json
from pathlib import Path


input_path = Path("data/processed/documents.json")
output_path = Path("data/processed/chunked_documents.json")

max_length = 1500
overlap = 200


def split_text(text):
    if len(text) <= max_length:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_length
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def chunk_documents():
    with open(input_path, encoding="utf-8") as file:
        documents = json.load(file)

    result = []
    document_id = 1

    for document in documents:
        for chunk in split_text(document["text"]):
            new_document = document.copy()
            new_document["id"] = str(document_id)
            new_document["text"] = chunk

            result.append(new_document)
            document_id += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    print(f"Before chunking: {len(documents)}")
    print(f"After chunking: {len(result)}")
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    chunk_documents()
import json
from pathlib import Path

from minsearch import VectorSearch
from sentence_transformers import SentenceTransformer


data_path = Path("data/processed/chunked_documents.json")
model_name = "all-MiniLM-L6-v2"


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


def create_index(documents, model):
    texts = [build_text(document) for document in documents]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    index = VectorSearch(
        keyword_fields=[
            "country",
            "destination",
            "place_type",
        ]
    )

    index.fit(embeddings, documents)

    return index


def search(
    index,
    model,
    query,
    country=None,
    destination=None,
    num_results=5,
):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    filters = {}

    if country:
        filters["country"] = country

    if destination:
        filters["destination"] = destination

    return index.search(
        query_embedding,
        filter_dict=filters,
        num_results=num_results,
    )


def print_results(results):
    for result in results:
        print()
        print(f"ID: {result['id']}")
        print(f"Country: {result['country']}")
        print(f"Destination: {result['destination']}")
        print(f"Section: {result['section']}")
        print(f"Subsection: {result['subsection']}")
        print(result["text"][:400])


if __name__ == "__main__":
    documents = load_documents()
    model = create_model()
    index = create_index(documents, model)

    results = search(
        index=index,
        model=model,
        query="How can I get around Marrakech?",
        country="Morocco",
    )

    print_results(results)
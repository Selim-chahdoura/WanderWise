import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


EMBEDDED_DATA_DIR = Path("data/processed/embeddings")
MODEL_NAME = "all-MiniLM-L6-v2"


def normalize_country_name(country: str) -> str:
    """
    Convert a country name into a safe filename.

    Example:
        "New Zealand" -> "new_zealand"
    """
    return country.strip().lower().replace(" ", "_")


def get_country_output_path(country: str) -> Path:
    """
    Return the embedding output path for one country.
    """
    filename = f"{normalize_country_name(country)}.json"
    return EMBEDDED_DATA_DIR / filename


def build_text(document: dict) -> str:
    """
    Combine document metadata and content into the text
    that will be converted into an embedding.
    """
    parts = [
        document.get("country"),
        document.get("destination"),
        document.get("section"),
        document.get("subsection"),
        document.get("text"),
    ]

    return " ".join(
        str(part) for part in parts if part
    )


def create_model(
    model_name: str = MODEL_NAME,
) -> SentenceTransformer:
    """
    Load the sentence-transformer embedding model.
    """
    print(f"Loading embedding model: {model_name}")

    return SentenceTransformer(model_name)


def embed_country(
    country: str,
    input_path: Path | str,
    model_name: str = MODEL_NAME,
) -> Path:
    """
    Generate embeddings for all chunks of one country.

    Args:
        country:
            Country currently being embedded.

        input_path:
            JSON file produced by the chunking stage.

        model_name:
            Sentence-transformer model to use.

    Returns:
        Path to the JSON file containing the documents
        and their embeddings.
    """
    country = country.strip()
    input_path = Path(input_path)

    if not country:
        raise ValueError("Country must not be empty.")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Chunked country file was not found: {input_path}"
        )

    print(f"Loading chunks for {country}...")

    with input_path.open(encoding="utf-8") as file:
        documents = json.load(file)

    if not isinstance(documents, list):
        raise ValueError(
            f"Expected a list of documents in {input_path}"
        )

    if not documents:
        raise ValueError(
            f"No documents were found for {country}"
        )

    texts = [
        build_text(document)
        for document in documents
    ]

    model = create_model(model_name)

    print(
        f"Generating embeddings for "
        f"{len(documents)} {country} chunks..."
    )

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embedded_documents = []

    for document, embedding in zip(
        documents,
        embeddings,
    ):
        embedded_document = document.copy()

        embedded_document["embedding"] = (
            embedding.tolist()
        )

        embedded_documents.append(
            embedded_document
        )

    output_path = get_country_output_path(country)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            embedded_documents,
            file,
            ensure_ascii=False,
        )

    print(
        f"Saved {len(embedded_documents)} embedded "
        f"documents for {country} to {output_path}"
    )

    return output_path


if __name__ == "__main__":
    embed_country(
        country="Japan",
        input_path="data/processed/chunks/japan.json",
    )

import hashlib
import json
from pathlib import Path


CHUNKED_DATA_DIR = Path("data/processed/chunks")

MAX_LENGTH = 1500
OVERLAP = 400


def normalize_country_name(country: str) -> str:
    """
    Convert a country name into a safe filename.

    Example:
        "New Zealand" -> "new_zealand"
    """
    return country.strip().lower().replace(" ", "_")


def get_country_output_path(country: str) -> Path:
    """
    Return the chunked output path for one country.
    """
    filename = f"{normalize_country_name(country)}.json"
    return CHUNKED_DATA_DIR / filename


def split_text(
    text: str,
    max_length: int = MAX_LENGTH,
    overlap: int = OVERLAP,
) -> list[str]:
    """
    Split text into overlapping character-based chunks.
    """
    if max_length <= 0:
        raise ValueError("max_length must be greater than zero.")

    if overlap < 0:
        raise ValueError("overlap must not be negative.")

    if overlap >= max_length:
        raise ValueError(
            "overlap must be smaller than max_length."
        )

    text = text.strip()

    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_length
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def create_document_id(
    document: dict,
    chunk_index: int,
) -> str:
    """
    Create a deterministic and globally unique document ID.

    The ID is based on:
        - country
        - destination
        - section
        - subsection
        - chunk position

    The same chunk receives the same ID when the pipeline
    is executed again.
    """
    identity = "|".join(
        [
            str(document.get("country") or ""),
            str(document.get("destination") or ""),
            str(document.get("place_type") or ""),
            str(document.get("section") or ""),
            str(document.get("subsection") or ""),
            str(chunk_index),
        ]
    )

    return hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()


def chunk_country(
    country: str,
    input_path: Path | str,
    max_length: int = MAX_LENGTH,
    overlap: int = OVERLAP,
) -> Path:
    """
    Split processed documents for one country into chunks.

    Args:
        country:
            Country currently being processed.

        input_path:
            JSON file produced by the processing stage.

        max_length:
            Maximum number of characters in each chunk.

        overlap:
            Number of characters repeated between chunks.

    Returns:
        Path to the chunked JSON file.
    """
    country = country.strip()
    input_path = Path(input_path)

    if not country:
        raise ValueError("Country must not be empty.")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Processed country file was not found: {input_path}"
        )

    print(f"Chunking processed documents for {country}...")

    with input_path.open(encoding="utf-8") as file:
        documents = json.load(file)

    if not isinstance(documents, list):
        raise ValueError(
            f"Expected a list of documents in {input_path}"
        )

    chunked_documents = []

    for document in documents:
        text = document.get("text") or ""

        chunks = split_text(
            text=text,
            max_length=max_length,
            overlap=overlap,
        )

        for chunk_index, chunk in enumerate(chunks):
            new_document = document.copy()

            new_document["id"] = create_document_id(
                document=document,
                chunk_index=chunk_index,
            )

            new_document["chunk_index"] = chunk_index
            new_document["text"] = chunk

            chunked_documents.append(new_document)

    if not chunked_documents:
        raise ValueError(
            f"No chunks were produced for {country}"
        )

    output_path = get_country_output_path(country)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            chunked_documents,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Country: {country}")
    print(f"Before chunking: {len(documents)} documents")
    print(f"After chunking: {len(chunked_documents)} chunks")
    print(f"Saved chunked documents to {output_path}")

    return output_path


if __name__ == "__main__":
    chunk_country(
        country="Japan",
        input_path="data/processed/countries/japan.json",
    )


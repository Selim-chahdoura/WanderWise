import json
import re
from pathlib import Path


PROCESSED_DATA_DIR = Path("data/processed/countries")


def normalize_country_name(country: str) -> str:
    """
    Convert a country name into a safe filename.

    Example:
        "New Zealand" -> "new_zealand"
    """
    return country.strip().lower().replace(" ", "_")


def get_country_output_path(country: str) -> Path:
    """
    Return the processed output path for one country.
    """
    filename = f"{normalize_country_name(country)}.json"
    return PROCESSED_DATA_DIR / filename


def split_sections(text: str) -> list[dict]:
    """
    Split raw Wikivoyage text into sections and subsections.

    Wikivoyage headings look like:

        == See ==
        === Museums ===

    The number of equal signs determines the heading level.
    """
    pattern = re.compile(
        r"^(==+)\s*(.*?)\s*\1\s*$",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(text))
    sections = []

    for index, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()

        start = match.end()

        if index + 1 < len(matches):
            end = matches[index + 1].start()
        else:
            end = len(text)

        sections.append(
            {
                "title": title,
                "level": level,
                "text": text[start:end].strip(),
            }
        )

    return sections


def clean_text(text: str) -> str:
    """
    Remove common Wikivoyage markup from section text.
    """
    text = re.sub(
        r"\{\{.*?\}\}",
        "",
        text,
        flags=re.DOTALL,
    )

    text = re.sub(
        r"\[\[[^|\]]+\|([^\]]+)\]\]",
        r"\1",
        text,
    )

    text = re.sub(
        r"\[\[([^\]]+)\]\]",
        r"\1",
        text,
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = re.sub(
        r"^\s*[*#;-]+\s*$",
        "",
        text,
        flags=re.MULTILINE,
    )

    text = text.replace("'''", "")
    text = text.replace("''", "")

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def process_country(
    country: str,
    input_path: Path | str,
) -> Path:
    """
    Process the extracted pages for one country.

    Args:
        country:
            Country currently being processed.

        input_path:
            JSON file produced by the extraction stage.

    Returns:
        Path to the processed JSON file.
    """
    country = country.strip()
    input_path = Path(input_path)

    if not country:
        raise ValueError("Country must not be empty.")

    if not input_path.exists():
        raise FileNotFoundError(
            f"Extracted country file was not found: {input_path}"
        )

    print(f"Processing extracted pages for {country}...")

    with input_path.open(encoding="utf-8") as file:
        pages = json.load(file)

    if not isinstance(pages, list):
        raise ValueError(
            f"Expected a list of extracted pages in {input_path}"
        )

    documents = []

    for page in pages:
        current_section = None
        current_subsection = None

        raw_text = page.get("text") or ""

        for section in split_sections(raw_text):
            if section["level"] == 2:
                current_section = section["title"]
                current_subsection = None
            else:
                current_subsection = section["title"]

            cleaned_text = clean_text(section["text"])

            if not cleaned_text:
                continue

            if len(cleaned_text) < 100:
                continue

            documents.append(
                {
                    "country": page["country"],
                    "destination": page["destination"],
                    "place_type": page["place_type"],
                    "section": current_section,
                    "subsection": current_subsection,
                    "text": cleaned_text,
                }
            )

    if not documents:
        raise ValueError(
            f"No valid documents were produced for {country}"
        )

    output_path = get_country_output_path(country)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Saved {len(documents)} processed documents "
        f"for {country} to {output_path}"
    )

    return output_path


if __name__ == "__main__":
    process_country(
        country="Japan",
        input_path="data/raw/countries/japan.json",
    )
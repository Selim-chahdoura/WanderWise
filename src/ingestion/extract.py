import bz2
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


DUMP_PATH = Path("data/raw/wikivoyage.xml.bz2")
RAW_DATA_DIR = Path("data/raw/countries")


def normalize_country_name(country: str) -> str:
    """
    Convert a country name into a safe filename.

    Example:
        "New Zealand" -> "new_zealand"
    """
    return country.strip().lower().replace(" ", "_")


def get_country_output_path(country: str) -> Path:
    """
    Return the raw output path for one country.
    """
    filename = f"{normalize_country_name(country)}.json"
    return RAW_DATA_DIR / filename


def get_pages(dump_path: Path = DUMP_PATH) -> dict[str, str]:
    """
    Read the Wikivoyage XML dump and return a dictionary in which:

        key   = Wikivoyage page title
        value = raw Wikivoyage page text
    """
    pages = {}

    with bz2.open(dump_path, "rb") as file:
        for _, elem in ET.iterparse(file, events=("end",)):
            if elem.tag.endswith("page"):
                title = elem.find("./{*}title")
                text = elem.find("./{*}revision/{*}text")

                if title is not None and title.text:
                    pages[title.text] = text.text if text is not None else ""

                elem.clear()

    return pages


def get_cities(country_text: str) -> list[str]:
    """
    Extract city links from the Cities section of a country article.
    """
    match = re.search(
        r"==\s*Cities\s*==(.*?)(?=^==[^=]|\Z)",
        country_text,
        flags=re.DOTALL | re.MULTILINE | re.IGNORECASE,
    )

    if not match:
        return []

    cities_section = match.group(1)

    links = re.findall(
        r"\[\[([^|\]#]+)",
        cities_section,
    )

    return list(dict.fromkeys(link.strip() for link in links))


def extract_country(
    country: str,
    dump_path: Path = DUMP_PATH,
) -> Path:
    """
    Extract one country and its cities from the Wikivoyage dump.

    Returns:
        Path to the generated JSON file.
    """
    dump_path = Path(dump_path)
    country = country.strip()
    
    if not country:
        raise ValueError("Country must not be empty.")

    if not dump_path.exists():
        raise FileNotFoundError(
            f"Wikivoyage dump was not found: {dump_path}"
        )

    print(f"Reading Wikivoyage dump for {country}...")

    pages = get_pages(dump_path)
    country_text = pages.get(country)

    if not country_text:
        raise ValueError(
            f"No Wikivoyage page was found for country: {country}"
        )

    extracted = [
        {
            "country": country,
            "destination": None,
            "place_type": "country",
            "title": country,
            "text": country_text,
        }
    ]

    cities = get_cities(country_text)

    print(f"{country}: found {len(cities)} city links")

    extracted_city_count = 0

    for city in cities:
        city_text = pages.get(city)

        if not city_text:
            print(f"Skipping missing city page: {city}")
            continue

        extracted.append(
            {
                "country": country,
                "destination": city,
                "place_type": "city",
                "title": city,
                "text": city_text,
            }
        )

        extracted_city_count += 1

    output_path = get_country_output_path(country)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(extracted, file, ensure_ascii=False, indent=2)

    print(
        f"Saved {len(extracted)} pages for {country} "
        f"to {output_path}"
    )
    print(f"Successfully extracted {extracted_city_count} city pages")

    return output_path


if __name__ == "__main__":
    extract_country("Japan")
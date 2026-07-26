import bz2
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


dump_path = Path("data/raw/wikivoyage.xml.bz2")
output_path = Path("data/raw/extracted_pages.json")

countries = [
    "Tunisia",
    "Morocco",
    "Portugal",
    "Thailand",
    "Japan",
    "Mauritius"
]


def get_pages():
    pages = {}

    with bz2.open(dump_path, "rb") as file:
        for _, elem in ET.iterparse(file, events=("end",)):
            if elem.tag.endswith("page"):
                title = elem.find("./{*}title")
                text = elem.find("./{*}revision/{*}text")

                if title is not None:
                    pages[title.text] = text.text if text is not None else ""

                elem.clear()

    return pages


def get_cities(country_text):
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


def extract_pages():
    print("Reading Wikivoyage dump...")

    pages = get_pages()
    extracted = []

    for country in countries:
        country_text = pages.get(country)

        if not country_text:
            continue

        extracted.append({
            "country": country,
            "destination": None,
            "place_type": "country",
            "title": country,
            "text": country_text,
        })

        cities = get_cities(country_text)

        print(f"{country}: found {len(cities)} cities")

        for city in cities:
            city_text = pages.get(city)

            if not city_text:
                continue

            extracted.append({
                "country": country,
                "destination": city,
                "place_type": "city",
                "title": city,
                "text": city_text,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(extracted, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(extracted)} pages to {output_path}")


if __name__ == "__main__":
    extract_pages()
import json
import re
from pathlib import Path


input_path = Path("data/raw/extracted_pages.json")
output_path = Path("data/processed/documents.json")


def split_sections(text):
    pattern = re.compile(
        r"^(==+)\s*(.*?)\s*\1\s*$",
        re.MULTILINE,
    )

    matches = list(pattern.finditer(text))
    sections = []

    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        sections.append({
            "title": title,
            "level": level,
            "text": text[start:end].strip(),
        })

    return sections


def clean_text(text):
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)

    text = text.replace("'''", "")
    text = text.replace("''", "")

    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def process_pages():
    with open(input_path, encoding="utf-8") as file:
        pages = json.load(file)

    documents = []

    for page in pages:
        current_section = None

        for section in split_sections(page["text"]):
            if section["level"] == 2:
                current_section = section["title"]
                subsection = None
            else:
                subsection = section["title"]

            text = clean_text(section["text"])

            if not text:
                continue
            if len(text) < 100:
                continue
            documents.append({
                "country": page["country"],
                "destination": page["destination"],
                "place_type": page["place_type"],
                "section": current_section,
                "subsection": subsection,
                "text": text,
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)

    print(f"Saved {len(documents)} documents to {output_path}")


if __name__ == "__main__":
    process_pages()
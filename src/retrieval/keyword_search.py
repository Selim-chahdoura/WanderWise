import json
from pathlib import Path

from minsearch import Index


data_path = Path("data/processed/chunked_documents.json")

def load_documents():
    with open(data_path, encoding="utf-8") as file:
        return json.load(file)

def create_index(documents): 
    index = Index(
    text_fields=["country", "destination", "section", "subsection", "text"],
    keyword_fields=["country", "place_type", "destination"]
    )
    index.fit(documents)
    return index

boost = {
        "country": 1.5,
        "destination": 3.0,
        "section": 2.0,
        "subsection": 2.0,
        "text": 1.0,
    }

def search(index, query, boost_dict=None):
    return index.search(
        query=query,
        boost_dict=boost_dict,
        num_results=5,
    )

if __name__ == "__main__":
    documents = load_documents()
    index = create_index(documents)

    results = search(
        index,
        "How can I get around Tunis?",
    )

    for result in results:
        print()
        print(result["country"])
        print(result["destination"])
        print(result["section"])
        print(result["subsection"])
        print(result["text"][:300])
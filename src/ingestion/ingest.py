from pathlib import Path

import requests


dump_url = (
    "https://dumps.wikimedia.org/enwikivoyage/latest/"
    "enwikivoyage-latest-pages-articles.xml.bz2"
)

data_dir = Path("data/raw")
dump_path = data_dir / "wikivoyage.xml.bz2"


def download_dump():
    data_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading Wikivoyage dump...")

    response = requests.get(
        dump_url,
        headers={
            "User-Agent": "WanderWise/0.1 "
        },
        stream=True,
        timeout=60,
    )

    response.raise_for_status()

    with open(dump_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)

    print(f"Saved to {dump_path}")


if __name__ == "__main__":
    download_dump()
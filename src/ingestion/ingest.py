from pathlib import Path

import requests


DUMP_URL = (
    "https://dumps.wikimedia.org/enwikivoyage/latest/"
    "enwikivoyage-latest-pages-articles.xml.bz2"
)

DATA_DIR = Path("data/raw")
DUMP_PATH = DATA_DIR / "wikivoyage.xml.bz2"


def download_dump(force: bool = False) -> Path:
    """
    Download the Wikivoyage dump when it does not already exist.

    Args:
        force:
            When True, download the dump again even if a local
            copy already exists.

    Returns:
        Path to the local Wikivoyage dump.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if DUMP_PATH.exists() and not force:
        print(f"Wikivoyage dump already exists: {DUMP_PATH}")
        print("Skipping download.")
        return DUMP_PATH

    print("Downloading Wikivoyage dump...")

    response = requests.get(
        DUMP_URL,
        headers={
            "User-Agent": "WanderWise/0.1"
        },
        stream=True,
        timeout=60,
    )

    response.raise_for_status()

    temporary_path = DUMP_PATH.with_suffix(
        DUMP_PATH.suffix + ".part"
    )

    try:
        with temporary_path.open("wb") as file:
            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    file.write(chunk)

        temporary_path.replace(DUMP_PATH)

    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    print(f"Saved Wikivoyage dump to {DUMP_PATH}")

    return DUMP_PATH


if __name__ == "__main__":
    download_dump()
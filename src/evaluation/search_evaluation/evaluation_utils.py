import json
from pathlib import Path


ground_truth_path = Path(
    "data/evaluation/generated_ground_truth.json"
)


def load_ground_truth():
    with open(ground_truth_path, "r", encoding="utf-8") as file:
        return json.load(file)


def hit_rate(retrieved_ids, relevant_ids):
    return int(
        any(
            document_id in relevant_ids
            for document_id in retrieved_ids
        )
    )


def reciprocal_rank(retrieved_ids, relevant_ids):
    for rank, document_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if document_id in relevant_ids:
            return 1 / rank

    return 0


def calculate_metrics(all_retrieved_ids, all_relevant_ids):
    hits = []
    reciprocal_ranks = []

    for retrieved_ids, relevant_ids in zip(
        all_retrieved_ids,
        all_relevant_ids,
    ):
        hits.append(
            hit_rate(retrieved_ids, relevant_ids)
        )

        reciprocal_ranks.append(
            reciprocal_rank(
                retrieved_ids,
                relevant_ids,
            )
        )

    return {
        "hit_rate": sum(hits) / len(hits),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
    }
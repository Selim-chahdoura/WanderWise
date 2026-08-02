import itertools

from src.evaluation.evaluation_utils import (
    hit_rate,
    load_ground_truth,
    reciprocal_rank,
)
from src.retrieval.keyword_search import search as keyword_search
from src.retrieval.index_documents import connect


number_of_results = 5


def evaluate_keyword(
    connection,
    ground_truth,
    destination_weight,
    section_weight,
    subsection_weight,
    text_weight,
):
    hits = []
    reciprocal_ranks = []

    for item in ground_truth:
        results = keyword_search(
            connection=connection,
            query=item["question"],
            num_results=number_of_results,
            destination_weight=destination_weight,
            section_weight=section_weight,
            subsection_weight=subsection_weight,
            text_weight=text_weight,
        )

        retrieved_ids = [
            str(result[0])
            for result in results
        ]

        relevant_ids = [
            str(document_id)
            for document_id in item["relevant_document_ids"]
        ]

        hits.append(
            hit_rate(retrieved_ids, relevant_ids)
        )

        reciprocal_ranks.append(
            reciprocal_rank(retrieved_ids, relevant_ids)
        )

    return {
        "hit_rate": sum(hits) / len(hits),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
    }


if __name__ == "__main__":
    ground_truth = load_ground_truth()

    weight_values = [0.1, 0.2, 0.5, 0.7, 1.0]

    combinations = itertools.product(
        weight_values,
        weight_values,
        weight_values,
        weight_values,
    )

    evaluation_results = []

    with connect() as connection:
        for weights in combinations:
            (
                destination_weight,
                section_weight,
                subsection_weight,
                text_weight,
            ) = weights

            metrics = evaluate_keyword(
                connection=connection,
                ground_truth=ground_truth,
                destination_weight=destination_weight,
                section_weight=section_weight,
                subsection_weight=subsection_weight,
                text_weight=text_weight,
            )

            evaluation_results.append(
                {
                    "destination_weight": destination_weight,
                    "section_weight": section_weight,
                    "subsection_weight": subsection_weight,
                    "text_weight": text_weight,
                    "hit_rate": metrics["hit_rate"],
                    "mrr": metrics["mrr"],
                }
            )

    evaluation_results.sort(
        key=lambda result: (
            result["hit_rate"],
            result["mrr"],
        ),
        reverse=True,
    )

    print("Best configurations:")

    for result in evaluation_results[:10]:
        print(
            f"Hit Rate@5: {result['hit_rate']:.3f}, "
            f"MRR@5: {result['mrr']:.3f}, "
            f"destination={result['destination_weight']}, "
            f"section={result['section_weight']}, "
            f"subsection={result['subsection_weight']}, "
            f"text={result['text_weight']}"
        )
    print("Worst configurations:")
    for result in evaluation_results[-10:]:
        print(
            f"Hit Rate@5: {result['hit_rate']:.3f}, "
            f"MRR@5: {result['mrr']:.3f}, "
            f"destination={result['destination_weight']}, "
            f"section={result['section_weight']}, "
            f"subsection={result['subsection_weight']}, "
            f"text={result['text_weight']}"
        )
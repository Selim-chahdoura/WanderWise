from src.evaluation.evaluation_utils import (
    load_ground_truth,
    hit_rate,
    reciprocal_rank,
)
from src.retrieval.keyword_search import search as keyword_search
from src.retrieval.vector_search import search as vector_search
from src.retrieval.index_documents import connect


number_of_results = 5


def evaluate(search_function, connection, ground_truth):
    hits = []
    reciprocal_ranks = []

    for item in ground_truth:
        results = search_function(
            connection=connection,
            query=item["question"],
            num_results=number_of_results,
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

    with connect() as connection:
        keyword_metrics = evaluate(
            search_function=keyword_search,
            connection=connection,
            ground_truth=ground_truth,
        )

        vector_metrics = evaluate(
            search_function=vector_search,
            connection=connection,
            ground_truth=ground_truth,
        )

    print("Keyword search")
    print(f"Hit Rate@5: {keyword_metrics['hit_rate']:.3f}")
    print(f"MRR@5: {keyword_metrics['mrr']:.3f}")

    print()

    print("Vector search")
    print(f"Hit Rate@5: {vector_metrics['hit_rate']:.3f}")
    print(f"MRR@5: {vector_metrics['mrr']:.3f}")
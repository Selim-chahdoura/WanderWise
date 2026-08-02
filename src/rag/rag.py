import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.retrieval.index_documents import connect
from src.retrieval.vector_search import search as vector_search


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

model_name = "gpt-5-nano"
maximum_tool_calls = 3
maximum_iterations = 5
default_number_of_results = 5


instructions = """
You are WanderWise, a helpful travel assistant.

Use the travel_search tool whenever travel information is needed.

Rules:
- Base all travel facts only on information returned by the tool.
- You may call the travel_search tool at most 3 times.
- Review all previously retrieved information before searching again.
- Do not repeat the same or nearly identical search query.
- Stop searching once you have enough information to answer.
- Never use your own knowledge to add hotels, attractions, prices, or destination facts.
- If the tool returns no relevant information for the requested destination, say:
  "I don't have enough information about this destination in the WanderWise knowledge base."
- When information is unavailable, do not ask for budget, dates, preferences, or other details unless the available tool could use those details to find an answer.
- Do not claim that you can browse the web, check availability, compare current prices, or perform searches outside the WanderWise knowledge base.
- Do not offer to do something that the available tools cannot perform.
- Give a clear and practical final answer.
- Do not mention document IDs, retrieval scores, tool calls, searches, or internal tools.
""".strip()


travel_search_tool = {
    "type": "function",
    "name": "travel_search",
    "description": (
        "Search the WanderWise travel knowledge base for information "
        "about destinations, attractions, transport, accommodation, "
        "food, safety, and practical travel advice."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A focused query for the travel knowledge base.",
            },
            "number_of_results": {
                "type": "integer",
                "description": "The number of documents to retrieve.",
                "minimum": 1,
                "maximum": 10,
            },
        },
        "required": [
            "query",
            "number_of_results",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


def retrieve_documents(connection, query, number_of_results):
    return vector_search(
        connection=connection,
        query=query,
        num_results=number_of_results,
        )


def format_document(document):
    (
        document_id,
        country,
        destination,
        place_type,
        section,
        subsection,
        text,
        score,
    ) = document

    return f"""
Country: {country}
Destination: {destination or ""}
Section: {section}
Subsection: {subsection or ""}
Content:
{text}
""".strip()


def build_context(documents):
    return "\n\n".join(
        format_document(document)
        for document in documents
    )


def travel_search(
    connection,
    query,
    number_of_results,
    search_history,
):
    documents = retrieve_documents(
        connection=connection,
        query=query,
        number_of_results=number_of_results,
    )

    if not documents:
        result = "No relevant travel information was found."

        search_history.append(
            {
                "query": query,
                "retrieved_document_ids": [],
                "context": result,
            }
        )

        return result

    context = build_context(documents)

    retrieved_document_ids = [
        str(document[0])
        for document in documents
    ]

    search_history.append(
        {
            "query": query,
            "retrieved_document_ids": retrieved_document_ids,
            "context": context,
        }
    )

    return context


def get_tool_calls(response):
    return [
        item
        for item in response.output
        if item.type == "function_call"
    ]


def run_tool(
    tool_call,
    connection,
    search_history,
):
    arguments = json.loads(tool_call.arguments)

    if tool_call.name == "travel_search":
        return travel_search(
            connection=connection,
            query=arguments["query"],
            number_of_results=arguments.get(
                "number_of_results",
                default_number_of_results,
            ),
            search_history=search_history,
        )

    return f"Unknown tool: {tool_call.name}"


def create_tool_output(tool_call, result):
    return {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": result,
    }


def call_model(input_items):
    return client.responses.create(
        model=model_name,
        instructions=instructions,
        tools=[travel_search_tool],
        tool_choice="auto",
        input=input_items,
    )


def answer_question_with_trace(question):
    input_items = [
        {
            "role": "user",
            "content": question,
        }
    ]

    search_history = []
    tool_call_count = 0

    with connect() as connection:
        for _ in range(maximum_iterations):
            response = call_model(input_items)

            input_items.extend(response.output)

            tool_calls = get_tool_calls(response)

            if not tool_calls:
                return {
                    "answer": response.output_text,
                    "tool_call_count": tool_call_count,
                    "search_history": search_history,
                }

            for tool_call in tool_calls:
                if tool_call_count >= maximum_tool_calls:
                    input_items.append(
                        create_tool_output(
                            tool_call=tool_call,
                            result=(
                                "The search limit has been reached. "
                                "Use the information already retrieved "
                                "and provide the best supported answer."
                            ),
                        )
                    )
                    continue

                result = run_tool(
                    connection=connection,
                    tool_call=tool_call,
                    search_history=search_history,
                )

                tool_call_count += 1

                input_items.append(
                    create_tool_output(
                        tool_call=tool_call,
                        result=result,
                    )
                )

    return {
        "answer": (
            "I could not produce a reliable answer within "
            "the allowed number of search steps."
        ),
        "tool_call_count": tool_call_count,
        "search_history": search_history,
    }


def answer_question(question):
    result = answer_question_with_trace(question)

    return result["answer"]


if __name__ == "__main__":
    question = input("Ask WanderWise: ")

    answer = answer_question(question)

    print()
    print(answer)
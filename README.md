# WanderWise

WanderWise is an AI-powered travel knowledge assistant built with **Retrieval-Augmented Generation (RAG)**.

Users can ask natural-language questions about destinations, and WanderWise retrieves relevant travel information before generating a grounded answer.

Examples:

- What are the best things to do in Marrakech?
- How can I get around Bangkok?
- When is the best time to visit Sukhothai’s ruins?

## WanderWise v1

The first version of WanderWise focuses on building a complete, evaluated, and reproducible travel RAG application.

The current version includes:

- A Wikivoyage ingestion pipeline
- PostgreSQL with pgvector
- Keyword and vector search
- Retrieval evaluation
- An agentic RAG pipeline
- OpenAI answer generation
- Local LLM evaluation with Ollama

## Travel Knowledge Base

Travel information is collected from the official English Wikivoyage dump.

The data is:

- Downloaded from the official dump
- Extracted by country and destination
- Cleaned and structured
- Split into sections and chunks
- Stored in PostgreSQL
- Embedded for semantic search

## Search and Retrieval

WanderWise implements two retrieval approaches:

- PostgreSQL full-text keyword search
- Semantic vector search with pgvector

A ground-truth question dataset was generated locally with Ollama and used to evaluate both approaches using:

- Hit Rate@5
- Mean Reciprocal Rank at 5

### Search Evaluation

![Search evaluation results](images/search_evaluation.png)

The evaluation showed that vector search performs significantly better than keyword search and is therefore used as the main retrieval method in WanderWise v1.

## Agentic RAG

The vector search method is exposed to the LLM as a tool.

The model can decide:

- When retrieval is needed
- How to formulate the search query
- Whether additional context is required
- When it has enough information to answer

The search tool can be called up to three times.

```text
User Question
↓
LLM
↓
Travel Search Tool
↓
Vector Search
↓
Retrieved Context
↓
Grounded Answer
```

The final answers are generated using the OpenAI API.

## RAG Evaluation

The complete RAG pipeline was evaluated using:

- The user question
- A reference answer generated from the relevant document
- The generated RAG answer
- The exact retrieved context

A local Ollama model was used as an LLM judge.

The judge evaluated:

- Correctness
- Faithfulness
- Relevance
- Completeness

### LLM Evaluation

![LLM evaluation results](images/llm_evaluation.png)

The evaluation helps identify where the RAG pipeline performs well and where answer quality can still be improved.

## Monitoring

WanderWise will monitor application usage and performance.

This can include:

- User questions
- Generated answers
- Retrieved documents
- Response time
- Token usage
- LLM cost
- User feedback
- Timestamps

## Application

WanderWise v1 will include a simple web interface where users can ask travel questions and receive grounded answers.

The project will also be containerized with Docker to make it easy to reproduce and run.

## v1 Architecture

```text
Wikivoyage
↓
Data Ingestion
↓
PostgreSQL + pgvector
↓
Vector Search
↓
Agentic RAG
↓
OpenAI Answer Generation
↓
Evaluation
↓
User Interface
↓
Monitoring
```

## Goal of v1

The goal of WanderWise v1 is to build a small, complete, evaluated, and reproducible travel RAG application.

The focus is on building a strong foundation before adding more advanced travel features.

## Future Versions

### WanderWise v2 — Travel Data Platform

The next version can include:

- More destinations
- Additional travel data sources
- Better metadata and filtering
- Improved retrieval
- Conversation history
- Additional agent tools

### WanderWise v3 — Live Travel Intelligence

Future versions can integrate live external data such as:

- Weather
- Currency information
- Transportation data
- Travel APIs
- Real-time destination information

This foundation can later support recommendations, itinerary planning, personalization, and a more complete AI travel assistant.

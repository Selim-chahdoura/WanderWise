# WanderWise

WanderWise is an AI-powered travel knowledge assistant built with **Retrieval-Augmented Generation (RAG)**.

Users can ask natural-language questions about destinations, and WanderWise retrieves relevant travel information before generating a grounded answer.

Examples:

- What are the best things to do in Marrakech?
- How can I get around Bangkok?
- Which areas of Lisbon are known for nightlife?
- What should I know before visiting Morocco?

## WanderWise v1

The first version of WanderWise focuses on building a complete and evaluated travel RAG application.

### Travel Knowledge Base

Travel information is collected from **Wikivoyage** through a reproducible ingestion pipeline.

The data is:

- Downloaded from the official Wikivoyage dump
- Extracted by country and destination
- Cleaned and structured
- Split into sections and chunks
- Prepared for search and retrieval

### Search & Retrieval

WanderWise will experiment with multiple retrieval approaches:

- Keyword Search
- Vector Search
- Hybrid Search

The goal is to retrieve the most relevant travel information for each user question.

### Evaluation

The retrieval system will be evaluated using a ground-truth question dataset.

Different retrieval approaches will be compared using metrics such as:

- Hit Rate
- Mean Reciprocal Rank (MRR)

The RAG answers will also be evaluated to understand how well the system uses the retrieved information and how relevant the generated answers are.

### RAG

The final retrieval pipeline will be connected to an LLM.

User Question  
↓  
Search Travel Knowledge Base  
↓  
Retrieve Relevant Documents  
↓  
Build Context  
↓  
LLM  
↓  
Grounded Answer + Sources

The goal is to generate useful travel answers based primarily on retrieved information rather than relying only on the LLM's internal knowledge.

### Monitoring

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

Users will also be able to provide simple feedback on whether an answer was helpful.

### Application

WanderWise v1 will include a simple web interface where users can ask travel-related questions and receive grounded answers with sources.

The project will also be containerized with Docker to make the application easy to reproduce and run.

## v1 Architecture

Wikivoyage  
↓  
Data Ingestion  
↓  
Travel Knowledge Base  
↓  
Keyword + Vector Search  
↓  
Hybrid Retrieval  
↓  
Evaluation  
↓  
RAG  
↓  
Answer + Sources  
↓  
User Interface  
↓  
Monitoring & Feedback

## Goal of v1

The goal of WanderWise v1 is to build a small, complete, evaluated, and reproducible travel RAG application.

The focus is on building a strong foundation before adding more complex travel features.

## Future Versions

### WanderWise v2  Travel Data Platform

The next version will expand the data layer with:

- Structured destination data
- PostgreSQL
- Larger data ingestion pipelines
- More countries and destinations
- Better metadata and filtering
- Additional travel data sources

### WanderWise v3  Live Travel Intelligence

WanderWise will then start integrating live external data such as:

- Weather
- Currency information
- Transportation data
- Travel APIs
- Other real-time destination information

Future versions can build on this foundation to add destination recommendations, itinerary planning, personalization, and eventually a more complete AI travel assistant.

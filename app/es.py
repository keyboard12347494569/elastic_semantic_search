# app/es.py

import os
from typing import Dict
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Configuration
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "people-index")
MAX_SIZE = int(os.getenv("MAX_SIZE", "100"))

# Load environment variables from .env file
load_dotenv()

# Initialize Elasticsearch client
es = Elasticsearch(ES_URL)


def execute_search(dsl: Dict[str, any]) -> Dict[str, any]:
    """
    Executes a DSL query against Elasticsearch.

    Args:
        dsl (dict): The Elasticsearch query in the form of a dictionary, containing the query, aggregation,
                    size, and sorting parameters.

    Returns:
        dict: The search result from Elasticsearch containing the matching documents and any aggregations.

    Note:
        - The query is executed against the index specified in the `dsl` argument or the default index `ES_INDEX`.
        - The `size` parameter is enforced to respect the `MAX_SIZE` limit set in the configuration.
        - If the query is an aggregation-only query, the `size` is set to 0.
    """
    # Extract index from DSL, using the default index if not specified
    index = dsl.get("index", ES_INDEX)

    # Filter the DSL to include only valid parameters: query, aggs, size, and sort
    body = {k: v for k, v in dsl.items() if k in {"query", "aggs", "size", "sort"}}

    # If it's an aggregation-only query (no size specified), set size to 0
    if "aggs" in body and "size" not in body:
        body["size"] = 0

    # Enforce the maximum size limit for query results
    if body.get("size", 10) > MAX_SIZE:
        body["size"] = MAX_SIZE

    # Execute the search query against Elasticsearch and return the results
    return es.search(index=index, body=body)

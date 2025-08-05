import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Configuration
ES_URL = os.getenv("ES_URL", "http://localhost:9200")
ES_INDEX = os.getenv("ES_INDEX", "people-index")
MAX_SIZE = int(os.getenv("MAX_SIZE", "100"))

# Load environment variables from .env
load_dotenv()

es = Elasticsearch(ES_URL)


def execute_search(dsl: dict):
    index = dsl.get("index", ES_INDEX)
    body = {k: v for k, v in dsl.items() if k in {"query", "aggs", "size", "sort"}}
    if "aggs" in body and "size" not in body:
        body["size"] = 0
    if body.get("size", 10) > MAX_SIZE:
        body["size"] = MAX_SIZE
    return es.search(index=index, body=body)

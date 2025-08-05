"""
Script to create or recreate an Elasticsearch index with a predefined mapping.
"""

import json
import os
from elasticsearch import Elasticsearch, exceptions
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
ES_HOST = os.getenv("ES_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ES_INDEX", "people-index")

# Define the mapping for the index
MAPPING = {
    "mappings": {
        "properties": {
            "People": {"type": "text"},
            "Families": {"type": "text"},
            "Locations": {"type": "text"},
            "Events": {"type": "text"}
        }
    }
}


def connect_elasticsearch():
    """Create an Elasticsearch client."""
    return Elasticsearch(ES_HOST)


def delete_index_if_exists(es, index_name):
    """Delete index if it already exists."""
    if es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Deleting it...")
        es.indices.delete(index=index_name)
        print(f"Index '{index_name}' deleted.")


def create_index(es, index_name, mapping):
    """Create a new index with the given mapping."""
    print(f"Creating index '{index_name}' with mapping...")
    try:
        response = es.indices.create(index=index_name, body=mapping)
        print(json.dumps(response, indent=2))
        print(f"Index '{index_name}' created successfully.")
    except exceptions.RequestError as e:
        print(f"Failed to create index: {e.info}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


def main():
    """Main execution function."""
    es = connect_elasticsearch()
    delete_index_if_exists(es, INDEX_NAME)
    create_index(es, INDEX_NAME, MAPPING)


if __name__ == "__main__":
    main()

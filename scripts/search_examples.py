"""
Script to perform common Elasticsearch queries and aggregations on an Index.
"""

import os
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
ES_HOST = os.getenv("ES_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ES_INDEX", "people-index")

# Create an Elasticsearch client.
es = Elasticsearch(ES_HOST)


def search_by_event(term):
    """
    Search for documents where the 'Events' field matches the given term.
    """
    print(f"Searching for events containing: '{term}'")
    body = {
        "query": {
            "match": {
                "Events": term
            }
        }
    }
    res = es.search(index=INDEX_NAME, body=body)
    hits = res.get("hits", {}).get("hits", [])
    print_results(hits)


def search_by_location(location):
    """
    Search for people associated with a given location.
    """
    print(f"Searching for people in location: {location}")
    body = {
        "query": {
            "match": {
                "Locations": location
            }
        }
    }
    res = es.search(index=INDEX_NAME, body=body)
    hits = res.get("hits", {}).get("hits", [])
    print_results(hits)


def count_by_team():
    """
    Count the number of people per team (i.e., Families).
    """
    print("Counting people per team (Families):")
    body = {
        "size": 0,
        "aggs": {
            "team_count": {
                "terms": {
                    "field": "Families.keyword",
                    "size": 10
                }
            }
        }
    }
    res = es.search(index=INDEX_NAME, body=body)
    buckets = res.get("aggregations", {}).get("team_count", {}).get("buckets", [])
    for bucket in buckets:
        print(f"🔹 {bucket['key']}: {bucket['doc_count']}")


def top_locations_for_event(event_keyword):
    """
    Find the top 5 locations for a given event keyword.
    """
    print(f"Top 5 locations for event containing: '{event_keyword}'")
    body = {
        "size": 0,
        "query": {
            "match": {
                "Events": {
                    "query": event_keyword,
                    "operator": "and"
                }
            }
        },
        "aggs": {
            "top_locations": {
                "terms": {
                    "field": "Locations.keyword",
                    "size": 5
                }
            }
        }
    }
    res = es.search(index=INDEX_NAME, body=body)
    buckets = res.get("aggregations", {}).get("top_locations", {}).get("buckets", [])
    for bucket in buckets:
        print(f"{bucket['key']}: {bucket['doc_count']}")


def print_results(hits):
    """
    Pretty-print hits from a search result.
    """
    if not hits:
        print("No results found.")
        return

    for i, hit in enumerate(hits, 1):
        source = hit.get("_source", {})
        print(f"{i}. {source}")


if __name__ == "__main__":
    search_by_event("workshop")
    search_by_location("Vietnam")
    count_by_team()
    top_locations_for_event("cybersecurity")
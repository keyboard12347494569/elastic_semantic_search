"""
Bulk insert structured CSV data into an existing Elasticsearch index.
"""

import os
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
ES_HOST = os.getenv("ES_URL", "http://localhost:9200")
INDEX_NAME = os.getenv("ES_INDEX", "people-index")
CSV_PATH = os.getenv("CSV_PATH", "../data/data.csv")


def load_csv(csv_path):
    """Load the CSV into a pandas DataFrame."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")
    df = pd.read_csv(csv_path).fillna("")
    return df


def connect_elasticsearch():
    """Return an Elasticsearch client."""
    return Elasticsearch(ES_HOST)


def index_exists(es, index_name):
    """Check if the Elasticsearch index exists."""
    return es.indices.exists(index=index_name)


# Convert rows to ES bulk format
def generate_actions(df):
    """Yield Elasticsearch bulk insert actions from a DataFrame."""
    for _, row in df.iterrows():
        yield {
            "_index": INDEX_NAME,
            "_source": {
                "People": row["People"],
                "Families": row["Families"],
                "Locations": row["Locations"],
                "Events": row["Events"]
            }
        }


# Bulk upload
def bulk_insert(es, df):
    """Perform bulk insert into Elasticsearch."""
    try:
        response = helpers.bulk(es, generate_actions(df))
        print(f"Inserted {response[0]} documents into '{INDEX_NAME}'")
    except Exception as e:
        print(f"Bulk insert failed: {str(e)}")


def main():
    """Main execution function."""
    print("Starting CSV to Elasticsearch import...")
    df = load_csv(CSV_PATH)
    es = connect_elasticsearch()

    if not index_exists(es, INDEX_NAME):
        raise ValueError(f"Index '{INDEX_NAME}' does not exist. Please create it first.")

    bulk_insert(es, df)


if __name__ == "__main__":
    main()

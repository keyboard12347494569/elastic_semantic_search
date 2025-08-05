# ingest/bulk_load.py

import argparse
import hashlib
import sys
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import TransportError
from typing import Optional, Generator


def ensure_columns(df: pd.DataFrame, cols: list):
    """
    Ensures that the required columns are present in the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to check.
        cols (list): List of required column names.

    Raises:
        ValueError: If any required column is missing from the DataFrame.
    """
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the DataFrame by stripping whitespace, filling NaN values,
    and ensuring all columns are of string dtype.

    Args:
        df (pd.DataFrame): The DataFrame to normalize.

    Returns:
        pd.DataFrame: The normalized DataFrame.
    """
    # strip whitespace; fill NaN; ensure str dtype
    for c in df.columns:
        df[c] = df[c].astype(str).fillna("").str.strip()
    return df


def make_id(row: dict) -> str:
    """
    Generate a stable, idempotent ID from key fields.

    Args:
        row (dict): A dictionary containing the row data.

    Returns:
        str: A stable SHA256 hash-based ID.
    """
    # Stable id from key fields -> idempotent loads
    h = hashlib.sha256()
    key = f"{row.get('People','')}|{row.get('Families','')}|{row.get('Locations','')}|{row.get('Events','')}"
    h.update(key.encode("utf-8"))
    return h.hexdigest()


def gen_actions(df: pd.DataFrame, index: str, pipeline: Optional[str] = None, use_id: bool = True) -> Generator[dict, None, None]:
    """
    Generate the bulk actions for Elasticsearch.

    Args:
        df (pd.DataFrame): The DataFrame containing the data to be indexed.
        index (str): The target Elasticsearch index.
        pipeline (Optional[str]): The ingest pipeline to apply (optional).
        use_id (bool): Whether to set a document ID (default is True).

    Yields:
        dict: A dictionary representing an Elasticsearch bulk action.
    """
    for _, r in df.iterrows():
        src = {
            "People": r["People"],
            "Families": r["Families"],
            "Locations": r["Locations"],
            "Events": r["Events"],
        }
        action = {"_index": index, "_source": src}
        if use_id:
            action["_id"] = make_id(src)
        if pipeline:
            action["pipeline"] = pipeline
        yield action


def main():
    """
    Main function to load data from a CSV file into Elasticsearch using bulk API.

    Parses command-line arguments, reads the CSV file, ensures required columns,
    normalizes the data, and performs the bulk insert into Elasticsearch.
    """
    # Argument parser setup
    p = argparse.ArgumentParser(description="Bulk load CSV into Elasticsearch.")
    p.add_argument("--es", default="http://localhost:9200", help="Elasticsearch URL")
    p.add_argument("--csv", default="data/data.csv", help="Path to CSV file")
    p.add_argument("--index", default="people-index", help="Target index name")
    p.add_argument("--pipeline", default="people_loc_split", help="Ingest pipeline (or '' to disable)")
    p.add_argument("--chunk-size", type=int, default=2000, help="Bulk chunk size")
    p.add_argument("--request-timeout", type=int, default=120, help="ES request timeout (seconds)")
    p.add_argument("--no-id", action="store_true", help="Do not set document _id (not idempotent)")
    args = p.parse_args()

    # Elasticsearch client setup
    es = Elasticsearch(args.es, request_timeout=args.request_timeout)

    # Read the CSV file into a DataFrame
    try:
        df = pd.read_csv(args.csv)
    except Exception as e:
        print(f"Failed to read CSV: {e}", file=sys.stderr)
        sys.exit(1)

    # Ensure required columns are present
    required = ["People", "Families", "Locations", "Events"]
    ensure_columns(df, required)

    # Normalize the DataFrame
    df = normalize_df(df)

    # Set pipeline, if provided
    pipeline = args.pipeline if args.pipeline else None

    # Initialize counters for successful and failed operations
    success, failed = 0, 0
    try:
        # Perform bulk insert using Elasticsearch's streaming_bulk helper
        for ok, item in helpers.streaming_bulk(
            es,
            gen_actions(df, args.index, pipeline=pipeline, use_id=not args.no_id),
            chunk_size=args.chunk_size,
            max_retries=3,
            request_timeout=args.request_timeout,
        ):
            if ok:
                success += 1
            else:
                failed += 1
    except TransportError as e:
        print(f"Elasticsearch transport error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected error during bulk: {e}", file=sys.stderr)
        sys.exit(3)

    # Output the results
    print(f"Done. Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()

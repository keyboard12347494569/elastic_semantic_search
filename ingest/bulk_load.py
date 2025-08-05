# bulk_load.py
import argparse
import hashlib
import sys
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import TransportError


def ensure_columns(df, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def normalize_df(df):
    # strip whitespace; fill NaN; ensure str dtype
    for c in df.columns:
        df[c] = df[c].astype(str).fillna("").str.strip()
    return df


def make_id(row):
    # Stable id from key fields -> idempotent loads
    h = hashlib.sha256()
    key = f"{row.get('People','')}|{row.get('Families','')}|{row.get('Locations','')}|{row.get('Events','')}"
    h.update(key.encode("utf-8"))
    return h.hexdigest()


def gen_actions(df, index, pipeline=None, use_id=True):
    for _, r in df.iterrows():
        src = {
            "People": r["People"],
            "Families": r["Families"],
            "Locations": r["Locations"],
            "Events": r["Events"],
        }
        a = {"_index": index, "_source": src}
        if use_id:
            a["_id"] = make_id(src)
        if pipeline:
            a["pipeline"] = pipeline
        yield a


def main():
    p = argparse.ArgumentParser(description="Bulk load CSV into Elasticsearch.")
    p.add_argument("--es", default="http://localhost:9200", help="Elasticsearch URL")
    p.add_argument("--csv", default="data/data.csv", help="Path to CSV file")
    p.add_argument("--index", default="people-index", help="Target index name")
    p.add_argument("--pipeline", default="people_loc_split", help="Ingest pipeline (or '' to disable)")
    p.add_argument("--chunk-size", type=int, default=2000, help="Bulk chunk size")
    p.add_argument("--request-timeout", type=int, default=120, help="ES request timeout (seconds)")
    p.add_argument("--no-id", action="store_true", help="Do not set document _id (not idempotent)")
    args = p.parse_args()

    es = Elasticsearch(args.es, request_timeout=args.request_timeout)

    try:
        df = pd.read_csv(args.csv)
    except Exception as e:
        print(f"Failed to read CSV: {e}", file=sys.stderr)
        sys.exit(1)

    required = ["People", "Families", "Locations", "Events"]
    ensure_columns(df, required)
    df = normalize_df(df)

    pipeline = args.pipeline if args.pipeline else None

    # Bulk with streaming + progress
    success, failed = 0, 0
    try:
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

    print(f"Done. Success: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()

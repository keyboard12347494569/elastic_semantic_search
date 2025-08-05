# app/telemetry.py

import time
import json
import logging
from typing import Optional

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nl2es")


def log_query(nl: str, dsl: dict, ok: bool, hits_total: int | None, took_ms: int | None, error: str | None):
    """
    Logs the details of a query, including the natural language query, DSL query,
    result status, total hits, execution time, and any error that occurred.

    Args:
        nl (str): The natural language query from the user.
        dsl (dict): The corresponding DSL query.
        ok (bool): Whether the query was successful or not.
        hits_total (Optional[int]): The total number of hits found (can be None if not applicable).
        took_ms (Optional[int]): The time taken to process the query in milliseconds (can be None if not available).
        error (Optional[str]): Any error message generated during query execution (can be None if no error occurred).
    """

    # Log the query information as a JSON object with timestamp
    log.info(json.dumps({
        "ts": int(time.time()*1000),  # Current timestamp in milliseconds
        "nl_query": nl,               # The user's natural language query
        "dsl": dsl,                   # The corresponding DSL query
        "ok": ok,                     # Query success status
        "hits_total": hits_total,     # Total number of hits (if applicable)
        "took_ms": took_ms,           # Time taken in milliseconds (if available)
        "error": error                # Any error message (if applicable)
    }))

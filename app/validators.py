# app/validators.py

import os
from jsonschema import validate, ValidationError
from .schema import DSL_SCHEMA
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ES_INDEX = os.getenv("ES_INDEX", "people-index")

# Allowed index names and top-level keys for the DSL query
ALLOWED_INDEXES = {ES_INDEX}
ALLOWED_TOP_KEYS = {"index", "query", "aggs", "size", "sort", "_explain"}


def validate_dsl(dsl: Dict[str, any]) -> bool:
    """
    Validate the structure and contents of a DSL query.

    Args:
        dsl (dict): The DSL query to validate.

    Returns:
        bool: True if the DSL query is valid, raises ValueError if invalid.

    Raises:
        ValueError: If the index is not allowed, the schema is invalid, or disallowed operations are found.
    """
    # Check if the index is allowed
    if dsl.get("index") not in ALLOWED_INDEXES:
        raise ValueError("Index not allowed.")

    # Validate the DSL query against the predefined schema
    try:
        validate(instance=dsl, schema=DSL_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"DSL schema invalid: {e.message}")

    # Disallow write operations or scripts if they are present erroneously
    txt = str(dsl).lower()
    for bad in ["update_by_query", "delete", "script", "reindex"]:
        if bad in txt:
            raise ValueError(f"Disallowed operation: {bad}")

    # Return True if validation passes
    return True

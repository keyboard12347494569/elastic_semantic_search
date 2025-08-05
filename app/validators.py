from jsonschema import validate, ValidationError
from .schema import DSL_SCHEMA

ALLOWED_INDEXES = {"people-index"}
ALLOWED_TOP_KEYS = {"index","query","aggs","size","sort","_explain"}


def validate_dsl(dsl: dict):
    if dsl.get("index") not in ALLOWED_INDEXES:
        raise ValueError("Index not allowed.")
    try:
        validate(instance=dsl, schema=DSL_SCHEMA)
    except ValidationError as e:
        raise ValueError(f"DSL schema invalid: {e.message}")

    # Disallow write ops / scripts if ever present erroneously
    txt = str(dsl).lower()
    for bad in ["update_by_query", "delete", "script", "reindex"]:
        if bad in txt:
            raise ValueError(f"Disallowed operation: {bad}")

    return True

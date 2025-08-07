# app/schema.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

ES_INDEX = os.getenv("ES_INDEX", "people-index")

"""
It defines a JSON schema for validating the DSL query structure — ensuring index, query, and optional fields like size, aggs, etc., are well-formed.
"""
DSL_SCHEMA = {
  "type": "object",
  "properties": {
    "index": {"type": "string", "enum": [ES_INDEX]},
    "query": {"type": "object"},
    "aggs":  {"type": "object"},
    "size":  {"type": "integer", "minimum": 0, "maximum": 200},
    "sort":  {"type": "array", "items": {"type": "object"}},
    "_explain": {"type": "string"}
  },
  "required": ["index", "query"],
  "additionalProperties": True
}

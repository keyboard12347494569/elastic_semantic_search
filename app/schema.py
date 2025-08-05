# app/schema.py
"""
It defines a JSON schema for validating the DSL query structure — ensuring index, query, and optional fields like size, aggs, etc., are well-formed.
"""
DSL_SCHEMA = {
  "type": "object",
  "properties": {
    "index": {"type": "string", "enum": ["people-index"]},
    "query": {"type": "object"},
    "aggs":  {"type": "object"},
    "size":  {"type": "integer", "minimum": 0, "maximum": 200},
    "sort":  {"type": "array", "items": {"type": "object"}},
    "_explain": {"type": "string"}
  },
  "required": ["index", "query"],
  "additionalProperties": True
}

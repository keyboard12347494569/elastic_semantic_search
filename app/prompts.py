QUERY_SYS = """Translate NL to Elasticsearch DSL (JSON only) for index "people-index".
Fields:
- People (text, n-gram)
- Families (text, n-gram), Families_raw (keyword)
- Locations (text, n-gram), Locations_raw (keyword)
- Events (text, n-gram)
Rules:
- Use match/match_phrase for text search on People/Families/Locations/Events.
- For aggregations or exact buckets, use *_raw keyword fields (e.g., Locations_raw).
- Combine multiple conditions with bool.must.
- Default size to 10 unless size is specified or using pure aggs (size:0).
- Return ONLY JSON. No prose."""

FEWSHOTS = [
    ("Count people per team.",
     {"index":"people-index","size":0,"query":{"match_all":{}},"aggs":{"by_team":{"terms":{"field":"Families_raw","size":50}}}}),
    ("People in Tokyo who joined a workshop.",
     {"index":"people-index","query":{"bool":{"must":[{"match":{"Locations":"Tokyo, Japan"}},{"match":{"Events":"workshop"}}]}},"size":10}),
    ("Top 5 locations for cybersecurity training.",
     {"index":"people-index","size":0,"query":{"match":{"Events":{"query":"cybersecurity","operator":"and"}}},"aggs":{"top_locations":{"terms":{"field":"Locations_raw","size":5}}}}),
    ("list all those who lives in Vietnam",
     {"index":"people-index","query":{"match":{"Locations":"Vietnam"}},"size":100})
]

SUMM_SYS = "Summarize hits or aggregations briefly for a non-technical user. Only use those hits which are more relevant and answers user's query."

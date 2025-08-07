import os
from dotenv import load_dotenv

# ---------------------- Environment Setup ---------------------- #
load_dotenv()


PROMPT_TEMPLATE_PATH = os.getenv("SYS_PROMPT")


def load_prompt_template(file_path: str = PROMPT_TEMPLATE_PATH) -> str:
    """Load the LLM prompt template from file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


QUERY_SYS = load_prompt_template(PROMPT_TEMPLATE_PATH)

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

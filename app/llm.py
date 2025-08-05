import os, json
from openai import AzureOpenAI
from .prompts import QUERY_SYS, FEWSHOTS, SUMM_SYS
from dotenv import load_dotenv

# ---------------------- Environment Setup ---------------------- #
load_dotenv()

# Azure OpenAI Client Initialization
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

MODEL_DSL = os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT", "gpt-4o-mini")
MODEL_SUM = os.getenv("AZURE_OPENAI_COMPLETION_DEPLOYMENT", "gpt-4o-mini")


def build_messages(nl_query: str):
    msgs = [{"role":"system","content":QUERY_SYS}]
    for q, dsl in FEWSHOTS:
        msgs.append({"role":"user","content":q})
        msgs.append({"role":"assistant","content":json.dumps(dsl)})
    msgs.append({"role": "user", "content": nl_query})
    return msgs


def llm_to_dsl(nl_query: str) -> dict:
    resp = client.chat.completions.create(
        model=MODEL_DSL, temperature=0, messages=build_messages(nl_query)
    )
    text = resp.choices[0].message.content.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # repair pass
        fix = client.chat.completions.create(
            model=MODEL_DSL, temperature=0,
            messages=[
              {"role":"system","content":"Return ONLY valid JSON. Repair the following into a valid JSON object. No comments."},
              {"role":"user","content":text}
            ]
        )
        return json.loads(fix.choices[0].message.content.strip())


def summarize(nl_query: str, es_response: dict) -> str:
    payload = {
        "query": nl_query,
        "hits": [h.get("_source", {}) for h in es_response.get("hits", {}).get("hits", [])],
        "aggs": es_response.get("aggregations", {})
    }
    resp = client.chat.completions.create(
        model=MODEL_SUM, temperature=0,
        messages=[
          {"role":"system","content":SUMM_SYS},
          {"role":"user","content":json.dumps(payload)}
        ]
    )
    return resp.choices[0].message.content.strip()

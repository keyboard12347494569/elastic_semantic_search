import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.llm import llm_to_dsl, summarize
from app.validators import validate_dsl
from app.es import execute_search
from app.telemetry import log_query


class SearchRequest(BaseModel):
    query: str
    size: int | None = None
    summarize: bool = True


app = FastAPI(title="NL → ES DSL Search")


@app.post("/search")
def search(req: SearchRequest):
    try:
        dsl = llm_to_dsl(req.query)
        if req.size is not None:
            dsl["size"] = req.size
        validate_dsl(dsl)
        res = execute_search(dsl)
        hits_total = res.get("hits",{}).get("total",{}).get("value") or res.get("hits",{}).get("total")
        took = res.get("took")
        log_query(req.query, dsl, True, hits_total, took, None)
        return {
            "dsl": dsl,
            "es_meta": {"took_ms": took, "hits_total": hits_total},
            "hits": [h.get("_source",{}) for h in res.get("hits",{}).get("hits",[])],
            "aggs": res.get("aggregations"),
            "summary": summarize(req.query, res) if req.summarize else None
        }
    except Exception as e:
        log_query(req.query, {}, False, None, None, str(e))
        raise HTTPException(status_code=400, detail=str(e))

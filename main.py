# main.py

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from app.llm import llm_to_dsl, summarize
from app.validators import validate_dsl
from app.es import execute_search
from app.telemetry import log_query


class SearchRequest(BaseModel):
    """
    Pydantic model for validating search requests.

    Args:
        query (str): The natural language query to search.
        size (Optional[int]): The number of results to return (optional).
        summarize (bool): Whether to return a summary of the results (default is True).
    """
    query: str
    size: Optional[int] = 100
    summarize: bool = True


# Initialize FastAPI application
app = FastAPI(title="NL → ES DSL Search")


@app.post("/search")
def search(req: SearchRequest) -> Dict:
    """
    Search for documents in Elasticsearch based on a natural language query.

    Args:
        req (SearchRequest): The request payload containing the user's query and optional parameters.

    Returns:
        dict: The search results, including the DSL query, Elasticsearch metadata, hits, and a summary (if requested).

    Raises:
        HTTPException: If an error occurs during the process, a 400 HTTPException is raised with the error message.
    """
    try:
        # Convert the user's natural language query to a DSL query
        dsl = llm_to_dsl(req.query)

        # Set the size of the search if provided in the request
        if req.size is not None:
            dsl["size"] = req.size

        # Validate the DSL query to ensure it's well-formed
        validate_dsl(dsl)

        # Execute the search query on Elasticsearch
        res = execute_search(dsl)

        # Extract the total number of hits and the time taken for the query
        hits_total = res.get("hits", {}).get("total", {}).get("value") or res.get("hits", {}).get("total")
        took = res.get("took")

        # Log the query details for telemetry
        log_query(req.query, dsl, True, hits_total, took, None)

        # Return the search results, including DSL, metadata, hits, aggregations, and summary if requested
        return {
            "dsl": dsl,
            "es_meta": {"took_ms": took, "hits_total": hits_total},
            "hits": [h.get("_source",{}) for h in res.get("hits",{}).get("hits",[])],
            "aggs": res.get("aggregations"),
            "summary": summarize(req.query, res) if req.summarize else None
        }
    except Exception as e:
        # Log the error and raise an HTTP exception if something goes wrong
        log_query(req.query, {}, False, None, None, str(e))
        raise HTTPException(status_code=400, detail=str(e))

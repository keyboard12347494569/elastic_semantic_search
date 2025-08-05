import time, json, logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("nl2es")


def log_query(nl: str, dsl: dict, ok: bool, hits_total: int | None, took_ms: int | None, error: str | None):
    log.info(json.dumps({
        "ts": int(time.time()*1000),
        "nl_query": nl,
        "dsl": dsl,
        "ok": ok,
        "hits_total": hits_total,
        "took_ms": took_ms,
        "error": error
    }))

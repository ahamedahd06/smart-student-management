from datetime import datetime
from typing import Any


def serialize_doc(doc: dict | None) -> dict[str, Any]:
    if not doc:
        return {}
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out["id"] = str(v)
            continue
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def serialize_docs(docs: list[dict]) -> list[dict[str, Any]]:
    return [serialize_doc(d) for d in docs]

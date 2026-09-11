"""Persistence for Dhaal — MongoDB Atlas when MONGODB_URI is set (the backend
is serverless, so memory resets on cold starts), in-memory otherwise, and a
per-call failover so a mid-demo Atlas outage degrades instead of erroring.
"""

import os
import uuid
from datetime import datetime, timezone

from pymongo import MongoClient, ReturnDocument

import fixtures as FX


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _matches(doc: dict, filt: dict | None) -> bool:
    return all(doc.get(k) == v for k, v in (filt or {}).items())


class MemoryStore:
    name = "memory"

    def __init__(self):
        self.data: dict[str, dict] = {
            "checks": {}, "reports": {}, "indicators": {},
            "guardian_links": {}, "guardian_requests": {},
        }
        for ind in FX.SEED_INDICATORS:
            self.data["indicators"][ind["_id"]] = dict(ind)

    def insert(self, coll: str, doc: dict) -> dict:
        self.data[coll][doc["_id"]] = dict(doc)
        return doc

    def get(self, coll: str, doc_id: str) -> dict | None:
        d = self.data[coll].get(doc_id)
        return dict(d) if d else None

    def list(self, coll: str, filt: dict | None = None) -> list[dict]:
        return [dict(d) for d in self.data[coll].values() if _matches(d, filt)]

    def update(self, coll: str, doc_id: str, fields: dict) -> dict | None:
        d = self.data[coll].get(doc_id)
        if not d:
            return None
        d.update(fields)
        return dict(d)

    def indicators_map(self) -> dict:
        return {d["value"]: dict(d) for d in self.data["indicators"].values()}

    def upsert_indicator(self, value: str, itype: str, category: str) -> dict:
        for d in self.data["indicators"].values():
            if d["value"] == value:
                d["report_count"] += 1
                return dict(d)
        doc = {"_id": _id("ind"), "type": itype, "value": value,
               "report_count": 1, "first_seen": _now(), "category": category}
        self.data["indicators"][doc["_id"]] = doc
        return dict(doc)

    def active_name(self) -> str:
        return self.name


class MongoStore:
    name = "atlas"

    def __init__(self, uri: str):
        self.client = MongoClient(
            uri, serverSelectionTimeoutMS=3000, connectTimeoutMS=3000,
            socketTimeoutMS=8000,
        )
        self.db = self.client[os.getenv("DB_NAME", "dhaal")]
        self.client.admin.command("ping")
        self.db.indicators.create_index("value", unique=True)
        if self.db.indicators.count_documents({}) == 0:
            self.db.indicators.insert_many([dict(i) for i in FX.SEED_INDICATORS])

    def insert(self, coll: str, doc: dict) -> dict:
        self.db[coll].insert_one(dict(doc))
        return doc

    def get(self, coll: str, doc_id: str) -> dict | None:
        return self.db[coll].find_one({"_id": doc_id})

    def list(self, coll: str, filt: dict | None = None) -> list[dict]:
        return list(self.db[coll].find(filt or {}))

    def update(self, coll: str, doc_id: str, fields: dict) -> dict | None:
        return self.db[coll].find_one_and_update(
            {"_id": doc_id}, {"$set": fields}, return_document=ReturnDocument.AFTER
        )

    def indicators_map(self) -> dict:
        return {d["value"]: d for d in self.db.indicators.find({})}

    def upsert_indicator(self, value: str, itype: str, category: str) -> dict:
        return self.db.indicators.find_one_and_update(
            {"value": value},
            {"$inc": {"report_count": 1},
             "$setOnInsert": {"_id": _id("ind"), "type": itype, "value": value,
                              "first_seen": _now(), "category": category}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )

    def active_name(self) -> str:
        try:
            self.client.admin.command("ping")
            return self.name
        except Exception:
            return "memory"


class FailoverStore:
    """Try Atlas, fall back to memory per call — the demo never 500s on wifi."""

    _METHODS = ("insert", "get", "list", "update", "indicators_map", "upsert_indicator")

    def __init__(self, primary: MongoStore, shadow: MemoryStore):
        self.primary, self.shadow = primary, shadow

    def __getattr__(self, method):
        if method not in self._METHODS:
            raise AttributeError(method)

        def call(*args, **kwargs):
            try:
                return getattr(self.primary, method)(*args, **kwargs)
            except Exception as e:
                print(f"[store] atlas {method} failed ({type(e).__name__}) — memory fallback")
                return getattr(self.shadow, method)(*args, **kwargs)

        return call

    def active_name(self) -> str:
        return self.primary.active_name()


def get_store():
    uri = os.getenv("MONGODB_URI", "").strip()
    memory = MemoryStore()
    if not uri:
        return memory
    try:
        return FailoverStore(MongoStore(uri), memory)
    except Exception as e:
        print(f"[store] atlas unreachable at startup ({type(e).__name__}) — memory store")
        return memory

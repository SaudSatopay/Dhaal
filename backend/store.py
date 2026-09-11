"""Persistence for Dhaal — MongoDB Atlas when MONGODB_URI is set (the backend
is serverless, so memory resets on cold starts), in-memory otherwise, and a
per-call failover so a mid-demo Atlas outage degrades instead of erroring.
"""

import os
import threading
import time
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
        # defaultdict: new channel collections (wa_events, ivr_jobs, …) work
        # without registration, mirroring Mongo's create-on-write behavior.
        from collections import defaultdict
        self.data: dict[str, dict] = defaultdict(dict)
        for coll in ("checks", "reports", "indicators",
                     "guardian_links", "guardian_requests"):
            self.data[coll]  # seed the classic collections
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

    _cas_lock = threading.Lock()

    def insert_new(self, coll: str, doc: dict) -> bool:
        """Insert ONLY if the _id doesn't exist — single-winner creation."""
        with self._cas_lock:
            if doc["_id"] in self.data[coll]:
                return False
            self.data[coll][doc["_id"]] = dict(doc)
            return True

    def set_indicator_count(self, value: str, count: int) -> None:
        """Absolute repair (reconciliation): count derives from the ledger."""
        with self._cas_lock:
            for k, d in list(self.data["indicators"].items()):
                if d["value"] == value:
                    if count <= 0:
                        del self.data["indicators"][k]
                    else:
                        d["report_count"] = count
                    return

    def update_if(self, coll: str, doc_id: str, expect: dict,
                  fields: dict) -> dict | None:
        """Atomic check-and-set (H16): update ONLY if every `expect` field
        currently matches (None matches missing). Returns the updated doc or
        None — the single-winner primitive behind pair-code claims, outbox
        leases and contribution ledgers."""
        with self._cas_lock:
            d = self.data[coll].get(doc_id)
            if not d:
                return None
            for k, v in expect.items():
                if d.get(k) != v:
                    return None
            d.update(fields)
            return dict(d)

    def indicators_map(self) -> dict:
        return {d["value"]: dict(d) for d in self.data["indicators"].values()}

    def upsert_indicator(self, value: str, itype: str, category: str) -> dict:
        for d in self.data["indicators"].values():
            if d["value"] == value:
                d["report_count"] += 1
                d["last_seen"] = _now()  # freshness (H14): stale intel is visible
                return dict(d)
        doc = {"_id": _id("ind"), "type": itype, "value": value,
               "report_count": 1, "first_seen": _now(), "last_seen": _now(),
               "category": category}
        self.data["indicators"][doc["_id"]] = doc
        return dict(doc)

    def decrement_indicator(self, value: str) -> None:
        # withdraw one verification (H12); remove the indicator at zero
        for k, d in list(self.data["indicators"].items()):
            if d["value"] == value:
                d["report_count"] -= 1
                if d["report_count"] <= 0:
                    del self.data["indicators"][k]
                return

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
        # H14 guardian auth: token-hash and pair-code lookups must not scan
        self.db.guardian_links.create_index("guardian_token_sha256", sparse=True)
        self.db.guardian_links.create_index("ward_token_sha256", sparse=True)
        self.db.guardian_links.create_index("pair_code")
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

    def update_if(self, coll: str, doc_id: str, expect: dict,
                  fields: dict) -> dict | None:
        """Atomic check-and-set via Mongo's own find_one_and_update filter —
        {field: None} matches both explicit-null and missing, mirroring the
        memory store's semantics."""
        filt: dict = {"_id": doc_id}
        for k, v in expect.items():
            filt[k] = v if v is not None else {"$in": [None]}
        return self.db[coll].find_one_and_update(
            filt, {"$set": fields}, return_document=ReturnDocument.AFTER
        )

    def indicators_map(self) -> dict:
        return {d["value"]: d for d in self.db.indicators.find({})}

    def upsert_indicator(self, value: str, itype: str, category: str) -> dict:
        return self.db.indicators.find_one_and_update(
            {"value": value},
            {"$inc": {"report_count": 1},
             "$set": {"last_seen": _now()},  # freshness (H14)
             "$setOnInsert": {"_id": _id("ind"), "type": itype, "value": value,
                              "first_seen": _now(), "category": category}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )

    def decrement_indicator(self, value: str) -> None:
        # withdraw one verification (H12); remove the indicator at zero
        doc = self.db.indicators.find_one_and_update(
            {"value": value}, {"$inc": {"report_count": -1}},
            return_document=ReturnDocument.AFTER,
        )
        if doc and doc.get("report_count", 0) <= 0:
            self.db.indicators.delete_one({"_id": doc["_id"]})

    def insert_new(self, coll: str, doc: dict) -> bool:
        """Insert ONLY if the _id doesn't exist — single-winner creation."""
        from pymongo.errors import DuplicateKeyError
        try:
            self.db[coll].insert_one(dict(doc))
            return True
        except DuplicateKeyError:
            return False

    def set_indicator_count(self, value: str, count: int) -> None:
        """Absolute repair (reconciliation): count derives from the ledger."""
        if count <= 0:
            self.db.indicators.delete_one({"value": value})
        else:
            self.db.indicators.update_one({"value": value},
                                          {"$set": {"report_count": count}})

    def active_name(self) -> str:
        try:
            self.client.admin.command("ping")
            return self.name
        except Exception:
            return "memory"


class FailoverStore:
    """Try Atlas, fall back to memory per call — the demo never 500s on wifi.
    Honesty contract (H14): the memory shadow is NOT a replica; while degraded,
    reads may miss recent community intel and writes are not durable. The API
    layer surfaces this via recently_degraded()."""

    _METHODS = ("insert", "get", "list", "update", "update_if", "insert_new",
                "set_indicator_count", "indicators_map", "upsert_indicator",
                "decrement_indicator")
    DEGRADED_WINDOW_S = 60

    def __init__(self, primary: MongoStore, shadow: MemoryStore):
        self.primary, self.shadow = primary, shadow
        self._last_fallback: float | None = None

    def __getattr__(self, method):
        if method not in self._METHODS:
            raise AttributeError(method)

        def call(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                out = getattr(self.primary, method)(*args, **kwargs)
                print(f"[latency] atlas_ms={(time.perf_counter() - t0) * 1000:.0f} op={method}")
                return out
            except Exception as e:
                self._last_fallback = time.monotonic()
                print(f"[latency] atlas_ms={(time.perf_counter() - t0) * 1000:.0f} "
                      f"op={method} err={type(e).__name__} — memory fallback")
                return getattr(self.shadow, method)(*args, **kwargs)

        return call

    def recently_degraded(self) -> bool:
        return (self._last_fallback is not None
                and time.monotonic() - self._last_fallback < self.DEGRADED_WINDOW_S)

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
        # Atlas WAS configured — this memory store is a degraded stand-in, and
        # the API layer must say so rather than imply durable community intel.
        memory.recently_degraded = lambda: True  # type: ignore[attr-defined]
        return memory

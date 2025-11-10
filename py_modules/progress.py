import os
import json
from typing import Optional

try:
    # Optional import to infer progress from job registry if progress file isn't present yet
    from job_registry import get_jobs
except Exception:  # pragma: no cover - best-effort fallback
    get_jobs = None

BASE_DIR = os.path.join("outputs", "progress")
os.makedirs(BASE_DIR, exist_ok=True)


def _path(task_id: str) -> str:
    safe = "".join(c for c in task_id if c.isalnum() or c in ("-", "_")) or "default"
    return os.path.join(BASE_DIR, f"{safe}.json")


def set_progress(task_id: str, status: str, percent: int, extra: Optional[dict] = None) -> None:
    data = get_progress(task_id)
    data.update({
        "task_id": task_id,
        "status": status,
        "percent": int(max(0, min(100, percent))),
    })
    if extra:
        data.update(extra)
    try:
        with open(_path(task_id), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def set_canceled(task_id: str, message: str = "") -> None:
    data = get_progress(task_id)
    data.update({"status": "canceled", "percent": data.get("percent", 0), "canceled": True})
    if message:
        data["message"] = message
    try:
        with open(_path(task_id), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def is_canceled(task_id: str) -> bool:
    return bool(get_progress(task_id).get("canceled"))


def _infer_from_jobs(task_id: str) -> Optional[dict]:
    if not get_jobs:
        return None
    try:
        jobs = get_jobs() or []
        job = next((j for j in jobs if j.get("id") == task_id), None)
        if not job:
            return None
        status = str(job.get("status", "pending"))
        details = job.get("details", {}) or {}
        stage = details.get("stage")
        msg = details.get("message") or details.get("note")
        doc_path = details.get("doc_path")

        # Rough percent mapping based on known stages
        stage_map = {
            "validate": 5,
            "cache": 15,
            "clone": 40,
            "map": 60,
            "mapped": 60,
            "analyze": 75,
            "analyzed": 80,
            "docs": 90,
            "complete": 100,
        }
        percent = stage_map.get(str(stage), 10)
        if status in {"completed", "done"}:
            percent = 100
            status_out = "done"
        elif status in {"error", "timeout"}:
            percent = max(percent, 100)
            status_out = status
        elif status in {"canceled"}:
            status_out = "canceled"
            percent = percent
        else:
            status_out = "pending"

        out = {"task_id": task_id, "status": status_out, "percent": int(percent)}
        if stage:
            out["stage"] = stage
        if msg:
            out["message"] = msg
        if doc_path:
            out["doc_path"] = doc_path
        return out
    except Exception:
        return None


def get_progress(task_id: str) -> dict:
    try:
        with open(_path(task_id), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If progress file isn't there yet, infer from job registry
        inferred = _infer_from_jobs(task_id)
        if inferred:
            return inferred
        return {"task_id": task_id, "status": "unknown", "percent": 0}


def clear_progress(task_id: str) -> None:
    try:
        os.remove(_path(task_id))
    except Exception:
        pass

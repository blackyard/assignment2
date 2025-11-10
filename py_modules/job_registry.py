import os
import json
from typing import List, Dict, Any
from datetime import datetime

REG_PATH = os.path.join("outputs", "jobs.json")
os.makedirs(os.path.dirname(REG_PATH), exist_ok=True)

def _now() -> str:
    try:
        return datetime.now().isoformat(timespec="seconds")
    except Exception:
        return str(datetime.now())


def _load() -> List[Dict[str, Any]]:
    try:
        with open(REG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(data: List[Dict[str, Any]]) -> None:
    try:
        with open(REG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


def create_job(task_id: str, repo_url: str) -> None:
    jobs = _load()
    jobs = [j for j in jobs if j.get("id") != task_id]
    jobs.append({
        "id": task_id,
        "repo_url": repo_url,
        "status": "pending",
        "agent": "CodeAnalyzer",
        "priority": "medium",
        "date": _now(),
        "created_at": _now(),
        "updated_at": _now(),
        "ended_at": "",
        "details": {"stage": "start"},
        "history": [{"at": _now(), "status": "pending"}]
    })
    _save(jobs)


def update_job(task_id: str, status: str, details: Dict[str, Any] | None = None) -> None:
    jobs = _load()
    for j in jobs:
        if j.get("id") == task_id:
            j["status"] = status
            if details:
                d = j.get("details", {})
                d.update(details)
                j["details"] = d
                # Lift some commonly-used fields to top-level for quick access
                if "agent" in details:
                    j["agent"] = details.get("agent")
                if "priority" in details:
                    j["priority"] = details.get("priority")
            # Enforce agent mapping by status for consistency across the system
            s = str(status or "").lower()
            mapped_agent = None
            if s == "completed":
                mapped_agent = "DocGenerator"
            elif s in {"error", "canceled", "timeout"}:
                mapped_agent = "Supervisor"
            elif s in {"pending", "in_progress"}:
                mapped_agent = "CodeAnalyzer"
            if mapped_agent:
                j["agent"] = mapped_agent
                # Keep details in sync for UI that reads nested data
                d = j.get("details", {}) or {}
                d["agent"] = mapped_agent
                j["details"] = d
            j["updated_at"] = _now()
            hist = j.get("history", [])
            hist.append({"at": _now(), "status": status})
            j["history"] = hist
            if status in {"completed", "canceled", "error", "timeout"}:
                j["ended_at"] = _now()
            break
    _save(jobs)


def get_jobs() -> List[Dict[str, Any]]:
    return _load()


def search_jobs(query: str = "", status: str = "") -> List[Dict[str, Any]]:
    q = (query or "").lower()
    s = (status or "").lower()
    out = []
    for j in _load():
        if q:
            jid = j.get("id", "").lower()
            jurl = j.get("repo_url", "").lower()
            jagent = j.get("agent", "").lower()
            jdetails = j.get("details", {}) or {}
            d_agent = (jdetails.get("agent") or "").lower()

            # agent alias handling (docsgenerator vs docgenerator)
            def _agent_match(qs: str, agent_val: str) -> bool:
                if not agent_val:
                    return False
                if qs in agent_val:
                    return True
                # tolerate missing or extra trailing 's'
                if qs.endswith("s") and qs[:-1] in agent_val:
                    return True
                if (qs + "s") in agent_val:
                    return True
                return False

            if not (
                (q in jid)
                or (q in jurl)
                or _agent_match(q, jagent)
                or _agent_match(q, d_agent)
            ):
                continue
        if s and s != "any" and s != j.get("status", "").lower():
            continue
        out.append(j)
    return out

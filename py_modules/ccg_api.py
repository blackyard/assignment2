import os
import json
from typing import List, Dict, Any, Optional, Tuple

def query_callers(analysis_path: str, target: str) -> List[str]:
    
    try:
        files = _load_files_array(analysis_path)
        out: List[str] = []
        for item in files:
            rels = item.get("relationships") or {}
            calls = rels.get("calls") if isinstance(rels, dict) else None
            if isinstance(calls, list) and target in calls:
                p = item.get("path")
                if isinstance(p, str):
                    out.append(p)
        return out
    except Exception:
        return []

def _load_files_array(analysis_path: str) -> List[Dict[str, Any]]:
    
    if not analysis_path or not os.path.exists(analysis_path):
        return []
    with open(analysis_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        arr = data.get("files")
        return arr if isinstance(arr, list) else []
    elif isinstance(data, list):
        return data
    return []

def query_defs(analysis_path: str, file: Optional[str] = None) -> Dict[str, List[str]]:
    try:
        files = _load_files_array(analysis_path)
        funs: List[str] = []
        clss: List[str] = []
        for item in files:
            if file and item.get("path") != file:
                continue
            rels = item.get("relationships") or {}
            fs = rels.get("functions") if isinstance(rels, dict) else None
            cs = rels.get("classes") if isinstance(rels, dict) else None
            if isinstance(fs, list):
                funs.extend([x for x in fs if isinstance(x, str)])
            if isinstance(cs, list):
                clss.extend([x for x in cs if isinstance(x, str)])
        # Deduplicate and sort
        funs = sorted(list({x for x in funs}))
        clss = sorted(list({x for x in clss}))
        return {"functions": funs, "classes": clss}
    except Exception:
        return {"functions": [], "classes": []}

def query_files(analysis_path: str) -> List[Dict[str, Any]]:
    try:
        files = _load_files_array(analysis_path)
        out: List[Dict[str, Any]] = []
        for item in files:
            p = item.get("path") if isinstance(item, dict) else None
            lang = item.get("language") if isinstance(item, dict) else None
            if isinstance(p, str):
                out.append({"path": p, "language": lang or "unknown"})
        return out
    except Exception:
        return []

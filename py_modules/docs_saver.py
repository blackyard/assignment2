import os
import json
from typing import Dict, Any, List, Optional
from markdown_writer import generate_markdown, save_markdown


def build_and_save_docs(repo_path: str, file_tree: Dict[str, Any], readme: str, files: Optional[List[Dict[str, Any]]] = None) -> str:
    
    #Create a simple markdown doc for the repo and save it under outputs/<repo_name>/docs.md.


    try:
        repo_name = os.path.basename(repo_path.rstrip(os.sep)) or "repo"
        data = {
            "name": repo_name,
            "readme_summary": readme or "",
            "file_tree": file_tree or {},
            "files": files or [],
        }
        md = generate_markdown(data)

        # Save analysis payload if available
        if files:
            out_dir = os.path.join("outputs", repo_name)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, "analysis.json"), "w", encoding="utf-8") as fh:
                json.dump(files, fh, indent=2)

        return save_markdown(repo_name, md)
    except Exception:
        return ""

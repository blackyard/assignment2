import os
import json


def format_tree(tree: dict, indent: int = 0) -> str:
    lines = []
    for key, val in tree.items():
        if key == "_files":
            for f in val:
                lines.append("  " * indent + f"- {f}")
        else:
            lines.append("  " * indent + f"{key}/")
            lines.append(format_tree(val, indent + 1))
    return "\n".join(lines)


def generate_markdown(repo: dict) -> str:
    name = repo.get("name", "UnnamedRepo")
    readme = repo.get("readme_summary", "")
    tree = repo.get("file_tree", {})
    files = repo.get("files", [])

    md = [f"# 📘 Documentation for `{name}`\n"]

    # Overview
    md.append("## 🧭 Project Overview\n")
    md.append(readme or "_No README summary available._")

    # File Tree (collapsible)
    md.append("## 🗂️ File Structure\n")
    if tree:
        md.append("<details><summary>Show file tree</summary>\n\n")
        md.append("```text\n" + format_tree(tree) + "\n```\n")
        md.append("</details>\n")
    else:
        md.append("_No file structure available._")

    # Diagram (lazy import to avoid circulars/heavy deps at import time)
    try:
        try:
            from diagram_builder import build_ccg_graph  # type: ignore
        except Exception:
            try:
                from modules.diagram_builder import build_ccg_graph  # type: ignore
            except Exception as ie:
                raise RuntimeError(f"diagram builder not available: {ie}")

        diagram_path = build_ccg_graph(name, files)
        md.append("## 📊 Code Context Graph\n")
        if diagram_path:
            md.append(f"![CCG Diagram]({diagram_path})\n")
            # Also embed a Mermaid fallback for portability (e.g., GitHub/Git viewers)
            md.append("<details><summary>Show Mermaid fallback</summary>\n\n")
            md.append(_build_mermaid_graph(files))
            md.append("</details>\n")
        else:
            # Prefer Mermaid when Graphviz is unavailable
            md.append(_build_mermaid_graph(files))
    except Exception as e:
        md.append(f"_Diagram generation skipped or failed: {e}_")

    # API Reference (collapsible per file)
    md.append("## 🧪 API Reference\n")
    if not files:
        md.append("_No source files analyzed._")
    else:
        for f in files:
            md.append(f"<details><summary>{f['path']}</summary>\n\n")
            md.append(f"- Language: `{f['language']}`\n")
            md.append(f"- Relationships:\n\n```json\n{json.dumps(f['relationships'], indent=2)}\n```\n")
            md.append("</details>\n")

    return "\n".join(md)


def _build_mermaid_graph(files: list[dict]) -> str:
    
    try:
        # Safe helpers
        def _top_dir(p: str) -> str:
            p = (p or "").strip().replace("\\", "/")
            parts = [seg for seg in p.split("/") if seg]
            return parts[0] if parts else "root"

        def _basename(p: str) -> str:
            p = (p or "").strip().replace("\\", "/")
            return p.split("/")[-1] if "/" in p else p

        def _node_id(p: str) -> str:
            # Mermaid id cannot contain quotes/backticks; also avoid spaces
            return (p or "").replace("`", "").replace("\"", "").replace("'", "").replace(" ", "_")

        # Collect nodes by group and edges
        groups: dict[str, list[str]] = {}
        edges: set[tuple[str, str, str]] = set()  # (src_id, label, dst_id)

        for f in files or []:
            src_path = f.get("path") or ""
            if not src_path:
                continue
            grp = _top_dir(src_path)
            groups.setdefault(grp, []).append(src_path)
            rels = f.get("relationships") or {}

            for callee in (rels.get("calls") or []):
                if isinstance(callee, str) and callee:
                    edges.add((src_path, "calls", callee))
            for parent in (rels.get("inherits") or []):
                if isinstance(parent, str) and parent:
                    edges.add((src_path, "inherits", parent))
            for imp in (rels.get("imports") or []):
                if isinstance(imp, str) and imp:
                    edges.add((src_path, "imports", imp))

        # Build Mermaid text
        mer = ["```mermaid", "graph LR"]
        # Legend
        mer.append("%% Relationships: calls = -->, inherits = ==>, imports = -.->")

        # Nodes grouped by top-level folder
        for grp, paths in sorted(groups.items()):
            mer.append(f"  subgraph {grp}")
            for p in sorted(set(paths)):
                nid = _node_id(p)
                label = _basename(p)
                mer.append(f"    {nid}[\"{label}\"]")
            mer.append("  end")

        # Edges (limit for readability)
        MAX_EDGES = 300
        count = 0
        for src, kind, dst in sorted(edges):
            sid = _node_id(src)
            did = _node_id(dst)
            arrow = "-->" if kind == "calls" else ("==>" if kind == "inherits" else "-.->")
            mer.append(f"  {sid} {arrow} {did}")
            count += 1
            if count >= MAX_EDGES:
                mer.append("  %% (edges truncated for readability)")
                break

        mer.append("```")
        return "\n".join(mer) + "\n"
    except Exception as e:
        return f"_Mermaid graph generation failed: {e}_\n"


def save_markdown(repo_name: str, content: str) -> str:
    output_dir = os.path.join("outputs", repo_name)
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "docs.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
import os
from tree_sitter import Language, Parser

# Build Tree-sitter language library once (only needed once per setup)
# This assumes grammars are cloned into ./grammars/
# Run this manually before first use:
# Language.build_library(
import os
from tree_sitter import Language, Parser

# Build Tree-sitter language library once (only needed once per setup)
# This assumes grammars are cloned into ./grammars/
# Run this manually before first use:
# Language.build_library(
#     'build/my-languages.so',
#     [
#         'grammars/tree-sitter-python',
#         'grammars/tree-sitter-javascript',
#         'grammars/tree-sitter-java',
#         'grammars/tree-sitter-jac'  # if available
#     ]
# )
import os
import re
from tree_sitter import Language, Parser

# Load compiled languages (ensure build/my-languages.so exists)
LANGUAGE_SO_PATH = 'build/my-languages.so'
LANGUAGES = {}
try:
    LANGUAGES = {
        "python": Language(LANGUAGE_SO_PATH, "python"),
        "javascript": Language(LANGUAGE_SO_PATH, "javascript"),
        "java": Language(LANGUAGE_SO_PATH, "java"),
    }
except Exception:
    # If the shared object isn't available, LANGUAGES remains empty and
    # we fall back to regex heuristics in extract_relationships.
    LANGUAGES = {}

EXT_TO_LANG = {
    "py": "python",
    "js": "javascript",
    "java": "java",
    "jac": "jac"
}


def detect_language(file_path: str) -> str:
    ext = file_path.split(".")[-1]
    return EXT_TO_LANG.get(ext, "unknown")


def parse_file(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return ""


def _regex_extract(code: str, language: str = "python") -> dict:
    """Simple regex heuristics to find function names, class names, and call sites.

    This is intentionally conservative and language-specific where straightforward.
    Returns a dict: {"functions": [], "classes": [], "calls": []}
    """
    functions = set()
    classes = set()
    calls = set()

    if language == "python":
        functions.update(re.findall(r'^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', code, re.M))
        classes.update(re.findall(r'^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[:\(]', code, re.M))
        calls.update(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
    elif language == "javascript":
        functions.update(re.findall(r'function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
        # arrow assignments: foo = (...) =>
        functions.update(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\(?.*?\)?\s*=>', code))
        classes.update(re.findall(r'class\s+([A-Za-z_][A-Za-z0-9_]*)', code))
        calls.update(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
    elif language == "java":
        classes.update(re.findall(r'class\s+([A-Za-z_][A-Za-z0-9_]*)', code))
        # method-like signatures: [modifiers] ReturnType name(...)
        functions.update(re.findall(r'(?:public|private|protected)?\s*(?:static\s+)?[A-Za-z0-9_<>,\[\]]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
        calls.update(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', code))
    else:
        # Generic fallback: collect call-looking identifiers
        calls.update(re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', code))

    # Filter out common keywords appearing as call-like matches
    keywords = {
        'if', 'for', 'while', 'return', 'def', 'class', 'new', 'catch',
        'switch', 'case', 'else', 'import', 'from', 'try', 'except', 'with'
    }
    calls = {c for c in calls if c not in keywords}

    return {
        "functions": sorted(functions),
        "classes": sorted(classes),
        "calls": sorted(calls),
    }


def extract_relationships(code: str, language: str = "python") -> dict:
    """Extract relationships from source code.

    This tries tree-sitter first (if available) and then augments/backs off to
    simple regex heuristics. Returned dict includes keys:
      - calls: list of call targets
      - inherits: list of inheritance strings (best-effort)
      - functions: list of function names (from parser or regex)
      - classes: list of class names
    """
    results = {"calls": [], "inherits": [], "functions": [], "classes": []}

    # If tree-sitter language isn't available, use regex-only extraction
    if language not in LANGUAGES:
        rex = _regex_extract(code, language)
        results["calls"] = rex.get("calls", [])
        results["functions"] = rex.get("functions", [])
        results["classes"] = rex.get("classes", [])
        return results

    parser = Parser()
    try:
        # setting language may fail if the compiled language is incompatible
        parser.set_language(LANGUAGES[language])
        tree = parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
    except Exception:
        # parsing failed or incompatible language — fall back to regex heuristics
        rex = _regex_extract(code, language)
        results["calls"] = rex.get("calls", [])
        results["functions"] = rex.get("functions", [])
        results["classes"] = rex.get("classes", [])
        return results

    calls = set()
    inherits = set()
    functions = set()
    classes = set()

    def walk(node):
        try:
            t = node.type
            # call nodes
            if t == "call":
                for child in node.children:
                    if child.type == "identifier":
                        calls.add(child.text.decode("utf8"))

            # language-specific structural nodes (best-effort)
            if t in {"function_definition", "function_declaration", "method_declaration"}:
                for child in node.children:
                    if child.type == "identifier":
                        functions.add(child.text.decode("utf8"))

            if t in {"class_definition", "class_declaration"}:
                for child in node.children:
                    if child.type == "identifier":
                        classes.add(child.text.decode("utf8"))
                    # capture inheritance-ish children if present
                    if child.type in {"argument_list", "base_clause", "inheritance"}:
                        try:
                            inherits.add(child.text.decode("utf8"))
                        except Exception:
                            pass

            for child in node.children:
                walk(child)
        except Exception:
            pass

    walk(root_node)

    # Augment/merge with regex heuristics to provide richer results
    rex = _regex_extract(code, language)
    functions.update(rex.get("functions", []))
    classes.update(rex.get("classes", []))
    calls.update(rex.get("calls", []))

    results["calls"] = sorted(calls)
    results["inherits"] = sorted(inherits)
    results["functions"] = sorted(functions)
    results["classes"] = sorted(classes)
    return results

import from py_modules.parser { parse_file as py_parse_file, extract_relationships as py_extract_relationships, detect_language as py_detect_language }
import from py_modules.repo_utils { flatten_tree as py_flatten_tree }

impl CodeAnalyzer.analyze_tree {
    let analyzed = [];
    let flattened = py_flatten_tree(repo_path=repo_path, tree=file_tree);
    if flattened != None {
        for f in flattened {
            let fp = f.get("abs");
            let rel = f.get("rel");
            let lang = py_detect_language(file_path=fp);
            if (lang != "unknown") {
                let content = py_parse_file(file_path=fp);
                let rels = py_extract_relationships(code=content, language=lang);
                analyzed.append({
                    "path": rel,
                    "language": lang,
                    "relationships": rels
                });
            }
        }
    }
    return analyzed;
}

impl CodeAnalyzer.query_calls {
    let callers = [];
    for f in files {
        let rels = f.get("relationships");
        if rels != None {
            let calls = rels.get("calls");
            if calls != None and target in calls { callers.append(f.get("path")); }
        }
    }
    return callers;
}

impl CodeAnalyzer.query_inheritance {
    let children = [];
    for f in files {
        let rels = f.get("relationships");
        if rels != None {
            let inh = rels.get("inherits");
            if inh != None and class_name in inh { children.append(f.get("path")); }
        }
    }
    return children;
}

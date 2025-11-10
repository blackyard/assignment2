import from dotenv { load_dotenv }
import sys;
import os;
import from utils { get_current_datetime }
import from py_modules.repo_utils { is_valid_github_url as py_is_valid_github_url, generate_file_tree as py_generate_file_tree, summarize_readme as py_summarize_readme, flatten_tree as py_flatten_tree }
import from py_modules.parser { detect_language as py_detect_language, parse_file as py_parse_file, extract_relationships as py_extract_relationships }
import from py_modules.progress { set_progress as py_set_progress, get_progress as py_get_progress, set_canceled as py_set_canceled, is_canceled as py_is_canceled }
import from py_modules.docs_saver { build_and_save_docs as py_build_and_save_docs }
import from py_modules.job_registry { create_job as py_create_job, update_job as py_update_job, get_jobs as py_get_jobs, search_jobs as py_search_jobs }
import from py_modules.clone_worker { interruptible_clone as py_interruptible_clone, cancel_clone as py_cancel_clone }
import from py_modules.repo_cache { ensure_cached_repo as py_ensure_cached_repo }
import from py_modules.ccg_api { query_callers, query_defs as py_query_defs, query_files as py_query_files }

node API {
    def set_progress(task_id: str, status: str, percent: int, extra: dict);
    def set_canceled(task_id: str, message: str);
    def is_canceled(task_id: str) -> bool;
    def get_progress(task_id: str) -> dict;
    def create_job(task_id: str, repo_url: str);
    def update_job(task_id: str, status: str, details: dict);
    def get_jobs() -> list;
    def search_jobs(query: str, status: str) -> list;
}

impl API.set_progress {
    py_set_progress(task_id=task_id, status=status, percent=percent, extra=extra);
}

impl API.set_canceled {
    py_set_canceled(task_id=task_id, message=message);
}

impl API.is_canceled -> bool {
    return py_is_canceled(task_id=task_id);
}

impl API.get_progress -> dict {
    return py_get_progress(task_id=task_id);
}

impl API.create_job {
    py_create_job(task_id=task_id, repo_url=repo_url);
}

impl API.update_job {
    py_update_job(task_id=task_id, status=status, details=details);
}

impl API.get_jobs -> list {
    return py_get_jobs();
}

impl API.search_jobs -> list {
    return py_search_jobs(query=query, status=status);
}

node URLHandling {
    def save_link(github_link: str) -> str;
    def validate_and_register(task_id: str, github_link: str) -> dict;
}

node AssignAgentTask {
    def assign(task_id: str) -> str {
        api = API();
        if task_id { api.update_job(task_id=task_id, status="pending", details={"agent": "CodeAnalyzer"}); }
        return "CodeAnalyzer";
    }
}

node AssignPriority {
    def prioritize(task_id: str) -> str {
        api = API();
        if task_id { api.update_job(task_id=task_id, status="pending", details={"priority": "medium"}); }
        return "medium";
    }
}

node RetrieveTask {
    def do_clone(task_id: str, repo_url: str) -> str;
}

node RepoCache {
    def ensure(task_id: str, repo_url: str) -> str;
    def ensure_with_options(task_id: str, repo_url: str, refresh: bool, timeout: int, depth: int) -> str;
}

node GetTaskState {
    def map_repo(task_id: str, repo_path: str) -> dict;
}

node CodeAnalysis {
    def analyze_repo(task_id: str, repo_path: str, file_tree: dict) -> list;
}

node FinalDocumentAssembly {
    def assemble(task_id: str, repo_path: str, file_tree: dict, readme: str, files: list) -> dict;
}

node Session {
    has history: list = [];
    has created_at: str = get_current_datetime();
    def add_history(entry: str);
    def get_history() -> str;
}

node Toolbox {
    def route_and_run(utterance: str, history: str) -> str abs;
    can execute with agent entry {
        session = visitor.session;
        response = self.route_and_run(visitor.utterance, session.get_history());
        session.add_history(
            "user: " + visitor.utterance + "\nai: " + response
        );
        report {
            "session_id": jid(visitor.session),
            "response": response
        };
    }
}

enum RoutingNodes {
    GITHUB_URL = "URLHandling",
    TASK_AGENT = "AssignAgentTask",
    TASK_PRIORITY = "AssignPriority",
    TASK_STATE = "GetTaskState",
    FINAL_ASSEMBLY = "FinalDocumentAssembly"
}

def execute_docs_workflow(task_id: str, repo_url: str) -> dict {
    api = API();

    # Initialize pipeline nodes
    cache_node = RepoCache();
    state_node = GetTaskState();
    analysis_node = CodeAnalysis();
    final_node = FinalDocumentAssembly();

    # 1) URL validation
    if task_id { api.set_progress(task_id=task_id, status="starting", percent=5, extra={"stage": "validate"}); }
    if not repo_url or not ("github.com" in repo_url) or not py_is_valid_github_url(url=repo_url) {
        let msg = "Invalid GitHub URL";
        if task_id { api.set_progress(task_id=task_id, status="error", percent=100, extra={"stage": "validate", "message": msg}); }
        if task_id { api.update_job(task_id=task_id, status="error", details={"stage": "validate", "message": msg, "agent": "Supervisor", "priority": "high"}); }
        return {"error": msg};
    }
    if task_id { api.create_job(task_id, repo_url); api.update_job(task_id=task_id, status="pending", details={"stage": "validate", "agent": "CodeAnalyzer", "repo_url": repo_url}); }
    if task_id and api.is_canceled(task_id) { api.update_job(task_id=task_id, status="canceled", details={"stage": "validate", "agent": "Supervisor", "priority": "low"}); return {"error": "canceled"}; }

    # 2) Agent assignment and priority
    agent = "CodeAnalyzer";
    prio = "medium";
    if task_id { api.update_job(task_id=task_id, status="pending", details={"agent": agent}); }
    if task_id { api.update_job(task_id=task_id, status="pending", details={"priority": prio}); }

    # 3) Cache or Clone
    if task_id { api.set_progress(task_id=task_id, status="cache", percent=12, extra={"stage": "cache"}); }
    repo_path = cache_node.ensure_with_options(task_id=task_id, repo_url=repo_url, refresh=False, timeout=120, depth=1);
    if not repo_path {
        repo_path = py_interruptible_clone(task_id=task_id, url=repo_url, max_seconds=180, depth=1);
    } else {
        if task_id { api.set_progress(task_id=task_id, status="cache", percent=25, extra={"stage": "cache"}); }
    }
    if not repo_path {
        if task_id { api.set_progress(task_id=task_id, status="error", percent=100, extra={"stage": "clone", "message": "Failed to clone"}); }
        if task_id { api.update_job(task_id=task_id, status="error", details={"message": "Failed to clone", "agent": "Supervisor", "priority": "high"}); }
        return {"error": "Failed to clone repository."};
    }

    # 4) Repo mapping and README
    m = state_node.map_repo(task_id=task_id, repo_path=repo_path);
    if m.get("canceled") { return {"error": "canceled"}; }
    file_tree = m.get("file_tree", {});
    readme = m.get("readme", "");

    # 5) Code analysis
    files = analysis_node.analyze_repo(task_id=task_id, repo_path=repo_path, file_tree=file_tree);

    # 6) Final doc assembly
    fin = final_node.assemble(task_id=task_id, repo_path=repo_path, file_tree=file_tree, readme=readme, files=files);
    if fin.get("canceled") { return {"error": "canceled"}; }
    doc_path = fin.get("doc_path", "");

    # 7) Return results
    return {"repo": {"path": repo_path, "file_tree": file_tree, "readme": readme, "doc_path": doc_path, "agent": agent, "priority": prio}};
}

def update_progress_and_job(task_id: str, status: str, percent: int, stage: str, priority: str) -> API {
    api = API();
    if task_id and api.is_canceled(task_id) {
        api.update_job(task_id=task_id, status="canceled", details={"stage": stage, "agent": "Supervisor", "priority": "low"});
        return api;
    }
    if task_id { api.set_progress(task_id=task_id, status=status, percent=percent, extra={"stage": stage}); }
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": stage, "priority": priority}); }
    return api;
}

def get_doc_path_from_task(task_id: str) -> str {
    api = API();
    jobs = api.get_jobs();
    for j in jobs {
        if j.get("id") == task_id {
            let det = j.get("details", {});
            let doc_path = det.get("doc_path");
            if doc_path { return doc_path; }
        }
    }
    return "";
}

walker agent {
    has utterance: str = "";
    has session_id: str = "";

    obj __specs__ {
        static has auth: bool = False;
    }
    def get_node_class(class_name: str) {
        main_mod = sys.modules.get("main");
        if main_mod and hasattr(main_mod, class_name) {
            return getattr(main_mod, class_name);
        }

        for (mod_name, mod) in sys.modules.items() {
            if mod and hasattr(mod, class_name) {
                return getattr(mod, class_name);
            }
        }
        return None;
    }
    def route_to_node(utterance: str, history: str) -> RoutingNodes abs;
    can execute with `root entry {
        memory_list = [root --> (`?Memory)];
        if not memory_list {
            memory_list = root ++> Memory();
        }
        memory = memory_list[0];
        if not self.session_id {
            session_list = memory ++> Session();
            self.session = session_list[0];
        } else {
            self.session = &(self.session_id);
        }
        routed_node = self.route_to_node(self.utterance, self.session.get_history());
        node_cls = self.get_node_class(routed_node.value);
        if not node_cls {
            print("Failed to get node class");
            return;
        }
        node_inst = node_cls();
        visit [-->(`?node_cls)] else {
            attached_routed_node = here ++> node_inst;
            visit attached_routed_node;
        }
    }
}

walker get_all_sessions {
    obj __specs__ {
        static has auth: bool = False;
    }
    can get_all_sessions with `root entry {
        memory_list = [here --> (`?Memory)];
        if not memory_list {
            report "No sessions found.";
            disengage;
        }
        memory = memory_list[0];
        session_list = [memory --> (`?Session)];
        report [{
            "id": jid(session),
            "created_at": session.created_at
        } for session in session_list];
    }
}

with entry {
    load_dotenv();
    here = os.getcwd();
    parent = os.path.abspath(os.path.join(here, ".."));
    py1 = os.path.join(here, "py_modules");
    py2 = os.path.join(parent, "py_modules");
    if py1 not in sys.path { sys.path.append(py1); }
    if py2 not in sys.path { sys.path.append(py2); }
    if parent not in sys.path { sys.path.append(parent); }
}


walker generate_docs {
    has repo_url: str = "";
    has session_id: str = "";
    has task_id: str = "";

    obj __specs__ {
        static has auth: bool = False;
    }

    can generate_docs with `root entry {
        api = API();
        if self.task_id { api.set_progress(task_id=self.task_id, status="starting", percent=1, extra={"stage": "validate"}); }

        result = execute_docs_workflow(task_id=self.task_id, repo_url=self.repo_url);
        if result.get("error") {
            report result;
            disengage;
        }
        report result;
    }

    # Alias for REST default ability
    can start with `root entry {
        api = API();
        if self.task_id { api.set_progress(task_id=self.task_id, status="starting", percent=1, extra={"stage": "validate"}); }

        result = execute_docs_workflow(task_id=self.task_id, repo_url=self.repo_url);
        if result.get("error") {
            report result;
            disengage;
        }
        report result;
    }
}

walker get_progress {
    has task_id: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can get_progress with `root entry {
        api = API();
        if not self.task_id {
            report {"error": "task_id required"};
            disengage;
        }
        
        prog = api.get_progress(self.task_id);
        if (not prog) or (prog.get("status", "unknown") == "unknown" and int(prog.get("percent", 0)) == 0) {
            jobs = api.get_jobs();
            for j in jobs {
                if j.get("id") == self.task_id {
                    det = j.get("details", {});
                    status = j.get("status", "pending");
                    stage = det.get("stage");
                    doc_path = det.get("doc_path");
                    pct = 0;
                    if status in {"pending"} { pct = 5; }
                    if stage == "cache" { pct = 15; }
                    if stage == "clone" { pct = 40; }
                    if stage == "map" { pct = 60; }
                    if stage == "analyze" { pct = 75; }
                    if stage == "docs" { pct = 85; }
                    if status in {"completed"} { pct = 100; }
                    prog = {
                        "task_id": self.task_id,
                        "status": status,
                        "percent": pct,
                        "stage": stage,
                    };
                    if doc_path { prog["doc_path"] = doc_path; }
                    break;
                }
            }
        }
        report prog;
    }
}

walker workflow_status {
    obj __specs__ {
        static has auth: bool = False;
    }
    can workflow_status with `root entry {
        api = API();
        jobs = api.get_jobs();
        report {"jobs": jobs};
    }
}

walker tasks_search {
    has query: str = "";
    has status: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can tasks_search with `root entry {
        api = API();
        results = api.search_jobs(self.query, self.status);
        report {"tasks": results};
    }
}

walker cancel_task {
    has task_id: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can cancel_task with `root entry {
        api = API();
        if not self.task_id { report {"error": "task_id required"}; disengage; }
        api.set_canceled(task_id=self.task_id, message="User requested cancel");
        api.update_job(task_id=self.task_id, status="canceled", details={"message": "User canceled", "agent": "Supervisor", "priority": "low"});
        py_cancel_clone(task_id=self.task_id);
        report {"ok": True};
    }
}

walker refresh_cache {
    has repo_url: str = "";
    has task_id: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can refresh_cache with `root entry {
        api = API();
        if not self.repo_url { report {"error": "repo_url required"}; disengage; }
        # Force refresh the persistent cache clone
        if self.task_id { api.set_progress(task_id=self.task_id, status="cache", percent=10, extra={"stage": "cache_refresh"}); }
        cache_node = RepoCache();
        path = cache_node.ensure_with_options(task_id=self.task_id, repo_url=self.repo_url, refresh=True, timeout=180, depth=1);
        if not path { report {"error": "Failed to refresh cache"}; disengage; }
        if self.task_id { api.set_progress(task_id=self.task_id, status="cache", percent=30, extra={"stage": "cache_refreshed", "path": path}); }
        report {"path": path};
    }
}

walker query_ccg {
    has task_id: str = "";
    has target: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can query_ccg with `root entry {
        if not self.task_id { report {"error": "task_id required"}; disengage; }
        if not self.target { report {"error": "target function/class required"}; disengage; }
        doc_path = get_doc_path_from_task(task_id=self.task_id);
        if not doc_path { report {"error": "analysis not available for task (no doc_path)"}; disengage; }
        let analysis_path = doc_path;
        if analysis_path.endswith("docs.md") {
            analysis_path = analysis_path[:-7] + "analysis.json";
        } else {
            analysis_path = analysis_path + ".analysis.json";
        }
        callers = query_callers(analysis_path, self.target);
        report {"target": self.target, "callers": callers};
    }
}

walker query_defs {
    has task_id: str = "";
    has file: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can query_defs with `root entry {
        if not self.task_id { report {"error": "task_id required"}; disengage; }
        doc_path = get_doc_path_from_task(task_id=self.task_id);
        if not doc_path { report {"error": "analysis not available for task (no doc_path)"}; disengage; }
        let analysis_path = doc_path;
        if analysis_path.endswith("docs.md") { analysis_path = analysis_path[:-7] + "analysis.json"; }
        else { analysis_path = analysis_path + ".analysis.json"; }
        defs = py_query_defs(analysis_path=analysis_path, file=self.file);
        report defs;
    }
}

walker query_files {
    has task_id: str = "";
    obj __specs__ { static has auth: bool = False; }
    can query_files with `root entry {
        if not self.task_id { report {"error": "task_id required"}; disengage; }
        doc_path = get_doc_path_from_task(task_id=self.task_id);
        if not doc_path { report {"error": "analysis not available for task (no doc_path)"}; disengage; }
        let analysis_path = doc_path;
        if analysis_path.endswith("docs.md") { analysis_path = analysis_path[:-7] + "analysis.json"; }
        else { analysis_path = analysis_path + ".analysis.json"; }
        files = py_query_files(analysis_path=analysis_path);
        report {"files": files};
    }
}


walker repo_map_debug {
    has repo_url: str = "";
    has task_id: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can repo_map_debug with `root entry {
        api = API();
        if not self.repo_url { report {"error": "repo_url required"}; disengage; }
        cache_node = RepoCache();
        state_node = GetTaskState();
        path = cache_node.ensure_with_options(task_id=self.task_id, repo_url=self.repo_url, refresh=False, timeout=120, depth=1);
        if not path { report {"error": "failed to cache/clone repo"}; disengage; }
        m = state_node.map_repo(task_id=self.task_id, repo_path=path);
        if m.get("canceled") { report {"error": "canceled"}; disengage; }
        files = m.get("file_tree", {});
        readme = m.get("readme", "");
        report {"path": path, "file_tree": files, "readme": readme};
    }
}

walker analyze_debug {
    has repo_url: str = "";
    has task_id: str = "";
    obj __specs__ {
        static has auth: bool = False;
    }
    can analyze_debug with `root entry {
        api = API();
        if not self.repo_url { report {"error": "repo_url required"}; disengage; }
        cache_node = RepoCache();
        path = cache_node.ensure_with_options(task_id=self.task_id, repo_url=self.repo_url, refresh=False, timeout=120, depth=1);
        if not path { report {"error": "failed to cache/clone repo"}; disengage; }
        state_node = GetTaskState();
        m = state_node.map_repo(task_id=self.task_id, repo_path=path);
        if m.get("canceled") { report {"error": "canceled"}; disengage; }
        file_tree = m.get("file_tree", {});
        analyzer = CodeAnalysis();
        files = analyzer.analyze_repo(task_id=self.task_id, repo_path=path, file_tree=file_tree);
        report {"path": path, "file_tree": file_tree, "files": files};
    }
}

# Implementations 
impl CodeAnalysis.analyze_repo {
    api = update_progress_and_job(task_id=task_id, status="analyzing", percent=75, stage="analyze", priority="medium");
    analyzed = [];
    files = py_flatten_tree(repo_path=repo_path, tree=file_tree);
    # Prioritize likely entry points first
    if files != None {
        let entry_names = {"main.py", "app.py", "__main__.py", "manage.py", "index.js", "index.ts"};
        let first = [];
        let later = [];
        for item in files {
            let relp = item.get("rel");
            let base = "";
            if relp { base = relp.split("/")[-1]; }
            if base in entry_names { first.append(item); }
            else { later.append(item); }
        }
        let ordered = first + later;
        for f in ordered {
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
        # Iterative expansion using CCG frontier (best-effort)
        let known_defs = [];
        let pending_calls = [];
        for a in analyzed {
            let r = a.get("relationships", {});
            for fn in (r.get("functions", []) or []) { if fn not in known_defs { known_defs.append(fn); } }
            for cl in (r.get("classes", []) or []) { if cl not in known_defs { known_defs.append(cl); } }
            for c in (r.get("calls", []) or []) { if c not in pending_calls { pending_calls.append(c); } }
        }
        let analyzed_paths = [a.get("path") for a in analyzed];
        let remaining = [];
        for it in later {
            let rp = it.get("rel");
            if (rp not in analyzed_paths) { remaining.append(it); }
        }
        let max_extra = 200;
        let added_count = 0;

        # Pass 1
        let frontier1 = [];
        for t in pending_calls { if t not in known_defs { frontier1.append(t); } }
        if len(frontier1) > 0 {
            let next_remaining1 = [];
            let added_any1 = False;
            for cand in remaining {
                if added_count >= max_extra { next_remaining1.append(cand); continue; }
                let fp2 = cand.get("abs");
                let rel2 = cand.get("rel");
                let lang2 = py_detect_language(file_path=fp2);
                if (lang2 == "unknown") { next_remaining1.append(cand); continue; }
                let code2 = py_parse_file(file_path=fp2);
                let rels2 = py_extract_relationships(code=code2, language=lang2);
                let defines = (rels2.get("functions", []) or []) + (rels2.get("classes", []) or []);
                let hit1 = False;
                for n in defines { if n in frontier1 { hit1 = True; break; } }
                if hit1 {
                    analyzed.append({
                        "path": rel2,
                        "language": lang2,
                        "relationships": rels2
                    });
                    for fn in (rels2.get("functions", []) or []) { if fn not in known_defs { known_defs.append(fn); } }
                    for cl in (rels2.get("classes", []) or []) { if cl not in known_defs { known_defs.append(cl); } }
                    for c in (rels2.get("calls", []) or []) { if c not in pending_calls { pending_calls.append(c); } }
                    added_count = added_count + 1;
                    added_any1 = True;
                } else {
                    next_remaining1.append(cand);
                }
            }
            remaining = next_remaining1;
            if task_id and added_any1 { api.set_progress(task_id=task_id, status="analyzing", percent=77, extra={"stage": "analyze+1"}); }
        }

        # Pass 2
        let frontier2 = [];
        for t in pending_calls { if t not in known_defs { frontier2.append(t); } }
        if len(frontier2) > 0 {
            let next_remaining2 = [];
            let added_any2 = False;
            for cand in remaining {
                if added_count >= max_extra { next_remaining2.append(cand); continue; }
                let fp3 = cand.get("abs");
                let rel3 = cand.get("rel");
                let lang3 = py_detect_language(file_path=fp3);
                if (lang3 == "unknown") { next_remaining2.append(cand); continue; }
                let code3 = py_parse_file(file_path=fp3);
                let rels3 = py_extract_relationships(code=code3, language=lang3);
                let defines2 = (rels3.get("functions", []) or []) + (rels3.get("classes", []) or []);
                let hit2 = False;
                for n in defines2 { if n in frontier2 { hit2 = True; break; } }
                if hit2 {
                    analyzed.append({
                        "path": rel3,
                        "language": lang3,
                        "relationships": rels3
                    });
                    for fn in (rels3.get("functions", []) or []) { if fn not in known_defs { known_defs.append(fn); } }
                    for cl in (rels3.get("classes", []) or []) { if cl not in known_defs { known_defs.append(cl); } }
                    for c in (rels3.get("calls", []) or []) { if c not in pending_calls { pending_calls.append(c); } }
                    added_count = added_count + 1;
                    added_any2 = True;
                } else {
                    next_remaining2.append(cand);
                }
            }
            remaining = next_remaining2;
            if task_id and added_any2 { api.set_progress(task_id=task_id, status="analyzing", percent=78, extra={"stage": "analyze+2"}); }
        }

        # Pass 3
        let frontier3 = [];
        for t in pending_calls { if t not in known_defs { frontier3.append(t); } }
        if len(frontier3) > 0 {
            let next_remaining3 = [];
            let added_any3 = False;
            for cand in remaining {
                if added_count >= max_extra { next_remaining3.append(cand); continue; }
                let fp4 = cand.get("abs");
                let rel4 = cand.get("rel");
                let lang4 = py_detect_language(file_path=fp4);
                if (lang4 == "unknown") { next_remaining3.append(cand); continue; }
                let code4 = py_parse_file(file_path=fp4);
                let rels4 = py_extract_relationships(code=code4, language=lang4);
                let defines3 = (rels4.get("functions", []) or []) + (rels4.get("classes", []) or []);
                let hit3 = False;
                for n in defines3 { if n in frontier3 { hit3 = True; break; } }
                if hit3 {
                    analyzed.append({
                        "path": rel4,
                        "language": lang4,
                        "relationships": rels4
                    });
                    for fn in (rels4.get("functions", []) or []) { if fn not in known_defs { known_defs.append(fn); } }
                    for cl in (rels4.get("classes", []) or []) { if cl not in known_defs { known_defs.append(cl); } }
                    for c in (rels4.get("calls", []) or []) { if c not in pending_calls { pending_calls.append(c); } }
                    added_count = added_count + 1;
                    added_any3 = True;
                } else {
                    next_remaining3.append(cand);
                }
            }
            remaining = next_remaining3;
            if task_id and added_any3 { api.set_progress(task_id=task_id, status="analyzing", percent=79, extra={"stage": "analyze+3"}); }
        }
    }
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": "analyzed", "priority": "medium"}); }
    return analyzed;
}

impl FinalDocumentAssembly.assemble {
    api = update_progress_and_job(task_id=task_id, status="documenting", percent=85, stage="docs", priority="medium");
    if task_id and api.is_canceled(task_id) { return {"canceled": True}; }
    doc_path = py_build_and_save_docs(repo_path=repo_path, file_tree=file_tree, readme=readme, files=files);
    if task_id { api.set_progress(task_id=task_id, status="done", percent=100, extra={"stage": "complete", "doc_path": doc_path}); api.update_job(task_id=task_id, status="completed", details={"doc_path": doc_path, "priority": "normal", "agent": "DocGenerator"}); }
    return {"doc_path": doc_path};
}

# URLHandling
impl URLHandling.save_link {
    return github_link;
}

impl URLHandling.validate_and_register {
    api = API();
    if task_id { api.set_progress(task_id=task_id, status="starting", percent=5, extra={"stage": "validate"}); }
    # Defensive normalization
    let url = github_link if github_link else "";
    if not url { if task_id { api.set_progress(task_id=task_id, status="error", percent=100, extra={"stage": "validate", "message": "Missing URL"}); } return {"ok": False, "error": "Invalid GitHub URL."}; }
    if not ("github.com" in url) { if task_id { api.set_progress(task_id=task_id, status="error", percent=100, extra={"stage": "validate", "message": "Not a GitHub URL"}); } return {"ok": False, "error": "Invalid GitHub URL."}; }
    if not py_is_valid_github_url(url=url) {
    if task_id { api.set_progress(task_id=task_id, status="error", percent=100, extra={"stage": "validate", "message": "Invalid GitHub URL format"}); }
        return {"ok": False, "error": "Invalid GitHub URL format."};
    }
    if task_id { api.create_job(task_id, url); api.update_job(task_id=task_id, status="pending", details={"stage": "validate", "agent": "CodeAnalyzer", "repo_url": url}); }
    return {"ok": True, "url": url};
}

# RetrieveTask
impl RetrieveTask.do_clone {
    api = API();
    if task_id and api.is_canceled(task_id) { api.update_job(task_id=task_id, status="canceled", details={"stage": "clone", "agent": "Supervisor", "priority": "low"}); return ""; }
    if task_id { api.set_progress(task_id=task_id, status="cloning", percent=20, extra={"stage": "clone"}); }
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": "clone", "priority": "medium"}); }
    return py_interruptible_clone(task_id=task_id, url=repo_url, max_seconds=180, depth=1);
}

# RepoCache
impl RepoCache.ensure {
    api = API();
    if task_id and api.is_canceled(task_id) { api.update_job(task_id=task_id, status="canceled", details={"stage": "cache", "agent": "Supervisor", "priority": "low"}); return ""; }
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": "cache", "priority": "medium"}); }
    path = py_ensure_cached_repo(task_id=task_id, url=repo_url, refresh=False, timeout=120, depth=1);
    return path;
}

impl RepoCache.ensure_with_options {
    api = API();
    if task_id and api.is_canceled(task_id) { api.update_job(task_id=task_id, status="canceled", details={"stage": "cache", "agent": "Supervisor", "priority": "low"}); return ""; }
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": "cache", "priority": "medium"}); }
    path = py_ensure_cached_repo(task_id=task_id, url=repo_url, refresh=refresh, timeout=timeout, depth=depth);
    return path;
}

# AssignAgentTask / AssignPriority and GetTaskState

impl GetTaskState.map_repo {
    api = API();
    if task_id and api.is_canceled(task_id) { api.update_job(task_id=task_id, status="canceled", details={"stage": "map", "agent": "Supervisor", "priority": "low"}); return {"canceled": True}; }
    if task_id { api.set_progress(task_id=task_id, status="mapping", percent=60, extra={"stage": "map"}); }
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": "map", "priority": "medium"}); }
    files = py_generate_file_tree(repo_path=repo_path);
    readme = py_summarize_readme(repo_path=repo_path);
    if task_id { api.update_job(task_id=task_id, status="in_progress", details={"stage": "mapped", "priority": "medium"}); }
    return {"file_tree": files, "readme": readme};
}

# Session methods
impl Session.add_history {
    self.history = self.history + [entry];
}

impl Session.get_history -> str {
    return "\n".join(self.history[-10:]);
}
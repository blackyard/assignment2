import streamlit as st
import requests
import threading
import time
import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from streamlit.components.v1 import html as components_html
from urllib.parse import urlparse
from typing import cast, Dict, List, Optional

# --- CONFIG ---
st.set_page_config(page_title="Agentic Codebase Genius", layout="wide")

# --- CSS ---
st.markdown("""
<style>
.main > div {max-width: 1000px; padding: 50px;}
.block-container {display: flex; flex-direction: column; height: 100vh; padding-top: 1rem;}
.stTabs {position: sticky; top: 0; z-index: 100; background-color: white; padding-bottom: 1rem;}
.status-dash {background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); border: 1px solid #eef2f7; padding: 14px 18px; border-radius: 12px; margin: 8px 0 18px 0;}
.chat-wrapper {display: flex; flex-direction: column; height: calc(100vh - 200px); overflow: hidden;}
.chat-scroll {overflow-y: auto; padding: 1rem 0; margin-bottom: 1rem; max-height: calc(100vh - 300px);}
.chat-input {position: absolute; bottom: 0; left: 0; width: 100%; background-color: white; padding: 1rem 0; border-top: 1px solid #e0e0e0; z-index: 50;}
.stChatInput {margin: 0 !important;}
.chat-scroll::-webkit-scrollbar {width: 8px;}
.chat-scroll::-webkit-scrollbar-track {background: #f1f1f1; border-radius: 4px;}
.chat-scroll::-webkit-scrollbar-thumb {background: #888; border-radius: 4px;}
.chat-scroll::-webkit-scrollbar-thumb:hover {background: #555;}
.stChatMessage {margin-bottom: 1rem;}
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS ---
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "generate": f"{BASE_URL}/walker/generate_docs",
    "status": f"{BASE_URL}/walker/workflow_status",
    "search": f"{BASE_URL}/walker/tasks_search",
    "progress": f"{BASE_URL}/walker/get_progress",
    "cancel": f"{BASE_URL}/walker/cancel_task"
}

STAGE_LABELS = {
    "validate": "Validating URL", "cache": "Checking cache", "clone": "Cloning repository",
    "map": "Mapping repository", "analyze": "Analyzing code", "docs": "Generating documentation",
    "complete": "Complete"
}

STATUS_BADGE = {
    "starting": ("#1f77b4", "Starting"), "validate": ("#1f77b4", "Validating"),
    "cache": ("#1f77b4", "Caching"), "cloning": ("#1f77b4", "Cloning"),
    "mapping": ("#9467bd", "Mapping"), "mapped": ("#9467bd", "Mapped"),
    "analyzing": ("#ff7f0e", "Analyzing"), "documenting": ("#17becf", "Documenting"),
    "done": ("#2ca02c", "Done"), "completed": ("#2ca02c", "Completed"),
    "error": ("#d62728", "Error"), "timeout": ("#d62728", "Timeout"),
    "canceled": ("#7f7f7f", "Canceled")
}

TAB_OPTIONS = ["📄 Generate Docs", "📋 Workflow Status", "📚 Docs Review", "📈 Repo History"]

def render_badge(status: str) -> str:
    label = status or "unknown"
    color, text = STATUS_BADGE.get(str(status).lower(), ("#7f7f7f", str(status)))
    return f"<span style='display:inline-block;padding:2px 8px;border-radius:12px;background:{color};color:white;font-size:12px'>{text}</span>"

def api_call(endpoint: str, data: Optional[Dict] = None, timeout: int = 30) -> Optional[Dict]:
    """Generic API call helper"""
    try:
        res = requests.post(ENDPOINTS[endpoint], json=data or {}, timeout=timeout)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None

def parse_api_response(payload: Dict) -> Dict:
    """Extract data from API response"""
    if not isinstance(payload, dict):
        return payload
    if "report" in payload and isinstance(payload["report"], dict):
        return payload["report"]
    reports = payload.get("reports")
    if isinstance(reports, list) and reports:
        first = reports[0]
        if isinstance(first, dict):
            return first.get("report", first) if "report" in first else first
    return payload

def get_project_name(job: Dict) -> str:
    """Extract project name from job data"""
    if not isinstance(job, dict):
        return ""
    for key in ("project", "project_name", "repo_name"):
        val = job.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    details = job.get("details", {})
    if isinstance(details, dict):
        for key in ("project", "project_name", "repo_name"):
            val = details.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    repo_url = job.get("repo_url") or details.get("repo_url")
    if isinstance(repo_url, str) and repo_url:
        return repo_url.split("/")[-1].replace(".git", "")
    return ""

def parse_repo_url(url: str) -> tuple[str, str, str]:
    """Parse GitHub URL into components"""
    try:
        p = urlparse(url.strip())
        host = p.netloc.lower()
        parts = [seg for seg in p.path.strip("/").split("/") if seg]
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1].replace(".git", "")
            return host, owner, repo
    except Exception:
        pass
    return "", "", ""

def is_valid_github_url(url: str) -> bool:
    """Validate GitHub repository URL"""
    host, owner, repo = parse_repo_url(url)
    return host == "github.com" and bool(owner) and bool(repo)

def normalize_repo_key(url: str) -> str:
    """Create normalized repo key"""
    host, owner, repo = parse_repo_url(url)
    return f"{host}/{owner}/{repo}" if host and owner and repo else ""

def paginate(total: int, page_key: str, page_size: int = 10, label: str = "Page") -> tuple[int, int, int]:
    """Handle pagination controls"""
    import math
    pages = max(1, math.ceil(total / max(1, page_size)))
    cur = int(st.session_state.get(page_key, 1) or 1)
    cur = max(1, min(cur, pages))
    st.session_state[page_key] = cur

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀ Prev", key=f"{page_key}_prev", disabled=cur <= 1):
            st.session_state[page_key] = cur - 1
            st.rerun()
    with col2:
        start_idx = (cur - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        st.markdown(f"**{label}: {cur}/{pages}** — {start_idx + 1 if total else 0}–{end_idx} of {total}")
    with col3:
        if st.button("Next ▶", key=f"{page_key}_next", disabled=cur >= pages):
            st.session_state[page_key] = cur + 1
            st.rerun()

    start_idx = (st.session_state[page_key] - 1) * page_size
    end_idx = min(start_idx + page_size, total)
    return start_idx, end_idx, st.session_state[page_key]

def get_workflow_jobs() -> List[Dict]:
    """Fetch workflow jobs from API"""
    data = api_call("status")
    if data:
        parsed = parse_api_response(data)
        if isinstance(parsed, dict):
            return parsed.get("jobs", []) or parsed.get("results", []) or parsed.get("history", [])
    return []

def render_status_dashboard(show_snapshot: bool = True):
    """Display workflow status metrics"""
    if show_snapshot:
        st.caption("Workflow Snapshot")
        jobs = get_workflow_jobs()

        status_counts = Counter(str(j.get("status", "")).lower() for j in jobs)
        completed = status_counts.get("completed", 0) + status_counts.get("done", 0)
        pending = status_counts.get("pending", 0) + status_counts.get("in_progress", 0)
        canceled = status_counts.get("canceled", 0)
        errors = status_counts.get("error", 0) + status_counts.get("timeout", 0)

        cols = st.columns(4)
        cols[0].metric("✅ Completed", completed)
        cols[1].metric("🕒 Pending", pending)
        cols[2].metric("⛔ Canceled", canceled)
        cols[3].metric("⚠️ Errors", errors)

        st.divider()
        st.caption("Recent Jobs")
        if jobs:
            recent = jobs[:5]
            chip_cols = st.columns(len(recent))
            for idx, job in enumerate(recent):
                proj = get_project_name(job) or "N/A"
                status = str(job.get("status", "")).lower()
                chip_cols[idx].markdown(f"**{proj}**<br/>{render_badge(status)}", unsafe_allow_html=True)
        st.divider()


# --- SESSION STATE ---
for key, default in [
    ('session_id', ''), ('chat_history', []), ('repo_url_input', ''),
    ('request_clear_repo_input', False), ('active_tab', '📄 Generate Docs'),
    ('gen_task_id', ''), ('gen_running', False), ('gen_last_progress', {})
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.request_clear_repo_input:
    st.session_state.repo_url_input = ""
    st.session_state.request_clear_repo_input = False

# --- SIDEBAR ---
with st.sidebar:
    st.title("Side Menu")
    if st.button("Start New Session"):
        for key in ['session_id', 'chat_history', 'gen_task_id', 'repo_url_input']:
            st.session_state[key] = [] if key == 'chat_history' else ''
        st.session_state.gen_running = False
        st.session_state.gen_last_progress = {}
        st.success("Session cleared.")
        st.rerun()

    st.divider()
    st.subheader("📑 Navigation")
    current_tab = st.session_state.active_tab if st.session_state.active_tab in TAB_OPTIONS else TAB_OPTIONS[0]
    selected_tab = st.radio("Select Tab:", TAB_OPTIONS, index=TAB_OPTIONS.index(current_tab))
    if selected_tab != st.session_state.active_tab:
        st.session_state.active_tab = selected_tab
        st.rerun()

# --- TITLE ---
st.title("Agentic Codebase :blue[Genius] :sunglasses:")

# --- TABS ---
if st.session_state.active_tab == "📄 Generate Docs":
    st.header("📄 Generate Docs")
    render_status_dashboard()

    st.subheader("📄 Generate Docs from Repo")
    repo_url = st.text_input("Enter GitHub repo URL:", key="repo_url_input", disabled=st.session_state.gen_running)
    force_rerun = st.checkbox("Force re-run (skip duplicate check)", disabled=st.session_state.gen_running)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Generation", disabled=st.session_state.gen_running):
            if not repo_url:
                st.warning("Please enter a repo URL.")
            elif not is_valid_github_url(repo_url):
                st.error("Enter a valid GitHub URL")
            else:
                # Check for duplicates
                jobs = get_workflow_jobs()
                new_key = normalize_repo_key(repo_url)
                already_completed = any(
                    str(j.get("status", "")).lower() == "completed" and
                    normalize_repo_key(j.get("repo_url", "")) == new_key
                    for j in jobs
                ) if not force_rerun else False

                if already_completed:
                    st.error("Repository already processed. Use 'Force re-run' to process again.")
                else:
                    task_id = str(uuid.uuid4())
                    st.session_state.gen_task_id = task_id
                    st.session_state.gen_running = True
                    st.session_state.gen_last_progress = {"status": "starting", "percent": 0}
                    threading.Thread(target=lambda: api_call("generate", {"repo_url": repo_url, "task_id": task_id}), daemon=True).start()
                    st.rerun()

    with col2:
        if st.session_state.gen_running and st.button("Cancel"):
            api_call("cancel", {"task_id": st.session_state.gen_task_id})
            st.session_state.gen_running = False
            st.session_state.gen_last_progress = {"status": "canceled"}
            st.session_state.request_clear_repo_input = True
            st.rerun()

    # Progress monitoring
    if st.session_state.gen_running and st.session_state.gen_task_id:
        with st.spinner("Processing..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            for _ in range(180):
                progress_data = api_call("progress", {"task_id": st.session_state.gen_task_id})
                if progress_data:
                    parsed = parse_api_response(progress_data)
                    if isinstance(parsed, dict):
                        st.session_state.gen_last_progress = parsed
                        pct = int(parsed.get("percent", 0))
                        progress_bar.progress(min(pct, 100))
                        stage = parsed.get("stage", "")
                        stage_text = STAGE_LABELS.get(stage, stage)
                        msg = parsed.get("message", "")
                        status = parsed.get("status", "unknown")
                        badge = render_badge(status)
                        status_text.markdown(f"Status: {badge} — {pct}% {f'| {stage_text}' if stage_text else ''} {f'| {msg}' if msg else ''}", unsafe_allow_html=True)
                        if pct >= 100 or status in {"done", "error", "canceled", "completed"}:
                            st.session_state.gen_running = False
                            if status in {"done", "completed"} and pct >= 100:
                                st.session_state.request_clear_repo_input = True
                            break
                time.sleep(1)

    # Results display
    progress = st.session_state.gen_last_progress
    doc_path = progress.get("doc_path") or progress.get("doc")
    if isinstance(doc_path, str) and doc_path and os.path.exists(doc_path):
        st.success("Documentation generated!")
        st.write(f"Saved at: {doc_path}")
        st.session_state.request_clear_repo_input = True

        out_dir = os.path.dirname(doc_path)
        if st.button("Open Folder"):
            try:
                os.startfile(out_dir) if os.name == "nt" else subprocess.Popen(["open" if os.name == "posix" else "xdg-open", out_dir])
            except Exception as e:
                st.warning(f"Couldn't open folder: {e}")

        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                md_content = f.read()
            st.markdown(md_content, unsafe_allow_html=True)
            st.download_button("Download Markdown", md_content, file_name=os.path.basename(doc_path))
        except Exception as e:
            st.info(f"Unable to preview docs: {e}")
    elif progress.get("status") == "error":
        st.error(f"Generation failed: {progress.get('message', 'unknown error')}")
    elif progress.get("status") not in (None, "unknown"):
        stage = progress.get("stage", "")
        stage_text = STAGE_LABELS.get(stage, stage)
        msg = progress.get("message", "")
        badge = render_badge(progress.get("status", "unknown"))
        st.markdown(f"Status: {badge} {f'| {stage_text}' if stage_text else ''} {f'| {msg}' if msg else ''}", unsafe_allow_html=True)

elif st.session_state.active_tab == "📋 Workflow Status":
    st.header("📋 Workflow Status")

    cols = st.columns([1, 2, 3])
    with cols[0]:
        wf_status_filter = st.multiselect(
            "Filter Status",
            options=["canceled", "completed", "error", "in_progress", "pending"],
            default=[],
            help="Leave empty to show all"
        )

    with st.spinner("Loading workflow status..."):
        jobs = get_workflow_jobs()
        if jobs:
            if wf_status_filter:
                has_any_status_values = any(isinstance(j.get("status"), str) and j.get("status").strip() for j in jobs)
                if not has_any_status_values:
                    st.info("Status field is missing in the returned data, so the status filter can't be applied. Showing all jobs.")
                else:
                    lowered = set([s.lower() for s in wf_status_filter])
                    filtered = [j for j in jobs if str(j.get("status", "")).lower() in lowered]
                    if not filtered:
                        available = sorted({str(j.get("status", "")).lower() for j in jobs if str(j.get("status", "")).strip()})
                        st.info(f"No jobs match the selected status filter. Available statuses in data: {', '.join(available) or 'none'}.")
                        jobs = []
                    else:
                        jobs = filtered

            if not jobs:
                st.info("No jobs to display with the current filters.")
            else:
                start_idx, end_idx, current_page = paginate(len(jobs), "wf_page", 10, "Page")

                # Show snapshot and recent jobs only on first page
                render_status_dashboard(show_snapshot=False)

                page_items = jobs[start_idx:end_idx]

                for j in page_items:
                    proj = get_project_name(j) or "N/A"
                    job_id = j.get("id", j.get("job_id", ""))
                    date = j.get("date", "N/A")
                    agent = j.get("agent", "N/A")
                    status = j.get("status", "N/A")
                    details = j.get("details", {}) or {}
                    doc_path = details.get("doc_path")
                    has_doc = isinstance(doc_path, str) and doc_path and os.path.exists(doc_path)
                    folder = os.path.dirname(doc_path) if has_doc else ""

                    # Row layout
                    with st.container():
                        c1, c2, c3, c4 = st.columns([4, 2, 2, 4])
                        c1.markdown(f"**{proj}**\n\n<small>{date}</small>", unsafe_allow_html=True)
                        c2.write(agent)
                        c3.markdown(render_badge(str(status)), unsafe_allow_html=True)
                        btn_col1, btn_col2 = c4.columns([1, 1])

                        # Open folder button
                        open_disabled = not folder or not os.path.exists(folder)
                        if btn_col1.button("Repo Download", key=f"open_{job_id}", disabled=open_disabled):
                            try:
                                os.startfile(folder) if os.name == "nt" else subprocess.Popen(["open" if os.name == "posix" else "xdg-open", folder])
                            except Exception as e:
                                st.warning(f"Couldn't open folder: {e}")

                        # Download markdown button
                        if has_doc:
                            try:
                                with open(doc_path, "r", encoding="utf-8") as f:
                                    md_data = f.read()
                                btn_col2.download_button("Download markdown", md_data, file_name=os.path.basename(doc_path), key=f"dl_{job_id}")
                            except Exception as e:
                                btn_col2.button("Download markdown", key=f"dl_{job_id}", disabled=True)
                        else:
                            btn_col2.button("Download markdown", key=f"dl_{job_id}", disabled=True)

                    st.divider()
        else:
            st.info("No ongoing jobs found.")

elif st.session_state.active_tab == "📚 Docs Review":
    st.header("📚 Docs Review")
    render_status_dashboard(show_snapshot=False)

    srch_col1, srch_col2 = st.columns([3, 1])
    with srch_col1:
        docrev_query = st.text_input("Search by project name", key="docrev_query")

    with st.spinner("Loading documentation list..."):
        jobs = get_workflow_jobs()
        completed = [j for j in jobs if str(j.get("status", "")).lower() == "completed"]
        items = []
        for j in completed:
            proj = get_project_name(j) or ""
            details = j.get("details", {}) if isinstance(j.get("details"), dict) else {}
            items.append({
                "job": j,
                "project": proj,
                "doc_path": details.get("doc_path"),
            })

        q = (docrev_query or "").strip().lower()
        if q:
            items = [it for it in items if q in (it.get("project") or "").lower()]

        # Pagination
        start, end, _ = paginate(len(items), "docrev_page", 10, "Page")
        page_items = items[start:end]

        if not page_items:
            st.info("No matching completed documents.")
        else:
            for it in page_items:
                j = it["job"]
                proj = it.get("project") or "(unknown)"
                details = j.get("details", {}) if isinstance(j.get("details"), dict) else {}
                doc_path = it.get("doc_path")
                job_id = j.get("id", j.get("job_id", ""))
                date = j.get("date", details.get("ended_at") or details.get("started_at") or "N/A")
                with st.expander(f"{proj}"):
                    st.write(f"Date: {date}")
                    st.write(f"Task id: {job_id}")
                    if isinstance(doc_path, str) and doc_path and os.path.exists(doc_path):
                        try:
                            with open(doc_path, "r", encoding="utf-8") as f:
                                md = f.read()
                            st.markdown(md, unsafe_allow_html=True)
                            st.download_button("Download markdown", md, file_name=os.path.basename(doc_path), key=f"dl_docrev_{job_id}")
                        except Exception as e:
                            st.warning(f"Couldn't load documentation: {e}")
                    else:
                        st.info("Documentation file not found for this task.")

elif st.session_state.active_tab == "📈 Repo History":
    st.header("📈 Repo History")
    render_status_dashboard(show_snapshot=False)

    @st.cache_data(ttl=10)
    def _fetch_all_jobs_cached():
        return get_workflow_jobs()

    def _repo_label_from_job(j: dict) -> str:
        url = j.get("repo_url") or (j.get("details", {}) or {}).get("repo_url") or ""
        key = normalize_repo_key(url)
        # turn github.com/owner/repo -> owner/repo
        if key and key.count('/') >= 2:
            parts = key.split('/')
            return f"{parts[1]}/{parts[2]}"
        return ""

    def _parse_job_date(j: dict):
        for field in ("date", "ended_at", "started_at"):
            val = j.get(field) or (j.get("details", {}) or {}).get(field)
            if isinstance(val, str) and val.strip():
                s = val.strip()
                try:
                    # tolerate Z suffix
                    s2 = s.replace("Z", "+00:00")
                    return datetime.fromisoformat(s2)
                except Exception:
                    pass
        return None
    jobs_all = _fetch_all_jobs_cached()
    repo_opts = sorted({lbl for lbl in (_repo_label_from_job(j) for j in jobs_all) if lbl})
    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        sel_repos = st.multiselect(
            "Filter by repo",
            options=repo_opts,
            default=repo_opts,
            help="Select one or more repositories to include"
        )
    with c2:
        range_choice = st.selectbox("Range", options=[7, 14, 30, 90, "All"], index=2, help="Days to include")
    with c3:
        hist_auto = st.checkbox("Auto-refresh", key="hist_auto", value=st.session_state.get("hist_auto", False))
        hist_interval = st.select_slider("Interval (sec)", options=[5, 10, 15, 30, 60], value=st.session_state.get("hist_interval", 15), key="hist_interval")

    if hist_auto:
        nxt = st.session_state.get("hist_next_ts")
        now = time.time()
        if not nxt or now >= float(nxt):
            st.session_state["hist_next_ts"] = now + int(st.session_state.get("hist_interval", 15) or 15)
            _rr = getattr(st, "rerun", None) or getattr(st, "experimental_rerun", None)
            if callable(_rr):
                try:
                    _rr()
                except Exception:
                    pass

    jobs = [j for j in jobs_all if (not sel_repos or _repo_label_from_job(j) in sel_repos)]

    end_dt = datetime.now(timezone.utc)
    if range_choice != "All":
        days = int(range_choice)
        start_dt = end_dt - timedelta(days=days - 1)
    else:
        dates = [d for d in (_parse_job_date(j) for j in jobs) if d]
        if dates:
            start_dt = min(dates)
        else:
            start_dt = end_dt - timedelta(days=29)
    def _bucket(status: str) -> str:
        s = (status or "").lower()
        if s in {"completed", "done"}: return "Completed"
        if s in {"pending", "in_progress"}: return "Pending"
        if s == "canceled": return "Canceled"
        if s in {"error", "timeout"}: return "Error"
        return "Pending"

    def _daterange(start: datetime, end: datetime):
        cur = datetime(year=start.year, month=start.month, day=start.day)
        last = datetime(year=end.year, month=end.month, day=end.day)
        while cur <= last:
            yield cur
            cur = cur + timedelta(days=1)

    x_dates = [d.strftime("%Y-%m-%d") for d in _daterange(start_dt, end_dt)]
    counts: dict[str, dict[str, int]] = {x: {"Completed": 0, "Pending": 0, "Error": 0, "Canceled": 0} for x in x_dates}

    for j in jobs:
        dt = _parse_job_date(j)
        if not dt:
            continue
        day = datetime(year=dt.year, month=dt.month, day=dt.day)
        if day < datetime(year=start_dt.year, month=start_dt.month, day=start_dt.day) or day > datetime(year=end_dt.year, month=end_dt.month, day=end_dt.day):
            continue
        key = day.strftime("%Y-%m-%d")
        b = _bucket(str(j.get("status", "")))
        counts[key][b] = counts[key].get(b, 0) + 1

    series_completed = [counts[d]["Completed"] for d in x_dates]
    series_pending = [counts[d]["Pending"] for d in x_dates]
    series_error = [counts[d]["Error"] for d in x_dates]
    series_canceled = [counts[d]["Canceled"] for d in x_dates]

    chart_height = 420
    echarts_html = f"""
    <div id='repo_hist' style='width:100%;height:{chart_height}px;'></div>
    <div style='margin-top:8px;'>
      <button id='dl_png' style='padding:6px 10px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer;'>Download PNG</button>
    </div>
    <script src='https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js'></script>
    <script>
      const el = document.getElementById('repo_hist');
      const chart = echarts.init(el);
      const option = {{
        backgroundColor: '#fff',
        tooltip: {{ trigger: 'axis' }},
        legend: {{ data: ['Completed','Pending','Error','Canceled'] }},
        grid: {{ left: '3%', right: '4%', bottom: '8%', containLabel: true }},
        xAxis: {{ type: 'category', boundaryGap: false, data: {json.dumps(x_dates)} }},
        yAxis: {{ type: 'value' }},
        series: [
          {{ name: 'Completed', type: 'line', smooth: true, data: {json.dumps(series_completed)}, lineStyle: {{ width: 2 }}, color: '#2ca02c' }},
          {{ name: 'Pending', type: 'line', smooth: true, data: {json.dumps(series_pending)}, lineStyle: {{ width: 2 }}, color: '#1f77b4' }},
          {{ name: 'Error', type: 'line', smooth: true, data: {json.dumps(series_error)}, lineStyle: {{ width: 2 }}, color: '#d62728' }},
          {{ name: 'Canceled', type: 'line', smooth: true, data: {json.dumps(series_canceled)}, lineStyle: {{ width: 2 }}, color: '#7f7f7f' }}
        ]
      }};
      chart.setOption(option);
      window.addEventListener('resize', () => chart.resize());
      const dl = document.getElementById('dl_png');
      dl.addEventListener('click', () => {{
        const url = chart.getDataURL({{ type: 'png', pixelRatio: 2, backgroundColor: '#fff' }});
        const a = document.createElement('a');
        a.href = url;
        a.download = 'repo_history.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }});
    </script>
    """
    components_html(echarts_html, height=chart_height + 60)

    st.caption("Data shown: daily counts by status within the selected range. Uses a small 10s cache to reduce backend calls.")


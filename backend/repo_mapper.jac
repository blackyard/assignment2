import from py_modules.repo_utils { is_valid_github_url as py_is_valid_github_url, generate_file_tree as py_generate_file_tree, summarize_readme as py_summarize_readme }
import from py_modules.repo_cache { ensure_cached_repo as py_ensure_cached_repo }

node RepoMapper {
	def clone_and_map(github_link: str) -> dict {
		if not py_is_valid_github_url(url=github_link) {
			report {"error": "Invalid GitHub URL"};
			disengage;
		}
		repo_path = py_ensure_cached_repo(task_id="", url=github_link, refresh=False, timeout=180, depth=1);
		if not repo_path {
			report {"error": "Clone failed"};
			disengage;
		}
		tree = py_generate_file_tree(repo_path=repo_path);
		if not tree {
			report {"error": "File tree generation failed"};
			disengage;
		}
		readme = py_summarize_readme(repo_path=repo_path);
		return {"path": repo_path, "file_tree": tree, "readme": readme};
	}
}


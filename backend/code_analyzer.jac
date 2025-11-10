node CodeAnalyzer {
    # Analyze a repository 
    def analyze_tree(repo_path: str, file_tree: dict) -> list;

   
    def query_calls(files: list, target: str) -> list;

    
    def query_inheritance(files: list, class_name: str) -> list;
}

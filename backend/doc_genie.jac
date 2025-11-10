import from byllm.llm { Model }
import from dotenv { load_dotenv }
import os;
import from py_modules.docs_saver { build_and_save_docs }

glob llm: Model = Model(model_name='gemini/gemini-2.0-flash', verbose=False);

node DocGenie {
    # Generate enhanced markdown docs 
    def generate(repo_path: str, file_tree: dict, readme: str, files: list) -> str;

    # Generate LLM-powered documentation 
    def generate_llm_docs(repo_name: str, file_tree: dict, readme: str, files: list) -> str;

    
    def generate_code_descriptions(files: list) -> dict;

    
    def generate_architecture_overview(repo_name: str, file_tree: dict, files: list) -> str;

    
    def build_comprehensive_documentation(repo_name: str, file_tree: dict, readme: str, files: list, executive_summary: str, comprehensive_overview: str, architecture_overview: str, code_descriptions: dict, diagram_result: dict) -> str;

    # Structured documentation sections
    def generate_installation_guide(repo_name: str, file_tree: dict, readme: str) -> str;
    def generate_usage_guide(repo_name: str, readme: str, files: list) -> str;
    def generate_api_reference(repo_name: str, files: list, code_descriptions: dict) -> str;

   
    def describe_diagram(diagram_result: dict) -> str;
    def extract_key_features(files: list) -> str;
}

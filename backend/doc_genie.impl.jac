import from py_modules.docs_saver { build_and_save_docs as py_build_and_save_docs }

node DocsApi {
    def build_and_save_docs(repo_path: str, file_tree: dict, readme: str, files: list) -> str;
}

impl DocsApi.build_and_save_docs { return py_build_and_save_docs(repo_path=repo_path, file_tree=file_tree, readme=readme, files=files); }


def llm_generate(prompt_type: str, **kwargs): str by llm(model_name='gemini/gemini-2.0-flash');

# Wrapper functions 
def generate_code_description(code: str, language: str) -> str {
    return llm_generate("code_description", code=code, language=language);
}

def generate_architecture_description(codebase_summary: str, file_structure: str) -> str {
    return llm_generate("architecture", codebase_summary=codebase_summary, file_structure=file_structure);
}

def generate_function_description(function_code: str, language: str) -> str {
    return llm_generate("function", function_code=function_code, language=language);
}

def generate_class_description(class_code: str, language: str) -> str {
    return llm_generate("class", class_code=class_code, language=language);
}

def generate_comprehensive_system_overview(repo_name: str, readme: str, architecture_desc: str, diagram_description: str) -> str {
    return llm_generate("system_overview", repo_name=repo_name, readme=readme, architecture_desc=architecture_desc, diagram_description=diagram_description);
}

def generate_executive_summary(repo_name: str, overview: str, key_features: str) -> str {
    return llm_generate("executive_summary", repo_name=repo_name, overview=overview, key_features=key_features);
}

def generate_installation_guide(repo_name: str, file_tree: dict, readme: str) -> str {
    return llm_generate("installation", repo_name=repo_name, file_tree=file_tree, readme=readme);
}

def generate_usage_guide(repo_name: str, readme: str, files: list) -> str {
    return llm_generate("usage", repo_name=repo_name, readme=readme, files=files);
}

def generate_api_reference(repo_name: str, files: list, code_descriptions: dict) -> str {
    return llm_generate("api_reference", repo_name=repo_name, files=files, code_descriptions=code_descriptions);
}

impl DocGenie.generate {
    repo_name = os.path.basename(repo_path.rstrip(os.sep)) or "repo";

    # LLM-powered documentation
    llm_docs = self.generate_llm_docs(repo_name, file_tree, readme, files);

    doc_path = self.save_llm_docs(repo_name, llm_docs);

    return doc_path;
}

impl DocGenie.generate_llm_docs(repo_name: str, file_tree: dict, readme: str, files: list) -> str {

    try {
        diagram_result = self.generate_architecture_diagram(repo_name, files);
        diagram_description = self.describe_diagram(diagram_result);

        architecture_overview = self.generate_architecture_overview(repo_name, file_tree, files);

        comprehensive_overview = generate_comprehensive_system_overview(repo_name, readme, architecture_overview, diagram_description);

        key_features = self.extract_key_features(files);
        executive_summary = generate_executive_summary(repo_name, comprehensive_overview, key_features);
        
        installation_guide = self.generate_installation_guide(repo_name, file_tree, readme);
        usage_guide = self.generate_usage_guide(repo_name, readme, files);

        api_reference = self.generate_api_reference(repo_name, files, code_descriptions);
        code_descriptions = self.generate_code_descriptions(files);

        # Complete integrated documentation
        md = self.build_documentation(repo_name, file_tree, readme, files, executive_summary, comprehensive_overview, architecture_overview, code_descriptions, diagram_result, installation_guide, usage_guide, api_reference, True);

        return md;
    } catch e {
        # Fallback 
        return self.generate_fallback_docs(repo_name, file_tree, readme, files, diagram_result);
    }
}

impl DocGenie.generate_fallback_docs(repo_name: str, file_tree: dict, readme: str, files: list, diagram_result: dict) -> str {
    # Generate basic documentation 
    return self.build_documentation(repo_name, file_tree, readme, files, "", "", "", {}, diagram_result, "", "", "", False);
}

impl DocGenie.generate_code_descriptions(files: list) -> dict {
    descriptions = {};

    for f in files {
        if f["language"] in ["python", "javascript", "typescript", "java", "cpp", "c", "csharp", "go", "rust"] {
            # Generate descriptions for the entire file
            file_descriptions = self.analyze_file_with_llm(f);
            descriptions[f["path"]] = file_descriptions;
        }
    }

    return descriptions;
}

impl DocGenie.analyze_file_with_llm(file_data: dict) -> dict {
    code_content = file_data.get("content", "");
    language = file_data.get("language", "unknown");
    relationships = file_data.get("relationships", {});

    if not code_content {
        return {"classes": {}, "functions": {}, "modules": {}};
    }
    
    description = generate_code_description(code_content, language);

    structured_desc = self.parse_llm_description(description, relationships);

    return structured_desc;
}

impl DocGenie.parse_llm_description(description: str, relationships: dict) -> dict {
    
    classes = {};
    functions = {};
    modules = {};

    if relationships.get("classes") {
        for cls in relationships["classes"] {
            class_name = cls.get("name", "Unknown");
            classes[class_name] = f"Class {class_name} - {description}";
        }
    }

    if relationships.get("functions") {
        for func in relationships["functions"] {
            func_name = func.get("name", "Unknown");
            functions[func_name] = f"Function {func_name} - {description}";
        }
    }

    return {"classes": classes, "functions": functions, "modules": modules, "overview": description};
}

impl DocGenie.generate_architecture_overview(repo_name: str, file_tree: dict, files: list) -> str {
    file_summary = self.summarize_codebase(files);
    structure_summary = self.summarize_file_structure(file_tree);

    architecture_desc = generate_architecture_description(file_summary, structure_summary);

    return architecture_desc;
}

impl DocGenie.describe_diagram(diagram_result: dict) -> str {
    # Create a text description 
    svg_path = diagram_result.get("svg_path", "");
    mermaid_code = diagram_result.get("mermaid_code", "");

    if svg_path {
        return "A visual architecture diagram has been generated showing the code relationships and dependencies between files in the codebase.";
    } else if mermaid_code {
        return "A code context graph diagram is available showing the relationships between different files and their dependencies.";
    } else {
        return "Architecture diagrams are available to visualize the codebase structure.";
    }
}

impl DocGenie.extract_key_features(files: list) -> str {
    languages = {};
    frameworks = [];
    patterns = [];

    for f in files {
        lang = f.get("language", "unknown");
        if languages.get(lang) {
            languages[lang] = languages[lang] + 1;
        } else {
            languages[lang] = 1;
        }

        # Framework hints from filenames and content
        filename = f.get("path", "").lower();
        if "react" in filename or "jsx" in filename or "tsx" in filename {
            frameworks.append("React");
        }
        if "django" in filename or "flask" in filename {
            frameworks.append("Python Web Framework");
        }
        if "jac" in filename {
            frameworks.append("Jac Language");
        }
    }

    features = "Languages: " + ", ".join([f"{lang} ({count} files)" for lang, count in languages.items()]);
    if frameworks {
        features = features + ". Frameworks/Libraries: " + ", ".join(set(frameworks));
    }

    return features;
}
    # Mermaid fallback
    diagram_result = {"svg_path": "", "mermaid_code": ""};

    try {
        from py_modules.diagram_builder import build_ccg_graph;
        svg_path = build_ccg_graph(repo_name, files);
        diagram_result["svg_path"] = svg_path;
    } catch e {
        
    }

    try {
        mermaid_code = self.build_mermaid_graph(files);
        diagram_result["mermaid_code"] = mermaid_code;
    } catch e {
        # Mermaid generation failed
    }

    return diagram_result;
}

impl DocGenie.build_mermaid_graph(files: list) -> str {
    
    try {
        # Collect nodes by group and edges
        groups = {};
        edges = [];

        for f in files {
            src_path = f.get("path", "");
            if not src_path {
                continue;
            }

            # Group by top directory
            parts = src_path.replace("\\", "/").split("/");
            grp = parts[0] if len(parts) > 0 else "root";

            if not groups.get(grp) {
                groups[grp] = [];
            }
            groups[grp].append(src_path);

            # Collect relationships
            rels = f.get("relationships", {});
            calls = rels.get("calls", []);
            inherits = rels.get("inherits", []);
            imports = rels.get("imports", []);

            for callee in calls {
                if callee {
                    edges.append({"src": src_path, "dst": callee, "type": "calls"});
                }
            }

            for parent in inherits {
                if parent {
                    edges.append({"src": src_path, "dst": parent, "type": "inherits"});
                }
            }

            for imp in imports {
                if imp {
                    edges.append({"src": src_path, "dst": imp, "type": "imports"});
                }
            }
        }

        # Build Mermaid code
        mermaid_lines = ["```mermaid", "graph LR"];
        mermaid_lines.append("%% Relationships: calls = -->, inherits = ==>, imports = -.->");

        # Add subgraphs
        for grp, paths in groups.items() {
            mermaid_lines.append(f"  subgraph {grp}");
            for p in paths {
                node_id = p.replace("`", "").replace("\"", "").replace("'", "").replace(" ", "_");
                basename = p.split("/")[-1] if "/" in p else p;
                mermaid_lines.append(f"    {node_id}[\"{basename}\"]");
            }
            mermaid_lines.append("  end");
        }

        # Add edges (limit for readability)
        max_edges = 50;
        edge_count = 0;
        for edge in edges {
            if edge_count >= max_edges {
                mermaid_lines.append("  %% (edges truncated for readability)");
                break;
            }

            src_id = edge["src"].replace("`", "").replace("\"", "").replace("'", "").replace(" ", "_");
            dst_id = edge["dst"].replace("`", "").replace("\"", "").replace("'", "").replace(" ", "_");
            edge_type = edge["type"];

            arrow = "-->" if edge_type == "calls" else ("==>" if edge_type == "inherits" else "-.->");
            mermaid_lines.append(f"  {src_id} {arrow} {dst_id}");
            edge_count = edge_count + 1;
        }

        mermaid_lines.append("```");
        return "\n".join(mermaid_lines) + "\n";

    } catch e {
        return f"_Mermaid graph generation failed: {e}_\n";
    }
}

impl DocGenie.summarize_codebase(files: list) -> str {
    summary = "";
    lang_count = {};

    for f in files {
        lang = f.get("language", "unknown");
        if lang_count.get(lang) {
            lang_count[lang] = lang_count[lang] + 1;
        } else {
            lang_count[lang] = 1;
        }
    }

    summary = "Languages used:\n";
    for lang, count in lang_count.items() {
        summary = summary + f"- {lang}: {count} files\n";
    }

    summary = summary + f"\nTotal files analyzed: {len(files)}\n";

    return summary;
}

impl DocGenie.summarize_file_structure(file_tree: dict) -> str {
    # Convert file tree dict to readable string
    lines = [];
    self.flatten_tree(file_tree, "", lines);
    return "\n".join(lines);
}

impl DocGenie.flatten_tree(tree: dict, prefix: str, lines: list) {
    for key, val in tree.items() {
        if key == "_files" {
            for f in val {
                lines.append(prefix + "- " + f);
            }
        } else {
            lines.append(prefix + key + "/");
            self.flatten_tree(val, prefix + "  ", lines);
        }
    }
}

impl DocGenie.build_documentation(repo_name: str, file_tree: dict, readme: str, files: list, executive_summary: str, comprehensive_overview: str, architecture_overview: str, code_descriptions: dict, diagram_result: dict, installation_guide: str, usage_guide: str, api_reference: str, use_llm: bool) -> str {
    md = [];

    # Title and Executive Summary
    title_prefix = "📖 Comprehensive Documentation:" if use_llm else "📚 Enhanced Documentation for";
    md.append(f"# {title_prefix} `{repo_name}`\n");
    md.append("---\n");

    if use_llm {
        md.append("## 📋 Executive Summary\n");
        md.append(executive_summary);
        md.append("\n---\n");

        # Project Overview
        md.append("## 🧭 Project Overview\n");
        md.append(comprehensive_overview);
        md.append("\n---\n");

        # Installation Guide
        md.append("## 📦 Installation\n");
        md.append(installation_guide);
        md.append("\n---\n");

        # Usage Guide
        md.append("## 🚀 Usage\n");
        md.append(usage_guide);
        md.append("\n---\n");
    } else {
        # Executive summary 
        key_features = self.extract_key_features(files);
        md.append("## 📋 Executive Summary\n");
        md.append(f"This documentation provides a comprehensive analysis of the `{repo_name}` codebase. ");
        md.append(f"The system is built using {key_features}. ");
        md.append("While advanced AI analysis is currently unavailable, this document includes visual architecture diagrams and detailed code analysis.\n\n");
        md.append("---\n");

        # System Overview
        md.append("## 🏗️ System Architecture & Overview\n");
        md.append(readme or "This repository contains software code that has been automatically analyzed.");
        md.append("\n\n");
        md.append("### Key Technologies\n");
        md.append(key_features);
        md.append("\n\n");
    }

    # System Architecture & Visual Diagrams
    if use_llm {
        md.append("## 🏗️ System Architecture\n");
        md.append("### Architecture Overview\n");
        md.append(architecture_overview);
        md.append("\n");
    }

    # Visual Architecture Diagram
    svg_path = diagram_result.get("svg_path", "");
    mermaid_code = diagram_result.get("mermaid_code", "");

    diagram_title = "📊 Code Context Graph" if use_llm else "📊 Architecture Diagram";
    description = "*This visual representation shows function calls (blue), inheritance relationships (red), and composition relationships (purple) between system components.*" if use_llm else "*This visual representation shows how different parts of the system interact and depend on each other.*";

    if svg_path {
        svg_filename = os.path.basename(svg_path);
        md.append(f"### {diagram_title}\n");
        md.append("The following diagram illustrates the relationships and dependencies between components:\n\n");
        md.append(f"![System Architecture]({svg_filename})\n\n");
        md.append(f"{description}\n\n");
        if mermaid_code {
            md.append("<details><summary>📈 Interactive Diagram (Mermaid)</summary>\n\n");
            md.append(mermaid_code);
            md.append("</details>\n\n");
        }
    } else if mermaid_code {
        md.append(f"### 📊 System Architecture\n");
        md.append(mermaid_code);
        md.append("\n");
    }

    if not use_llm {
        
        md.append("### 🏛️ Architecture Analysis\n");
        md.append("The codebase has been analyzed for structural relationships and dependencies. ");
        md.append("The architecture diagram above shows how different files and components interact.\n\n");
    }

    md.append("## 📁 Project Structure\n");
    if file_tree {
        md.append("<details><summary>📂 Complete File Tree</summary>\n\n");
        md.append("```\n" + self.summarize_file_structure(file_tree) + "\n```\n");
        md.append("</details>\n\n");
    }

    if use_llm {
        md.append("---\n");
        md.append("## 📚 API Reference\n");
        md.append(api_reference);
        md.append("\n---\n");
    }

    # Code Documentation
    section_title = "💻 Implementation Details" if use_llm else "💻 Code Components";
    section_desc = "This section provides detailed analysis of the source files and their technical implementation:" if use_llm else "Detailed analysis of each source file:";

    md.append(f"## {section_title}\n");
    md.append(f"{section_desc}\n\n");

    if files {
        for f in files {
            md.append(f"### 📄 `{f['path']}`\n");
            md.append(f"**Language:** {f['language']}\n\n");

            if use_llm {
                file_desc = code_descriptions.get(f['path'], {});
                if file_desc.get('overview') {
                    md.append("**📝 Overview:**\n");
                    md.append(file_desc['overview']);
                    md.append("\n\n");
                }

                # Classes
                if file_desc.get('classes') and len(file_desc['classes']) > 0 {
                    md.append("**🏗️ Classes:**\n");
                    for cls_name, desc in file_desc['classes'].items() {
                        md.append(f"- **{cls_name}**: {desc}\n");
                    }
                    md.append("\n");
                }

                # Functions
                if file_desc.get('functions') and len(file_desc['functions']) > 0 {
                    md.append("**⚡ Functions:**\n");
                    for func_name, desc in file_desc['functions'].items() {
                        md.append(f"- **{func_name}**: {desc}\n");
                    }
                    md.append("\n");
                }
            } else {
                
                md.append("**📝 Description:**\n");
                md.append(f"This {f['language']} file contains code that contributes to the overall system functionality.\n\n");
            }

            # Relationships
            relationships = f.get('relationships', {});
            if relationships {
                md.append("<details><summary>🔧 Technical Implementation Details</summary>\n\n");
                md.append("**Dependencies & Relationships:**\n");
                if relationships.get('calls') {
                    md.append(f"- **{('Calls:' if use_llm else 'Function Calls:')}** {', '.join(relationships['calls'])}\n");
                }
                if relationships.get('inherits') {
                    md.append(f"- **{('Inherits from:' if use_llm else 'Inheritance:')}** {', '.join(relationships['inherits'])}\n");
                }
                if relationships.get('imports') {
                    md.append(f"- **Imports:** {', '.join(relationships['imports'])}\n");
                }
                md.append("\n**Complete Technical Analysis:**\n");
                md.append("```json\n" + json.dumps(relationships, indent=2) + "\n```\n");
                md.append("</details>\n\n");
            }
            md.append("---\n\n");
        }
    } else {
        md.append("_No source files were analyzed for this documentation._\n\n");
    }

    # Summary & Conclusion
    md.append("## 🎯 Summary\n");
    if use_llm {
        md.append("This comprehensive documentation provides a complete guide to the codebase, from installation and usage to detailed API reference. ");
        md.append("The enhanced Code Context Graph visualizes function calls, inheritance, and composition relationships, ");
        md.append("while AI-powered analysis explains the architecture and implementation details.\n\n");

        md.append("---\n");
        md.append("*Generated with AI assistance • Enhanced visual architecture diagrams • Structured documentation with installation, usage, and API reference*\n");
    } else {
        md.append("This documentation provides a structural analysis of the codebase with visual architecture diagrams. ");
        md.append("The diagrams help understand how different components relate to each other, ");
        md.append("while the detailed file analysis shows the technical implementation.\n\n");

        md.append("---\n");
        md.append("*Generated with automated analysis • Includes visual architecture diagrams • Comprehensive code structure*\n");
    }

    return "\n".join(md);
}
    md = [f"# 📚 Enhanced Documentation for `{repo_name}`\n"];

    # Overview section
    md.append("## 🧭 Project Overview\n");
    md.append(readme or "_No README summary available._");
    md.append("\n");

    # Architecture Overview
    md.append("## 🏗️ Architecture Overview\n");
    md.append(architecture_overview);
    md.append("\n");

    # Architecture Diagram
    svg_path = diagram_result.get("svg_path", "");
    mermaid_code = diagram_result.get("mermaid_code", "");

    if svg_path {
        svg_filename = os.path.basename(svg_path);
        md.append("## 📊 Code Context Graph\n");
        md.append(f"![Architecture Diagram]({svg_filename})\n");
        if mermaid_code {
            md.append("<details><summary>Show Mermaid fallback</summary>\n\n");
            md.append(mermaid_code);
            md.append("</details>\n");
        }
        md.append("\n");
    } else if mermaid_code {
        md.append("## 📊 Code Context Graph\n");
        md.append(mermaid_code);
        md.append("\n");
    }

    # File Structure
    md.append("## 📁 File Structure\n");
    if file_tree {
        md.append("<details><summary>Show file tree</summary>\n\n");
        md.append("```\n" + self.summarize_file_structure(file_tree) + "\n```\n");
        md.append("</details>\n");
    } else {
        md.append("_No file structure available._\n");
    }
    md.append("\n");

    # Code Documentation
    md.append("## 💻 Code Documentation\n");
    if files {
        for f in files {
            md.append(f"### {f['path']}\n");
            md.append(f"**Language:** {f['language']}\n\n");

            # LLM-generated 
            file_desc = code_descriptions.get(f['path'], {});
            if file_desc.get('overview') {
                md.append(f"**Overview:** {file_desc['overview']}\n\n");
            }

            if file_desc.get('classes') and len(file_desc['classes']) > 0 {
                md.append("#### Classes\n");
                for cls_name, desc in file_desc['classes'].items() {
                    md.append(f"- **{cls_name}**: {desc}\n");
                }
                md.append("\n");
            }

            if file_desc.get('functions') and len(file_desc['functions']) > 0 {
                md.append("#### Functions\n");
                for func_name, desc in file_desc['functions'].items() {
                    md.append(f"- **{func_name}**: {desc}\n");
                }
                md.append("\n");
            }

            relationships = f.get('relationships', {});
            if relationships {
                md.append("<details><summary>Technical Details</summary>\n\n");
                md.append("```json\n" + json.dumps(relationships, indent=2) + "\n```\n");
                md.append("</details>\n");
            }
            md.append("\n");
        }
    } else {
        md.append("_No source files analyzed._\n");
    }

    return "\n".join(md);
}

impl DocGenie.save_llm_docs(repo_name: str, content: str) -> str {
    try {
        out_dir = os.path.join("outputs", repo_name);
        os.makedirs(out_dir, exist_ok=True);

        doc_path = os.path.join(out_dir, "docs.md");
        with open(doc_path, "w", encoding="utf-8") as f {
            f.write(content);
        }

        return doc_path;
    } catch e {
        return "";
    }
}

impl DocGenie.generate_installation_guide(repo_name: str, file_tree: dict, readme: str) -> str {
    
    try {
        return generate_installation_guide(repo_name, file_tree, readme);
    } catch e {
        
        return f"""### Basic Installation

To set up `{repo_name}` locally:

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd {repo_name}
   ```

2. **Install dependencies:**
   - Check for `requirements.txt`, `package.json`, `setup.py`, or similar dependency files
   - Install using the appropriate package manager for your language

3. **Environment setup:**
   - Copy any `.env.example` files to `.env`
   - Configure necessary environment variables

4. **Run the application:**
   - Follow the usage instructions in the next section

*Note: This is a basic installation guide. Check the project files for specific setup requirements.*""";
    }
}

impl DocGenie.generate_usage_guide(repo_name: str, readme: str, files: list) -> str {
    
    try {
        return generate_usage_guide(repo_name, readme, files);
    } catch e {
        
        return f"""### Basic Usage

After installation, you can use `{repo_name}` as follows:

1. **Start the application:**
   - Look for main entry points in the source files
   - Run the appropriate command based on the project type

2. **Configuration:**
   - Check for configuration files or command-line options
   - Modify settings as needed for your environment

3. **Basic operations:**
   - The application provides core functionality based on the analyzed source files
   - Refer to the API Reference section for detailed function usage

*Note: This is a basic usage guide. Check the README and source code for specific usage instructions.*""";
    }
}

impl DocGenie.generate_api_reference(repo_name: str, files: list, code_descriptions: dict) -> str {
    
    try {
        return generate_api_reference(repo_name, files, code_descriptions);
    } catch e {
        
        md = [];
        md.append("### API Overview\n");
        md.append(f"This section provides a reference for the `{repo_name}` API and key functions.\n\n");

        if files {
            for f in files {
                file_desc = code_descriptions.get(f['path'], {});
                md.append(f"#### {f['path']} ({f['language']})\n");

                # Classes
                if file_desc.get('classes') and len(file_desc['classes']) > 0 {
                    md.append("**Classes:**\n");
                    for cls_name, desc in file_desc['classes'].items() {
                        md.append(f"- `{cls_name}`: {desc}\n");
                    }
                    md.append("\n");
                }

                # Functions
                if file_desc.get('functions') and len(file_desc['functions']) > 0 {
                    md.append("**Functions:**\n");
                    for func_name, desc in file_desc['functions'].items() {
                        md.append(f"- `{func_name}`: {desc}\n");
                    }
                    md.append("\n");
                }

                # Technical details
                relationships = f.get('relationships', {});
                if relationships.get('calls') {
                    md.append(f"**Function Calls:** {', '.join(relationships['calls'])}\n");
                }
                if relationships.get('inherits') {
                    md.append(f"**Inheritance:** {', '.join(relationships['inherits'])}\n");
                }
                md.append("\n---\n");
            }
        }

        return "\n".join(md);
    }
}

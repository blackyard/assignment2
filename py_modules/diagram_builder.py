import os

def build_ccg_graph(repo_name: str, source_files: list) -> str:
    """
    Builds a Code Context Graph (CCG) diagram from source file relationships.
    Saves the diagram as an SVG under ./outputs/<repo_name>/ccg.svg

    Enhanced to show function calls, inheritance, and composition relationships
    with different visual styles for each relationship type.
    """
    # Try Graphviz first
    try:
        import graphviz  # type: ignore
        return _build_with_graphviz(repo_name, source_files)
    except Exception as e:
        print(f"[diagram_builder] graphviz unavailable: {e}")
        # Fall back to networkx + matplotlib
        try:
            return _build_with_networkx(repo_name, source_files)
        except Exception as e2:
            print(f"[diagram_builder] networkx fallback failed: {e2}")
            return ""

def _infer_composition_relationships(source_files: list) -> dict:
    """
    Infer composition relationships from existing analysis data.
    Composition is detected when:
    1. A class calls methods on other class instances (attribute access patterns)
    2. Constructor calls that suggest object composition
    3. Import patterns that indicate composition usage
    """
    compositions = {}

    for f in source_files:
        file_path = f.get("path", "unknown")
        if file_path == "unknown":
            continue

        calls = f.get("relationships", {}).get("calls", [])
        classes = f.get("relationships", {}).get("classes", [])
        functions = f.get("relationships", {}).get("functions", [])

        # Initialize composition list for this file
        compositions[file_path] = []

        # Look for composition patterns in calls
        for call in calls:
            # If a call matches a class name, it might be composition
            # (e.g., self.logger.log() where logger is a composed object)
            if any(cls in call for cls in classes):
                # Check if it's likely an attribute access pattern
                if '.' in call or call in ['__init__', 'append', 'extend']:
                    if call not in classes:  # Avoid self-reference
                        compositions[file_path].append(call)

        # Look for constructor patterns that suggest composition
        for func in functions:
            if func == '__init__':
                # Constructor calls often indicate composition setup
                for call in calls:
                    if call not in ['super', '__init__'] and call not in classes:
                        compositions[file_path].append(call)

    return compositions

def _build_with_graphviz(repo_name: str, source_files: list) -> str:
    """Build diagram using Graphviz with enhanced relationship visualization"""
    import graphviz  # type: ignore

    dot = graphviz.Digraph(comment="Code Context Graph")
    dot.attr(rankdir="LR", size="12,8")

    # Get composition relationships
    compositions = _infer_composition_relationships(source_files)

    # Add nodes for each file with better styling
    for f in source_files:
        file_id = f.get("path", "unknown")
        classes = f.get("relationships", {}).get("classes", [])
        functions = f.get("relationships", {}).get("functions", [])

        # Style nodes based on content
        if classes:
            dot.node(file_id, shape="box", style="filled", fillcolor="lightblue", label=f"{file_id}\\n({len(classes)} classes, {len(functions)} functions)")
        else:
            dot.node(file_id, shape="ellipse", style="filled", fillcolor="lightgreen", label=f"{file_id}\\n({len(functions)} functions)")

    # Add edges for relationships with different styles
    for f in source_files:
        file_id = f.get("path", "unknown")
        calls = f.get("relationships", {}).get("calls", [])
        inherits = f.get("relationships", {}).get("inherits", [])
        file_compositions = compositions.get(file_id, [])

        # Function calls - solid arrows
        for callee in calls:
            if callee and callee != "unknown" and callee not in [file_id]:
                # Check if this call represents composition
                if callee in file_compositions:
                    dot.edge(file_id, callee, label="composes", color="purple", style="dashed", arrowhead="diamond")
                else:
                    dot.edge(file_id, callee, label="calls", color="blue", arrowhead="normal")

        # Inheritance - thick arrows
        for parent in inherits:
            if parent and parent != "unknown":
                dot.edge(file_id, parent, label="inherits", color="red", style="bold", arrowhead="empty")

    # Save diagram
    output_dir = os.path.join("outputs", repo_name)
    os.makedirs(output_dir, exist_ok=True)
    diagram_path = os.path.join(output_dir, "ccg")
    try:
        dot.render(diagram_path, format="svg", cleanup=True)
        return diagram_path + ".svg"
    except Exception as e:
        raise e

def _build_with_networkx(repo_name: str, source_files: list) -> str:
    """Build diagram using NetworkX and Matplotlib with enhanced relationship visualization"""
    try:
        import networkx as nx
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        import numpy as np
    except ImportError as e:
        raise e

    # Get composition relationships
    compositions = _infer_composition_relationships(source_files)

    # Create directed graph
    G = nx.DiGraph()

    # Collect all unique nodes (files + their relationships)
    all_nodes = set()
    relationship_types = {"calls": [], "inherits": [], "composes": []}

    for f in source_files:
        file_path = f.get("path", "unknown")
        all_nodes.add(file_path)
        calls = f.get("relationships", {}).get("calls", [])
        inherits = f.get("relationships", {}).get("inherits", [])
        file_compositions = compositions.get(file_path, [])

        all_nodes.update(calls)
        all_nodes.update(inherits)
        all_nodes.update(file_compositions)

        # Track relationship types for styling
        for callee in calls:
            if callee and callee != "unknown" and callee != file_path:
                rel_type = "composes" if callee in file_compositions else "calls"
                relationship_types[rel_type].append((file_path, callee))

        for parent in inherits:
            if parent and parent != "unknown":
                relationship_types["inherits"].append((file_path, parent))

    # Add all nodes with labels and types
    for node in all_nodes:
        if node and node != "unknown":
            basename = os.path.basename(node) if "/" in node or "\\" in node else node

            # Determine node type
            is_file = any(f.get("path") == node for f in source_files)
            if is_file:
                classes = next((f.get("relationships", {}).get("classes", []) for f in source_files if f.get("path") == node), [])
                functions = next((f.get("relationships", {}).get("functions", []) for f in source_files if f.get("path") == node), [])
                node_type = "file"
                label = f"{basename}\\n({len(classes)} classes, {len(functions)} funcs)"
            else:
                node_type = "entity"
                label = basename

            G.add_node(node, label=label, type=node_type)

    # Add edges with relationship types
    edge_colors = {"calls": "blue", "inherits": "red", "composes": "purple"}
    edge_styles = {"calls": "solid", "inherits": "solid", "composes": "dashed"}

    for rel_type, edges in relationship_types.items():
        for source, target in edges:
            if source in G.nodes and target in G.nodes:
                G.add_edge(source, target, relationship=rel_type, color=edge_colors[rel_type], style=edge_styles[rel_type])

    if len(G.nodes) == 0:
        return ""

    # Create the plot with enhanced styling
    plt.figure(figsize=(14, 10))

    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Draw nodes with different colors based on type
    file_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "file"]
    entity_nodes = [n for n, d in G.nodes(data=True) if d.get("type") == "entity"]

    nx.draw_networkx_nodes(G, pos, nodelist=file_nodes, node_color='lightblue',
                          node_size=2500, alpha=0.8, node_shape='s')
    nx.draw_networkx_nodes(G, pos, nodelist=entity_nodes, node_color='lightgreen',
                          node_size=2000, alpha=0.8, node_shape='o')

    # Draw edges with different colors and styles
    for rel_type in ["calls", "inherits", "composes"]:
        edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("relationship") == rel_type]
        if edges:
            color = edge_colors[rel_type]
            style = edge_styles[rel_type]
            nx.draw_networkx_edges(G, pos, edgelist=edges, edge_color=color,
                                 arrows=True, arrowsize=20, alpha=0.7,
                                 style=style, width=2 if rel_type == "inherits" else 1)

    # Draw labels
    labels = {node: data['label'] for node, data in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold')

    # Draw edge labels
    edge_labels = {}
    for u, v, d in G.edges(data=True):
        rel = d.get("relationship", "")
        if rel == "composes":
            edge_labels[(u, v)] = "composes"
        elif rel == "inherits":
            edge_labels[(u, v)] = "inherits"
        elif rel == "calls":
            edge_labels[(u, v)] = "calls"

    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=7, font_color='darkred')

    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], color='blue', lw=2, label='Function Calls'),
        plt.Line2D([0], [0], color='red', lw=3, label='Inheritance'),
        plt.Line2D([0], [0], color='purple', lw=2, linestyle='--', label='Composition'),
        plt.scatter([], [], c='lightblue', marker='s', s=100, label='Source Files'),
        plt.scatter([], [], c='lightgreen', marker='o', s=100, label='Entities')
    ]
    plt.legend(handles=legend_elements, loc='upper right', fontsize=10)

    plt.title("Code Context Graph - Enhanced Relationships", fontsize=16, fontweight='bold')
    plt.axis('off')
    plt.tight_layout()

    # Save as SVG
    output_dir = os.path.join("outputs", repo_name)
    os.makedirs(output_dir, exist_ok=True)
    diagram_path = os.path.join(output_dir, "ccg_networkx.svg")

    try:
        # Use a more compatible SVG backend
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        plt.savefig(diagram_path, format='svg', bbox_inches='tight', dpi=100)
        plt.close()
        return diagram_path
    except Exception as e:
        plt.close()
        raise e
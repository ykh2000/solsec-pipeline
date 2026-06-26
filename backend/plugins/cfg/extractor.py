import json
import os
from typing import Dict, Any, List, Optional
from slither import Slither
from slither.core.declarations.function import Function
from slither.core.cfg.node import NodeType

class CFGExtractor:
    """
    Control Flow Graph (CFG) Extractor using Slither.
    Extracts, structures, and formats CFGs into JSON, DOT, and Mermaid representations.
    """

    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Target Solidity file not found: {file_path}")
        self.file_path = file_path
        self.slither = Slither(file_path)

    def extract_all_cfgs(self) -> Dict[str, Any]:
        """
        Extracts CFGs for all contracts and functions in the target file.
        Returns a nested dictionary representation.
        """
        contracts_data = {}

        for contract in self.slither.contracts:
            # Skip dependency/inherited library contracts if desired,
            # but usually, we want to extract everything in the user's file.
            contract_data = {
                "name": contract.name,
                "kind": contract.contract_kind,
                "functions": {}
            }

            # Gather both functions and modifiers since modifiers also have CFGs in Slither
            all_callable = list(contract.functions) + list(contract.modifiers)

            for func in all_callable:
                # We skip functions that don't have nodes (e.g. interfaces, abstract functions)
                if not func.nodes:
                    continue

                # Safe name resolution
                if func.name:
                    func_name = func.name
                else:
                    func_type_val = getattr(func, "function_type", None)
                    func_name = f"[{func_type_val.name if func_type_val and hasattr(func_type_val, 'name') else 'UNKNOWN'}]"

                # Safe type resolution
                if func in contract.modifiers:
                    func_type = "modifier"
                else:
                    func_type_val = getattr(func, "function_type", None)
                    if func_type_val is not None:
                        func_type = func_type_val.name if hasattr(func_type_val, "name") else str(func_type_val)
                    else:
                        func_type = "function"

                func_data = {
                    "name": func_name,
                    "type": func_type,
                    "visibility": func.visibility,
                    "is_shadowed": func.is_shadowed,
                    "state_mutability": getattr(func, "state_mutability", None),
                    "nodes": self._extract_nodes(func),
                    "mermaid": self.generate_mermaid_for_function(func),
                    "dot": self.generate_dot_for_function(contract.name, func)
                }
                contract_data["functions"][func_name] = func_data

            contracts_data[contract.name] = contract_data

        return contracts_data

    def _extract_nodes(self, func: Any) -> List[Dict[str, Any]]:
        """
        Extracts details for each node in a function's CFG.
        """
        nodes_list = []
        for node in func.nodes:
            # Extract source mapping details
            source_lines = []
            if node.source_mapping and hasattr(node.source_mapping, 'lines'):
                source_lines = node.source_mapping.lines

            node_data = {
                "id": node.node_id,
                "type": node.type.name,
                "label": str(node),
                "expression": str(node.expression) if node.expression else None,
                "lines": source_lines,
                "successors": [s.node_id for s in node.sons],
                "predecessors": [f.node_id for f in node.fathers],
                "ir": [str(ir) for ir in node.irs]
            }
            nodes_list.append(node_data)
        return nodes_list

    def generate_dot_for_function(self, contract_name: str, func: Any) -> str:
        """
        Generates a Graphviz DOT representation of the function's CFG.
        """
        func_name = func.name if func.name else f"[{func.type.name}]"
        dot_lines = [f'digraph "{contract_name}_{func_name}" {{']
        dot_lines.append('  node [shape=box, style=filled, color=lightgray, fontname="Courier"];')
        
        # Define Nodes
        for node in func.nodes:
            label = str(node).replace('"', '\\"')
            if node.expression:
                expr = str(node.expression).replace('"', '\\"')
                label = f"{node.type.name}\\n{expr}"
            
            # Highlight Entry and Return/Throw nodes
            color = "lightblue"
            if node.type == NodeType.ENTRYPOINT:
                color = "lightgreen"
                label = "ENTRY_POINT"
            elif node.type in [NodeType.RETURN, NodeType.THROW]:
                color = "pink"

            dot_lines.append(f'  {node.node_id} [label="{label}", fillcolor={color}];')

        # Define Edges
        for node in func.nodes:
            for son in node.sons:
                dot_lines.append(f'  {node.node_id} -> {son.node_id};')

        dot_lines.append("}")
        return "\n".join(dot_lines)

    def generate_mermaid_for_function(self, func: Any) -> str:
        """
        Generates a Mermaid flowchart TD representation of the function's CFG.
        """
        mermaid_lines = ["flowchart TD"]
        
        # Define nodes with appropriate shape styles based on type
        for node in func.nodes:
            # Escape strings for Mermaid safety
            escaped_str = str(node).replace('"', "'")
            if node.expression:
                expr = str(node.expression).replace('"', "'")
                escaped_str = f"{node.type.name}: {expr}"
            
            # Nodes shape styling: 
            # Entry/Exit -> rounded or oval. Conditionals -> diamond. Standard -> rectangle.
            if node.type == NodeType.ENTRYPOINT:
                shape_start, shape_end = "([", "])"
            elif node.type in [NodeType.IF, NodeType.IFLOOP]:
                shape_start, shape_end = "{", "}"
            elif node.type in [NodeType.RETURN, NodeType.THROW]:
                shape_start, shape_end = "[[", "]]"
            else:
                shape_start, shape_end = "[", "]"
                
            mermaid_lines.append(f'  Node{node.node_id}{shape_start}"{escaped_str}"{shape_end}')

        # Define transitions
        for node in func.nodes:
            for son in node.sons:
                # If the parent is a conditional, we label the edges if possible (e.g., true/false branch)
                # Slither's first successor of an IF node is typically True branch, second is False branch.
                edge_label = ""
                if node.type in [NodeType.IF, NodeType.IFLOOP] and len(node.sons) == 2:
                    if son.node_id == node.sons[0].node_id:
                        edge_label = " -- True --> "
                    else:
                        edge_label = " -- False --> "
                
                if edge_label:
                    mermaid_lines.append(f'  Node{node.node_id}{edge_label}Node{son.node_id}')
                else:
                    mermaid_lines.append(f'  Node{node.node_id} --> Node{son.node_id}')

        # Add styling classes
        mermaid_lines.append("  classDef entry fill:#d4edda,stroke:#28a745,stroke-width:2px;")
        mermaid_lines.append("  classDef exit fill:#f8d7da,stroke:#dc3545,stroke-width:2px;")
        mermaid_lines.append("  classDef cond fill:#fff3cd,stroke:#ffc107,stroke-width:2px;")
        
        # Apply styles
        for node in func.nodes:
            if node.type == NodeType.ENTRYPOINT:
                mermaid_lines.append(f"  class Node{node.node_id} entry;")
            elif node.type in [NodeType.RETURN, NodeType.THROW]:
                mermaid_lines.append(f"  class Node{node.node_id} exit;")
            elif node.type in [NodeType.IF, NodeType.IFLOOP]:
                mermaid_lines.append(f"  class Node{node.node_id} cond;")

        return "\n".join(mermaid_lines)

    def export_json(self) -> str:
        """
        Exports the entire CFG set to a JSON string.
        """
        return json.dumps(self.extract_all_cfgs(), indent=2)

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "tests/sample_vulnerable.sol"
    extractor = CFGExtractor(target)
    print(extractor.export_json())

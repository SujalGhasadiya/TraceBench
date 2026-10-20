import ast
from typing import List, Dict, Any, Optional
from .base import BaseParser, ParseResult
from ..models.schemas import CodeSymbol, SymbolType, Relationship, RelationshipType

class PythonASTParser(BaseParser):
    """
    Parses Python source code using Python's built-in AST.
    Provides precise docstring extraction, nested symbol hierarchy, and call extraction.
    """
    
    def parse(self, file_path: str, source_code: str, repo_id: str) -> ParseResult:
        symbols: List[CodeSymbol] = []
        imports: List[str] = []
        calls: List[Dict[str, Any]] = []
        relationships: List[Relationship] = []
        errors: List[str] = []
        
        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            return ParseResult(
                file_path=file_path,
                language="python",
                is_parsed=False,
                errors=[f"SyntaxError at line {e.lineno}, col {e.offset}: {e.msg}"]
            )
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language="python",
                is_parsed=False,
                errors=[f"AST Parse failed: {str(e)}"]
            )
            
        file_node_id = f"{repo_id}:{file_path}"
        
        # Helper to extract call name from an ast.Call node
        def get_call_name(node: ast.Call) -> Optional[str]:
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
            return None

        # Helper to extract all calls inside a block
        def extract_calls_in_node(parent_node: ast.AST, caller_name: str, caller_id: str):
            for child in ast.walk(parent_node):
                if isinstance(child, ast.Call):
                    callee = get_call_name(child)
                    if callee:
                        line_no = getattr(child, "lineno", 1)
                        calls.append({
                            "caller_name": caller_name,
                            "caller_id": caller_id,
                            "callee_name": callee,
                            "line": line_no
                        })
                        relationships.append(
                            Relationship(
                                source_id=caller_id,
                                target_id=callee,  # Will be resolved during graph building
                                relationship_type=RelationshipType.CALLS,
                                provenance="python_ast",
                                confidence=0.85,
                                is_inferred=True,
                                source_location={"file": file_path, "line": line_no}
                            )
                        )

        # Traverse top-level and class-level statements
        for node in ast.iter_child_nodes(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    relationships.append(
                        Relationship(
                            source_id=file_node_id,
                            target_id=alias.name,
                            relationship_type=RelationshipType.IMPORTS,
                            provenance="python_ast",
                            confidence=1.0,
                            is_inferred=False,
                            source_location={"file": file_path, "line": node.lineno}
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                for alias in node.names:
                    full_import = f"{module_name}.{alias.name}" if module_name else alias.name
                    imports.append(full_import)
                    relationships.append(
                        Relationship(
                            source_id=file_node_id,
                            target_id=full_import,
                            relationship_type=RelationshipType.IMPORTS,
                            provenance="python_ast",
                            confidence=1.0,
                            is_inferred=False,
                            source_location={"file": file_path, "line": node.lineno}
                        )
                    )
            # Top-level Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sym_type = SymbolType.ASYNC_FUNCTION if isinstance(node, ast.AsyncFunctionDef) else SymbolType.FUNCTION
                start_l = node.lineno
                end_l = getattr(node, "end_lineno", start_l)
                doc = ast.get_docstring(node)
                sym_id = f"{repo_id}:{file_path}:{node.name}:{start_l}"
                
                symbols.append(
                    CodeSymbol(
                        id=sym_id,
                        repo_id=repo_id,
                        file_path=file_path,
                        language="python",
                        name=node.name,
                        symbol_type=sym_type,
                        start_line=start_l,
                        end_line=end_l,
                        docstring=doc,
                        parent_id=None,
                        signature=f"def {node.name}(...)",
                    )
                )
                relationships.append(
                    Relationship(
                        source_id=file_node_id,
                        target_id=sym_id,
                        relationship_type=RelationshipType.CONTAINS,
                        provenance="python_ast",
                        confidence=1.0,
                        is_inferred=False
                    )
                )
                extract_calls_in_node(node, node.name, sym_id)

            # Classes
            elif isinstance(node, ast.ClassDef):
                cls_start = node.lineno
                cls_end = getattr(node, "end_lineno", cls_start)
                cls_doc = ast.get_docstring(node)
                cls_id = f"{repo_id}:{file_path}:{node.name}:{cls_start}"
                
                symbols.append(
                    CodeSymbol(
                        id=cls_id,
                        repo_id=repo_id,
                        file_path=file_path,
                        language="python",
                        name=node.name,
                        symbol_type=SymbolType.CLASS,
                        start_line=cls_start,
                        end_line=cls_end,
                        docstring=cls_doc,
                        parent_id=None,
                        signature=f"class {node.name}",
                    )
                )
                relationships.append(
                    Relationship(
                        source_id=file_node_id,
                        target_id=cls_id,
                        relationship_type=RelationshipType.CONTAINS,
                        provenance="python_ast",
                        confidence=1.0,
                        is_inferred=False
                    )
                )

                # Class methods
                for class_child in node.body:
                    if isinstance(class_child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_start = class_child.lineno
                        m_end = getattr(class_child, "end_lineno", m_start)
                        m_doc = ast.get_docstring(class_child)
                        m_id = f"{repo_id}:{file_path}:{node.name}.{class_child.name}:{m_start}"
                        
                        symbols.append(
                            CodeSymbol(
                                id=m_id,
                                repo_id=repo_id,
                                file_path=file_path,
                                language="python",
                                name=f"{node.name}.{class_child.name}",
                                symbol_type=SymbolType.METHOD,
                                start_line=m_start,
                                end_line=m_end,
                                docstring=m_doc,
                                parent_id=cls_id,
                                signature=f"def {class_child.name}(self, ...)",
                            )
                        )
                        relationships.append(
                            Relationship(
                                source_id=cls_id,
                                target_id=m_id,
                                relationship_type=RelationshipType.CONTAINS,
                                provenance="python_ast",
                                confidence=1.0,
                                is_inferred=False
                            )
                        )
                        extract_calls_in_node(class_child, f"{node.name}.{class_child.name}", m_id)

        return ParseResult(
            file_path=file_path,
            language="python",
            is_parsed=True,
            symbols=symbols,
            imports=imports,
            calls=calls,
            relationships=relationships,
            errors=errors
        )

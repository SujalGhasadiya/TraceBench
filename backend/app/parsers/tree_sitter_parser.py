from typing import List, Dict, Any, Optional, Set
import tree_sitter_languages
from .base import BaseParser, ParseResult
from ..models.schemas import CodeSymbol, SymbolType, Relationship, RelationshipType

class TreeSitterParser(BaseParser):
    """
    Unified multi-language parser leveraging Tree-sitter.
    Supports JavaScript, TypeScript, Java, C, C++, Go, Rust, PHP, and Python.
    """
    
    LANG_GRAMMAR_MAP = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "go": "go",
        "rust": "rust",
        "php": "php",
    }
    
    def __init__(self):
        self._parsers = {}

    def get_parser(self, lang_name: str):
        grammar_name = self.LANG_GRAMMAR_MAP.get(lang_name)
        if not grammar_name:
            return None
        if grammar_name not in self._parsers:
            try:
                self._parsers[grammar_name] = tree_sitter_languages.get_parser(grammar_name)
            except Exception as e:
                print(f"Warning: Failed to load grammar for {grammar_name}: {e}")
                return None
        return self._parsers[grammar_name]

    def parse(self, file_path: str, source_code: str, repo_id: str, language: Optional[str] = None) -> ParseResult:
        if not language:
            return ParseResult(
                file_path=file_path,
                language="unknown",
                is_parsed=False,
                errors=["No language specified for TreeSitterParser"]
            )
            
        parser = self.get_parser(language)
        if not parser:
            return ParseResult(
                file_path=file_path,
                language=language,
                is_parsed=False,
                errors=[f"Grammar parser unavailable for language: {language}"]
            )
            
        source_bytes = source_code.encode("utf-8")
        try:
            tree = parser.parse(source_bytes)
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language=language,
                is_parsed=False,
                errors=[f"Tree-sitter parse error: {str(e)}"]
            )
            
        root = tree.root_node
        symbols: List[CodeSymbol] = []
        imports: List[str] = []
        calls: List[Dict[str, Any]] = []
        relationships: List[Relationship] = []
        file_node_id = f"{repo_id}:{file_path}"

        def get_node_text(node) -> str:
            return node.text.decode("utf-8", errors="replace")

        def find_child_by_type(node, target_type: str):
            for child in node.children:
                if child.type == target_type:
                    return child
            return None

        def find_first_descendant_by_types(node, target_types: Set[str]):
            for child in node.children:
                if child.type in target_types:
                    return child
                found = find_first_descendant_by_types(child, target_types)
                if found:
                    return found
            return None

        # Recursive AST walk extracting declarations and references
        def walk(node, parent_sym_id: Optional[str] = None, scope_name: Optional[str] = None):
            node_type = node.type
            current_sym_id = parent_sym_id
            current_scope = scope_name

            # ----------------------------------------------------
            # 1. IMPORTS & INCLUDES
            # ----------------------------------------------------
            if node_type in {
                "import_statement", "import_declaration", "preproc_include",
                "use_declaration", "namespace_use_declaration"
            }:
                import_text = get_node_text(node).strip()
                imports.append(import_text)
                relationships.append(
                    Relationship(
                        source_id=file_node_id,
                        target_id=import_text,
                        relationship_type=RelationshipType.IMPORTS,
                        provenance="tree_sitter",
                        confidence=1.0,
                        is_inferred=False,
                        source_location={"file": file_path, "line": node.start_point[0] + 1}
                    )
                )

            # ----------------------------------------------------
            # 2. FUNCTIONS & METHODS
            # ----------------------------------------------------
            elif node_type in {
                "function_declaration", "function_definition", "function_item",
                "method_declaration", "method_definition", "constructor_declaration"
            }:
                name_node = (
                    find_child_by_type(node, "name") or
                    find_child_by_type(node, "identifier") or
                    find_child_by_type(node, "field_identifier")
                )
                
                # C/C++ declarator fallback
                if not name_node and node_type == "function_definition":
                    decl = find_child_by_type(node, "function_declarator") or find_child_by_type(node, "declarator")
                    if decl:
                        name_node = (
                            find_child_by_type(decl, "field_identifier") or
                            find_child_by_type(decl, "identifier") or
                            find_first_descendant_by_types(decl, {"field_identifier", "identifier"})
                        )
                    if not name_node:
                        name_node = find_first_descendant_by_types(node, {"field_identifier", "identifier"})

                # Go method receiver extraction
                if node_type == "method_declaration":
                    rec_list = find_child_by_type(node, "parameter_list")
                    if rec_list:
                        rec_type_node = find_first_descendant_by_types(rec_list, {"type_identifier"})
                        if rec_type_node:
                            scope_name = get_node_text(rec_type_node)
                        
                sym_name = get_node_text(name_node) if name_node else f"anonymous_{node.start_point[0] + 1}"
                is_method = (
                    node_type in {"method_declaration", "method_definition", "constructor_declaration"} or
                    (parent_sym_id is not None) or
                    (scope_name is not None)
                )
                
                # Full scoped name if inside class or receiver
                full_name = f"{scope_name}.{sym_name}" if (scope_name and is_method) else sym_name
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                sym_id = f"{repo_id}:{file_path}:{full_name}:{start_line}"
                
                symbol = CodeSymbol(
                    id=sym_id,
                    repo_id=repo_id,
                    file_path=file_path,
                    language=language,
                    name=full_name,
                    symbol_type=SymbolType.METHOD if is_method else SymbolType.FUNCTION,
                    start_line=start_line,
                    end_line=end_line,
                    parent_id=parent_sym_id,
                    signature=f"{sym_name}(...)"
                )
                symbols.append(symbol)
                
                # Link hierarchy
                parent_source = parent_sym_id or file_node_id
                relationships.append(
                    Relationship(
                        source_id=parent_source,
                        target_id=sym_id,
                        relationship_type=RelationshipType.CONTAINS,
                        provenance="tree_sitter",
                        confidence=1.0,
                        is_inferred=False
                    )
                )
                current_sym_id = sym_id
                current_scope = full_name

            # ----------------------------------------------------
            # 3. CLASSES, STRUCTS & INTERFACES
            # ----------------------------------------------------
            elif node_type in {
                "class_declaration", "class_specifier", "struct_specifier",
                "struct_item", "interface_declaration", "type_declaration",
                "trait_item", "impl_item"
            }:
                name_node = (
                    find_child_by_type(node, "name") or
                    find_child_by_type(node, "identifier") or
                    find_child_by_type(node, "type_identifier")
                )
                # Go type_spec fallback
                if not name_node and node_type == "type_declaration":
                    type_spec = find_child_by_type(node, "type_spec")
                    if type_spec:
                        name_node = find_child_by_type(type_spec, "type_identifier") or find_child_by_type(type_spec, "identifier")
                        
                sym_name = get_node_text(name_node) if name_node else f"type_{node.start_point[0] + 1}"
                
                if "interface" in node_type or "trait" in node_type:
                    stype = SymbolType.INTERFACE
                elif "struct" in node_type:
                    stype = SymbolType.STRUCT
                else:
                    stype = SymbolType.CLASS

                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                sym_id = f"{repo_id}:{file_path}:{sym_name}:{start_line}"

                symbols.append(
                    CodeSymbol(
                        id=sym_id,
                        repo_id=repo_id,
                        file_path=file_path,
                        language=language,
                        name=sym_name,
                        symbol_type=stype,
                        start_line=start_line,
                        end_line=end_line,
                        parent_id=parent_sym_id,
                        signature=f"{node_type.split('_')[0]} {sym_name}"
                    )
                )
                parent_source = parent_sym_id or file_node_id
                relationships.append(
                    Relationship(
                        source_id=parent_source,
                        target_id=sym_id,
                        relationship_type=RelationshipType.CONTAINS,
                        provenance="tree_sitter",
                        confidence=1.0,
                        is_inferred=False
                    )
                )
                current_sym_id = sym_id
                current_scope = sym_name

            # ----------------------------------------------------
            # 4. CALL EXPRESSIONS
            # ----------------------------------------------------
            elif node_type in {
                "call_expression", "method_invocation", "function_call_expression",
                "member_call_expression", "scoped_call_expression", "call"
            }:
                callee_node = find_first_descendant_by_types(
                    node, {"identifier", "property_identifier", "field_identifier", "name"}
                )
                if callee_node:
                    callee_name = get_node_text(callee_node)
                    line_no = node.start_point[0] + 1
                    calls.append({
                        "caller_name": current_scope or "global",
                        "caller_id": current_sym_id or file_node_id,
                        "callee_name": callee_name,
                        "line": line_no
                    })
                    if current_sym_id:
                        relationships.append(
                            Relationship(
                                source_id=current_sym_id,
                                target_id=callee_name,
                                relationship_type=RelationshipType.CALLS,
                                provenance="tree_sitter",
                                confidence=0.8,
                                is_inferred=True,
                                source_location={"file": file_path, "line": line_no}
                            )
                        )

            # Traverse children
            for child in node.children:
                walk(child, current_sym_id, current_scope)

        walk(root)

        return ParseResult(
            file_path=file_path,
            language=language,
            is_parsed=True,
            symbols=symbols,
            imports=imports,
            calls=calls,
            relationships=relationships,
            errors=[]
        )

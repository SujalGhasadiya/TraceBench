from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

@dataclass
class SearchableUnit:
    """A granular searchable document unit in the repository."""
    document_id: str
    file_path: str
    language: str
    line_range: Tuple[int, int]
    content: str
    snippet: str
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    node_id: Optional[str] = None

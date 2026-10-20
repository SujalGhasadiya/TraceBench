from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from ..models.schemas import CodeSymbol, Relationship

class ParseResult(BaseModel):
    file_path: str
    language: str
    is_parsed: bool
    symbols: List[CodeSymbol] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    calls: List[Dict[str, Any]] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

class BaseParser:
    def parse(self, file_path: str, source_code: str, repo_id: str) -> ParseResult:
        raise NotImplementedError

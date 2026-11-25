"""Shared data models for CodeAtlas."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Repository:
    name: str
    path: Path
    source: str


@dataclass
class CodeSymbol:
    name: str
    kind: str
    file_path: str
    start_line: int
    end_line: int
    source: str
    docstring: str = ""


@dataclass
class ParsedFile:
    file_path: str
    source: str
    symbols: list[CodeSymbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


@dataclass
class CodeChunk:
    chunk_id: str
    repository: str
    file_path: str
    content: str
    start_line: int
    end_line: int
    symbol_name: str
    symbol_type: str

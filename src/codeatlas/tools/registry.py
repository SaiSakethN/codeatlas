"""Structured tool definitions and execution."""

from pydantic import BaseModel, ConfigDict, Field

from codeatlas.tools.repository_tools import RepositoryTools


class ToolInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListFilesInput(ToolInput):
    prefix: str = Field(default="", max_length=500)


class ReadFileInput(ToolInput):
    file_path: str = Field(max_length=500)
    start_line: int = Field(default=1, ge=1)
    end_line: int = Field(default=100, ge=1)


class SearchInput(ToolInput):
    query: str = Field(min_length=1, max_length=500)


class SymbolInput(ToolInput):
    symbol_name: str = Field(min_length=1, max_length=200)


class SemanticSearchInput(SearchInput):
    top_k: int = Field(default=5, ge=1, le=8)


class FileInput(ToolInput):
    file_path: str = Field(max_length=500)


class TestsInput(ToolInput):
    query: str = Field(default="", max_length=500)


class EmptyInput(ToolInput):
    pass


class ToolRegistry:
    def __init__(self, tools: RepositoryTools):
        self.entries = {
            "list_files": (
                tools.list_files,
                ListFilesInput,
                "List Python source files by optional path prefix.",
            ),
            "read_file": (
                tools.read_file,
                ReadFileInput,
                "Read a specific range of source code lines.",
            ),
            "search_code": (
                tools.search_code,
                SearchInput,
                "Find exact text within repository source code.",
            ),
            "find_symbol": (
                tools.find_symbol,
                SymbolInput,
                "Locate a Python function or class by name.",
            ),
            "semantic_search": (
                tools.semantic_search,
                SemanticSearchInput,
                "Find conceptually relevant source code.",
            ),
            "get_repository_overview": (
                tools.get_repository_overview,
                EmptyInput,
                "Get repository metadata and structure.",
            ),
            "get_dependencies": (
                tools.get_dependencies,
                FileInput,
                "Inspect imports used by a Python file.",
            ),
            "find_references": (
                tools.find_references,
                SymbolInput,
                "Find textual references to a code symbol.",
            ),
            "inspect_tests": (
                tools.inspect_tests,
                TestsInput,
                "Find test files relevant to a search term.",
            ),
        }

    def schemas(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": schema.model_json_schema(),
                },
            }
            for name, (_, schema, description) in self.entries.items()
        ]

    def execute(self, name: str, arguments: dict):
        if name not in self.entries:
            raise ValueError(f"Unknown tool: {name}")

        function, schema, _ = self.entries[name]

        validated = schema.model_validate(arguments)

        return function(**validated.model_dump())

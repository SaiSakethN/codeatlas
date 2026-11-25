"""Read-only repository investigation tools."""

import tokenize
from pathlib import Path

from codeatlas.ingestion.explorer import discover_python_files
from codeatlas.models import Repository
from codeatlas.parsing.parser import parse_python_file


class RepositoryTools:
    def __init__(self, repository: Repository, retriever=None):
        self.repository = repository
        self.root = repository.path.resolve()
        self.retriever = retriever

        self.files = discover_python_files(self.root)

        self.file_map = {path.relative_to(self.root).as_posix(): path for path in self.files}

    def _safe_path(self, file_path: str) -> Path:
        if file_path not in self.file_map:
            raise ValueError("File is not in the repository index.")

        path = self.file_map[file_path].resolve()

        if not path.is_relative_to(self.root):
            raise ValueError("Access outside repository denied.")

        if not path.is_file():
            raise ValueError("File does not exist.")

        return path

    def list_files(self, prefix: str = "") -> dict:
        matches = [path for path in sorted(self.file_map) if path.startswith(prefix)]

        return {
            "total": len(matches),
            "files": matches[:100],
            "truncated": len(matches) > 100,
        }

    def read_file(
        self,
        file_path: str,
        start_line: int = 1,
        end_line: int = 100,
    ) -> dict:
        path = self._safe_path(file_path)

        if start_line < 1 or end_line < start_line:
            raise ValueError("Invalid line range.")

        end_line = min(end_line, start_line + 119)

        with tokenize.open(path) as file:
            lines = file.read().splitlines()

        selected = lines[start_line - 1 : end_line]

        if not selected:
            raise ValueError("Requested lines do not exist.")

        return {
            "file_path": file_path,
            "start_line": start_line,
            "end_line": start_line + len(selected) - 1,
            "content": "\n".join(selected),
        }

    def search_code(self, query: str) -> list[dict]:
        if not query.strip():
            raise ValueError("Search query cannot be empty.")

        results = []
        needle = query.casefold()

        for file_path in self.file_map:
            try:
                path = self._safe_path(file_path)

                with tokenize.open(path) as file:
                    lines = file.read().splitlines()

                for index, line in enumerate(lines):
                    if needle in line.casefold():
                        start = max(0, index - 3)
                        end = min(len(lines), index + 4)

                        results.append(
                            {
                                "file_path": file_path,
                                "start_line": start + 1,
                                "end_line": end,
                                "content": "\n".join(lines[start:end]),
                            }
                        )

                        if len(results) >= 20:
                            return results

            except (OSError, UnicodeError, SyntaxError, ValueError):
                continue

        return results

    def find_symbol(self, symbol_name: str) -> list[dict]:
        if not symbol_name.strip():
            raise ValueError("Symbol name cannot be empty.")

        results = []

        for file_path in self.file_map:
            try:
                path = self._safe_path(file_path)

                parsed = parse_python_file(
                    path,
                    self.root,
                )

                for symbol in parsed.symbols:
                    if symbol.name.casefold() == symbol_name.casefold():
                        results.append(
                            {
                                "name": symbol.name,
                                "kind": symbol.kind,
                                "file_path": file_path,
                                "start_line": symbol.start_line,
                                "end_line": symbol.end_line,
                                "docstring": symbol.docstring[:1000],
                            }
                        )

                        if len(results) >= 20:
                            return results

            except (
                SyntaxError,
                UnicodeError,
                OSError,
                ValueError,
            ):
                continue

        return results

    def semantic_search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        if self.retriever is None:
            raise RuntimeError("Repository is not indexed.")

        return self.retriever.search(
            query,
            top_k=max(1, min(top_k, 8)),
        )

    def get_repository_overview(self) -> dict:
        return {
            "name": self.repository.name,
            "source": self.repository.source,
            "python_files": len(self.files),
            "sample_files": sorted(self.file_map)[:30],
        }

    def get_dependencies(self, file_path: str) -> dict:
        path = self._safe_path(file_path)

        parsed = parse_python_file(
            path,
            self.root,
        )

        return {
            "file_path": file_path,
            "imports": parsed.imports[:100],
        }

    def find_references(self, symbol_name: str) -> list[dict]:
        return self.search_code(symbol_name)

    def inspect_tests(self, query: str = "") -> list[dict]:
        results = []

        for file_path in self.file_map:
            path = Path(file_path)

            is_test = (
                path.name.startswith("test_")
                or path.name.endswith("_test.py")
                or "tests" in path.parts
            )

            if not is_test:
                continue

            if query:
                try:
                    safe_path = self._safe_path(file_path)

                    with tokenize.open(safe_path) as file:
                        content = file.read()

                    if query.casefold() not in content.casefold():
                        continue

                except (OSError, UnicodeError, SyntaxError, ValueError):
                    continue

            results.append({"file_path": file_path})

            if len(results) >= 30:
                break

        return results

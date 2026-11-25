"""Python source code analysis using AST."""

import ast
import tokenize
from pathlib import Path

from codeatlas.models import CodeSymbol, ParsedFile


def parse_python_file(path: Path, root: Path) -> ParsedFile:
    """Extract symbols and imports from a Python source file."""

    with tokenize.open(path) as file:
        source = file.read()

    relative_path = path.relative_to(root).as_posix()

    tree = ast.parse(source)
    lines = source.splitlines()

    symbols = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom):
            module = "." * node.level + (node.module or "")
            imports.append(module)

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"

            start = min([node.lineno] + [decorator.lineno for decorator in node.decorator_list])

            end = node.end_lineno or node.lineno

            symbols.append(
                CodeSymbol(
                    name=node.name,
                    kind=kind,
                    file_path=relative_path,
                    start_line=start,
                    end_line=end,
                    source="\n".join(lines[start - 1 : end]),
                    docstring=ast.get_docstring(node) or "",
                )
            )

    return ParsedFile(
        file_path=relative_path,
        source=source,
        symbols=sorted(symbols, key=lambda item: item.start_line),
        imports=sorted(set(imports)),
    )

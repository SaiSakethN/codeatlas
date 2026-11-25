"""Static Python module analysis; imported code is never executed."""

import ast
import subprocess
from collections import Counter, deque

from codeatlas.parsing.parser import parse_python_file
from codeatlas.tools.repository_tools import RepositoryTools


def analyze(tools: RepositoryTools) -> dict:
    files = sorted(tools.file_map)
    modules = {}
    for path in files:
        name = path.removesuffix(".py").replace("/", ".")
        if name.endswith(".__init__"):
            name = name.removesuffix(".__init__")
        modules[name] = path
        if name.startswith("src."):
            modules[name[4:]] = path
    nodes, edges, failures = [], set(), []
    external = Counter()
    symbol_count = 0
    for path in files:
        try:
            parsed = parse_python_file(tools._safe_path(path), tools.root)
            symbol_count += len(parsed.symbols)
            nodes.append(
                {
                    "id": path,
                    "label": path.rsplit("/", 1)[-1],
                    "symbols": len(parsed.symbols),
                    "lines": len(parsed.source.splitlines()),
                }
            )
            package = path.removesuffix(".py").replace("/", ".").split(".")[:-1]
            for item in ast.walk(ast.parse(parsed.source)):
                candidates = []
                if isinstance(item, ast.Import):
                    candidates = [alias.name for alias in item.names]
                elif isinstance(item, ast.ImportFrom):
                    base = item.module or ""
                    if item.level:
                        base = ".".join(package[: len(package) - item.level + 1] + [base])
                        base = base.strip(".")
                    candidates = [f"{base}.{alias.name}".strip(".") for alias in item.names]
                    candidates.append(base)
                for candidate in candidates:
                    target = modules.get(candidate)
                    if target and target != path:
                        edges.add((path, target))
                    elif candidate and candidate.split(".")[0] not in modules:
                        external[candidate.split(".")[0]] += 1
        except (SyntaxError, UnicodeError, OSError, ValueError):
            failures.append(path)
    tests = [p for p in files if p.rsplit("/", 1)[-1].startswith("test_") or "tests/" in p]
    entrypoints = [p for p in files if p.endswith(("__main__.py", "/app.py", "/main.py"))]
    return {
        "name": tools.repository.name,
        "python_files": len(files),
        "symbols": symbol_count,
        "lines": sum(n["lines"] for n in nodes),
        "test_files": len(tests),
        "nodes": nodes,
        "edges": [{"source": a, "target": b} for a, b in sorted(edges)],
        "external_imports": dict(external.most_common(30)),
        "failed_files": failures,
        "onboarding": {
            "summary": f"Explore {len(files)} Python files and {symbol_count} extracted symbols.",
            "entrypoints": entrypoints,
            "tests": tests[:30],
            "suggested_questions": [
                "What are the main entry points and how do they connect?",
                "How does this repository handle errors?",
                "Which tests describe the core behavior?",
            ],
            "method": "Static file and AST heuristics; no generated architectural claims.",
        },
        "limitations": "Python imports only; dynamic imports and runtime calls are not resolved.",
    }


def change_impact(tools: RepositoryTools, analysis: dict) -> dict:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(tools.root),
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--name-only",
                "HEAD~1",
                "HEAD",
                "--",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError):
        return {
            "available": False,
            "reason": "Requires at least two local commits; public imports use shallow clones.",
        }
    changed = sorted(set(result.stdout.splitlines()) & set(tools.file_map))
    reverse = {}
    for edge in analysis["edges"]:
        reverse.setdefault(edge["target"], set()).add(edge["source"])
    seen, queue = set(changed), deque(changed)
    while queue:
        for dependency in reverse.get(queue.popleft(), set()):
            if dependency not in seen:
                seen.add(dependency)
                queue.append(dependency)
    return {
        "available": True,
        "comparison": "HEAD~1..HEAD",
        "changed": changed,
        "potentially_affected": sorted(seen - set(changed)),
        "method": "Transitive reverse static import edges; not runtime impact proof.",
    }

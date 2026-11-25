import pytest
from pydantic import ValidationError

from codeatlas.ingestion.repository import load_local_repository
from codeatlas.retrieval.hybrid import reciprocal_rank_fusion
from codeatlas.retrieval.keyword import KeywordRetriever, tokenize
from codeatlas.tools.registry import ToolRegistry
from codeatlas.tools.repository_tools import RepositoryTools


@pytest.fixture
def tools(tmp_path):
    (tmp_path / "auth.py").write_text(
        "import hashlib\n\ndef authenticate_user(token):\n    return bool(token)\n",
        encoding="utf-8",
    )

    (tmp_path / "test_auth.py").write_text(
        "def test_authenticate_user():\n    assert True\n",
        encoding="utf-8",
    )

    repository = load_local_repository(str(tmp_path))

    return RepositoryTools(repository)


def test_tokenizer():
    assert tokenize("HTTPAdapter") == ["http", "adapter"]

    assert tokenize("authenticate_user") == [
        "authenticate",
        "user",
    ]


def test_keyword_retrieval():
    retriever = KeywordRetriever(
        [
            {
                "chunk_id": "a",
                "file_path": "auth.py",
                "symbol_name": "authenticate",
                "content": "def authenticate(token): pass",
            },
            {
                "chunk_id": "b",
                "file_path": "database.py",
                "symbol_name": "connect",
                "content": "def connect(): pass",
            },
        ]
    )

    results = retriever.search("authenticate")

    assert results[0]["chunk_id"] == "a"


def test_rank_fusion():
    a = {"chunk_id": "a"}
    b = {"chunk_id": "b"}

    results = reciprocal_rank_fusion([[a, b], [b]])

    assert results[0]["chunk_id"] == "b"


def test_list_files(tools):
    assert tools.list_files()["total"] == 2


def test_read_file(tools):
    result = tools.read_file("auth.py", 3, 4)

    assert "authenticate_user" in result["content"]
    assert result["start_line"] == 3


def test_find_symbol(tools):
    results = tools.find_symbol("authenticate_user")

    assert len(results) == 1
    assert results[0]["file_path"] == "auth.py"


def test_search_code(tools):
    results = tools.search_code("authenticate_user")

    assert len(results) == 2


def test_dependencies(tools):
    result = tools.get_dependencies("auth.py")

    assert "hashlib" in result["imports"]


def test_inspect_tests(tools):
    results = tools.inspect_tests("authenticate_user")

    assert results[0]["file_path"] == "test_auth.py"


def test_path_traversal(tools):
    with pytest.raises(ValueError):
        tools.read_file("../../secret.py")


def test_unknown_tool(tools):
    registry = ToolRegistry(tools)

    with pytest.raises(ValueError):
        registry.execute("execute_shell", {})


def test_invalid_arguments(tools):
    registry = ToolRegistry(tools)

    with pytest.raises(ValidationError):
        registry.execute(
            "read_file",
            {
                "file_path": "auth.py",
                "start_line": -1,
            },
        )


def test_tool_execution(tools):
    registry = ToolRegistry(tools)

    results = registry.execute(
        "find_symbol",
        {"symbol_name": "authenticate_user"},
    )

    assert len(results) == 1


def test_tool_schemas(tools):
    registry = ToolRegistry(tools)

    assert len(registry.schemas()) == 9

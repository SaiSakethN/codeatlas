from codeatlas.parsing.chunker import create_chunks
from codeatlas.parsing.parser import parse_python_file


def test_extract_symbols(tmp_path):
    path = tmp_path / "example.py"

    path.write_text(
        "import os\n\nclass Calculator:\n    def add(self, a, b):\n        return a + b\n",
        encoding="utf-8",
    )

    parsed = parse_python_file(path, tmp_path)

    assert parsed.imports == ["os"]

    names = {symbol.name for symbol in parsed.symbols}

    assert "Calculator" in names
    assert "add" in names


def test_create_chunks(tmp_path):
    path = tmp_path / "example.py"

    path.write_text(
        "def greet():\n    return 'hello'\n",
        encoding="utf-8",
    )

    parsed = parse_python_file(path, tmp_path)
    chunks = create_chunks(parsed, "example")

    assert len(chunks) >= 1

    function_chunk = next(chunk for chunk in chunks if chunk.symbol_name == "greet")

    assert function_chunk.start_line == 1
    assert function_chunk.end_line == 2
    assert function_chunk.file_path == "example.py"
    assert function_chunk.repository == "example"


def test_module_without_functions(tmp_path):
    path = tmp_path / "settings.py"
    path.write_text("DEBUG = True\n", encoding="utf-8")

    parsed = parse_python_file(path, tmp_path)
    chunks = create_chunks(parsed, "example")

    assert len(chunks) == 1
    assert chunks[0].symbol_type == "module"

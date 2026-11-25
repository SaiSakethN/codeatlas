from codeatlas.analysis.repository import analyze, change_impact
from codeatlas.models import Repository
from codeatlas.tools.repository_tools import RepositoryTools


def test_static_relative_imports_and_invalid_source(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text("")
    (package / "core.py").write_text("def hello():\n    return 1\n")
    (package / "app.py").write_text("from .core import hello\n")
    (package / "broken.py").write_text("def !invalid")
    tools = RepositoryTools(Repository("fixture", tmp_path, "local"))
    result = analyze(tools)
    assert {"source": "package/app.py", "target": "package/core.py"} in result["edges"]
    assert result["symbols"] == 1
    assert result["failed_files"] == ["package/broken.py"]
    assert result["onboarding"]["entrypoints"] == ["package/app.py"]
    assert change_impact(tools, result)["available"] is False

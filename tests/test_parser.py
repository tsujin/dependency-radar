import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radar.parser import parse_dependencies


def test_parse_requirements_txt(tmp_path):
    req_file = tmp_path / "requirements.txt"
    req_file.write_text("""
    requests>=2.0.0
    numpy==1.21.0
    # This is a comment
    pandas
    requests>=2.0.0
    flask>=2.0,<3.0
    """)

    deps = parse_dependencies(str(tmp_path))
    expected = [
        {"name": "requests", "version": ">=2.0.0"},
        {"name": "numpy", "version": "==1.21.0"},
        {"name": "pandas", "version": "Any"},
        {"name": "flask", "version": "<3.0,>=2.0"},
    ]
    assert deps == expected


def test_parse_pyproject_toml(tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text("""
    [tool.poetry.dependencies]
    python = "^3.8"
    requests = ">=2.0.0"
    numpy = "==1.21.0"

    [tool.poetry.dev-dependencies]
    pytest = "^6.2"
    black = ">=21.9b0"
    requests = ">=2.0.0"
    """)

    deps = parse_dependencies(str(tmp_path))
    expected = [
        {"name": "python", "version": "^3.8"},
        {"name": "requests", "version": ">=2.0.0"},
        {"name": "numpy", "version": "==1.21.0"},
        {"name": "pytest", "version": "^6.2"},
        {"name": "black", "version": ">=21.9b0"},
    ]
    assert deps == expected
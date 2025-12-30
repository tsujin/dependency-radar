from pathlib import Path
from typing import List, Dict
from packaging.requirements import Requirement

try:
    import tomllib  # Python 3.11 and later
except ImportError:
    import tomli as tomllib  # Python 3.10 and earlier

Dependency = Dict[str, str]

def parse_dependencies(file_path: str = ".") -> List[Dependency]:
    """
    Detect and parse dependency files from a repo root.
    """
    root = Path(file_path)

    if (root / "pyproject.toml").exists():
        return parse_pyproject_toml(root / "pyproject.toml")
    
    if (root / "requirements.txt").exists():
        return parse_requirements_txt(root / "requirements.txt")
    
    return []

def parse_pyproject_toml(file_path: Path) -> List[Dependency]:
    """
    Parse dependencies from a pyproject.toml file.
    """
    with open(file_path, "rb") as f:
        data = tomllib.load(f)

    dependencies = []
    for section in ["dependencies", "dev-dependencies"]:
        deps = data.get("tool", {}).get("poetry", {}).get(section, [])
        for dep in deps:
            requirement = Requirement(dep)
            dependencies.append({
                "name": requirement.name,
                "version": str(requirement.specifier) if requirement.specifier else "Any"
            })

    return deduplicate_dependencies(dependencies)

def parse_requirements_txt(file_path: Path) -> List[Dependency]:
    """
    Parse dependencies from a requirements.txt file.
    """
    dependencies = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirement = Requirement(line)
                dependencies.append({
                    "name": requirement.name,
                    "version": str(requirement.specifier) if requirement.specifier else "Any"
                })
    
    return deduplicate_dependencies(dependencies)

def deduplicate_dependencies(dependencies: List[Dependency]) -> List[Dependency]:
    """
    Deduplicate dependencies by name, keeping the first occurrence.
    """
    seen = set()
    unique_deps = []
    for dep in dependencies:
        if dep["name"] not in seen:
            seen.add(dep["name"])
            unique_deps.append(dep)
    return unique_deps

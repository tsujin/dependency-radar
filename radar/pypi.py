from typing import Tuple, List, Dict
import json
import urllib.request
from urllib.error import HTTPError, URLError

from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet

Dependency = Dict[str, str]


def normalize_poetry_specifier(version: str) -> str:
    """Convert common Poetry version operators (^, ~) to a PEP 440 specifier string.

    Returns an empty string for a wildcard or unbounded spec (meaning "Any").
    """
    if not version:
        return ""
    version = version.strip()
    if version == "*":
        return ""

    # caret operator
    if version.startswith("^"):
        base = version[1:].strip()
        try:
            v = Version(base)
        except InvalidVersion:
            return version

        if v.major > 0:
            upper = f">{v.major + 1}.0.0"
            return f">={v.public},<{v.major + 1}.0.0"
        if v.major == 0 and v.minor > 0:
            return f">={v.public},<0.{v.minor + 1}.0"
        # 0.0.x -> allow patch bumps only
        return f">={v.public},<0.0.{v.micro + 1}"

    # tilde operator (~) roughly means: compatible with minor
    if version.startswith("~"):
        base = version[1:].strip()
        try:
            v = Version(base)
        except InvalidVersion:
            return version
        return f">={v.public},<{v.major}.{v.minor + 1}.0"

    # otherwise return as-is (could be PEP 440 already)
    return version


def get_latest_version(package_name: str, timeout: int = 5) -> str:
    """Fetch the latest released version for `package_name` from PyPI.

    Raises `ValueError` if the package is not found or network errors occur.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.load(resp)
            version = data.get("info", {}).get("version")
            if not version:
                raise ValueError(f"No version info for package {package_name}")
            return version
    except HTTPError as e:
        if e.code == 404:
            raise ValueError(f"Package not found on PyPI: {package_name}") from e
        raise
    except URLError as e:
        raise ValueError(f"Network error when contacting PyPI: {e}") from e


def is_outdated(name: str, version_spec: str) -> Tuple[bool, str]:
    """Return (outdated, latest_version).

    - `version_spec` is a version string as produced by the parser (could be
      a PEP 440 specifier like `>=1.2.0`, a requirements wildcard like
      `==4.2.*`, or Poetry operators like `^1.2.3`/`~1.2`).
    - If `version_spec` is empty or represents Any, the function returns
      (False, latest_version).
    """
    latest = get_latest_version(name)

    if not version_spec or version_spec == "Any":
        return False, latest

    normalized = normalize_poetry_specifier(version_spec)

    try:
        spec = SpecifierSet(normalized)
    except Exception:
        # If we can't parse the specifier, conservatively treat as not outdated
        return False, latest

    try:
        latest_v = Version(latest)
    except InvalidVersion:
        return False, latest

    in_range = latest_v in spec
    return (not in_range), latest


def check_dependencies(dependencies: List[Dependency]) -> List[Dict[str, str]]:
    """Check a list of dependencies and report which are outdated.

    Input: list of {"name": ..., "version": ...}
    Output: list of {"name": ..., "current": ..., "latest": ..., "outdated": "true|false"}
    """
    results = []
    for dep in dependencies:
        name = dep.get("name")
        spec = dep.get("version")
        try:
            outdated, latest = is_outdated(name, spec)
        except ValueError:
            # package not found or network error; mark as unknown
            results.append({"name": name, "current": spec, "latest": "unknown", "outdated": "unknown"})
            continue
        results.append({"name": name, "current": spec, "latest": latest, "outdated": str(outdated).lower()})
    return results

import io
import json
from unittest.mock import patch

from radar import pypi


def test_normalize_poetry_specifier():
    assert pypi.normalize_poetry_specifier("*") == ""
    assert pypi.normalize_poetry_specifier("^1.2.3") == ">=1.2.3,<2.0.0"
    assert pypi.normalize_poetry_specifier("^0.5.2") == ">=0.5.2,<0.6.0"
    assert pypi.normalize_poetry_specifier("~1.2.3") == ">=1.2.3,<1.3.0"
    assert pypi.normalize_poetry_specifier("==4.2.*") == "==4.2.*"


def test_get_latest_version(monkeypatch):
    data = {"info": {"version": "1.2.3"}}
    payload = json.dumps(data).encode()

    class DummyResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    def fake_urlopen(url, timeout=...):
        return DummyResp(payload)

    monkeypatch.setattr(pypi.urllib.request, "urlopen", fake_urlopen)
    assert pypi.get_latest_version("somepkg") == "1.2.3"


@patch("radar.pypi.get_latest_version")
def test_is_outdated_and_wildcards(mock_get_latest):
    # exact match -> not outdated
    mock_get_latest.return_value = "1.2.3"
    assert pypi.is_outdated("pkg", "==1.2.3") == (False, "1.2.3")

    # wildcard minor in requirements -> not outdated when latest matches
    mock_get_latest.return_value = "4.2.5"
    assert pypi.is_outdated("django", "==4.2.*") == (False, "4.2.5")

    # caret specifier -> outdated if latest outside range
    mock_get_latest.return_value = "2.0.0"
    outdated, latest = pypi.is_outdated("example", "^1.2.0")
    assert outdated is True
    assert latest == "2.0.0"


def test_check_dependencies_handles_missing_package(monkeypatch):
    deps = [{"name": "nope", "version": "==0.0.1"}]

    def fake_get_latest(name, timeout=...):
        raise ValueError("not found")

    monkeypatch.setattr(pypi, "get_latest_version", fake_get_latest)
    results = pypi.check_dependencies(deps)
    assert results == [{"name": "nope", "current": "==0.0.1", "latest": "unknown", "outdated": "unknown"}]

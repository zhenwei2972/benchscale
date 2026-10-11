import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Each test gets its own measured references and designs folder."""
    monkeypatch.setenv("BENCHSCALE_HOME", str(tmp_path / "home"))
    from benchscale import tools
    tools._lib = None
    yield tmp_path / "home"
    tools._lib = None

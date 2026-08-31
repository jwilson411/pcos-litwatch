"""The PEP 561 `py.typed` marker ships with the importable package."""

import tomllib
from importlib.resources import as_file, files
from pathlib import Path


def test_py_typed_is_importable_package_data():
    marker = files("pcos_litwatch").joinpath("py.typed")

    assert marker.is_file()
    with as_file(marker) as path:
        assert path.stat().st_size == 0


def test_pyproject_declares_py_typed_package_data():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    config = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    package_data = config["tool"]["setuptools"]["package-data"]
    assert package_data["pcos_litwatch"] == ["py.typed"]

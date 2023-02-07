import os

import pytest

import pushsource


DOC_PATH = os.path.join(os.path.dirname(__file__), "../../docs")


def all_rst_files():
    for dirpath, _, filenames in os.walk(DOC_PATH):
        for name in filenames:
            if name.endswith(".rst"):
                yield os.path.join(dirpath, name)


@pytest.fixture(scope="session")
def all_rst_content():
    out = []
    for filename in all_rst_files():
        with open(filename, "rt") as f:
            content = f.read()
        out.append(content)
    yield out


def public_class_names():
    all_attrs = dir(pushsource)
    return [elem for elem in all_attrs if not elem.startswith("_")]


@pytest.mark.parametrize("class_name", public_class_names())
def test_class_has_autodoc(class_name, all_rst_content):
    expected = ".. autoclass:: pushsource.%s" % class_name
    for content in all_rst_content:
        if expected in content:
            return

    raise AssertionError("Public class is missing from docs")

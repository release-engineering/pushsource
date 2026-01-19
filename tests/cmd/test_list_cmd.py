import os
import sys
import logging
import textwrap
import itertools

import yaml
import pytest

from pushsource import Source

from pushsource._impl.list_cmd import (
    format_python_black,
    main as list_main,
    default_format,
    format_python_black,
)
from pushsource._impl import list_cmd

STAGED_DATA_DIR = os.path.join(os.path.dirname(__file__), "../staged/data")


@pytest.fixture(autouse=True)
def reset():
    # Reset sources after every test, since we'll be registering backends
    # as we load config.
    Source.reset()

    # Reset pushsource logger which may have been set to DEBUG
    # if we ran any command with --debug.
    logging.getLogger("pushsource").setLevel(logging.NOTSET)


@pytest.fixture()
def black_noop(monkeypatch, tmpdir):
    """A fixture which, when used, forces black command to succeed
    (though doesn't actually format anything).
    """

    monkeypatch.setenv("PATH", str(tmpdir))

    black = tmpdir.join("black")
    black.write('#!/bin/sh\necho "$@"\n')
    black.chmod(0o755)


@pytest.fixture()
def black_error(monkeypatch, tmpdir):
    """A fixture which, when used, forces black command to fail."""

    monkeypatch.setenv("PATH", str(tmpdir))

    black = tmpdir.join("black")
    black.write("#!/bin/sh\nexit 30\n")
    black.chmod(0o755)


def test_typical(monkeypatch, capsys):
    """A typical usage of pushsource-ls works as expected."""

    monkeypatch.setattr(sys, "argv", ["", "staged:%s/simple_files" % STAGED_DATA_DIR])

    # It should run OK
    list_main()

    # The output should contain push item stuff.
    # Just sample it.
    out, _ = capsys.readouterr()
    assert "FilePushItem(" in out
    assert "My wonderful ISO" in out


@pytest.mark.parametrize(
    "format,case",
    itertools.product(
        # The supported formats
        ["yaml", "python", "python-black"],
        # The staging areas.
        # Note: limited to 'simple' because there are some staging areas
        # intentionally set up to trigger errors, which will also cause
        # pushsource-ls to fail.
        [
            e.name
            for e in os.scandir(STAGED_DATA_DIR)
            if e.is_dir() and "simple" in e.name
        ],
    ),
)
def test_staged(monkeypatch, format, case):
    """pushsource-ls runs without crashing with all formats on staging areas
    in the test data.
    """

    monkeypatch.setattr(
        sys, "argv", ["", "--format", format, f"staged:{STAGED_DATA_DIR}/{case}"]
    )

    # It should run OK
    list_main()


def test_valid_yaml(monkeypatch, capsys):
    """'--format yaml' generates valid YAML."""

    monkeypatch.setattr(
        sys,
        "argv",
        ["", "--debug", "--format", "yaml", "staged:%s/simple_files" % STAGED_DATA_DIR],
    )

    # It should run OK
    list_main()

    # The output should be valid YAML.
    out, _ = capsys.readouterr()
    data = yaml.safe_load(out)

    # It should be a list.
    assert isinstance(data, list)

    # Not gonna check it all, but they should be dicts reproducing the
    # PushItem model.
    assert isinstance(data[0]["FilePushItem"]["name"], str)


def test_uses_config(monkeypatch, capsys, tmpdir):
    """pushsource-ls loads custom sources from a config file."""

    monkeypatch.setenv("HOME", str(tmpdir))
    tmpdir.mkdir(".config").join("pushsource.conf").write(textwrap.dedent("""
                sources:
                - name: list-cmd-test
                  url: staged:threads=2
            """).strip())
    monkeypatch.setattr(
        sys, "argv", ["", "list-cmd-test:%s/simple_files" % STAGED_DATA_DIR]
    )

    # It should run OK
    list_main()

    # It should load as normal, thus proving that list-cmd-test was
    # registered from config.
    out, _ = capsys.readouterr()
    assert "FilePushItem(" in out


def test_bad_config(monkeypatch, caplog, tmpdir):
    """pushsource-ls gives a reasonable error if config is invalid."""

    monkeypatch.setenv("HOME", str(tmpdir))
    tmpdir.mkdir(".config").join("pushsource.conf").write(
        "oops, [ this ain't valid YAML is it?"
    )
    monkeypatch.setattr(sys, "argv", ["", "any:thing"])

    # It should exit
    with pytest.raises(SystemExit) as excinfo:
        list_main()

    # With this exit code
    assert excinfo.value.code == 52

    # And it should have told us why
    assert "Error loading config" in caplog.text


def test_default_format_black(black_noop):
    """pushsource-ls picks python-black as default format if black is working."""

    assert default_format() == "python-black"


def test_default_format_noblack(black_error):
    """pushsource-ls picks python as default format if black is not working."""

    assert default_format() == "python"


def test_format_black_error(black_error):
    """black formatter raises if black command fails"""

    # It should raise
    with pytest.raises(RuntimeError) as excinfo:
        format_python_black("some-object")

    # It should tell us something about what went wrong
    assert "Cannot format with black, exit code 30" in str(excinfo.value)

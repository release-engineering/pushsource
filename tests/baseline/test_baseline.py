import os
import glob
import functools
import logging
import difflib

import yaml
import attr
import jinja2
import pytest
from mock import patch

from ..errata.fake_errata_tool import FakeErrataToolController
from ..koji.fake_koji import FakeKojiController


from pushsource import Source

LOG = logging.getLogger("test_baseline")

THIS_DIR = os.path.dirname(__file__)
CASE_DIR = os.path.join(THIS_DIR, "cases")
CASE_TEMPLATE_FILE = os.path.join(THIS_DIR, "template.yml.j2")
SRC_DIR = os.path.abspath(os.path.join(THIS_DIR, "../.."))


@pytest.fixture(scope="module")
def fake_errata_tool():
    controller = FakeErrataToolController()
    with patch(
        "pushsource._impl.backend.errata_source.errata_client.xmlrpc_client.ServerProxy"
    ) as mock_proxy:
        mock_proxy.side_effect = controller.proxy
        yield controller


@pytest.fixture(scope="module")
def fake_koji():
    controller = FakeKojiController()

    controller.load_all_builds()

    with patch("koji.ClientSession") as mock_session:
        mock_session.side_effect = controller.session
        yield controller


@pytest.fixture(scope="module")
def koji_dir(tmpdir_factory):
    yield str(tmpdir_factory.mktemp("koji"))


@pytest.fixture(scope="module", autouse=True)
def koji_test_backend(fake_koji, koji_dir):
    # kojitest backend is koji backend pointing at our koji testdata
    bound = Source.get_partial("koji:https://koji.example.com/", basedir=koji_dir)

    Source.register_backend("kojitest", bound)

    yield

    Source.reset()


@pytest.fixture(scope="module", autouse=True)
def errata_test_backend(fake_errata_tool, koji_test_backend):
    # erratatest backend is errata backend pointing at kojitest and our errata testdata
    bound = Source.get_partial(
        "errata:https://errata.example.com/", koji_source="kojitest:"
    )
    Source.register_backend("erratatest", bound)

    yield

    Source.reset()


class CaseHelper(object):
    # A helper used to deal with (de)serializing of cases.

    def __init__(self, koji_dir):
        jinja_env = jinja2.Environment()

        src_dir = os.path.join(os.path.dirname(__file__), "../..")
        src_dir = os.path.abspath(src_dir)
        jinja_env.globals["src_dir"] = src_dir

        jinja_env.globals["koji_dir"] = koji_dir

        jinja_env.filters["toyaml"] = functools.partial(
            yaml.dump, Dumper=yaml.SafeDumper
        )

        self.jinja_environment = jinja_env

        with open(CASE_TEMPLATE_FILE, "rt") as f:
            self.case_template = jinja_env.from_string(f.read())

    def unrender(self, text):
        # Given raw text that we want to save to a file, try to
        # replace various values with the best available jinja var to remove
        # per-environment differences.
        #
        # Although this is just a plain text substitution which doesn't attempt
        # to understand anything about jinja or YAML, it should be good enough
        # for our purposes.

        env = self.jinja_environment

        for var in ["src_dir", "koji_dir"]:
            text = text.replace(env.globals[var], "{{ %s }}" % var)

        return text

    def serialize(self, url, items):
        # Given:
        # - url of Source instance
        # - list of items generated by source
        # ...generate a serialized form of the case's outcome, ready for
        # comparison against baseline or for updating the baseline.

        items = sorted(items, key=lambda i: (type(i).__name__, i.src, i.name))

        item_dicts = []
        for item in items:
            asdict = attr.asdict(item, recurse=True)

            item_dicts.append({type(item).__name__: asdict})

        out_yaml = self.case_template.render(url=url, items=item_dicts)
        out_yaml = self.unrender(out_yaml)

        return out_yaml

    def case_filename(self, casename):
        return os.path.join(CASE_DIR, casename) + ".yml"

    def load_case(self, casename):
        # Given name of a case, returns case info tuple:
        # (raw text loaded from yaml file, parsed yaml)
        filename = self.case_filename(casename)

        with open(filename, "rt") as f:
            raw_case = f.read()

        template = self.jinja_environment.from_string(raw_case)
        rendered = template.render()
        data = yaml.load(rendered, Loader=yaml.BaseLoader)

        return (raw_case, data)

    def update_baseline(self, casename, case_text):
        filename = self.case_filename(casename)

        with open(filename, "wt") as f:
            f.write(case_text)


@pytest.fixture(scope="module")
def case_helper(koji_dir):
    # We use one session-scoped case helper to avoid repeatedly reloading/rendering
    # same jinja templates
    return CaseHelper(koji_dir=koji_dir)


def all_cases():
    out = [os.path.basename(name) for name in glob.glob(CASE_DIR + "/*.yml")]
    out = [os.path.splitext(name)[0] for name in out]
    return out


@pytest.mark.parametrize("casename", all_cases())
def test_source_against_baseline(casename, case_helper):
    """Using data from 'cases' directory, verify that a Source retrieved via
    URL produces exactly the items recorded in the case's data.

    If data does not match and the new behavior is desired, re-run the
    test with PUSHSOURCE_UPDATE_BASELINE=1 to automatically update the case
    files.
    """

    (case_text, case_data) = case_helper.load_case(casename)

    url = case_data["url"]

    source = Source.get(url)
    all_items = list(source)

    new_case_text = case_helper.serialize(url, all_items)

    if new_case_text == case_text:
        # Equal => passed
        return

    if os.environ.get("PUSHSOURCE_UPDATE_BASELINE") == "1":
        # Not equal but env var is set => update the baseline.
        case_helper.update_baseline(casename, new_case_text)

        return pytest.skip("Updated baseline")

    # We failed, then make a nice-looking diff
    old_lines = case_text.splitlines(keepends=True)
    new_lines = new_case_text.splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(old_lines, new_lines))
    raise AssertionError(
        (
            "Output differs from baseline:\n\n%s\n\n"
            "Re-run with PUSHSOURCE_UPDATE_BASELINE=1 if this is correct."
        )
        % diff
    )

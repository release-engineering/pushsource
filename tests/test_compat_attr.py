from pushsource._impl import compat_attr

from mock import patch


@patch("attr.s")
def test_attrs(attr_s, monkeypatch):
    monkeypatch.setattr(compat_attr, "ATTR_VERSION", (17, 4))
    compat_attr.s()
    attr_s.assert_called_once_with(frozen=True, slots=True)


@patch("attr.s")
def test_attrs_18_2(attr_s, monkeypatch):
    monkeypatch.setattr(compat_attr, "ATTR_VERSION", (18, 2))
    compat_attr.s()
    attr_s.assert_called_once_with(frozen=True, slots=True, kw_only=True)

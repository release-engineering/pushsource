import os
from pytest import raises

from pushsource import ProductIdPushItem


THIS_DIR = os.path.dirname(__file__)
CASE_DIR = os.path.join(THIS_DIR, "cases")


def test_invalid_productid():
    with raises(ValueError) as ex:
        _ = ProductIdPushItem(
            name="foo", src=os.path.join(CASE_DIR, "invalid-productid.pem")
        )

    assert "is not a ProductID certificate." in str(ex.value)

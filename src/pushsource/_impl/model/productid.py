from collections import defaultdict

from cryptography import x509
from frozenlist2 import frozenlist
from pyasn1.codec.der import decoder

from .base import PushItem
from .conv import convert_maybe, sloppylist
from .. import compat_attr as attr
from ..utils.openers import open_src_local


# Red Hat OID namespace is "1.3.6.1.4.1.2312.9",
# the trailing ".1" designates a Product Certificate.
OID_NAMESPACE = "1.3.6.1.4.1.2312.9.1."


@attr.s()
class ProductId(object):
    """A ProductID represents a group of metadata pertaining to a single product
    contained in a ProductID certificate."""

    id = attr.ib(type=int)
    """Product Engineering ID (EngID), e.g. 72

    :type: int
    """

    name = attr.ib(type=str, default=None)
    """Human readable product name, e.g. "Red Hat Enterprise Linux for IBM z Systems"

    :type: str
    """

    version = attr.ib(type=str, default=None)
    """Human readable product version string, e.g. "9.4"

    :type: str
    """

    architecture = attr.ib(type=list, default=None, converter=convert_maybe(sloppylist))
    """List of architectures supported by the product, e.g. ["s390x"]

    :type: List[str]
    """

    provided_tags = attr.ib(
        type=list, default=None, converter=convert_maybe(sloppylist)
    )
    """List of tags describing the provided platforms used for pairing with other products,
    e.g. ["rhel-9", "rhel-9-s390x"]

    :type: List[str]
    """


@attr.s()
class ProductIdPushItem(PushItem):
    """A :class:`~pushsource.PushItem` representing a product ID certificate.

    For push items of this type, the :meth:`~pushsource.PushItem.src` attribute
    refers to a file containing a PEM certificate identifying a product.
    """

    products = attr.ib(type=list, converter=frozenlist)
    """List of products described by the ProductID certificate.

    :type: List[ProductID]

    .. versionadded:: 2.45.0
    """

    @products.default
    def _default_products(self):
        return frozenlist(self._load_products(self.src) if self.src else [])

    def _load_products(self, path):
        """Returns a list of ProductIDs described by the ProductID X.509 certificate file
        in PEM format. Raises ValueError if the file doesn't describe any ProductID."""

        with open(path, "rb") as f:
            x509_certificate = x509.load_pem_x509_certificate(f.read())
        # Extensions are most commonly ASN.1 (DER) encoded UTF-8 strings.
        # First byte is usually 0x13 = PrintableString, second byte is the length of the string
        # However we can't rely on that and must parse the fields safely using a proper ASN.1 / DER
        # parser. Although cryptography module does its own ASN.1 / DER parsing, it doesn't provide
        # any public API for that yet (see https://github.com/pyca/cryptography/issues/9283),
        # so pyasn1 module has to be used instead.
        products_data = defaultdict(dict)
        for extension in x509_certificate.extensions:
            oid = extension.oid.dotted_string
            if oid.startswith(OID_NAMESPACE):
                # OID component with index 9 is always EngID
                # OID component with index 10 (last) is:
                #  1 = Product Name, e.g. "Red Hat Enterprise Linux for IBM z Systems"
                #  2 = Product Version, e.g. "9.4"
                #  3 = Product Architecture, e.g. "s390x"
                #  4 = Product Tags / Provides, e.g. "rhel-9,rhel-9-s390x"
                eng_id, attribute_id = map(int, oid.split(".")[9:11])
                products_data[eng_id][attribute_id] = str(
                    decoder.decode(extension.value.value)[0]
                )

        if not products_data:
            raise ValueError("File '%s' is not a ProductID certificate." % path)

        result = []
        for eng_id, product_data in products_data.items():
            product = ProductId(
                id=eng_id,
                name=product_data.get(1),
                version=product_data.get(2),
                architecture=product_data.get(3),
                provided_tags=product_data.get(4),
            )
            result.append(product)
        return result

    opener = attr.ib(type=callable, default=open_src_local, repr=False)
    """Identical to :attr:`~pushsource.PushItem.opener`.

    This defaults to reading content as file from :attr:`~pushsource.PushItem.src`
    
    .. versionadded:: 2.51.0
    """

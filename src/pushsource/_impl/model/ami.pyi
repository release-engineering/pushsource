from collections import Sequence
from typing import Text, Optional

from pushsource import PushItem
from pushsource._impl.type_aliases import Date


class AmiRelease(object):
    product: Text
    date: Date
    arch: Text
    respin: int
    version: Optional[Text] = ...
    base_product: Optional[Text] = ...
    base_version: Optional[Text] = ...
    variant: Optional[Text] = ...
    type: Optional[Text] = ...

class AmiBillingCodes(object):
    name: Text = ...
    codes: Sequence[Text] = ...

class AmiPushItem(PushItem):
    release: Optional[AmiRelease] = ...
    type: Optional[Text] = ...
    region: Optional[Text] = ...
    virtualization: Optional[Text] = ...
    volume: Optional[Text] = ...
    root_device: Optional[Text] = ...
    description: Optional[Text] = ...
    sriov_net_support: Optional[Text] = ...
    ena_support: Optional[bool] = ...
    billing_codes: Optional[AmiBillingCodes] = ...

from typing import Text, Optional

from pushsource import PushItem

class RpmPushItem(PushItem):
    module_build: Optional[Text] = ...

from typing import Optional, Text

from pushsource import PushItem


class FilePushItem(PushItem):
    description: Optional[Text] = ...
    version: Optional[Text] = ...
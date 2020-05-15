from ...model import ModuleMdPushItem
from .staged_base import StagedBaseMixin, handles_type


class StagedModuleMdMixin(StagedBaseMixin):
    @handles_type("MODULEMD")
    def __push_item(self, leafdir, _, entry):
        return ModuleMdPushItem(
            name=entry.name, src=entry.path, origin=leafdir.topdir, dest=[leafdir.dest]
        )

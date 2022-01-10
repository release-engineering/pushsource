class Module(object):
    name: str
    stream: str
    version: str
    context: str
    arch: str
    nsvca: str
    @classmethod
    def from_file(cls, fname: str) -> "Module": ...
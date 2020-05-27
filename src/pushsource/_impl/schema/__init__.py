import yaml
import os


SCHEMA_PATH = os.path.dirname(__file__)


def get_schema(name):
    filename = "%s-schema.yaml" % name
    path = os.path.join(SCHEMA_PATH, filename)
    with open(path) as f:
        return yaml.load(f, Loader=yaml.SafeLoader)

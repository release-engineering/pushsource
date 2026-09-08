import datetime
from collections import Mapping, Sequence
from numbers import Number
from typing import Union, Collection, Optional

Date = datetime.date
DateTime = datetime.datetime

MaybeString = Union[str, Collection[str]]

# First attempt at a JsonObject type based on the spec from
# https://www.json.org/json-en.html
# from the spec a Value can be a string, number, object, array, true, false, or null
# the "null" case is covered by Optional[]
_JsonValue = Optional[Union[str, Number, object, "_JsonArray", bool]]
_JsonArray = Sequence[_JsonValue]
JsonObject = Mapping[str, _JsonValue]

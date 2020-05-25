"""Utilities for JSON serialization."""

import json
from google.protobuf import json_format
from google.protobuf import message


class ProtoJsonEncoder(json.JSONEncoder):
    """Custom encoder which can serialize protobuf objects."""
    def default(self, obj):
        if isinstance(obj, message.Message):
            # Object is protobuf. Convert to python json representation.
            return json.loads(json_format.MessageToJson(obj))
        else:
            return super().default(obj)

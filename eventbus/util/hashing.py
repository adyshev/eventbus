# -*- coding: utf-8 -*-
import os
import hashlib

from eventbus.util.transcoding import ObjectJSONEncoder

SALT_FOR_DATA_INTEGRITY = os.getenv("SALT_FOR_DATA_INTEGRITY", "")


def hash_object(json_encoder: ObjectJSONEncoder, obj: dict) -> str:
    """
    Calculates SHA-256 hash of JSON encoded 'obj'.
    """
    s = json_encoder.encode((obj, SALT_FOR_DATA_INTEGRITY))
    return hashlib.sha256(s).hexdigest()

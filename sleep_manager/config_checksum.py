import hashlib
import json


def compute_config_checksum(common: dict, waker: dict, sleeper: dict) -> str:
    payload = {"common": common, "waker": waker, "sleeper": sleeper}
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

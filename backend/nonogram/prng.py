from __future__ import annotations

import hashlib
import random


GENERATOR_VERSION = 1


def build_rng(seed: int, size: int, version: int = GENERATOR_VERSION) -> random.Random:
    payload = f"{seed}:{size}:{version}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return random.Random(int(digest, 16))

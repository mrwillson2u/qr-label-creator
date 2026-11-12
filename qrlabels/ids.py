"""Label ID generation."""
import secrets
from typing import List

# shortuuid's alphabet: drops 0/O, 1/I/l and other lookalikes.
RANDOM_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def sequential_ids(count: int, start: int = 1, prefix: str = "", digits: int = 8) -> List[str]:
    """e.g. ASN00000001, ASN00000002, ..."""
    return [f"{prefix}{n:0{digits}d}" for n in range(start, start + count)]


def random_ids(count: int, prefix: str = "", length: int = 12) -> List[str]:
    """Random IDs, unique within the batch."""
    ids = set()
    while len(ids) < count:
        ids.add(prefix + "".join(secrets.choice(RANDOM_ALPHABET) for _ in range(length)))
    return sorted(ids)


def read_ids(path: str) -> List[str]:
    """One ID per line; blank lines are skipped."""
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

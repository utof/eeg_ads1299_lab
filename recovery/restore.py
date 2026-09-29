"""One-time, data-only transport of original Git objects; never edits a worktree."""
from __future__ import annotations

import base64
import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess
import sys

BASE_TREE = "31a4cfa2af5be77f688d2669efa0a3b4c72d6901"
HEAD = "07edcacc4c22bfd2ae5aa053c658d6c480b75f5e"
TREE = "0c6dd0675c977cbcef2ef043cb49e9081b8c9b8f"
BOARD = "hardware/rev_a/layout/rev_a.kicad_pcb"
BOARD_SHA = "71b066ed8c9842035553bbc125b5c428877d180b2b2ef66ba986a2032830899f"
ARCHIVE_SHA = "e2322918a0d44e7a91ffd8651e9d2de0714a36820518e6c996d1231b4993952c"
PART_HASHES = (
    "26c380478fdd901d98dce7bf4c5574d91c352c3cdc0f7a9e66917702fd253eca",
    "a68d532cab0f6fc402eacf0d9341f3697213be91a2428c244387335625dcde0d",
    "39044aa8cf6c7bdc3164a96a5038bf0259b632d1c140368e0fc33efbaf198199",
    "921e343f57108217f124c16c6e0f899a79adbaffaedecf5d745e6095f581bceb",
    "dc1f3125ffb5097650bde4c080a0e9426b5dd0fad4f228624e8049e89eeef02e",
    "7199fc383ff111a3bf92a4c4940c52b73460eaf6d4f2a88930fb1057fe30601a",
    "ec93571a485ad729a597fcea17a4b7865ff1acb251dca961d891d9c3a9994c57",
    "f53f48761db0cdb0247eb16e83245ef814166f9cdccfb5107f5ab53604f7b7e4",
)


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def git(*args: str, data: bytes | None = None) -> bytes:
    return subprocess.run(
        ["git", *args], input=data, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True, timeout=60,
    ).stdout


def records(folder: Path) -> list[tuple[str, str, bytes]]:
    parts = []
    for number, digest in enumerate(PART_HASHES, 1):
        part = (folder / f"objects-{number:02d}.b64").read_bytes()
        require(len(part) == (14489 if number == 8 else 16001), f"part {number}: size")
        require(hashlib.sha256(part).hexdigest() == digest, f"part {number}: digest")
        parts.append(part.strip())
    packed = base64.b64decode(b"".join(parts), validate=True)
    require(len(packed) == 94864, "archive size")
    require(hashlib.sha256(packed).hexdigest() == ARCHIVE_SHA, "archive digest")
    decoder = lzma.LZMADecompressor(memlimit=256 * 1024 * 1024)
    raw = decoder.decompress(packed, max_length=1724637)
    require(len(raw) == 1724636 and decoder.eof and not decoder.unused_data, "archive framing")
    result = []
    seen = set()
    offset = 0
    while offset < len(raw):
        require(offset + 24 <= len(raw), "truncated record")
        oid = raw[offset:offset + 20].hex()
        size = struct.unpack_from(">I", raw, offset + 20)[0]
        offset += 24
        require(0 < size <= len(raw) - offset, "record length")
        obj = raw[offset:offset + size]
        offset += size
        require(hashlib.sha1(obj).hexdigest() == oid and oid not in seen, "object identity")
        header, body = obj.split(b"\0", 1)
        kind, length = header.decode("ascii").split(" ")
        require(kind in {"blob", "tree", "commit"} and str(len(body)) == length, "object header")
        seen.add(oid)
        result.append((oid, kind, body))
    require(len(result) == 77, "object count")
    return result


def verify() -> dict[str, object]:
    require(git("rev-parse", f"{HEAD}^{{tree}}").decode().strip() == TREE, "candidate tree")
    require(git("rev-list", "--count", HEAD).strip() == b"10", "local ancestry count")
    git("rev-list", "--objects", HEAD)
    files = git("ls-tree", "-r", "--name-only", "-z", HEAD).split(b"\0")[:-1]
    require(len(files) == 280, "candidate source count")
    require(hashlib.sha256(git("show", f"{HEAD}:{BOARD}")).hexdigest() == BOARD_SHA, "board hash")
    git("fsck", "--no-reflogs", "--no-dangling", HEAD)
    return {
        "scope": "source_integrity_only_not_native_ci_or_electrical_review",
        "original_local_head": HEAD, "tree": TREE, "source_files": len(files),
        "original_local_commits": 10, "board_sha256": BOARD_SHA,
        "fabrication_ready": False, "body_connection_authorized": False,
    }


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--verify-only":
        result = verify()
    else:
        require(git("cat-file", "-t", BASE_TREE).strip() == b"tree", "required base tree absent")
        objects = records(Path(__file__).resolve().parent)
        for oid, kind, body in objects:
            actual = git("hash-object", "-w", "-t", kind, "--stdin", data=body).decode().strip()
            require(actual == oid, "Git import identity")
        result = verify()
        result.update(imported_objects=len(objects), transport_sha256=ARCHIVE_SHA)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

"""Map only the exact L5 delta for legacy hash checks; never edit PCB source."""

import hashlib
import json
import re
from pathlib import Path

from tests.test_pcb_power import _form_end

DELTA = Path(__file__).parent / "fixtures/auxiliary_l5_delta.json"


def copper_records(text: str, excluded_net: str | None = None) -> dict[str, dict[str, str]]:
    code = None
    if excluded_net is not None:
        match = re.search(r'\(net (\d+) "' + re.escape(excluded_net) + r'"\)', text)
        assert match is not None, "missing excluded net"
        code = match[1]
    result: dict[str, dict[str, str]] = {}
    for match in re.finditer(r"\((footprint|segment|via)\s", text):
        form = text[match.start() : _form_end(text, match.start())]
        if match[1] != "footprint" and code is not None and re.search(rf"\(net {code}\)", form):
            continue
        ident = re.search(r'\(uuid "([^"]+)"', form)
        assert ident is not None and ident[1] not in result, "missing/duplicate source UUID"
        result[ident[1]] = {"type": match[1], "sha256": hashlib.sha256(form.encode()).hexdigest()}
    return result


def _records(value: object) -> dict[str, dict[str, str]]:
    assert isinstance(value, dict), "invalid L5 delta"
    result: dict[str, dict[str, str]] = {}
    items: dict[object, object] = value
    for ident, record in items.items():
        assert isinstance(ident, str) and isinstance(record, dict), "invalid L5 delta item"
        assert set(record) == {"type", "sha256"}, "invalid L5 delta fields"
        kind: object = record["type"]
        digest: object = record["sha256"]
        assert isinstance(kind, str) and kind in ("footprint", "segment", "via")
        assert isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
        result[ident] = {"type": kind, "sha256": digest}
    return result


def legacy_auxiliary_records(actual: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Accept the old objects OR the complete exact L5 delta, never a mixture.

    Only hash-comparison records are mapped. Original P2/clock fixtures, actual
    routing, native DRC and electrical checks are untouched. An unrelated object
    survives this mapping and must still satisfy the original caller's guard.
    """
    raw: object = json.loads(DELTA.read_text())
    assert isinstance(raw, dict), "invalid L5 delta root"
    before, after = _records(raw["before"]), _records(raw["after"])
    assert len(before) == 21 and len(after) == 41
    affected = before.keys() | after.keys()
    observed = {ident: actual[ident] for ident in affected & actual.keys()}
    if observed == before:
        return dict(actual)
    assert observed == after, "unreviewed or partial L5 source delta"
    result = {ident: record for ident, record in actual.items() if ident not in affected}
    result.update(before)
    return result

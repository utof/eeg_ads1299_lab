"""Read-only local-library/cache equality check, not a KiCad editor or netlist parser.

Only balanced S-expression structure is read here. KiCad still interprets CAD
semantics. Symbol bodies must match token-for-token (whitespace is immaterial),
after removing the embedded root identifier's RevA: prefix. No inheritance or
implicit library update is supported by this closed, project-local contract.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass

_TOKEN = re.compile(r'\s+|"(?:[^"\\]|\\.)*"|[()]|[^\s()"]+')


@dataclass(frozen=True)
class _Form:
    items: tuple[str | _Form, ...]


def _tokens(content: str) -> Iterator[str]:
    if len(content) > 2_000_000:
        raise ValueError("symbol source exceeds the bounded input size")
    end = 0
    for match in _TOKEN.finditer(content):
        if match.start() != end:
            raise ValueError("malformed symbol string/token")
        end = match.end()
        token = match[0]
        if not token.isspace():
            yield token
    if end != len(content):
        raise ValueError("unterminated symbol string/token")


def _parse(content: str) -> _Form:
    stack: list[list[str | _Form]] = [[]]
    for token in _tokens(content):
        if token == "(":
            if len(stack) >= 64:
                raise ValueError("symbol source nesting exceeds the bounded depth")
            stack.append([])
        elif token == ")":
            if len(stack) == 1 or not stack[-1]:
                raise ValueError("unbalanced or empty symbol expression")
            form = _Form(tuple(stack.pop()))
            stack[-1].append(form)
        else:
            stack[-1].append(token)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError("symbol source must contain exactly one balanced root")
    root = stack[0][0]
    if not isinstance(root, _Form):
        raise ValueError("symbol source requires a parenthesized root")
    return root


def _children(form: _Form, head: str) -> list[_Form]:
    return [child for child in form.items if isinstance(child, _Form) and child.items[0] == head]


def _name(form: _Form) -> str:
    if len(form.items) < 2 or not isinstance(form.items[1], str):
        raise ValueError("symbol identifier is absent or malformed")
    token = form.items[1]
    if not token.startswith('"'):
        raise ValueError("symbol identifier must be quoted")
    name: object = json.loads(token)
    if not isinstance(name, str) or not name:
        raise ValueError("symbol identifier must be a nonempty string")
    return name


def _symbols(root: _Form, embedded: bool) -> dict[str, tuple[str | _Form, ...]]:
    result: dict[str, tuple[str | _Form, ...]] = {}
    for symbol in _children(root, "symbol"):
        name = _name(symbol)
        if embedded:
            if not name.startswith("RevA:"):
                raise ValueError("embedded symbol is outside the local RevA library")
            name = name.removeprefix("RevA:")
        if not name or name in result:
            raise ValueError("empty or duplicate symbol definition")
        if _children(symbol, "extends"):
            raise ValueError("symbol inheritance is not supported by this closed library")
        result[name] = symbol.items[2:]
    if not result:
        raise ValueError("empty symbol library/cache")
    return result


def _cache(content: str) -> dict[str, tuple[str | _Form, ...]]:
    root = _parse(content)
    if root.items[0] != "kicad_sch":
        raise ValueError("embedded symbol cache requires a kicad_sch root")
    sections = _children(root, "lib_symbols")
    if len(sections) != 1:
        raise ValueError("sheet requires exactly one embedded symbol cache")
    cache = _symbols(sections[0], embedded=True)
    used: set[str] = set()
    for instance in _children(root, "symbol"):
        ids = _children(instance, "lib_id")
        if len(ids) != 1 or len(ids[0].items) != 2:
            raise ValueError("symbol instance requires exactly one library identifier")
        used.add(_name(ids[0]))
    if used != {"RevA:" + name for name in cache}:
        raise ValueError("embedded symbol inventory differs from the placed symbols")
    return cache


def validate_symbol_caches(library: str, sheets: dict[str, str]) -> None:
    """Reject stale/conflicting local definitions without modifying native sources."""
    root = _parse(library)
    if root.items[0] != "kicad_symbol_lib":
        raise ValueError("local symbols require a kicad_symbol_lib root")
    local = _symbols(root, embedded=False)
    for sheet, content in sheets.items():
        for name, body in _cache(content).items():
            if name not in local or local[name] != body:
                raise ValueError(f"{sheet}: embedded symbol {name} differs from the local library")

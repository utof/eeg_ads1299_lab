"""Frozen native text shared by software tests; never the installed production library."""

import gzip
from pathlib import Path


def footprint_sources() -> dict[str, str]:
    directory = Path(__file__).parent / "fixtures/footprints"
    result: dict[str, str] = {}
    for path in sorted(directory.glob("*.pretty/*.kicad_mod.gz")):
        identifier = path.parent.stem + ":" + path.name.removesuffix(".kicad_mod.gz")
        content = gzip.decompress(path.read_bytes()).decode()
        if identifier in result or len(content) > 100_000:
            raise ValueError("invalid frozen footprint entry")
        result[identifier] = content
    if len(result) != 9:
        raise ValueError("expected exactly nine frozen footprint sources")
    return result


def write_footprint_library(directory: Path) -> Path:
    for identifier, content in footprint_sources().items():
        library, name = identifier.split(":")
        path = directory / (library + ".pretty") / (name + ".kicad_mod")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return directory

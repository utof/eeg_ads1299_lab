"""One-time serialization of an already verified native board; removed after publication."""
import gzip
import hashlib
import json
from pathlib import Path

from hardware.rev_a import load_documents, make_pcb_seed, parse_schematic_xml
from hardware.rev_a.pcb_seed import _render
from hardware.rev_a.schematic_symbols import _children, _Form, _name, _parse
from tests.footprint_fixtures import footprint_sources

EXPECTED = 'd0b08a12aa90265e6ec4a9339fe6306668ed43795148a437ad1a66ed06264aaf'


def form(*items):
    return _Form(items)


def replace_child(node, name, new):
    children = [i for i, x in enumerate(node.items) if isinstance(x, _Form) and x.items[0] == name]
    assert len(children) == 1, name
    items = list(node.items)
    items[children[0]] = new
    return form(*items)


def placed(fp, pose):
    angle = pose[2]
    fp = replace_child(fp, 'at', form('at', *(f'{v:g}' for v in pose)))
    result = list(fp.items[:2])
    ref = json.loads(_children(fp, 'property')[0].items[2])
    for child in fp.items[2:]:
        assert isinstance(child, _Form)
        kind = child.items[0]
        if kind == 'property' and _name(child) in {'Reference', 'Value'}:
            child = replace_child(child, 'layer', form('layer', '"F.Fab"'))
            child = form(*child.items, form('hide', 'yes'))
        elif kind == 'pad':
            old = _children(child, 'at')[0]
            rotation = float(old.items[3]) if len(old.items) == 4 else 0
            child = replace_child(child, 'at', form(*old.items[:3], f'{(rotation + angle) % 360:g}'))
        elif kind == 'fp_text' and child.items[2] == '"${REFERENCE}"':
            child = replace_child(child, 'at', form('at', '0', '0', f'{angle:g}'))
            child = replace_child(child, 'effects', form('effects', form('font', form('size', '0.6', '0.6'), form('thickness', '0.1'))))
        elif kind == 'fp_text' and child.items[2] == '"+"' and _name(_children(child, 'layer')[0]) == 'F.SilkS':
            child = replace_child(child, 'effects', form('effects', form('font', form('size', '0.8', '0.8'), form('thickness', '0.12'))))
            if ref == 'C7':
                child = replace_child(child, 'at', form('at', '-2.9', '-2.2'))
        result.append(child)
    return form(*result)


def content(repo, recipe):
    cad = repo / 'hardware/rev_a/kicad'
    xml = gzip.decompress((repo/'tests/fixtures/rev_a_netlist.xml.gz').read_bytes()).decode()
    graph = parse_schematic_xml(xml)
    libraries = footprint_sources()
    for path in (cad/'RevA_Passives.pretty').glob('*.kicad_mod'):
        libraries['RevA_Passives:'+path.stem] = path.read_text()
    libraries = {k: libraries[k] for k in {p.footprint for p in graph.parts.values()} - {''}}
    profile, bom, _ = load_documents(cad.parent)
    seed = make_pcb_seed(xml, (cad/'rev_a.kicad_sch').read_text(), libraries, profile, bom)
    footprints = _children(_parse(seed), 'footprint')
    poses = json.loads((recipe/'positions.json').read_text())
    assert len(footprints) == len(poses) == 68
    lines = []
    for fp in footprints:
        ref = json.loads(_children(fp, 'property')[0].items[2])
        lines.append(_render(placed(fp, poses.pop(ref))))
    assert not poses
    result = (recipe/'prefix.txt').read_text() + '\n'.join(lines) + (recipe/'tail.txt').read_text()
    assert hashlib.sha256(result.encode()).hexdigest() == EXPECTED, hashlib.sha256(result.encode()).hexdigest()
    return result


if __name__ == '__main__':
    import sys
    repo = Path.cwd()
    recipe = Path(__file__).resolve().parent
    result = content(repo, recipe)
    path = repo/'hardware/rev_a/layout/rev_a.kicad_pcb'
    assert not path.exists(), 'Never overwrite an authored board'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result)
    print('Exact verified native board restored:', EXPECTED)

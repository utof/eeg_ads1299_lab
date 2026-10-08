"""One-shot read-only native source inspection for the L5 implementation."""
from pathlib import Path
import hashlib
import json
import subprocess
import pcbnew

BASE = Path('/tmp/l5-edit')
OUT = Path('/tmp/l5-out')
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == 'ff953c03c452f1572602b52aa62f42e80bfa9588'
assert pcbnew.GetBuildVersion().startswith('9.0.2')

def xy(v):
    return [round(pcbnew.ToMM(v.x), 6), round(pcbnew.ToMM(v.y), 6)]

def inspect_board(rel, region, refs, nets):
    board = pcbnew.LoadBoard(str(BASE / rel))
    rows = []
    for fp in board.GetFootprints():
        if fp.GetReference() in refs:
            rows.append({'ref': fp.GetReference(), 'at': xy(fp.GetPosition()), 'angle': fp.GetOrientationDegrees(), 'pads': [{'n': p.GetNumber(), 'at': xy(p.GetPosition()), 'size': xy(p.GetSize()), 'net': p.GetNetname()} for p in fp.Pads()]})
    tracks = []
    for t in board.GetTracks():
        a, b = xy(t.GetStart()), xy(t.GetEnd())
        inside = any(region[0] <= p[0] <= region[1] and region[2] <= p[1] <= region[3] for p in (a, b))
        if inside and (t.GetNetname() in nets or t.GetClass() == 'PCB_VIA'):
            tracks.append({'id': t.m_Uuid.AsString(), 'net': t.GetNetname(), 'kind': t.GetClass(), 'a': a, 'b': b, 'layer': t.GetLayerName(), 'width': pcbnew.ToMM(t.GetWidth())})
    print('BOARD_GEOMETRY', rel, json.dumps({'footprints': rows, 'tracks': tracks}, separators=(',', ':')))

inspect_board('hardware/rev_a/layout/rev_a.kicad_pcb', (50, 65, 31, 41), {'U1','C17','R20','R21','R22','R23'}, {'MISO','GPIO1','GPIO2','GPIO3','GPIO4','DVDD','SCLK','GND'})
inspect_board('hardware/rev_a/auxiliary/auxiliary.kicad_pcb', (35, 45, 21, 39), {'U102','C103','C104','R114'}, {'AFE_SCLK','AFE_MOSI','AFE_CS','MCU_MISO','AFE_MISO','AFE_DVDD','MCU_3V3','MCU_SCLK','MCU_MOSI','MCU_CS','TARGET_GND'})
for path, keywords, radius in (
    ('hardware/rev_a/kicad/digital.kicad_sch', ['global_label "MISO"','property "Reference" "R20"'], 14),
    ('hardware/rev_a/auxiliary/bus.kicad_sch', ['global_label "AFE_SCLK"','global_label "AFE_MOSI"','global_label "AFE_CS"','global_label "MCU_MISO"','property "Reference" "R114"'], 10),
    ('hardware/rev_a/check_schematic.py', ['FOOTPRINTS =','def _symbol','def _ads_pins','def _fixed_pins','def _passive_pairs'], 50),
    ('hardware/rev_a/check_baseline.py', ['def validate_bom','def validate_baseline'], 30),
    ('tests/test_pcb_placement.py', ['def _output', 'MISO','DRDY'], 4),
):
    lines = (BASE / path).read_text().splitlines()
    keep = set()
    for i, line in enumerate(lines):
        if any(key in line for key in keywords):
            keep.update(range(max(0, i-radius if 'global_label' in line else i), min(len(lines), i+radius+1)))
    print('SOURCE_ANCHORS', path)
    for i in sorted(keep):
        print(f'{i+1}: {lines[i]}')
contract = json.loads((BASE/'hardware/rev_a/auxiliary/contract.json').read_text())
print('AUX_PARTS', json.dumps([p for p in contract['parts'] if p['reference'] in ['U102','R114','R113']], separators=(',',':')))
bom = json.loads((BASE/'hardware/rev_a/bom.json').read_text())
print('BOM_SCHEMA', json.dumps(bom, separators=(',',':')))
subprocess.run(['git','diff','--exit-code'], check=True)
(OUT/'inspection.json').write_text(json.dumps({'head':'ff953c03c452f1572602b52aa62f42e80bfa9588','source_changed':False,'native_version':pcbnew.GetBuildVersion()},indent=2)+'\n')

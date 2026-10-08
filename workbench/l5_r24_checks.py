"""Author focused R24 regressions and collect bounded diagnostics; no publication."""
from pathlib import Path
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path('/tmp/l5-edit')
OUT = Path('/tmp/l5-out')

def replace(path, old, new):
    text = path.read_text()
    assert text.count(old) == 1, (path, old, text.count(old))
    path.write_text(text.replace(old,new))

def run(name, args, timeout):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    (OUT/(name+'.log')).write_text(result.stdout+result.stderr)
    tail = (result.stdout+result.stderr)[-5000:]
    print('CHECK_RESULT',name,result.returncode,tail,flush=True)
    return result

native = r'''

# These faults operate on the authored PCB and use the existing fresh-refill
# native DRC helper. They do not borrow schematic connectivity as PCB evidence.
_R24_MUTATION_SCRIPT = r"""
import sys
import pcbnew as p
assert p.Version() == "9.0.2"
b = p.LoadBoard(sys.argv[1])
rows = [f for f in b.GetFootprints() if f.GetReference() == "R24"]
assert len(rows) == 1, "R24 footprint missing"
pads = {pad.GetNumber(): pad for pad in rows[0].Pads()}
assert pads["1"].GetNetname() == "MISO_DRV"
assert pads["2"].GetNetname() == "MISO"
change = sys.argv[2]
if change == "bridge":
    track = p.PCB_TRACK(b)
    track.SetStart(pads["1"].GetPosition())
    track.SetEnd(pads["2"].GetPosition())
    track.SetLayer(p.F_Cu)
    track.SetWidth(p.FromMM(0.15))
    track.SetNetCode(pads["1"].GetNetCode())
    b.Add(track)
else:
    if change == "driver-cut":
        adc = next(f for f in b.GetFootprints() if f.GetReference() == "U1")
        anchor = next(pad for pad in adc.Pads() if pad.GetNumber() == "43")
    else:
        assert change == "receiver-cut"
        anchor = pads["2"]
    tracks = [t for t in b.GetTracks() if t.Type() == p.PCB_TRACE_T
              and t.GetNetCode() == anchor.GetNetCode()
              and anchor.GetPosition() in (t.GetStart(), t.GetEnd())]
    assert len(tracks) == 1, "fault must remove exactly one endpoint launch"
    b.Remove(tracks[0])
p.SaveBoard(sys.argv[1], b)
"""


@pytest.mark.schematic
@pytest.mark.parametrize("change", ["driver-cut", "receiver-cut", "bridge"])
def test_native_r24_detects_either_open_or_a_parallel_copper_bypass(
    tmp_path: Path, change: str
) -> None:
    cad = tmp_path / "cad"
    shutil.copytree(CAD, cad)
    board = cad / "rev_a.kicad_pcb"
    shutil.copyfile(BOARD, board)
    result = subprocess.run(
        [
            os.environ.get("KICAD_PYTHON", "/usr/bin/python3"),
            "-c",
            _R24_MUTATION_SCRIPT,
            str(board),
            change,
        ],
        capture_output=True,
        text=True,
        timeout=45,
        env=dict(os.environ, KICAD_CONFIG_HOME=str(cad / "mutation-config")),
    )
    (cad / "r24-mutation.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    report = _native_report(cad)
    assert report["schematic_parity"] == []
    if change == "bridge":
        findings = json.dumps(report["violations"])
        assert "shorting_items" in findings and "MISO_DRV" in findings and "MISO" in findings
        assert report["unconnected_items"] == []
    else:
        findings = json.dumps(report["unconnected_items"])
        assert "R24" in findings and "MISO" in findings
'''
population = '''


def test_r24_remains_an_unselected_open_position_not_an_approved_fit(
    spi_graphs: dict[Board, SchematicNetlist],
) -> None:
    graph = spi_graphs["afe"]
    rows = [part for part in graph.parts.values() if part.native_ref == "R24"]
    assert len(rows) == 1, "R24 open-fit requirement needs a real schematic position"
    part = rows[0]
    assert part.value == "UNSELECTED" and part.properties["MPN"] == "UNSELECTED"
    assert part.properties["Population"] == "dnp" and "dnp" in part.properties
    assert "exclude_from_board" not in part.properties
'''

phase = sys.argv[1]
pcbtests = ROOT/'tests/test_pcb_placement.py'
spitests = ROOT/'tests/test_spi_series_positions.py'
if phase == 'before':
    pcbtests.write_text(pcbtests.read_text()+native)
    spitests.write_text(spitests.read_text()+population)
    replace(pcbtests, 'for name in ("MISO", "DRDY"):', 'for name in ("MISO", "MISO_DRV", "DRDY"):')
    replace(pcbtests, '        "inner_trace_mm": sum(p.ToMM(t.GetLength()) for t in inner),', '        "inner_trace_mm": sum(p.ToMM(t.GetLength()) for t in inner),\n        "total_trace_mm": sum(p.ToMM(t.GetLength()) for t in traces),')
    replace(pcbtests, '@pytest.mark.parametrize("net", ["MISO", "DRDY"])\ndef test_output_corridor_uses_front_runs_and_local_ground_referenced_escapes(', '@pytest.mark.parametrize("net", ["MISO", "MISO_DRV", "DRDY"])\ndef test_output_corridor_uses_front_runs_and_local_ground_referenced_escapes(')
    replace(pcbtests, '    assert _output_reference_ok(output_reference[net]), output_reference[net]\n', '''    assert _output_reference_ok(output_reference[net]), output_reference[net]
    if net == "MISO_DRV":
        row = output_reference[net]
        assert isinstance(row, dict)
        assert row["layers"] == ["F.Cu"] and row["vias"] == 0
        length = row["total_trace_mm"]
        assert isinstance(length, (int, float)) and length <= 3.0
''')
    result = run('r24-new-requirements-before', ['uv','run','--locked','python','-m','pytest','tests/test_spi_series_positions.py::test_r24_remains_an_unselected_open_position_not_an_approved_fit','tests/test_pcb_placement.py::test_native_r24_detects_either_open_or_a_parallel_copper_bypass','tests/test_pcb_placement.py::test_output_corridor_uses_front_runs_and_local_ground_referenced_escapes[MISO_DRV]','-q','--junitxml='+str(OUT/'r24-before.xml')], 90)
    root = ET.parse(OUT/'r24-before.xml').getroot()
    assert result.returncode == 1 and len(root.findall('.//failure')) == 5 and not root.findall('.//error')
    print('FIVE_NEW_R24_REQUIREMENTS_OBSERVED_FAILING', flush=True)
elif phase == 'after':
    replace(pcbtests, "assert text.count('(footprint \"') == 69", "assert text.count('(footprint \"') == 70")
    replace(pcbtests, "assert text.count('(pad \"') == 251", "assert text.count('(pad \"') == 253")
    replace(pcbtests, 'assert text.count(" dnp)") == 8', 'assert text.count(" dnp)") == 9')
    result=run('r24-format',['uv','run','--locked','ruff','format','hardware/rev_a/check_schematic.py','tests/test_pcb_placement.py','tests/test_spi_series_positions.py'],45)
    assert result.returncode == 0
    result=run('ordinary-gate',['uv','run','--locked','python','-m','tools.check'],300)
    # An expected four-position red stage is not a successful quality gate.
    print('ORDINARY_GATE_IS_NOT_ASSUMED_GREEN', result.returncode, flush=True)
    cad = run('r24-native-module',['uv','run','--locked','python','-m','pytest','tests/test_pcb_placement.py','-q','--junitxml='+str(OUT/'r24-native.xml'),'--basetemp='+str(OUT/'native-tests')],450)
    assert cad.returncode == 0, 'R24 native module has unresolved findings'
    (OUT/'checked-source.patch').write_bytes(subprocess.check_output(['git','diff','--binary','ff953c03c452f1572602b52aa62f42e80bfa9588'],cwd=ROOT))
    print('R24_NATIVE_MODULE_PASSED_BUT_AUXILIARY_FOUR_ARE_UNFINISHED',flush=True)
else:
    raise ValueError(phase)

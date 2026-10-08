"""Continue the bounded R24 author with demonstrated reference/test corrections."""
from pathlib import Path
import subprocess

# Reuse the already inspected wrapper, including all exact baseline identities,
# native DRC corrections, fail-first ordering, diagnostics and retention.
wrapper = subprocess.check_output(['git','show','6c7687fcf11035379978bc600db329b3a396c47f:workbench/l5_author.py'],text=True)
anchor="OUT.mkdir(exist_ok=True)\n(OUT/'corrected-author.py').write_text(source)"
assert wrapper.count(anchor)==1
changes=r'''
# Retain destructive-test IDs and the existing one-form-per-track convention.
change("(59.475,34.3)],'GPIO2/local')", "(59.475,34.3)],'GPIO2/local',first_identity='2cd6645a-3169-55d4-b8f1-11a0a91ef3ac')")
change("def normalize(form):\n    return re.sub", "def normalize(form):\n    if form.startswith('(segment'):\n        form=' '.join(form.split())\n    return re.sub")
# The old planar grid checked copper spacing but not the wider real plane voids.
# Use exactly the native full-width reference operation already used by the tests,
# on each proposed MISO edge; no foreign-contact exclusion or tolerance increase.
change("    dist={s:0.}; parent={}; heap=[(math.dist(s,goal),0.,s)]", """    if net == 'MISO':
        b.BuildConnectivity()
        assert p.ZONE_FILLER(b).Fill(b.Zones())
        planes=[z for z in b.Zones() if z.GetNetname()=='GND' and z.IsOnLayer(p.In1_Cu)]
        assert len(planes)==1
        allowed=p.SHAPE_POLY_SET(planes[0].GetFilledPolysList(p.In1_Cu))
        def shape(item, extra=0):
            poly=p.SHAPE_POLY_SET()
            item.TransformShapeToPolygon(poly,item.GetLayer(),extra,p.FromMM(.005),p.ERROR_OUTSIDE)
            return poly
        contacts=[t for t in b.GetTracks() if t.GetNetname()==net and t.Type()==p.PCB_VIA_T]
        contacts += [pad for fp in b.GetFootprints() for pad in fp.Pads() if pad.GetNetname()==net and pad.IsOnLayer(p.In1_Cu)]
        for contact in contacts:
            allowed.BooleanAdd(shape(contact,planes[0].GetLocalClearance()+p.FromMM(.025)))
        for t in b.GetTracks():
            if t.GetNetname()!=net or t.Type()==p.PCB_VIA_T: continue
            uncovered=shape(t); uncovered.BooleanSubtract(allowed)
            if uncovered.Area():
                print('EXISTING_MISO_REFERENCE_GAP',t.m_Uuid.AsString(),point(t.GetStart()),point(t.GetEnd()),t.GetLayerName(),uncovered.Area()/1e12,flush=True)
                assert uncovered.Area()/1e12 <= .00001, 'Local new contact intersects preserved MISO reference; relocate contact, not waive gap'
        def referenced(u,v):
            t=p.PCB_TRACK(b); t.SetLayer(p.In2_Cu); t.SetWidth(p.FromMM(.15))
            t.SetStart(vec((x0+u[0]*step,y0+u[1]*step)))
            t.SetEnd(vec((x0+v[0]*step,y0+v[1]*step)))
            uncovered=shape(t); uncovered.BooleanSubtract(allowed)
            return uncovered.Area()==0
    dist={s:0.}; parent={}; heap=[(math.dist(s,goal),0.,s)]""")
change("            ng=g+math.hypot(dx,dy)", "            if net=='MISO' and not referenced(u,v): continue\n            ng=g+math.hypot(dx,dy)")
'''
wrapper=wrapper.replace(anchor,changes+'\n'+anchor)
# Amend disposable test authoring in memory; actual resulting tests stay explicit.
checks=Path('/tmp/l5-r24-corrected-checks.py')
text=Path(__file__).with_name('l5_r24_checks.py').read_text()
assert text.count('        length = row["total_trace_mm"]')==1
text=text.replace('        length = row["total_trace_mm"]','        length: object = row["total_trace_mm"]')
assert text.count('        assert "R24" in findings and "MISO" in findings')==1
text=text.replace('        assert "R24" in findings and "MISO" in findings','        expected_net = "MISO_DRV" if change == "driver-cut" else "MISO"\n        assert expected_net in findings and "unconnected_items" in findings')
fast="""    quick=run('r24-native-focused', ['uv','run','--locked','python','-m','pytest',
        'tests/test_pcb_placement.py::test_output_corridor_uses_front_runs_and_local_ground_referenced_escapes',
        'tests/test_pcb_placement.py::test_native_r24_detects_either_open_or_a_parallel_copper_bypass',
        'tests/test_pcb_placement.py::test_each_new_signal_route_exposes_a_cut_without_changing_the_schematic[GPIO1]',
        'tests/test_pcb_placement.py::test_each_new_signal_route_exposes_a_cut_without_changing_the_schematic[GPIO2]',
        '-q','--junitxml='+str(OUT/'r24-focused-native.xml')],90)
    assert quick.returncode==0, 'Resolve focused native geometry/fault findings before the broader diagnostics'
"""
key="    result=run('ordinary-gate'"
assert text.count(key)==1
text=text.replace(key,fast+key)
checks.write_text(text)
key="checks = Path(os.environ['GITHUB_WORKSPACE'])/'workbench/l5_r24_checks.py'"
assert wrapper.count(key)==1
wrapper=wrapper.replace(key,"checks = Path('/tmp/l5-r24-corrected-checks.py')")
exec(compile(wrapper,'/tmp/l5-reference-corrected-wrapper.py','exec'),{'__name__':'__main__'})

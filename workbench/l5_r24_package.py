"""Package immutable read-only authoring data; no GitHub write or code execution."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

BASE='ff953c03c452f1572602b52aa62f42e80bfa9588'
ROOT=Path('/tmp/l5-stage')
OUT=Path('/tmp/l5-package')
OUT.mkdir(exist_ok=True)
ALLOW={
 'hardware/rev_a/bom.json','hardware/rev_a/check_schematic.py',
 'hardware/rev_a/kicad/digital.kicad_sch','hardware/rev_a/layout/rev_a.kicad_pcb',
 'tests/fixtures/rev_a_netlist.xml.gz','tests/test_pcb_placement.py','tests/test_spi_series_positions.py',
}
def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def digest(data): return hashlib.sha256(data).hexdigest()
def junit(data):
    root=ET.fromstring(data)
    cases=root.findall('.//testcase')
    return {'cases':len(cases),'failures':[c.attrib.get('name','') for c in cases if c.find('failure') is not None], 'errors':len(root.findall('.//error')),'skips':len(root.findall('.//skipped'))}

assert git('rev-parse','HEAD')==BASE
with zipfile.ZipFile('/tmp/l5-data.zip') as z:
    patch=z.read('partial-source.patch')
    before=junit(z.read('before.xml'))
    new_before=junit(z.read('r24-before.xml'))
    after=junit(z.read('after.xml'))
    native=junit(z.read('r24-native.xml'))
    drc=json.loads(z.read('afe-drc.json'))
    erc=json.loads(z.read('afe-erc.json'))
    ordinary=z.read('ordinary-gate.log').decode()
    logs={n:z.read(n) for n in ('ordinary-gate.log','r24-native-module.log','r24-new-requirements-before.log','author-console.log')}
assert before['errors']==new_before['errors']==after['errors']==native['errors']==0
assert len(before['failures'])==6 and len(new_before['failures'])==5
expected={f'test_each_spi_driver_has_its_own_two_terminal_series_boundary[{ref}]' for ref in ('R117','R118','R119','R120')}
assert set(after['failures'])==expected and after['skips']==0
assert native['failures']==[] and native['skips']==0
assert all(drc[k]==[] for k in ('violations','unconnected_items','schematic_parity'))
assert all(sheet.get('violations',[])==[] for sheet in erc['sheets'])
(OUT/'applied-source.patch').write_bytes(patch)
subprocess.run(['git','apply','--index','--whitespace=error-all',str(OUT/'applied-source.patch')],cwd=ROOT,check=True)
assert set(git('diff','--cached','--name-only').splitlines())==ALLOW
source_hashes={path:digest((ROOT/path).read_bytes()) for path in sorted(ALLOW)}
board_sha=source_hashes['hardware/rev_a/layout/rev_a.kicad_pcb']
observed_failed=re.findall(r'^FAILED\s+(\S+)\s+-',ordinary,re.M)
only_four=bool(observed_failed) and {name.rsplit('::',1)[-1] for name in observed_failed}==expected
print('ORDINARY_GATE_EXPECTED_FOUR_ONLY',only_four,observed_failed)
assert only_four, 'The ordinary gate has not yet demonstrated only the four missing auxiliary positions'

checkpoint={
 'stage':'L5 R24 source-only partial implementation; PR98 remains draft',
 'base_commit':BASE,'authoring_run':int(os.environ['L5_AUTHOR_RUN']),
 'authoring_artifact':int(os.environ['L5_AUTHOR_ARTIFACT']),
 'authoring_zip_sha256':digest(Path('/tmp/l5-data.zip').read_bytes()),
 'source_sha256':source_hashes,'before':before,'new_requirements_before':new_before,
 'focused_after':after,'native_placement_module':native,
 'native_drc':{k:0 for k in ('violations','unconnected_items','schematic_parity')},
 'native_erc_violations':0,'ordinary_gate':'FAILED: four missing AUX positions; not a pass',
 'ordinary_failure_names':observed_failed,
 'diagnostic_log_sha256':{name:digest(data) for name,data in logs.items()},
 'scope':{'implemented':['AFE R24'],'unimplemented':['AUX R117','AUX R118','AUX R119','AUX R120'],
          'population':'R24 DNP/open; UNSELECTED value/MPN is not orderable or a zero-ohm selection',
          'collateral_local_change':'R20 GPIO1 10k shunt moved to (64,35.9); GPIO1 and GPIO2 local routing changed; no R114 change',
          'reference_policy':'MISO load escape shifted locally; original 10mm/two-via/full-copper requirements retained; MISO_DRV added with front-only, no-via, <=3mm source geometry requirement',
          'physical_access':'Nominal placement only; populated assembly/process access is not qualified'},
 'release':{'fabrication':False,'purchase':False,'power':False,'external_acquisition':False,'body_connection':False},
}
cp=ROOT/'docs/checkpoints/20261008_l5_r24.json'
cp.write_text(json.dumps(checkpoint,indent=2)+'\n')
handoff=ROOT/'docs/LLM_HANDOFF.md'
text=handoff.read_text()
text=text.replace('# Continue PR98: L5 fail-first tests published; five-position CAD edit unfinished','# Continue PR98: R24 implemented as an open position; AUX R117-R120 remain')
a=text.index('## Unfinished PR98:')
b=text.index('## Current source and next practical task')
intro=f'''## Unfinished PR98: R24 is authored; four auxiliary positions remain

Live main was c2f93ee30eb47f80a7702603f20ed22e6cce86af (merged PR97).
Continue the existing draft PR98 / `work/l5-spi-series`; read back its live
head/tree and original review threads. Do not recreate the L4 decision or red tests.
The first hardware slice builds on `{BASE}`. It changes R24 coherently in the
AFE schematic, BOM, native PCB, connectivity contract and freshly exported fixture.

R24 is a genuine 0603 series boundary: U1.43 -> MISO_DRV -> R24.1, then
R24.2 -> MISO -> J1.5 and logical off-board MOD1.GPIO13. The latter is not a
new physical PCB pad or a direct MCU wire around the auxiliary buffers.
R24 remains DNP / OPEN. Value and MPN are `UNSELECTED`, non-orderable sentinels.
The zero BOM accounting placeholder is not a quotation or a fitted 0-ohm link.
Do not power or expect capture through the open position; fitting needs review.

The nominal R24 centre is (56.8,35.9). Making room moves the existing GPIO1
10k shunt R20 to (64,35.9), with local GPIO1/GPIO2 routing and R20 return changes.
GPIO1's longer inner-layer route is an explicit collateral change, not an SPI
performance claim. R114 on the AUX board is unchanged and remains receiver-side.
No other component choice, auxiliary copper, firmware, Q1 input hash or gate changes.

The reference check covers BOTH MISO_DRV and MISO, not only the old net name.
The source is front-only, without vias, with a 3mm authoring bound (not a noise
or impedance limit). The load's local escape rectangle moves with R24; its
10mm inner-route, two-via and full-copper GND-reference rules are retained.
Native tests cut either side and add a parallel copper bridge. Nominal courtyard
clearance and passing DRC are not populated-board soldering/access qualification.

See `checkpoints/20261008_l5_r24.json` for source hashes, fail-first and hosted
native diagnostics. Those are a bounded authoring run, NOT a green full project
gate: the four missing AUX R117-R120 tests still fail. Read exact published-head
CI and review separately. No native-integration or ESP32 result is inferred here.
Local downloads failed and the local execution service later failed to start;
pinned uv0.12.18 / KiCad9.0.2 worked in a separate read-only hosted workbench.
A staging artifact or authoring script is not the active engineering source.

NEXT: implement AUX R117-R120 in THIS draft PR. Keep R114 with J102.19 after
R120, preserve actual U102 driver identities, and apply coherent contract,
schematic/BOM, fresh fixture and PCB edits. Add both-side cut/bridge checks,
fresh refill/parity/DRC/reference checks and review. Do not xfail the four tests.
Three MCU-driven segments and DRDY/control/partial-rail requirements remain
separate. No purchase, construction/mating, fabrication, power, external-input
acquisition or person/animal connection is authorized. Keep the PR unmerged.

'''
text=text[:a]+intro+text[b:]
text=text.replace('These are proposed unused references, NOT implemented footprints or selected\nnonzero resistor values.', 'This was the L4 proposal; L5 now implements R24 in this draft only.\nAUX R117-R120 and all resistor-value/MPN selections remain unfinished.')
a=text.index('**Next source task:**')
b=text.index('B1-B3 now define',a)
text=text[:a]+'''**Next source task:** finish AUX R117-R120 in PR98 as specified above, not
another generic timing/rework plan. Preserve R24, its open-fit state and new
both-side/reference checks. Three MCU-driven stages are not fixed by positions
after U102, and no AUX J102 resistor is automatically DevKit source termination.
DRDY/control requirements remain separate. Q1 remains historical and unchanged.

'''+text[b:]
text=text.replace('AFE authored PCB:', 'AFE authored PCB on this unfinished draft:')
text=text.replace('60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6',board_sha)
handoff.write_text(text)

road=ROOT/'docs/REV_A_COMPLETION_ROADMAP.md'
text=road.read_text()
a=text.index('| Category |')
text='''# Rev A roadmap - PR98 has R24; four auxiliary series positions remain

L4/PR97 is merged; PR98 remains the unfinished implementation. R24 now has
coherent AFE schematic/BOM/PCB/contract/fresh-fixture source plus open-fit,
full-reference and native cut/bridge regressions. R24 is DNP/open and unselected,
not an approved fitted link. AUX R117-R120 remain missing; the full gate is red.
Read the current handoff, checkpoint, live head and independent review.
Moscow remains the planning destination; detailed prices/outreach stay paused.

'''+text[a:]
old='| Five-position implementation | 1-2 source turns | PR98 has six topology tests; the five required positions still fail as missing. No CAD/BOM changes | NEXT: finish coordinated schematic/BOM/PCB/contracts/fixtures in PR98, then native both-side faults/refill/parity/access review |'
new='| Five-position implementation | 1-2 source turns | R24 source and focused native checks exist; R117-R120 still missing; PR98 remains draft | NEXT: coordinated AUX edits, both-side fault/reference checks, full exact-head CI and review; physical access still needs qualification |'
assert old in text
text=text.replace(old,new)
text=text.replace('Next resume PR98 and implement AUX R117-R120 and AFE R24 as proposed in L4, not a further','Next resume PR98 and implement the remaining AUX R117-R120; preserve R24, not a further')
text=text.replace('Local Git network access, the locked Python environment and pinned KiCad were\nunavailable in the starting session. GitHub source publication did work.', 'Local execution failed, but pinned uv and KiCad authoring worked in an isolated\nread-only hosted workbench. See the R24 checkpoint; no full green gate is claimed.')
road.write_text(text)

for name,data in logs.items(): (OUT/name).write_bytes(data)
(OUT/'diagnostics.json').write_text(json.dumps(checkpoint,indent=2)+'\n')
subprocess.run(['git','add','--',*sorted(ALLOW),str(cp.relative_to(ROOT)), 'docs/LLM_HANDOFF.md','docs/REV_A_COMPLETION_ROADMAP.md'],cwd=ROOT,check=True)
expected=ALLOW|{'docs/checkpoints/20261008_l5_r24.json','docs/LLM_HANDOFF.md','docs/REV_A_COMPLETION_ROADMAP.md'}
assert set(git('diff','--cached','--name-only').splitlines())==expected
subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
tree=git('write-tree')
env=dict(os.environ,GIT_AUTHOR_NAME='utof',GIT_AUTHOR_EMAIL='38869938+utof@users.noreply.github.com',GIT_COMMITTER_NAME='utof',GIT_COMMITTER_EMAIL='38869938+utof@users.noreply.github.com')
message='feat(hardware): implement open R24 series position in unfinished PR98\n\nCoherent AFE source and native regressions only. AUX R117-R120 remain\nmissing and the full gate remains intentionally red. R24 is DNP/open,\nnot a fitted 0-ohm or selected damping resistor. No release gate changes.\n'
head=subprocess.check_output(['git','commit-tree',tree,'-p',BASE],input=message,text=True,cwd=ROOT,env=env).strip()
subprocess.run(['git','update-ref','refs/heads/l5-r24-packaged',head],cwd=ROOT,check=True)
subprocess.run(['git','bundle','create',str(OUT/'source.bundle'),'l5-r24-packaged','^'+BASE],cwd=ROOT,check=True)
manifest={'base':BASE,'head':head,'tree':tree,'changed_files':sorted(expected),'source_bundle_sha256':digest((OUT/'source.bundle').read_bytes()),'source_files':source_hashes,'hardware_release':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(OUT/'source.patch').write_bytes(subprocess.check_output(['git','diff','--binary',BASE,head],cwd=ROOT))
print('PACKAGE_IDENTITY',json.dumps(manifest),flush=True)

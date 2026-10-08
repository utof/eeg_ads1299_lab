"""Bounded R24 native authoring on an exact disposable worktree; no remote writes."""
from pathlib import Path
import collections
import gzip
import hashlib
import heapq
import json
import math
import os
import re
import shutil
import subprocess
import uuid
import pcbnew as p

BASE = Path('/tmp/l5-edit')
OUT = Path('/tmp/l5-out')
HEAD = 'ff953c03c452f1572602b52aa62f42e80bfa9588'
assert subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip() == HEAD
assert p.Version() == '9.0.2'
os.environ['KICAD_CONFIG_HOME'] = '/tmp/l5-kicad-config'
OUT.mkdir(exist_ok=True)

def uid(label):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'eeg-ads1299/l5/r24/'+label))

def topforms(text):
    depth = 0
    quoted = False
    escaped = False
    start = None
    result = []
    for i, c in enumerate(text):
        if quoted:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == '"': quoted = False
        elif c == '"': quoted = True
        elif c == '(':
            depth += 1
            if depth == 2: start = i
        elif c == ')':
            if depth == 2:
                assert start is not None
                result.append((start, i+1, text[start:i+1]))
            depth -= 1
    assert depth == 0 and not quoted
    return result

def one(text, head, needle):
    matches = [(a,b,f) for a,b,f in topforms(text) if re.match(r'\('+head+r'\s', f) and needle in f]
    assert len(matches) == 1, (head, needle, len(matches))
    return matches[0]

def prop(form, key, value):
    pattern = r'(\(property\s+"'+re.escape(key)+r'"\s+)"(?:\\.|[^"\\])*"'
    form, count = re.subn(pattern, lambda m:m[1]+json.dumps(value), form)
    assert count == 1, (key, count)
    return form

def fresh_uuids(form, prefix):
    return re.sub(r'(\(uuid\s+)"([^"]+)"', lambda m:m[1]+json.dumps(uid(prefix+'/'+m[2])), form)

def replace_once(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new)

def label(net, x, y, angle, name):
    just = 'right' if angle == 180 else 'left'
    return f'(global_label "{net}" (shape passive) (at {x:g} {y:g} {angle}) (effects (font (size 1 1)) (justify {just})) (uuid "{uid(name)}"))\n'

def wire(a, b, name):
    return f'(wire (pts (xy {a[0]:g} {a[1]:g}) (xy {b[0]:g} {b[1]:g})) (stroke (width 0) (type default)) (uuid "{uid(name)}"))\n'

# Re-run the original fail-first contract before any engineering changes.
red = subprocess.run(['uv','run','--locked','python','-m','pytest','tests/test_spi_series_positions.py','-q','--junitxml='+str(OUT/'before.xml')],capture_output=True,text=True,timeout=60)
(OUT/'before.log').write_text(red.stdout+red.stderr)
assert red.returncode == 1 and '5 failed, 1 passed' in red.stdout, red.stdout+red.stderr
print('BASELINE_RED', red.stdout[-1000:])

# Add one explicitly unselected, DNP/open passive position; not a resistor-value decision.
schpath = BASE/'hardware/rev_a/kicad/digital.kicad_sch'
sch = schpath.read_text()
a,b,driverlabel = one(sch, 'global_label', 'a85bb828-0345-5b20-9d28-4edee4b2acab')
sch = sch[:a]+driverlabel.replace('"MISO"','"MISO_DRV"',1)+sch[b:]
_,_,template = one(sch, 'symbol', '(property "Reference" "R20"')
part = fresh_uuids(template, 'schematic/R24')
old_uuid = re.search(r'\(uuid\s+"([^"]+)"',template)[1]
schuuid = uid('schematic/R24/'+old_uuid)
dx, dy = 312.42-157.48, 147.32-228.6
part = re.sub(r'\(at\s+(-?[0-9.]+)\s+(-?[0-9.]+)(\s+[^)]*)?\)',lambda m:f'(at {float(m[1])+dx:g} {float(m[2])+dy:g}{m[3] or ""})',part)
for key,value in {'Reference':'R24','Value':'UNSELECTED','ContractRef':'R_MISO_SERIES','MPN':'UNSELECTED','BOM_ID':'spi_series','Population':'dnp','Tolerance':''}.items():
    part = prop(part,key,value)
part = part.replace('(reference "R20")','(reference "R24")').replace('(dnp no)','(dnp yes)')
extra = '\n'+part+'\n'
extra += wire((312.42,139.7),(312.42,137.16),'R24/source-wire')
extra += label('MISO_DRV',312.42,137.16,0,'R24/source-label')
extra += wire((312.42,154.94),(312.42,157.48),'R24/load-wire')
extra += label('MISO',312.42,157.48,0,'R24/load-label')
extra += f'(text "R24: footprint only; DNP / OPEN. Value and MPN unselected. No first-power approval." (at 225 171 0) (effects (font (size 1 1)) (justify left)) (uuid "{uid("R24/note")}"))\n'
schpath.write_text(sch.rstrip()[:-1]+extra+')\n')

bompath = BASE/'hardware/rev_a/bom.json'
bom = json.loads(bompath.read_text())
assert not any(row['id']=='spi_series' for row in bom['line_items'])
bom['line_items'].append({'id':'spi_series','mpn':'UNSELECTED','manufacturer':'NOT_SELECTED','description':'R24 source-side SPI series footprint provision only; leave OPEN / DNP pending a reviewed value and MPN','package':'0603','references':['R_MISO_SERIES'],'quantity':1,'population':'dnp','planning_unit_usd':'0.00','source_ids':['TI_ADS_DS'],'evidence':'L4 topology decision only. UNSELECTED is a non-orderable sentinel, not a manufacturer part. Zero is an accounting placeholder for an absent component, not a quote or future component price. No zero-ohm or nonzero fit is approved.','spec':{}})
bom['excluded'].append('unselected SPI series components and tuning replacements; no cost estimate yet')
bompath.write_text(json.dumps(bom,indent=2)+'\n')
codepath = BASE/'hardware/rev_a/check_schematic.py'
code = codepath.read_text()
code = replace_once(code, '    "analog_feed": "Resistor_SMD:R_0603_1608Metric",', '    "analog_feed": "Resistor_SMD:R_0603_1608Metric",\n    "spi_series": "Resistor_SMD:R_0603_1608Metric",')
code = replace_once(code, '{"input_r", "bias_r", "straps", "bus_pulldowns", "analog_feed"}', '{"input_r", "bias_r", "straps", "bus_pulldowns", "analog_feed", "spi_series"}')
code = replace_once(code, '("MISO" if function == "DOUT" else function, "output", function)', '("MISO_DRV" if function == "DOUT" else function, "output", function)')
code = replace_once(code, '        "R_AVDD_FEED": ("VIN_5V_AFE", "AVDD"),', '        "R_AVDD_FEED": ("VIN_5V_AFE", "AVDD"),\n        "R_MISO_SERIES": ("MISO_DRV", "MISO"),')
codepath.write_text(code)

# Native schematic exports, not manual fixture modifications.
cmd = ['kicad-cli','sch','export','netlist','--format','kicadxml','--output',str(OUT/'afe.xml'),str(BASE/'hardware/rev_a/kicad/rev_a.kicad_sch')]
subprocess.run(cmd,check=True,capture_output=True,text=True,timeout=45)
(BASE/'tests/fixtures/rev_a_netlist.xml.gz').write_bytes(gzip.compress((OUT/'afe.xml').read_bytes(),mtime=0))
erc = subprocess.run(['kicad-cli','sch','erc','--severity-all','--exit-code-violations','--format','json','--output',str(OUT/'afe-erc.json'),str(BASE/'hardware/rev_a/kicad/rev_a.kicad_sch')],capture_output=True,text=True,timeout=45)
print('ERC',erc.returncode,erc.stdout,erc.stderr)
assert erc.returncode == 0

# Preserve original source forms except the named local edits and fresh zone fills.
boardpath = BASE/'hardware/rev_a/layout/rev_a.kicad_pcb'
original = boardpath.read_text()
assert hashlib.sha256(boardpath.read_bytes()).hexdigest() == '60097ff4acf8408d5a172930de74bcd36aa50a379dd30a831e4bc64d3841c8a6'
nets = {name:int(number) for number,name in re.findall(r'\(net\s+(\d+)\s+"([^"]+)"\)',original)}
new_code = max(nets.values())+1
nets['MISO_DRV'] = new_code
_,_,oldfp = one(original,'footprint','(property "Reference" "R20"')
newfp = fresh_uuids(oldfp,'footprint/R24')
newfp = re.sub(r'\(at\s+[^)]*\)', '(at 56.8 35.9)',newfp,count=1)
for key,value in {'Reference':'R24','Value':'UNSELECTED','ContractRef':'R_MISO_SERIES','MPN':'UNSELECTED','BOM_ID':'spi_series','Population':'dnp','Tolerance':''}.items():
    newfp = prop(newfp,key,value)
newfp = newfp.replace('(attr smd)','(attr smd dnp)')
newfp = re.sub(r'(\(path\s+")([^"\n]+)(")',lambda m:m[1]+m[2].rsplit('/',1)[0]+'/'+schuuid+m[3],newfp)
for n,net in [('1','MISO_DRV'),('2','MISO')]:
    a,b,pad = one(newfp,'pad','(pad "'+n+'"')
    pad,count = re.subn(r'\(net\s+\d+\s+"[^"]+"\)',f'(net {nets[net]} "{net}")',pad)
    assert count==1
    newfp = newfp[:a]+pad+newfp[b:]
a,b,ic = one(original,'footprint','(property "Reference" "U1"')
pa,pb,pad = one(ic,'pad','(pad "43"')
pad = re.sub(r'\(net\s+\d+\s+"MISO"\)',f'(net {new_code} "MISO_DRV")',pad)
ic = ic[:pa]+pad+ic[pb:]
text = original[:a]+ic+original[b:]
a,b,oldfp_current = one(text,'footprint','(property "Reference" "R20"')
moved = re.sub(r'\(at\s+[^)]*\)','(at 64 35.9)',oldfp_current,count=1)
text = text[:a]+moved+text[b:]
removed = {
'd62dab04-82cb-5c0b-9d6f-c901c9d73358','ffe208ae-cbe0-5a57-b524-15872f133e0e',
'a2581856-2729-5017-a58c-2f1907eca900','66226eab-fa37-509f-ac84-225cfde1de5e','b634b695-1fda-5ee9-a8e0-4b95da610085','ac44305d-37c6-52b6-bfd7-d78f6c407686',
'31d63b38-6d8a-5677-94fe-df0cf3083830','b85a2afd-af02-524d-8eb0-e389f9b833de','6fddc1d8-5fdd-5af1-89a2-ab3541f40710',
'2cd6645a-3169-55d4-b8f1-11a0a91ef3ac','76056fc3-9264-5f54-ae5b-7b5cdab3f032','dbf10413-cc72-52d0-a0d7-6b1aa55e77ab'}
found = set()
for a,b,form in reversed(topforms(text)):
    m = re.search(r'\(uuid\s+"([^"]+)"',form)
    if m and m[1] in removed:
        found.add(m[1]); text = text[:a]+text[b:]
assert found == removed
text = text.rstrip()[:-1]+f'\n(net {new_code} "MISO_DRV")\n'+newfp+'\n)\n'
boardpath.write_text(text)
b = p.LoadBoard(str(boardpath))
changed_ids = {re.search(r'\(uuid\s+"([^"]+)"',f)[1] for f in (ic,moved,newfp)}
netcodes = {n.GetNetname():n.GetNetCode() for n in b.GetNetInfo().NetsByNetcode().values()}

def vec(pt): return p.VECTOR2I(p.FromMM(pt[0]),p.FromMM(pt[1]))
def point(v): return (p.ToMM(v.x),p.ToMM(v.y))
def track(net,layer,a,z,name,width=.15,identity=None):
    t=p.PCB_TRACK(b); t.SetStart(vec(a)); t.SetEnd(vec(z)); t.SetLayer(layer); t.SetWidth(p.FromMM(width)); t.SetNetCode(netcodes[net]); t.m_Uuid=p.KIID(identity or uid(name)); b.Add(t); changed_ids.add(t.m_Uuid.AsString()); return t

def chain(net,layer,pts,name,width=.15,first_identity=None):
    for i,(a,z) in enumerate(zip(pts,pts[1:])):
        if a!=z: track(net,layer,a,z,f'{name}/{i}',width,first_identity if i==0 else None)

def via(net,at,name):
    v=p.PCB_VIA(b); v.SetPosition(vec(at)); v.SetWidth(p.FromMM(.6)); v.SetDrill(p.FromMM(.3)); v.SetViaType(p.VIATYPE_THROUGH); v.SetLayerPair(p.F_Cu,p.B_Cu); v.SetNetCode(netcodes[net]); v.m_Uuid=p.KIID(uid(name)); b.Add(v); changed_ids.add(v.m_Uuid.AsString()); return v

chain('MISO_DRV',p.F_Cu,[(53.6625,35.75),(55.825,35.75),(55.975,35.9)],'R24/source')
chain('MISO',p.F_Cu,[(57.625,35.9),(58.55,35.9)],'R24/load')
via('MISO',(58.55,35.9),'R24/load-via')
chain('GPIO2',p.F_Cu,[(55,35.25),(55.15,35.1),(58.675,35.1),(59.475,34.3)],'GPIO2/local')
chain('GPIO1',p.F_Cu,[(53.6625,36.25),(54.7,36.25),(54.95,36.5),(54.95,36.6)],'GPIO1/source',first_identity='31d63b38-6d8a-5677-94fe-df0cf3083830')
via('GPIO1',(54.95,36.6),'GPIO1/source-via')
via('GPIO1',(62.3,35.9),'GPIO1/load-via')
chain('GPIO1',p.F_Cu,[(62.3,35.9),(63.175,35.9)],'GPIO1/load')
chain('GND',p.F_Cu,[(64.825,35.9),(65.8,35.9)],'R20/return',.25)
via('GND',(65.8,35.9),'R20/return-via')

# A bounded authoring-only grid for two short local inner-layer routes.
# It does not replace the exact native DRC/reference tests below.
def route(net,start,finish,bounds,name):
    step=.05; x0,x1,y0,y1=bounds
    nx=round((x1-x0)/step)+1; ny=round((y1-y0)/step)+1
    blocked=bytearray(nx*ny)
    clearance=.175; trace_radius=.075; slack=.025
    def mark(ax,ay,bx,by,r,box=False):
        ix0=max(0,math.floor((min(ax,bx)-r-x0)/step)); ix1=min(nx-1,math.ceil((max(ax,bx)+r-x0)/step))
        iy0=max(0,math.floor((min(ay,by)-r-y0)/step)); iy1=min(ny-1,math.ceil((max(ay,by)+r-y0)/step))
        dx=bx-ax; dy=by-ay; den=dx*dx+dy*dy
        for j in range(iy0,iy1+1):
            yy=y0+j*step
            for i in range(ix0,ix1+1):
                xx=x0+i*step
                if box:
                    d2=max(ax-xx,0,xx-bx)**2+max(ay-yy,0,yy-by)**2
                else:
                    u=0 if den==0 else max(0,min(1,((xx-ax)*dx+(yy-ay)*dy)/den))
                    d2=(xx-ax-u*dx)**2+(yy-ay-u*dy)**2
                if d2 <= r*r: blocked[j*nx+i]=1
    for t in b.GetTracks():
        if t.GetNetname()==net or not t.IsOnLayer(p.In2_Cu): continue
        if t.Type()==p.PCB_VIA_T:
            a=point(t.GetPosition()); mark(*a,*a,p.ToMM(t.GetWidth(p.In2_Cu))/2+clearance+trace_radius+slack)
        elif t.Type()==p.PCB_TRACE_T:
            mark(*point(t.GetStart()),*point(t.GetEnd()),p.ToMM(t.GetWidth())/2+clearance+trace_radius+slack)
        else:
            bb=t.GetBoundingBox(); mark(*point(bb.GetOrigin()),*point(bb.GetEnd()),clearance+trace_radius+slack,True)
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname()==net or not pad.IsOnLayer(p.In2_Cu): continue
            bb=pad.GetBoundingBox(); mark(*point(bb.GetOrigin()),*point(bb.GetEnd()),clearance+trace_radius+slack,True)
    def node(pt): return (round((pt[0]-x0)/step),round((pt[1]-y0)/step))
    s=node(start); goal=node(finish)
    assert not blocked[s[1]*nx+s[0]] and not blocked[goal[1]*nx+goal[0]], ('blocked endpoint',net,s,goal)
    dist={s:0.}; parent={}; heap=[(math.dist(s,goal),0.,s)]
    moves=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    while heap:
        _,g,u=heapq.heappop(heap)
        if g!=dist.get(u): continue
        if u==goal: break
        for dx,dy in moves:
            v=(u[0]+dx,u[1]+dy)
            if not (0<=v[0]<nx and 0<=v[1]<ny) or blocked[v[1]*nx+v[0]]: continue
            if dx and dy and (blocked[u[1]*nx+v[0]] or blocked[v[1]*nx+u[0]]): continue
            ng=g+math.hypot(dx,dy)
            if ng < dist.get(v,math.inf):
                dist[v]=ng; parent[v]=u; heapq.heappush(heap,(ng+math.dist(v,goal),ng,v))
    assert goal in dist, ('no bounded inner route',net,bounds)
    path=[goal]
    while path[-1]!=s: path.append(parent[path[-1]])
    path.reverse(); reduced=[path[0]]
    for i in range(1,len(path)-1):
        a,u,v=path[i-1],path[i],path[i+1]
        if (u[0]-a[0],u[1]-a[1]) != (v[0]-u[0],v[1]-u[1]): reduced.append(u)
    reduced.append(path[-1])
    pts=[(round(x0+i*step,6),round(y0+j*step,6)) for i,j in reduced]
    pts[0]=start; pts[-1]=finish
    chain(net,p.In2_Cu,pts,name)
    length=sum(math.dist(a,z) for a,z in zip(pts,pts[1:]))
    print('LOCAL_ROUTE',net,length,pts)
    return length

assert any(t.Type()==p.PCB_VIA_T and t.GetNetname()=='MISO' and math.dist(point(t.GetPosition()),(55.1,29.5))<1e-5 for t in b.GetTracks())
miso_length=route('MISO',(58.55,35.9),(55.1,29.5),(54.8,58.7,29.5,36.5),'R24/inner')
assert miso_length <= 10
route('GPIO1',(54.95,36.6),(62.3,35.9),(54.5,64,34.8,38.5),'GPIO1/inner')
b.BuildConnectivity()
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(OUT/'native-r24.kicad_pcb'),b)

# The native writer renumbers nets. Transplant only allowed forms, restoring
# canonical numeric identities; all other old source forms remain byte-identical.
native=(OUT/'native-r24.kicad_pcb').read_text()
saved_nets={int(n):s for n,s in re.findall(r'\(net\s+(\d+)\s+"([^"]+)"\)',native)}
def normalize(form):
    return re.sub(r'\(net\s+(\d+)(?=[\s)])',lambda m:'(net '+str(nets.get(saved_nets[int(m[1])],0)) if int(m[1]) in saved_nets else m[0],form)
native_forms=topforms(native)
replacements={}
for _,_,form in native_forms:
    m=re.search(r'\(uuid\s+"([^"]+)"',form)
    if m and (m[1] in changed_ids or form.startswith('(zone')): replacements[m[1]]=normalize(form)
result=original
seen=set()
for a,z,form in reversed(topforms(original)):
    m=re.search(r'\(uuid\s+"([^"]+)"',form)
    if not m: continue
    identity=m[1]
    if identity in replacements:
        result=result[:a]+replacements[identity]+result[z:]; seen.add(identity)
    elif identity in removed: result=result[:a]+result[z:]
extras=[f for identity,f in replacements.items() if identity not in seen]
result=result.rstrip()[:-1]+f'\n(net {new_code} "MISO_DRV")\n'+'\n'.join(extras)+'\n)\n'
boardpath.write_text(result)
# Assert untouched top-level UUID forms retained exact bytes, not just connectivity.
orig_by_id={re.search(r'\(uuid\s+"([^"]+)"',f)[1]:f for _,_,f in topforms(original) if re.search(r'\(uuid\s+"([^"]+)"',f)}
new_by_id={re.search(r'\(uuid\s+"([^"]+)"',f)[1]:f for _,_,f in topforms(result) if re.search(r'\(uuid\s+"([^"]+)"',f)}
protected=0
for identity,form in orig_by_id.items():
    if identity not in removed and identity not in changed_ids and not form.startswith('(zone'):
        assert new_by_id[identity]==form, identity; protected+=1
print('UNCHANGED_NATIVE_FORMS',protected)

# Explicitly move only MISO's local escape region to its new source location.
# Keep DRDY's existing region, the 10mm limit, two-via limit and full-copper check.
testpath=BASE/'tests/test_pcb_placement.py'
test=testpath.read_text()
test=replace_once(test,'    bounds_ok = all(50 <= p.ToMM(v.x) <= 56 and 29.5 <= p.ToMM(v.y) <= 36.5', '    xmin, xmax = (54.8, 58.7) if name == "MISO" else (50, 56)\n    bounds_ok = all(xmin <= p.ToMM(v.x) <= xmax and 29.5 <= p.ToMM(v.y) <= 36.5')
testpath.write_text(test)

# Native fresh refill plus full-severity schematic/PCB parity in adjacent CAD copy.
cad=OUT/'afe-cad'
shutil.copytree(BASE/'hardware/rev_a/kicad',cad)
shutil.copytree(BASE/'hardware/rev_a/footprints',OUT/'footprints')
shutil.copyfile(boardpath,cad/'rev_a.kicad_pcb')
fresh=p.LoadBoard(str(cad/'rev_a.kicad_pcb')); p.ZONE_FILLER(fresh).Fill(fresh.Zones()); p.SaveBoard(str(cad/'rev_a.kicad_pcb'),fresh)
drc=subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--severity-all','--exit-code-violations','--format','json','--output',str(OUT/'afe-drc.json'),str(cad/'rev_a.kicad_pcb')],capture_output=True,text=True,timeout=60)
print('DRC_EXIT',drc.returncode,drc.stdout,drc.stderr)
report=json.loads((OUT/'afe-drc.json').read_text())
for key in ('violations','schematic_parity','unconnected_items'):
    print('NATIVE_FINDINGS',key,len(report[key]),json.dumps(report[key],separators=(',',':')))

# Retain an exact source patch even on a diagnostic failure; never publish/merge here.
subprocess.run(['uv','run','--locked','ruff','format','hardware/rev_a/check_schematic.py','tests/test_pcb_placement.py'],check=True,capture_output=True,text=True,timeout=45)
(OUT/'source.patch').write_bytes(subprocess.check_output(['git','diff','--binary',HEAD]))
print('SOURCE_DIFF',subprocess.check_output(['git','diff','--stat'],text=True))
assert drc.returncode == 0, 'Native R24 candidate still has findings; not an accepted PCB'
focused=subprocess.run(['uv','run','--locked','python','-m','pytest','tests/test_spi_series_positions.py','-q','--junitxml='+str(OUT/'after.xml')],capture_output=True,text=True,timeout=60)
(OUT/'after.log').write_text(focused.stdout+focused.stderr)
print('FOCUSED_AFTER',focused.stdout,focused.stderr)
assert focused.returncode==1 and '4 failed, 2 passed' in focused.stdout
print('R24_CANDIDATE_NATIVE_PASS_NO_RELEASE',hashlib.sha256(boardpath.read_bytes()).hexdigest())

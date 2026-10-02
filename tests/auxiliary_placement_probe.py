"""Pinned-system-Python probe text. No pcbnew import in the ordinary environment."""

SCRIPT = r"""
import json,math,os,sys
from pathlib import Path
import pcbnew as p
assert p.Version() == '9.0.2'
cad=Path(sys.argv[1]);mode=sys.argv[2]
path=cad/'auxiliary.kicad_pcb'
b=p.LoadBoard(str(path));fs={f.GetReference():f for f in b.GetFootprints()}
def move(ref,dx,dy): fs[ref].Move(p.VECTOR2I(p.FromMM(dx),p.FromMM(dy)))
if mode=='far-bypass':move('C110',0,-6)
elif mode=='host-in-target':move('J103',30,0)
elif mode=='blocked-mating':move('R116',6,7)
elif mode=='mount-over-pad':move('H2',-57,3)
elif mode in ('mount-into-access','mount-touch-access','mount-near-access'):
    x={'mount-into-access':85,'mount-touch-access':86,'mount-near-access':86.25}[mode]
    fs['H4'].SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(70)))
elif mode=='mount-benign':move('H4',0,-.25)
elif mode=='wrong-sense':
    next(z for z in fs['J104'].Pads() if z.GetNumber()=='3').SetNet(b.FindNet('AFE_DVDD'))
elif mode=='outer-only-barrier':
    next(iter(b.Zones())).SetLayerSet(p.LSET.AllCuMask(2))
elif mode=='weaken-keepout':
    next(iter(b.Zones())).SetDoNotAllowTracks(False)
elif mode=='mirrored-buffer':fs['U102'].SetOrientationDegrees(270)
elif mode=='benign':move('R116',.2,0)
else:assert mode=='canonical'
if mode!='canonical':p.SaveBoard(str(path),b)
def pos(x):return [x.GetPosition().x/1e6,x.GetPosition().y/1e6]
def bounds(box):return [box.GetX()/1e6,box.GetY()/1e6,box.GetRight()/1e6,box.GetBottom()/1e6]
def dist(a,c):return math.hypot(a[0]-c[0],a[1]-c[1])
def gap(a,c):return math.hypot(max(a[0]-c[2],c[0]-a[2],0),max(a[1]-c[3],c[1]-a[3],0))
def pad(ref,n):return next(x for x in fs[ref].Pads() if x.GetNumber()==str(n))
contract=json.loads((cad/'contract.json').read_text())
assert set(fs)=={r['reference'] for r in contract['parts']}|{'H1','H2','H3','H4'},'inventory'
assert len(list(b.GetTracks()))==0,'placement is not routed'
assert b.GetCopperLayerCount()==4,'four-layer low-EMI planning target'
assert b.GetDesignSettings().GetBoardThickness()==p.FromMM(1.6)
outline=[g for g in b.GetDrawings() if g.GetLayer()==p.Edge_Cuts]
assert len(outline)==1 and outline[0].GetShape()==p.SHAPE_T_RECT
assert outline[0].GetStart()==p.VECTOR2I(0,0) and outline[0].GetEnd()==p.VECTOR2I(p.FromMM(90),p.FromMM(75))
libraries=Path(os.environ['KICAD9_FOOTPRINT_DIR']);courts={}
for row in contract['parts']:
    ref=row['reference'];f=fs[ref]
    assert f.GetValue()==row['value'] and f.GetFPID().GetLibItemName()==row['footprint'].split(':')[1]
    assert f.IsExcludedFromBOM()==(not row['in_bom']) and not f.IsDNP()
    assert f.GetLayer()==p.F_Cu,'front-side only'
    pads={z.GetNumber():z for z in f.Pads()};assert set(pads)==set(row['pins'])
    lib,name=row['footprint'].split(':')
    original=p.FootprintLoad(str((cad if lib=='Aux_Lands' else libraries)/(lib+'.pretty')),name)
    assert original is not None
    original.SetOrientation(f.GetOrientation());original.SetPosition(f.GetPosition())
    for source in original.Pads():
        actual=pads[source.GetNumber()]
        assert (actual.GetPosition()==source.GetPosition() and actual.GetSize()==source.GetSize()
                and actual.GetShape()==source.GetShape() and actual.GetDrillSize()==source.GetDrillSize()
                and actual.GetAttribute()==source.GetAttribute() and list(actual.GetLayerSet().Seq())==list(source.GetLayerSet().Seq())),ref+' land drift'
    for n,expected in row['pins'].items():
        net=pads[n].GetNetname()
        assert (net==expected['net']) if expected['net'] else net.startswith('unconnected-'),ref+' net mismatch'
    f.BuildCourtyardCaches();court=f.GetCourtyard(p.F_Cu)
    assert court.OutlineCount()==1,ref+' courtyard'
    r=bounds(court.BBox());assert .5<=r[0]<r[2]<=89.5 and .5<=r[1]<r[3]<=74.5,ref+' edge'
    courts[ref]=r
# Explicit domain guard does not rely on name matching in custom-rule execution alone.
host=[];target=[]
for row in contract['parts']:
    for z in fs[row['reference']].Pads():
        r=bounds(z.GetBoundingBox())
        if z.GetNetname().startswith('HOST_'):
            host.append(r);assert r[2]<=20.5,'host side'
        else:
            target.append(r);assert r[0]>=23.5,'target side'
separation=min(gap(a,c) for a in host for c in target)
assert separation>=3.0,'HOST/TARGET gap'
zones=list(b.Zones());assert len(zones)==1
z=zones[0];assert z.GetIsRuleArea() and list(z.GetLayerSet().Seq())==list(p.LSET.AllCuMask(4).Seq()),'barrier layers'
assert z.GetZoneName()=='HOST_TARGET_NO_COPPER'
assert all((z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowPads(),z.GetDoNotAllowCopperPour())),'keepout policy'
assert not z.GetDoNotAllowFootprints()
assert z.Outline().OutlineCount()==1 and z.Outline().VertexCount()==4
assert bounds(z.Outline().BBox())==[20.5,0.,23.5,75.],'barrier bounds'
# Fifteen individual supply bypasses; distances are pad-center placement budgets,
# not routed-loop inductance or an actual-plane return qualification.
pairs=[('C101','U101',1),('C102','U101',8),('C103','U102',1),('C104','U102',14),
       ('C105','U103',1),('C106','U103',14),('C107','U104',1),('C108','U104',14),
       ('C109','U105',2),('C110','U106',2),('C111','U107',2),('C112','U108',2),
       ('C113','U109',5),('C114','U110',5),('C115','U111',8)]
measured={}
for cap,ic,n in pairs:
    a=pad(cap,1);v=pad(ic,n);assert a.GetNetname()==v.GetNetname()
    d=dist(pos(a),pos(v));assert d<=2.5,cap+' bypass distance';measured[cap]=d
# Native copper/pads, not component centers, establish the mechanical fastener budget.
hole_margins={};mount_areas={}
for ref in ('H1','H2','H3','H4'):
    f=fs[ref];ps=list(f.Pads());assert len(ps)==1
    z=ps[0];assert z.GetAttribute()==p.PAD_ATTRIB_NPTH and z.GetDrillSize()==p.VECTOR2I(p.FromMM(2.7),p.FromMM(2.7))
    assert f.GetAttributes() & p.FP_BOARD_ONLY and f.IsExcludedFromBOM()
    X,Y=pos(z);area=[X-3,Y-3,X+3,Y+3];mount_areas[ref]=area
    assert area[0]>=.5 and area[1]>=.5 and area[2]<=89.5 and area[3]<=74.5
    distances=[gap(area,bounds(a.GetBoundingBox())) for r in contract['parts'] for a in fs[r['reference']].Pads()]
    assert min(distances)>.25,'mount copper allocation';hole_margins[ref]=min(distances)
# Termination and plug/tool envelopes are declared allocations, not vendor maximums.
areas={'J101':[26,0,78.5,12],'J102':[26,61.5,83,75],'J103':[0,29,14.5,35],
       'J104':[27,50,45.5,58]}
mount_access_gaps={}
for ref,area in areas.items():
    for mount,reserved in mount_areas.items():
        d=gap(area,reserved)
        assert d>=.5,ref+' mount/termination clearance to '+mount
        mount_access_gaps[ref+'/'+mount]=d
    for other,court in courts.items():
        if other!=ref: assert gap(area,court)>0,ref+' mating/termination envelope'
for ref in ('U102','U103','U104'):
    assert pad(ref,14).GetPosition().y < pad(ref,1).GetPosition().y,'AFE/MCU buffer orientation'
# Sense loading resistors remain close to each monitored input; separate rail nets stay separate.
for r,u in [('R102','U105'),('R104','U106'),('R106','U107'),('R108','U108')]:
    assert dist(pos(pad(r,1)),pos(pad(u,1)))<=3.,r+' sense locality'
assert pad('J104',2).GetNetCode()!=pad('J104',3).GetNetCode(),'premature feed/sense join'
print(json.dumps({'mode':mode,'circuit_footprints':48,'mechanical_NPTH':4,'all_pads':sum(len(list(f.Pads())) for f in fs.values()),
    'host_target_pad_bbox_gap_mm':separation,'bypass_supply_pad_centers_mm':measured,
    'hole_reserved_box_to_pad_gap_mm':hole_margins,'mating_allocations_mm':areas,
    'mount_allocations_mm':mount_areas,'mount_to_termination_gaps_mm':mount_access_gaps,
    'minimum_mount_to_termination_gap_mm':min(mount_access_gaps.values()),'physical_qualification':False},indent=2))
"""

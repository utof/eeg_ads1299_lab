"""Native P2 geometry probe. Runs only in the pinned KiCad Python subprocess."""

SCRIPT = r"""
import heapq,json,math,sys
from pathlib import Path
import pcbnew as p
assert p.Version()=='9.0.2'
path,mode=sys.argv[1:];b=p.LoadBoard(path)
fs={f.GetReference():f for f in b.GetFootprints()}
def pad(r,n):return next(x for x in fs[r].Pads() if x.GetNumber()==str(n))
def xy(x):return (x.GetPosition().x,x.GetPosition().y)
def coord(x):return (x.x,x.y)
def bb(x):
    box=x.BBox();return [box.GetX()/1e6,box.GetY()/1e6,box.GetRight()/1e6,box.GetBottom()/1e6]
def short_path(net,start,end):
    edges={}
    for t in b.GetTracks():
        if t.Type()!=p.PCB_TRACE_T or t.GetLayer()!=p.F_Cu or t.GetNetname()!=net:continue
        a,c=coord(t.GetStart()),coord(t.GetEnd());d=t.GetLength()/1e6
        edges.setdefault(a,[]).append((c,d));edges.setdefault(c,[]).append((a,d))
    queue=[(0.,start)];seen=set()
    while queue:
        cost,n=heapq.heappop(queue)
        if n==end:return cost
        if n in seen:continue
        seen.add(n)
        for c,d in edges.get(n,[]):heapq.heappush(queue,(cost+d,c))
    return math.inf
pairs=[('C101','U101',1),('C102','U101',8),('C103','U102',1),('C104','U102',14),
       ('C105','U103',1),('C106','U103',14),('C107','U104',1),('C108','U104',14),
       ('C109','U105',2),('C110','U106',2),('C111','U107',2),('C112','U108',2),
       ('C113','U109',5),('C114','U110',5),('C115','U111',8)]
if mode.startswith('bypass-'):
    ref=mode.removeprefix('bypass-');cap,ic,pin=next(row for row in pairs if row[0]==ref)
    a,c=pad(cap,1),pad(ic,pin);assert a.GetNetname()==c.GetNetname()
    length=short_path(a.GetNetname(),xy(a),xy(c))
    assert length<=2.5,cap+' missing or excessive local bypass path'
    print(json.dumps({'capacitor':cap,'ic':ic,'pin':pin,'front_path_mm':length}))
else:
    assert mode=='grounds'
    zones=[z for z in b.Zones() if not z.GetIsRuleArea()]
    assert len(zones)==2,'two separate ground reference zones required'
    bynet={z.GetNetname():z for z in zones};assert set(bynet)=={'HOST_GND','TARGET_GND'}
    rows={}
    for net,z in bynet.items():
        assert list(z.GetLayerSet().Seq())==[p.In1_Cu],'reference layer'
        filled=z.GetFilledPolysList(p.In1_Cu)
        assert filled.OutlineCount()==1,net+' must be one actually filled region'
        bounds=bb(filled)
        assert bounds[2]<=20.5 if net=='HOST_GND' else bounds[0]>=23.5,'filled ground crosses barrier'
        assert filled.Area()>p.FromMM(100)*p.FromMM(1),'ground region area'
        vias=[v for v in b.GetTracks() if v.Type()==p.PCB_VIA_T and v.GetNetname()==net]
        # Each SMD ground pad has a short actual F-track path to a same-net
        # through via that enters the real refilled region. No cap body is copper.
        distances={}
        for ref,f in fs.items():
            for a in f.Pads():
                if a.GetNetname()!=net or a.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
                choices=[short_path(net,xy(a),xy(v)) for v in vias if filled.Contains(v.GetPosition())]
                d=min(choices,default=math.inf)
                assert d<=2.5,ref+'.'+a.GetNumber()+' missing or excessive ground access'
                distances[ref+'.'+a.GetNumber()]=d
        for f in fs.values():
            for a in f.Pads():
                if a.GetNetname()==net and a.GetAttribute()==p.PAD_ATTRIB_PTH:
                    # Thermals can be clear at the drill center. Native DRC proves
                    # actual PTH-to-plane connectivity separately.
                    assert z.Outline().Contains(a.GetPosition()),'PTH outside reference domain'
        rows[net]={'filled_area_mm2':filled.Area()/1e12,'filled_regions':1,'SMD_ground_access_mm':distances}
    for tr in b.GetTracks():
        assert tr.GetNetname() in {'HOST_GND','TARGET_GND','HOST_3V3','MCU_3V3','AFE_DVDD'},'P2 scope'
        if tr.Type()==p.PCB_TRACE_T:assert tr.GetLayer()==p.F_Cu,'no hidden inner signal route'
    print(json.dumps(rows,indent=2))
"""

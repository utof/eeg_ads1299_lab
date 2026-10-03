"""Native P3 routing and explicit reference-screen limits; not an EM solver."""

SCRIPT = r"""
import json,math,sys
from collections import Counter,defaultdict
import pcbnew as p
assert p.Version()=='9.0.2'
b=p.LoadBoard(sys.argv[1]);mode=sys.argv[2]
planes={z.GetNetname():z for z in b.Zones() if not z.GetIsRuleArea()}
assert set(planes)=={'HOST_GND','TARGET_GND'},'reference domains'
for z in planes.values():
    assert list(z.GetLayerSet().Seq())==[p.In1_Cu],'reference layer'
    assert z.GetFilledPolysList(p.In1_Cu).OutlineCount()==1,'split reference'
tracks=list(b.GetTracks());pads=[a for f in b.GetFootprints() for a in f.Pads()]
netnames={t.GetNetname() for t in tracks if t.GetNetname() not in planes}
assert netnames,'missing routed signals'
# Same-net through contacts inevitably have a clearance hole in the ground.
# This is an EXPLICIT bounded screen exclusion, not permission for arbitrary voids:
# native copper silhouette +0.35mm, allowing existing 0.25mm zone clearance and
# its 0.20mm minimum-width fill shaping. It is not a measured HF field boundary.
exclusions={}
for net in netnames:
    poly=p.SHAPE_POLY_SET()
    for a in pads:
        if a.GetNetname()==net and a.GetAttribute()==p.PAD_ATTRIB_PTH:
            a.TransformShapeToPolygon(poly,p.In1_Cu,p.FromMM(.35),p.FromMM(.002),p.ERROR_OUTSIDE)
    for t in tracks:
        if t.GetNetname()==net and t.Type()==p.PCB_VIA_T:
            t.TransformShapeToPolygon(poly,p.In1_Cu,p.FromMM(.35),p.FromMM(.002),p.ERROR_OUTSIDE)
    exclusions[net]=poly

def uncovered(t,width):
    a,c=t.GetStart(),t.GetEnd();d=math.hypot(c.x-a.x,c.y-a.y)
    assert d>0,'zero length segment'
    nx,ny=-(c.y-a.y)*width/2/d,(c.x-a.x)*width/2/d
    q=p.SHAPE_POLY_SET();q.NewOutline()
    for x,y in [(a.x+nx,a.y+ny),(c.x+nx,c.y+ny),(c.x-nx,c.y-ny),(a.x-nx,a.y-ny)]:
        q.Append(round(x),round(y))
    net=t.GetNetname();ground='HOST_GND' if net.startswith('HOST_') else 'TARGET_GND'
    q.BooleanSubtract(exclusions[net]);q.BooleanSubtract(planes[ground].GetFilledPolysList(p.In1_Cu))
    return q.Area()/1e12

rows=defaultdict(lambda:{'front_length_mm':0.,'inner_length_mm':0.,'through_vias':0})
edge_gaps=[]
for t in tracks:
    net=t.GetNetname()
    if t.Type()==p.PCB_VIA_T:
        assert t.TopLayer()==p.F_Cu and t.BottomLayer()==p.B_Cu,'through via pair'
        assert t.GetWidth(p.F_Cu)==p.FromMM(.6) and t.GetDrillValue()==p.FromMM(.3),'via geometry'
        if net in planes:continue
        rows[net]['through_vias']+=1
        continue
    assert t.Type()==p.PCB_TRACE_T,'unsupported copper item'
    assert t.GetLayer() in (p.F_Cu,p.In2_Cu),'signal on unreviewed layer'
    assert t.GetWidth() in (p.FromMM(.2),p.FromMM(.3),p.FromMM(.6)),'track width'
    if net in planes:continue
    rows[net]['front_length_mm' if t.GetLayer()==p.F_Cu else 'inner_length_mm']+=t.GetLength()/1e6
    # A continuous central 0.10mm reference spine is a NEW geometric screen for
    # the global routes, not the stronger existing 0.20mm P2 bypass requirement.
    # Full-width uncovered edges are ALWAYS inventoried below, never called zero.
    spine=uncovered(t,p.FromMM(.10))
    assert spine<=1e-6,'P3 central reference spine gap: '+t.m_Uuid.AsString()
    full=uncovered(t,t.GetWidth())
    if full>1e-6:
        edge_gaps.append({'track':t.m_Uuid.AsString(),'net':net,'layer':b.GetLayerName(t.GetLayer()),
                          'uncovered_full_width_area_mm2':full})
assert mode in ('reference','inventory')
print(json.dumps({'nets':dict(sorted(rows.items())),
 'counts':{'segments':sum(t.Type()==p.PCB_TRACE_T for t in tracks),
           'vias':sum(t.Type()==p.PCB_VIA_T for t in tracks)},
 'reference_spine_width_mm':.10,'same_net_antipad_screen_expansion_mm':.35,
 'full_width_edge_gaps_pending_review':edge_gaps,
 'full_width_ground_coverage_qualified':False,
 'EMC_impedance_timing_or_physical_qualification':False},indent=2))
"""

MUTATE = r"""
import sys,pcbnew as p
path,mode,ref,pin=sys.argv[1:];b=p.LoadBoard(path)
if mode=='cut':
    f=b.FindFootprintByReference(ref);assert f is not None
    a=next(a for a in f.Pads() if a.GetNumber()==pin)
    tracks=[t for t in b.GetConnectivity().GetConnectedTracks(a) if t.Type()==p.PCB_TRACE_T]
    assert tracks,'no terminal escape found'
    for t in tracks:b.Remove(t)
elif mode in ('reverse','split','reverse-residual','split-residual'):
    ident='90ba6800-0027-5595-a212-7b1f01cfa8dd' if mode.endswith('-residual') else '36f3b6dd-9d7a-54fe-9c03-f7ebe5f77ae8'
    t=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==ident)
    a,c=p.VECTOR2I(t.GetStart()),p.VECTOR2I(t.GetEnd())
    if mode.startswith('reverse'):t.SetStart(c);t.SetEnd(a)
    else:
        mid=p.VECTOR2I((a.x+c.x)//2,(a.y+c.y)//2);t.SetEnd(mid)
        n=p.PCB_TRACK(b);n.SetStart(mid);n.SetEnd(c);n.SetNet(t.GetNet());n.SetLayer(t.GetLayer());n.SetWidth(t.GetWidth());b.Add(n)
elif mode in ('edge-growth','edge-remote'):
    # The 0.60mm TARGET_VIN5 segment stays fully connected and its central
    # 0.10mm reference remains present. Only the outer reference projection grows.
    dx=0. if mode=='edge-growth' else 2.
    z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayer(p.In1_Cu);z.SetZoneName('P3_EDGE_REVIEW_PROBE')
    z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowFootprints(False)
    o=z.Outline();o.NewOutline()
    for x,y in [(79.45+dx,19.49),(79.65+dx,19.49),(79.65+dx,19.69),(79.45+dx,19.69)]:
        o.Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
elif mode in ('reference-void','remote-void'):
    # One real existing long AFE_SCLK segment at (34.3,9.6)-(39.05,24.9).
    # A local ground-only window changes no signal copper and does not cross a source P2 bypass.
    x,y=(36.675,17.25) if mode=='reference-void' else (10.,15.)
    z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayer(p.In1_Cu);z.SetZoneName('P3_REFERENCE_PROBE')
    z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False)
    z.SetDoNotAllowCopperPour(True);z.SetDoNotAllowFootprints(False)
    o=z.Outline();o.NewOutline()
    for xx,yy in [(x-.2,y-.2),(x+.2,y-.2),(x+.2,y+.2),(x-.2,y+.2)]:o.Append(p.FromMM(xx),p.FromMM(yy))
    b.Add(z)
else:raise AssertionError('unknown P3 mutation')
p.SaveBoard(path,b)
"""

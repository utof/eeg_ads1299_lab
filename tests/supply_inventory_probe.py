"""S1 read-only native centerline study; executable only in pinned KiCad subprocess."""

SCRIPT = r"""
import pcbnew as k, json, math, heapq, hashlib, sys
from pathlib import Path
from collections import defaultdict
assert k.Version() == "9.0.2"
# Read-only exact-centerline inventory. Does NOT follow copper-width intersections,
# plane currents, pad spreading or parallel conductance; no impedance extraction.
def inventory(board, active, requests):
    b=k.LoadBoard(str(board));fs={f.GetReference():f for f in b.GetFootprints()}
    pads=[p for f in fs.values()for p in f.Pads()]
    tracks=[t for t in b.GetTracks()if t.Type()==k.PCB_TRACE_T]
    vias=[t for t in b.GetTracks()if t.Type()==k.PCB_VIA_T]
    xy=lambda p:(p.x,p.y)
    cent=lambda a:xy(a.GetPosition())
    
    def circuit(net):
     pts=defaultdict(set);adj=defaultdict(list)
     ts=[t for t in tracks if t.GetNetname()==net]
     for t in ts:pts[t.GetLayer()].update([xy(t.GetStart()),xy(t.GetEnd())])
     for v in vias:
      if v.GetNetname()==net:
       for l in active:pts[l].add(cent(v))
     for a in pads:
      if a.GetNetname()==net:
       for l in active:
        if a.IsOnLayer(l):pts[l].add(cent(a))
     def add(a,z,cost,kind,ident):
      adj[a].append((z,cost,kind,ident));adj[z].append((a,cost,kind,ident))
     for t in ts:
      a,z=xy(t.GetStart()),xy(t.GetEnd());l=t.GetLayer();dx,dy=z[0]-a[0],z[1]-a[1];dd=dx*dx+dy*dy;assert dd>0
      hits=[]
      for p in pts[l]:
       u=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/dd
       # Only exact centerline incidence (1 nm roundoff), not copper-width shortcutting.
       if -1e-12<=u<=1+1e-12 and abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)/math.sqrt(dd)<=1.0:hits.append((u,p))
      hits.sort()
      for (_,p),(_,q) in zip(hits,hits[1:]):
       if p==q:continue
       add((*p,l),(*q,l),math.dist(p,q)/1e6,'segment',t.m_Uuid.AsString())
     for v in vias:
      if v.GetNetname()==net:add((*cent(v),active[0]),(*cent(v),active[1]),0.,'via',v.m_Uuid.AsString())
     for a in pads:
      if a.GetNetname()==net and a.GetAttribute()==k.PAD_ATTRIB_PTH:add((*cent(a),active[0]),(*cent(a),active[1]),0.,'PTH',a.GetParentFootprint().GetReference()+'.'+a.GetNumber())
     return adj
    
    def route(start,end):
     def find(endpoint):
      ref,pin=endpoint.split('.');return next(a for a in fs[ref].Pads() if a.GetNumber()==pin)
     a,z=find(start),find(end);assert a.GetNetname()==z.GetNetname()
     net=a.GetNetname();adj=circuit(net);first=(*cent(a),k.F_Cu);last=(*cent(z),k.F_Cu)
     Q=[(0.,first,[])];seen=set();result=None
     while Q:
      d,p,history=heapq.heappop(Q)
      if p in seen:continue
      seen.add(p)
      if p==last:result=d,history;break
      for q,c,kind,ident in adj[p]:heapq.heappush(Q,(d+c,q,history+[(kind,ident,c,p,q)]))
     assert result is not None,(start,end,net,'no exact-centerline path; do not infer from airwire zero')
     d,h=result
     byid={t.m_Uuid.AsString():t for t in tracks}
     for _,ident,length,_,_ in h:
      if ident in byid:assert byid[ident].GetNetname()==net
     widths=[byid[x[1]].GetWidth()/1e6 for x in h if x[0]=='segment']
     return {'net':net,'from':start,'to':end,'centerline_mm_excludes_vertical_via_length':d,'via_transitions':sum(k=='via' for k,*_ in h),'segments_traversed':len({x[1]for x in h if x[0]=='segment'}),'front_mm':sum(x[2]for x in h if x[0]=='segment'and x[3][2]==k.F_Cu),'In2_mm':sum(x[2]for x in h if x[0]=='segment'and x[3][2]==k.In2_Cu),'minimum_track_width_mm':min(widths),'front_resistance_squares':sum(x[2]/(byid[x[1]].GetWidth()/1e6) for x in h if x[0]=='segment'and x[3][2]==k.F_Cu),'inner_resistance_squares':sum(x[2]/(byid[x[1]].GetWidth()/1e6) for x in h if x[0]=='segment'and x[3][2]==k.In2_Cu),'sections':[{'kind':kind,'id':ident,'length_mm':dist,'from':list(a),'to':list(z),'width_mm':byid[ident].GetWidth()/1e6 if kind=='segment' else None} for kind,ident,dist,a,z in h], 'trace_UUIDs':sorted({x[1]for x in h if x[0]=='segment'})}
    return [route(a,b) for a,b in requests]
ROOT=Path(sys.argv[1])
aux=inventory(ROOT/"hardware/rev_a/auxiliary/auxiliary.kicad_pcb", (k.F_Cu,k.In2_Cu), [('J104.2','U102.14'),('J104.2','U103.14'),('J104.2','U104.14'),('J104.2','R116.1'),('J105.1','J101.17'),('J105.1','J102.21'),('J104.3','U106.1'),('J104.4','U107.1'),('J105.1','U108.1'),('J105.1','R108.1')])
afe=inventory(ROOT/"hardware/rev_a/layout/rev_a.kicad_pcb", (k.F_Cu,k.B_Cu), [('U2.5','J3.2'),('U2.5','C33.1'),('C33.1','J3.2'),('J1.17','R11.1'),('J1.17','U2.1'),('J3.3','C33.1'),('J3.4','C31.1')])
def named_sections(row,board):
 return [(board+':'+json.dumps([s['kind'],s['id'],s['from'],s['to']],separators=(',',':')),s,board)for s in row['sections']]
def collapse(paths):
 prefixes={};sections={};routes={};users=defaultdict(list)
 for sink,path in paths.items():
  ids=[x[0] for x in path];assert len(set(ids))==len(ids)
  for i,(key,section,board) in enumerate(path):
   prefix=ids[:i+1];assert prefixes.setdefault(key,prefix)==prefix,(sink,key,'not a tree')
   sections[key]=section,board;users[key].append(sink)
  routes[sink]=ids
 groupkeys={tuple(v):'E'+str(i) for i,v in enumerate(dict.fromkeys(tuple(v)for v in users.values()))}
 groups={}; membership={}
 for key,sinks in users.items():
  name=groupkeys[tuple(sinks)];membership[key]=name;s,board=sections[key]
  g=groups.setdefault(name,{'downstream':sinks,'F_squares':0.,'In2_squares':0.,'B_squares':0.,'vias':0,'PTH':0,'wire_m':0.,'contact_pairs':0,'extra_ohm':0.,'section_count':0})
  if s['kind']=='segment':
   layer='F' if s['from'][2]==0 else ('B' if board=='AFE' else 'In2');g[layer+'_squares']+=s['length_mm']/s['width_mm']
  elif s['kind']=='via':g['vias']+=1
  elif s['kind']=='PTH':g['PTH']+=1
  elif s['kind']=='cable':g['wire_m']+=.155;g['contact_pairs']+=2;g['extra_ohm']+=.020
  else:raise AssertionError(s)
  g['section_count']+=1
 compact={}
 for sink,ids in routes.items():
  seq=[membership[e] for e in ids];compact[sink]=[e for i,e in enumerate(seq) if i==0 or seq[i-1]!=e]
 return {'groups':groups,'paths':compact}
# Distinct graph identity: across-board link is data, not an inferred copper contact.
feed=named_sections(afe[0],'AFE')+[('cable_feed',{'kind':'cable'},'harness')]
paths={p['to']:feed+named_sections(p,'AUX')for p in aux[:4]}
paths['local_at_C33']=named_sections(afe[1],'AFE')
dvdd=collapse(paths)
vin=collapse({p['to']:named_sections(p,'AUX')for p in [aux[4],aux[5],aux[8],aux[9]]})
rows=[]
for board,ps in [('AUX',aux),('AFE',afe)]:
 for p in ps:
  rows.append({'board':board,'from':p['from'],'to':p['to'],'mm':round(p['centerline_mm_excludes_vertical_via_length'],9),'vias':p['via_transitions'],'PTH':sum(s['kind']=='PTH'for s in p['sections']),'F_squares':round(sum(s['length_mm']/s['width_mm']for s in p['sections']if s['kind']=='segment'and s['from'][2]==0),9),'other_squares':round(sum(s['length_mm']/s['width_mm']for s in p['sections']if s['kind']=='segment'and s['from'][2]!=0),9),'other_layer':'In2.Cu'if board=='AUX'else'B.Cu'})
model={'schema':1,'scope':'selected centerline-tree DC sensitivity; NOT parasitic extraction or qualification','source_commit':'f6932ead58c1d02af145de405312a7f885dbb010','source_tree':'a1bb3a16687c65f736de9c2634bb5ec2e4b990ac','boards':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in ['hardware/rev_a/layout/rev_a.kicad_pcb','hardware/rev_a/auxiliary/auxiliary.kicad_pcb']},'geometry':rows,'dvdd':dvdd,'vin5_aux':vin,'assumed':{'rho20_ohm_mm2_per_m':.0175,'alpha_per_C':.00393,'temperature_C':30.,'F_mm':.035,'In2_mm':.018,'B_mm':.035,'wire_area_mm2':.205,'via_length_mm':1.6,'via_bore_mm':.3,'via_plating_mm':.020,'contact_pair_ohm':.020,'PTH_extra_ohm':.005},'scope_limits':['ADC/local DVDD load lumped at C33, not die extraction','centerline arborescence excludes parallel copper/pad spreading','ground network NOT represented by ideal zero-ohm reference','mode currents, crimp, material and return impedances unqualified','steady sensitivity, no inrush, ringing, regulator thermal or fault deadline'],'qualified':False}
print(json.dumps(model,indent=2))
"""

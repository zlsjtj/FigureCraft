"""Independent analytic visibility samples and polygon-topology checks."""
import argparse, collections, importlib.util, json, math
from pathlib import Path
import numpy as np

def ray_surfaces(xy,r,u,v):
    o=xy[0]*r-xy[1]*u
    hits=[]
    def retained(p):return abs(math.atan2(p[1],p[0]))>=math.radians(35)-1e-8
    def add(t,role,keep):
        p=o+t*v
        if keep(p):hits.append((t,role))
    for radius,zlo,zhi,role,sleeve in [(12,0,30,'sleeve_outer',True),(9,0,30,'sleeve_inner',True),(5,-3,33,'core_wall',False)]:
        aa=np.dot(v[:2],v[:2]);bb=2*np.dot(o[:2],v[:2]);cc=np.dot(o[:2],o[:2])-radius**2
        disc=bb*bb-4*aa*cc
        if aa>1e-10 and disc>=0:
            for t in [(-bb-math.sqrt(disc))/(2*aa),(-bb+math.sqrt(disc))/(2*aa)]:
                add(t,role,lambda p:zlo-1e-8<=p[2]<=zhi+1e-8 and (not sleeve or retained(p)))
    if abs(v[2])>1e-10:
        for z in [0,30]:add((z-o[2])/v[2],'sleeve_annular_rim',lambda p:9-1e-8<=np.linalg.norm(p[:2])<=12+1e-8 and retained(p))
        for z in [-3,33]:add((z-o[2])/v[2],'core_end',lambda p:np.linalg.norm(p[:2])<=5+1e-8)
    for theta in np.radians([35,325]):
        n=np.array([-math.sin(theta),math.cos(theta),0]);radial=np.array([math.cos(theta),math.sin(theta),0]);den=n@v
        if abs(den)>1e-10:add(-(n@o)/den,'sleeve_opening_edge',lambda p:9-1e-8<=radial@p<=12+1e-8 and -1e-8<=p[2]<=30+1e-8)
    return max(hits) if hits else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument('out',type=Path);a=ap.parse_args();out=a.out
    sp=importlib.util.spec_from_file_location('source',out/'build_figure.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
    faces=m.model_faces();stats={}
    for entity in ['sleeve','core']:
        fs=[f for f in faces if f['role'].startswith(entity)];edges=collections.Counter();vertices=set();neighbors=collections.defaultdict(list)
        for i,f in enumerate(fs):
            pts=[tuple(np.round(p,8)) for p in f['p']];vertices.update(pts)
            for p,q in zip(pts,pts[1:]+pts[:1]):
                edge=tuple(sorted([p,q]));edges[edge]+=1;neighbors[edge].append(i)
        adj=collections.defaultdict(set)
        for ids in neighbors.values():
            for i in ids:adj[i].update(ids)
        todo=[0];seen=set()
        while todo:
            i=todo.pop()
            if i not in seen:seen.add(i);todo.extend(adj[i]-seen)
        stats[entity]={'faces':len(fs),'vertices':len(vertices),'edges':len(edges),'edge_incidence_counts':dict(collections.Counter(edges.values())),'connected':len(seen)==len(fs),'euler_characteristic':len(vertices)-len(edges)+len(fs)}
        assert all(x==2 for x in edges.values());assert len(seen)==len(fs);assert stats[entity]['euler_characteristic']==2
    spec=json.loads((out/'figure_spec.json').read_text(encoding='utf-8'));visibility={}
    for name in ['main','axial']:
        rec=json.loads((out/f'surface-record-{name}.json').read_text());c=spec['camera'] if name=='main' else spec['axial_view']
        r,u=np.array(c['right']),np.array(c['up']);v=np.array(c['view_toward_observer'] if name=='main' else c['view'])
        roles={value:key for key,value in rec['roles'].items()};errs=[];bad=[]
        for s in rec['visibility_samples']:
            hit=ray_surfaces(np.array(s['xy']),r,u,v)
            if hit is None:bad.append({'sample':s,'reason':'no analytic intersection'});continue
            err=abs(hit[0]-s['depth']);errs.append(err)
            if err>.006 or roles[s['role_id']]!=hit[1]:bad.append({'sample':s,'analytic':hit,'depth_error':err})
        visibility[name]={'samples':len(rec['visibility_samples']),'max_depth_error':max(errs),'tolerance':.006,'mismatches':bad,'status':'PASS' if not bad else 'FAIL'}
    result={'topology':stats,'analytic_visibility':visibility,'gap':{'minimum_analytic_radius_difference':9-5,'contact':False},'status':'PASS' if all(v['status']=='PASS' for v in visibility.values()) else 'FAIL','scope':'Closed-manifold topology plus 400 deterministic visible samples per view; not a proof for every output pixel.'}
    (out/'geometry-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()

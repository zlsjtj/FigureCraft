"""Editable 2.5D object components for the existing Scene / JSON renderer.

These builders describe geometry, not material properties or performance.
They never select a layout, role palette, scientific relation or object count.
All lengths use the scene viewBox. Existing low-level Scene calls remain valid.
"""
from __future__ import annotations
import math


def _spec(scene):
    return scene.s if hasattr(scene, 's') else scene


def _add(scene, ident, kind, **fields):
    item = dict(id=ident, type=kind, **fields)
    spec = _spec(scene)
    if any(p['id'] == ident for p in spec['items']):
        raise ValueError('Duplicate item ID: ' + ident)
    spec['items'].append(item)
    return item


def _record(scene, record):
    _spec(scene).setdefault('component_constraints', []).append(record)
    return record


def array_grid(scene, ident, labels, *, x, y, columns, cell_w=64, cell_h=36,
               gap=6, entity, role, size=20, states=None):
    """Row-major labeled cells; optional boolean state has explicit fill encoding."""
    if columns < 1 or not labels or (states is not None and len(states) != len(labels)):
        raise ValueError('Nonempty labels, positive columns, and one state per cell required')
    ids=[]
    for index,label in enumerate(labels):
        logical=f'{ident}-{index}';ids.append(logical)
        xx=x+(index%columns)*(cell_w+gap);yy=y+(index//columns)*(cell_h+gap)
        fields=dict(entity=entity,role=role,logical_id=logical)
        live=True if states is None else states[index]
        if not isinstance(live,bool):raise ValueError('Cell states must be bool')
        _add(scene,logical,'rect',x=xx,y=yy,w=cell_w,h=cell_h,fill=f'@{role}.fill' if live else '#FFFFFF',
             stroke=f'@{role}.stroke',stroke_width=1.5,object_part='primary',**fields,
             **({'occupied':live} if states is not None else {}))
        _add(scene,logical+'-label','text',x=xx+cell_w/2,y=yy+cell_h/2+size*.34,
             text=str(label),size=size,align='center',fill='#24323B',object_part='decoration',**fields)
    rule=dict(name=ident,expected=len(ids),scope={'id_prefix':ident+'-'},expected_logical_ids=ids)
    if states is not None:
        rule.update(expected_states=dict(zip(ids,states)),state_field='occupied',
                    state_styles=[{'state':True,'style':{'fill':f'@{role}.fill'}},
                                  {'state':False,'style':{'fill':'#FFFFFF'}}])
    _spec(scene).setdefault('count_constraints',[]).append(rule)
    return ids


def layered_slab(scene, ident, *, x, y, width, depth_x, depth_y, thickness,
                 entity, role, logical_id=None):
    """A parallel-projection slab, top plus two visible bound faces.

    x/y is the front-left top; positive depth_x and negative depth_y recede
    right/up. Draw lower slabs before upper ones; no physical scale implied.
    """
    if min(width,depth_x,thickness)<=0 or depth_y>=0:raise ValueError('Invalid slab projection')
    logical_id=logical_id or ident
    a=[x,y];b=[x+width,y];c=[x+width+depth_x,y+depth_y];d=[x+depth_x,y+depth_y]
    front=[a,b,[b[0],b[1]+thickness],[a[0],a[1]+thickness]]
    side=[b,c,[c[0],c[1]+thickness],[b[0],b[1]+thickness]]
    fields=dict(entity=entity,role=role,logical_id=logical_id,stroke=f'@{role}.stroke',stroke_width=1.5)
    _add(scene,ident+'-front','polygon',points=front,fill=f'@{role}.shadow',object_part='decoration',**fields)
    _add(scene,ident+'-side','polygon',points=side,fill=f'@{role}.fill',object_part='decoration',**fields)
    _add(scene,ident+'-top','polygon',points=[a,b,c,d],fill=f'@{role}.highlight',object_part='primary',**fields)
    return _record(scene,dict(id=ident,kind='slab',logical_id=logical_id,entity=entity,
        primary=ident+'-top',parts=[ident+'-front',ident+'-side',ident+'-top'],
        geometry=dict(x=x,y=y,width=width,depth_x=depth_x,depth_y=depth_y,thickness=thickness)))


def index_correspondence(scene, ident, source_cell, target_cell, *, meaning, color='#5B6470'):
    """Vertical array correspondence, not causal flow; labels/data stay caller-owned."""
    items={p['id']:p for p in _spec(scene)['items']}
    source,target=items[source_cell],items[target_cell]
    if any(p['type']!='rect' for p in (source,target)):raise ValueError('Correspondence requires two array cells')
    points=[[source['x']+source['w']/2,source['y']+source['h']],
            [target['x']+target['w']/2,target['y']]]
    relation=dict(id=ident,**{'from':source['entity'],'to':target['entity']},kind='correspondence',meaning=meaning,
                  geometry={'item_id':ident,'from':points[0],'to':points[-1],'arrow_required':False})
    _spec(scene)['relations'].append(relation)
    return _add(scene,ident,'line',points=points,stroke=color,stroke_width=1.3,dash=[3,4],relation=ident)


def _sector(x,y,r,start=-35,end=95,segments=28):
    return [[x,y]]+[[x+r*math.cos(math.radians(start+(end-start)*i/segments)),
                      y+r*math.sin(math.radians(start+(end-start)*i/segments))] for i in range(segments+1)]


def coated_particle(scene, ident, *, x, y, radius, core_radius, entity,
                    shell_role, core_role, logical_id=None, view='whole', detail_of=None):
    """An intact shell, a cut wedge, or a flat local section of one particle.

    view='whole' hides its core. view='cutaway' exposes one radial wedge.
    view='section' is a planar circle cross-section. detail_of is a component
    ID already in this scene and repeats its logical object, never a new one.
    """
    if not 0<core_radius<radius:raise ValueError('Core must lie strictly inside its shell')
    if view not in ('whole','cutaway','section'):raise ValueError('Unknown particle view')
    if detail_of:
        sources=[c for c in _spec(scene).get('component_constraints',[]) if c['id']==detail_of]
        if len(sources)!=1 or sources[0]['kind']!='coated_particle':raise ValueError('detail_of must identify one existing particle')
        source=sources[0]
        if source.get('detail_of'):raise ValueError('Bind detail to primary object, not another detail')
        logical_id=source['logical_id'];entity=source['entity']
        # Preserve the source core/shell ratio in every repeated detail.
        ratio=source['geometry']['core_radius']/source['geometry']['radius']
        if abs(core_radius/radius-ratio)>1e-9:raise ValueError('Repeated section must preserve the source core/shell ratio')
    logical_id=logical_id or ident
    mainpart='detail' if detail_of else 'primary';part='detail' if detail_of else 'decoration'
    bind=dict(entity=entity,logical_id=logical_id)
    parts=[]
    def add(suffix,kind,role,**geometry):
        pid=ident+'-'+suffix;parts.append(pid)
        return _add(scene,pid,kind,role=role,**bind,**geometry)
    add('shell','circle',shell_role,x=x,y=y,r=radius,fill=f'@{shell_role}.fill',
        stroke=f'@{shell_role}.stroke',stroke_width=1.6,object_part=mainpart)
    if view!='section':
        add('light','ellipse',shell_role,x=x-radius*.23,y=y-radius*.28,rx=radius*.38,ry=radius*.24,
            fill=f'@{shell_role}.highlight',object_part=part,decorative_depth=True)
    if view=='section':
        add('core','circle',core_role,x=x,y=y,r=core_radius,fill=f'@{core_role}.fill',
            stroke=f'@{core_role}.stroke',stroke_width=1.2,object_part=part)
    elif view=='cutaway':
        add('cut-face','polygon',shell_role,points=_sector(x,y,radius),fill=f'@{shell_role}.highlight',
            stroke=f'@{shell_role}.stroke',stroke_width=1.2,object_part=part)
        add('core','polygon',core_role,points=_sector(x,y,core_radius),fill=f'@{core_role}.fill',
            stroke=f'@{core_role}.stroke',stroke_width=1.2,object_part=part)
    return _record(scene,dict(id=ident,kind='coated_particle',logical_id=logical_id,entity=entity,
        primary=ident+'-shell',parts=parts,detail_of=detail_of,view=view,
        geometry=dict(x=x,y=y,radius=radius,core_radius=core_radius),
        shell_role=shell_role,core_role=core_role))


def detail_link(scene, ident, source_component, detail_component, points, color='#5B6470'):
    """Noncausal dashed leader for a repeated detail; no arrowhead."""
    comps={c['id']:c for c in _spec(scene).get('component_constraints',[])}
    source,detail=comps[source_component],comps[detail_component]
    if detail.get('detail_of')!=source_component:raise ValueError('Detail is not bound to this source')
    relation=dict(id=ident,**{'from':source['entity'],'to':detail['entity']},kind='detail',
                  meaning='Repeated view of the same logical object; not an additional particle',
                  geometry={'item_id':ident,'from':points[0],'to':points[-1],'arrow_required':False})
    _spec(scene)['relations'].append(relation)
    return _add(scene,ident,'line',points=points,stroke=color,stroke_width=1.5,dash=[5,4],relation=ident)


def _hemisphere_outline(x,y,r,aspect):
    """Visible curved half joined to the oblique great-circle cut face."""
    k=.5522847498307936
    return [['M',x,y-r],['C',x-k*r,y-r,x-r,y-k*r,x-r,y],
            ['C',x-r,y+k*r,x-k*r,y+r,x,y+r],
            ['C',x+k*r*aspect,y+r,x+r*aspect,y+k*r,x+r*aspect,y],
            ['C',x+r*aspect,y-k*r,x+k*r*aspect,y-r,x,y-r],['Z']]


def _arc_commands(x,y,r,start,end):
    commands=[];n=max(1,math.ceil(abs(end-start)/80))
    for i in range(n):
        a=math.radians(start+(end-start)*i/n);b=math.radians(start+(end-start)*(i+1)/n);k=4/3*math.tan((b-a)/4)
        commands.append(['C',x+r*(math.cos(a)-k*math.sin(a)),y+r*(math.sin(a)+k*math.cos(a)),
                         x+r*(math.cos(b)+k*math.sin(b)),y+r*(math.sin(b)-k*math.cos(b)),x+r*math.cos(b),y+r*math.sin(b)])
    return commands


def _wedge_path(x,y,r,start=-35,end=65,remaining=False):
    a=math.radians(start)
    return [['M',x,y],['L',x+r*math.cos(a),y+r*math.sin(a)]]+_arc_commands(x,y,r,start,end-360 if remaining else end)+[['Z']]


def _cut_rim(x,y,r,core_r,angle,offset):
    a,b=map(math.radians,(angle,angle+offset))
    return [[x+rr*math.cos(aa),y+rr*math.sin(aa)] for rr,aa in ((r,a),(r,b),(core_r,b),(core_r,a))]


def rounded_coated_particle(scene, ident, *, x, y, radius, core_radius, entity,
                             shell_role, core_role, logical_id=None, view='whole',
                             detail_of=None, section_aspect=.56):
    """Smooth D1 surface or an explicit oblique hemisphere section.

    Lighting is an illustrative upper-left radial ramp, not a physical renderer.
    hemisphere uses a flat projected great-circle face, with no glossy core.
    Old coated_particle() remains unchanged for compatibility.
    """
    if view not in ('whole','section','hemisphere','cutaway'):raise ValueError('Unknown rounded-particle view')
    if not 0<core_radius<radius:raise ValueError('Core must lie strictly inside its shell')
    if not .25<=section_aspect<=1:raise ValueError('Section aspect must be 0.25..1')
    if detail_of:
        source=next((c for c in _spec(scene).get('component_constraints',[]) if c['id']==detail_of),None)
        if not source or source.get('detail_of') or source['kind'] not in ('coated_particle','rounded_coated_particle'):raise ValueError('Detail must bind to one original particle')
        if abs(core_radius/radius-source['geometry']['core_radius']/source['geometry']['radius'])>1e-9:raise ValueError('Repeated section must preserve the source core/shell ratio')
        logical_id=source['logical_id'];entity=source['entity']
    logical_id=logical_id or ident;parts=[]
    bind=dict(entity=entity,logical_id=logical_id)
    def add(suffix,kind,role,**kw):
        pid=ident+'-'+suffix;parts.append(pid)
        return _add(scene,pid,kind,role=role,object_part=('detail' if detail_of else 'primary' if suffix=='shell' else 'decoration'),**bind,**kw)
    surface=dict(fill=f'@{shell_role}.base',stroke=f'@{shell_role}.stroke',stroke_width=.8,
        fill_gradient={'kind':'radial','cx':x-radius*.32,'cy':y-radius*.4,'r':radius*1.6,
                       'stops':[[0,f'@{shell_role}.highlight'],[.30,f'@{shell_role}.fill'],[.63,f'@{shell_role}.base'],[1,f'@{shell_role}.shadow']]})
    if view=='cutaway':add('shell','path',shell_role,commands=_wedge_path(x,y,radius,remaining=True),**surface)
    elif view=='hemisphere':add('shell','path',shell_role,commands=_hemisphere_outline(x,y,radius,section_aspect),**surface)
    elif view=='whole':add('shell','circle',shell_role,x=x,y=y,r=radius,**surface)
    else:add('shell','circle',shell_role,x=x,y=y,r=radius,fill=f'@{shell_role}.base',stroke=f'@{shell_role}.stroke',stroke_width=1)
    if view=='hemisphere':
        add('cut-face','ellipse',shell_role,x=x,y=y,rx=radius*section_aspect,ry=radius,
            fill=f'@{shell_role}.fill',stroke=f'@{shell_role}.stroke',stroke_width=1)
        add('core','ellipse',core_role,x=x,y=y,rx=core_radius*section_aspect,ry=core_radius,
            fill=f'@{core_role}.fill',stroke=f'@{core_role}.stroke',stroke_width=.9)
    elif view=='section':add('core','circle',core_role,x=x,y=y,r=core_radius,fill=f'@{core_role}.fill',stroke=f'@{core_role}.stroke',stroke_width=.9)
    elif view=='cutaway':
        # The opening removes a schematic coating wedge, leaving the inner
        # sphere intact. Two narrow annular cut rims show coating thickness.
        add('core','path',core_role,commands=_wedge_path(x,y,core_radius),fill=f'@{core_role}.base',
            stroke=f'@{core_role}.stroke',stroke_width=.9,
            fill_gradient={'kind':'radial','cx':x-core_radius*.32,'cy':y-core_radius*.4,'r':core_radius*1.6,
                           'stops':[[0,f'@{core_role}.highlight'],[.38,f'@{core_role}.fill'],[.72,f'@{core_role}.base'],[1,f'@{core_role}.shadow']]})
        for name,angle,offset,tone in [('upper-rim',-35,-8,'highlight'),('lower-rim',65,8,'shadow')]:
            add(name,'polygon',shell_role,points=_cut_rim(x,y,radius,core_radius,angle,offset),
                fill=f'@{shell_role}.{tone}',stroke=f'@{shell_role}.stroke',stroke_width=.7)
    return _record(scene,dict(id=ident,kind='rounded_coated_particle',logical_id=logical_id,entity=entity,
        primary=ident+'-shell',parts=parts,detail_of=detail_of,view=view,shell_role=shell_role,core_role=core_role,
        geometry=dict(x=x,y=y,radius=radius,core_radius=core_radius,section_aspect=section_aspect),
        light_direction='upper_left',depth_mode='D1_vector_2_5d_not_physical_3D'))


def declare_count(scene, name, entity, logical_ids):
    """Cover every main, decorative and detail item carrying this entity."""
    rule=dict(name=name,expected=len(logical_ids),scope={'entity':entity},expected_logical_ids=list(logical_ids))
    _spec(scene).setdefault('count_constraints',[]).append(rule)
    return rule


def _ellipse_arc_commands(x, y, rx, ry, start, end):
    """Cubic ellipse arc in degrees; no polygonal rim approximation."""
    out=[];n=max(1,math.ceil(abs(end-start)/75))
    for i in range(n):
        a=math.radians(start+(end-start)*i/n);b=math.radians(start+(end-start)*(i+1)/n)
        k=4/3*math.tan((b-a)/4)
        out.append(['C',x+rx*(math.cos(a)-k*math.sin(a)),y+ry*(math.sin(a)+k*math.cos(a)),
                    x+rx*(math.cos(b)+k*math.sin(b)),y+ry*(math.sin(b)-k*math.cos(b)),
                    x+rx*math.cos(b),y+ry*math.sin(b)])
    return out


def _slice_geometry(x,y,r,core_r,cut_offset,normal_angle_deg,face_direction):
    """Orthographic sphere/plane intersection used as an editable D1 drawing.

    Plane normal = (sin(theta),0,cos(theta)); plane offset = cut_offset*r.
    No material dimensions, fracture mechanics or physical lighting implied.
    """
    if not all(math.isfinite(v) for v in (x,y,r,core_r,cut_offset,normal_angle_deg)):
        raise ValueError('Finite slice geometry required')
    if not 0<core_r<r or not 0<=cut_offset<core_r/r:
        raise ValueError('The cut plane must intersect the core and its coating')
    if not 20<=normal_angle_deg<=70 or face_direction not in ('left','right'):
        raise ValueError('Angle must be 20..70 degrees; face_direction left or right')
    theta=math.radians(normal_angle_deg);nx,nz=math.sin(theta),math.cos(theta)
    d=cut_offset*r;rho=math.sqrt(r*r-d*d);core_rho=math.sqrt(core_r*core_r-d*d)
    cx=x+d*nx;rx=rho*nz;ry=rho
    if d<nx*r:
        alpha=math.degrees(math.acos(d/(nx*r)))
        joinx=d/nx;beta=math.degrees(math.acos((joinx-d*nx)/rx))
        top=[x+joinx,y-math.sqrt(r*r-joinx*joinx)]
        outline=[['M',*top]]+_arc_commands(x,y,r,-alpha,-360+alpha)
        outline+=_ellipse_arc_commands(cx,y,rx,ry,beta,-beta)+[['Z']]
    else:
        outline=[['M',x+r,y]]+_arc_commands(x,y,r,0,360)+[['Z']]
    if face_direction=='left':
        for command in outline:
            for i in range(1,len(command),2):command[i]=2*x-command[i]
        cx=2*x-cx
    return {'outline':outline,'cut_face':dict(x=cx,y=y,rx=rx,ry=ry),
            'core_face':dict(x=cx,y=y,rx=core_rho*nz,ry=core_rho),
            'plane_offset':d,'normal_angle_deg':normal_angle_deg}


def sliced_coated_particle(scene,ident,*,x,y,radius,core_radius,entity,shell_role,
                          core_role,logical_id=None,detail_of=None,cut_offset=.32,
                          normal_angle_deg=55,face_direction='right'):
    """Coherent cap removal: curved silhouette joined to one flat cut plane.

    A zero offset is a central section; a positive offset removes a smaller cap.
    The two projected cut radii are calculated, not copied from sphere radii.
    The selected source's original radius ratio stays unchanged in metadata.
    Legacy rounded_coated_particle cutaway behavior is intentionally retained.
    """
    geometry=_slice_geometry(x,y,radius,core_radius,cut_offset,normal_angle_deg,face_direction)
    if detail_of:
        source=next((c for c in _spec(scene).get('component_constraints',[]) if c['id']==detail_of),None)
        if not source or source.get('detail_of') or source['kind'] not in ('coated_particle','rounded_coated_particle','sliced_coated_particle','opened_coating_particle'):
            raise ValueError('Detail must bind to one original particle')
        if abs(core_radius/radius-source['geometry']['core_radius']/source['geometry']['radius'])>1e-9:
            raise ValueError('Repeated section must preserve the source core/shell radius ratio')
        logical_id=source['logical_id'];entity=source['entity']
    logical_id=logical_id or ident;parts=[]
    def add(suffix,kind,role,**kw):
        pid=ident+'-'+suffix;parts.append(pid)
        return _add(scene,pid,kind,role=role,entity=entity,logical_id=logical_id,
                    object_part='detail' if detail_of else 'primary' if suffix=='shell' else 'decoration',**kw)
    add('shell','path',shell_role,commands=geometry['outline'],fill=f'@{shell_role}.base',
        stroke=f'@{shell_role}.stroke',stroke_width=.9,
        fill_gradient={'kind':'radial','cx':x-radius*.35,'cy':y-radius*.4,'r':radius*1.65,
                       'stops':[[0,f'@{shell_role}.highlight'],[.28,f'@{shell_role}.fill'],[.66,f'@{shell_role}.base'],[1,f'@{shell_role}.shadow']]})
    add('cut-face','ellipse',shell_role,**geometry['cut_face'],fill=f'@{shell_role}.fill',
        stroke=f'@{shell_role}.stroke',stroke_width=1)
    add('core','ellipse',core_role,**geometry['core_face'],fill=f'@{core_role}.fill',
        stroke=f'@{core_role}.stroke',stroke_width=.9)
    return _record(scene,dict(id=ident,kind='sliced_coated_particle',view='oblique_cap_section',
        logical_id=logical_id,entity=entity,primary=ident+'-shell',parts=parts,detail_of=detail_of,
        shell_role=shell_role,core_role=core_role,light_direction='upper_left',
        depth_mode='D1_analytic_projection_not_physical_3D',
        geometry=dict(x=x,y=y,radius=radius,core_radius=core_radius,cut_offset=cut_offset,
                      normal_angle_deg=normal_angle_deg,face_direction=face_direction)))


def _exposed_cap_outline(x,y,r,plane_offset,normal_angle_deg,face_direction):
    """Projected curved core cap in front of a coating-only removal plane."""
    th=math.radians(normal_angle_deg);nx,nz=math.sin(th),math.cos(th)
    d=plane_offset;rho=math.sqrt(r*r-d*d);cx=x+d*nx;rx=rho*nz
    if d<nx*r:
        joinx=d/nx;alpha=math.degrees(math.acos(joinx/r))
        beta=math.degrees(math.acos((joinx-d*nx)/rx))
        commands=[['M',x+joinx,y-math.sqrt(r*r-joinx*joinx)]]
        commands+=_arc_commands(x,y,r,-alpha,alpha)
        commands+=_ellipse_arc_commands(cx,y,rx,rho,beta,360-beta)+[['Z']]
    else:
        commands=[['M',cx+rx,y]]+_ellipse_arc_commands(cx,y,rx,rho,0,360)+[['Z']]
    if face_direction=='left':
        for c in commands:
            for i in range(1,len(c),2):c[i]=2*x-c[i]
    return commands


def opened_coating_particle(scene,ident,*,x,y,radius,core_radius,entity,shell_role,
                            core_role,logical_id=None,detail_of=None,cut_offset=.15,
                            normal_angle_deg=65,face_direction='right'):
    """Remove only a coating cap; expose an intact curved core through the rim.

    Unlike sliced_coated_particle, no core material is removed. The flat coating
    rim and the curved core share the same plane intersection; the exposed cap
    is drawn in front of the rim. This is a limited analytic D1 projection.
    """
    record=sliced_coated_particle(scene,ident,x=x,y=y,radius=radius,core_radius=core_radius,
        entity=entity,shell_role=shell_role,core_role=core_role,logical_id=logical_id,
        detail_of=detail_of,cut_offset=cut_offset,normal_angle_deg=normal_angle_deg,
        face_direction=face_direction)
    core=next(p for p in _spec(scene)['items'] if p['id']==ident+'-core')
    for key in ('x','y','rx','ry'):core.pop(key,None)
    core.update(type='path',commands=_exposed_cap_outline(x,y,core_radius,cut_offset*radius,normal_angle_deg,face_direction),
        fill=f'@{core_role}.base',fill_gradient={'kind':'radial','cx':x-core_radius*.32,'cy':y-core_radius*.4,'r':core_radius*1.6,
               'stops':[[0,f'@{core_role}.highlight'],[.3,f'@{core_role}.fill'],[.66,f'@{core_role}.base'],[1,f'@{core_role}.shadow']]})
    record.update(kind='opened_coating_particle',view='coating_cap_removed_core_intact',
                  core_state='intact',coating_state='illustrative_cap_removed')
    return record


def declare_occlusion(scene, back_item, front_item):
    """Validate this explicit painter-order pair and overlapping bounds only."""
    _spec(scene).setdefault('occlusion_constraints',[]).append({'back':back_item,'front':front_item})


def _bounds(item):
    t=item['type']
    if t=='circle':return (item['x']-item['r'],item['y']-item['r'],item['x']+item['r'],item['y']+item['r'])
    if t=='ellipse':return (item['x']-item['rx'],item['y']-item['ry'],item['x']+item['rx'],item['y']+item['ry'])
    if t=='rect':return (item['x'],item['y'],item['x']+item['w'],item['y']+item['h'])
    if t=='polygon':
        xs,ys=zip(*item['points']);return (min(xs),min(ys),max(xs),max(ys))
    return None


def audit_components(spec):
    """Checks helper geometry and bindings. No inferred physical occlusion claim."""
    findings=[];items={p['id']:p for p in spec['items']};order={p['id']:i for i,p in enumerate(spec['items'])}
    comps={c['id']:c for c in spec.get('component_constraints',[])}
    def fail(check,**fields):findings.append(dict(level='FAIL',check=check,**fields))
    if len(comps)!=len(spec.get('component_constraints',[])):fail('duplicate_component_id')
    for c in comps.values():
        if c.get('kind') not in ('slab','coated_particle','rounded_coated_particle','sliced_coated_particle','opened_coating_particle'):
            findings.append(dict(level='REVIEW_REQUIRED',check='unknown_component_kind',component=c['id']));continue
        if any(pid not in items for pid in c['parts']):fail('component_part_missing',component=c['id']);continue
        primary=items[c['primary']]
        for pid in c['parts']:
            p=items[pid]
            part='detail' if c.get('detail_of') else 'primary' if pid==c['primary'] else 'decoration'
            if p.get('logical_id')!=c['logical_id'] or p.get('entity')!=c['entity'] or p.get('object_part')!=part:
                fail('component_part_binding',item=pid)
        g=c['geometry']
        if c['kind']=='slab':
            x,y,w,dx,dy,t=(g[k] for k in ('x','y','width','depth_x','depth_y','thickness'))
            expected={'top':[[x,y],[x+w,y],[x+w+dx,y+dy],[x+dx,y+dy]],
                'front':[[x,y],[x+w,y],[x+w,y+t],[x,y+t]],
                'side':[[x+w,y],[x+w+dx,y+dy],[x+w+dx,y+dy+t],[x+w,y+t]]}
            for side,points in expected.items():
                if items[c['id']+'-'+side].get('points')!=points:fail('slab_shared_edge',item=c['id']+'-'+side)
        else:
            if c.get('kind') in ('sliced_coated_particle','opened_coating_particle'):
                try:
                    expected=_slice_geometry(g['x'],g['y'],g['radius'],g['core_radius'],g['cut_offset'],g['normal_angle_deg'],g['face_direction'])
                    if primary.get('commands')!=expected['outline']:fail('slice_shared_silhouette',component=c['id'])
                    for suffix,face in [('cut-face','cut_face'),('core','core_face')]:
                        p=items.get(c['id']+'-'+suffix,{})
                        if c['kind']=='opened_coating_particle' and suffix=='core':
                            if p.get('type')!='path' or p.get('commands')!=_exposed_cap_outline(g['x'],g['y'],g['core_radius'],g['cut_offset']*g['radius'],g['normal_angle_deg'],g['face_direction']):fail('exposed_core_cap_geometry',component=c['id'])
                            if c.get('core_state')!='intact' or c.get('coating_state')!='illustrative_cap_removed':fail('opened_core_state_inconsistent',component=c['id'])
                            continue
                        if p.get('type')!='ellipse' or any(p.get(k)!=v for k,v in expected[face].items()):fail('slice_plane_projection',component=c['id'],part=suffix)
                        if p.get('fill_gradient'):fail('curved_shading_on_flat_slice',component=c['id'],part=suffix)
                    if order[c['id']+'-core']<=order[c['id']+'-cut-face']:fail('slice_core_hidden_by_cut_face',component=c['id'])
                except (ValueError,KeyError):fail('invalid_slice_geometry',component=c['id'])
            elif c.get('kind')=='rounded_coated_particle' and c.get('view')=='cutaway':
                if primary.get('commands')!=_wedge_path(g['x'],g['y'],g['radius'],remaining=True):fail('cutaway_opening_outline',component=c['id'])
                if items.get(c['id']+'-core',{}).get('commands')!=_wedge_path(g['x'],g['y'],g['core_radius']):fail('cutaway_core_projection',component=c['id'])
                for suffix,angle,offset in [('upper-rim',-35,-8),('lower-rim',65,8)]:
                    p=items.get(c['id']+'-'+suffix,{})
                    if p.get('points')!=_cut_rim(g['x'],g['y'],g['radius'],g['core_radius'],angle,offset):fail('cutaway_rim_geometry',component=c['id'])
                    if p.get('fill_gradient'):fail('curved_shading_on_flat_cut_rim',item=p['id'])
            elif c.get('view')=='hemisphere':
                if primary.get('commands')!=_hemisphere_outline(g['x'],g['y'],g['radius'],g['section_aspect']):fail('hemisphere_outline',component=c['id'])
                for suffix,r in [('cut-face',g['radius']),('core',g['core_radius'])]:
                    p=items.get(c['id']+'-'+suffix,{})
                    expected=dict(type='ellipse',x=g['x'],y=g['y'],rx=r*g['section_aspect'],ry=r)
                    if any(p.get(k)!=v for k,v in expected.items()):fail('hemisphere_cut_plane',component=c['id'],part=suffix)
                    if p.get('fill_gradient'):fail('curved_shading_on_flat_cut_plane',item=p['id'])
            elif any(primary.get(k)!=v for k,v in {'x':g['x'],'y':g['y'],'r':g['radius'],'type':'circle'}.items()):fail('shell_geometry',component=c['id'])
            if not 0<g['core_radius']<g['radius']:fail('core_outside_shell',component=c['id'])
            core=items.get(c['id']+'-core')
            if c['view']=='whole' and core:fail('core_visible_in_intact_shell',component=c['id'])
            if c['view']=='section':
                if not core or any(core.get(k)!=v for k,v in {'x':g['x'],'y':g['y'],'r':g['core_radius'],'type':'circle'}.items()):fail('section_core_geometry',component=c['id'])
            if c['view']=='cutaway' and c['kind']=='coated_particle':
                for suffix,r in [('cut-face',g['radius']),('core',g['core_radius'])]:
                    p=items.get(c['id']+'-'+suffix)
                    if not p or p.get('points')!=_sector(g['x'],g['y'],r):fail('cutaway_correspondence',component=c['id'],part=suffix)
            if core and order[core['id']]<order[primary['id']]:fail('core_hidden_by_shell_order',component=c['id'])
            if c.get('detail_of'):
                source=comps.get(c['detail_of'])
                if not source or source.get('detail_of') or source.get('logical_id')!=c['logical_id']:
                    fail('detail_source_binding',component=c['id'])
                elif abs(g['core_radius']/g['radius']-source['geometry']['core_radius']/source['geometry']['radius'])>1e-9:
                    fail('detail_section_ratio',component=c['id'])
    for pair in spec.get('occlusion_constraints',[]):
        back,front=pair['back'],pair['front']
        if back not in items or front not in items:fail('occlusion_item_missing',pair=pair);continue
        if order[back]>=order[front]:fail('occlusion_order',pair=pair)
        a,b=_bounds(items[back]),_bounds(items[front])
        if a is None or b is None:findings.append(dict(level='REVIEW_REQUIRED',check='occlusion_bounds_unsupported',pair=pair))
        elif min(a[2],b[2])<=max(a[0],b[0]) or min(a[3],b[3])<=max(a[1],b[1]):fail('occlusion_no_bounds_overlap',pair=pair)
    return {'status':'FAIL' if any(f['level']=='FAIL' for f in findings) else 'REVIEW_REQUIRED' if findings else 'PASS',
            'scope':'Declared components, shared edges, section ratios and painter order/bounds; actual visibility and physical interpretation require visual review',
            'components':len(comps),'occlusion_pairs':len(spec.get('occlusion_constraints',[])),'findings':findings}

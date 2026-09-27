"""Small editable geometry for sampled patterns and explicit one-to-many links.

Returns the same flat primitive dictionaries used by FigureCraft scenes. It
does not choose a layout, infer reuse, invent an axis break or render a figure.
Caller-owned labels/units/captions distinguish data from physical objects.
"""
from __future__ import annotations
import math
import warnings
_UNSPECIFIED=object()


def _finite(*numbers):
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in numbers):
        raise ValueError('Geometry and values must be finite numbers')


def sampled_pattern(ident, values, *, x, y, units, entity, role,
                    base=0, labels=None, marker=6, label_size=11,
                    fill='#E3EFF3', stroke='#3E7B8F', ink='#253B44',
                    label_side='above', source_pattern=None):
    """Draw ordered samples on a local numeric axis with a caller-given origin.

    x is the position of local zero; position=value*units+x (never ordinal).
    base changes address labels, not local geometry. labels is an index list;
    None labels every sample and [] labels none. Negative samples are valid.
    source_pattern is provenance only: it does not imply an extra allocation.
    Units, omitted samples and separate origins must be explained by caller.
    """
    values=list(values)
    _finite(x,y,units,base,marker,label_size,*values)
    if not values or units<=0 or marker<=0 or label_size<=0:
        raise ValueError('Nonempty values and positive scale/sizes required')
    if any(b<=a for a,b in zip(values,values[1:])):
        raise ValueError('Samples must increase strictly; unordered categories need another layout')
    if label_side not in ('above','below'):
        raise ValueError('label_side must be above or below')
    labels=list(range(len(values))) if labels is None else list(labels)
    if len(set(labels))!=len(labels) or any(type(i) is not int or i<0 or i>=len(values) for i in labels):
        raise ValueError('Label indices must be distinct valid sample indices')
    positions=[[x+v*units,y] for v in values]
    binding=dict(entity=entity,role=role)
    items=[dict(id=ident+'-axis',type='line',points=[[positions[0][0]-marker,y],[positions[-1][0]+marker,y]],stroke=stroke,stroke_width=1,object_part='decoration',**binding)]
    for i,((xx,yy),value) in enumerate(zip(positions,values)):
        logical=f'{ident}-{i}'
        items.append(dict(id=logical,type='rect',x=xx-marker/2,y=yy-marker/2,w=marker,h=marker,fill=fill,stroke=stroke,stroke_width=.9,logical_id=logical,object_part='primary',sample_index=i,sample_value=value,**binding))
        if i in labels:
            ly=yy-marker/2-6 if label_side=='above' else yy+marker/2+label_size+5
            val=value+base
            items.append(dict(id=logical+'-label',type='text',x=xx,y=ly,text=f'{val:g}',size=label_size,align='center',fill=ink,logical_id=logical,object_part='decoration',**binding))
    return {'id':ident,'kind':'sampled_pattern','items':items,'anchors':positions,
            'data':{'values':values,'base':base,'units_per_value':units,'origin':[x,y],
                    'source_pattern':source_pattern,'displayed_indices':labels}}


def branch_bus(ident, *, source, targets, junction_x, source_entity,
               target_entities, meaning, color='#567580', width=.9, head=4,
               arrowheads=_UNSPECIFIED, semantics=None):
    """A shared source with a trunk and caller-selected endpoint semantics.

    Caller chooses anchors and meaning. Targets must be distinct and lie right
    of the trunk. This represents a relation, not a measured transport path.
    New calls choose common_reference, value_mapping, data_flow or motion.
    Common references are undirected; mapping, flow and motion are directed.
    Omitting semantics retains the old reuse/arrow behavior with a warning.
    No automatic routing, hidden obstruction avoidance or aesthetic scoring.
    """
    kinds={'common_reference':'reference','value_mapping':'mapping','data_flow':'flow','motion':'motion'}
    if semantics is None:
        warnings.warn('branch_bus without semantics uses legacy reuse arrows; choose common_reference, value_mapping, data_flow or motion',DeprecationWarning,stacklevel=2)
        kind='reuse';arrowheads=True if arrowheads is _UNSPECIFIED else arrowheads
    else:
        if semantics not in kinds:raise ValueError('Unknown branch semantics: '+str(semantics))
        kind=kinds[semantics];directed=semantics!='common_reference'
        if arrowheads is not _UNSPECIFIED and arrowheads is not directed:
            raise ValueError('Arrowheads conflict with explicit relation semantics')
        arrowheads=directed
    source=list(source);targets=[list(p) for p in targets];target_entities=list(target_entities)
    if len(source)!=2 or not targets or any(len(p)!=2 for p in targets):
        raise ValueError('One source and at least one two-coordinate target required')
    _finite(*source,junction_x,width,head,*(v for p in targets for v in p))
    if type(arrowheads) is not bool:
        raise ValueError('arrowheads must be a boolean')
    if len(target_entities)!=len(targets) or len({tuple(p) for p in targets})!=len(targets):
        raise ValueError('Distinct targets and one entity per target required')
    if not meaning or not source[0]<junction_x or any(p[0]<=junction_x+head for p in targets) or min(width,head)<=0:
        raise ValueError('Provide meaning, positive sizes, and left-to-right routing room')
    ys=[source[1]]+[p[1] for p in targets]
    items=[dict(id=ident+'-stem',type='line',points=[source,[junction_x,source[1]]],stroke=color,stroke_width=width,entity=source_entity,role='shared_relation'),
           dict(id=ident+'-trunk',type='line',points=[[junction_x,min(ys)],[junction_x,max(ys)]],stroke=color,stroke_width=width,entity=source_entity,role='shared_relation')]
    relations=[]
    for i,((x,y),entity) in enumerate(zip(targets,target_entities)):
        rid=f'{ident}-{i}'
        items.append(dict(id=rid,type='line',points=[[junction_x,y],[x,y]],stroke=color,stroke_width=width,relation=rid,role='shared_relation'))
        geometry={'item_id':rid,'from':[junction_x,y],'to':[x,y],'arrow_required':arrowheads}
        if arrowheads:
            items.append(dict(id=rid+'-head',type='polygon',points=[[x,y],[x-head,y-head*.42],[x-head,y+head*.42]],fill=color,stroke=color,stroke_width=0,relation=rid,role='shared_relation'))
            geometry['arrow']={'item_id':rid+'-head','tip':[x,y],'base':[x-head,y]}
        relations.append(dict(id=rid,**{'from':source_entity,'to':entity},kind=kind,meaning=meaning,
                              geometry=geometry))
    return {'id':ident,'kind':'branch_bus','items':items,'relations':relations,
            'anchors':{'source':source,'targets':targets},'data':{'meaning':meaning,'semantics':semantics or 'legacy_reuse','junction_x':junction_x}}

def relation_branch(ident, *, semantics, **geometry):
    """Preferred new-call entry. Relation semantics cannot be omitted.

    branch_bus remains the legacy adapter so old sources can be rebuilt.
    This entry never infers a relation from its free-text meaning or caption.
    """
    if semantics is None:raise ValueError('New relation branches need explicit semantics')
    return branch_bus(ident,semantics=semantics,**geometry)


def relation_path(ident, *, semantics, points, source_entity, target_entity,
                  meaning, label=None, color='#567580', width=.9, head=4,
                  dash=None, role='relation'):
    """An explicitly typed relation on a caller-owned polyline in any direction.

    common_reference has no arrow; value_mapping/data_flow/motion have a head
    aligned with the final segment. Points are layout, not a measured path.
    Optional label is anchored to segment/fraction plus an explicit x/y offset:
    {'text': 'observe', 'segment': 0, 'fraction': .5, 'offset': [0,-8],
     'size': 18, 'align': 'center'}. It retains this relation ID in native text.
    No routing, physical pose inference, text fitting or collision avoidance.
    """
    kinds={'common_reference':'reference','value_mapping':'mapping',
           'data_flow':'flow','motion':'motion'}
    if semantics not in kinds:
        raise ValueError('Choose explicit relation semantics')
    if not all(isinstance(v,str) and v.strip() for v in
               (ident,source_entity,target_entity,meaning)):
        raise ValueError('Relation ID, entity IDs and meaning must be nonempty strings')
    points=[list(p) for p in points]
    if len(points)<2 or any(len(p)!=2 for p in points):
        raise ValueError('A polyline needs at least two 2D points')
    _finite(width,head,*(v for p in points for v in p))
    lengths=[math.dist(a,b) for a,b in zip(points,points[1:])]
    if min(width,head)<=0 or min(lengths)<=0:
        raise ValueError('Positive stroke/head and distinct consecutive points required')
    directed=semantics!='common_reference'
    if directed and lengths[-1]<head:
        raise ValueError('Final segment must fit the arrowhead')
    line=dict(id=ident+'-line',type='line',points=points,stroke=color,
              stroke_width=width,relation=ident,role=role)
    if dash is not None:
        dash=list(dash);_finite(*dash)
        if not dash or min(dash)<=0:raise ValueError('Positive nonempty dash pattern required')
        line['dash']=dash
    items=[line]
    geometry={'item_id':line['id'],'from':points[0],'to':points[-1],
              'arrow_required':directed}
    if directed:
        x,y=points[-1];px,py=points[-2];length=lengths[-1]
        ux,uy=(x-px)/length,(y-py)/length
        base=[x-head*ux,y-head*uy];nx,ny=-uy,ux
        items.append(dict(id=ident+'-head',type='polygon',
            points=[[x,y],[base[0]+head*.42*nx,base[1]+head*.42*ny],
                    [base[0]-head*.42*nx,base[1]-head*.42*ny]],
            fill=color,stroke=color,stroke_width=0,relation=ident,role=role))
        geometry['arrow']={'item_id':ident+'-head','tip':[x,y],'base':base}
    label_binding=None
    if label is not None:
        allowed={'text','segment','fraction','offset','size','align','fill','background','leading'}
        if not isinstance(label,dict) or set(label)-allowed:
            raise ValueError('Label must use the supported binding fields')
        label=dict(label);segment=label.get('segment',0);fraction=label.get('fraction',.5)
        offset=list(label.get('offset',[0,-8]));size=label.get('size',18)
        if type(segment) is not int or not 0<=segment<len(points)-1 or len(offset)!=2:
            raise ValueError('Label needs a valid segment and 2D offset')
        _finite(fraction,size,*offset)
        if not 0<=fraction<=1 or size<=0 or not isinstance(label.get('text'),str) or not label['text'].strip():
            raise ValueError('Label requires text, positive size and fraction in [0,1]')
        align=label.get('align','center')
        if align not in ('left','center','right'):raise ValueError('Unknown label alignment')
        if 'leading' in label:
            _finite(label['leading'])
            if label['leading']<=0:raise ValueError('Positive label leading required')
        a,b=points[segment:segment+2]
        anchor=[a[i]+fraction*(b[i]-a[i]) for i in (0,1)]
        label_binding={'segment':segment,'fraction':fraction,'offset':offset,'anchor':anchor}
        items.append(dict(id=ident+'-label',type='text',text=label['text'],
            x=anchor[0]+offset[0],y=anchor[1]+offset[1],size=size,align=align,
            fill=label.get('fill','#253B44'),background=label.get('background','#FFFFFF'),
            relation=ident,role=role,relation_label_binding=label_binding,
            **({'leading':label['leading']} if 'leading' in label else {})))
    return {'id':ident,'kind':'relation_path','items':items,
        'relations':[dict(id=ident,**{'from':source_entity,'to':target_entity},
                          kind=kinds[semantics],meaning=meaning,geometry=geometry)],
        'anchors':{'source':points[0],'target':points[-1]},
        'data':{'meaning':meaning,'semantics':semantics,'label_binding':label_binding}}


def add_component(scene, component):
    """Append to Scene or JSON without altering its existing fields or APIs."""
    spec=scene.s if hasattr(scene,'s') else scene
    ids={item['id'] for item in spec['items']}
    new=[item['id'] for item in component['items']]
    if len(new)!=len(set(new)) or ids.intersection(new):
        raise ValueError('Component item IDs must be unique in scene')
    spec['items'].extend(component['items'])
    spec.setdefault('relations',[]).extend(component.get('relations',[]))
    spec.setdefault('relation_components',[]).append({k:v for k,v in component.items() if k not in ('items','relations')})
    return component

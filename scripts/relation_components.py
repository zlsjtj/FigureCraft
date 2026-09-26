"""Small editable geometry for sampled patterns and explicit one-to-many links.

Returns the same flat primitive dictionaries used by FigureCraft scenes. It
does not choose a layout, infer reuse, invent an axis break or render a figure.
Caller-owned labels/units/captions distinguish data from physical objects.
"""
from __future__ import annotations
import math


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
               arrowheads=True):
    """A shared source with a trunk and caller-selected endpoint semantics.

    Caller chooses anchors and meaning. Targets must be distinct and lie right
    of the trunk. This represents a relation, not a measured transport path.
    arrowheads=False gives an undirected association without transport cues.
    The default preserves existing callers. A named relation is still required;
    metadata cannot repair a visible arrow that suggests the wrong operation.
    No automatic routing, hidden obstruction avoidance or aesthetic scoring.
    """
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
        relations.append(dict(id=rid,**{'from':source_entity,'to':entity},kind='reuse',meaning=meaning,
                              geometry=geometry))
    return {'id':ident,'kind':'branch_bus','items':items,'relations':relations,
            'anchors':{'source':source,'targets':targets},'data':{'meaning':meaning,'junction_x':junction_x}}


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

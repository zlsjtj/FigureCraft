"""Original two-core cable DEMO. Rebuilds FigureCraft-native editable scenes.

Usage: python build_cable_demo.py --skill-root PATH --font PATH --pdftoppm PATH
       --brief PATH --out NEW_DIRECTORY
All external resources are explicit; existing output is never overwritten.
"""
from pathlib import Path
import argparse, copy, hashlib, json, subprocess, sys

INK = '#23343D'
MUTED = '#465965'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def add(s, ident, kind, **kw):
    s['items'].append(dict(id=ident, type=kind, **kw))

def bind(entity, logical, part='decoration'):
    return dict(entity=entity, logical_id=logical, object_part=part)

def text(s, ident, label, x, y, size=20, align='left'):
    add(s, ident, 'text', text=label, x=x, y=y, size=size,
        align=align, fill=INK, background='#FFFFFF')

def line(s, ident, points, **kw):
    add(s, ident, 'line', points=points, fill='none', stroke=MUTED,
        stroke_width=1.6, **kw)

def gradient(role, y0, y1):
    return dict(kind='linear', x1=0, y1=y0, x2=0, y2=y1,
                stops=[[0, f'@{role}.shadow'], [.19, f'@{role}.highlight'],
                       [.45, f'@{role}.base'], [1, f'@{role}.shadow']])

def capsule(x0, x1, y0, y1, rx):
    return [['M', x0, y0], ['L', x1, y0],
            ['C', x1+rx, y0, x1+rx, y1, x1, y1], ['L', x0, y1],
            ['C', x0-rx, y1, x0-rx, y0, x0, y0], ['Z']]

def make_base(name, briefpath):
    return dict(schema_version=1, figure_id='two_core_cable_DEMO_'+name,
      mode='new_schematic', demo=True,
      evidence_status='Original constructed DEMO; no measured cable or experiment',
      scientific_message='Opening only the outer sheath reveals two intact individual insulation layers.',
      source_refs=[dict(path=str(briefpath.resolve()),sha256=sha(briefpath),
                       kind='User-provided facts frozen for this original DEMO')],
      forbidden_implications=['No third core, shield, twist, current or load',
        'No leakage, thermal, safety, efficiency, performance or innovation evidence',
        'The end section repeats the same cable, not an additional cable',
        'No physical proportions or material properties encoded'],
      entities=[
        dict(id='cable', semantic_role='assembly', description='One two-core cable assembly'),
        dict(id='sheath', semantic_role='sheath', description='One common outer sheath with one local opening'),
        dict(id='insulation', semantic_role='polymer_insulation', description='Two separate intact polymer insulation layers'),
        dict(id='conductors', semantic_role='copper', description='Exactly two copper conductors, hidden in the window'),
        dict(id='section_view', semantic_role='repeated_view', description='End-section diagram of the same cable')],
      relations=[
        dict(id='contains_pair', **{'from':'sheath','to':'insulation'}, kind='containment',
             meaning='The same common sheath surrounds both individual insulation layers'),
        dict(id='individual_wrap', **{'from':'insulation','to':'conductors'}, kind='containment',
             meaning='Each copper conductor has its own separate polymer insulation layer'),
        dict(id='same_cable_view', **{'from':'cable','to':'section_view'}, kind='detail',
             meaning='The end section repeats the same cable; it is not the window or a second specimen',
             arrow_required=False)],
      exact_labels=[],
      locked_values=dict(cables=1, copper_conductors=2, individual_polymer_layers=2,
        common_outer_sheaths=1, local_windows=1, copper_visible_in_window=False,
        insulation_cut_in_window=False, sheath_only_removed=True,
        shield=False, twist=False, third_core=False, current_or_load=False,
        dimensions_and_colors='schematic, not physical measurements'),
      count_constraints=[
        dict(name='outer_sheath', expected=1, scope=dict(entity='sheath'), expected_logical_ids=['S']),
        dict(name='individual_insulation', expected=2, scope=dict(entity='insulation'), expected_logical_ids=['I1','I2']),
        dict(name='copper_conductors', expected=2, scope=dict(entity='conductors'), expected_logical_ids=['C1','C2'])],
      reference_palette='blue_teal_peach',
      role_map=dict(sheath=dict(base='#657985'), cut_edge=dict(base='#B8C4CA'),
        insulation_1=dict(swatch='sky_blue'), insulation_2=dict(swatch='cream'),
        copper=dict(base='#B87443')),
      layout=dict(archetype='window_and_same_object_end_section',
        reading_order='window_then_individual_layers_then_common_sheath' if name=='after' else 'layer_inventory_then_window'),
      depth=dict(mode='D1_shallow_2_5d' if name=='after' else 'D0', affects_quantitative_encoding=False),
      edit_scope=dict(allowed=['Original construction, layout, wording and schematic shades'],
        protected=['Frozen user facts, counts and evidence boundaries']),
      publication=dict(target_journal=None, eligibility='unverified'),
      output=dict(width_mm=160, placement_width_mm=160, view_width=900,
        view_height=380, font_profile='Arial; 10.08 pt main labels; 9.07 pt section qualifier'),
      items=[dict(id='canvas', type='rect', x=0,y=0,w=900,h=380,fill='#FFFFFF')],
      caption='Original DEMO of one two-core cable. The local window removes only the common outer sheath; both polymer insulation layers and both copper conductors remain uncut there. The end-section diagram repeats this same cable to show one copper conductor inside each separate insulation layer, with both enclosed by the common sheath. It is not the opened window. Colors, shapes and proportions are schematic, not measurements. No shield, twist, third core, load or current direction is represented.',
      alt_text='A local opening in one common cable sheath reveals two parallel, smooth insulation surfaces. Copper is not exposed in the window. A separately identified end section of the same cable shows exactly two copper circles, each nested within its own insulation, together inside one sheath.')

def window(s, x0, x1, y0, y1, cut0, cut1, deep):
    """A local SHEATH opening, not a cut through the insulated cores.
    Two uninterrupted side surfaces traverse the window and disappear beneath
    the unremoved jacket. No conductor face is drawn in this function.
    """
    common=bind('sheath','S','primary')
    add(s, 'sheath-body','path',commands=capsule(x0,x1,y0,y1,22),
        fill='@sheath.base',stroke='@sheath.stroke',stroke_width=1.7,
        **({'fill_gradient':gradient('sheath',y0,y1)} if deep else {}), **common)
    wy0=y0+15;wy1=y1-15
    add(s,'window-interior','rect',x=cut0,y=wy0,w=cut1-cut0,h=wy1-wy0,
        radius=6,fill='#253840', **bind('sheath','S'))
    r=(wy1-wy0-20)/4
    centers=[wy0+4+r,wy1-4-r]
    for i,cy in enumerate(centers,1):
        role=f'insulation_{i}'
        add(s,f'window-insulation-{i}','rect',x=cut0,y=cy-r,w=cut1-cut0,h=2*r,
            fill=f'@{role}.base',stroke=f'@{role}.stroke',stroke_width=1,
            **({'fill_gradient':gradient(role,cy-r,cy+r)} if deep else {}),
            **bind('insulation',f'I{i}','primary'))
    # Cut-edge rim is sheath material; it overlays rod ends to communicate
    # that the intact insulated cores continue under the remaining jacket.
    for edge,x in [('left',cut0),('right',cut1-5)]:
        add(s,'window-rim-'+edge,'rect',x=x,y=wy0,w=5,h=wy1-wy0,
            fill='@cut_edge.base',stroke='@sheath.stroke',stroke_width=.7,
            **bind('sheath','S'))
    line(s,'window-rim-top',[[cut0,wy0],[cut1,wy0]],**bind('sheath','S'))
    add(s,'window-rim-bottom','line',points=[[cut0,wy1],[cut1,wy1]],
        stroke='@cut_edge.highlight',stroke_width=3,**bind('sheath','S'))
    if deep:
        add(s,'sheath-high-edge','path',commands=[['M',x0,y0+5],['L',x1,y0+5]],
            fill='none',stroke='@sheath.highlight',stroke_width=1.2,**bind('sheath','S'))
    return centers,wy0,wy1

def section(s,x,y,rx,ry,r):
    """Flat end section; decorative shading is deliberately absent on cut faces."""
    add(s,'same-cable-sheath-section','ellipse',x=x,y=y,rx=rx,ry=ry,
        fill='@sheath.base',stroke='@sheath.stroke',stroke_width=1.6,
        **bind('sheath','S','detail'))
    add(s,'same-cable-interior-section','ellipse',x=x,y=y,rx=rx-9,ry=ry-10,
        fill='#FFFFFF',stroke='@sheath.stroke',stroke_width=1,
        **bind('sheath','S','detail'))
    cy=[y-r-3,y+r+3]
    for i,yy in enumerate(cy,1):
        role=f'insulation_{i}'
        add(s,f'same-cable-insulation-section-{i}','circle',x=x,y=yy,r=r,
            fill=f'@{role}.base',stroke=f'@{role}.stroke',stroke_width=1.3,
            **bind('insulation',f'I{i}','detail'))
        add(s,f'copper-section-{i}','circle',x=x,y=yy,r=r*.49,
            fill='@copper.base',stroke='@copper.stroke',stroke_width=1.4,
            **bind('conductors',f'C{i}','primary'))
    return cy

def before(brief):
    s=make_base('before',brief)
    text(s,'title','Two-core cable structure',26,33,22)
    section(s,136,151,49,83,29)
    text(s,'same-view','Same cable: end section',30,258,18)
    line(s,'sheath-label-line',[[168,89],[231,76],[259,76]])
    text(s,'sheath-label','Common outer sheath',269,83)
    line(s,'ins-label-line',[[162,118],[233,118],[259,123]])
    line(s,'ins-label-line-2',[[162,186],[225,186],[259,123]])
    text(s,'ins-label','Two separate polymer insulation layers',269,130)
    line(s,'copper-label-line',[[148,119],[206,159],[259,171]])
    line(s,'copper-label-line-2',[[148,183],[206,192],[259,171]])
    text(s,'copper-label','Two copper conductors',269,178)
    centers,y0,y1=window(s,349,813,237,346,478,707,False)
    text(s,'window-title','Local window: outer sheath removed',340,220)
    line(s,'window-top-label-line',[[618,224],[618,y0]])
    text(s,'intact-label','Both inner layers remain intact',343,374)
    text(s,'demo','DEMO',26,370,18)
    s['exact_labels']=[x['text'] for x in s['items'] if x['type']=='text']
    return s

def after(brief):
    s=make_base('after',brief)
    s['layout']['archetype']='integrated_window_and_same_cable_end_section'
    s['caption']='Original DEMO of one two-core cable. The local window removes only the common outer sheath; both polymer insulation layers and both copper conductors remain uncut there. The end-section representation at the right shows the same cable: one copper conductor inside each separate insulation layer, with both enclosed by the common sheath. Copper is shown at this sectional end, not at the local window. Colors, shapes and proportions are schematic, not measurements. No shield, twist, third core, load or current direction is represented.'
    text(s,'opening-title','Sheath-only window',350,52,22,align='center')
    text(s,'demo','DEMO',26,28,18)
    centers,y0,y1=window(s,55,713,110,290,170,557,True)
    line(s,'opening-leader',[[350,64],[350,y0]])
    text(s,'outer-label','Common outer sheath',137,331,20,align='center')
    line(s,'outer-leader',[[137,313],[137,292]])
    text(s,'intact-label','Intact polymer insulation',428,331,20,align='center')
    # The repeated section is integrated into the cable end. All faces retain
    # the exact logical IDs of this cable, with flat (not rounded) copper faces.
    text(s,'section-name','End section',719,52,20,align='center')
    text(s,'same-cable','same cable',719,78,18,align='center')
    add(s,'same-cable-sheath-section','ellipse',x=713,y=200,rx=44,ry=90,
        fill='@sheath.base',stroke='@sheath.stroke',stroke_width=1.6,
        **bind('sheath','S','detail'))
    add(s,'same-cable-interior-section','ellipse',x=713,y=200,rx=37,ry=80,
        fill='#FFFFFF',stroke='@sheath.stroke',stroke_width=1,
        **bind('sheath','S','detail'))
    for i,yy in enumerate(centers,1):
        role=f'insulation_{i}'
        add(s,f'same-cable-insulation-section-{i}','ellipse',x=713,y=yy,rx=18,ry=32.5,
            fill=f'@{role}.base',stroke=f'@{role}.stroke',stroke_width=1.3,
            **bind('insulation',f'I{i}','detail'))
        add(s,f'copper-section-{i}','ellipse',x=713,y=yy,rx=8.82,ry=15.925,
            fill='@copper.base',stroke='@copper.stroke',stroke_width=1.3,
            **bind('conductors',f'C{i}','primary'))
    text(s,'copper-label','Copper',818,207,20,align='center')
    line(s,'copper-leader-1',[[790,182],[771,centers[0]],[721,centers[0]]])
    line(s,'copper-leader-2',[[790,218],[771,centers[1]],[721,centers[1]]])
    text(s,'pair-label','Two conductors',716,331,20,align='center')
    s['exact_labels']=[x['text'] for x in s['items'] if x['type']=='text']
    return s

def run(cmd, receipt):
    p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,
                     encoding='utf-8',errors='replace')
    receipt.append(dict(command=[str(x) for x in cmd],exit_code=p.returncode,
                        stdout=p.stdout,stderr=p.stderr))
    return p.returncode

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for arg in ['skill-root','font','pdftoppm','brief','out']:
        ap.add_argument('--'+arg,type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():
        ap.error('Output exists; choose a new directory')
    for p in [a.skill_root/'scripts/render_figure.py',a.font,a.pdftoppm,a.brief]:
        if not p.is_file():ap.error('Missing dependency: '+str(p))
    a.out.mkdir(parents=True)
    receipt=[]
    for name,fn in [('before',before),('after',after)]:
        spec=fn(a.brief)
        save(a.out/(name+'.json'),spec)
        code=run([sys.executable,a.skill_root/'scripts/render_figure.py',
            a.out/(name+'.json'),'--out',a.out/name,'--font',a.font,
            '--pdftoppm',a.pdftoppm,'--placement-width-mm','160','--qa-views'],receipt)
        if code:print(f'{name} render/check exit {code}; retained for review')
    run([sys.executable,a.skill_root/'scripts/compare_designs.py',
         '--baseline',a.out/'before/figure.svg','--candidate',a.out/'after/figure.svg',
         '--placement-width-mm','160','--out',a.out/'comparison'],receipt)
    run([sys.executable,a.skill_root/'scripts/measure_label_load.py',
         a.out/'before/figure.svg','--width-mm','160','--out',a.out/'before/label-load.json'],receipt)
    run([sys.executable,a.skill_root/'scripts/measure_label_load.py',
         a.out/'after/figure.svg','--width-mm','160','--out',a.out/'after/label-load.json'],receipt)
    save(a.out/'commands.json',receipt)
    save(a.out/'build_inputs.json',dict(script_sha256=sha(Path(__file__)),
        skill_root=str(a.skill_root.resolve()),font=dict(path=str(a.font),sha256=sha(a.font)),
        pdftoppm=dict(path=str(a.pdftoppm),sha256=sha(a.pdftoppm)),
        brief=dict(path=str(a.brief.resolve()),sha256=sha(a.brief)),
        dimensions_mm=[160,380/900*160]))
    print(json.dumps(dict(out=str(a.out),commands=len(receipt)),ensure_ascii=False))
    return 0 if all(item['exit_code']==0 for item in receipt) else 1

if __name__=='__main__':raise SystemExit(main())

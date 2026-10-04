"""同一共卷几何的编辑呈现。静态 DEMO，无剥离、场量或实测尺寸。"""
from pathlib import Path
import argparse, base64, hashlib, importlib.util, io, json, math, subprocess, sys
import numpy as np
from PIL import Image, ImageOps
from reportlab.lib.utils import ImageReader


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--skill', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--font', type=Path, required=True)
    ap.add_argument('--bold-font', type=Path, required=True)
    ap.add_argument('--pdftoppm', type=Path, required=True)
    ap.add_argument('--variant', choices=['upright', 'diagonal'], default='diagonal')
    a = ap.parse_args()
    if a.out.exists(): ap.error('输出目录必须尚不存在')
    source = a.skill / 'examples/co-wound-laminate/build_laminate.py'
    spec = importlib.util.spec_from_file_location('base_laminate', source)
    base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
    sys.path.insert(0, str(a.skill / 'scripts'))
    from surface_renderer import render
    a.out.mkdir(parents=True)
    f = base.Drawing(a.out, a.font, a.bold_font)
    faces = base.mesh()  # 原几何逐顶点保留。
    views = []

    def view(fs, direction, box, name, roll=0, px=36):
        v = np.array(direction, float); v /= np.linalg.norm(v)
        r = np.cross([0, 0, 1], v); r /= np.linalg.norm(r)
        u = np.cross(v, r)
        rr = r * math.cos(roll) + u * math.sin(roll)
        uu = u * math.cos(roll) - r * math.sin(roll)
        # 光从画面左上方进入；同一世界光向用于整体及局部。
        light = np.array([-.10, .60, 1.0])
        im, mask, lo, hi, record = render(fs, r, u, v, px_per_unit=px, light=light, ambient=.25)
        # 先按竖直轴光栅化，再在 PDF/SVG 放置时旋转整幅表面。
        # 相机滚转只改变画面朝向，不改变遮挡，避免细长面片的大量空包围盒采样。
        rotation=np.array([[math.cos(roll),-math.sin(roll)],[math.sin(roll),math.cos(roll)]])
        extent=hi-lo
        allpoints=np.concatenate([face['p'] for face in fs])
        rotated=np.column_stack([allpoints@rr,-allpoints@uu])
        rlo=rotated.min(axis=0)-.3;rhi=rotated.max(axis=0)+.3
        rot_extent=rhi-rlo;geometry_centre=(rlo+rhi)/2
        x,y,bw,bh=box;scale=min(bw/rot_extent[0],bh/rot_extent[1])
        centre=np.array([x+bw/2,y+bh/2]);image_centre=centre+(rotation@((lo+hi)/2)-geometry_centre)*scale;wh=extent*scale
        im.save(a.out / (name + '.png')); mask.save(a.out / (name + '-roles.png'))
        f.c.saveState();f.c.translate(image_centre[0],base.H-image_centre[1]);f.c.rotate(-math.degrees(roll))
        f.c.drawImage(ImageReader(im),-wh[0]/2,-wh[1]/2,width=wh[0],height=wh[1],mask='auto');f.c.restoreState()
        buf=io.BytesIO();im.save(buf,format='PNG')
        f.svg.append(f'<image id="{name}" x="{-wh[0]/2}" y="{-wh[1]/2}" width="{wh[0]}" height="{wh[1]}" transform="translate({image_centre[0]},{image_centre[1]}) rotate({math.degrees(roll)})" href="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')
        def project(p):
            p=np.asarray(p);return centre+(np.array([p@rr,-p@uu])-geometry_centre)*scale
        record.update(name=name,box_pt=list(box),native_dpi=im.width/(wh[0]/72),roll_radians=roll,camera={'right':rr.tolist(),'up':uu.tolist(),'view':v.tolist()})
        views.append(record)
        return project

    # 只截取已有顶面、外表面和端面；这是同一尾端的裁切视图。
    def clip_polygon(points, axis, lower):
        out=[]
        for p,q in zip(points, np.roll(points,-1,axis=0)):
            ip=p[axis]>=lower; iq=q[axis]>=lower
            if ip:out.append(p)
            if ip!=iq:
                t=(lower-p[axis])/(q[axis]-p[axis]);out.append(p+t*(q-p))
        return np.array(out)
    local=[]
    for face in faces:
        if not face['role'].startswith('layer'):continue
        pts=clip_polygon(face['p'],1,13.0)
        if len(pts)<3:continue
        pts=clip_polygon(pts,2,22.0)
        if len(pts)<3:continue
        item={k:v for k,v in face.items() if k!='vertex_normals'};item['p']=pts;local.append(item)

    f.text('Three layers. One continuous winding.',14,22,11,True)
    if a.variant=='diagonal':
        p=view(faces,(.70,1.15,.95),(17,50,300,198),'assembly',roll=-.62)
    else:
        p=view(faces,(.65,1.15,1.20),(16,43,275,207),'assembly')
    f.text('Hollow support',15,44,10)
    target=p([3.5,3.7,29]);f.line([(87,42),target],width=.65)
    q=view(local,(1.2,1.7,1.1),(314,109,118,111),'detail',px=100)
    f.text('Same tail, enlarged',301,91,10,True)
    # 局部标签按颜色和端面的实际落点归属，不以另一套示意块代替。
    labels=[]
    for k in range(3):
        point=q([9.6+k*.6+.30,18,22.2]);labels.append((point,k))
    for j,(point,k) in enumerate(sorted(labels,key=lambda v:v[0][0])):
        tx=360+j*25;ty=247
        f.text(chr(65+k),tx-3.4,ty,10,True,color=base.INK)
        f.line([point,(tx,ty-15)],color=base.INK,width=.65)
    corners=[p(v) for v in [[9.6,18,28],[11.4,18,28],[11.4,18,22],[9.6,18,22],[9.6,18,28]]]
    f.line(corners,color='#223C48',width=.6,dash=True)
    f.line([p([11.4,18,28]),(296,103),q([11.4,13,28])],color='#71848B',width=.65,dash=True)
    f.finish()
    subprocess.run([str(a.pdftoppm),'-png','-singlefile','-r','220',str(a.out/'figure.pdf'),str(a.out/'figure')],check=True,capture_output=True)
    im=Image.open(a.out/'figure.png').convert('RGB')
    ImageOps.grayscale(im).save(a.out/'grayscale.png')
    arr=np.asarray(im,dtype=float)/255;mat=np.array([[.625,.375,0],[.7,.3,0],[0,.3,.7]])
    Image.fromarray(np.uint8(np.clip(arr@mat.T,0,1)*255)).save(a.out/'deuteranopia-approx.png')
    caption='Three adjacent layers A (blue), B (gold) and C (coral) follow the same two-turn spiral around a hollow support. The three layers continue together into a straight tangent tail without separation. The enlarged view repeats the marked region of that same tail; it is not an additional set of layers. Geometry and thicknesses are illustrative, with no measured field or performance encoding.'
    (a.out/'caption.txt').write_text(caption+'\n',encoding='utf-8')
    (a.out/'alt.txt').write_text('A hollow co-wound roll continues into one flat three-layer tail. A connected close-up shows the same joined layers, labelled A, B and C.\n',encoding='utf-8')
    # 顶点和材料与旧几何精确相同；不是以投影外观替代对象验收。
    geometry_hash=hashlib.sha256(b''.join(x['p'].tobytes()+x['role'].encode() for x in faces)).hexdigest()
    record={'variant':a.variant,'canvas_mm':[160,95],'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'geometry_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'geometry_sha256':geometry_hash,'surface_renderer_sha256':hashlib.sha256((a.skill/'scripts/surface_renderer.py').read_bytes()).hexdigest(),'actual_objects':['layer-A','layer-B','layer-C','support'],'detail':'same tail, cropped at y=13 and z=22; no extra layer and no added cut face','labels':f.labels,'views':views,'scope':'presentation of existing constructed geometry; no new scientific data','scientific_review':'pending model-assisted inspection','visual_review':'pending model-assisted inspection','author_acceptance':False}
    (a.out/'record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(a.out),'variant':a.variant,'geometry_sha256':geometry_hash}))


if __name__=='__main__':main()

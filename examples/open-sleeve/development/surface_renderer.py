"""Opaque surface rasterization with depth and interpolated/analytic normals.
Only presentation shading; no physical response, measured field or texture.
Faces are independent source polygons; labels never enter this raster layer.
"""
import numpy as np
from PIL import Image

def render(faces,right,up,view,px_per_unit=12,scale=1,*,light=(.25,.65,1),ambient=.40):
    right,up,view=map(np.asarray,[right,up,view])
    if not faces or px_per_unit <= 0 or scale <= 0:
        raise ValueError('Nonempty faces and positive sampling scale required')
    basis=np.array([right,-up,view])
    if not np.allclose(basis@basis.T,np.eye(3),atol=1e-7):
        raise ValueError('Camera axes must be orthonormal unit vectors')
    light=np.asarray(light,dtype=float)
    if light.shape!=(3,) or not np.all(np.isfinite(light)) or np.linalg.norm(light)==0 or not 0<=ambient<=1:
        raise ValueError('Finite nonzero light direction and ambient in [0,1] required')
    light=light/np.linalg.norm(light)
    allp=np.concatenate([f['p'] for f in faces]);screen=allp@basis.T
    lo=screen[:,:2].min(axis=0)-.3;hi=screen[:,:2].max(axis=0)+.3
    sample=px_per_unit*2*scale;wh=np.ceil((hi-lo)*sample).astype(int)
    w,h=wh;depth=np.full((h,w),-np.inf);normal=np.zeros((h,w,3));colors=np.zeros((h,w,3));roles=np.zeros((h,w),dtype=np.uint8)
    role_ids={r:i+1 for i,r in enumerate(sorted({f['role'] for f in faces}))}
    for f in faces:
        points=f['p'];proj=points@basis.T;xy=(proj[:,:2]-lo)*sample
        if f['n']@view<=0:continue
        role=f['role'];color=f.get('base_color',f['color'])
        c=np.array([int(color[j:j+2],16) for j in (1,3,5)])/255
        for k in range(1,len(points)-1):
            ids=[0,k,k+1];q=xy[ids];z=proj[ids,2];p=points[ids]
            low=np.maximum(np.floor(q.min(axis=0)).astype(int),0);high=np.minimum(np.ceil(q.max(axis=0)).astype(int),wh-1)
            if np.any(high<low):continue
            xx,yy=np.meshgrid(np.arange(low[0],high[0]+1)+.5,np.arange(low[1],high[1]+1)+.5)
            x0,y0=q[0];x1,y1=q[1];x2,y2=q[2];den=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(den)<1e-10:continue
            a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/den
            b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/den;cc=1-a-b
            inside=(a>=-1e-8)&(b>=-1e-8)&(cc>=-1e-8)
            zz=a*z[0]+b*z[1]+cc*z[2];sl=np.s_[low[1]:high[1]+1,low[0]:high[0]+1]
            take=inside&(zz>depth[sl]+1e-7)
            localn=np.broadcast_to(f['n'],(*xx.shape,3)).copy()
            if 'vertex_normals' in f:
                vn=np.asarray(f['vertex_normals'])[ids]
                localn=a[...,None]*vn[0]+b[...,None]*vn[1]+cc[...,None]*vn[2]
                localn/=np.maximum(np.linalg.norm(localn,axis=-1,keepdims=True),1e-9)
            depth[sl][take]=zz[take];normal[sl][take]=localn[take];colors[sl][take]=c;roles[sl][take]=role_ids[role]
    intensity=ambient+(1-ambient)*np.maximum(normal@light,0)
    rgb=np.power(np.power(colors,2.2)*intensity[...,None],1/2.2)
    alpha=np.isfinite(depth).astype(float)
    arr=np.dstack([np.clip(rgb*255,0,255),alpha*255]).astype('uint8')
    im=Image.fromarray(arr).resize((int(np.ceil(w/2)),int(np.ceil(h/2))),Image.Resampling.LANCZOS)
    mask=Image.fromarray(roles).resize(im.size,Image.Resampling.NEAREST)
    occupied=np.argwhere(np.isfinite(depth))
    selected=occupied[np.linspace(0,len(occupied)-1,min(400,len(occupied)),dtype=int)] if len(occupied) else []
    samples=[{'xy':(lo+(np.array([x,y])+.5)/sample).tolist(),'depth':float(depth[y,x]),'role_id':int(roles[y,x])} for y,x in selected]
    return im,mask,lo,hi,{'roles':role_ids,'pixels':list(im.size),'native_units_bounds':[lo.tolist(),hi.tolist()],'smooth_normals_roles':sorted({f['role'] for f in faces if 'vertex_normals' in f}),'light':light.tolist(),'projection':'orthographic; maximum depth per sampled ray','sampled_visible_materials':{str(k):int(np.sum(roles==k)) for k in np.unique(roles)},'visibility_samples':samples}

"""Rebuild the supplied teaching DEMO only; no network or external research inputs.

Run with explicit CLI paths. All generated files remain under a new empty --out directory.
The SVG uses editable text and individual vector shapes; the PDF is drawn from the
same primitives, with embedded Arial fonts. No bitmap assets enter the figure.
"""
from pathlib import Path
import argparse, hashlib, json, math, os, subprocess, sys, xml.etree.ElementTree as ET
from html import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
from PIL import Image
import numpy as np

parser = argparse.ArgumentParser(description="Portability rebuild of the fixed dual-channel teaching DEMO; not a fresh scientific generation.")
parser.add_argument("--font",type=Path,required=True,help="Arial regular TTF used by this fixed design")
parser.add_argument("--bold-font",type=Path,required=True,help="Arial bold TTF used by this fixed design")
parser.add_argument("--pdftoppm",type=Path,required=True)
parser.add_argument("--brief",type=Path,required=True)
parser.add_argument("--skill-root",type=Path,required=True,help="FigureCraft skill directory containing SKILL.md and scripts")
parser.add_argument("--out",type=Path,required=True,help="New or empty output directory; existing files are never overwritten")
args = parser.parse_args()
OUT = args.out.resolve()
SKILL_ROOT = args.skill_root.resolve()
BRIEF = args.brief.resolve()
FONT = args.font.resolve()
BOLD = args.bold_font.resolve()
POPPLER = args.pdftoppm.resolve()
for field,path in [("font",FONT),("bold-font",BOLD),("pdftoppm",POPPLER),("brief",BRIEF)]:
    if not path.is_file(): parser.error(f"--{field} must name an existing file: {path}")
for rel in ["SKILL.md","scripts/probe_runtime.py","scripts/audit_svg_labels.py","vendor/nature-figure/audit_pdf_text.py"]:
    if not (SKILL_ROOT/rel).is_file(): parser.error(f"Missing candidate skill file: {SKILL_ROOT/rel}")
if OUT.exists() and (not OUT.is_dir() or any(OUT.iterdir())):
    parser.error(f"Refusing to overwrite a nonempty output directory: {OUT}")
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
sys.dont_write_bytecode=True
MM = 72 / 25.4
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
pdfmetrics.registerFont(TTFont("ArialDemo", str(FONT)))
pdfmetrics.registerFont(TTFont("ArialDemoBold", str(BOLD)))

COL = {
    "ink": "#20353C", "muted": "#53676D", "rule": "#C9D2D4",
    "common": "#AC7418", "common_fill": "#FBEDCB",
    "reference": "#326AAB", "reference_fill": "#DCE9F7",
    "measurement": "#167D79", "measurement_fill": "#DAEFEC",
    "body": "#E6ECEE", "body_side": "#9DADB2", "body_highlight": "#F7F9FA",
    "sample": "#C4E4DB", "sample_side": "#86BFB0",
    "dark_state": "#EFF2F3", "light_state": "#FFF2D6",
    "invalid": "#865043", "white": "#FFFFFF",
}

PARAGRAPH = (
    "An illuminated transmission reading T1 carries both the detector's dark value and changes in source strength. "
    "The DEMO therefore pairs dark subtraction with a reference channel: a single shutter H, placed before splitter B, "
    "blocks light from source S to both detectors when closed. When H opens, B sends one branch directly to reference "
    "detector R and the other through sample P to transmission detector T (Figure 1). The same sample and detectors "
    "remain in place while the two shutter states provide (R0, T0) and (R1, T1). The procedure first checks that the "
    "reference difference R1 − R0 is positive; only then does it compute q = (T1 − T0)/(R1 − R0). Otherwise it returns "
    "INVALID without division. In four constructed cases, doubling both dark-subtracted inputs preserves q = 0.5, "
    "whereas zero and negative reference differences are rejected. These checks establish the stated arithmetic and "
    "invalid-state handling for those inputs. They do not establish absolute transmittance, cancellation of all drift, "
    "or real-instrument accuracy, speed or signal-to-noise performance."
)
ORIGINAL = (
    "The demonstrator comprises a source, a shutter, a splitter, a sample and two detectors. "
    "It acquires dark and illuminated readings and implements subtraction, division and denominator validation. "
    "Four constructed cases check the output and invalid-state handling. The components and software form a complete "
    "dual-channel readout procedure."
)
ALTERNATIVE = (
    "Four constructed inputs test two parts of this DEMO's readout: the valid pairs yield q = 0.5, while zero and "
    "negative reference differences yield INVALID. The readout uses one source S and a shutter H upstream of splitter B, "
    "which feeds reference detector R directly and transmission detector T through sample P. Closing H removes source "
    "light from both branches to obtain R0 and T0; opening it obtains R1 and T1 with P, R and T unchanged. This paired "
    "acquisition makes the dark values explicit and supplies a contemporaneous reference difference for normalization, "
    "rather than comparing T1 alone. Division is allowed only when R1 − R0 > 0, giving q = (T1 − T0)/(R1 − R0); other "
    "cases are rejected. The constructed checks cover these arithmetic cases, without establishing absolute "
    "transmittance or real accuracy, speed, noise performance, or cancellation of all drift."
)
CAPTION = (
    "Figure 1. One optical setup, two shutter states, and a guarded normalized readout. "
    "The upper schematic shows H open: source S illuminates splitter B through shutter H; the reference branch ends "
    "at R, and the measurement branch passes through sample P to T. Optical colors identify routes, not wavelengths. "
    "The lower shutter symbols are state views of the same H, not additional shutters. Closing H blocks source "
    "light to both branches and provides R0 and T0; opening H provides R1 and T1. P, R and T remain fixed in both "
    "states. After ΔR = R1 − R0 is formed, the positivity test precedes division. ΔR ≤ 0 returns INVALID, not zero. "
    "The output q is the DEMO's definition, with no calibration constant; it is not absolute transmittance and does "
    "not guarantee cancellation of all drift. This is an illustrative mechanism, not measured instrument performance; "
    "geometry is schematic and not to scale."
)
ALT = (
    "A single source S sends light rightwards through open shutter H to a tilted splitter B. One arrow turns upwards "
    "to reference detector R. A second continues through sample P to transmission detector T. Below this single layout, "
    "two horizontal acquisition rows show the same shutter closed with R0, T0 and open with R1, T1. The rows converge "
    "on a diamond testing ΔR > 0, where ΔR = R1 − R0. Yes leads to q = (T1 − T0)/ΔR; No leads to INVALID. "
    "Each instrument component appears once in the main layout; only H is repeated in explicitly identified state views."
)

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save_json(name, obj): (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

class Figure:
    def __init__(self, name):
        self.name = name
        self.root = ET.Element(f"{{{NS}}}svg", {"width":"160mm", "height":"90mm", "viewBox":"0 0 160 90", "role":"img"})
        ET.SubElement(self.root, f"{{{NS}}}title").text = "Dual-channel readout teaching DEMO"
        ET.SubElement(self.root, f"{{{NS}}}desc").text = ALT if name == "figure" else "Description-based reconstruction of the supplied previous figure; not a correct algorithm."
        self.c = canvas.Canvas(str(OUT / f"{name}.pdf"), pagesize=(160*MM,90*MM), pageCompression=0, invariant=1)
        self.c.setTitle("Dual-channel readout teaching DEMO")
        self.n = 0

    def elem(self, tag, attrs, meta=None):
        self.n += 1
        attrs = {k: str(v) for k,v in attrs.items()}
        attrs["id"] = attrs.get("id", f"{self.name}-{self.n}")
        attrs.update(meta or {})
        return ET.SubElement(self.root, f"{{{NS}}}{tag}", attrs)

    def paint(self, fill=None, stroke=None, sw=.3):
        if fill: self.c.setFillColor(HexColor(fill))
        if stroke: self.c.setStrokeColor(HexColor(stroke))
        self.c.setLineWidth(sw*MM)

    def rect(self,x,y,w,h,fill,stroke=None,sw=.3,meta=None):
        self.elem("rect",dict(x=x,y=y,width=w,height=h,fill=fill or "none",stroke=stroke or "none", **{"stroke-width":sw}),meta)
        self.paint(fill,stroke,sw)
        self.c.rect(x*MM,(90-y-h)*MM,w*MM,h*MM,fill=bool(fill),stroke=bool(stroke))

    def ellipse(self,x,y,rx,ry,fill,stroke=None,sw=.3,meta=None):
        self.elem("ellipse",dict(cx=x,cy=y,rx=rx,ry=ry,fill=fill or "none",stroke=stroke or "none",**{"stroke-width":sw}),meta)
        self.paint(fill,stroke,sw)
        self.c.ellipse((x-rx)*MM,(90-y-ry)*MM,(x+rx)*MM,(90-y+ry)*MM,fill=bool(fill),stroke=bool(stroke))

    def poly(self, points, fill, stroke=None, sw=.3, meta=None):
        self.elem("polygon",dict(points=" ".join(f"{x},{y}" for x,y in points),fill=fill or "none",stroke=stroke or "none",**{"stroke-width":sw}),meta)
        self.paint(fill,stroke,sw)
        p=self.c.beginPath();p.moveTo(points[0][0]*MM,(90-points[0][1])*MM)
        for x,y in points[1:]:p.lineTo(x*MM,(90-y)*MM)
        p.close();self.c.drawPath(p,fill=bool(fill),stroke=bool(stroke))

    def line(self,x1,y1,x2,y2,color=None,sw=.4,dash=False,meta=None):
        color=color or COL["ink"]
        a=dict(x1=x1,y1=y1,x2=x2,y2=y2,stroke=color,fill="none",**{"stroke-width":sw})
        if dash:a["stroke-dasharray"]="1.1 0.7"
        self.elem("line",a,meta)
        self.paint(None,color,sw)
        self.c.setDash(1.1*MM,.7*MM) if dash else self.c.setDash()
        self.c.line(x1*MM,(90-y1)*MM,x2*MM,(90-y2)*MM)
        self.c.setDash()

    def arrow(self,x1,y1,x2,y2,color=None,sw=.55,dash=False,relation=None):
        color=color or COL["ink"]
        meta={"data-relation":relation,"data-part":"shaft"} if relation else None
        self.line(x1,y1,x2,y2,color,sw,dash,meta)
        dx,dy=x2-x1,y2-y1;n=math.hypot(dx,dy);ux,uy=dx/n,dy/n
        l=1.8;half=.75
        self.poly([(x2,y2),(x2-l*ux+half*uy,y2-l*uy-half*ux),(x2-l*ux-half*uy,y2-l*uy+half*ux)],color,meta={"data-relation":relation or "reading-flow","data-part":"arrowhead"})

    def text(self,x,y,value,size=9.2,bold=False,color=None,anchor="middle",meta=None):
        color=color or COL["ink"]
        attrs={"x":x,"y":y,"font-family":"Arial","font-size":size/MM,"font-weight":"bold" if bold else "normal","fill":color,"text-anchor":anchor}
        e=self.elem("text",attrs,meta);e.text=value
        self.c.setFillColor(HexColor(color));self.c.setFont("ArialDemoBold" if bold else "ArialDemo",size)
        fn={"middle":self.c.drawCentredString,"start":self.c.drawString,"end":self.c.drawRightString}[anchor]
        fn(x*MM,(90-y)*MM,value)

    def save(self):
        ET.indent(self.root)
        ET.ElementTree(self.root).write(OUT / f"{self.name}.svg",encoding="utf-8",xml_declaration=True)
        self.c.showPage();self.c.save()
        subprocess.run([str(POPPLER),"-png","-singlefile","-r","300",str(OUT/f"{self.name}.pdf"),str(OUT/self.name)],check=True,capture_output=True)

def part(logical,which="decoration",state=None):
    d={"data-logical-id":logical,"data-object-part":which,"data-entity":"optical-component"}
    if state:d["data-state"]=state
    return d

def main_figure():
    f=Figure("figure")
    f.rect(0,0,160,90,COL["white"])
    f.text(5,7,"One optical setup · H open",10.2,True,anchor="start")
    f.text(155,7,"DEMO",9.1,True,COL["muted"],"end")
    # Optical bands are route emphasis, not additional rays or components.
    f.line(23,31,69,31,COL["common_fill"],3.2,meta={"data-role":"common-route-highlight"})
    f.line(69,31,69,19,COL["reference_fill"],3.2,meta={"data-role":"reference-route-highlight"})
    f.line(69,31,138,31,COL["measurement_fill"],3.2,meta={"data-role":"measurement-route-highlight"})
    for a,b,r,c in [((23,31),(38.5,31),"S-H","common"),((41.5,31),(69,31),"H-B","common"),((69,31),(69,19),"B-R","reference"),((69,31),(104,31),"B-P","measurement"),((107,31),(138,31),"P-T","measurement")]:
        f.arrow(*a,*b,COL[c],.65,relation=r)
    # S: barrel and single emitting face.
    f.poly([(10,26),(21,26),(23,28),(12,28)],COL["body_highlight"],COL["muted"],.25,part("S"))
    f.rect(10,28,12,7,COL["body"],COL["muted"],.35,part("S","primary"))
    f.poly([(10,35),(22,35),(23,33),(12,33)],COL["body_side"],meta=part("S"))
    f.ellipse(22,31,1.8,4,COL["body_highlight"],COL["muted"],.35,part("S"))
    f.ellipse(22,31,.75,2,COL["common"],meta=part("S"))
    # H: housing with a visible open gap; a blade is retracted upwards.
    f.rect(38.6,24.3,2.8,3.8,COL["body"],COL["muted"],.35,part("H","primary","open"))
    f.rect(38.6,33.7,2.8,4,COL["body"],COL["muted"],.35,part("H"))
    f.rect(40.2,21.7,1.1,5.4,COL["body_side"],COL["muted"],.25,part("H"))
    f.line(38.5,31,41.5,31,COL["common"],.65,meta={"data-role":"open-shutter-through-path"})
    # B: tilted thin plate, with its rear edge attached to its face.
    f.poly([(63.9,35.7),(73.9,25.7),(74.7,26.5),(64.7,36.5)],COL["reference_fill"],COL["reference"],.4,part("B","primary"))
    f.line(64.7,36.5,74.7,26.5,COL["reference"],.6,meta=part("B"))
    # P: one solid sample slab, light front with a darker side.
    f.poly([(103.5,25),(107,26),(107,38),(103.5,37)],COL["sample"],COL["measurement"],.35,part("P","primary"))
    f.poly([(107,26),(108.6,24.6),(108.6,36.6),(107,38)],COL["sample_side"],COL["measurement"],.25,part("P"))
    f.poly([(103.5,25),(105.1,23.6),(108.6,24.6),(107,26)],COL["body_highlight"],COL["measurement"],.25,part("P"))
    # Detectors: one housing per detector, active faces oriented toward their branch.
    f.rect(64,11,10,7,COL["body"],COL["muted"],.35,part("R","primary"))
    f.poly([(64,11),(66,9.8),(76,9.8),(74,11)],COL["body_highlight"],COL["muted"],.25,part("R"))
    f.poly([(74,11),(76,9.8),(76,16.8),(74,18)],COL["body_side"],COL["muted"],.25,part("R"))
    f.rect(65,18,8,1.1,COL["reference"],meta=part("R"))
    f.text(80,15.7,"Reference R",9.3,False,anchor="start")
    f.rect(138,26,10,10,COL["body"],COL["muted"],.35,part("T","primary"))
    f.poly([(138,26),(140,24.7),(150,24.7),(148,26)],COL["body_highlight"],COL["muted"],.25,part("T"))
    f.poly([(148,26),(150,24.7),(150,34.7),(148,36)],COL["body_side"],COL["muted"],.25,part("T"))
    f.rect(137.4,27,1.2,8,COL["measurement"],meta=part("T"))
    for x,label in [(17,"Source S"),(40,"Shutter H"),(69,"Splitter B"),(106,"Sample P"),(141,"Detector T")]: f.text(x,44,label,9.1)
    f.line(5,49.5,155,49.5,COL["rule"],.25)
    f.text(5,55.6,"Two readings · same P, R and T",9.6,True,anchor="start")
    f.text(114,56.2,"ΔR = R1 − R0",10.2,True)
    # Paired acquisition rows. The miniature shutter symbols are state views of H.
    for y,closed in [(62.3,True),(75.0,False)]:
        f.rect(5,y,54,9.5,COL["dark_state"] if closed else COL["light_state"])
        f.text(17,y+6,"H closed" if closed else "H open",9.1,anchor="start")
        f.text(48.7,y+6,"R0, T0" if closed else "R1, T1",10.1)
        f.line(7,y+4.8,10.3,y+4.8,COL["common"],.55)
        if closed:
            f.rect(10.3,y+1.9,1.3,5.6,COL["muted"],meta=part("H","detail","closed"))
        else:
            f.rect(10.3,y+.8,1.3,2.1,COL["muted"],meta=part("H","detail","open"))
            f.arrow(10.3,y+4.8,14.6,y+4.8,COL["common"],.55)
    f.line(59,67.1,64.0,67.1,COL["muted"],.4)
    f.line(59,79.8,64.0,79.8,COL["muted"],.4)
    f.line(64,67.1,64,79.8,COL["muted"],.4)
    f.arrow(64,69.5,75.5,69.5,COL["muted"],.5)
    f.poly([(75.5,69.5),(87.5,62.0),(99.5,69.5),(87.5,77)],COL["body_highlight"],COL["muted"],.4,{"data-operation":"validate-before-division"})
    f.text(87.5,70.6,"ΔR > 0",10,True)
    f.arrow(99.5,69.5,115.0,69.5,COL["muted"],.45,True,relation="valid-to-divide")
    f.text(107,65.9,"Yes",9.0)
    f.text(121,70.7,"q =",11)
    f.text(141,65.8,"T1 − T0",10.4)
    f.line(130.8,68,151.2,68,COL["ink"],.35)
    f.text(141,73,"ΔR",10.4)
    f.line(87.5,77,87.5,85,COL["invalid"],.45,True)
    f.arrow(87.5,85,116,85,COL["invalid"],.45,True,relation="invalid-no-division")
    f.text(101,81.6,"No",9.0,color=COL["invalid"])
    f.text(135,86.0,"INVALID",10.1,True,COL["invalid"])
    f.save()

def baseline():
    f=Figure("baseline_reconstructed")
    f.rect(0,0,160,90,COL["white"])
    f.text(5,7,"Reconstructed previous layout",10.2,True,anchor="start")
    def box(x,y,w,label):
        f.rect(x,y,w,12,COL["body_highlight"],COL["muted"],.35)
        lines=label.split("\n")
        for i,t in enumerate(lines):f.text(x+w/2,y+7+(i-(len(lines)-1)/2)*3.7,t,8.6)
    box(5,26,24,"Source");box(38,26,24,"Shutter");box(71,26,24,"Splitter")
    f.arrow(29,32,38,32,COL["muted"]);f.arrow(62,32,71,32,COL["muted"])
    f.line(95,32,102,32,COL["muted"]);f.line(102,19,102,44,COL["muted"])
    f.arrow(102,19,118,19,COL["muted"]);box(118,13,37,"Reference\ndetector")
    f.arrow(102,44,106,44,COL["muted"]);box(106,38,19,"Sample")
    f.arrow(125,44,130,44,COL["muted"]);box(130,38,25,"Transmission\ndetector")
    for i,t in enumerate(["Dark\nreadings","Light\nreadings","Subtract","Divide","Check\ndenominator"]):
        x=5+i*31;box(x,65,26,t)
        if i<4:f.arrow(x+26,71,x+31,71,COL["muted"],.4)
    f.text(5,86,"Comparison only: description-based, not an original image file.",8.2,color=COL["muted"],anchor="start")
    f.save()

def qa_previews():
    im=Image.open(OUT/"figure.png").convert("RGB")
    a=np.asarray(im).astype(float)/255
    lin=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
    lum=lin@np.array([.2126,.7152,.0722])
    def srgb(v):return np.where(v<=.0031308,12.92*v,1.055*np.maximum(v,0)**(1/2.4)-.055)
    gray=np.repeat(srgb(lum)[...,None],3,axis=-1)
    # Machado et al. severity-100 deuteranomaly approximation; one condition only.
    mat=np.array([[.367322,.860646,-.227968],[.280085,.672501,.047413],[-.011820,.042940,.968881]])
    cvd=srgb(np.clip(lin@mat.T,0,1))
    for name,data in [("figure_grayscale",gray),("figure_deuteranomaly",cvd)]:
        Image.fromarray(np.uint8(np.clip(data,0,1)*255+.5)).save(OUT/f"{name}.png",dpi=(300,300))
    im.resize((605,340),Image.Resampling.LANCZOS).save(OUT/"figure_160mm_96dpi.png",dpi=(96,96))

CASES=[dict(R0=2,T0=3,R1=12,T1=8,expected=.5),dict(R0=2,T0=3,R1=22,T1=13,expected=.5),dict(R0=2,T0=3,R1=2,T1=8,expected="INVALID"),dict(R0=2,T0=3,R1=1,T1=8,expected="INVALID")]
def readout(R0,T0,R1,T1):
    delta=R1-R0
    if delta<=0:return "INVALID",False
    return (T1-T0)/delta,True

def checks():
    root=ET.parse(OUT/"figure.svg").getroot()
    primary=[e.get("data-logical-id") for e in root.iter() if e.get("data-object-part")=="primary"]
    assert sorted(primary)==["B","H","P","R","S","T"]
    expected_edges={"S-H":((23,31),(38.5,31)),"H-B":((41.5,31),(69,31)),"B-R":((69,31),(69,19)),"B-P":((69,31),(104,31)),"P-T":((107,31),(138,31))}
    checked=[]
    for r,(start,end) in expected_edges.items():
        shaft=[e for e in root.iter() if e.get("data-relation")==r and e.get("data-part")=="shaft"]
        heads=[e for e in root.iter() if e.get("data-relation")==r and e.get("data-part")=="arrowhead"]
        assert len(shaft)==len(heads)==1
        s=shaft[0];actual=(float(s.get("x1")),float(s.get("y1")),float(s.get("x2")),float(s.get("y2")))
        assert actual==(*start,*end)
        pts=[tuple(map(float,p.split(","))) for p in heads[0].get("points").split()]
        assert pts[0]==end
        avg=((pts[1][0]+pts[2][0])/2,(pts[1][1]+pts[2][1])/2)
        assert (end[0]-avg[0])*(end[0]-start[0])+(end[1]-avg[1])*(end[1]-start[1])>0
        checked.append(r)
    pdf=PdfReader(OUT/"figure.pdf");page=pdf.pages[0]
    texts=[e for e in root.iter() if e.tag.endswith("}text")]
    sizes=[float(e.get("font-size"))*MM for e in texts]
    missing=[]
    for e in texts:
        font=pdfmetrics.getFont("ArialDemoBold" if e.get("font-weight")=="bold" else "ArialDemo")
        missing.extend(c for c in (e.text or "") if ord(c) not in font.face.charToGlyph)
    assert not missing
    assert min(sizes)>=9
    dims=[round(float(page.mediabox.width)/MM,3),round(float(page.mediabox.height)/MM,3)]
    assert dims==[160,90]
    pdftext=page.extract_text()
    assert "INVALID" in pdftext and "Reference R" in pdftext and "R1" in pdftext
    image_objects=[]
    for k,v in page["/Resources"].get("/XObject",{}).items():
        if v.get_object().get("/Subtype")=="/Image":image_objects.append(k)
    assert not image_objects
    tested=[]
    for row in CASES:
        got,divided=readout(**{k:row[k] for k in ("R0","T0","R1","T1")})
        assert got==row["expected"]
        tested.append(dict(**row,delta_R=row["R1"]-row["R0"],delta_T=row["T1"]-row["T0"],actual=got,division_executed=divided))
    save_json("logic_checks.json",dict(evidence="Four constructed inputs supplied in brief.md; not measurements",cases=tested))
    save_json("technical_checks.json",dict(
        technical_status="PASS",figure_sha256=sha(OUT/"figure.svg"),pdf_sha256=sha(OUT/"figure.pdf"),png_sha256=sha(OUT/"figure.png"),
        dimensions_mm=dims,png_px=list(Image.open(OUT/"figure.png").size),
        primary_objects=primary,expected_primary_objects=["S","H","B","P","R","T"],optical_relations_checked=checked,
        extra_physical_instances="Two explicitly marked H state views; no extra source, splitter, sample or detector",
        smallest_figure_text_pt=min(sizes),missing_glyphs=missing,svg_bitmap_count=len(root.findall(f".//{{{NS}}}image")),pdf_bitmap_objects=image_objects,
        pdf_searchable_text=pdftext,
        checks_scope="Actual SVG object IDs, line endpoints, arrowhead directions, text glyph coverage, physical dimensions, PDF text, raster exclusion, four constructed arithmetic cases",
        not_covered=["General SVG collision analysis","Independent scientific review","Human-reader improvement","Cross-editor rendering","Physical apparatus","Author acceptance"],
        scientific_review_status="REVIEW_REQUIRED",visual_review_status="REVIEW_REQUIRED",overall_status="REVIEW_REQUIRED"))

def text_artifacts():
    (OUT/"revised_paragraph.txt").write_text(PARAGRAPH+"\n",encoding="utf-8")
    (OUT/"caption.txt").write_text(CAPTION+"\n",encoding="utf-8")
    (OUT/"alt_text.txt").write_text(ALT+"\n",encoding="utf-8")
    (OUT/"manuscript.md").write_text(PARAGRAPH+"\n\n![Dual-channel readout](figure.png)\n\n"+CAPTION+"\n",encoding="utf-8")
    (OUT/"paragraph_comparison.md").write_text("# 局部叙事对照\n\n## 原段落\n\n"+ORIGINAL+"\n\n## 候选 A：从读数问题进入（选用）\n\n"+PARAGRAPH+"\n\n## 候选 B：从检查结果进入（未选）\n\n"+ALTERNATIVE+"\n\n选择 A：面对尚不了解装置的读者，先提出 T1 所混合的两类因素，再解释 H 的位置及参考支路，避免读者在尚不知 R/T 含义时先处理四个结果。B 的检查范围更早出现，但装置动机延后。A 比原段长，代价是增加篇幅；增加的内容来自任务书已有事实，没有新增实验或创新结论。\n",encoding="utf-8")
    html="""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>DEMO 图文审阅</title>
    <style>body{font:16px/1.7 Arial,'Microsoft YaHei',sans-serif;max-width:980px;margin:35px auto;color:#20353c}p{max-width:850px}img{width:160mm;height:90mm;display:block;border:1px solid #ddd;margin:16px 0}mark{background:#fff1a6}h2{font-size:19px;margin-top:30px}.cap{font-size:15px}small{font-size:14px}</style>
    <h1>双通道透射读出 DEMO：局部修订候选</h1><p>黄色为本轮重写文本；未生成 Word 原生修订。图像按 160 × 90 mm CSS 尺寸并列于同一审阅页。屏幕真实毫米取决于显示器与浏览器缩放。</p>
    <h2>原段落</h2><p>"""+escape(ORIGINAL)+"</p><h2>实际改写</h2><p><mark>"+escape(PARAGRAPH)+"</mark></p><h2>旧图描述的重建</h2><p>任务书未附旧图文件。此图仅复现已描述的矩形流程及原有错误次序，供比较；不是原作截图。</p><img src='baseline_reconstructed.png'><h2>候选图</h2><img src='figure.svg'><p class='cap'>"+escape(CAPTION)+"</p><h2>灰度与单一色觉模拟</h2><img src='figure_grayscale.png'><img src='figure_deuteranomaly.png'><p><small>模拟为 Machado severity 100 deuteranomaly 近似，仅覆盖这一条件；不代表所有色觉条件或真实打印认证。</small></p></html>"
    (OUT/"review.html").write_text(html,encoding="utf-8")
    save_json("figure_spec.json",dict(
        title="Dual-channel readout teaching DEMO",source=dict(path=str(BRIEF),sha256=sha(BRIEF)),
        evidence_status="Constructed teaching DEMO only",output=dict(width_mm=160,height_mm=90,placement_width_mm=160),
        figure_question="How does one upstream shutter yield two paired channel readings, and when may their differences be divided?",
        entities=[dict(id=k,primary_count=1) for k in ["S","H","B","P","R","T"]],
        main_view_state="H open",state_views=[dict(id="H",state="closed",source_light_to_R=False,source_light_to_T=False),dict(id="H",state="open",source_light_to_R=True,source_light_to_T=True)],
        fixed_between_states=["P","R","T"],
        directed_optical_edges=[["S","H"],["H","B"],["B","R"],["B","P"],["P","T"]],
        prohibited=["second source","feedback loop","reflection-return loop","motion of P/R/T between states","division before denominator validation","invalid converted to zero","absolute transmittance claim"],
        locked_values=CASES,equation="q=(T1-T0)/(R1-R0) if R1-R0>0, otherwise INVALID without division",calibration_constant=None,
        depth="D1: editable shallow vector side faces on optical objects; no measured geometry or D2 model",role_colors=COL,
        text=dict(font=str(FONT),bold_font=str(BOLD),minimum_pt=9.0),
        svg_backend="Custom editable native SVG; no claim to scene-engine PASS",pdf_backend="ReportLab vector primitives with embedded fonts",caption=CAPTION,alt_text=ALT))

def manifest():
    dependencies=["SKILL.md","scripts/probe_runtime.py","scripts/audit_svg_labels.py","vendor/nature-figure/audit_pdf_text.py"]
    save_json("dependency_manifest.json",dict(task_input=dict(path=str(BRIEF),sha256=sha(BRIEF)),files=[dict(path=str(SKILL_ROOT/p),sha256=sha(SKILL_ROOT/p),access="executed by rebuild" if p!="SKILL.md" else "hash only; not evidence of model skill loading") for p in dependencies],fonts=[dict(path=str(p),sha256=sha(p)) for p in [FONT,BOLD]],note="Fixed-artifact rebuild. Does not run the PaperCraft editor or generate a new scientific design."))
    save_json("artifact_manifest.json",dict(python=sys.executable,script=dict(path=str(Path(__file__).resolve()),sha256=sha(__file__)),source_sha256=sha(BRIEF),purpose="fixed DEMO rebuild only",files={str(p.relative_to(OUT)):sha(p) for p in OUT.iterdir() if p.is_file() and p.name!="artifact_manifest.json"}))

def external_audits():
    commands=[
        [sys.executable,str(SKILL_ROOT/"scripts/audit_svg_labels.py"),str(OUT/"figure.svg"),"--font",str(FONT),"--bold-font",str(BOLD),"--placement-width-mm","160","--out",str(OUT/"label_audit.json")],
        [sys.executable,str(SKILL_ROOT/"vendor/nature-figure/audit_pdf_text.py"),str(OUT/"figure.pdf"),"--min-pt","8","--json"],
    ]
    receipt=[]
    for i,command in enumerate(commands):
        run=subprocess.run(command,capture_output=True,text=True,encoding="utf-8")
        receipt.append(dict(command=command,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr))
        if i==1 and run.returncode==0:save_json("pdf_text_audit.json",json.loads(run.stdout))
        if run.returncode!=0:raise RuntimeError(f"Audit {i} failed: {run.stderr} {run.stdout}")
    save_json("audit_commands.json",receipt)
    font_results=[]
    for name,entry in PdfReader(OUT/"figure.pdf").pages[0]["/Resources"]["/Font"].items():
        entry=entry.get_object(); desc=entry.get("/FontDescriptor")
        embedded=False
        if desc:
            d=desc.get_object();embedded=any(k in d for k in ["/FontFile","/FontFile2","/FontFile3"])
        font_results.append(dict(resource=name,base_font=str(entry.get("/BaseFont")),embedded=embedded))
    # ReportLab lists an unused built-in font too; the actual Arial subsets must be embedded.
    actual_arial=[r for r in font_results if "Arial" in r["base_font"]]
    assert len(actual_arial)==2 and all(r["embedded"] for r in actual_arial)
    save_json("pdf_fonts.json",dict(fonts=font_results,actual_Arial_fonts_embedded=True))

if __name__=="__main__":
    OUT.mkdir(parents=True,exist_ok=True)
    probe=[sys.executable,str(SKILL_ROOT/"scripts/probe_runtime.py"),"--font",str(FONT),"--pdftoppm",str(POPPLER),"--out",str(OUT/"runtime.json")]
    probe_run=subprocess.run(probe,capture_output=True,text=True,encoding="utf-8")
    save_json("runtime_probe_command.json",dict(command=probe,exit_code=probe_run.returncode,stdout=probe_run.stdout,stderr=probe_run.stderr))
    if probe_run.returncode!=0:raise RuntimeError("Runtime probe failed; see runtime_probe_command.json")
    main_figure();baseline();qa_previews();text_artifacts();checks();external_audits();manifest()
    print(json.dumps({"generated":"SVG, vector PDF, PNG, paired previews, text, editable source, checks", "out":str(OUT),"technical":"PASS","overall":"REVIEW_REQUIRED"},ensure_ascii=False))

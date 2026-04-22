"""
Rebuild the English PPTX with everything in BLACK:
- Emblem with one circle only (remove gray ring)
- All 8 small icons redrawn in black
- All text colors changed to black
- All line shapes changed to black
"""
import io
import math
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE

SRC = Path(__file__).resolve().parent / "mapa_curricular_english_v3.pptx"
DST = Path(__file__).resolve().parent / "mapa_curricular_english_black.pptx"

BLACK = (30, 30, 30)
BLACK_RGBA = (30, 30, 30, 255)
BG = (0, 0, 0, 0)
ICON_SIZE = 512
LW = 18


def _canvas():
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), BG)
    return img, ImageDraw.Draw(img)


# ── Emblem: single circle + text ──
def icon_emblem():
    W, H = 2116, 2016
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    outer_r = 880
    inner_r = 840
    # Single circle ring
    d.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], fill=BLACK_RGBA)
    d.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=(255, 255, 255, 255))
    # Text
    fp = r"C:\Windows\Fonts\arialbd.ttf"
    if not os.path.exists(fp):
        fp = r"C:\Windows\Fonts\arial.ttf"
    font = ImageFont.truetype(fp, 195)
    for txt, y_off in [("Aerospace", -160), ("Engineering", 50)]:
        bb = d.textbbox((0, 0), txt, font=font)
        w = bb[2] - bb[0]
        d.text((cx - w // 2, cy + y_off), txt, fill=BLACK_RGBA, font=font)
    return img


# ── Small icons (same designs as before, but BLACK) ──
def icon_credits():
    img, d = _canvas()
    cx, cy = 256, 200
    r = 100
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=BLACK, width=LW)
    pts = []
    for i in range(5):
        a = math.radians(-90 + i*72)
        pts.append((cx+int(70*math.cos(a)), cy+int(70*math.sin(a))))
    star = []
    for i in range(5):
        star.append(pts[i])
        ma = math.radians(-90 + i*72 + 36)
        star.append((cx+int(30*math.cos(ma)), cy+int(30*math.sin(ma))))
    d.polygon(star, outline=BLACK, width=LW//2)
    d.line([cx-50, cy+r, cx-90, cy+r+140], fill=BLACK, width=LW)
    d.line([cx-50, cy+r, cx-20, cy+r+80], fill=BLACK, width=LW//2)
    d.line([cx+50, cy+r, cx+90, cy+r+140], fill=BLACK, width=LW)
    d.line([cx+50, cy+r, cx+20, cy+r+80], fill=BLACK, width=LW//2)
    return img


def icon_semesters():
    img, d = _canvas()
    x0, y0, x1, y1 = 80, 100, 432, 432
    d.rounded_rectangle([x0, y0, x1, y1], radius=24, outline=BLACK, width=LW)
    d.rectangle([x0, y0, x1, y0+70], outline=BLACK, fill=BLACK)
    for rx in [170, 256, 342]:
        d.line([rx, y0-30, rx, y0+30], fill=BLACK, width=LW)
    for gy in range(210, 420, 55):
        d.line([x0+30, gy, x1-30, gy], fill=BLACK, width=LW//3)
    for gx in range(160, 420, 70):
        d.line([gx, 195, gx, 410], fill=BLACK, width=LW//3)
    return img


def icon_basic_sciences():
    img, d = _canvas()
    cx, cy = 256, 256
    d.ellipse([cx-22, cy-22, cx+22, cy+22], fill=BLACK)
    for angle_deg in [0, 60, 120]:
        a = math.radians(angle_deg)
        pts = []
        for t in range(0, 360, 3):
            tr = math.radians(t)
            ex = 160*math.cos(tr); ey = 55*math.sin(tr)
            rx = ex*math.cos(a) - ey*math.sin(a)
            ry = ex*math.sin(a) + ey*math.cos(a)
            pts.append((cx+int(rx), cy+int(ry)))
        for i in range(len(pts)-1):
            d.line([pts[i], pts[i+1]], fill=BLACK, width=LW//2)
        d.line([pts[-1], pts[0]], fill=BLACK, width=LW//2)
    return img


def icon_social_sciences():
    img, d = _canvas()
    d.ellipse([226, 80, 286, 140], outline=BLACK, width=LW)
    d.arc([186, 150, 326, 290], 0, 180, fill=BLACK, width=LW)
    d.ellipse([106, 120, 156, 170], outline=BLACK, width=LW-4)
    d.arc([76, 180, 186, 300], 0, 180, fill=BLACK, width=LW-4)
    d.ellipse([356, 120, 406, 170], outline=BLACK, width=LW-4)
    d.arc([326, 180, 436, 300], 0, 180, fill=BLACK, width=LW-4)
    d.arc([100, 260, 412, 420], 0, 180, fill=BLACK, width=LW//2)
    return img


def icon_engineering_sciences():
    img, d = _canvas()
    cx, cy = 230, 230
    teeth = 8
    for i in range(teeth):
        a = math.radians(i*360/teeth)
        x1 = cx+int(120*math.cos(a)); y1 = cy+int(120*math.sin(a))
        d.rectangle([x1-20, y1-20, x1+20, y1+20], fill=BLACK)
    d.ellipse([cx-100, cy-100, cx+100, cy+100], outline=BLACK, width=LW)
    d.ellipse([cx-40, cy-40, cx+40, cy+40], outline=BLACK, width=LW)
    d.line([330, 330, 440, 440], fill=BLACK, width=LW+4)
    d.ellipse([300, 300, 370, 370], outline=BLACK, width=LW)
    return img


def icon_economics():
    img, d = _canvas()
    d.line([100, 400, 100, 80], fill=BLACK, width=LW)
    d.line([100, 400, 430, 400], fill=BLACK, width=LW)
    bars = [(140, 320), (210, 250), (280, 180), (350, 130)]
    for bx, by in bars:
        d.rectangle([bx, by, bx+50, 400], outline=BLACK, width=LW//2)
    d.line([150, 340, 390, 120], fill=BLACK, width=LW//2)
    d.polygon([(390, 120), (360, 140), (370, 110)], fill=BLACK)
    return img


def icon_applied_eng():
    img, d = _canvas()
    cx, cy = 256, 200
    d.ellipse([cx-90, cy-120, cx+90, cy+60], outline=BLACK, width=LW)
    d.line([cx-25, cy-40, cx, cy-70, cx+25, cy-40], fill=BLACK, width=LW//2)
    d.rectangle([cx-45, cy+60, cx+45, cy+120], outline=BLACK, width=LW)
    d.line([cx-45, cy+80, cx+45, cy+80], fill=BLACK, width=LW//3)
    d.line([cx-45, cy+100, cx+45, cy+100], fill=BLACK, width=LW//3)
    gcx, gcy = 370, 370; gr = 55
    d.ellipse([gcx-gr, gcy-gr, gcx+gr, gcy+gr], outline=BLACK, width=LW-4)
    d.ellipse([gcx-20, gcy-20, gcx+20, gcy+20], outline=BLACK, width=LW-4)
    for i in range(6):
        a = math.radians(i*60)
        tx = gcx+int((gr+12)*math.cos(a)); ty = gcy+int((gr+12)*math.sin(a))
        d.rectangle([tx-10, ty-10, tx+10, ty+10], fill=BLACK)
    return img


def icon_other_courses():
    img, d = _canvas()
    d.polygon([(256,130),(80,100),(80,390),(256,400)], outline=BLACK, width=LW)
    d.polygon([(256,130),(432,100),(432,390),(256,400)], outline=BLACK, width=LW)
    d.line([256, 130, 256, 400], fill=BLACK, width=LW)
    for ly in range(190, 370, 40):
        d.line([120, ly, 230, ly+10], fill=BLACK, width=LW//4)
    for ly in range(190, 370, 40):
        d.line([282, ly+10, 400, ly], fill=BLACK, width=LW//4)
    d.polygon([(370,100),(370,220),(390,195),(410,220),(410,100)], outline=BLACK, width=LW//3)
    return img


SHAPE_ICON_MAP = {
    "Picture 74": icon_credits,
    "Picture 77": icon_semesters,
    "Picture 80": icon_basic_sciences,
    "Picture 82": icon_social_sciences,
    "Picture 84": icon_engineering_sciences,
    "Picture 86": icon_economics,
    "Picture 88": icon_applied_eng,
    "Picture 90": icon_other_courses,
}


def img_to_bytes(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def replace_blob(shape, png_bytes):
    rel = shape.part.rels[shape._element.blipFill.blip.get(
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
    )]
    rel.target_part._blob = png_bytes


def main():
    print("Loading PPTX...")
    prs = Presentation(str(SRC))

    BLACK_RGB = RGBColor(30, 30, 30)

    # 1) Replace emblem
    emblem_bytes = img_to_bytes(icon_emblem())

    # 2) Replace small icons + emblem
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name == "Picture 56":
                replace_blob(shape, emblem_bytes)
                print("  Replaced emblem -> black single circle")
            elif shape.name in SHAPE_ICON_MAP:
                gen = SHAPE_ICON_MAP[shape.name]
                replace_blob(shape, img_to_bytes(gen()))
                print(f"  Replaced {shape.name} -> black")

    # 3) Change all text to black
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        run.font.color.rgb = BLACK_RGB
                        run.font.name = "Arial"

    # 4) Change all line/rectangle shape fills and outlines to black
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                try:
                    if shape.fill.type is not None:
                        shape.fill.solid()
                        shape.fill.fore_color.rgb = BLACK_RGB
                    shape.line.color.rgb = BLACK_RGB
                except Exception:
                    pass

    prs.save(str(DST))
    print(f"\nSaved: {DST}")


if __name__ == "__main__":
    main()

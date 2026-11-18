"""Render a small Thai test page (PNG + 2-page PDF) into samples/, using a Thai system font.

Usage: .venv/bin/python scripts/make_sample.py

Pillow without libraqm (the default macOS wheel) cannot stack a tone mark on an upper
vowel, so e.g. "เพื่อ" is drawn as "เพือ". Use real documents to judge accuracy.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "samples"
FONTS = [
    "/System/Library/Fonts/Supplemental/Tahoma.ttf",
    "/System/Library/Fonts/Thonburi.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/tlwg/Garuda.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
]

LINES = [
    "บันทึกข้อความ",
    "ส่วนราชการ  สำนักงานหลักประกันสุขภาพแห่งชาติ",
    "ที่  สปสช. 1234/2569        วันที่  12 พฤศจิกายน 2569",
    "เรื่อง  ขออนุมัติเดินทางไปราชการ",
    "เรียน  เลขาธิการสำนักงานหลักประกันสุขภาพแห่งชาติ",
    "ด้วยข้าพเจ้าได้รับมอบหมายให้เข้าร่วมประชุมเชิงปฏิบัติการ",
    "ระหว่างวันที่ 20 - 22 พฤศจิกายน 2569 ณ จังหวัดเชียงใหม่",
    "จึงเรียนมาเพื่อโปรดพิจารณาอนุมัติ",
    "OCR test: Thai and English 0123456789",
]


def font(size):
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    raise SystemExit("No Thai font found; edit FONTS in scripts/make_sample.py")


def page(lines):
    img = Image.new("RGB", (1654, 1100), "white")  # A4 width at 200 dpi
    d = ImageDraw.Draw(img)
    f = font(40)
    y = 80
    for text in lines:
        d.text((120, y), text, fill="black", font=f)
        y += 100
    return img


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    first = page(LINES)
    first.save(OUT / "thai_letter.png")
    second = page(LINES[::-1])
    first.save(OUT / "thai_letter.pdf", "PDF", resolution=200, save_all=True, append_images=[second])
    print("Wrote", OUT / "thai_letter.png", "and", OUT / "thai_letter.pdf")

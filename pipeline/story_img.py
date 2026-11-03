"""단신용 스토리 이미지: python3 pipeline/story_img.py <01.jpg> <story.jpg> "KIT 0NN" [브랜드명]
카드 01을 1080x1920 어두운 바탕 가운데에 원본 비율로 놓고, 아래에 '피드에서 자세히'를 적는다."""
import sys
from PIL import Image, ImageDraw, ImageFont
src, out, kit = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
bg = Image.new('RGB', (W, H), (20, 22, 21))
im = Image.open(src).convert('RGB'); im.thumbnail((960, 1200))
bg.paste(im, ((W - im.width) // 2, 260))
d = ImageDraw.Draw(bg)
def f(sz, bold=True):
    for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
name = sys.argv[4] if len(sys.argv) > 4 else ''
d.text((64, 120), name or 'NEWS', font=f(44), fill=(217, 164, 65))
d.text((64, 260 + im.height + 70), f'피드의 {kit}에서 자세히', font=f(58), fill=(244, 242, 236))
bg.save(out, quality=92); print('story', out)

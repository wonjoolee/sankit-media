"""오늘(KST) 슬롯 중 릴스 영상도 story.jpg도 없는 것에 9:16 스토리 이미지를 만든다.
카드(4:5)를 그대로 스토리로 올리면 인스타가 위아래를 꽉 채우며 잘라 버리기 때문.
GitHub Actions 게시 전에 실행. 만든 파일이 있으면 출력의 마지막 줄이 'created N'."""
import datetime, glob, json, os, re
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KST = datetime.timezone(datetime.timedelta(hours=9))
day = datetime.datetime.now(KST).strftime("%Y-%m-%d")
FONT = os.path.join(ROOT, "pipeline", "assets", "story_font.otf")
BRAND = "MUKIT" if "mukit" in ROOT.lower() else "SANKIT"
n = 0
for d in sorted(glob.glob(os.path.join(ROOT, "queue", day, "slot*"))):
    if not os.path.exists(os.path.join(d, "post.json")) or os.path.exists(os.path.join(d, "posted.json")):
        continue
    if os.path.exists(os.path.join(d, "story.jpg")) or os.path.exists(os.path.join(d, "reel.mp4")):
        continue
    src = os.path.join(d, "01.jpg")
    if not os.path.exists(src):
        continue
    cap = json.load(open(os.path.join(d, "post.json"), encoding="utf-8")).get("caption", "")
    m = re.search(r"KIT\s*0*(\d+)", cap)
    kit = f"KIT {int(m.group(1)):03d}" if m else BRAND
    W, H = 1080, 1920
    bg = Image.new("RGB", (W, H), (20, 22, 21))
    im = Image.open(src).convert("RGB"); im.thumbnail((940, 1175))
    top = (H - im.height) // 2 - 40          # 위아래 인스타 UI(약 250px)를 피해 가운데
    bg.paste(im, ((W - im.width) // 2, top))
    dr = ImageDraw.Draw(bg)
    f1 = ImageFont.truetype(FONT, 46); f2 = ImageFont.truetype(FONT, 30)
    t = f"피드의 {kit}에서 자세히"
    w = dr.textlength(t, font=f1)
    dr.text(((W - w) / 2, top + im.height + 48), t, font=f1, fill=(244, 242, 236))
    s = f"@{BRAND.lower()}mag"
    w2 = dr.textlength(s, font=f2)
    dr.text(((W - w2) / 2, top + im.height + 118), s, font=f2, fill=(217, 164, 65))
    bg.save(os.path.join(d, "story.jpg"), quality=92)
    n += 1
    print("story", d)
print("created", n)
